"""Tests for producer table-handoff edge cases."""

import json
from pathlib import Path

import pytest

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.tables import load_producer_table_bundle


def _write_no_table_handoff(tmp_path: Path) -> Path:
    producer = tmp_path / "producer"
    tables = producer / "tables"
    tables.mkdir(parents=True)
    marker = {
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
    summary = {
        "physical_pdf_pages": [],
        "page_count": 0,
        "logical_table_count": 0,
        "family_count": 0,
        "zero_table_pages": [],
        "review_derivatives_retained": False,
    }
    manifest = {
        "schema_version": "1.0.0",
        "source_id": "document",
        "physical_pdf_pages": [],
        "summary": "summary.json",
        "pages": "pages.jsonl",
        "tables": "tables.jsonl",
        "family_assignments": "family_assignments.jsonl",
        "table_families": "table_families.json",
    }
    for name, payload in (
        ("summary.json", summary),
        ("table_families.json", {"families": [], "continuation_decisions": []}),
        ("manifest.json", manifest),
        ("no_table_stage.json", marker),
    ):
        (tables / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    for name in ("pages.jsonl", "tables.jsonl", "family_assignments.jsonl"):
        (tables / name).write_text("", encoding="utf-8")
    return producer


def test_explicit_no_table_stage_produces_empty_bundle(tmp_path: Path) -> None:
    """Accept a no-table claim only with its complete empty producer contract."""
    producer = _write_no_table_handoff(tmp_path)

    bundle = load_producer_table_bundle(producer)

    assert bundle.tables == ()
    assert bundle.families == ()
    assert bundle.region_mappings == ()


def test_marker_only_no_table_stage_is_rejected(tmp_path: Path) -> None:
    producer = _write_no_table_handoff(tmp_path)
    (producer / "tables" / "manifest.json").unlink()

    with pytest.raises(MappingContractError, match="missing artifacts.*manifest.json"):
        load_producer_table_bundle(producer)
