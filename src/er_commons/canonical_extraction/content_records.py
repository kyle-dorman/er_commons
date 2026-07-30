"""Build canonical content records from one verified materialization context."""

from __future__ import annotations

from collections import defaultdict

from er_commons.canonical_extraction.assets import AssetCatalog, raw_link
from er_commons.canonical_extraction.constants import BLOCK_TYPE_BY_LABEL, SCHEMA_VERSION
from er_commons.canonical_extraction.context import MaterializationContext
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.provenance import project_regions, table_region
from er_commons.canonical_extraction.record_sets import (
    ContentRecordSet,
    JsonRecord,
    MappedRecord,
    MaterializationReport,
)
from er_commons.canonical_extraction.tables import ProducerTable, ProducerTableBundle
from er_commons.canonical_extraction.traversal import TraversalEvent


def _blocks(
    *,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
    assets: AssetCatalog,
) -> tuple[tuple[JsonRecord, ...], tuple[JsonRecord, ...]]:
    """Build text blocks and return rejected provenance separately."""
    records: list[JsonRecord] = []
    rejected: list[JsonRecord] = []
    for sequence, event in enumerate(context.block_events, start=1):
        index = int(event.pointer.rsplit("/", 1)[1])
        item = inputs.document["texts"][index]
        projection = project_regions(
            item=item,
            pointer=event.pointer,
            page_ids=dict(context.page_ids),
            page_sizes=dict(context.page_sizes),
        )
        rejected.extend(projection.rejected)
        if not projection.regions:
            raise ContractError(f"text has no valid canonical region: pointer={event.pointer}")
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": context.block_id_by_pointer[event.pointer],
                "document_id": context.document_id,
                "section_id": context.section_id_by_layer[event.content_layer],
                "sequence": sequence,
                "content_layer": event.content_layer,
                "block_type": BLOCK_TYPE_BY_LABEL.get(item["label"], "other"),
                "raw_text": item["orig"],
                "canonical_text": item["orig"],
                "normalization_operations": ["none"],
                "regions": list(projection.regions),
                "raw_links": [
                    raw_link(
                        "docling",
                        assets.raw_docling_asset_id,
                        event.pointer,
                        provenance_index,
                    )
                    for provenance_index in range(len(item["prov"]))
                ],
            }
        )
    return tuple(records), tuple(rejected)


def _caption_ids_by_owner(
    *,
    context: MaterializationContext,
    document: JsonRecord,
) -> dict[str, tuple[str, ...]]:
    """Resolve producer caption pointers to emitted canonical block IDs."""
    caption_ids: dict[str, list[str]] = defaultdict(list)
    owners = [
        *[(f"#/tables/{index}", item) for index, item in enumerate(document["tables"])],
        *[(f"#/pictures/{index}", item) for index, item in enumerate(document["pictures"])],
    ]
    for pointer, item in owners:
        for caption in item.get("captions", []):
            caption_pointer = caption["$ref"]
            if caption_pointer not in context.block_id_by_pointer:
                raise ContractError(
                    f"caption was not emitted: owner={pointer}, caption={caption_pointer}"
                )
            caption_ids[pointer].append(context.block_id_by_pointer[caption_pointer])
    return {owner: tuple(ids) for owner, ids in caption_ids.items()}


def _cleanup_operations(table: ProducerTable) -> list[str]:
    """Describe only cleanup operations actually applied to a producer table."""
    operations: list[str] = []
    if table.cleanup.removed_footer_row_indices:
        operations.append("remove_footer_rows")
    if table.cleanup.removed_filename_row_indices:
        operations.append("remove_filename_rows")
    if table.cleanup.retained_column_indices != tuple(range(table.shape_raw[1])):
        operations.append("remove_footer_only_columns")
    return operations or ["none"]


def _tables(
    *,
    context: MaterializationContext,
    table_bundle: ProducerTableBundle,
    assets: AssetCatalog,
    caption_ids: dict[str, tuple[str, ...]],
) -> tuple[JsonRecord, ...]:
    """Build canonical rectangular tables from the reconciled clean grid."""
    records: list[JsonRecord] = []
    for sequence, table in enumerate(table_bundle.tables, start=1):
        event = context.table_event_by_id[table.table_id]
        cells = [
            {
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "producer_row_index": cell.row_index,
                "producer_column_index": table.cleanup.retained_column_indices[cell.column_index],
                "producer_normalized_text": cell.text,
                "canonical_text": cell.text,
                "region": table_region(
                    cell.bbox_pdf_points_bottom_left,
                    table.physical_pdf_page,
                    dict(context.page_ids),
                    dict(context.page_sizes),
                ),
            }
            for cell in table.cells
        ]
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": context.table_id_by_producer[table.table_id],
                "document_id": context.document_id,
                "section_id": context.section_id_by_layer[event.content_layer],
                "sequence": sequence,
                "table_family_id": context.family_id_by_producer[table.family_id],
                "producer_table_id": table.table_id,
                "parser": table.parser,
                "shape": list(table.shape_clean),
                "cells": cells,
                "caption_block_ids": list(caption_ids.get(event.pointer, ())),
                "regions": [
                    table_region(
                        table.bbox_pdf_points_bottom_left,
                        table.physical_pdf_page,
                        dict(context.page_ids),
                        dict(context.page_sizes),
                    )
                ],
                "raw_links": list(assets.table_raw_links_by_id[table.table_id]),
                "cleanup_operations": _cleanup_operations(table),
            }
        )
    return tuple(records)


