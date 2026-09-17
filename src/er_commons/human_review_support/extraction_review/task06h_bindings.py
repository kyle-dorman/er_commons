"""Explicit substitution and repair-owner bindings for Task 06H."""

from __future__ import annotations

from typing import Any

JsonObject = dict[str, Any]


def terminal_dimensions() -> JsonObject:
    """Keep the five evidence dimensions and overall result independently terminal."""
    return {
        "mechanical_readiness": ["ready_for_review", "not_ready"],
        "exact_target_identity": ["confirmed", "rejected", "not_applicable"],
        "human_usability": ["usable", "usable_with_limitation", "unusable"],
        "visual_evidence_quality": [
            "legible",
            "legible_with_limitation",
            "illegible",
            "not_applicable",
        ],
        "text_only_model_eligibility": [
            "eligible",
            "eligible_with_warning",
            "unavailable_to_text_only_model",
            "not_evaluated_not_applicable",
        ],
        "overall_review": ["accepted", "accepted_with_limitation", "rejected_repair_required"],
    }


def figure_controls(qualification: JsonObject, mapped: tuple[JsonObject, ...]) -> JsonObject:
    """Retain all 96 negative controls separately from 178 eligible targets."""
    decisions = qualification.get("decisions")
    if not isinstance(decisions, list) or any(not isinstance(row, dict) for row in decisions):
        raise ValueError("Task 06F decisions must be a list of objects")
    rejected = [row for row in decisions if row.get("eligibility") == "rejected"]
    if len(rejected) != 96 or len(mapped) != 178:
        raise ValueError("Task 06F positive/negative-control closure differs")
    return {
        "eligible_target_count": 178,
        "eligible_page_count": len({row["physical_page_number"] for row in mapped}),
        "rejected_negative_control_count": 96,
        "negative_controls": sorted(rejected, key=lambda value: str(value.get("figure_id"))),
        "figure_4_8_exact_target_count": 0,
        "marker_truncation_allowed": False,
        "text_only_status": "pending_independent_human_disposition",
    }


def source_substitution(source_rows: list[JsonObject]) -> JsonObject:
    """Bind the Draft-to-Final F1 substitution without asserting equivalence."""
    row = next(
        value for value in source_rows if value.get("logical_source_id") == "deir_appendix_f1"
    )
    baseline = _object(row, "baseline_source")
    selected = _object(row, "selected_source")
    if (
        row.get("semantic_equivalence") is not False
        or row.get("change_class") != "substituted_new_source"
    ):
        raise ValueError("Final F1 substitution classification differs")
    return {
        "logical_source_id": "deir_appendix_f1",
        "owner": "task06c",
        "classification": "new_source_addition_no_old_entity_equivalence",
        "baseline": {
            "source_id": baseline["source_id"],
            "candidate_id": row["baseline_candidate_id"],
            "sha256": baseline["sha256"],
            "pdf_page_count": baseline["pdf_page_count"],
        },
        "selected": {
            "source_id": selected["source_id"],
            "candidate_id": row["replacement_candidate_id"],
            "sha256": selected["sha256"],
            "pdf_page_count": selected["pdf_page_count"],
        },
        "semantic_equivalence": False,
        "draft_final_equivalence_proven": False,
    }


def repair_owner_evidence(
    targets: tuple[JsonObject, ...], figure_mappings: tuple[JsonObject, ...]
) -> JsonObject:
    """Bind every targeted repair class to its accepted owner and exact targets."""
    appendix = [row["target_id"] for row in targets if row["target_kind"] == "repaired_section"]
    chapters = [row["target_id"] for row in targets if row["target_kind"] == "repaired_chapter"]
    figures = [row["selected_figure_id"] for row in figure_mappings]
    if (len(appendix), len(chapters), len(figures)) != (4, 2, 178):
        raise ValueError("Task 06H repair-owner population differs")
    return {
        "task06d": {
            "qualification": "qualification_v8",
            "target_ids": appendix,
            "accepted_seals": ["06d_completion", "06d_qualification", "06d_decisions"],
        },
        "task06e": {
            "qualification": "qualification_v17",
            "target_ids": chapters,
            "accepted_seals": ["06e_completion", "06e_qualification", "06e_decisions"],
        },
        "task06f": {
            "qualification": "qualification_v10",
            "selected_figure_ids": figures,
            "accepted_seals": ["06f_completion", "06f_qualification", "06f_aliases", "06f_targets"],
            "alias_resolution_implies_text_only_support": False,
        },
    }


def _object(value: JsonObject, field: str) -> JsonObject:
    result = value.get(field)
    if not isinstance(result, dict):
        raise ValueError(f"Task 06H field must be an object: {field}")
    return result


__all__ = [
    "figure_controls",
    "repair_owner_evidence",
    "source_substitution",
    "terminal_dimensions",
]
