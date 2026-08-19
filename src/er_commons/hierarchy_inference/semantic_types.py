"""Typed in-memory records for deterministic hierarchy-inference stages.

Persisted JSON remains owned by the v1 schemas.  These types make the fields
available at each semantic stage explicit without changing those records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NewType, TypedDict

from er_commons.document_parsing.heading_evidence_parsing.types import (
    TocClassifiedItem,
)

StableItemKey = NewType("StableItemKey", str)
RegimeId = NewType("RegimeId", str)
TocEntryId = NewType("TocEntryId", str)

CorrectedRole = Literal["heading", "content", "excluded"]
DecisionOutcome = Literal["applied", "ambiguous", "unchanged"]


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


class HierarchyDecisionRecord(TypedDict):
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


JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class SemanticCandidate:
    """Complete in-memory semantic result passed from inference to publication."""

    features: tuple[JsonRecord, ...]
    toc_entries: tuple[JsonRecord, ...]
    reconciliations: tuple[JsonRecord, ...]
    regimes: tuple[JsonRecord, ...]
    decisions: tuple[JsonRecord, ...]
    hierarchy: JsonRecord
    ambiguities: tuple[JsonRecord, ...]
    warnings: tuple[JsonRecord, ...]

    def as_mapping(self) -> dict[str, object]:
        """Expose the schema-owned field names without copying record collections."""
        return {
            "features": self.features,
            "toc_entries": self.toc_entries,
            "reconciliations": self.reconciliations,
            "regimes": self.regimes,
            "decisions": self.decisions,
            "hierarchy": self.hierarchy,
            "ambiguities": self.ambiguities,
            "warnings": self.warnings,
        }
