"""Tests for contextual repeated-header fragment projection."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.table_reconstruction.fragments import project_logical_tables


def _table(table_id: str, page: int, *, rows: int, header_rows: int) -> dict[str, Any]:
    return {
        "table_id": table_id,
        "physical_pdf_page": page,
        "page_table_index": 1,
        "region_id": "layout_001",
        "bbox_pdf_points_bottom_left": [100.0, 100.0, 700.0, 550.0],
        "page_size_pdf_points": [800.0, 600.0],
        "columns_pdf_points": [
            {"left": 100.0, "right": 400.0},
            {"left": 400.0, "right": 700.0},
        ],
        "shape_clean": [rows, 2],
        "header_matrix": [["A", "B"] for _ in range(header_rows)],
        "table_record": f"pages/page_{page:05d}/tables/{table_id}/table.json",
    }


def _page_result(page: int, table: dict[str, Any]) -> dict[str, Any]:
    return {
        "physical_pdf_page": page,
        "table_count": 1,
        "tables": [table],
        "parser_evidence": {
            "region_matches": [{"region_id": "layout_001", "matched": True, "matched_iou": 1.0}]
        },
    }


def _page_record(page: int, *, markers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "physical_pdf_page": page,
        "table_count": 1,
        "footer_owner_table_id": None,
        "boundary_markers_before_first_table": markers or [],
    }


def test_repeated_header_only_edge_is_preserved_but_not_logical() -> None:
    left = _table("left", 10, rows=8, header_rows=2)
    right = _table("right", 11, rows=2, header_rows=2)

    projection = project_logical_tables(
        [_page_result(10, left), _page_result(11, right)],
        [_page_record(10), _page_record(11)],
        [left, right],
    )

    assert [table["table_id"] for table in projection.tables] == ["left"]
    assert projection.page_records[1]["detected_table_count"] == 1
    assert projection.page_records[1]["table_count"] == 0
    assert projection.fragments[0]["fragment_table_id"] == "right"
    assert projection.fragments[0]["source_table_id"] == "left"
    assert projection.page_results[1]["tables"] == []
    match = projection.page_results[1]["parser_evidence"]["region_matches"][0]
    assert match["matched"] is False
    assert match["disposition"] == "header_only_continuation_fragment"


def test_header_only_table_without_prior_context_remains_logical() -> None:
    right = _table("right", 11, rows=2, header_rows=2)

    projection = project_logical_tables(
        [_page_result(11, right)],
        [_page_record(11)],
        [right],
    )

    assert [table["table_id"] for table in projection.tables] == ["right"]
    assert projection.fragments == []


def test_new_marker_prevents_header_only_fragment_projection() -> None:
    left = _table("left", 10, rows=8, header_rows=2)
    right = _table("right", 11, rows=2, header_rows=2)

    projection = project_logical_tables(
        [_page_result(10, left), _page_result(11, right)],
        [_page_record(10), _page_record(11, markers=[{"label": "caption"}])],
        [left, right],
    )

    assert [table["table_id"] for table in projection.tables] == ["left", "right"]
    assert projection.fragments == []


def test_projection_is_idempotent_for_reused_page_results() -> None:
    left = _table("left", 10, rows=8, header_rows=2)
    right = _table("right", 11, rows=2, header_rows=2)
    first = project_logical_tables(
        [_page_result(10, left), _page_result(11, right)],
        [_page_record(10), _page_record(11)],
        [left, right],
    )

    second = project_logical_tables(first.page_results, first.page_records, first.tables)

    assert second == first
