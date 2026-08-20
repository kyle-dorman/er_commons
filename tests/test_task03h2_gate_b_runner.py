"""Offline behavior and ownership tests for the Task 03H.2 Gate B runner."""

from __future__ import annotations

import ast
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    read_json_object,
    write_json_atomic,
)
from er_commons.chunked_conversion.qualification.gate_b_application import (
    verify_completed_run,
)
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    SEAMS,
    GateBContractError,
    GateBWorkerSpec,
)
from er_commons.chunked_conversion.qualification.gate_b_inputs import identity_payload
from er_commons.chunked_conversion.qualification.gate_b_trace import (
    GateBTraceError,
    compare_sealed_page_trace,
)
from er_commons.chunked_conversion.qualification.gate_b_worker import write_failure
from er_commons.document_parsing.content_parsing.identity import code_identity

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _heading(text: str, level: int) -> dict[str, Any]:
    return {
        "page_no": 13,
        "level": level,
        "item": {"label": "section_header", "text": text, "_trace_pages": [13]},
    }


def _trace(levels: tuple[int, ...]) -> dict[str, Any]:
    return {
        "schema_version": "er_commons.task03h2_gate_b_page_trace.v1",
        "pages": [13],
        "collections": {"texts": []},
        "headings": [_heading(f"heading-{index}", level) for index, level in enumerate(levels)],
        "alignment_pages": [],
        "assets": [],
    }


def test_heading_difference_requires_one_floor_preserving_compression() -> None:
    differences = compare_sealed_page_trace(
        _trace((1, 2, 3)), _trace((1, 1, 2)), seam_id="p0013_p0014_cross_page"
    )
    assert len(differences) == 2
    assert {row["compression_offset"] for row in differences} == {1}
    assert {row["classification"] for row in differences} == {
        "expected_whole_document_heading_context"
    }


def test_heading_difference_has_stable_contextual_diagnostic() -> None:
    with pytest.raises(GateBTraceError) as raised:
        compare_sealed_page_trace(_trace((1, 2, 3)), _trace((1, 1, 3)), seam_id="corrupt")
    assert raised.value.code == "heading_compression_not_floor_preserving"
    assert raised.value.path == "corrupt"


def test_worker_spec_rejects_extra_fields_and_invalid_topology() -> None:
    payload = {
        "source_root": "/source",
        "config_path": "/config.json",
        "data_root": "/data",
        "seam_root": "/attempt/seam",
        "sealed_trace_path": "/attempt/trace.json",
        "seam": SEAMS[0].model_dump(mode="json"),
        "max_rss_bytes": 1,
        "foreign": True,
    }
    with pytest.raises(ValueError, match="extra_forbidden"):
        GateBWorkerSpec.model_validate(payload)
    payload.pop("foreign")
    payload["seam"]["right_core"] = {"start": 88, "end": 89}
    with pytest.raises(ValueError, match="adjacent"):
        GateBWorkerSpec.model_validate(payload)


def test_completed_run_rejects_transplanted_identity(tmp_path: Path) -> None:
    original = _completed_run(tmp_path, "gateb1-" + "a" * 64)
    assert verify_completed_run(original, expected_run_id=original.name).is_file()
    transplanted = tmp_path / ("gateb1-" + "b" * 64)
    shutil.copytree(original, transplanted)
    with pytest.raises(GateBContractError) as raised:
        verify_completed_run(transplanted, expected_run_id=transplanted.name)
    assert raised.value.code == "foreign_run_completion"
    assert raised.value.path.endswith("records/completion_record.json")


def test_completed_run_rejects_corrupted_inventory(tmp_path: Path) -> None:
    root = _completed_run(tmp_path, "gateb1-" + "a" * 64)
    (root / "evidence.json").write_text('{"changed":true}\n')
    with pytest.raises(ValueError, match="inventory_file_size.*evidence.json"):
        verify_completed_run(root, expected_run_id=root.name)


def test_failure_recovery_preserves_first_context(tmp_path: Path) -> None:
    root = tmp_path / "attempt"
    first = GateBContractError("first_failure", "seams[s1]", "original evidence")
    second = GateBContractError("second_failure", "seams[s1]", "later symptom")
    path = write_failure(root, first, stage="seam_execution", seam_id="s1")
    original = path.read_bytes()
    assert write_failure(root, second, stage="coordinator", seam_id="s1") == path
    assert path.read_bytes() == original
    record = read_json_object(path)
    assert record["error_code"] == "first_failure"
    assert record["error_path"] == "seams[s1]"


def test_identity_excludes_cli_shell_but_binds_implementation(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    records = source_root / "records"
    records.mkdir(parents=True)
    (records / "artifact_inventory.json").write_text("{}\n")
    config = tmp_path / "config.json"
    config.write_text("{}\n")
    conversion = SimpleNamespace(run_id="dconv1-" + "a" * 64, payload={"sealed": True})
    prepared = SimpleNamespace(
        conversion_identity=conversion,
        runtime={"package_versions": {"docling": "2.115.0"}},
    )
    first = identity_payload(
        project_root=PROJECT_ROOT,
        source_root=source_root,
        config_path=config,
        prepared=prepared,
        max_rss_bytes=8 * 1024**3,
        max_wall_seconds=2700.0,
    )
    assert "runner_sha256" not in first
    assert "scripts/run_task03h2_gate_b.py" not in {
        item["path"] for item in first["implementation"]["files"]
    }
    expected = code_identity(
        [PROJECT_ROOT / "src/er_commons/chunked_conversion/qualification/gate_b_application.py"],
        repo_root=PROJECT_ROOT,
    )
    assert any(
        item["sha256"] == expected["files"][0]["sha256"]
        for item in first["implementation"]["files"]
    )
    second_prepared = SimpleNamespace(
        conversion_identity=conversion,
        runtime={"package_versions": {"docling": "different"}},
    )
    second = identity_payload(
        project_root=PROJECT_ROOT,
        source_root=source_root,
        config_path=config,
        prepared=second_prepared,
        max_rss_bytes=8 * 1024**3,
        max_wall_seconds=2700.0,
    )
    assert canonical_json_sha256(first) != canonical_json_sha256(second)


def test_cli_is_a_small_package_backed_shell() -> None:
    path = PROJECT_ROOT / "scripts/run_task03h2_gate_b.py"
    source = path.read_text()
    assert len(source.splitlines()) <= 60
    imports = {
        node.module
        for node in ast.parse(source).body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "er_commons.chunked_conversion.qualification.gate_b_application" in imports
    assert "docling.document_converter" not in imports


def _completed_run(tmp_path: Path, run_id: str) -> Path:
    root = tmp_path / run_id
    (root / "records").mkdir(parents=True)
    (root / "evidence.json").write_text('{"stable":true}\n')
    inventory_path = root / "records/artifact_inventory.json"
    write_json_atomic(
        inventory_path,
        artifact_inventory(
            root, excluded={"records/artifact_inventory.json", "records/completion_record.json"}
        ),
    )
    from er_commons.artifact_io import sha256_file

    write_json_atomic(
        root / "records/completion_record.json",
        {
            "schema_version": "er_commons.task03h2_gate_b_completion.v1",
            "status": "complete",
            "run_id": run_id,
            "source_conversion_id": (
                "dconv1-97a8d4048839d9ba26c78151d0446e1c1bbef9848183f1ce9b9140c92e4c3f68"
            ),
            "artifact_inventory": "records/artifact_inventory.json",
            "completion_last": True,
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "gate_c_started": False,
            "g2_started": False,
        },
    )
    return root
