"""Validate, serialize, and seal one assembled canonical candidate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from er_commons.canonical_extraction.config import CanonicalizationConfig
from er_commons.canonical_extraction.constants import SCHEMA_PATH
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.identifiers import make_record_id
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.layout import RECORD_COLLECTIONS
from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_inventory,
    write_json,
    write_jsonl,
)
from er_commons.canonical_extraction.record_sets import (
    CanonicalRecordSet,
    JsonRecord,
    MaterializationReport,
)
from er_commons.canonical_extraction.tables import ProducerTableBundle
from er_commons.canonical_extraction.validation import validate_bundle_integrity

RECORD_PATHS = {
    "documents": "canonical/documents.jsonl",
    "pages": "canonical/pages.jsonl",
    "sections": "canonical/sections.jsonl",
    "blocks": "canonical/blocks.jsonl",
    "tables": "canonical/tables.jsonl",
    "table_families": "canonical/table_families.jsonl",
    "figures": "canonical/figures.jsonl",
    "images": "canonical/images.jsonl",
    "assets": "canonical/assets.jsonl",
    "cross_references": "canonical/cross_references.jsonl",
    "routing_observations": "observations/routing.jsonl",
    "table_stage_observations": "observations/table_stage.jsonl",
    "conversion_observations": "observations/conversion.jsonl",
    "raw_mappings": "mappings/raw_to_canonical.jsonl",
}


def canonicalization_warnings(
    inputs: CanonicalizationInputs,
    table_bundle: ProducerTableBundle,
    report: MaterializationReport,
) -> list[str]:
    """Preserve producer, zero-mapping, and invalid-provenance warnings."""
    return [
        *inputs.conversion_observation_record.captured_python_warnings,
        *[
            f"zero table mapping: {mapping.raw_object_ref} provenance {mapping.provenance_index}"
            for mapping in table_bundle.region_mappings
            if not mapping.clean_table_ids
        ],
        *[
            f"invalid provenance: {item['raw_object_pointer']} "
            f"index {item['provenance_index']} {item['rejection_reason']}"
            for item in report.invalid_provenance
        ],
    ]


def build_summary(
    *,
    records: CanonicalRecordSet,
    inputs: CanonicalizationInputs,
    table_bundle: ProducerTableBundle,
    report: MaterializationReport,
    candidate_id: str,
) -> JsonRecord:
    """Build the Task 03D accounting summary once from named projections."""
    mapped_regions = sum(bool(mapping.clean_table_ids) for mapping in table_bundle.region_mappings)
    zero_regions = sum(not mapping.clean_table_ids for mapping in table_bundle.region_mappings)
    summary: JsonRecord = {
        "schema_version": "er_commons.canonicalization_summary.v1",
        "candidate_id": candidate_id,
        "release_candidate": False,
        "source_id": inputs.selected_source.source_id,
        "counts": records.counts(),
        "clean_table_cell_count": sum(len(table["cells"]) for table in records.tables),
        "table_region_mapping_count": len(table_bundle.region_mappings),
        "mapped_table_region_count": mapped_regions,
        "zero_table_region_count": zero_regions,
        "document_index_count": sum(
            item["label"] == "document_index" for item in inputs.document["tables"]
        ),
        "document_index_descendant_text_count": report.document_index_descendant_count,
        "text_accounting": {
            "producer_item_count": report.producer_text_count,
            "emitted_count": report.emitted_text_count,
            "suppressed_count": report.suppressed_text_count,
            "unaccounted_count": (
                report.producer_text_count
                - report.emitted_text_count
                - report.suppressed_text_count
            ),
        },
        "furniture": {
            "producer_item_count": report.producer_furniture_count,
            "emitted_count": report.emitted_furniture_count,
            "suppressed_picture_descendant_count": len(
                report.suppressed_picture_furniture_pointers
            ),
            "suppressed_picture_descendant_pointers": list(
                report.suppressed_picture_furniture_pointers
            ),
        },
        "invalid_provenance": copy.deepcopy(list(report.invalid_provenance)),
        "producer_warnings": list(inputs.producer_summary_record.warnings),
        "errors": [],
    }
    validate_appendix_p_acceptance(summary)
    return summary


def _require_equal(*, invariant: str, actual: Any, expected: Any) -> None:
    """Raise one diagnostic error for a named Appendix P invariant."""
    if actual != expected:
        raise ContractError(
            f"Appendix P invariant failed: {invariant}; expected={expected!r}, actual={actual!r}"
        )


def validate_appendix_p_acceptance(summary: JsonRecord) -> None:
    """Enforce the reviewed Task 03D counts with actionable failures."""
    expected_counts = {
        "pages": 222,
        "routing_observations": 222,
        "table_stage_observations": 34,
        "tables": 19,
        "table_families": 19,
        "figures": 27,
        "images": 27,
    }
    for record_family, expected in expected_counts.items():
        _require_equal(
            invariant=f"{record_family} count",
            actual=summary["counts"][record_family],
            expected=expected,
        )
    expected_facts = {
        "clean table cell count": (summary["clean_table_cell_count"], 3669),
        "mapped table region count": (summary["mapped_table_region_count"], 19),
        "zero-table region count": (summary["zero_table_region_count"], 15),
        "document-index descendant text count": (
            summary["document_index_descendant_text_count"],
            663,
        ),
        "producer furniture count": (summary["furniture"]["producer_item_count"], 522),
        "emitted furniture count": (summary["furniture"]["emitted_count"], 521),
        "picture-owned furniture suppression count": (
            summary["furniture"]["suppressed_picture_descendant_count"],
            1,
        ),
    }
    for invariant, (actual, expected) in expected_facts.items():
        _require_equal(invariant=invariant, actual=actual, expected=expected)


def write_record_files(root: Path, records: CanonicalRecordSet) -> list[JsonRecord]:
    """Serialize schema collections in the published layout and order."""
    collections = records.as_bundle_collections()
    manifest_files = []
    for collection in RECORD_COLLECTIONS:
        path = root / RECORD_PATHS[collection.bundle_key]
        count = write_jsonl(path, collections[collection.bundle_key])
        manifest_files.append(
            {
                "record_type": collection.record_type.replace("-", "_"),
                "path": RECORD_PATHS[collection.bundle_key],
                "sha256": sha256_file(path),
                "record_count": count,
            }
        )
    return manifest_files


def validate_schema(bundle: JsonRecord) -> None:
    """Validate every persisted record against the published JSON Schema."""
    schema = json.loads(SCHEMA_PATH.read_text())
    registry = Registry().with_resource(
        schema["$id"],
        DRAFT202012.create_resource(schema),
    )
    Draft202012Validator(schema, registry=registry).validate(bundle)


def build_manifest(
    *,
    identity: JsonRecord,
    config: CanonicalizationConfig,
    record_files: list[JsonRecord],
    warnings: list[str],
) -> JsonRecord:
    """Build the canonical manifest from validated identity and file facts."""
    return {
        "schema_version": "er_commons.canonical_extraction_manifest.v1",
        "extraction_id": identity["extraction_id"],
        "identity_sha256": identity["identity_sha256"],
        "source_release_version": config.source_release_version,
        "source_manifest_path": config.source_manifest_relative_path.as_posix(),
        "source_manifest_sha256": identity["source_release"]["source_manifest_sha256"],
        "ordered_document_ids": [
            records_document_id(identity["extraction_id"], config.selected_source_id)
        ],
        "record_files": record_files,
        "canonicalization_status": "complete_with_warnings" if warnings else "complete",
        "canonicalization_warnings": warnings,
        "canonicalization_errors": [],
        "document_scope_complete": True,
    }


def records_document_id(extraction_id: str, source_id: str) -> str:
    """Return the deterministic document ID without depending on build context."""
    return make_record_id(extraction_id, "document", source_id)


def write_validate_and_seal_candidate(
    *,
    root: Path,
    identity: JsonRecord,
    config: CanonicalizationConfig,
    inputs: CanonicalizationInputs,
    table_bundle: ProducerTableBundle,
    records: CanonicalRecordSet,
    report: MaterializationReport,
) -> None:
    """Write, independently validate, summarize, and completion-seal a candidate."""
    write_json(root / "records" / "extraction_identity.json", identity)
    record_files = write_record_files(root, records)
    warnings = canonicalization_warnings(inputs, table_bundle, report)
    manifest = build_manifest(
        identity=identity,
        config=config,
        record_files=record_files,
        warnings=warnings,
    )
    collections = records.as_bundle_collections()
    bundle: JsonRecord = {
        "identity": identity,
        "manifest": manifest,
        **collections,
    }
    validate_schema(bundle)
    validate_bundle_integrity(bundle)
    summary = build_summary(
        records=records,
        inputs=inputs,
        table_bundle=table_bundle,
        report=report,
        candidate_id=identity["extraction_id"],
    )
    summary["validation"] = {
        "schema_valid": True,
        "bundle_integrity_valid": True,
    }
    write_json(root / "records" / "manifest.json", manifest)
    write_json(root / "records" / "canonicalization_summary.json", summary)
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonicalization_completion.v1",
            "candidate_id": identity["extraction_id"],
            "release_candidate": False,
            "candidate_scope": "document_scoped",
            "source_ids": [config.selected_source_id],
            "status": manifest["canonicalization_status"],
            "manifest_sha256": sha256_file(root / "records" / "manifest.json"),
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "warning_count": len(warnings),
            "error_count": 0,
        },
    )
