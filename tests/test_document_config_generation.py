"""Explicit generation and preparation preserve semantics without source/model access."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from document_publication_test_support import _workspace

from er_commons.artifact_io import write_json_atomic
from er_commons.document_publication.config import load_document_run_spec
from er_commons.document_publication.config_generation.shared import (
    GenerationSpec,
    load_generation_spec,
)
from er_commons.document_publication.config_generation.workflow import generate_document_configs
from er_commons.document_publication.input_preparation import (
    InputPreparationRequest,
    prepare_document_inputs,
)

ROOT = Path(__file__).parents[1]
ROLES = (
    "content_parsing",
    "heading_evidence_parsing",
    "record_mapping",
    "hierarchy_inference",
    "document_structure",
    "document_reference_linking",
)


def generation_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Bind ordinary alpha/beta fixtures to explicitly copied current templates."""
    data, original = _workspace(tmp_path)
    original_spec = json.loads(original.read_text())
    original_spec["resource_policy"]["docling_timeout_seconds"] = None
    manifest = json.loads((data / "release/records/source_manifest.json").read_text())
    templates = {}
    for role in ROLES:
        relative = Path("templates") / f"{role}.json"
        target = tmp_path / relative
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "configs/task03h_templates" / f"{role}.json", target)
        templates[role] = relative.as_posix()
    (tmp_path / "writer.py").write_text("# synthetic writer\n")
    write_json_atomic(tmp_path / "target.json", {"target": "policy"})
    write_json_atomic(tmp_path / "resolution.json", {"resolution": "policy"})
    write_json_atomic(data / "descriptors/model_inventory.json", {"models": []})
    request = {
        "schema_version": "er_commons.document_config_generation.v1",
        "repository_root": ".",
        "data_root": "data",
        "templates": templates,
        "sources": [
            {
                "source_id": row["source_id"],
                "source_release_version": "release",
                "source_manifest_relative_path": "release/records/source_manifest.json",
                "expected_sha256": row["sha256"],
                "reference_aliases": [row["official_title"]],
            }
            for row in manifest["sources"]
        ],
        "baseline_manifest_relative_path": "release/records/source_manifest.json",
        "baseline_release_version": "release",
        "config_root": "generated/configs",
        "run_root": "runs/new_cycle",
        "catalog_output": "generated/source_family_catalog.json",
        "catalog_data_relative_path": "runs/new_cycle/inputs/source_family_catalog.json",
        "document_spec_output": "generated/document.json",
        "collection_spec_output": "generated/collection.json",
        "identity_output": "generated/identity.json",
        "model_inventory_relative_path": "descriptors/model_inventory.json",
        "target_policy": "target.json",
        "resolution_policy": "resolution.json",
        "resource_policy": original_spec["resource_policy"],
        "chunked_page_threshold": 300,
        "chunked_policy": {
            "schema_version": "er_commons.chunked_execution_policy.v1",
            "mode": "fixed_size",
            "source_selection": {"pdf_page_count_greater_than": 300},
            "target_range_size": 225,
            "hard_maximum": 275,
            "overlap_pages": 1,
            "max_range_rss_bytes": 1000000,
            "max_aggregate_rss_bytes": 1000000,
            "max_wall_seconds": 10,
        },
        "name_prefix": "synthetic_cycle",
        "source_family_id": "synthetic",
        "family_root_source_id": "alpha",
        "document_code": ["writer.py"],
        "collection_code": ["writer.py"],
        "document_contracts": [],
        "collection_contracts": [],
    }
    path = tmp_path / "generation.json"
    write_json_atomic(path, request)
    return data, path


