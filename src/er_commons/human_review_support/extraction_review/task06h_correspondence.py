"""Fail-closed Task 06H human-disposition correspondence policy."""

from __future__ import annotations

from typing import Any, Literal

from er_commons.artifact_io import canonical_json_sha256

CorrespondenceResult = Literal[
    "reused_unchanged",
    "reused_remapped_equivalent",
    "new_review_required",
    "rejected_ambiguous",
]


def substantive_digest(evidence: dict[str, Any]) -> str:
    """Hash only decision-relevant content after an explicit entity mapping."""
    required = ("text", "tables", "image_attachments", "placement", "context")
    missing = [field for field in required if field not in evidence]
    if missing:
        raise ValueError(f"substantive evidence is incomplete: {', '.join(missing)}")
    return canonical_json_sha256({field: evidence[field] for field in required})


def correspondence_result(
    *,
    classification: str,
    source_change_class: str,
    mapping_cardinality: str,
    old_evidence: dict[str, Any] | None,
    new_evidence: dict[str, Any] | None,
    policy_compatible: bool,
    sample_result: str | None = None,
) -> CorrespondenceResult:
    """Decide reuse without treating namespaced-ID inequality as substantive change."""
    if source_change_class == "substituted_new_source" or classification == "unproven":
        return "new_review_required"
    if mapping_cardinality != "one_to_one":
        return "rejected_ambiguous"
    if not policy_compatible or old_evidence is None or new_evidence is None:
        return "new_review_required"
    if sample_result == "mismatch_invalidate_stratum":
        return "new_review_required"
    if substantive_digest(old_evidence) != substantive_digest(new_evidence):
        return "new_review_required"
    old_ids = old_evidence.get("entity_ids", [])
    new_ids = new_evidence.get("entity_ids", [])
    return "reused_unchanged" if old_ids == new_ids else "reused_remapped_equivalent"


def build_task04_correspondence(
    review_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], ...]:
    """Project accepted 06G classifications into fresh, explicitly nonterminal rows."""
    sources = {str(row["logical_source_id"]): row for row in source_rows}
    result: list[dict[str, Any]] = []
    for row in sorted(review_rows, key=lambda item: str(item["entry_id"])):
        source_id = str(row["source_id"])
        source = sources.get(source_id)
        if source is None:
            raise ValueError(f"review correspondence source is absent: {source_id}")
        classification = str(row["classification"])
        if classification not in {"unchanged", "unproven"}:
            raise ValueError(f"unsupported Task 06G review classification: {classification}")
        baseline = row["baseline_evidence"]
        current = (
            "new_review_required"
            if classification == "unproven"
            else "reuse_candidate_pending_proof"
        )
        result.append(
            {
                "entry_id": str(row["entry_id"]),
                "source_id": source_id,
                "baseline_candidate_id": str(baseline["candidate_id"]),
                "selected_candidate_id": str(source["replacement_candidate_id"]),
                "physical_page": int(baseline["physical_page"]),
                "baseline_disposition": str(baseline["disposition"]),
                "baseline_entity_ids_by_kind": baseline["entity_ids_by_kind"],
                "source_change_class": str(source["change_class"]),
                "task06g_classification": classification,
                "correspondence_result": current,
                "policy_status": "pending_substantive_correspondence_proof",
                "sample_status": "selected_pending_visual_review" if False else "not_sampled",
            }
        )
    counts = {
        "unchanged": sum(row["task06g_classification"] == "unchanged" for row in result),
        "unproven": sum(row["task06g_classification"] == "unproven" for row in result),
    }
    if len(result) != 757 or counts != {"unchanged": 706, "unproven": 51}:
        raise ValueError(f"Task 04 correspondence closure differs: {counts}")
    return tuple(result)


def exclusion_correspondence(
    exclusions: list[dict[str, Any]], comparison_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], ...]:
    """Rebind exclusions only when the complete candidate set remains unchanged."""
    comparisons = {str(row["mention_key"]): row for row in comparison_rows}
    output: list[dict[str, Any]] = []
    for old in sorted(exclusions, key=lambda row: str(row["reference_id"])):
        reference_id = str(old["reference_id"])
        marker = "/cross-reference/"
        if marker not in reference_id:
            raise ValueError(f"historical exclusion has unsupported reference ID: {reference_id}")
        mention_key = "cross-reference/" + reference_id.split(marker, 1)[1]
        current = comparisons.get(mention_key)
        baseline_candidates = sorted(
            str(value).split("/", 1)[1] if "/" in str(value) else str(value)
            for value in old["machine_evidence"]["candidate_target_ids"]
        )
        comparison_candidates = (
            []
            if current is None
            else sorted(
                str(value["target_record_id"]) for value in current["baseline"]["candidates"]
            )
        )
        mapped = (
            current is not None
            and current.get("classification") == "unchanged"
            and baseline_candidates == comparison_candidates
            and current["baseline"]["candidates"] == current["replacement"]["candidates"]
        )
        output.append(
            {
                "historical_reference_id": reference_id,
                "mention_key": mention_key,
                "source_id": str(old["source_id"]),
                "result": (
                    "excluded_rebound" if mapped else "historical_exclusion_no_current_counterpart"
                ),
                "link_promoted": False,
            }
        )
    if len(output) != 725 or len({row["historical_reference_id"] for row in output}) != 725:
        raise ValueError("Task 04 ambiguous exclusion closure differs from 725 unique entries")
    return tuple(output)


__all__ = [
    "build_task04_correspondence",
    "correspondence_result",
    "exclusion_correspondence",
    "substantive_digest",
]
