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

PERMITTED_BRIDGE_DISPOSITIONS = frozenset(
    {
        "canonical_table_replacement_descendant",
        "canonical_figure_suppressed_descendant",
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
