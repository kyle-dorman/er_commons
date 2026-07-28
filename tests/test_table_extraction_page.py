"""Unit tests for the pure parts of one-page table extraction."""

from __future__ import annotations

import pytest

from er_commons.table_extraction import page


def test_bbox_iou_and_visual_order() -> None:
    """Geometry helpers use bottom-left PDF coordinates consistently."""
    assert page.bbox_iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0
    assert page.bbox_iou([0, 0, 5, 5], [6, 6, 10, 10]) == 0.0
    records = [
        {"bbox_pdf_points_bottom_left": [50, 0, 60, 10]},
        {"bbox_pdf_points_bottom_left": [20, 20, 30, 30]},
        {"bbox_pdf_points_bottom_left": [10, 20, 15, 30]},
    ]
    assert sorted(records, key=page.visual_order_key) == [
        records[2],
        records[1],
        records[0],
    ]


def test_cleanup_removes_footer_filename_and_empty_columns() -> None:
    """Cleanup is explicit and does not invent or join cell text."""
    rows = [
        ["workbook_v1", "", ""],
        ["header", "value", ""],
        ["row", "1", ""],
        ["sheet", "1 of 2", ""],
    ]
    cleanup = {
        "footer_counter_pattern": r"\b\d+\s+of\s+\d+\b",
        "leading_filename_pattern": r"^[a-z0-9_]+_v[0-9]+$",
    }
    cleaned, evidence = page.clean_rows(rows, cleanup)
    assert cleaned == [["header", "value"], ["row", "1"]]
    assert evidence["removed_footer_row_indices"] == [3]
    assert evidence["removed_filename_row_indices"] == [0]
    assert evidence["retained_column_indices"] == [0, 1]


def test_footer_and_network_coverage() -> None:
    """Native footer parsing and ruled-coverage evidence are deterministic."""
    cleanup = {
        "footer_pattern": (
            r"(?P<sheet>\d+\.[A-Za-z0-9_]+)\s+"
            r"(?P<page>\d+)\s+of\s+(?P<total>\d+)"
        )
    }
    assert page.parse_footer("body 2.HRA_BLOCKS 3 of 10", cleanup) == {
        "sheet_id": "2.hra_blocks",
        "internal_page": 3,
        "internal_total": 10,
        "matched_text": "2.HRA_BLOCKS 3 of 10",
    }
    regions = [{"bbox_pdf_points_bottom_left": [0, 0, 5, 10]}]
    assert page.rectangle_union_coverage([0, 0, 10, 10], regions, 2.0) == pytest.approx(0.5)
