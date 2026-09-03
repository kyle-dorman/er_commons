"""Frozen policy values for the Task 03J final review pass."""

from __future__ import annotations

from typing import Any

FINAL_PASS = "task03j_final"
FINAL_SCHEMA_VERSION = "er_commons.task04a_review.v1"


def final_review_policy() -> dict[str, Any]:
    """Return the immutable Gate A policy for the final review extension."""
    return {
        "pass": FINAL_PASS,
        "source_scope": "all_35_task03j_terminal_sources_in_activation_plan_order",
        "selection": {
            "per_source_page_floor": 3,
            "main_report_page_floor": 8,
            "warning_sampling": "one_representative_per_normalized_warning_class",
            "failure_sampling": "every_terminal_failure_and_recovered_attempt_history",
            "table_sampling": (
                "all_selected_navigation_tables_plus_two_substantive_controls_per_source"
            ),
        },
        "toc_candidate_census": {
            "signals": [
                "canonical_toc_block",
                "canonical_toc_placement",
                "canonical_toc_table",
                "table_under_navigation_ancestry",
                "hierarchy_visible_toc_evidence",
                "document_index_table_stage",
                "raw_docling_document_index",
                "page_furniture_or_heading",
                "plausible_navigation_layout",
                "ambiguous_toc_alias",
                "ambiguous_reference_link",
                "substantive_table_control",
            ],
            "signal_precedence": "union_without_classification_or_extraction_mutation",
            "adjacency_rule": "include_immediate_physical_neighbors_of_each_seed_page",
            "raw_evidence_rule": "stream_raw_docling_json_assets_only;never_read_source_pdf",
            "ordering": "source_ordinal,physical_page,candidate_page_id",
            "population_claim": "complete_for_frozen_machine_detectable_signals_only",
        },
        "human_fields": {
            "page_role": [
                "toc_or_document_index",
                "list_of_tables_or_figures",
                "substantive_table",
                "mixed",
                "neither",
            ],
            "representation": [
                "correct_toc_blocks",
                "incorrect_generic_table",
                "missing_or_suppressed_text",
                "duplicate_representation",
                "incorrect_heading_or_ownership",
                "incorrect_order",
                "other",
            ],
            "navigation_outcome": ["usable", "usable_with_limitation", "repair_required"],
            "alias_outcome": ["intended_body_target", "unresolved"],
        },
        "approval_boundary": {
            "gate_a": "machine_artifact_validation_and_source_free_workload_only",
            "gate_b": "source_free_final_mode_qualification",
            "gate_c": "explicit_approval_required_before_pdf_reads_or_renders",
            "gate_d": "human_dispositions_required_before_freeze",
        },
    }


__all__ = ["FINAL_PASS", "FINAL_SCHEMA_VERSION", "final_review_policy"]
