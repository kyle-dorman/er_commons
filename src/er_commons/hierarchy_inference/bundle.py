"""A readable indexed view over a schema-valid correction bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

JsonRecord = dict[str, Any]
CorrectionBundle = dict[str, Any]


@dataclass(frozen=True)
class HierarchyBundleView:
    """Cache named record collections and their stable-key indexes."""

    bundle: CorrectionBundle
    features: tuple[JsonRecord, ...] = field(init=False)
    decisions: tuple[JsonRecord, ...] = field(init=False)
    regimes: tuple[JsonRecord, ...] = field(init=False)
    toc_entries: tuple[JsonRecord, ...] = field(init=False)
    reconciliations: tuple[JsonRecord, ...] = field(init=False)
    features_by_key: dict[str, JsonRecord] = field(init=False)
    decisions_by_key: dict[str, JsonRecord] = field(init=False)
    regimes_by_id: dict[str, JsonRecord] = field(init=False)
    toc_entries_by_id: dict[str, JsonRecord] = field(init=False)
    order_by_key: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        features = tuple(self.bundle["features"])
        decisions = tuple(self.bundle["decisions"])
        regimes = tuple(self.bundle["regimes"])
        toc_entries = tuple(self.bundle["toc_entries"])
        reconciliations = tuple(self.bundle["reconciliations"])

        object.__setattr__(self, "features", features)
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(self, "regimes", regimes)
        object.__setattr__(self, "toc_entries", toc_entries)
        object.__setattr__(self, "reconciliations", reconciliations)
        object.__setattr__(
            self,
            "features_by_key",
            {item["stable_item_key"]: item for item in features},
        )
        object.__setattr__(
            self,
            "decisions_by_key",
            {item["stable_item_key"]: item for item in decisions},
        )
        object.__setattr__(
            self,
            "regimes_by_id",
            {item["regime_id"]: item for item in regimes},
        )
        object.__setattr__(
            self,
            "toc_entries_by_id",
            {item["toc_entry_id"]: item for item in toc_entries},
        )
        object.__setattr__(
            self,
            "order_by_key",
            {feature["stable_item_key"]: feature["reading_order_index"] for feature in features},
        )

    @property
    def feature_keys(self) -> list[str]:
        """Return stable item keys in producer reading order."""
        return [item["stable_item_key"] for item in self.features]

    @property
    def decision_keys(self) -> list[str]:
        """Return decision keys in serialized order."""
        return [item["stable_item_key"] for item in self.decisions]

    @property
    def exact_reconciliations_by_toc(self) -> dict[str, JsonRecord]:
        """Return successful TOC reconciliations keyed by TOC row ID."""
        return {
            item["toc_entry_id"]: item for item in self.reconciliations if item["state"] == "exact"
        }
