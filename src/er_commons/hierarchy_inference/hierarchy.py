"""Corrected hierarchy reconstruction and inverse-membership policies."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from er_commons.hierarchy_inference.bundle import HierarchyBundleView
from er_commons.hierarchy_inference.checks import require, require_unique
from er_commons.hierarchy_inference.scope_lifecycle import NumberingScopeLifecycle


@dataclass(frozen=True)
class OpenHeading:
    """One heading currently open in a regime's reading-order stack."""

    level: int
    stable_item_key: str


@dataclass(frozen=True)
class ExpectedHierarchy:
    """Hierarchy relationships derived independently from decisions."""

    roots: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    direct_membership: tuple[tuple[str, str], ...]
    unassigned_content: tuple[str, ...]
    sparse_warnings: tuple[tuple[str, str], ...]


def hierarchy_matches_decisions(view: HierarchyBundleView) -> None:
    """Reconstruct hierarchy from decisions and compare every relationship."""
    expected = derive_expected_hierarchy(view)
    actual = view.bundle["hierarchy"]

    roots = tuple(actual["roots"])
    require_unique(roots, "duplicate hierarchy root")
    edge_pairs = [(edge["parent_key"], edge["child_key"]) for edge in actual["edges"]]
    require_unique(edge_pairs, "duplicate hierarchy edge")
    edges = tuple(edge_pairs)

    membership = tuple(
        (item["item_key"], item["heading_key"]) for item in actual["direct_membership"]
    )
    membership_items = [item_key for item_key, _ in membership]
    require_unique(membership_items, "duplicate direct membership")
    unassigned = tuple(actual["unassigned_content"])
    require_unique(unassigned, "duplicate unassigned content")

    require(roots == expected.roots, "hierarchy roots differ")
    require(edges == expected.edges, "hierarchy edges differ")
    require(membership == expected.direct_membership, "direct membership differs")
    require(unassigned == expected.unassigned_content, "unassigned content differs")
    require(
        not (set(unassigned) & set(membership_items)),
        "content assignment overlaps",
    )

    heading_keys = {
        key
        for key, decision in view.decisions_by_key.items()
        if decision["corrected_role"] == "heading"
    }
    represented_headings = set(roots) | {child for _, child in edges}
    require(represented_headings == heading_keys, "hierarchy heading coverage differs")
    actual_sparse_warnings = tuple(
        (item["stable_item_key"], item["detail"])
        for item in view.bundle["warnings"]
        if item["code"] == "RAW_HEADING_DEPTH_UNSUPPORTED"
    )
    require(
        actual_sparse_warnings == expected.sparse_warnings,
        "sparse hierarchy warnings differ",
    )


def derive_expected_hierarchy(view: HierarchyBundleView) -> ExpectedHierarchy:
    """Build the only valid hierarchy from ordered corrected decisions."""
    roots: list[str] = []
    edges: list[tuple[str, str]] = []
    membership: list[tuple[str, str]] = []
    unassigned: list[str] = []
    sparse_warnings: list[tuple[str, str]] = []
    stacks: defaultdict[str, list[OpenHeading]] = defaultdict(list)
    lifecycle = NumberingScopeLifecycle.from_regimes(view.regimes)

    for feature in view.features:
        key = feature["stable_item_key"]
        for event in lifecycle.before_item(key):
            stacks[event.enclosing_regime_id].clear()
        decision = view.decisions_by_key[key]
        stack = stacks[feature["regime_id"]]
        role = decision["corrected_role"]

        if role == "heading":
            warning = _append_heading(
                view, feature["regime_id"], key, decision["corrected_level"], stack
            )
            if warning is not None:
                sparse_warnings.append((key, warning))
            heading = stack[-1]
            if len(stack) == 1:
                roots.append(heading.stable_item_key)
            else:
                edges.append((stack[-2].stable_item_key, heading.stable_item_key))
        elif role == "content":
            if stack:
                membership.append((key, stack[-1].stable_item_key))
            else:
                unassigned.append(key)

    return ExpectedHierarchy(
        roots=tuple(roots),
        edges=tuple(edges),
        direct_membership=tuple(membership),
        unassigned_content=tuple(unassigned),
        sparse_warnings=tuple(sparse_warnings),
    )


def _append_heading(
    view: HierarchyBundleView,
    regime_id: str,
    key: str,
    level: int,
    stack: list[OpenHeading],
) -> str | None:
    """Close completed branches, attach to the nearest lower level, and warn on gaps."""
    while stack and stack[-1].level >= level:
        stack.pop()

    root_level = view.regimes_by_id[regime_id]["root_level"]
    warning: str | None = None
    if not stack:
        missing = level - root_level
        if missing > 0:
            warning = (
                "sparse hierarchy root: "
                f"regime_root_level={root_level}, child_level={level}, "
                f"missing_intermediate_level_count = {missing}"
            )
    else:
        missing = level - stack[-1].level - 1
        if missing > 0:
            warning = (
                "sparse hierarchy edge: "
                f"parent_level={stack[-1].level}, child_level={level}, "
                f"missing_intermediate_level_count = {missing}"
            )
    stack.append(OpenHeading(level=level, stable_item_key=key))
    return warning
