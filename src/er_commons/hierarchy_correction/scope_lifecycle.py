"""Translate nested numbering-scope exits into explicit hierarchy events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class CloseEnclosingStack:
    """Close one enclosing scope before processing a peer boundary item."""

    boundary_item_key: str
    enclosing_regime_id: str
    ended_regime_id: str


@dataclass(frozen=True)
class NumberingScopeLifecycle:
    """Hierarchy events indexed by the boundary before which they occur."""

    closes_before_item: dict[str, tuple[CloseEnclosingStack, ...]]

    @classmethod
    def from_regimes(cls, regimes: Iterable[Mapping[str, Any]]) -> NumberingScopeLifecycle:
        """Derive explicit stack-close events from exclusive nested-scope ends."""
        indexed: defaultdict[str, list[CloseEnclosingStack]] = defaultdict(list)
        for regime in regimes:
            boundary_key = regime["end_item_key"]
            parent_id = regime["parent_regime_id"]
            if boundary_key is None or parent_id is None:
                continue
            indexed[boundary_key].append(
                CloseEnclosingStack(
                    boundary_item_key=boundary_key,
                    enclosing_regime_id=parent_id,
                    ended_regime_id=regime["regime_id"],
                )
            )
        return cls({key: tuple(events) for key, events in indexed.items()})

    def before_item(self, stable_item_key: str) -> tuple[CloseEnclosingStack, ...]:
        """Return all stack-close events before one item in stable order."""
        return self.closes_before_item.get(stable_item_key, ())
