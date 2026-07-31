"""Focused tests for named numbering-scope exit lifecycle events."""

from __future__ import annotations

from typing import Any, cast

from er_commons.hierarchy_correction.hierarchy_builder import build_corrected_hierarchy
from er_commons.hierarchy_correction.scope_lifecycle import NumberingScopeLifecycle


def _regime(
    regime_id: str,
    *,
    start: str,
    parent: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    return {
        "regime_id": regime_id,
        "parent_regime_id": parent,
        "root_level": 1,
        "start_item_key": start,
        "end_item_key": end,
        "outline_anchor_key": None,
        "page_label_reset": False,
    }


def _feature(index: int, regime_id: str) -> dict[str, Any]:
    return {
        "stable_item_key": f"item-{index}",
        "reading_order_index": index,
        "regime_id": regime_id,
    }


def _decision(index: int, role: str, level: int | None) -> dict[str, Any]:
    return {
        "stable_item_key": f"item-{index}",
        "corrected_role": role,
        "corrected_level": level,
    }


def test_lifecycle_names_every_enclosing_stack_closed_before_boundary() -> None:
    regimes = (
        _regime("outer-a", start="item-0"),
        _regime("outer-b", start="item-1"),
        _regime("nested-a", start="item-2", parent="outer-a", end="peer-boundary"),
        _regime("nested-b", start="item-3", parent="outer-b", end="peer-boundary"),
        _regime("open-ended", start="item-4", parent="outer-a"),
    )

    lifecycle = NumberingScopeLifecycle.from_regimes(regimes)

    events = lifecycle.before_item("peer-boundary")
    assert [(event.enclosing_regime_id, event.ended_regime_id) for event in events] == [
        ("outer-a", "nested-a"),
        ("outer-b", "nested-b"),
    ]
    assert lifecycle.before_item("item-4") == ()


def test_scope_exit_closes_only_named_parent_stack() -> None:
    features = (
        _feature(0, "outer-a"),
        _feature(1, "outer-b"),
        _feature(2, "nested-a"),
        _feature(3, "outer-b"),
        _feature(4, "outer-a"),
    )
    decisions = (
        _decision(0, "heading", 2),
        _decision(1, "heading", 2),
        _decision(2, "heading", 1),
        _decision(3, "content", None),
        _decision(4, "content", None),
    )
    regimes = (
        _regime("outer-a", start="item-0"),
        _regime("outer-b", start="item-1"),
        _regime("nested-a", start="item-2", parent="outer-a", end="item-3"),
    )

    result = build_corrected_hierarchy(
        features=cast(Any, features),
        decisions=cast(Any, decisions),
        regimes=cast(Any, regimes),
    )

    assert {tuple(item.values()) for item in result.hierarchy["direct_membership"]} == {
        ("item-3", "item-1"),
    }
    assert result.hierarchy["unassigned_content"] == ["item-4"]