def _sentinels(monkeypatch):
    """Source bytes and model weights remain inaccessible through the complete path."""
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.suffix in {".pdf", ".safetensors", ".pt"}:
            raise AssertionError(f"source/model bytes opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)


def test_generate_check_and_prepare_an_explicit_nonhistorical_scope(tmp_path, monkeypatch):
    data, path = generation_workspace(tmp_path)
    _sentinels(monkeypatch)
    result = generate_document_configs(path)
    assert len(result.values) == 16
    generated_bytes = {path: path.read_bytes() for path in result.values}
    assert generate_document_configs(path, check=True).values == result.values
    assert {path: path.read_bytes() for path in result.values} == generated_bytes
    spec, _ = load_document_run_spec(tmp_path / "generated/document.json")
    assert [item.source_id for item in spec.document_processes] == ["alpha", "beta"]
    for process in spec.document_processes:
        for role, relative in process.configs.model_dump().items():
            config = json.loads((tmp_path / relative).read_text())
            if "source_manifest_relative_path" in config:
                assert (
                    config["source_manifest_relative_path"]
                    == "release/records/source_manifest.json"
                )
            if role in {"content_parsing", "heading_evidence_parsing"}:
                assert config["model_inventory_relative_path"] == "descriptors/model_inventory.json"
    request = InputPreparationRequest(
        tmp_path / "generated/document.json",
        tmp_path / "generated/collection.json",
        data / "runs/new_cycle",
        data,
        tmp_path,
    )
    readiness_path = prepare_document_inputs(request)
    readiness = json.loads(readiness_path.read_text())
    assert readiness["source_scope"]["ordered_source_ids"] == ["alpha", "beta"]
    assert len(readiness["owner_configs"]) == 12
    assert readiness["source_pdf_bytes_read"] is False
    assert readiness["model_files_read"] is False
    assert readiness["freshness"]["task_root"] == "runs/new_cycle"


def test_generation_rejects_drift_without_overwriting_outputs(tmp_path):
    _, request = generation_workspace(tmp_path)
    result = generate_document_configs(request)
    target = tmp_path / "generated/configs/alpha/content_parsing.json"
    target.write_text('{"preserved":"different"}')
    before = {path: path.read_bytes() for path in result.values}
    for check in (False, True):
        with pytest.raises(ValueError, match="current outputs differ"):
            generate_document_configs(request, check=check)
        assert {path: path.read_bytes() for path in result.values} == before


def test_generation_has_no_implicit_version_and_rejects_wrong_binding(tmp_path, monkeypatch):
    _, request = generation_workspace(tmp_path)
    spec = load_generation_spec(request)
    monkeypatch.setenv("ER_COMMONS_TASK03H_RUN_VERSION", "wrong_legacy_version")
    assert load_generation_spec(request) == spec
    value = json.loads(request.read_text())
    value["sources"][0]["expected_sha256"] = "f" * 64
    write_json_atomic(request, value)
    with pytest.raises(ValueError, match="source binding differs"):
        generate_document_configs(request)
    assert not (tmp_path / "generated").exists()
    value["identity_output"] = "../escape.json"
    with pytest.raises(ValueError, match="contained relative"):
        GenerationSpec.model_validate(value)


def test_generation_rejects_invalid_membership_before_writing(tmp_path):
    """A logical replacement cannot omit its explicit substitution record."""
    _, path = generation_workspace(tmp_path)
    request = json.loads(path.read_bytes())
    request["sources"][1]["logical_source_id"] = "deir_appendix_f1"
    write_json_atomic(path, request)
    with pytest.raises(ValueError, match="substitution"):
        generate_document_configs(path)
    assert not (tmp_path / "generated").exists()


def test_chunk_selection_retains_accepted_threshold(tmp_path):
    """Only source metadata above the existing production threshold gets a chunk policy."""
    from er_commons.document_publication.config_generation.shared import load_generation_spec

    _, path = generation_workspace(tmp_path)
    spec = load_generation_spec(path)
    paths = spec.chunked_policy_paths(
        [
            {"source_id": "alpha", "pdf_page_count": 300},
            {"source_id": "beta", "pdf_page_count": 301},
        ]
    )
    assert paths == (tmp_path / "generated/configs/beta/chunked_conversion.json",)


@pytest.mark.parametrize(
    "role",
    ["record_mapping", "hierarchy_inference", "document_structure", "document_reference_linking"],
)
def test_invalid_downstream_template_rejected_before_outputs(tmp_path, role):
    """Every generated downstream owner validates its controls before publication."""
    _, request_path = generation_workspace(tmp_path)
    request = json.loads(request_path.read_bytes())
    template = tmp_path / request["templates"][role]
    value = json.loads(template.read_bytes())
    value["schema_relative_path"] = "/outside/schema.json"
    write_json_atomic(template, value)
    with pytest.raises(ValueError):
        generate_document_configs(request_path)
    assert not (tmp_path / "generated").exists()
