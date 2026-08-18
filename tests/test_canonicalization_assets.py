"""Focused tests for deterministic canonical asset registration."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.canonical_extraction.assets import materialize_assets
from er_commons.canonical_extraction.context import (
    CanonicalIds,
    MaterializationContext,
)
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.tables import (
    CleanTableCell,
    ProducerTable,
    ProducerTableBundle,
    ProducerTableFamily,
    TableCleanupEvidence,
)
from er_commons.canonical_extraction.traversal import TraversalResult

EXTRACTION_ID = f"exv1-{'b' * 64}"


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _context() -> MaterializationContext:
    ids = CanonicalIds(
        extraction_id=EXTRACTION_ID,
        source_id="deir_appendix_p",
        document_id=f"{EXTRACTION_ID}/document/deir_appendix_p",
        page_ids={},
        block_id_by_pointer={},
        table_id_by_producer={},
        family_id_by_producer={},
        figure_id_by_pointer={},
        image_id_by_pointer={},
        section_id_by_layer={},
    )
    traversal = TraversalResult(
        events=(),
        emitted_text_pointers=frozenset(),
        suppressed_text_pointers=frozenset(),
        invalid_geometry_text_pointers=frozenset(),
        suppressed_picture_furniture_pointers=frozenset(),
        zero_table_pointers=frozenset(),
    )
    return MaterializationContext(
        ids=ids,
        page_sizes={},
        traversal=traversal,
        block_events=(),
        figure_pointers=(),
        table_event_by_id={},
        document_index_descendants=frozenset(),
        all_text_pointers=frozenset(),
        accounted_text_pointers=frozenset(),
        invalid_text_provenance=(),
    )


def _fixture(
    data_root: Path,
) -> tuple[CanonicalizationInputs, ProducerTableBundle, bytes, bytes]:
    run_root = data_root / "producer_run"
    document_root = run_root / "documents" / "deir_appendix_p"
    producer_root = document_root / "producer"
    tables_root = producer_root / "tables"
    table_id = "producer_table_1"
    table_relative_root = f"pages/page_00001/tables/{table_id}"

    _write(producer_root / "docling/document.json", b'{"document":true}\n')
    _write(producer_root / "docling/conversion_pages.json", b'{"pages":[]}\n')
    _write(producer_root / "routing/page_routes.jsonl", b'{"page":1}\n')
    _write(tables_root / f"{table_relative_root}/table.json", b'{"table":true}\n')
    _write(tables_root / f"{table_relative_root}/cells.json", b"[]\n")
    _write(tables_root / f"{table_relative_root}/raw.csv", b"cell\n")
    _write(tables_root / f"{table_relative_root}/table.csv", b"cell\n")
    _write(tables_root / "family_assignments.jsonl", b'{"family":"one"}\n')
    _write(tables_root / "table_families.json", b'{"families":[]}\n')

    picture_bytes = b"\x89PNG\r\nfixture"
    picture_relative = "documents/deir_appendix_p/assets/figures/p00001.png"
    _write(run_root / picture_relative, picture_bytes)

    clean_csv_sha256 = _sha256(b"cell\n")
    table = ProducerTable(
        table_id=table_id,
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
        raw_csv_path=f"{table_relative_root}/raw.csv",
        clean_csv_path=f"{table_relative_root}/table.csv",
        clean_csv_sha256=clean_csv_sha256,
        cells_path=f"{table_relative_root}/cells.json",
        table_record_path=f"{table_relative_root}/table.json",
        family_id="producer_family_1",
    )
    family = ProducerTableFamily(
        family_id="producer_family_1",
        table_ids=(table_id,),
        evidence=("singleton",),
    )
    inputs = cast(
        CanonicalizationInputs,
        SimpleNamespace(
            document_root=document_root,
            producer_run_root=run_root,
            document={"pictures": [{}]},
            asset_inventory={
                "assets": [
                    {
                        "raw_object_ref": "#/pictures/0",
                        "path": picture_relative,
                        "sha256": _sha256(picture_bytes),
                        "byte_size": len(picture_bytes),
                    }
                ]
            },
        ),
    )
    return (
        inputs,
        ProducerTableBundle(tables=(table,), families=(family,), region_mappings=()),
        picture_bytes,
        clean_csv_sha256.encode(),
    )


def test_asset_catalog_preserves_registration_order_and_generated_bytes(
    tmp_path: Path,
) -> None:
    inputs, table_bundle, _picture_bytes, clean_csv_digest = _fixture(tmp_path)
    candidate_root = tmp_path / "candidate"

    catalog = materialize_assets(
        data_root=tmp_path,
        candidate_root=candidate_root,
        context=_context(),
        inputs=inputs,
        table_bundle=table_bundle,
    )

    assert [record["role"] for record in catalog.records] == [
        "raw_docling_json",
        "conversion_pages_json",
        "routing_jsonl",
        "raw_table_json",
        "raw_table_cells_json",
        "raw_table_csv",
        "clean_table_csv",
        "clean_table_json",
        "clean_table_cells_json",
        "table_family_assignments_jsonl",
        "table_families_json",
        "content_image",
    ]
    assert catalog.raw_docling_asset_id.endswith("/raw_docling_json/ast000001")
    assert catalog.family_assignments_asset_id.endswith("/table_family_assignments_jsonl/ast000010")
    assert catalog.picture_asset_ids_by_pointer["#/pictures/0"].endswith("/content_image/ast000012")
    assert len(catalog.table_raw_links_by_id["producer_table_1"]) == 6

    clean_table_path = (
        candidate_root / "documents/deir_appendix_p/assets/tables/producer_table_1/table.json"
    )
    expected_table = (
        b'{"clean_csv_sha256":"' + clean_csv_digest + b'","cleanup":{"effective_column_count":1,'
        b'"removed_filename_row_indices":[],"removed_footer_row_indices":[],'
        b'"retained_column_indices":[0]},"producer_table_id":"producer_table_1",'
        b'"schema_version":"er_commons.clean_table.v1","shape":[1,1]}\n'
    )
    assert clean_table_path.read_bytes() == expected_table
    clean_cells_path = clean_table_path.with_name("cells.json")
    assert clean_cells_path.read_bytes() == (
        b'[{"bbox_pdf_points_bottom_left":[1.0,2.0,3.0,4.0],'
        b'"column_index":0,"row_index":0,"text":"cell"}]\n'
    )


def test_tableformer_fallback_assets_preserve_parser_lineage(tmp_path: Path) -> None:
    inputs, table_bundle, _picture_bytes, _clean_csv_digest = _fixture(tmp_path)
    fallback_table = replace(table_bundle.tables[0], parser="tableformer_accurate")

    catalog = materialize_assets(
        data_root=tmp_path,
        candidate_root=tmp_path / "candidate",
        context=_context(),
        inputs=inputs,
        table_bundle=replace(table_bundle, tables=(fallback_table,)),
    )

    raw_table_assets = [
        asset
        for asset in catalog.records
        if asset["role"] in {"raw_table_json", "raw_table_cells_json", "raw_table_csv"}
    ]
    assert {asset["producer"] for asset in raw_table_assets} == {"tableformer_fallback"}
    assert {link["producer"] for link in catalog.table_raw_links_by_id["producer_table_1"][:3]} == {
        "tableformer_fallback"
    }


def test_asset_catalog_lookup_mappings_are_read_only(tmp_path: Path) -> None:
    inputs, table_bundle, _picture_bytes, _clean_csv_digest = _fixture(tmp_path)
    catalog = materialize_assets(
        data_root=tmp_path,
        candidate_root=tmp_path / "candidate",
        context=_context(),
        inputs=inputs,
        table_bundle=table_bundle,
    )

    with pytest.raises(TypeError):
        catalog.picture_asset_ids_by_pointer["#/pictures/0"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        catalog.table_raw_links_by_id["producer_table_1"] = ()  # type: ignore[index]
