"""Build document, page, observation, and raw-lineage record families."""

from __future__ import annotations

from collections import defaultdict

from er_commons.canonical_extraction.assets import AssetCatalog, raw_link
from er_commons.canonical_extraction.config import CanonicalizationConfig
from er_commons.canonical_extraction.constants import SCHEMA_VERSION
from er_commons.canonical_extraction.context import MaterializationContext
from er_commons.canonical_extraction.identifiers import make_record_id
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.record_sets import (
    ContentRecordSet,
    JsonRecord,
    SupportRecordSet,
)
from er_commons.canonical_extraction.tables import ProducerTableBundle


def _routing_observations(
    *,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
    assets: AssetCatalog,
) -> tuple[JsonRecord, ...]:
    """Project the producer's ordered page-routing evidence."""
    records: list[JsonRecord] = []
    for route_record in inputs.page_route_records:
        route = route_record.model_dump(mode="json", exclude_unset=True)
        page = route["physical_pdf_page"]
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": make_record_id(
                    context.extraction_id,
                    "routing-observation",
                    context.source_id,
                    f"route-p{page:06d}",
                ),
                "page_id": context.page_ids[page],
                "status": route["status"],
                "route": route["route"],
                "native_text_features": {
                    key: value
                    for key, value in route.items()
                    if key
                    in {
                        "coordinate_key_count",
                        "digit_fraction",
                        "native_character_count",
                        "native_text_rectangle_count",
                        "nonempty_line_count",
                        "nonspace_character_count",
                        "nonspace_characters_per_square_point",
                        "numeric_table_bearing",
                        "strict_table_dominant",
                        "text_height_fraction",
                        "text_width_fraction",
                    }
                },
                "strict_checks": route["strict_checks"],
                "numeric_checks": route["numeric_checks"],
                "docling_table_region_raw_links": [
                    raw_link(
                        "docling",
                        assets.raw_docling_asset_id,
                        item["raw_object_ref"],
                        item["provenance_index"],
                    )
                    for item in route["layout_table_observations"]
                ],
                "warnings": [],
            }
        )
    return tuple(records)


def _table_stage_observations(
    *,
    context: MaterializationContext,
    table_bundle: ProducerTableBundle,
    assets: AssetCatalog,
) -> tuple[tuple[JsonRecord, ...], dict[int, tuple[str, ...]]]:
    """Project each producer table-region mapping and index it by page."""
    records: list[JsonRecord] = []
    ids_by_page: dict[int, list[str]] = defaultdict(list)
    for ordinal, mapping in enumerate(table_bundle.region_mappings, start=1):
        page = mapping.physical_pdf_page
        stage_id = make_record_id(
            context.extraction_id,
            "table-stage-observation",
            context.source_id,
            f"stage-p{page:06d}-o{ordinal:06d}",
        )
        ids_by_page[page].append(stage_id)
        warning = (
            []
            if mapping.clean_table_ids
            else [
                f"No clean table matched {mapping.raw_object_ref} "
                f"provenance {mapping.provenance_index}."
            ]
        )
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": stage_id,
                "page_id": context.page_ids[page],
                "status": "complete" if mapping.clean_table_ids else "complete_with_warnings",
                "route": "layout_regions",
                "source_region_raw_link": raw_link(
                    "docling",
                    assets.raw_docling_asset_id,
                    mapping.raw_object_ref,
                    mapping.provenance_index,
                ),
                "canonical_table_ids": [
                    context.table_id_by_producer[table_id] for table_id in mapping.clean_table_ids
                ],
                "unmapped_reason": mapping.unmapped_reason,
                "cleanup_complete": True,
                "footer_ownership_complete": True,
                "family_assignment_complete": True,
                "parser_diagnostics": {
                    "region_id": mapping.region_id,
                    "bbox_pdf_points_bottom_left": list(mapping.bbox_pdf_points_bottom_left),
                },
                "warnings": warning,
            }
        )
    return tuple(records), {page: tuple(stage_ids) for page, stage_ids in ids_by_page.items()}


