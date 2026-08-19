"""Prepare traversal and provenance evidence for record-mapping context."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from er_commons.document_records.record_mapping.context_types import (
    PageSize,
    TraversalContext,
)
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.inputs import RecordMappingInputs
from er_commons.document_records.record_mapping.provenance import project_regions
from er_commons.document_records.record_mapping.tables import (
    ProducerTable,
    ProducerTableBundle,
)
from er_commons.document_records.record_mapping.traversal import (
    TraversalEvent,
    TraversalResult,
    traverse_docling_document,
)


def page_sizes(document: Mapping[str, Any]) -> dict[int, PageSize]:
    """Validate and index saved Docling page geometry."""
    pages = document.get("pages")
    if not isinstance(pages, dict):
        raise MappingContractError("saved Docling document has no page objects")
    sizes: dict[int, PageSize] = {}
    for raw_page, record in pages.items():
        if not isinstance(record, dict) or not isinstance(record.get("size"), dict):
            raise MappingContractError(f"invalid Docling page object: {raw_page}")
        size = record["size"]
        try:
            page = int(raw_page)
            width = float(size["width"])
            height = float(size["height"])
        except (KeyError, TypeError, ValueError) as error:
            raise MappingContractError(f"invalid Docling page geometry: {raw_page}") from error
        sizes[page] = (width, height)
    return sizes


def _descendant_text_pointers(
    document: Mapping[str, Any],
    roots: list[dict[str, str]],
) -> set[str]:
    """Collect unique text descendants below saved group or item references."""
    texts: set[str] = set()
    active: set[str] = set()

    def visit(pointer: str) -> None:
        parts = pointer.split("/")
        if len(parts) != 3 or parts[0] != "#" or not parts[2].isdigit():
            raise MappingContractError(f"unsupported descendant pointer: {pointer}")
        collection, index = parts[1], int(parts[2])
        if collection == "texts":
            texts.add(pointer)
            return
        values = document.get(collection)
        if not isinstance(values, list) or index >= len(values):
            raise MappingContractError(f"unknown descendant pointer: {pointer}")
        if pointer in active:
            raise MappingContractError(f"descendant cycle: {pointer}")
        item = values[index]
        if not isinstance(item, dict):
            raise MappingContractError(f"invalid descendant object: {pointer}")
        active.add(pointer)
        for child in item.get("children", []):
            visit(child["$ref"])
        active.remove(pointer)

    for root in roots:
        visit(root["$ref"])
    return texts


def _figure_pointers(document: Mapping[str, Any]) -> tuple[str, ...]:
    """Order saved pictures by deterministic page and geometry evidence."""
    pictures = document.get("pictures")
    if not isinstance(pictures, list):
        raise MappingContractError("saved Docling document has no picture collection")
    pointers = [f"#/pictures/{index}" for index in range(len(pictures))]
    try:
        pointers.sort(
            key=lambda pointer: (
                pictures[int(pointer.rsplit("/", 1)[1])]["prov"][0]["page_no"],
                -pictures[int(pointer.rsplit("/", 1)[1])]["prov"][0]["bbox"]["t"],
                pictures[int(pointer.rsplit("/", 1)[1])]["prov"][0]["bbox"]["l"],
                pointer,
            )
        )
    except (IndexError, KeyError, TypeError) as error:
        raise MappingContractError("picture ordering provenance is incomplete") from error
    return tuple(pointers)


def _event_page(document: Mapping[str, Any], event: TraversalEvent) -> int:
    """Return the first declared page for one standard Docling traversal event."""
    parts = event.pointer.split("/")
    if len(parts) != 3 or parts[0] != "#" or not parts[2].isdigit():
        raise MappingContractError(f"invalid traversal event pointer: {event.pointer}")
    collection = document.get(parts[1])
    index = int(parts[2])
    if not isinstance(collection, list) or index >= len(collection):
        raise MappingContractError(f"unknown traversal event pointer: {event.pointer}")
    item = collection[index]
    provenance = item.get("prov") if isinstance(item, dict) else None
    if (
        not isinstance(provenance, list)
        or not provenance
        or not isinstance(provenance[0], dict)
        or not isinstance(provenance[0].get("page_no"), int)
    ):
        raise MappingContractError(f"traversal event has no page: {event.pointer}")
    return int(provenance[0]["page_no"])


def _attach_full_page_table_events(
    document: Mapping[str, Any],
    traversal: TraversalResult,
    tables: tuple[ProducerTable, ...],
) -> TraversalResult:
    """Place regionless page-wide tables after other body content on their page."""
    full_page_tables = sorted(
        (table for table in tables if table.region_id is None),
        key=lambda table: (table.physical_pdf_page, table.page_table_index, table.table_id),
    )
    if not full_page_tables:
        return traversal
    body_events = [event for event in traversal.events if event.content_layer == "body"]
    furniture_events = [event for event in traversal.events if event.content_layer == "furniture"]
    body_pages = [_event_page(document, event) for event in body_events]
    placements: dict[int, list[TraversalEvent]] = {}
    for table in full_page_tables:
        preceding = [
            index for index, page in enumerate(body_pages) if page <= table.physical_pdf_page
        ]
        placement = preceding[-1] if preceding else -1
        placements.setdefault(placement, []).append(
            TraversalEvent(
                kind="table",
                pointer=f"#/full_page_tables/{table.table_id}",
                content_layer="body",
                producer_table_id=table.table_id,
            )
        )
    ordered = list(placements.get(-1, ()))
    for index, event in enumerate(body_events):
        ordered.append(event)
        ordered.extend(placements.get(index, ()))
    return replace(
        traversal,
        events=tuple(ordered) + tuple(furniture_events),
    )


def build_traversal_context(
    inputs: RecordMappingInputs,
    table_bundle: ProducerTableBundle,
    page_ids: dict[int, str],
    sizes: dict[int, PageSize],
) -> TraversalContext:
    """Validate Docling traversal coverage and document-index descendants."""
    texts = inputs.document.get("texts")
    if not isinstance(texts, list):
        raise MappingContractError("saved Docling document has no text collection")
    all_text = frozenset(f"#/texts/{index}" for index in range(len(texts)))
    invalid_pointers: set[str] = set()
    rejected: list[dict[str, Any]] = []
    for index, item in enumerate(texts):
        pointer = f"#/texts/{index}"
        projection = project_regions(
            item=item, pointer=pointer, page_ids=page_ids, page_sizes=sizes
        )
        if projection.regions:
            continue
        if not projection.rejected:
            raise MappingContractError(f"text has no provenance to account: pointer={pointer}")
        invalid_pointers.add(pointer)
        rejected.extend(projection.rejected)
    mapped_tables = {
        mapping.raw_object_ref: mapping.clean_table_ids for mapping in table_bundle.region_mappings
    }
    suppressed_tables = {
        mapping.raw_object_ref
        for mapping in table_bundle.region_mappings
        if mapping.unmapped_reason == "full_page_numeric_route"
    }
    traversal = traverse_docling_document(
        inputs.document,
        mapped_tables,
        invalid_pointers,
        suppressed_tables,
    )
    traversal = _attach_full_page_table_events(inputs.document, traversal, table_bundle.tables)
    accounted = traversal.emitted_text_pointers | traversal.suppressed_text_pointers
    overlap = traversal.emitted_text_pointers & traversal.suppressed_text_pointers
    if overlap or accounted != all_text:
        raise MappingContractError(
            "Docling text traversal accounting is incomplete: "
            f"overlap={len(overlap)} unaccounted={len(all_text - accounted)}"
        )
    tables = inputs.document.get("tables")
    if not isinstance(tables, list):
        raise MappingContractError("saved Docling document has no table collection")
    descendants: set[str] = set()
    for item in tables:
        if not isinstance(item, dict):
            raise MappingContractError("invalid Docling table object")
        if item.get("label") == "document_index":
            descendants.update(_descendant_text_pointers(inputs.document, item.get("children", [])))
    index_accounted = traversal.emitted_text_pointers | traversal.invalid_geometry_text_pointers
    if not descendants <= index_accounted:
        raise MappingContractError(
            "document-index descendants were not emitted: "
            f"missing={sorted(descendants - index_accounted)}"
        )
    return TraversalContext(
        traversal=traversal,
        block_events=tuple(event for event in traversal.events if event.kind == "text"),
        figure_pointers=_figure_pointers(inputs.document),
        document_index_descendants=frozenset(descendants),
        all_text_pointers=all_text,
        accounted_text_pointers=accounted,
        invalid_text_provenance=tuple(rejected),
    )


def table_events(
    traversal: TraversalResult, table_bundle: ProducerTableBundle
) -> dict[str, TraversalEvent]:
    """Index table replacement events and require exact clean-table coverage."""
    events = {
        event.producer_table_id: event
        for event in traversal.events
        if event.kind == "table" and event.producer_table_id is not None
    }
    expected = {table.table_id for table in table_bundle.tables}
    if set(events) != expected:
        raise MappingContractError(
            "traversal table replacements differ from clean tables: "
            f"expected={sorted(expected)} actual={sorted(events)}"
        )
    return events
