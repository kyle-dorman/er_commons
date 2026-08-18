"""Tests for explicit table-family evidence ordering."""

from __future__ import annotations

from er_commons.document_parsing.table_reconstruction.families import assign_families


def table(
    table_id: str,
    page: int,
    index: int,
    header: list[list[str]],
) -> dict[str, object]:
    """Build the smallest family-relevant logical table record."""
    return {
        "table_id": table_id,
        "physical_pdf_page": page,
        "page_table_index": index,
        "header_matrix": header,
        "cleanup": {"effective_column_count": len(header[0]) if header else 0},
    }


def test_footer_run_merges_only_geometric_owners() -> None:
    """A multi-table start page contributes only its lowest table to the run."""
    pages = [
        {
            "physical_pdf_page": 10,
            "footer": {"sheet_id": "sheet", "internal_page": 1, "internal_total": 2},
            "footer_owner_table_id": "p10_bottom",
        },
        {
            "physical_pdf_page": 11,
            "footer": {"sheet_id": "sheet", "internal_page": 2, "internal_total": 2},
            "footer_owner_table_id": "p11_only",
        },
    ]
    tables = [
        table("p10_top", 10, 1, [["top"]]),
        table("p10_bottom", 10, 2, [["continuation"]]),
        table("p11_only", 11, 1, [["different header"]]),
    ]
    assignments, families = assign_families(pages, tables)
    by_table = {item["table_id"]: item for item in assignments}
    assert by_table["p10_bottom"]["family_id"] == by_table["p11_only"]["family_id"]
    assert by_table["p10_top"]["family_id"] != by_table["p10_bottom"]["family_id"]
    merged = next(item for item in families if item["page_count"] == 2)
    assert merged["evidence"] == ["footer_run"]


def test_exact_headers_merge_adjacent_nonowners() -> None:
    """Exact cleaned headers merge only the same visual slot on adjacent pages."""
    pages = [
        {"physical_pdf_page": 20, "footer": None, "footer_owner_table_id": None},
        {"physical_pdf_page": 21, "footer": None, "footer_owner_table_id": None},
    ]
    tables = [
        table("left", 20, 1, [["a", "b"]]),
        table("right", 21, 1, [["a", "b"]]),
    ]
    assignments, families = assign_families(pages, tables)
    assert len({item["family_id"] for item in assignments}) == 1
    assert families[0]["evidence"] == ["exact_cleaned_header"]


def test_explicit_rejection_blocks_exact_header_merge() -> None:
    """Older header evidence cannot override a terminal boundary decision."""
    pages = [
        {"physical_pdf_page": 20, "footer": None, "footer_owner_table_id": None},
        {"physical_pdf_page": 21, "footer": None, "footer_owner_table_id": None},
    ]
    tables = [
        table("left", 20, 1, [["a", "b"]]),
        table("right", 21, 1, [["a", "b"]]),
    ]
    decisions = [
        {
            "left_table_id": "left",
            "right_table_id": "right",
            "status": "rejected",
        }
    ]

    assignments, _families = assign_families(pages, tables, continuation_records=decisions)

    assert len({item["family_id"] for item in assignments}) == 2


def test_explicit_accepted_pair_uses_only_continuation_evidence() -> None:
    """An accepted decision owns the union even when exact headers also match."""
    pages = [
        {"physical_pdf_page": 20, "footer": None, "footer_owner_table_id": None},
        {"physical_pdf_page": 21, "footer": None, "footer_owner_table_id": None},
    ]
    tables = [
        table("left", 20, 1, [["a", "b"]]),
        table("right", 21, 1, [["a", "b"]]),
    ]
    decisions = [
        {
            "left_table_id": "left",
            "right_table_id": "right",
            "status": "accepted",
        }
    ]

    assignments, families = assign_families(pages, tables, continuation_records=decisions)

    assert len({item["family_id"] for item in assignments}) == 1
    assert families[0]["evidence"] == ["cross_page_continuation"]


def test_family_prefix_is_source_scoped() -> None:
    """Routed sources cannot collide while legacy G3 IDs remain the default."""
    pages = [{"physical_pdf_page": 1, "footer": None, "footer_owner_table_id": None}]
    assignments, families = assign_families(
        pages,
        [table("main_p00001_t001", 1, 1, [])],
        family_id_prefix="main_table",
    )
    assert assignments[0]["family_id"] == "main_table_family_0001"
    assert families[0]["family_id"] == "main_table_family_0001"
