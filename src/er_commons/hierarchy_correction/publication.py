"""Summary, measurement, inventory, and completion policies."""

from __future__ import annotations

import math

from er_commons.hierarchy_correction.bundle import CorrectionBundleView, JsonRecord
from er_commons.hierarchy_correction.checks import require, require_sorted, require_unique
from er_commons.hierarchy_correction.constants import MANAGED_PAYLOAD_PATHS, RULE_ORDER
from er_commons.hierarchy_correction.digests import canonical_json_sha256


def diagnostics_and_summary_match_decisions(view: CorrectionBundleView) -> None:
    """Match diagnostics, role counts, and status to serialized decisions."""
    bundle = view.bundle
    summary = bundle["summary"]
    identity = bundle["identity"]
    require(summary["candidate_id"] == identity["candidate_id"], "summary candidate differs")
    require(summary["feature_count"] == len(view.features), "summary feature count differs")
    require(summary["decision_count"] == len(view.decisions), "summary decision count differs")

    selected_counts = {rule_id: 0 for rule_id in RULE_ORDER}
    eligible_not_selected_counts = {rule_id: 0 for rule_id in RULE_ORDER}
    for decision in view.decisions:
        selected_rule_id = decision["selected_rule_id"]
        selected_counts[selected_rule_id] += 1
        for eligible_rule_id in decision["eligible_rule_ids"]:
            if eligible_rule_id != selected_rule_id:
                eligible_not_selected_counts[eligible_rule_id] += 1
    require(
        summary["selected_rule_counts"] == selected_counts,
        "summary selected rule counts differ",
    )
    require(
        summary["eligible_not_selected_rule_counts"] == eligible_not_selected_counts,
        "summary eligible-not-selected rule counts differ",
    )

    for role in ("heading", "content", "excluded"):
        actual_count = sum(item["corrected_role"] == role for item in view.decisions)
        require(summary[f"{role}_count"] == actual_count, f"summary {role} count differs")

    ambiguities = bundle["ambiguities"]
    warnings = bundle["warnings"]
    require(summary["ambiguity_count"] == len(ambiguities), "ambiguity count differs")
    require(summary["warning_count"] == len(warnings), "summary warning count differs")
    _require_diagnostics_in_order("ambiguities", ambiguities)
    _require_diagnostics_in_order("warnings", warnings)

    ambiguous_decisions = {
        item["stable_item_key"] for item in view.decisions if item["outcome"] == "ambiguous"
    }
    diagnosed_ambiguities = {
        item["stable_item_key"] for item in ambiguities if item["stable_item_key"] is not None
    }
    require(
        ambiguous_decisions == diagnosed_ambiguities,
        "ambiguity diagnostic coverage differs",
    )

    expected_status = "complete_with_ambiguities" if ambiguities else "complete"
    require(summary["status"] == expected_status, "summary ambiguity status differs")


def metrics_are_internally_consistent(view: CorrectionBundleView) -> None:
    """Recompute median, ratios, and the cheapness disposition."""
    metrics = view.bundle["metrics"]
    candidate_id = view.bundle["identity"]["candidate_id"]
    require(metrics["candidate_id"] == candidate_id, "metrics candidate differs")

    wall_times = sorted(metrics["fresh_wall_time_seconds"])
    require(metrics["median_fresh_wall_time_seconds"] == wall_times[1], "metrics median differs")
    require(
        math.isclose(
            metrics["wall_time_ratio"],
            metrics["median_fresh_wall_time_seconds"] / metrics["producer_build_wall_time_seconds"],
        ),
        "wall-time ratio differs",
    )
    require(
        metrics["artifact_bytes_ratio"]
        == round(metrics["artifact_bytes"] / metrics["producer_bytes"], 6),
        "artifact-byte ratio differs",
    )
    expected_cheapness = (
        metrics["median_fresh_wall_time_seconds"] < metrics["producer_build_wall_time_seconds"]
        and metrics["artifact_bytes"] < metrics["producer_bytes"]
    )
    require(
        metrics["cheap_relative_to_producer"] == expected_cheapness,
        "cheapness disposition differs",
    )


def completion_seals_required_artifacts(view: CorrectionBundleView) -> None:
    """Require the exact artifact set and bind completion to its inventory."""
    bundle = view.bundle
    summary = bundle["summary"]
    completion = bundle["completion"]
    inventory = bundle["artifact_inventory"]

    candidate_id = bundle["identity"]["candidate_id"]
    require(completion["candidate_id"] == candidate_id, "completion candidate differs")
    require(completion["status"] == summary["status"], "completion status differs")

    paths = [item["path"] for item in inventory["files"]]
    require_unique(paths, "duplicate artifact inventory path")
    require(paths == list(MANAGED_PAYLOAD_PATHS), "artifact inventory paths differ")
    require(
        completion["artifact_inventory_sha256"] == canonical_json_sha256(inventory),
        "artifact inventory seal differs",
    )


def _require_diagnostics_in_order(name: str, diagnostics: list[JsonRecord]) -> None:
    reading_order = [
        -1 if item["reading_order_index"] is None else item["reading_order_index"]
        for item in diagnostics
    ]
    require_sorted(reading_order, f"{name} order differs")
