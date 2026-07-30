"""Topology and feature-assignment policies for local numbering regimes."""

from __future__ import annotations

from dataclasses import dataclass

from er_commons.hierarchy_correction.bundle import CorrectionBundleView, JsonRecord
from er_commons.hierarchy_correction.checks import require, require_unique


@dataclass(frozen=True)
class RegimeInterval:
    """One half-open reading-order interval owned by a regime."""

    regime_id: str
    start: int
    end: int

    def contains(self, reading_order_index: int) -> bool:
        """Return whether one item falls inside this regime."""
        return self.start <= reading_order_index < self.end

    def overlaps(self, other: RegimeInterval) -> bool:
        """Return whether two regime intervals share any item position."""
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class RegimeTopology:
    """Resolved regime ancestry and reading-order intervals."""

    view: CorrectionBundleView
    initial_regime: JsonRecord
    intervals_by_id: dict[str, RegimeInterval]
    ancestors_by_id: dict[str, tuple[str, ...]]

    @classmethod
    def build(cls, view: CorrectionBundleView) -> RegimeTopology:
        """Validate references and resolve the complete regime topology."""
        _validate_regime_identifiers(view)
        initial_regime = _initial_regime(view)
        ancestors_by_id = {
            regime["regime_id"]: _ancestor_chain(regime["regime_id"], view)
            for regime in view.regimes
        }
        intervals_by_id = _resolve_intervals(view)
        topology = cls(
            view=view,
            initial_regime=initial_regime,
            intervals_by_id=intervals_by_id,
            ancestors_by_id=ancestors_by_id,
        )
        topology._validate_parent_containment()
        topology._validate_sibling_separation()
        return topology

    def active_regimes(self, reading_order_index: int) -> list[JsonRecord]:
        """Return the ancestor chain active at one reading-order position."""
        active = [
            regime
            for regime in self.view.regimes
            if self.intervals_by_id[regime["regime_id"]].contains(reading_order_index)
        ]
        initial_interval = self.intervals_by_id[self.initial_regime["regime_id"]]
        if reading_order_index < initial_interval.start:
            return [self.initial_regime]
        return active

    def _validate_parent_containment(self) -> None:
        """Require every child interval to sit strictly inside its parent start."""
        for regime in self.view.regimes:
            parent_id = regime["parent_regime_id"]
            if parent_id is None:
                continue
            child = self.intervals_by_id[regime["regime_id"]]
            parent = self.intervals_by_id[parent_id]
            require(
                parent.start < child.start < child.end <= parent.end,
                f"child regime escapes parent: {regime['regime_id']}",
            )

    def _validate_sibling_separation(self) -> None:
        """Reject overlapping intervals unless one regime contains the other."""
        regimes = list(self.view.regimes)
        for index, left_regime in enumerate(regimes):
            left_id = left_regime["regime_id"]
            left_interval = self.intervals_by_id[left_id]
            for right_regime in regimes[index + 1 :]:
                right_id = right_regime["regime_id"]
                right_interval = self.intervals_by_id[right_id]
                related = (
                    right_id in self.ancestors_by_id[left_id]
                    or left_id in self.ancestors_by_id[right_id]
                )
                require(
                    not left_interval.overlaps(right_interval) or related,
                    f"sibling regimes overlap: {left_id}, {right_id}",
                )


def features_use_innermost_regime(
    view: CorrectionBundleView,
    topology: RegimeTopology,
) -> None:
    """Assign every feature to the deepest active regime."""
    for feature in view.features:
        active = topology.active_regimes(feature["reading_order_index"])
        require(bool(active), f"feature is outside every regime: {feature['stable_item_key']}")
        deepest = max(
            active,
            key=lambda regime: len(topology.ancestors_by_id[regime["regime_id"]]),
        )
        require(
            feature["regime_id"] == deepest["regime_id"],
            f"feature regime assignment differs: {feature['stable_item_key']}",
        )


def _validate_regime_identifiers(view: CorrectionBundleView) -> None:
    """Require unique regimes and resolvable keys before interval work."""
    regime_ids = [regime["regime_id"] for regime in view.regimes]
    require_unique(regime_ids, "duplicate regime ID")
    require(bool(view.regimes), "initial regime differs")

    known_regimes = set(view.regimes_by_id)
    known_features = set(view.features_by_key)
    for regime in view.regimes:
        regime_id = regime["regime_id"]
        parent_id = regime["parent_regime_id"]
        require(
            parent_id is None or parent_id in known_regimes,
            f"unknown parent regime: {parent_id}",
        )
        require(parent_id != regime_id, f"regime is self-parented: {regime_id}")
        require(regime["root_level"] == 1, f"regime root level differs: {regime_id}")
        for field_name in ("start_item_key", "end_item_key", "outline_anchor_key"):
            reference = regime[field_name]
            require(
                reference is None or reference in known_features,
                f"unknown regime {field_name}: {regime_id}",
            )

    for feature in view.features:
        require(
            feature["regime_id"] in known_regimes,
            f"feature has unknown regime: {feature['stable_item_key']}",
        )


def _initial_regime(view: CorrectionBundleView) -> JsonRecord:
    """Return the sole root regime and validate its start item."""
    roots = [regime for regime in view.regimes if regime["parent_regime_id"] is None]
    require(len(roots) == 1, "initial regime differs")
    body_features = [item for item in view.features if item["content_layer"] == "body"]
    require(bool(body_features), "initial regime has no body feature")
    require(
        roots[0]["start_item_key"] == body_features[0]["stable_item_key"],
        "initial start differs",
    )
    return roots[0]


def _ancestor_chain(regime_id: str, view: CorrectionBundleView) -> tuple[str, ...]:
    """Return a cycle-checked parent chain including the named regime."""
    ancestors = []
    current: str | None = regime_id
    while current is not None:
        require(current not in ancestors, f"regime ancestry cycle: {regime_id}")
        ancestors.append(current)
        current = view.regimes_by_id[current]["parent_regime_id"]
    return tuple(ancestors)


def _resolve_intervals(view: CorrectionBundleView) -> dict[str, RegimeInterval]:
    """Resolve start and exclusive end keys to reading-order positions."""
    require(bool(view.order_by_key), "regime intervals require features")
    after_last_item = max(view.order_by_key.values()) + 1
    intervals = {}
    for regime in view.regimes:
        start = view.order_by_key[regime["start_item_key"]]
        end_key = regime["end_item_key"]
        end = after_last_item if end_key is None else view.order_by_key[end_key]
        require(start < end, f"regime interval is empty or reversed: {regime['regime_id']}")
        intervals[regime["regime_id"]] = RegimeInterval(
            regime_id=regime["regime_id"],
            start=start,
            end=end,
        )
    return intervals
