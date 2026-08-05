"""Tests for conservative cross-page table continuation decisions."""

from __future__ import annotations

from typing import Any

from er_commons.document_extraction.table_markers import markers_before_first_table
from er_commons.table_extraction.continuations import continuation_decisions
from er_commons.table_extraction.families import assign_families


def _table(
    table_id: str,
    page: int,
    index: int,
    *,
    bottom: float,
    top: float,
    columns: int = 3,
    retained: list[int] | None = None,
) -> dict[str, Any]:
    width = 800.0
    column_width = 600.0 / columns
    return {
        "table_id": table_id,
        "physical_pdf_page": page,
        "page_table_index": index,
        "bbox_pdf_points_bottom_left": [100.0, bottom, 700.0, top],
        "page_size_pdf_points": [width, 600.0],
        "columns_pdf_points": [
            {"left": 100.0 + i * column_width, "right": 100.0 + (i + 1) * column_width}
            for i in range(columns)
        ],
        "cleanup": {
            "retained_column_indices": retained if retained is not None else list(range(columns)),
            "effective_column_count": len(retained) if retained is not None else columns,
        },
        "header_matrix": [["A", "B", "C"]],
        "raw_column_type_signatures": [
            {"column_index": i, "dominant_type": "text"} for i in range(columns)
        ],
    }


def _pages(*, markers: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "physical_pdf_page": 10,
            "footer": None,
            "footer_owner_table_id": None,
            "boundary_markers_before_first_table": [],
        },
        {
            "physical_pdf_page": 11,
            "footer": None,
            "footer_owner_table_id": None,
            "boundary_markers_before_first_table": markers or [],
        },
    ]


def test_accepts_edge_aligned_columns_and_records_inherited_header() -> None:
    tables = [
        _table("left", 10, 2, bottom=60.0, top=300.0),
        _table("right", 11, 1, bottom=200.0, top=540.0, retained=[0, 2]),
    ]

    decisions = continuation_decisions(_pages(), tables)

    assert decisions[0]["status"] == "accepted"
    assert decisions[0]["inherited_header"]["origin"] == "inherited"
    assert (
        decisions[0]["inherited_header"]["content_status"]
        == "unresolved_no_printed_header_projection"
    )
    assert "source_header_matrix" not in decisions[0]["inherited_header"]
    assert decisions[0]["inherited_header"]["target_clean_to_source_column"] == [0, 2]
    assert decisions[0]["inherited_header"]["unrepresented_source_columns"] == [1]
    assignments, families = assign_families(_pages(), tables, continuation_records=decisions)
    assert len({assignment["family_id"] for assignment in assignments}) == 1
    assert families[0]["evidence"] == ["cross_page_continuation"]


def test_new_marker_rejects_geometry_compatible_boundary() -> None:
    marker = {"label": "section_header", "text": "A new table"}
    tables = [
        _table("left", 10, 1, bottom=30.0, top=300.0),
        _table("right", 11, 1, bottom=100.0, top=540.0),
    ]

    decision = continuation_decisions(_pages(markers=[marker]), tables)[0]

    assert decision["status"] == "rejected"
    assert decision["reasons"] == ["new_table_marker"]


def test_column_disagreement_remains_ambiguous_and_separate() -> None:
    tables = [
        _table("left", 10, 1, bottom=30.0, top=300.0, columns=3),
        _table("right", 11, 1, bottom=100.0, top=540.0, columns=2),
    ]

    decisions = continuation_decisions(_pages(), tables)

    assert decisions[0]["status"] == "ambiguous"
    assert "raw_column_geometry_mismatch" in decisions[0]["reasons"]
    assignments, _families = assign_families(_pages(), tables, continuation_records=decisions)
    assert len({assignment["family_id"] for assignment in assignments}) == 2


def test_incompatible_retained_column_types_remain_ambiguous() -> None:
    left = _table("left", 10, 1, bottom=30.0, top=300.0)
    right = _table("right", 11, 1, bottom=100.0, top=540.0)
    right["raw_column_type_signatures"][1]["dominant_type"] = "numeric"

    decision = continuation_decisions(_pages(), [left, right])[0]

    assert decision["status"] == "ambiguous"
    assert "retained_column_type_mismatch" in decision["reasons"]


def test_missing_placeholder_is_compatible_with_numeric_continuation() -> None:
    left = _table("left", 10, 1, bottom=30.0, top=300.0)
    right = _table("right", 11, 1, bottom=100.0, top=540.0)
    left["raw_column_type_signatures"][1] = {
        "dominant_type": "text",
        "counts": {"text": 1, "numeric": 0, "missing": 1, "empty": 0},
    }
    right["raw_column_type_signatures"][1] = {
        "dominant_type": "numeric",
        "counts": {"text": 1, "numeric": 4, "missing": 0, "empty": 0},
    }

    decision = continuation_decisions(_pages(), [left, right])[0]

    assert decision["status"] == "accepted"
    assert decision["measurements"]["compatible_retained_column_types"] is True


def test_markers_only_include_structural_text_above_first_table() -> None:
    payload = {
        "texts": [
            {
                "label": "section_header",
                "text": "New section",
                "prov": [{"page_no": 2, "bbox": {"l": 1, "b": 550, "r": 10, "t": 560}}],
            },
            {
                "label": "caption",
                "text": "Below the first table",
                "prov": [{"page_no": 2, "bbox": {"l": 1, "b": 300, "r": 10, "t": 310}}],
            },
            {
                "label": "text",
                "text": "Ordinary text",
                "prov": [{"page_no": 2, "bbox": {"l": 1, "b": 570, "r": 10, "t": 580}}],
            },
        ]
    }
    observations = [{"bbox_pdf_points_bottom_left": [0.0, 100.0, 100.0, 500.0]}]

    markers = markers_before_first_table(payload, 2, observations)

    assert [(marker["label"], marker["text"]) for marker in markers] == [
        ("section_header", "New section")
    ]
