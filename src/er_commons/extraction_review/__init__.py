"""Candidate-neutral comparison and requested-review utilities."""

from er_commons.extraction_review.authorization import (
    build_hierarchy_authorization_review,
    write_hierarchy_authorization_review,
)
from er_commons.extraction_review.comparison import compare_candidate_files, compare_table_evidence
from er_commons.extraction_review.rendering import (
    GeneratedReviewFile,
    RenderRecipe,
    ReviewInput,
    ReviewRequest,
    write_review_manifest,
)

__all__ = [
    "ReviewRequest",
    "ReviewInput",
    "RenderRecipe",
    "GeneratedReviewFile",
    "build_hierarchy_authorization_review",
    "compare_candidate_files",
    "compare_table_evidence",
    "write_hierarchy_authorization_review",
    "write_review_manifest",
]
