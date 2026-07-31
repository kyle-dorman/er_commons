"""Synthetic tests for the external Task 03E.2 quality-gate seam."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.hierarchy_correction.quality_gate import (
    REPORT_NAMES,
    SEMANTIC_PATHS,
    QualityGateConfig,
    QualityGatePass,
    assemble_quality_gate_pass,
    candidate_semantic_sha256,
    load_quality_gate_config,
    verify_quality_gate_pass,
    write_quality_gate_pass,
)

ROOT = Path(__file__).parents[1]
CHECKED_CONFIG = ROOT / "configs/brisbane_baylands_2025_deir_task03e2_quality_gate_v1.json"
CANDIDATE_ID = "hcorv1-" + "a" * 64
EXTRACTION_ID = "exv1-" + "b" * 64
COMPARISON_ID = "cmpv2-" + "c" * 64


def _bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _synthetic_gate(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    project_root = tmp_path / "project"
    data_root = tmp_path / "data"
    task03e_report_bytes = {
        "producer_comparison_report.json": _bytes({"status": "pass", "kind": "comparison"}),
        "bounded_review_report.json": _bytes({"status": "pass", "kind": "review"}),
        "controls/control_report.json": _bytes({"status": "pass", "kind": "controls"}),
    }
    tracked: dict[str, dict[str, str]] = {}
    for name in ("development_cases", "held_out_manifest", "review_schema"):
        relative = f"evidence/{name}.json"
        raw = _bytes({"name": name})
        _write(project_root / relative, raw)
        tracked[name] = {"path": relative, "sha256": _sha(raw)}
    fixture_manifest_relative = "evidence/fixture_manifest.json"
    fixture_manifest_raw = _bytes(
        {
            "development_evidence": {
                "reviewed_exact_outline_anchor_count": 29,
                "reviewed_numbering_relation_count": 21,
                "task_03e_comparison_report_sha256": _sha(
                    task03e_report_bytes["producer_comparison_report.json"]
                ),
                "task_03e_bounded_review_sha256": _sha(
                    task03e_report_bytes["bounded_review_report.json"]
                ),
            }
        }
    )
    _write(project_root / fixture_manifest_relative, fixture_manifest_raw)
    tracked["fixture_manifest"] = {
        "path": fixture_manifest_relative,
        "sha256": _sha(fixture_manifest_raw),
    }
    evaluation_relative = "configs/evaluation.json"
    evaluation_raw = _bytes(
        {
            "main_report_controls": [
                {
                    "first_page": 44,
                    "last_page": 46,
                    "purpose": "false_positive_list_item_control",
                },
                {
                    "first_page": 2000,
                    "last_page": 2000,
                    "purpose": "false_negative_visible_subheading_control",
                },
            ],
            "control_harness": {
                "expected_range_names": [
                    "deir_main_pages_00044_00046",
                    "deir_main_pages_02000_02000",
                ]
            },
        }
    )
    _write(project_root / evaluation_relative, evaluation_raw)
    inventory_raw = _bytes({"files": []})
    inventory_sha = _sha(inventory_raw)
    completion_raw = _bytes(
        {
            "candidate_id": EXTRACTION_ID,
            "artifact_inventory_sha256": inventory_sha,
        }
    )
    reference_root = data_root / "pipelines/task03d" / EXTRACTION_ID
    _write(reference_root / "records/artifact_inventory.json", inventory_raw)
    _write(reference_root / "records/completion_record.json", completion_raw)
    task03e_root = data_root / "pipelines/task03e" / COMPARISON_ID
    for relative, raw in task03e_report_bytes.items():
        _write(task03e_root / relative, raw)
    control_bytes = {
        "deir_main_pages_00044_00046": (_bytes({"document": 44}), _bytes({"pages": 44})),
        "deir_main_pages_02000_02000": (
            _bytes({"document": 2000}),
            _bytes({"pages": 2000}),
        ),
    }
    for range_name, (document_raw, pages_raw) in control_bytes.items():
        control_root = task03e_root / "controls/ranges" / range_name
        _write(control_root / "document.json", document_raw)
        _write(control_root / "conversion_pages.json", pages_raw)
    config_record = {
        "schema_version": "1.0.0",
        "quality_gate_id": "brisbane_baylands_2025_deir_task03e2_quality_gate_v1",
        **tracked,
        "task03e_evaluation_config": {
            "path": evaluation_relative,
            "sha256": _sha(evaluation_raw),
        },
        "expected_exact_outline_anchor_count": 29,
        "expected_numbering_relation_count": 21,
        "main_report_control_ranges": [
            {
                "range_name": "deir_main_pages_00044_00046",
                "first_page": 44,
                "last_page": 46,
                "purpose": "false_positive_list_item_control",
                "document_sha256": _sha(control_bytes["deir_main_pages_00044_00046"][0]),
                "conversion_pages_sha256": _sha(control_bytes["deir_main_pages_00044_00046"][1]),
            },
            {
                "range_name": "deir_main_pages_02000_02000",
                "first_page": 2000,
                "last_page": 2000,
                "purpose": "false_negative_visible_subheading_control",
                "document_sha256": _sha(control_bytes["deir_main_pages_02000_02000"][0]),
                "conversion_pages_sha256": _sha(control_bytes["deir_main_pages_02000_02000"][1]),
            },
        ],
        "task03e_review_reference": {
            "artifact_relative_root": "pipelines/task03e",
            "comparison_id": COMPARISON_ID,
            "control_ranges_relative_root": "controls/ranges",
            "producer_comparison_report_sha256": _sha(
                task03e_report_bytes["producer_comparison_report.json"]
            ),
            "bounded_review_report_sha256": _sha(
                task03e_report_bytes["bounded_review_report.json"]
            ),
            "control_report_sha256": _sha(task03e_report_bytes["controls/control_report.json"]),
        },
        "task03d1_reference": {
            "artifact_relative_root": "pipelines/task03d",
            "extraction_id": EXTRACTION_ID,
            "completion_sha256": _sha(completion_raw),
            "artifact_inventory_sha256": inventory_sha,
        },
        "review_artifact_relative_root": "pipelines/task03e2_review",
    }
    config_path = project_root / "configs/gate.json"
    config_raw = _bytes(config_record)
    _write(config_path, config_raw)
    candidate_root = data_root / "candidate"
    for index, relative in enumerate(SEMANTIC_PATHS):
        _write(candidate_root / relative, f"semantic-{index}\n".encode())
    metrics = {
        "candidate_id": CANDIDATE_ID,
        "median_fresh_wall_time_seconds": 1.0,
        "wall_time_ratio": 0.1,
        "artifact_bytes": 100,
        "artifact_bytes_ratio": 0.01,
        "peak_rss_bytes": 1000,
    }
    _write(candidate_root / "records/metrics.json", _bytes(metrics))
    review_root = data_root / "pipelines/task03e2_review" / CANDIDATE_ID
    reports: dict[str, dict[str, str]] = {}
    for name in REPORT_NAMES:
        relative = f"reports/{name}.json"
        status = "complete" if name == "review_inventory" else "pass"
        report = {"report_name": name, "status": status}
        if name == "repeat_resource":
            report = {**report, **metrics}
        raw = _bytes(report)
        _write(review_root / relative, raw)
        reports[name] = {"path": relative, "sha256": _sha(raw), "status": status}
    pass_record = QualityGatePass.model_validate(
        {
            "record_type": "hierarchy_quality_gate_pass",
            "schema_version": "1.0.0",
            "quality_gate_id": config_record["quality_gate_id"],
            "quality_gate_config_sha256": _sha(config_raw),
            "candidate_id": CANDIDATE_ID,
            "candidate_semantic_sha256": candidate_semantic_sha256(candidate_root),
            "reports": reports,
            "status": "pass",
        }
    )
    pass_path = review_root / "quality_gate_pass.json"
    write_quality_gate_pass(pass_path, pass_record)
    return project_root, data_root, candidate_root, pass_path


def test_checked_config_binds_current_tracked_inputs() -> None:
    config, _ = load_quality_gate_config(CHECKED_CONFIG)

    for evidence in (
        config.development_cases,
        config.fixture_manifest,
        config.held_out_manifest,
        config.review_schema,
        config.task03e_evaluation_config,
    ):
        assert _sha((ROOT / evidence.path).read_bytes()) == evidence.sha256
    assert config.task03d1_reference.extraction_id == (
        "exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28"
    )


def test_terminal_pass_verifies_candidate_reports_and_reference_seals(tmp_path: Path) -> None:
    project_root, data_root, candidate_root, pass_path = _synthetic_gate(tmp_path)

    verified = verify_quality_gate_pass(
        pass_path=pass_path,
        config_path=project_root / "configs/gate.json",
        candidate_root=candidate_root,
        candidate_id=CANDIDATE_ID,
        project_root=project_root,
        data_root=data_root,
    )

    assert verified.candidate_id == CANDIDATE_ID
    assert verified.candidate_semantic_sha256 == candidate_semantic_sha256(candidate_root)


def test_terminal_pass_assembler_binds_exact_named_report_set(tmp_path: Path) -> None:
    project_root, data_root, candidate_root, pass_path = _synthetic_gate(tmp_path)
    pass_path.unlink()

    verified = assemble_quality_gate_pass(
        config_path=project_root / "configs/gate.json",
        candidate_root=candidate_root,
        candidate_id=CANDIDATE_ID,
        project_root=project_root,
        data_root=data_root,
        report_relative_paths={name: Path(f"reports/{name}.json") for name in REPORT_NAMES},
    )

    assert verified.path == pass_path
    assert pass_path.is_file()
    with pytest.raises(FileExistsError):
        assemble_quality_gate_pass(
            config_path=project_root / "configs/gate.json",
            candidate_root=candidate_root,
            candidate_id=CANDIDATE_ID,
            project_root=project_root,
            data_root=data_root,
            report_relative_paths={name: Path(f"reports/{name}.json") for name in REPORT_NAMES},
        )


def test_terminal_pass_assembler_rejects_an_incomplete_report_set(tmp_path: Path) -> None:
    project_root, data_root, candidate_root, pass_path = _synthetic_gate(tmp_path)
    pass_path.unlink()

    with pytest.raises(ValueError, match="report-name set differs"):
        assemble_quality_gate_pass(
            config_path=project_root / "configs/gate.json",
            candidate_root=candidate_root,
            candidate_id=CANDIDATE_ID,
            project_root=project_root,
            data_root=data_root,
            report_relative_paths={"development": Path("reports/development.json")},
        )


@pytest.mark.parametrize("mutation", ["report", "semantic", "reference", "control", "metrics"])
def test_terminal_pass_fails_closed_on_changed_evidence(
    tmp_path: Path,
    mutation: str,
) -> None:
    project_root, data_root, candidate_root, pass_path = _synthetic_gate(tmp_path)
    if mutation == "report":
        (pass_path.parent / "reports/development.json").write_text('{"status":"reject"}\n')
        expected = "report checksum differs"
    elif mutation == "semantic":
        (candidate_root / SEMANTIC_PATHS[0]).write_text("changed\n")
        expected = "candidate semantic checksum differs"
    elif mutation == "reference":
        reference = data_root / "pipelines/task03d" / EXTRACTION_ID
        (reference / "records/completion_record.json").write_text("{}\n")
        expected = "Task 03D.1 terminal checksum differs"
    elif mutation == "control":
        control = (
            data_root
            / "pipelines/task03e"
            / COMPARISON_ID
            / "controls/ranges/deir_main_pages_00044_00046/document.json"
        )
        control.write_text("{}\n")
        expected = "Task 03E control checksum differs"
    else:
        metrics = json.loads((candidate_root / "records/metrics.json").read_text())
        metrics["artifact_bytes"] += 1
        (candidate_root / "records/metrics.json").write_bytes(_bytes(metrics))
        expected = "repeat/resource metrics differ"

    with pytest.raises(ValueError, match=expected):
        verify_quality_gate_pass(
            pass_path=pass_path,
            config_path=project_root / "configs/gate.json",
            candidate_root=candidate_root,
            candidate_id=CANDIDATE_ID,
            project_root=project_root,
            data_root=data_root,
        )


def test_quality_config_rejects_changed_control_ranges() -> None:
    record = json.loads(CHECKED_CONFIG.read_text())
    record["main_report_control_ranges"][0]["first_page"] = 45

    with pytest.raises(ValueError, match="control ranges differ"):
        QualityGateConfig.model_validate(record)
