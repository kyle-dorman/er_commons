"""Contextual failures for deterministic range recomposition."""

from __future__ import annotations

from typing import Never

from er_commons.chunked_conversion.range_contract import RangePlan


class RangeRecompositionError(ValueError):
    """Range evidence cannot produce one closed canonical conversion."""


def fail(
    plan: RangePlan,
    path: str,
    invariant: str,
    expected: object,
    actual: object,
) -> Never:
    """Raise one stable diagnostic naming the plan, path, and failed invariant."""
    raise RangeRecompositionError(
        f"plan={plan.plan_id} path={path} invariant={invariant} "
        f"expected={expected!r} actual={actual!r}"
    )


__all__ = ["RangeRecompositionError", "fail"]
