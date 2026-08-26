"""Policy tests for full-page table ownership of duplicate native text."""

from __future__ import annotations

from dataclasses import replace

import pytest

from er_commons.document_records.record_mapping.provenance import (
    ProvenanceProjection,
    project_regions,
)
from er_commons.document_records.record_mapping.table_text_ownership import (
    TABLE_TEXT_OWNERSHIP_REASON,
    TableTextOwnership,
    assign_table_text_ownership,
)
from er_commons.document_records.record_mapping.tables import (
    CleanTableCell,
    ProducerTable,
    TableCleanupEvidence,
)

PAGE_IDS = {1: "page-1", 2: "page-2"}
PAGE_SIZES = {1: (100.0, 100.0), 2: (100.0, 100.0)}


def text_item(
    *boxes: tuple[int, tuple[float, float, float, float]],
    content_layer: str = "body",
) -> dict[str, object]:
    """Build one editable native-text fixture from page and bbox pairs."""
    return {
        "content_layer": content_layer,
        "orig": "native text",
        "prov": [
            {
                "page_no": page,
                "bbox": {"l": bbox[0], "b": bbox[1], "r": bbox[2], "t": bbox[3]},
            }
            for page, bbox in boxes
        ],
    }


def full_page_table(
    table_id: str = "table-1",
    *,
    page: int = 1,
    bbox: tuple[float, float, float, float] = (5.0, 5.0, 45.0, 45.0),
) -> ProducerTable:
    """Build one valid clean full-page table fixture."""
    return ProducerTable(
        table_id=table_id,
        physical_pdf_page=page,
        page_table_index=1,
        region_id=None,
        parser="camelot_stream",
        shape_raw=(1, 1),
        shape_clean=(1, 1),
        bbox_pdf_points_bottom_left=bbox,
        cleanup=TableCleanupEvidence(
            removed_footer_row_indices=(),
            removed_filename_row_indices=(),
            retained_column_indices=(0,),
            effective_column_count=1,
        ),
        cells=(
            CleanTableCell(
                row_index=0,
                column_index=0,
                text="cell",
                bbox_pdf_points_bottom_left=bbox,
            ),
        ),
        raw_csv_path="raw.csv",
        clean_csv_path="table.csv",
        clean_csv_sha256="0" * 64,
        cells_path="cells.json",
        table_record_path="table.json",
        family_id=f"family-{table_id}",
    )


def ownership_for(
    texts: list[dict[str, object]],
    *tables: ProducerTable,
    document_index_descendants: set[str] | None = None,
) -> TableTextOwnership:
    """Project fixture provenance and run the public ownership policy."""
    document = {"texts": texts}
    projections: dict[str, ProvenanceProjection] = {}
    for index, item in enumerate(texts):
        pointer = f"#/texts/{index}"
        projections[pointer] = project_regions(
            item=item,
            pointer=pointer,
            page_ids=PAGE_IDS,
            page_sizes=PAGE_SIZES,
        )
    return assign_table_text_ownership(
        document=document,
        tables=tables,
        projections=projections,
        page_ids=PAGE_IDS,
        document_index_descendants=document_index_descendants or set(),
    )


def test_records_exact_text_pointer_to_producer_table_owner() -> None:
    ownership = ownership_for(
        [text_item((1, (10.0, 10.0, 20.0, 20.0)))],
        full_page_table("full-page-table"),
    )

    assert ownership.table_id_by_text_pointer == {
        "#/texts/0": "full-page-table",
    }
    assert ownership.decisions[0].as_json() == {
        "schema_version": "er_commons.table_text_ownership_observation.v1",
        "text_pointer": "#/texts/0",
        "producer_table_id": "full-page-table",
        "physical_pdf_page": 1,
        "table_bbox_pdf_points_bottom_left": [5.0, 5.0, 45.0, 45.0],
        "text_regions": [
            {
                "page_id": "page-1",
                "bbox_pdf_points_bottom_left": [10.0, 10.0, 20.0, 20.0],
            }
        ],
        "reason": TABLE_TEXT_OWNERSHIP_REASON,
    }


