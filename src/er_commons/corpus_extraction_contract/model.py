"""Small domain values shared by the corpus-contract validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

type JsonObject = dict[str, Any]


@dataclass(frozen=True)
class LifecycleEvidence:
    """Validated final attempt events and successful document completions."""

    final_events: dict[str, JsonObject]
    completions: dict[str, JsonObject]


@dataclass(frozen=True)
class ScopeEvidence:
    """Candidate and source sets derived from exact scope accounting."""

    candidate_sources: dict[str, str]
    candidate_inventories: dict[str, str]
    unavailable_source_ids: frozenset[str]

    @property
    def successful_candidate_ids(self) -> frozenset[str]:
        """Return the candidates eligible for corpus indexing."""
        return frozenset(self.candidate_sources)


@dataclass(frozen=True)
class IndexEvidence:
    """Validated candidate and target membership of the sealed corpus index."""

    target_ids_by_lookup_key: dict[str, tuple[str, ...]]
