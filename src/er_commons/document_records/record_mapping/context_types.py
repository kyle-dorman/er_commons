"""Immutable cross-stage types for canonical record materialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from er_commons.document_records.record_mapping.traversal import (
    TraversalEvent,
    TraversalResult,
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
class TraversalContext:
    """Validated traversal and provenance accounting before ID allocation."""

    traversal: TraversalResult
    block_events: tuple[TraversalEvent, ...]
    figure_pointers: tuple[str, ...]
    document_index_descendants: frozenset[str]
    all_text_pointers: frozenset[str]
    accounted_text_pointers: frozenset[str]
    invalid_text_provenance: tuple[dict[str, Any], ...]


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
