"""Allocate deterministic IDs and assemble the record-mapping context."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.document_records.record_mapping.context_preparation import (
    build_traversal_context,
    page_sizes,
    table_events,
)
from er_commons.document_records.record_mapping.context_types import (
    RecordIds,
    RecordMappingContext,
    TraversalContext,
)
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.identifiers import make_record_id
from er_commons.document_records.record_mapping.inputs import RecordMappingInputs
from er_commons.document_records.record_mapping.tables import ProducerTableBundle


def _allocate_record_ids(
    extraction_id: str,
    source_id: str,
    page_ids: Mapping[int, str],
    traversal: TraversalContext,
    table_bundle: ProducerTableBundle,
) -> RecordIds:
    """Allocate every candidate-scoped identifier from stable sequence order."""

    def ids(kind: str, prefix: str, values: list[str]) -> dict[str, str]:
        return {
            value: make_record_id(extraction_id, kind, source_id, f"{prefix}{index:06d}")
            for index, value in enumerate(values, start=1)
        }

    layers = {event.content_layer for event in traversal.traversal.events}
    return RecordIds(
        extraction_id=extraction_id,
        source_id=source_id,
        document_id=make_record_id(extraction_id, "document", source_id),
        page_ids=page_ids,
        block_id_by_pointer=ids(
            "block", "blk", [event.pointer for event in traversal.block_events]
        ),
        table_id_by_producer=ids("table", "tbl", [table.table_id for table in table_bundle.tables]),
        family_id_by_producer=ids(
            "table-family", "fam", [family.family_id for family in table_bundle.families]
        ),
        figure_id_by_pointer=ids("figure", "fig", list(traversal.figure_pointers)),
        image_id_by_pointer=ids("image", "img", list(traversal.figure_pointers)),
        section_id_by_layer={
            layer: make_record_id(extraction_id, "section", source_id, f"sec{index:06d}")
            for index, layer in enumerate(("body", "furniture"), start=1)
            if layer in layers
        },
    )


def build_record_mapping_context(
    *,
    config: RecordMappingConfig,
    inputs: RecordMappingInputs,
    identity: Mapping[str, Any],
    table_bundle: ProducerTableBundle,
) -> RecordMappingContext:
    """Build the immutable ordering and ID registry used by record builders."""
    extraction_id = identity.get("extraction_id")
    if not isinstance(extraction_id, str):
        raise MappingContractError("candidate identity has no extraction ID")
    source = config.ordered_materialization_scope[0]
    sizes = page_sizes(inputs.document)
    expected_pages = list(range(1, source.pdf_page_count + 1))
    if sorted(sizes) != expected_pages:
        raise MappingContractError(
            "canonical page context differs from configured document scope: "
            f"expected={len(expected_pages)} actual={len(sizes)}"
        )
    page_ids = {
        page: make_record_id(extraction_id, "page", source.source_id, f"p{page:06d}")
        for page in sorted(sizes)
    }
    traversal = build_traversal_context(inputs, table_bundle, page_ids, sizes)
    return RecordMappingContext(
        ids=_allocate_record_ids(
            extraction_id, source.source_id, page_ids, traversal, table_bundle
        ),
        page_sizes=sizes,
        traversal=traversal.traversal,
        block_events=traversal.block_events,
        figure_pointers=traversal.figure_pointers,
        table_event_by_id=table_events(traversal.traversal, table_bundle),
        document_index_descendants=traversal.document_index_descendants,
        all_text_pointers=traversal.all_text_pointers,
        accounted_text_pointers=traversal.accounted_text_pointers,
        invalid_text_provenance=traversal.invalid_text_provenance,
    )
