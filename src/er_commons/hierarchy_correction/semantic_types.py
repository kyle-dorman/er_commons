"""Typed in-memory records for deterministic hierarchy-correction stages.

Persisted JSON remains owned by the v1 schemas.  These types make the fields
available at each semantic stage explicit without changing those records.
"""

from __future__ import annotations

from typing import Any, Literal, NewType, TypedDict

StableItemKey = NewType("StableItemKey", str)
RegimeId = NewType("RegimeId", str)
TocEntryId = NewType("TocEntryId", str)

ContentLayer = Literal["body", "furniture"]
NumberingKind = Literal["none", "decimal", "article", "upper_alpha", "upper_roman", "bullet"]
OutlineState = Literal["absent", "unique_exact", "ambiguous"]
LayoutState = Literal["absent", "unique_aligned", "ambiguous"]
CorrectedRole = Literal["heading", "content", "excluded"]
DecisionOutcome = Literal["applied", "ambiguous", "unchanged"]


class BoundingBox(TypedDict):
    """One bottom-left PDF bounding box."""

    l: float  # noqa: E741 - persisted PDF schema uses l/r coordinate names
    t: float
    r: float
    b: float
    coord_origin: Literal["BOTTOMLEFT"]


class ObservedItem(TypedDict):
    """Producer evidence available before TOC and numbering-scope analysis."""

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


class ScopedItem(TocClassifiedItem):
    """TOC-classified item assigned to its innermost numbering scope."""

    regime_id: str


class NumberingScopeRecord(TypedDict):
    """Persisted local numbering-scope record."""

    regime_id: str
    parent_regime_id: str | None
    root_level: int
    start_item_key: str
    end_item_key: str | None
    outline_anchor_key: str | None
    page_label_reset: bool


class CorrectionDecisionRecord(TypedDict):
    """Persisted decision header; evidence retains the schema-owned shape."""

    stable_item_key: str
    raw_role: str
    corrected_role: CorrectedRole
    raw_level: int | None
    corrected_level: int | None
    outcome: DecisionOutcome
    selected_rule_id: str
    eligible_rule_ids: list[str]
    evidence: dict[str, Any]


class DiagnosticRecord(TypedDict):
    """One source-bound warning or ambiguity."""

    reading_order_index: int
    stable_item_key: str
    code: str
    detail: str


class HierarchyEdge(TypedDict):
    """One parent-to-child heading edge."""

    parent_key: str
    child_key: str


class DirectMembership(TypedDict):
    """One content item assigned to its nearest open heading."""

    item_key: str
    heading_key: str


class HierarchyRecord(TypedDict):
    """Persisted corrected hierarchy projection."""

    roots: list[str]
    edges: list[HierarchyEdge]
    direct_membership: list[DirectMembership]
    unassigned_content: list[str]