def test_owns_multiple_regions_when_one_table_contains_all_of_them() -> None:
    ownership = ownership_for(
        [
            text_item(
                (1, (10.0, 10.0, 20.0, 20.0)),
                (1, (25.0, 25.0, 35.0, 35.0)),
            )
        ],
        full_page_table("full-page-table"),
    )

    assert ownership.table_id_by_text_pointer == {"#/texts/0": "full-page-table"}
    assert len(ownership.decisions[0].text_regions) == 2


def test_retains_multiple_regions_when_one_is_outside_every_table() -> None:
    ownership = ownership_for(
        [
            text_item(
                (1, (10.0, 10.0, 20.0, 20.0)),
                (1, (70.0, 70.0, 80.0, 80.0)),
            )
        ],
        full_page_table("full-page-table"),
    )

    assert ownership.decisions == ()


def test_retains_multiple_regions_spanning_physical_pages() -> None:
    ownership = ownership_for(
        [
            text_item(
                (1, (10.0, 10.0, 20.0, 20.0)),
                (2, (10.0, 10.0, 20.0, 20.0)),
            )
        ],
        full_page_table("page-1-table", page=1),
        full_page_table("page-2-table", page=2),
    )

    assert ownership.decisions == ()


def test_requires_one_table_to_contain_every_text_region() -> None:
    ownership = ownership_for(
        [
            text_item(
                (1, (10.0, 10.0, 20.0, 20.0)),
                (1, (70.0, 70.0, 80.0, 80.0)),
            )
        ],
        full_page_table("lower-left"),
        full_page_table("upper-right", bbox=(55.0, 55.0, 95.0, 95.0)),
    )

    assert ownership.table_id_by_text_pointer == {}


def test_retains_mixed_valid_and_rejected_provenance() -> None:
    ownership = ownership_for(
        [
            text_item(
                (1, (10.0, 10.0, 20.0, 20.0)),
                (1, (-10.0, 10.0, -5.0, 20.0)),
            )
        ],
        full_page_table(),
    )

    assert ownership.table_id_by_text_pointer == {}


@pytest.mark.parametrize(
    "bbox",
    [
        (40.0, 40.0, 50.0, 50.0),
        (70.0, 70.0, 80.0, 80.0),
    ],
    ids=["partially-contained", "outside"],
)
def test_retains_text_not_fully_contained(
    bbox: tuple[float, float, float, float],
) -> None:
    ownership = ownership_for([text_item((1, bbox))], full_page_table())

    assert ownership.table_id_by_text_pointer == {}


def test_retains_matching_geometry_from_the_wrong_page() -> None:
    ownership = ownership_for(
        [text_item((2, (10.0, 10.0, 20.0, 20.0)))],
        full_page_table(page=1),
    )

    assert ownership.table_id_by_text_pointer == {}


def test_retains_text_for_non_full_page_table() -> None:
    layout_table = replace(full_page_table(), region_id="layout_001")

    ownership = ownership_for(
        [text_item((1, (10.0, 10.0, 20.0, 20.0)))],
        layout_table,
    )

    assert layout_table.route == "layout_regions"
    assert ownership.table_id_by_text_pointer == {}


def test_retains_document_index_and_furniture_text() -> None:
    ownership = ownership_for(
        [
            text_item((1, (10.0, 10.0, 20.0, 20.0))),
            text_item((1, (10.0, 10.0, 20.0, 20.0)), content_layer="furniture"),
        ],
        full_page_table(),
        document_index_descendants={"#/texts/0"},
    )

    assert ownership.table_id_by_text_pointer == {}


def test_retains_text_when_two_tables_are_equally_plausible_owners() -> None:
    ownership = ownership_for(
        [text_item((1, (10.0, 10.0, 20.0, 20.0)))],
        full_page_table("table-a"),
        full_page_table("table-b"),
    )

    assert ownership.table_id_by_text_pointer == {}
