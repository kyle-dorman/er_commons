"""Coverage, ordering, and shared invariants for correction decisions."""

from __future__ import annotations

from er_commons.hierarchy_correction.bundle import CorrectionBundleView
from er_commons.hierarchy_correction.checks import require, require_sorted, require_unique
from er_commons.hierarchy_correction.constants import RULE_ORDER


def feature_records_are_ordered_and_unique(view: CorrectionBundleView) -> None:
    """Require one feature per stable key in strict producer reading order."""
    require_unique(view.feature_keys, "duplicate feature key")
    reading_order = [item["reading_order_index"] for item in view.features]
    require_sorted(reading_order, "feature order differs")
    require_unique(reading_order, "feature order differs")


def decisions_cover_features_in_order(view: CorrectionBundleView) -> None:
    """Require exactly one serialized decision beside every feature."""
    require_unique(view.decision_keys, "duplicate decision key")
    require(
        set(view.decision_keys) == set(view.feature_keys),
        "decision coverage differs",
    )
    require(view.decision_keys == view.feature_keys, "decision order differs")


def decision_headers_and_evidence_are_consistent(view: CorrectionBundleView) -> None:
    """Validate fields shared by all eight selected-rule policies."""
    precedence = {rule_id: index for index, rule_id in enumerate(RULE_ORDER)}
    known_feature_keys = set(view.features_by_key)

    for decision in view.decisions:
        key = decision["stable_item_key"]
        feature = view.features_by_key[key]
        require(decision["raw_role"] == feature["raw_role"], f"raw role differs: {key}")
        require(decision["raw_level"] == feature["raw_level"], f"raw level differs: {key}")

        eligible_rules = decision["eligible_rule_ids"]
        require(bool(eligible_rules), f"eligible rule list is empty: {key}")
        require(
            eligible_rules == sorted(eligible_rules, key=precedence.__getitem__),
            f"rule precedence differs: {key}",
        )
        require(
            decision["selected_rule_id"] == eligible_rules[0],
            f"selected rule differs: {key}",
        )
        must_select_r01 = feature["content_layer"] == "furniture" or feature["toc_region"]
        require(
            (decision["selected_rule_id"] == "R01_EXCLUDE_NON_BODY_OR_TOC") == must_select_r01,
            f"R01 eligibility differs: {key}",
        )

        evidence = decision["evidence"]
        require(
            set(evidence["source_item_keys"]) <= known_feature_keys,
            f"unknown evidence key: {key}",
        )
        for field_name in ("previous_heading_key", "next_heading_key", "next_item_key"):
            reference = evidence[field_name]
            require(
                reference is None or reference in known_feature_keys,
                f"unknown {field_name}: {key}",
            )

        if decision["corrected_role"] == "heading":
            require(
                isinstance(decision["corrected_level"], int),
                f"heading level absent: {key}",
            )
            require(
                decision["outcome"] != "ambiguous",
                f"ambiguous heading published: {key}",
            )
        else:
            require(decision["corrected_level"] is None, f"non-heading has level: {key}")
