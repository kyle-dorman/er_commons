"""Focused tests for the Task 03D configuration and verified input boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import er_commons.canonical_extraction.inputs as input_module
from er_commons.canonical_extraction.config import (
    CanonicalizationConfig,
    load_canonicalization_config,
)
from er_commons.canonical_extraction.inputs import load_canonicalization_inputs
from er_commons.document_extraction.producer_records import (
    CompletionRecord,
    ConversionObservation,
    PageRouteRecord,
    ProducerSummary,
)
from er_commons.source_freeze import SourceManifest, SourceRecord, SourceRole

CONFIG_PATH = Path("configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def _fake_handoff(tmp_path: Path, config: CanonicalizationConfig) -> None:
    selected = config.ordered_materialization_scope[0]
    manifest_path = tmp_path / config.source_manifest_relative_path
    _write_json(
        manifest_path,
        {
            "source_release_version": config.source_release_version,
            "sources": [
                {
                    "source_id": selected.source_id,
                    "source_role": "model_corpus",
                    "sha256": selected.source_sha256,
                    "pdf_page_count": selected.pdf_page_count,
                }
            ],
        },
    )
    _write_json(manifest_path.parent / "completion_record.json", {"sealed": True})

    run_root = tmp_path / config.producer_artifact_relative_root / config.producer_run_id
    records_root = run_root / "records"
    producer_root = run_root / "documents" / selected.source_id / "producer"
    _write_json(
        records_root / "producer_identity.json",
        {
            "producer_run_id": config.producer_run_id,
            "identity": {
                "source": {
                    "source_id": selected.source_id,
                    "sha256": selected.source_sha256,
                    "pdf_page_count": selected.pdf_page_count,
                }
            },
        },
    )
    _write_json(
        records_root / "producer_summary.json",
        {
            "producer_run_id": config.producer_run_id,
            "producer_status": "complete",
            "publication_status": "complete",
            "source_id": selected.source_id,
            "physical_page_count": selected.pdf_page_count,
            "routing": {"no_table_route": selected.pdf_page_count},
            "tables": {
                "status": "complete",
                "document_scope_complete": True,
                "verified_no_table_routes": True,
                "routed_pages": [],
                "routed_page_count": 0,
                "logical_table_count": 0,
                "family_assignment_count": 0,
                "family_count": 0,
                "zero_table_pages": [],
                "manifest": None,
            },
            "asset_count": 0,
            "warnings": [],
            "error_count": 0,
            "wall_seconds": 1.0,
            "conversion_cpu_seconds": 1.0,
            "peak_rss_bytes": 1,
            "output_bytes_before_inventory": 1,
        },
    )
    _write_json(
        records_root / "completion_record.json",
        {
            "schema_version": "1.0.0",
            "producer_run_id": config.producer_run_id,
            "producer_status": "complete",
            "publication_status": "complete",
            "source_id": selected.source_id,
            "source_sha256": selected.source_sha256,
            "source_manifest_sha256": "1" * 64,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": "2" * 64,
            "completed_at_utc": "2026-07-30T00:00:00Z",
        },
    )

    for path in (
        producer_root / "docling" / "document.json",
        producer_root / "asset_inventory.json",
    ):
        _write_json(path, {"path": path.name})
    _write_json(
        producer_root / "docling" / "conversion_observation.json",
        {
            "source_id": selected.source_id,
            "raw_status": "success",
            "status": "complete",
            "errors": [],
            "captured_python_warnings": [],
            "source_manifest_warnings": [],
            "expected_physical_pages": [1],
            "converted_physical_pages": [1],
            "page_coverage_complete": True,
            "asset_count": 0,
            "wall_seconds": 1.0,
            "cpu_seconds": 1.0,
            "peak_rss_bytes": 1,
        },
    )
    _write_jsonl(
        producer_root / "routing" / "page_routes.jsonl",
        [
            {
                "physical_pdf_page": 1,
                "page_size_pdf_points": [612.0, 792.0],
                "native_character_count": 0,
                "nonspace_character_count": 0,
                "native_text_rectangle_count": 0,
                "nonempty_line_count": 0,
                "text_width_fraction": 0.0,
                "text_height_fraction": 0.0,
                "nonspace_characters_per_square_point": 0.0,
                "digit_fraction": 0.0,
                "coordinate_key_count": 0,
                "strict_table_dominant": False,
                "strict_checks": {},
                "numeric_table_bearing": False,
                "numeric_checks": {},
                "layout_table_region_count": 0,
                "layout_table_regions_pdf_points_bottom_left": [],
                "route": "no_table_route",
                "source_id": selected.source_id,
                "layout_table_observations": [],
                "status": "complete",
            }
        ],
    )


def _typed_manifest(config: CanonicalizationConfig) -> SourceManifest:
    selected = config.ordered_materialization_scope[0]
    source = SourceRecord.model_construct(
        source_id=selected.source_id,
        source_role=SourceRole.MODEL_CORPUS,
        sha256=selected.source_sha256,
        pdf_page_count=selected.pdf_page_count,
        official_title="Fixture Appendix P",
        warnings=[],
    )
    return SourceManifest.model_construct(
        source_release_version=config.source_release_version,
        sources=[source],
    )


def test_checked_config_freezes_the_approved_non_release_scope() -> None:
    config, digest = load_canonicalization_config(CONFIG_PATH)

    assert len(digest) == 64
    assert config.candidate_scope == "document_scoped_non_release"
    assert config.acceptance_profile == "generic_complete_document"


def test_config_rejects_path_escape() -> None:
    payload = json.loads(CONFIG_PATH.read_text())
    payload["artifact_relative_root"] = "../escape"

    with pytest.raises(ValueError, match="contained relative"):
        CanonicalizationConfig.model_validate(payload)


def test_config_rejects_unknown_fields() -> None:
    payload = json.loads(CONFIG_PATH.read_text())
    payload["silent_new_policy"] = True

    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        CanonicalizationConfig.model_validate(payload)


def test_input_loader_verifies_seals_then_loads_preserved_plain_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = load_canonicalization_config(CONFIG_PATH)
    _fake_handoff(tmp_path, config)
    verified: list[tuple[Path, str]] = []

    def fake_verify(root: Path, run_id: str) -> Path:
        verified.append((root, run_id))
        return root / "records" / "completion_record.json"

    monkeypatch.setattr(input_module, "verify_completed_run", fake_verify)
    monkeypatch.setattr(
        input_module,
        "load_sealed_manifest",
        lambda _root, _config: _typed_manifest(config),
    )

    inputs = load_canonicalization_inputs(tmp_path, config)

    assert verified == [(inputs.producer_run_root, config.producer_run_id)]
    assert isinstance(inputs.document, dict)
    assert isinstance(inputs.sealed_manifest, SourceManifest)
    assert inputs.selected_source.source_id == config.selected_source_id
    assert isinstance(inputs.producer_summary_record, ProducerSummary)
    assert isinstance(inputs.producer_completion_record, CompletionRecord)
    assert isinstance(inputs.conversion_observation_record, ConversionObservation)
    assert isinstance(inputs.page_route_records[0], PageRouteRecord)
    assert inputs.page_route_records[0].physical_pdf_page == 1
    assert not hasattr(inputs, "table_records")
    assert not hasattr(inputs, "family_assignments")


def test_input_loader_stops_when_completed_run_verification_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = load_canonicalization_config(CONFIG_PATH)
    _fake_handoff(tmp_path, config)

    def reject_run(_root: Path, _run_id: str) -> Path:
        raise ValueError("inventory checksum changed")

    monkeypatch.setattr(input_module, "verify_completed_run", reject_run)

    with pytest.raises(ValueError, match="inventory checksum changed"):
        load_canonicalization_inputs(tmp_path, config)


def test_input_loader_rejects_producer_identity_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = load_canonicalization_config(CONFIG_PATH)
    _fake_handoff(tmp_path, config)
    run_root = tmp_path / config.producer_artifact_relative_root / config.producer_run_id
    identity_path = run_root / "records" / "producer_identity.json"
    identity = json.loads(identity_path.read_text())
    identity["identity"]["source"]["sha256"] = "0" * 64
    _write_json(identity_path, identity)

    monkeypatch.setattr(
        input_module,
        "verify_completed_run",
        lambda root, _run_id: root / "records" / "completion_record.json",
    )
    monkeypatch.setattr(
        input_module,
        "load_sealed_manifest",
        lambda _root, _config: _typed_manifest(config),
    )

    with pytest.raises(ValueError, match="source checksum differs"):
        load_canonicalization_inputs(tmp_path, config)
