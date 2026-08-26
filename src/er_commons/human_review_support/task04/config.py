"""Review policy constants for the completed Task 04 first pass."""

from __future__ import annotations

from er_commons.human_review_support.task04.models import JsonValue

SCHEMA_VERSION = "er_commons.task04_review.v1"
REVIEW_PASS = "task03h_first"
MAIN_SOURCE_ID = "deir_main"
RENDER_SCALE = 1.0


def review_policy() -> dict[str, JsonValue]:
    """Return the explicit, identity-bound first-pass selection policy."""
    return {
        "candidate_selection": "lexicographic_complete_success_candidate",
        "valid_pages": (
            "highest_content_score_in_early_middle_late_regions_plus_content_bearing_main_chapters"
        ),
        "warnings": (
            "one_representative_per_normalized_producer_and_canonicalization_class_"
            "with_population_counts_and_exact_or_labeled_context_page"
        ),
        "failures": "source_grouped_attempt_history_with_recovered_or_unresolved_status",
        "review_layout": ("wide_side_by_side_source_and_canonical_evidence_with_region_overlays"),
        "main_table_limit": 6,
        "appendix_table_limit": 2,
        "appendix_table_rule": "largest_multi_page_families_only",
        "renderer": "pypdfium2",
        "render_scale": RENDER_SCALE,
    }


__all__ = ["MAIN_SOURCE_ID", "RENDER_SCALE", "REVIEW_PASS", "SCHEMA_VERSION", "review_policy"]
