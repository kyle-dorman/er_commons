"""Candidate-neutral evidence for a separate hierarchy authorization decision."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.source_freeze import write_json_atomic

JsonObject = dict[str, Any]


def build_hierarchy_authorization_review(
    *,
    candidate_identity: JsonObject,
    prior_authorization: JsonObject,
    policy_sha256: str,
    expected_semantic_sha256: str,
    observed_semantic_sha256: str,
    expected_counts: JsonObject,
    observed_counts: JsonObject,
) -> JsonObject:
    """Describe a candidate rebind without granting publication authority."""
    candidate_id = candidate_identity.get("candidate_id")
    prior_candidate = prior_authorization.get("candidate")
    prior_identity = prior_candidate.get("identity") if isinstance(prior_candidate, dict) else None
    if not isinstance(candidate_id, str) or not isinstance(prior_identity, dict):
        raise ValueError("authorization review requires current and prior candidate identities")
    semantic_match = observed_semantic_sha256 == expected_semantic_sha256
    counts_match = observed_counts == expected_counts
    return {
        "record_type": "hierarchy_authorization_review",
        "schema_version": "er_commons.hierarchy_authorization_review.v1",
        "candidate_id": candidate_id,
        "prior_candidate_id": prior_identity.get("candidate_id"),
        "review_status": (
            "ready_for_user_review" if semantic_match and counts_match else "blocked"
        ),
        "publication_authority": False,
        "task04_status": "not_evaluated",
        "policy_sha256": policy_sha256,
        "scope": prior_authorization.get("scope"),
        "limitations": prior_authorization.get("limitations"),
        "candidate_identity": candidate_identity,
        "identity_changes": _identity_changes(prior_identity, candidate_identity),
        "semantic_comparison": {
            "expected_sha256": expected_semantic_sha256,
            "observed_sha256": observed_semantic_sha256,
            "exact_match": semantic_match,
        },
        "count_comparison": {
            "expected": expected_counts,
            "observed": observed_counts,
            "exact_match": counts_match,
        },
        "decision_required": (
            "explicit_user_authorization_before_bounded_acceptance_write_or_publication"
        ),
    }


def write_hierarchy_authorization_review(path: Path, report: JsonObject) -> Path:
    """Write review-only evidence that cannot impersonate an authorization."""
    if (
        report.get("record_type") != "hierarchy_authorization_review"
        or report.get("publication_authority") is not False
        or report.get("review_status") not in {"ready_for_user_review", "blocked"}
    ):
        raise ValueError("hierarchy authorization review record is invalid")
    write_json_atomic(path, report)
    return path


def _identity_changes(before: JsonObject, after: JsonObject) -> list[JsonObject]:
    return [
        {"field": field, "before": before.get(field), "after": after.get(field)}
        for field in sorted(before.keys() | after.keys())
        if before.get(field) != after.get(field)
    ]
