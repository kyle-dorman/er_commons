"""Canonical-only table projection over immutable producer evidence."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.canonical_extraction.assets import AssetCatalog
from er_commons.canonical_extraction.candidate import canonicalization_warnings
from er_commons.canonical_extraction.context import MaterializationContext
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.record_sets import MaterializationReport
from er_commons.canonical_extraction.support_records import _table_stage_observations
from er_commons.canonical_extraction.table_projection import (
    DOCUMENT_INDEX_UNMAPPED_REASON,
    project_canonical_table_bundle,
)
from er_commons.canonical_extraction.tables import (
    CleanTableCell,
    ProducerTable,
    ProducerTableBundle,
    ProducerTableFamily,
    RegionTableMapping,
    TableCleanupEvidence,
)
from er_commons.canonical_extraction.traversal import traverse_docling_document
from er_commons.semantic_materialization import producer_evidence


def _table(table_id: str, family_id: str, page: int) -> ProducerTable:
    return ProducerTable(
        table_id=table_id,
        physical_pdf_page=page,
        page_table_index=1,
        region_id="layout_001",
        parser="tableformer_accurate",
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
        family_id=family_id,
    )


def _mapping(pointer: str, table_id: str | None, page: int) -> RegionTableMapping:
    return RegionTableMapping(
        physical_pdf_page=page,
        region_id="layout_001",
        raw_object_ref=pointer,
        provenance_index=0,
        bbox_pdf_points_bottom_left=(1.0, 2.0, 3.0, 4.0),
        clean_table_ids=() if table_id is None else (table_id,),
        unmapped_reason="no_clean_table_match" if table_id is None else None,
    )


def _bundle() -> ProducerTableBundle:
    index = _table("index_table", "index_family", 1)
    ordinary = _table("ordinary_table", "ordinary_family", 2)
    return ProducerTableBundle(
        tables=(index, ordinary),
        families=(
            ProducerTableFamily(
                family_id="index_family",
                table_ids=("index_table",),
                evidence=("singleton",),
            ),
            ProducerTableFamily(
                family_id="ordinary_family",
                table_ids=("ordinary_table",),
                evidence=("singleton",),
            ),
        ),
        region_mappings=(
            _mapping("#/tables/0", "index_table", 1),
            _mapping("#/tables/1", "ordinary_table", 2),
            _mapping("#/tables/2", None, 3),
        ),
    )


def _document() -> dict[str, object]:
    return {
        "tables": [
            {"label": "document_index"},
            {"label": "table"},
            {"label": "document_index"},
        ]
    }


def test_excludes_mapped_document_index_and_preserves_ordinary_table() -> None:
    original = _bundle()
    projected = project_canonical_table_bundle(_document(), original)

    assert [table.table_id for table in projected.tables] == ["ordinary_table"]
    assert [family.family_id for family in projected.families] == ["ordinary_family"]
    assert projected.region_mappings[0].clean_table_ids == ()
    assert projected.region_mappings[0].unmapped_reason == DOCUMENT_INDEX_UNMAPPED_REASON
    assert projected.region_mappings[1] is original.region_mappings[1]
    assert projected.region_mappings[2].unmapped_reason == DOCUMENT_INDEX_UNMAPPED_REASON
    assert original.region_mappings[0].clean_table_ids == ("index_table",)
    assert [table.table_id for table in original.tables] == ["index_table", "ordinary_table"]


def test_projection_is_deterministic() -> None:
    first = project_canonical_table_bundle(_document(), _bundle())
    second = project_canonical_table_bundle(_document(), first)

    assert first == second


def test_projected_traversal_emits_index_text_and_replaces_only_ordinary_table() -> None:
    document = {
        "pages": {"1": {"size": {"width": 100.0, "height": 100.0}}},
        "body": {"children": [{"$ref": "#/tables/0"}, {"$ref": "#/tables/1"}]},
        "groups": [],
        "texts": [
            {"content_layer": "body", "children": []},
            {"content_layer": "body", "children": []},
        ],
        "tables": [
            {
                "label": "document_index",
                "content_layer": "body",
                "children": [{"$ref": "#/texts/0"}],
                "captions": [],
            },
            {
                "label": "table",
                "content_layer": "body",
                "children": [{"$ref": "#/texts/1"}],
                "captions": [],
            },
            {"label": "document_index", "children": [], "captions": []},
        ],
        "pictures": [],
    }
    projected = project_canonical_table_bundle(document, _bundle())
    mapped = {
        mapping.raw_object_ref: mapping.clean_table_ids for mapping in projected.region_mappings
    }

    traversal = traverse_docling_document(document, mapped)

    assert traversal.emitted_text_pointers == {"#/texts/0"}
    assert traversal.suppressed_text_pointers == {"#/texts/1"}
    assert [event.producer_table_id for event in traversal.events if event.kind == "table"] == [
        "ordinary_table"
    ]


def test_projected_document_index_diagnostics_explain_text_preservation() -> None:
    projected = project_canonical_table_bundle(_document(), _bundle())
    context = cast(
        MaterializationContext,
        SimpleNamespace(
            extraction_id=f"exv1-{'a' * 64}",
            source_id="deir_main",
            page_ids={1: "page-1", 2: "page-2", 3: "page-3"},
            table_id_by_producer={"ordinary_table": "canonical-ordinary-table"},
        ),
    )
    assets = cast(
        AssetCatalog,
        SimpleNamespace(raw_docling_asset_id="raw-docling-asset"),
    )

    observations, _ = _table_stage_observations(
        context=context,
        table_bundle=projected,
        assets=assets,
    )

    index_observation = observations[0]
    assert index_observation["canonical_table_ids"] == []
    assert index_observation["unmapped_reason"] == DOCUMENT_INDEX_UNMAPPED_REASON
    assert index_observation["warnings"] == [
        "Parser evidence for #/tables/0 remains in the sealed producer; "
        "the document index is preserved as canonical text."
    ]
    ordinary_observation = observations[1]
    assert ordinary_observation["canonical_table_ids"] == ["canonical-ordinary-table"]
    assert ordinary_observation["unmapped_reason"] is None
    assert ordinary_observation["warnings"] == []

    inputs = cast(
        CanonicalizationInputs,
        SimpleNamespace(
            conversion_observation_record=SimpleNamespace(captured_python_warnings=[]),
        ),
    )
    report = cast(MaterializationReport, SimpleNamespace(invalid_provenance=()))
    warnings = canonicalization_warnings(inputs, projected, report)

    assert "document index preserved as text: #/tables/0 provenance 0" in warnings
    assert "zero table mapping: #/tables/0 provenance 0" not in warnings


def test_rejects_mixed_document_index_and_ordinary_family() -> None:
    bundle = _bundle()
    mixed = ProducerTableFamily(
        family_id="mixed_family",
        table_ids=("index_table", "ordinary_table"),
        evidence=("cross_page_continuation",),
    )
    tables = tuple(replace(table, family_id="mixed_family") for table in bundle.tables)

    with pytest.raises(ContractError, match="split a mixed table family"):
        project_canonical_table_bundle(
            _document(),
            replace(bundle, tables=tables, families=(mixed,)),
        )


@pytest.mark.parametrize("pointer", ["#/texts/0", "#/tables/not-an-index", "#/tables/99"])
def test_rejects_invalid_or_unknown_region_pointer(pointer: str) -> None:
    bundle = _bundle()
    mappings = (replace(bundle.region_mappings[0], raw_object_ref=pointer),)

    with pytest.raises(ContractError, match="Docling table pointer"):
        project_canonical_table_bundle(
            _document(),
            replace(bundle, region_mappings=mappings),
        )


def test_rejects_duplicate_region_pointer() -> None:
    bundle = _bundle()
    duplicate = replace(bundle.region_mappings[1], raw_object_ref="#/tables/0")

    with pytest.raises(ContractError, match="duplicate Docling table pointer"):
        project_canonical_table_bundle(
            _document(),
            replace(bundle, region_mappings=(bundle.region_mappings[0], duplicate)),
        )


def test_semantic_replacement_dispositions_use_projected_table_view(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    document = {
        "pages": {"1": {"size": {"width": 100.0, "height": 100.0}}},
        "tables": [
            {
                "label": "document_index",
                "children": [{"$ref": "#/texts/0"}],
                "captions": [],
            },
            {
                "label": "table",
                "children": [{"$ref": "#/texts/1"}],
                "captions": [],
            },
            {"label": "document_index", "children": [], "captions": []},
        ],
        "texts": [
            {
                "children": [],
                "prov": [{"page_no": 1, "bbox": {"l": 1.0, "b": 1.0, "r": 2.0, "t": 2.0}}],
            },
            {
                "children": [],
                "prov": [{"page_no": 1, "bbox": {"l": 2.0, "b": 2.0, "r": 3.0, "t": 3.0}}],
            },
            {
                "children": [],
                "prov": [
                    {
                        "page_no": 1,
                        "bbox": {"l": -10.0, "b": 2.0, "r": -3.0, "t": 3.0},
                    }
                ],
            },
        ],
        "groups": [],
        "pictures": [],
    }
    monkeypatch.setattr(producer_evidence, "load_producer_table_bundle", lambda _root: _bundle())

    dispositions = producer_evidence.replacement_dispositions(
        baseline_document=document,
        producer_root=tmp_path,
        key_by_pointer={
            "#/texts/0": "index-key",
            "#/texts/1": "table-key",
            "#/texts/2": "invalid-key",
        },
        relevant_keys={"index-key", "table-key", "invalid-key"},
    )

    assert dispositions == {
        "table-key": "canonical_table_replacement_descendant",
        "invalid-key": "canonical_invalid_provenance_suppressed",
    }
