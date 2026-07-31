"""Compatibility facade for corrected hierarchy projection."""

from typing import Any, cast

from er_commons.hierarchy_correction.hierarchy_projection import (
    HierarchyBuildResult,
)
from er_commons.hierarchy_correction.hierarchy_projection import (
    build_corrected_hierarchy as _build_corrected_hierarchy,
)
from er_commons.hierarchy_correction.semantic_types import (
    CorrectionDecisionRecord,
    NumberingScopeRecord,
    ScopedItem,
)

JsonRecord = dict[str, Any]


def build_corrected_hierarchy(
    *,
    features: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
    regimes: tuple[JsonRecord, ...],
) -> HierarchyBuildResult:
    """Adapt persisted records to the typed hierarchy projection stage."""
    return _build_corrected_hierarchy(
        features=cast(tuple[ScopedItem, ...], features),
        decisions=cast(tuple[CorrectionDecisionRecord, ...], decisions),
        regimes=cast(tuple[NumberingScopeRecord, ...], regimes),
    )


__all__ = ["HierarchyBuildResult", "build_corrected_hierarchy"]