def _conversion_observations(
    *,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
    assets: AssetCatalog,
) -> tuple[tuple[JsonRecord, ...], str]:
    """Project the complete producer conversion as one canonical observation."""
    conversion_id = make_record_id(
        context.extraction_id,
        "conversion-observation",
        context.source_id,
        "conv000001",
    )
    producer_runtime = inputs.producer_identity["identity"]["runtime"]
    observation = inputs.conversion_observation_record
    return (
        (
            {
                "schema_version": SCHEMA_VERSION,
                "extraction_id": context.extraction_id,
                "id": conversion_id,
                "document_id": context.document_id,
                "first_physical_page": 1,
                "last_physical_page": 222,
                "status": observation.status,
                "pipeline_class": producer_runtime["pipeline_class"],
                "backend_class": producer_runtime["backend_class"],
                "raw_document_asset_id": assets.raw_docling_asset_id,
                "errors": observation.errors,
                "warnings": observation.captured_python_warnings,
            },
        ),
        conversion_id,
    )


def _document_and_pages(
    *,
    context: MaterializationContext,
    config: CanonicalizationConfig,
    inputs: CanonicalizationInputs,
    content: ContentRecordSet,
    conversion_id: str,
    stage_ids_by_page: dict[int, tuple[str, ...]],
) -> tuple[tuple[JsonRecord, ...], tuple[JsonRecord, ...]]:
    """Build the selected document and all physical-page records."""
    source = inputs.selected_source.model_dump(mode="json", exclude_unset=True)
    document = {
        "schema_version": SCHEMA_VERSION,
        "extraction_id": context.extraction_id,
        "id": context.document_id,
        "source_release_version": config.source_release_version,
        "source_manifest_sha256": (inputs.producer_completion_record.source_manifest_sha256),
        "source_id": context.source_id,
        "source_sha256": source["sha256"],
        "source_role": source["source_role"],
        "title": source["official_title"],
        "page_count": source["pdf_page_count"],
        "page_ids": list(context.page_ids.values()),
        "conversion_observation_ids": [conversion_id],
        "source_manifest_warnings": source["warnings"],
        "source_edition_override": None,
        "document_scope_complete": True,
    }
    pages = tuple(
        {
            "schema_version": SCHEMA_VERSION,
            "extraction_id": context.extraction_id,
            "id": context.page_ids[page],
            "document_id": context.document_id,
            "physical_page_number": page,
            "printed_page_label": None,
            "width_pdf_points": context.page_sizes[page][0],
            "height_pdf_points": context.page_sizes[page][1],
            "rotation_degrees": 0,
            "source_edition_override": None,
            "ordered_content_ids": list(content.page_content[page]),
            "routing_observation_id": make_record_id(
                context.extraction_id,
                "routing-observation",
                context.source_id,
                f"route-p{page:06d}",
            ),
            "table_stage_observation_ids": list(stage_ids_by_page.get(page, ())),
        }
        for page in context.page_ids
    )
    return (document,), pages


def _raw_mappings(
    *,
    context: MaterializationContext,
    content: ContentRecordSet,
) -> tuple[JsonRecord, ...]:
    """Serialize explicit content-lineage classifications without ID parsing."""
    return tuple(
        {
            "schema_version": SCHEMA_VERSION,
            "extraction_id": context.extraction_id,
            "id": make_record_id(
                context.extraction_id,
                "raw-mapping",
                context.source_id,
                f"map{sequence:06d}",
            ),
            "canonical_record_id": mapped.record_id,
            "mapping_role": mapped.mapping_role,
            "raw_links": list(mapped.raw_links),
        }
        for sequence, mapped in enumerate(content.mapped_records, start=1)
    )


def build_support_records(
    *,
    context: MaterializationContext,
    config: CanonicalizationConfig,
    inputs: CanonicalizationInputs,
    table_bundle: ProducerTableBundle,
    assets: AssetCatalog,
    content: ContentRecordSet,
) -> SupportRecordSet:
    """Build all non-content canonical record families from named inputs."""
    routing = _routing_observations(context=context, inputs=inputs, assets=assets)
    table_stage, stage_ids_by_page = _table_stage_observations(
        context=context,
        table_bundle=table_bundle,
        assets=assets,
    )
    conversion, conversion_id = _conversion_observations(
        context=context,
        inputs=inputs,
        assets=assets,
    )
    documents, pages = _document_and_pages(
        context=context,
        config=config,
        inputs=inputs,
        content=content,
        conversion_id=conversion_id,
        stage_ids_by_page=stage_ids_by_page,
    )
    return SupportRecordSet(
        documents=documents,
        pages=pages,
        routing_observations=routing,
        table_stage_observations=table_stage,
        conversion_observations=conversion,
        raw_mappings=_raw_mappings(context=context, content=content),
    )
