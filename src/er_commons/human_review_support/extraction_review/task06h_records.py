"""Pure terminal-record validators for the Task 06H review boundary."""

from __future__ import annotations

from typing import Any

from er_commons.artifact_io import canonical_json_sha256

TERMINAL_VALUES = {
    "mechanical_readiness": {"ready_for_review", "not_ready"},
    "exact_target_identity": {"confirmed", "rejected", "not_applicable"},
    "human_usability": {"usable", "usable_with_limitation", "unusable"},
    "visual_evidence_quality": {
        "legible",
        "legible_with_limitation",
        "illegible",
        "not_applicable",
    },
    "text_only_model_eligibility": {
        "eligible",
        "eligible_with_warning",
        "unavailable_to_text_only_model",
        "not_evaluated_not_applicable",
    },
    "overall_review": {"accepted", "accepted_with_limitation", "rejected_repair_required"},
}
REQUIRED_METADATA = {
    "reviewer",
    "reviewed_at",
    "question_version",
    "source_id",
    "document_id",
    "stable_correspondence_key",
    "evidence_refs",
    "rationale",
    "limitations",
}


def validate_terminal_disposition(row: dict[str, Any]) -> None:
    """Require all six dimensions and provenance without inferring one from another."""
    missing = sorted((set(TERMINAL_VALUES) | REQUIRED_METADATA) - set(row))
    if missing:
        raise ValueError(f"Task 06H disposition is incomplete: {', '.join(missing)}")
    for field, values in TERMINAL_VALUES.items():
        if row[field] not in values:
            raise ValueError(f"Task 06H disposition has nonterminal {field}: {row[field]}")
    for field in REQUIRED_METADATA - {"limitations"}:
        if row[field] in (None, "", []):
            raise ValueError(f"Task 06H disposition has empty required field: {field}")
    if not isinstance(row["limitations"], list):
        raise ValueError("Task 06H disposition limitations must be a list")


def merge_disposition(
    journal: dict[str, dict[str, Any]], row: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Accept an identical replay and reject a conflicting answer for one stable key."""
    validate_terminal_disposition(row)
    key = str(row["stable_correspondence_key"])
    previous = journal.get(key)
    if previous is not None and canonical_json_sha256(previous) != canonical_json_sha256(row):
        raise ValueError(f"conflicting Task 06H disposition: {key}")
    return {**journal, key: row}


def validate_registry(
    *,
    source_rows: list[dict[str, Any]],
    expected_source_ids: set[str],
    target_rows: list[dict[str, Any]],
    expected_target_ids: set[str],
    exclusions: list[dict[str, Any]],
    task03i: dict[str, Any],
) -> None:
    """Require exact source, target, exclusion, and Task 03I membership closure."""
    source_ids = [str(row["source_id"]) for row in source_rows]
    target_ids = [str(row["target_id"]) for row in target_rows]
    if (
        len(source_ids) != 35
        or len(set(source_ids)) != 35
        or set(source_ids) != expected_source_ids
    ):
        raise ValueError("Task 06H registry source membership differs")
    if len(target_ids) != len(set(target_ids)) or set(target_ids) != expected_target_ids:
        raise ValueError("Task 06H registry target membership differs")
    exclusion_ids = [str(row["historical_reference_id"]) for row in exclusions]
    allowed = {"excluded_rebound", "historical_exclusion_no_current_counterpart"}
    if (
        len(exclusion_ids) != 725
        or len(set(exclusion_ids)) != 725
        or any(
            row.get("result") not in allowed or row.get("link_promoted") is not False
            for row in exclusions
        )
    ):
        raise ValueError("Task 06H registry exclusion closure differs")
    if task03i.get("source_id") != "deir_appendix_k2_part_5_of_5" or task03i.get(
        "physical_pages"
    ) != list(range(974, 984)):
        raise ValueError("Task 06H registry Task 03I mapping differs")


def acceptance_id(bindings: dict[str, Any]) -> str:
    """Derive acceptance identity only from a complete mechanical and human closure."""
    required = {
        "mechanical_handoff_id",
        "readiness_sha256",
        "review_completion_sha256",
        "correspondence_completion_sha256",
        "registry_id",
        "source_substitution",
        "limitations_sha256",
        "task05g_handoff_sha256",
    }
    missing = sorted(required - set(bindings))
    if missing:
        raise ValueError(f"Task 06H acceptance binding is incomplete: {', '.join(missing)}")
    if bindings.get("mechanical_status") != "ready_for_review":
        raise ValueError("Task 06H acceptance mechanical gate is not ready")
    if bindings.get("human_review_status") not in {"accepted", "accepted_with_limitation"}:
        raise ValueError("Task 06H acceptance human gate is incomplete")
    return "acceptv1-" + canonical_json_sha256(bindings)


__all__ = [
    "TERMINAL_VALUES",
    "acceptance_id",
    "merge_disposition",
    "validate_registry",
    "validate_terminal_disposition",
]
