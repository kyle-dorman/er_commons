"""Validate the producer's complete, completion-last no-table handoff."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.table_records import (
    JsonObject,
    read_json_object,
    read_jsonl_objects,
)


@dataclass(frozen=True)
class NoTableHandoff:
    """A verified producer claim that no pages were routed to table extraction."""

    marker: JsonObject


def load_no_table_handoff(table_root: Path) -> NoTableHandoff | None:
    """Return a verified no-table handoff, or ``None`` when no marker exists."""
    marker_path = table_root / "no_table_stage.json"
    if not marker_path.exists():
        return None
    required = (
        "summary.json",
        "pages.jsonl",
        "tables.jsonl",
        "family_assignments.jsonl",
        "table_families.json",
        "manifest.json",
    )
    missing = [name for name in required if not (table_root / name).is_file()]
    if missing:
        raise MappingContractError(
            f"incomplete no-table producer handoff; missing artifacts: {missing}"
        )
    marker = read_json_object(marker_path)
    _require_no_table_marker(marker)
    _require_empty_records(table_root / "pages.jsonl", label="pages")
    _require_empty_records(table_root / "tables.jsonl", label="tables")
    _require_empty_records(table_root / "family_assignments.jsonl", label="assignments")
    families = read_json_object(table_root / "table_families.json")
    if families != {"families": [], "continuation_decisions": []}:
        raise MappingContractError("no-table family artifact is not empty")
    summary = read_json_object(table_root / "summary.json")
    if summary != {
        "physical_pdf_pages": [],
        "page_count": 0,
        "logical_table_count": 0,
        "family_count": 0,
        "zero_table_pages": [],
        "review_derivatives_retained": False,
    }:
        raise MappingContractError("no-table summary is inconsistent")
    _require_no_table_manifest(read_json_object(table_root / "manifest.json"))
    return NoTableHandoff(marker=marker)


def _require_empty_records(path: Path, *, label: str) -> None:
    if read_jsonl_objects(path):
        raise MappingContractError(f"no-table {label} artifact is not empty")


def _require_no_table_marker(marker: JsonObject) -> None:
    expected = {
        "status": "not_applicable",
        "document_scope_complete": True,
        "verified_no_table_routes": True,
        "routed_pages": [],
        "routed_page_count": 0,
        "logical_table_count": 0,
        "family_assignment_count": 0,
        "family_count": 0,
        "zero_table_pages": [],
    }
    if marker != expected:
        raise MappingContractError("invalid no-table producer handoff marker")


def _require_no_table_manifest(manifest: JsonObject) -> None:
    expected_fields = {
        "schema_version": "1.0.0",
        "physical_pdf_pages": [],
        "summary": "summary.json",
        "pages": "pages.jsonl",
        "tables": "tables.jsonl",
        "family_assignments": "family_assignments.jsonl",
        "table_families": "table_families.json",
    }
    if any(manifest.get(key) != value for key, value in expected_fields.items()):
        raise MappingContractError("invalid no-table producer manifest")
    source_id = manifest.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise MappingContractError("no-table producer manifest lacks source_id")
