"""Typed in-memory records produced by heading-evidence parsing."""

from __future__ import annotations

from typing import Literal, TypedDict

ContentLayer = Literal["body", "furniture"]
NumberingKind = Literal["none", "decimal", "article", "upper_alpha", "upper_roman", "bullet"]
OutlineState = Literal["absent", "unique_exact", "ambiguous"]
LayoutState = Literal["absent", "unique_aligned", "ambiguous"]


class BoundingBox(TypedDict):
    """One bottom-left PDF bounding box."""

    l: float  # noqa: E741 - persisted PDF schema uses l/r coordinate names
    t: float
    r: float
    b: float
    coord_origin: Literal["BOTTOMLEFT"]


class ObservedItem(TypedDict):
    """Heading evidence available before TOC and numbering-scope analysis."""

    stable_item_key: str
    raw_self_ref: str
    raw_parent_ref: str
    text: str
    orig: str
    normalized_text: str
    reading_order_index: int
    content_layer: ContentLayer
    raw_role: str
    raw_level: int | None
    physical_page: int
    page_width: float
    page_height: float
    bbox: BoundingBox
    charspan: list[int]
    line_count: int | None
    left_pt: float
    height_pt: float
    numbering_kind: NumberingKind
    numbering_token: str | None
    numbering_depth: int | None
    outline_state: OutlineState
    outline_level: int | None
    layout_state: LayoutState
    printed_page_label: str | None


class TocClassifiedItem(ObservedItem):
    """Observed item after visible-TOC ownership is known."""

    toc_region: bool
