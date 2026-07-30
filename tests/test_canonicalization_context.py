"""Focused tests for immutable canonical materialization context."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.canonical_extraction.config import (
    CanonicalizationConfig,
    load_canonicalization_config,
)
from er_commons.canonical_extraction.context import build_materialization_context
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.tables import (
    CleanTableCell,
    ProducerTable,
    ProducerTableBundle,
    ProducerTableFamily,
    RegionTableMapping,
    TableCleanupEvidence,
)

CONFIG_PATH = Path("configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json")
EXTRACTION_ID = f"exv1-{'a' * 64}"


def _document() -> dict[str, object]:
    return {
        "body": {
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/tables/0"},
                {"$ref": "#/pictures/0"},
                {"$ref": "#/pictures/1"},
            ]
        },
        "furniture": {"children": []},
        "groups": [],
        "texts": [
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
            {"content_layer": "furniture", "children": []},
            {"content_layer": "furniture", "children": []},
        ],
        "tables": [
            {
                "label": "table",
                "content_layer": "body",
                "children": [{"$ref": "#/texts/1"}],
                "captions": [],
            }
        ],
        "pictures": [
            {
                "content_layer": "body",
                "children": [{"$ref": "#/texts/4"}],
                "captions": [{"$ref": "#/texts/2"}],
                "prov": [
                    {
                        "page_no": 2,
                        "bbox": {"l": 20.0, "b": 10.0, "r": 40.0, "t": 90.0},
                    }
                ],
            },
            {
                "content_layer": "body",
                "children": [],
                "captions": [],
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {"l": 10.0, "b": 5.0, "r": 30.0, "t": 20.0},
                    }
                ],
            },
        ],
        "pages": {str(page): {"size": {"width": 612.0, "height": 792.0}} for page in range(1, 223)},
    }


def _table_bundle() -> ProducerTableBundle:
    table = ProducerTable(
        table_id="producer_table_1",
        physical_pdf_page=1,
        page_table_index=1,
        region_id="layout_001",
        parser="camelot_lattice",
        shape_raw=(1, 1),
        shape_clean=(1, 1),
        bbox_pdf_points_bottom_left=(1.0, 2.0, 3.0, 4.0),
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
                bbox_pdf_points_bottom_left=(1.0, 2.0, 3.0, 4.0),
            ),
        ),
        raw_csv_path="raw.csv",
        clean_csv_path="table.csv",
        clean_csv_sha256="0" * 64,
        cells_path="cells.json",
        table_record_path="table.json",
        family_id="producer_family_1",
    )
    family = ProducerTableFamily(
        family_id="producer_family_1",
        table_ids=("producer_table_1",),
        evidence=("singleton",),
    )
    mapping = RegionTableMapping(
        physical_pdf_page=1,
        region_id="layout_001",
        raw_object_ref="#/tables/0",
        provenance_index=0,
        bbox_pdf_points_bottom_left=(1.0, 2.0, 3.0, 4.0),
        clean_table_ids=("producer_table_1",),
        unmapped_reason=None,
    )
    return ProducerTableBundle(
        tables=(table,),
        families=(family,),
        region_mappings=(mapping,),
    )


def _config() -> CanonicalizationConfig:
    return load_canonicalization_config(CONFIG_PATH)[0]


def test_context_names_deterministic_ordering_and_ids() -> None:
    inputs = cast(
        CanonicalizationInputs,
        SimpleNamespace(document=_document()),
    )

    context = build_materialization_context(
        config=_config(),
        inputs=inputs,
        identity={"extraction_id": EXTRACTION_ID},
        table_bundle=_table_bundle(),
    )

    assert list(context.page_ids) == list(range(1, 223))
    assert context.document_id == f"{EXTRACTION_ID}/document/deir_appendix_p"
    assert [event.pointer for event in context.block_events] == [
        "#/texts/0",
        "#/texts/2",
        "#/texts/3",
    ]
    assert context.block_id_by_pointer["#/texts/2"].endswith("/blk000002")
    assert context.table_id_by_producer["producer_table_1"].endswith("/tbl000001")
    assert context.family_id_by_producer["producer_family_1"].endswith("/fam000001")
    assert context.figure_pointers == ("#/pictures/1", "#/pictures/0")
    assert context.figure_id_by_pointer["#/pictures/1"].endswith("/fig000001")
    assert context.image_id_by_pointer["#/pictures/0"].endswith("/img000002")
    assert context.section_id_by_layer["body"].endswith("/sec000001")
    assert context.section_id_by_layer["furniture"].endswith("/sec000002")
    assert set(context.table_event_by_id) == {"producer_table_1"}
    assert context.accounted_text_pointers == context.all_text_pointers


def test_context_copies_and_freezes_cross_stage_mappings() -> None:
    inputs = cast(
        CanonicalizationInputs,
        SimpleNamespace(document=_document()),
    )
    context = build_materialization_context(
        config=_config(),
        inputs=inputs,
        identity={"extraction_id": EXTRACTION_ID},
        table_bundle=_table_bundle(),
    )

    with pytest.raises(TypeError):
        context.page_ids[1] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        context.block_id_by_pointer["#/texts/0"] = "changed"  # type: ignore[index]