def _table_families(
    *,
    context: MaterializationContext,
    table_bundle: ProducerTableBundle,
) -> tuple[JsonRecord, ...]:
    """Build exact producer-owned complete-document table families."""
    return tuple(
        {
            "schema_version": SCHEMA_VERSION,
            "extraction_id": context.extraction_id,
            "id": context.family_id_by_producer[family.family_id],
            "document_id": context.document_id,
            "sequence": sequence,
            "document_scope_complete": True,
            "member_table_ids": [
                context.table_id_by_producer[table_id] for table_id in family.table_ids
            ],
            "evidence": list(family.evidence),
        }
        for sequence, family in enumerate(table_bundle.families, start=1)
    )


def _figures_and_images(
    *,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
    assets: AssetCatalog,
    caption_ids: dict[str, tuple[str, ...]],
) -> tuple[
    tuple[JsonRecord, ...],
    tuple[JsonRecord, ...],
    tuple[JsonRecord, ...],
]:
    """Build figure/image pairs and return any rejected picture provenance."""
    figures: list[JsonRecord] = []
    images: list[JsonRecord] = []
    rejected: list[JsonRecord] = []
    for sequence, pointer in enumerate(context.figure_pointers, start=1):
        item = inputs.document["pictures"][int(pointer.rsplit("/", 1)[1])]
        projection = project_regions(
            item=item,
            pointer=pointer,
            page_ids=dict(context.page_ids),
            page_sizes=dict(context.page_sizes),
        )
        rejected.extend(projection.rejected)
        if not projection.regions:
            raise ContractError(f"picture has no valid canonical region: pointer={pointer}")
        figure_link = raw_link(
            "docling",
            assets.raw_docling_asset_id,
            pointer,
            0,
        )
        figures.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": context.figure_id_by_pointer[pointer],
                "document_id": context.document_id,
                "section_id": context.section_id_by_layer[item.get("content_layer", "body")],
                "sequence": sequence,
                "caption_block_ids": list(caption_ids.get(pointer, ())),
                "image_ids": [context.image_id_by_pointer[pointer]],
                "regions": list(projection.regions),
                "raw_links": [figure_link],
            }
        )
        images.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": context.image_id_by_pointer[pointer],
                "document_id": context.document_id,
                "sequence": sequence,
                "asset_id": assets.picture_asset_ids_by_pointer[pointer],
                "regions": list(projection.regions),
                "raw_links": [
                    raw_link(
                        "docling",
                        assets.raw_docling_asset_id,
                        f"{pointer}/image",
                    )
                ],
            }
        )
    return tuple(figures), tuple(images), tuple(rejected)


def _event_id(context: MaterializationContext, event: TraversalEvent) -> str:
    """Resolve one traversal event to its deterministic canonical content ID."""
    if event.kind == "text":
        return context.block_id_by_pointer[event.pointer]
    if event.kind == "table" and event.producer_table_id is not None:
        return context.table_id_by_producer[event.producer_table_id]
    if event.kind == "figure":
        return context.figure_id_by_pointer[event.pointer]
    raise ContractError(
        "unsupported traversal event: "
        f"kind={event.kind}, pointer={event.pointer}, "
        f"producer_table_id={event.producer_table_id}"
    )


