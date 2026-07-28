"""Tests for stable logical-output comparison."""

from __future__ import annotations

import json
from pathlib import Path

from er_commons.table_extraction.comparison import (
    compare_pipeline_outputs,
    compare_records,
)


def test_compare_records_ignores_unselected_runtime_fields() -> None:
    """Runtime and path changes do not count as logical extraction changes."""
    baseline = [{"table_id": "t1", "shape": [2, 3], "wall_seconds": 4.0}]
    candidate = [{"table_id": "t1", "shape": [2, 3], "wall_seconds": 1.0}]
    result = compare_records(
        artifact="tables.jsonl",
        baseline_records=baseline,
        candidate_records=candidate,
        key="table_id",
        fields=("shape",),
    )
    assert result["exact_match"] is True


def test_compare_records_reports_missing_extra_and_changed_fields() -> None:
    """Every stable mismatch is explicit rather than summarized away."""
    baseline = [{"table_id": "t1", "shape": [2, 3]}, {"table_id": "missing", "shape": [1, 1]}]
    candidate = [{"table_id": "t1", "shape": [3, 3]}, {"table_id": "extra", "shape": [1, 1]}]
    result = compare_records(
        artifact="tables.jsonl",
        baseline_records=baseline,
        candidate_records=candidate,
        key="table_id",
        fields=("shape",),
    )
    assert result["exact_match"] is False
    assert result["missing_keys"] == ["missing"]
    assert result["extra_keys"] == ["extra"]
    assert result["field_mismatches"] == [
        {
            "key": "t1",
            "field": "shape",
            "baseline": [2, 3],
            "candidate": [3, 3],
        }
    ]


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    """Write a tiny comparison fixture."""
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def test_baseline_page_comparison_ignores_larger_context(tmp_path: Path) -> None:
    """A large run compares reviewed pages without requiring identical family IDs."""
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    baseline.mkdir()
    candidate.mkdir()
    page = {
        "physical_pdf_page": 19,
        "route": "simple_stream",
        "complex_page": False,
        "ruling_region_count": 0,
        "table_count": 1,
        "footer": None,
        "footer_owner_table_id": None,
    }
    extra_page = {**page, "physical_pdf_page": 1}
    table = {
        "table_id": "g3_p00019_t001",
        "physical_pdf_page": 19,
        "page_table_index": 1,
        "route": "simple_stream",
        "parser": "camelot_stream",
        "parser_order": 1,
        "bbox_pdf_points_bottom_left": [0, 0, 1, 1],
        "shape_raw": [1, 1],
        "shape_clean": [1, 1],
        "columns_pdf_points": [],
        "cleanup": {},
        "header_matrix": [],
        "clean_csv": {"sha256": "abc", "path": "old.csv"},
    }
    extra_table = {
        **table,
        "table_id": "g3_p00001_t001",
        "physical_pdf_page": 1,
    }
    write_jsonl(baseline / "pages.jsonl", [page])
    write_jsonl(candidate / "pages.jsonl", [extra_page, page])
    write_jsonl(baseline / "tables.jsonl", [table])
    write_jsonl(candidate / "tables.jsonl", [extra_table, table])
    write_jsonl(
        baseline / "family_assignments.jsonl",
        [{"table_id": "g3_p00019_t001", "family_id": "old", "footer_owned": False}],
    )
    write_jsonl(
        candidate / "family_assignments.jsonl",
        [
            {"table_id": "g3_p00001_t001", "family_id": "new-1", "footer_owned": False},
            {"table_id": "g3_p00019_t001", "family_id": "new-2", "footer_owned": False},
        ],
    )
    result = compare_pipeline_outputs(
        baseline,
        candidate,
        baseline_pages_only=True,
    )
    assert result["exact_semantic_match"] is True
