"""Small assertion helpers shared by correction policy modules."""

from __future__ import annotations

from collections.abc import Iterable

from er_commons.hierarchy_correction.errors import HierarchyCorrectionContractError


def require(condition: bool, detail: str) -> None:
    """Raise the contract error with one actionable invariant description."""
    if not condition:
        raise HierarchyCorrectionContractError(detail)


def require_unique[Item](values: Iterable[Item], detail: str) -> None:
    """Require a collection to contain no duplicate values."""
    materialized = list(values)
    require(len(materialized) == len(set(materialized)), detail)


def require_sorted(values: Iterable[int], detail: str) -> None:
    """Require integer ordering fields to already be ascending."""
    materialized = list(values)
    require(materialized == sorted(materialized), detail)
