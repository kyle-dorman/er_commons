"""Focused tests for Task 03E.2 config, input verification, and identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import er_commons.hierarchy_inference.inputs as input_module
from er_commons.artifact_io import sha256_file
from er_commons.document_parsing.content_parsing.records import CompletionRecord
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.hierarchy_inference.candidate_identity import (
    build_candidate_identity,
    build_environment_record,
    code_bundle_sha256,
)
from er_commons.hierarchy_inference.config import (
    ACCEPTED_PRODUCER_RUN_ID,
    APPENDIX_P_PAGE_COUNT,
    APPENDIX_P_SOURCE_BYTES,
    APPENDIX_P_SOURCE_SHA256,
    HierarchyInferenceConfig,
)
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.inputs import (
    HierarchyInferenceInputs,
    load_hierarchy_inference_inputs,
)
from er_commons.source_release.models import SourceManifest


def _config(**updates: object) -> HierarchyInferenceConfig:
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "policy_version": "1.0.0",
        "pipeline_id": "brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1",
        "publication_authorization": "bounded_acceptance",
        "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
        "source_manifest_relative_path": "release/records/source_manifest.json",
        "source": {
            "source_id": "deir_appendix_p",
            "official_title": "Appendix P - Water Supply Assessment (PDF)",
            "expected_sha256": APPENDIX_P_SOURCE_SHA256,
            "expected_byte_size": APPENDIX_P_SOURCE_BYTES,
            "expected_pdf_page_count": APPENDIX_P_PAGE_COUNT,
        },
        "producer_artifact_relative_root": "pipelines/task03e",
        "producer_run_id": ACCEPTED_PRODUCER_RUN_ID,
        "artifact_relative_root": "pipelines/task03e2",
        "bounded_acceptance_artifact_relative_root": "pipelines/task03e2_review",
        "policy_relative_path": "docs/specs/hierarchy_correction_v1.md",
        "schema_relative_path": (
            "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json"
        ),
    }
    payload.update(updates)
    return HierarchyInferenceConfig.model_validate(payload)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def _completion(config: HierarchyInferenceConfig, manifest_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "producer_run_id": config.producer_run_id,
        "producer_status": "complete",
        "publication_status": "complete",
        "source_id": config.source.source_id,
        "source_sha256": config.source.expected_sha256,
        "source_manifest_sha256": manifest_sha256,
        "artifact_inventory": "records/artifact_inventory.json",
        "artifact_inventory_sha256": "a" * 64,
        "completed_at_utc": "2026-07-31T00:00:00Z",
    }


def test_config_rejects_unreviewed_fields_paths_and_source_changes() -> None:
    with pytest.raises(ValueError, match="extra_forbidden"):
        _config(unreviewed=True)
    with pytest.raises(ValueError, match="contained relative paths"):
        _config(artifact_relative_root="../escape")
    with pytest.raises(ValueError, match="artifact path must be contained"):
        _config(bounded_acceptance_artifact_relative_root="../escape")
    changed_source = _config().source.model_dump(mode="json")
    changed_source["expected_pdf_page_count"] = 221
    with pytest.raises(ValueError, match="approved Appendix P"):
        _config(source=changed_source)


def test_loader_verifies_run_and_source_before_loading_semantic_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    manifest_path = tmp_path / config.source_manifest_relative_path
    _write_json(manifest_path, {"source_release_version": config.source_release_version})
    source_path = tmp_path / "release/sources/appendix_p.pdf"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(b"fixture source")

    run_root = tmp_path / config.producer_artifact_relative_root / config.producer_run_id
    completion_path = run_root / "records/completion_record.json"
    inventory_path = run_root / "records/artifact_inventory.json"
    _write_json(completion_path, _completion(config, sha256_file(manifest_path)))
    _write_json(inventory_path, {"files": []})
    _write_json(
        run_root / "records/producer_identity.json",
        {
            "producer_run_id": config.producer_run_id,
            "identity": {
                "source": {
                    "source_id": config.source.source_id,
                    "sha256": config.source.expected_sha256,
                }
            },
        },
    )
    producer_root = run_root / "documents/deir_appendix_p/producer/docling"
    _write_json(producer_root / "document.json", {"texts": []})
    _write_json(producer_root / "conversion_pages.json", {"pages": []})

    calls: list[tuple[Path, str]] = []

    def verify(root: Path, run_id: str) -> Path:
        calls.append((root, run_id))
        return completion_path

    manifest = SourceManifest.model_construct(
        source_release_version=config.source_release_version,
        sources=[],
    )
    resolved = CompleteResolvedSource(
        source_id=config.source.source_id,
        source_path=source_path,
        source_sha256=config.source.expected_sha256,
        source_byte_size=config.source.expected_byte_size,
        source_page_count=config.source.expected_pdf_page_count,
        warnings=[],
    )
    monkeypatch.setattr(input_module, "verify_completed_run", verify)
    monkeypatch.setattr(input_module, "load_sealed_manifest", lambda *_args: manifest)
    monkeypatch.setattr(input_module, "resolve_complete_source", lambda *_args: resolved)

    inputs = load_hierarchy_inference_inputs(tmp_path, config)

    assert calls == [(run_root, config.producer_run_id)]
    assert inputs.document == {"texts": []}
    assert inputs.conversion_pages == {"pages": []}
    assert inputs.input_inventory == {
        "producer_completion_path": completion_path.relative_to(tmp_path).as_posix(),
        "producer_completion_sha256": sha256_file(completion_path),
        "producer_inventory_path": inventory_path.relative_to(tmp_path).as_posix(),
        "producer_inventory_sha256": sha256_file(inventory_path),
        "source_path": source_path.relative_to(tmp_path).as_posix(),
        "source_sha256": config.source.expected_sha256,
        "verified_file_count": 3,
    }


def test_identity_binds_exact_digests_and_derives_hcorv1_id(tmp_path: Path) -> None:
    config = _config()
    policy_path = tmp_path / "policy.md"
    schema_path = tmp_path / "schema.json"
    code_path = tmp_path / "src/owned.py"
    lock_path = tmp_path / "uv.lock"
    for path, content in (
        (policy_path, b"policy"),
        (schema_path, b"{}"),
        (code_path, b"VALUE = 1\n"),
        (lock_path, b"version = 1\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    completion = CompletionRecord.model_validate(_completion(config, "b" * 64))
    resolved = CompleteResolvedSource(
        source_id=config.source.source_id,
        source_path=tmp_path / "source.pdf",
        source_sha256=config.source.expected_sha256,
        source_byte_size=config.source.expected_byte_size,
        source_page_count=config.source.expected_pdf_page_count,
        warnings=[],
    )
    inputs = HierarchyInferenceInputs(
        producer_run_root=tmp_path / "producer",
        sealed_manifest=SourceManifest.model_construct(sources=[]),
        selected_source=resolved,
        producer_completion=completion,
        producer_identity={},
        document={},
        conversion_pages={},
        input_inventory={
            "producer_completion_sha256": "c" * 64,
            "producer_inventory_sha256": "d" * 64,
        },
    )

    identity = build_candidate_identity(
        config=config,
        config_sha256="e" * 64,
        inputs=inputs,
        policy_path=policy_path,
        schema_path=schema_path,
        project_root=tmp_path,
        owned_code_paths=(code_path,),
    )

    payload = {key: value for key, value in identity.items() if key != "candidate_id"}
    assert identity["candidate_id"] == f"hcorv1-{canonical_json_sha256(payload)}"
    assert identity["source_id"] == config.source.source_id
    assert identity["policy_sha256"] == sha256_file(policy_path)
    assert identity["schema_sha256"] == sha256_file(schema_path)
    assert identity["code_bundle_sha256"] == code_bundle_sha256(tmp_path, (code_path,))
    environment = build_environment_record(
        uv_lock_path=lock_path,
        package_names=("definitely-not-an-installed-package",),
    )
    assert environment["uv_lock_sha256"] == sha256_file(lock_path)
    assert environment["package_versions"] == {
        "definitely-not-an-installed-package": "not-installed"
    }
