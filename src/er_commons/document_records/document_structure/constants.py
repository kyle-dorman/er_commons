"""Candidate-neutral policy constants used by the semantic contract."""

SEMANTIC_COUNT_FIELDS = frozenset(
    {
        "features",
        "toc_entries",
        "reconciliations",
        "regimes",
        "decisions",
        "roots",
        "edges",
        "direct_membership",
        "unassigned_content",
        "ambiguities",
        "warnings",
    }
)

TABLE_REPLACEMENT_DISPOSITIONS = frozenset(
    {
        "canonical_table_replacement_descendant",
        "canonical_table_geometry_owned_text",
    }
)

PERMITTED_BRIDGE_DISPOSITIONS = frozenset(
    {
        *TABLE_REPLACEMENT_DISPOSITIONS,
        "canonical_figure_suppressed_descendant",
        "canonical_invalid_provenance_suppressed",
    }
)

ALLOWED_DIFFERENCE_CATEGORIES = (
    "identity_and_schema",
    "semantic_sections_and_membership",
    "page_label_resolution_and_observations",
    "target_aliases",
    "semantic_support_and_completion",
)

ALIAS_TARGET_TYPES = frozenset({"document", "page", "section", "table", "figure"})
