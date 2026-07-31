"""Compatibility facade for numbering-scope analysis."""

from er_commons.hierarchy_correction.numbering_scopes import (
    NumberingScopeAnalysis,
    build_numbering_regimes,
)

RegimeBuildResult = NumberingScopeAnalysis

__all__ = ["RegimeBuildResult", "build_numbering_regimes"]
