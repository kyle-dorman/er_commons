"""Build immutable page, traversal, and canonical-ID context for materialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.identifiers import make_record_id
from er_commons.document_records.record_mapping.inputs import RecordMappingInputs
from er_commons.document_records.record_mapping.provenance import project_regions
from er_commons.document_records.record_mapping.tables import ProducerTableBundle
from er_commons.document_records.record_mapping.traversal import (
    TraversalEvent,
    TraversalResult,
    traverse_docling_document,
)

PageSize = tuple[float, float]


def _readonly_mapping[K, V](values: Mapping[K, V]) -> Mapping[K, V]:
    """Return a read-only copy so callers cannot mutate shared build state."""
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class RecordIds:
    """All deterministic canonical identifiers allocated before record construction."""

    extraction_id: str
    source_id: str
    document_id: str
    page_ids: Mapping[int, str]
    block_id_by_pointer: Mapping[str, str]
    table_id_by_producer: Mapping[str, str]
    family_id_by_producer: Mapping[str, str]
    figure_id_by_pointer: Mapping[str, str]
    image_id_by_pointer: Mapping[str, str]
    section_id_by_layer: Mapping[str, str]

    def __post_init__(self) -> None:
        """Detach and freeze every caller-supplied identifier mapping."""
        for field_name in (
            "page_ids",
            "block_id_by_pointer",
            "table_id_by_producer",
            "family_id_by_producer",
            "figure_id_by_pointer",
            "image_id_by_pointer",
            "section_id_by_layer",
        ):
            object.__setattr__(
                self,
                field_name,
                _readonly_mapping(getattr(self, field_name)),
            )


@dataclass(frozen=True)
class RecordMappingContext:
    """Validated ordering, geometry, and IDs shared by record-family builders."""

    ids: RecordIds
    page_sizes: Mapping[int, PageSize]
    traversal: TraversalResult
    block_events: tuple[TraversalEvent, ...]
    figure_pointers: tuple[str, ...]
    table_event_by_id: Mapping[str, TraversalEvent]
    document_index_descendants: frozenset[str]
    all_text_pointers: frozenset[str]
    accounted_text_pointers: frozenset[str]
    invalid_text_provenance: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        """Freeze geometry and table-event indexes at the stage boundary."""
        object.__setattr__(self, "page_sizes", _readonly_mapping(self.page_sizes))
        object.__setattr__(
            self,
            "table_event_by_id",
            _readonly_mapping(self.table_event_by_id),
        )

    @property
    def extraction_id(self) -> str:
        """Return the candidate-scoped extraction identifier."""
        return self.ids.extraction_id

    @property
    def source_id(self) -> str:
        """Return the sole materialized source identifier."""
        return self.ids.source_id

    @property
    def document_id(self) -> str:
        """Return the canonical document identifier."""
        return self.ids.document_id

    @property
    def page_ids(self) -> Mapping[int, str]:
        """Return physical-page to canonical-page IDs."""
        return self.ids.page_ids

    @property
    def block_id_by_pointer(self) -> Mapping[str, str]:
        """Return saved text pointers to canonical block IDs."""
        return self.ids.block_id_by_pointer

    @property
    def page_number_by_id(self) -> Mapping[str, int]:
        """Return canonical page IDs to physical page numbers."""
        return MappingProxyType({page_id: page for page, page_id in self.page_ids.items()})

    @property
    def table_id_by_producer(self) -> Mapping[str, str]:
        """Return clean producer table IDs to canonical table IDs."""
        return self.ids.table_id_by_producer

    @property
    def family_id_by_producer(self) -> Mapping[str, str]:
        """Return producer family IDs to canonical family IDs."""
        return self.ids.family_id_by_producer

    @property
    def figure_id_by_pointer(self) -> Mapping[str, str]:
        """Return saved picture pointers to canonical figure IDs."""
        return self.ids.figure_id_by_pointer

    @property
    def image_id_by_pointer(self) -> Mapping[str, str]:
        """Return saved picture pointers to canonical image IDs."""
        return self.ids.image_id_by_pointer

    @property
    def section_id_by_layer(self) -> Mapping[str, str]:
        """Return present content layers to synthetic root-section IDs."""
        return self.ids.section_id_by_layer


def _page_sizes(document: Mapping[str, Any]) -> dict[int, PageSize]:
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


@dataclass(frozen=True)
class TraversalContext:
    """Validated traversal and provenance accounting before ID allocation."""

    traversal: TraversalResult
    block_events: tuple[TraversalEvent, ...]
    figure_pointers: tuple[str, ...]
    document_index_descendants: frozenset[str]
    all_text_pointers: frozenset[str]
    accounted_text_pointers: frozenset[str]
    invalid_text_provenance: tuple[dict[str, Any], ...]


def _build_traversal_context(
    inputs: RecordMappingInputs,
    table_bundle: ProducerTableBundle,
    page_ids: dict[int, str],
    page_sizes: dict[int, PageSize],
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
            item=item, pointer=pointer, page_ids=page_ids, page_sizes=page_sizes
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
    traversal = traverse_docling_document(inputs.document, mapped_tables, invalid_pointers)
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


def _table_events(
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
    page_sizes = _page_sizes(inputs.document)
    expected_pages = list(range(1, source.pdf_page_count + 1))
    if sorted(page_sizes) != expected_pages:
        raise MappingContractError(
            "canonical page context differs from configured document scope: "
            f"expected={len(expected_pages)} actual={len(page_sizes)}"
        )
    page_ids = {
        page: make_record_id(extraction_id, "page", source.source_id, f"p{page:06d}")
        for page in sorted(page_sizes)
    }
    traversal = _build_traversal_context(inputs, table_bundle, page_ids, page_sizes)
    return RecordMappingContext(
        ids=_allocate_record_ids(
            extraction_id, source.source_id, page_ids, traversal, table_bundle
        ),
        page_sizes=page_sizes,
        traversal=traversal.traversal,
        block_events=traversal.block_events,
        figure_pointers=traversal.figure_pointers,
        table_event_by_id=_table_events(traversal.traversal, table_bundle),
        document_index_descendants=traversal.document_index_descendants,
        all_text_pointers=traversal.all_text_pointers,
        accounted_text_pointers=traversal.accounted_text_pointers,
        invalid_text_provenance=traversal.invalid_text_provenance,
    )
