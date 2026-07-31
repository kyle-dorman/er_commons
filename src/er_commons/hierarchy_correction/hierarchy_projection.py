"""Project corrected decisions into hierarchy relationships and membership."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, cast

from er_commons.hierarchy_correction.scope_lifecycle import NumberingScopeLifecycle
from er_commons.hierarchy_correction.semantic_types import (
    CorrectionDecisionRecord,
    DiagnosticRecord,
    HierarchyRecord,
    NumberingScopeRecord,
    ScopedItem,
)

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class _OpenHeading:
    level: int
    key: str


@dataclass(frozen=True)
class HierarchyBuildResult:
    """Corrected relationships plus deterministic sparse-depth warnings."""

    hierarchy: HierarchyRecord
    warnings: tuple[DiagnosticRecord, ...]


def build_corrected_hierarchy(
    *,
    features: tuple[ScopedItem, ...],
    decisions: tuple[CorrectionDecisionRecord, ...],
    regimes: tuple[NumberingScopeRecord, ...],
) -> HierarchyBuildResult:
    """Build roots, edges, and exact direct membership per active regime."""
    decision_by_key = {item["stable_item_key"]: item for item in decisions}
    if len(decision_by_key) != len(decisions):
        raise ValueError("DECISION_COVERAGE_MISMATCH: duplicate decision key")
    feature_keys = [item["stable_item_key"] for item in features]
    if set(decision_by_key) != set(feature_keys):
        raise ValueError("DECISION_COVERAGE_MISMATCH: decision keys differ from features")
    regime_by_id = {item["regime_id"]: item for item in regimes}
    lifecycle = NumberingScopeLifecycle.from_regimes(regimes)
    stacks: defaultdict[str, list[_OpenHeading]] = defaultdict(list)
    roots: list[str] = []
    edges: list[JsonRecord] = []
    membership: list[JsonRecord] = []
    unassigned: list[str] = []
    warnings: list[JsonRecord] = []

    for feature in features:
        key = feature["stable_item_key"]
        for event in lifecycle.before_item(key):
            stacks[event.enclosing_regime_id].clear()
        regime_id = feature["regime_id"]
        if regime_id not in regime_by_id:
            raise ValueError(f"UNKNOWN_REFERENCE: unknown regime for {key}")
        decision = decision_by_key[key]
        role = decision["corrected_role"]
        stack = stacks[regime_id]
        if role == "heading":
            level = decision["corrected_level"]
            if not isinstance(level, int):
                raise ValueError(f"CORRECTED_LEVEL_INVALID: missing heading level for {key}")
            while stack and stack[-1].level >= level:
                stack.pop()
            root_level = regime_by_id[regime_id]["root_level"]
            if not stack:
                roots.append(key)
                missing = level - root_level
                if missing > 0:
                    warnings.append(
                        _sparse_warning(
                            feature,
                            "sparse hierarchy root: "
                            f"regime_root_level={root_level}, child_level={level}, "
                            f"missing_intermediate_level_count = {missing}",
                        )
                    )
            else:
                edges.append({"parent_key": stack[-1].key, "child_key": key})
                missing = level - stack[-1].level - 1
                if missing > 0:
                    warnings.append(
                        _sparse_warning(
                            feature,
                            "sparse hierarchy edge: "
                            f"parent_level={stack[-1].level}, child_level={level}, "
                            f"missing_intermediate_level_count = {missing}",
                        )
                    )
            stack.append(_OpenHeading(level, key))
        elif role == "content":
            if stack:
                membership.append({"item_key": key, "heading_key": stack[-1].key})
            else:
                unassigned.append(key)
        elif role != "excluded":
            raise ValueError(f"CORRECTED_LEVEL_INVALID: unknown corrected role for {key}")

    return HierarchyBuildResult(
        hierarchy=cast(
            HierarchyRecord,
            {
                "roots": roots,
                "edges": edges,
                "direct_membership": membership,
                "unassigned_content": unassigned,
            },
        ),
        warnings=cast(tuple[DiagnosticRecord, ...], tuple(warnings)),
    )


def _sparse_warning(feature: ScopedItem, detail: str) -> JsonRecord:
    """Build one ordered, source-bound sparse-depth warning."""
    return {
        "reading_order_index": feature["reading_order_index"],
        "stable_item_key": feature["stable_item_key"],
        "code": "RAW_HEADING_DEPTH_UNSUPPORTED",
        "detail": detail,
    }
