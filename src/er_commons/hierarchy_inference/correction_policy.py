"""Orchestrate ordered R01-R08 eligibility and rule application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.hierarchy_inference.rule_applications import apply_selected_rule
from er_commons.hierarchy_inference.rule_context import (
    build_item_rule_context,
    build_rule_policy_context,
)
from er_commons.hierarchy_inference.semantic_types import (
    DiagnosticRecord,
    HierarchyDecisionRecord,
    NumberingScopeRecord,
    ScopedItem,
)

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class DecisionBuildResult:
    """Ordered decisions and their fail-closed ambiguity diagnostics."""

    decisions: tuple[HierarchyDecisionRecord, ...]
    ambiguities: tuple[DiagnosticRecord, ...]


def build_rule_decisions(
    *,
    features: tuple[ScopedItem, ...],
    toc_entries: tuple[JsonRecord, ...],
    reconciliations: tuple[JsonRecord, ...],
    regimes: tuple[NumberingScopeRecord, ...],
) -> DecisionBuildResult:
    """Select and apply one terminal rule per item from immutable evidence."""
    policy = build_rule_policy_context(
        features=features,
        toc_entries=toc_entries,
        reconciliations=reconciliations,
        regimes=regimes,
    )
    decisions: list[HierarchyDecisionRecord] = []
    ambiguities: list[DiagnosticRecord] = []
    for index in range(len(features)):
        application = apply_selected_rule(build_item_rule_context(policy, index))
        decisions.append(application.decision)
        ambiguities.extend(application.ambiguities)
    return DecisionBuildResult(
        tuple(decisions),
        tuple(ambiguities),
    )
