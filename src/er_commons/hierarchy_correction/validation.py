"""Ordered cross-record policy validation for hierarchy correction v1."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from er_commons.hierarchy_correction.bundle import CorrectionBundleView
from er_commons.hierarchy_correction.decisions import (
    decision_headers_and_evidence_are_consistent,
    decisions_cover_features_in_order,
    feature_records_are_ordered_and_unique,
)
from er_commons.hierarchy_correction.hierarchy import hierarchy_matches_decisions
from er_commons.hierarchy_correction.identity import (
    candidate_identity_matches_digest,
    input_inventory_matches_identity,
)
from er_commons.hierarchy_correction.publication import (
    completion_seals_required_artifacts,
    diagnostics_and_summary_match_decisions,
    metrics_are_internally_consistent,
)
from er_commons.hierarchy_correction.regimes import (
    RegimeTopology,
    features_use_innermost_regime,
)
from er_commons.hierarchy_correction.rules import (
    exact_toc_targets_use_an_anchor_rule,
    selected_rules_follow_policy,
)
from er_commons.hierarchy_correction.toc import (
    toc_reconciliations_are_complete,
    toc_rows_are_ordered_and_owned,
)

PolicyCheck = Callable[[CorrectionBundleView], None]

# Order matters. Early identity, uniqueness, and reference checks establish the
# indexes consumed by the more specific topology and policy checks below.
FOUNDATION_POLICY_CHECKS: tuple[PolicyCheck, ...] = (
    candidate_identity_matches_digest,
    input_inventory_matches_identity,
    feature_records_are_ordered_and_unique,
    decisions_cover_features_in_order,
    decision_headers_and_evidence_are_consistent,
    toc_rows_are_ordered_and_owned,
    toc_reconciliations_are_complete,
)

FINAL_POLICY_CHECKS: tuple[PolicyCheck, ...] = (
    selected_rules_follow_policy,
    exact_toc_targets_use_an_anchor_rule,
    hierarchy_matches_decisions,
    diagnostics_and_summary_match_decisions,
    metrics_are_internally_consistent,
    completion_seals_required_artifacts,
)


def validate_hierarchy_correction_bundle(bundle: dict[str, Any]) -> None:
    """Validate a schema-valid hierarchy-correction bundle.

    JSON Schema owns individual record shapes. This function validates only
    relationships and policy that require the complete bundle.
    """
    view = CorrectionBundleView(bundle)
    for check in FOUNDATION_POLICY_CHECKS:
        check(view)

    topology = RegimeTopology.build(view)
    features_use_innermost_regime(view, topology)

    for check in FINAL_POLICY_CHECKS:
        check(view)
