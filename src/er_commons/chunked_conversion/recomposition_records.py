"""Immutable records shared by range partitioning and reconstruction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RangeItem:
    """One locally addressed record with its canonical position retained."""

    collection: str
    source_index: int
    local_ref: str
    source_ref: str
    pages: tuple[int, ...]
    value: dict[str, Any]


@dataclass(frozen=True)
class OverlapEvidence:
    """Duplicated semantic projection used to compare one non-owned read page."""

    page: int
    page_digest: str
    record_digests: tuple[tuple[str, str], ...]
    heading_overlay: tuple[dict[str, Any], ...] = ()
    alignment_page: dict[str, Any] | None = None
    assets: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RangeShard:
    """Source-free evidence owned by one planned core range."""

    plan_id: str
    range_id: str
    core_pages: tuple[int, ...]
    read_pages: tuple[int, ...]
    pages: tuple[tuple[int, dict[str, Any]], ...]
    items: tuple[RangeItem, ...]
    overlap_evidence: tuple[OverlapEvidence, ...]
    heading_overlay: tuple[dict[str, Any], ...] = ()
    alignment_pages: tuple[dict[str, Any], ...] = ()
    assets: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class PartitionedEvidence:
    """Global root plus independently owned range shards."""

    plan_id: str
    root: dict[str, Any]
    collection_counts: Mapping[str, int]
    global_items: tuple[RangeItem, ...]
    shards: tuple[RangeShard, ...]


__all__ = ["OverlapEvidence", "PartitionedEvidence", "RangeItem", "RangeShard"]
