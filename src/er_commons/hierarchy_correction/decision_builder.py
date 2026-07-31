"""Compatibility facade for correction-policy application."""

from er_commons.hierarchy_correction.correction_policy import (
    DecisionBuildResult,
    build_rule_decisions,
)

__all__ = ["DecisionBuildResult", "build_rule_decisions"]
