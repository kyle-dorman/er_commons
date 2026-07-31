"""Compatibility facade for visible-TOC analysis."""

from typing import Any, cast

from er_commons.hierarchy_correction.semantic_types import ObservedItem
from er_commons.hierarchy_correction.toc_analysis import (
    TocBuildResult,
)
from er_commons.hierarchy_correction.toc_analysis import (
    build_visible_toc as _build_visible_toc,
)
from er_commons.hierarchy_correction.toc_reconciliation import reconcile_toc_entries
from er_commons.hierarchy_correction.toc_regions import TocRegion, printed_page_observations

JsonObject = dict[str, Any]


def build_visible_toc(
    features: list[JsonObject],
    outline_observations: tuple[JsonObject, ...],
    *,
    native_heading_observations: dict[str, JsonObject] | None = None,
) -> TocBuildResult:
    """Adapt schema-shaped records to the typed TOC analysis stage."""
    return _build_visible_toc(
        cast(list[ObservedItem], features),
        outline_observations,
        native_heading_observations=native_heading_observations,
    )


__all__ = [
    "TocBuildResult",
    "TocRegion",
    "build_visible_toc",
    "printed_page_observations",
    "reconcile_toc_entries",
]