def _sections_and_page_content(
    *,
    context: MaterializationContext,
    assets: AssetCatalog,
    blocks: tuple[JsonRecord, ...],
    tables: tuple[JsonRecord, ...],
    figures: tuple[JsonRecord, ...],
) -> tuple[tuple[JsonRecord, ...], dict[int, tuple[str, ...]]]:
    """Build synthetic layer roots and exact page reading-order membership."""
    regions_by_content_id = {
        record["id"]: record["regions"] for record in [*blocks, *tables, *figures]
    }
    page_content: dict[int, list[str]] = {page: [] for page in context.page_ids}
    for event in context.traversal.events:
        content_id = _event_id(context, event)
        for region in regions_by_content_id[content_id]:
            page = context.page_number_by_id[region["page_id"]]
            if content_id not in page_content[page]:
                page_content[page].append(content_id)

    sections: list[JsonRecord] = []
    for sequence, layer in enumerate(("body", "furniture"), start=1):
        if layer not in context.section_id_by_layer:
            continue
        children = [
            _event_id(context, event)
            for event in context.traversal.events
            if event.content_layer == layer
        ]
        sections.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": context.section_id_by_layer[layer],
                "document_id": context.document_id,
                "sequence": sequence,
                "content_layer": layer,
                "parent_section_id": None,
                "heading_block_id": None,
                "ordered_child_ids": children,
                "raw_links": [
                    raw_link(
                        "docling",
                        assets.raw_docling_asset_id,
                        "#/body" if layer == "body" else "#/furniture",
                    )
                ],
            }
        )
    return tuple(sections), {page: tuple(content_ids) for page, content_ids in page_content.items()}


def _mapped_records(
    *,
    blocks: tuple[JsonRecord, ...],
    tables: tuple[JsonRecord, ...],
    table_families: tuple[JsonRecord, ...],
    figures: tuple[JsonRecord, ...],
    images: tuple[JsonRecord, ...],
    assets: AssetCatalog,
) -> tuple[MappedRecord, ...]:
    """Assign lineage roles explicitly rather than parsing canonical IDs."""
    records = [
        *[
            MappedRecord(
                record_id=record["id"],
                mapping_role="text_provenance",
                raw_links=tuple(record["raw_links"]),
            )
            for record in blocks
        ],
        *[
            MappedRecord(
                record_id=record["id"],
                mapping_role="producer_table_lineage",
                raw_links=tuple(record["raw_links"]),
            )
            for record in tables
        ],
        *[
            MappedRecord(
                record_id=record["id"],
                mapping_role="derived_family_lineage",
                raw_links=(
                    raw_link(
                        "project_family_assignment",
                        assets.family_assignments_asset_id,
                        "/",
                    ),
                    raw_link(
                        "project_family_assignment",
                        assets.table_families_asset_id,
                        "/",
                    ),
                ),
            )
            for record in table_families
        ],
        *[
            MappedRecord(
                record_id=record["id"],
                mapping_role="geometry_provenance",
                raw_links=tuple(record["raw_links"]),
            )
            for record in [*figures, *images]
        ],
    ]
    return tuple(records)


def build_content_records(
    *,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
    table_bundle: ProducerTableBundle,
    assets: AssetCatalog,
) -> tuple[ContentRecordSet, MaterializationReport]:
    """Build content records and their complete accounting report."""
    blocks, rejected_text = _blocks(
        context=context,
        inputs=inputs,
        assets=assets,
    )
    caption_ids = _caption_ids_by_owner(
        context=context,
        document=inputs.document,
    )
    tables = _tables(
        context=context,
        table_bundle=table_bundle,
        assets=assets,
        caption_ids=caption_ids,
    )
    table_families = _table_families(
        context=context,
        table_bundle=table_bundle,
    )
    figures, images, rejected_pictures = _figures_and_images(
        context=context,
        inputs=inputs,
        assets=assets,
        caption_ids=caption_ids,
    )
    sections, page_content = _sections_and_page_content(
        context=context,
        assets=assets,
        blocks=blocks,
        tables=tables,
        figures=figures,
    )
    invalid_provenance = (*rejected_text, *rejected_pictures)
    content = ContentRecordSet(
        blocks=blocks,
        tables=tables,
        table_families=table_families,
        figures=figures,
        images=images,
        sections=sections,
        page_content=page_content,
        invalid_provenance=invalid_provenance,
        mapped_records=_mapped_records(
            blocks=blocks,
            tables=tables,
            table_families=table_families,
            figures=figures,
            images=images,
            assets=assets,
        ),
    )
    report = MaterializationReport(
        invalid_provenance=invalid_provenance,
        document_index_descendant_count=len(context.document_index_descendants),
        producer_text_count=len(context.all_text_pointers),
        emitted_text_count=len(context.traversal.emitted_text_pointers),
        suppressed_text_count=len(context.traversal.suppressed_text_pointers),
        producer_furniture_count=sum(
            item["content_layer"] == "furniture" for item in inputs.document["texts"]
        ),
        emitted_furniture_count=sum(block["content_layer"] == "furniture" for block in blocks),
        suppressed_picture_furniture_pointers=tuple(
            sorted(context.traversal.suppressed_picture_furniture_pointers)
        ),
    )
    return content, report
