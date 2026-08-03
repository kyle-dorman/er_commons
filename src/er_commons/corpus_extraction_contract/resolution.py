"""Immutable corpus resolution and candidate-handoff validation."""

from __future__ import annotations

from collections import Counter

from er_commons.corpus_extraction_contract.checks import fail
from er_commons.corpus_extraction_contract.model import IndexEvidence, JsonObject, ScopeEvidence


def validate_resolution_completion(
    completion: JsonObject,
    index: JsonObject,
    scope: ScopeEvidence,
    index_evidence: IndexEvidence,
) -> None:
    """Validate exact mention coverage, candidates, and stage-one immutability."""
    if completion["index_id"] != index["index_id"]:
        fail("stale_resolution", "resolution references a different index")
    mention_ids = [resolution["mention_id"] for resolution in completion["resolutions"]]
    if mention_ids != completion["eligible_mention_ids"] or len(set(mention_ids)) != len(
        mention_ids
    ):
        fail("mention_coverage", "resolution coverage is not exact")
    for resolution in completion["resolutions"]:
        _validate_resolution(resolution, scope, index_evidence)
    _validate_counts(completion)


def _validate_resolution(
    resolution: JsonObject,
    scope: ScopeEvidence,
    index_evidence: IndexEvidence,
) -> None:
    mention_id = resolution["mention_id"]
    candidate_id = resolution["source_candidate_id"]
    if candidate_id not in scope.successful_candidate_ids:
        fail("resolution_source", "mention source candidate is not eligible", subject=mention_id)
    expected_inventory = scope.candidate_inventories[candidate_id]
    before = resolution["source_inventory_before"]
    after = resolution["source_inventory_after"]
    if before != expected_inventory:
        fail("resolution_source", "mention source inventory differs", subject=mention_id)
    if before != after:
        fail("stage_one_mutation", "resolution changed stage-one bytes", subject=mention_id)

    indexed_targets = index_evidence.target_ids_by_lookup_key.get(resolution["lookup_key"], ())
    candidates = resolution["candidate_target_ids"]
    if any(candidate not in indexed_targets for candidate in candidates):
        fail("resolution_target", "candidate is absent from the sealed index", subject=mention_id)
    if candidates != [target for target in indexed_targets if target in set(candidates)]:
        fail(
            "resolution_target", "candidate order differs from the sealed index", subject=mention_id
        )

    expected_status = (
        "unresolved" if not candidates else "resolved" if len(candidates) == 1 else "ambiguous"
    )
    if resolution["status"] != expected_status:
        fail("resolution_cardinality", "status disagrees with candidates", subject=mention_id)
    has_reason = resolution["unresolved_reason"] is not None
    if (expected_status == "unresolved") != has_reason:
        fail("resolution_reason", "unresolved reason disagrees with status", subject=mention_id)
    if (
        resolution["unresolved_reason"] == "target_source_failed"
        and not scope.unavailable_source_ids
    ):
        fail("failed_target_reason", "no failed source supports the reason", subject=mention_id)


def _validate_counts(completion: JsonObject) -> None:
    counts = Counter(resolution["status"] for resolution in completion["resolutions"])
    expected = {
        "total": len(completion["resolutions"]),
        "resolved": counts["resolved"],
        "ambiguous": counts["ambiguous"],
        "unresolved": counts["unresolved"],
    }
    if completion["counts"] != expected:
        fail("resolution_counts", "resolution aggregates do not recompute")


def validate_candidate_handoff(bundle: JsonObject) -> None:
    """Require current prerequisite IDs and the declared failure policy."""
    handoff = bundle["handoff"]
    if (
        handoff["scope_id"] != bundle["accounting"]["scope_id"]
        or handoff["index_id"] != bundle["target_index"]["index_id"]
        or handoff["resolution_id"] != bundle["resolution_completion"]["resolution_id"]
    ):
        fail("handoff_prerequisite", "handoff references stale prerequisites")
    failures = bundle["accounting"]["counts"]["failed_terminal"]
    requires_success = (
        handoff["status"] == "ready" and handoff["blocking_policy"] == "all_sources_successful"
    )
    if requires_success and failures:
        fail("handoff_policy", "ready handoff violates its failure policy")
    if bundle["task04_freezes"]:
        fail("task04_boundary", "Task 03F cannot issue a Task 04 freeze")
