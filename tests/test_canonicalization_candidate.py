"""Focused tests for candidate sealing and named record-set boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.canonical_extraction import candidate
from er_commons.canonical_extraction.candidate import (
    RECORD_PATHS,
    build_summary,
    write_record_files,
    write_validate_and_seal_candidate,
)
from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS
from er_commons.canonical_extraction.publication import verify_completed_candidate
from er_commons.canonical_extraction.record_sets import (
    CanonicalRecordSet,
    MaterializationReport,
)
from er_commons.canonical_extraction.tables import (
    ProducerTableBundle,
    RegionTableMapping,
)
from er_commons.canonical_extraction.validation import validate_bundle_integrity

ROOT = Path(__file__).parents[1]
FIXTURE_PATH = (
    ROOT
    / "benchmarks"
    / "er_bench"
    / "fixtures"
    / "canonical_extraction"
    / "v1"
    / "valid_bundle.json"
)


def _fixture_bundle() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text()))


def _records_from_bundle(bundle: dict[str, Any]) -> CanonicalRecordSet:
    return CanonicalRecordSet(
        documents=tuple(bundle["documents"]),
        pages=tuple(bundle["pages"]),
        sections=tuple(bundle["sections"]),
        blocks=tuple(bundle["blocks"]),
        tables=tuple(bundle["tables"]),
        table_families=tuple(bundle["table_families"]),
        figures=tuple(bundle["figures"]),
        images=tuple(bundle["images"]),
        assets=tuple(bundle["assets"]),
        cross_references=tuple(bundle["cross_references"]),
        routing_observations=tuple(bundle["routing_observations"]),
        table_stage_observations=tuple(bundle["table_stage_observations"]),
        conversion_observations=tuple(bundle["conversion_observations"]),
        raw_mappings=tuple(bundle["raw_mappings"]),
    )


def test_record_collections_serialize_in_contract_order_with_exact_counts(
    tmp_path: Path,
) -> None:
    bundle = _fixture_bundle()
    records = _records_from_bundle(bundle)

    manifest_files = write_record_files(tmp_path, records)

    assert list(records.as_bundle_collections()) == [
        collection.bundle_key for collection in RECORD_COLLECTIONS
    ]
    assert records.counts() == {
        collection.bundle_key: len(bundle[collection.bundle_key])
        for collection in RECORD_COLLECTIONS
    }
    assert [item["path"] for item in manifest_files] == [
        RECORD_PATHS[collection.bundle_key] for collection in RECORD_COLLECTIONS
    ]
    assert [item["record_count"] for item in manifest_files] == [
        len(bundle[collection.bundle_key]) for collection in RECORD_COLLECTIONS
    ]
    for collection in RECORD_COLLECTIONS:
        lines = (tmp_path / RECORD_PATHS[collection.bundle_key]).read_text().splitlines()
        assert [json.loads(line) for line in lines] == bundle[collection.bundle_key]


def _accepted_record_set() -> CanonicalRecordSet:
    table_cells = [{"text": str(index)} for index in range(3669)]
    return CanonicalRecordSet(
        documents=({},),
        pages=tuple({} for _ in range(222)),
        sections=(),
        blocks=(),
        tables=({"cells": table_cells}, *({"cells": []} for _ in range(18))),
        table_families=tuple({} for _ in range(19)),
        figures=tuple({} for _ in range(27)),
        images=tuple({} for _ in range(27)),
        assets=(),
        cross_references=(),
        routing_observations=tuple({} for _ in range(222)),
        table_stage_observations=tuple({} for _ in range(34)),
        conversion_observations=(),
        raw_mappings=(),
    )


def _region_mapping(index: int, mapped: bool) -> RegionTableMapping:
    return RegionTableMapping(
        physical_pdf_page=1,
        region_id=f"region-{index}",
        raw_object_ref=f"#/tables/{index}",
        provenance_index=0,
        bbox_pdf_points_bottom_left=(0.0, 0.0, 1.0, 1.0),
        clean_table_ids=(f"table-{index}",) if mapped else (),
        unmapped_reason=None if mapped else "zero_tables",
    )


def test_summary_snapshots_mutable_producer_evidence() -> None:
    invalid = {"raw_object_pointer": "#/texts/1", "rejection_reason": "outside"}
    producer_warnings = ["producer warning"]
    inputs = cast(
        Any,
        SimpleNamespace(
            selected_source=SimpleNamespace(source_id="deir_appendix_p"),
            document={"tables": [{"label": "document_index"} for _ in range(7)]},
            producer_summary_record=SimpleNamespace(warnings=producer_warnings),
        ),
    )
    table_bundle = ProducerTableBundle(
        tables=(),
        families=(),
        region_mappings=tuple(_region_mapping(index, mapped=index < 19) for index in range(34)),
    )
    report = MaterializationReport(
        invalid_provenance=(invalid,),
        document_index_descendant_count=663,
        producer_text_count=6931,
        emitted_text_count=3706,
        suppressed_text_count=3225,
        producer_furniture_count=522,
        emitted_furniture_count=521,
        suppressed_picture_furniture_pointers=("#/texts/312",),
    )

    summary = build_summary(
        records=_accepted_record_set(),
        inputs=inputs,
        table_bundle=table_bundle,
        report=report,
        candidate_id="exv1-" + "a" * 64,
    )
    summary["invalid_provenance"][0]["rejection_reason"] = "mutated"
    summary["producer_warnings"].append("mutated")

    assert report.invalid_provenance[0]["rejection_reason"] == "outside"
    assert producer_warnings == ["producer warning"]
    assert summary["text_accounting"]["unaccounted_count"] == 0


def test_fixture_bundle_reaches_validation_inventory_and_completion_seal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle()
    records = _records_from_bundle(bundle)
    identity = bundle["identity"]
    manifest = bundle["manifest"]
    config = cast(
        Any,
        SimpleNamespace(
            source_release_version=manifest["source_release_version"],
            source_manifest_relative_path=Path(manifest["source_manifest_path"]),
            selected_source_id="deir_fixture",
        ),
    )
    inputs = cast(
        Any,
        SimpleNamespace(
            conversion_observation_record=SimpleNamespace(captured_python_warnings=[]),
        ),
    )
    report = MaterializationReport((), 0, 0, 0, 0, 0, 0, ())
    table_bundle = ProducerTableBundle((), (), ())
    validation_calls: list[str] = []
    real_validate_schema = candidate.validate_schema

    def validate_schema(bundle_value: dict[str, Any]) -> None:
        validation_calls.append("schema")
        real_validate_schema(bundle_value)

    def validate_integrity(bundle_value: dict[str, Any]) -> None:
        validation_calls.append("integrity")
        validate_bundle_integrity(bundle_value)

    monkeypatch.setattr(candidate, "validate_schema", validate_schema)
    monkeypatch.setattr(candidate, "validate_bundle_integrity", validate_integrity)
    monkeypatch.setattr(
        candidate,
        "build_summary",
        lambda **_kwargs: {
            "schema_version": "er_commons.canonicalization_summary.v1",
            "candidate_id": identity["extraction_id"],
        },
    )
    candidate_root = tmp_path / identity["extraction_id"]

    write_validate_and_seal_candidate(
        root=candidate_root,
        identity=identity,
        config=config,
        inputs=inputs,
        table_bundle=table_bundle,
        records=records,
        report=report,
    )

    assert validation_calls == ["schema", "integrity"]
    assert (
        verify_completed_candidate(candidate_root, identity["extraction_id"])
        == candidate_root / "records" / "completion_record.json"
    )
    completion = json.loads((candidate_root / "records" / "completion_record.json").read_text())
    inventory = json.loads((candidate_root / "records" / "artifact_inventory.json").read_text())
    assert completion["warning_count"] == 0
    assert completion["status"] == "complete"
    assert "records/completion_record.json" not in {item["path"] for item in inventory["files"]}
