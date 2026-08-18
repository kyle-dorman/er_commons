"""Stable public facade for the bounded learned-table fallback.

Responsibility-owned implementation modules keep OTSL parsing, native-text
ownership, acceptance policy, and model execution independently reviewable.
"""

from er_commons.document_parsing.table_reconstruction.learned_table_acceptance import (
    evaluate_prediction,
    unmatched_layout_regions,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import (
    FallbackAttempt,
    LearnedFallbackRunner,
)
from er_commons.document_parsing.table_reconstruction.tableformer_fallback import (
    VerifiedTableFormerFallback,
)

__all__ = [
    "FallbackAttempt",
    "LearnedFallbackRunner",
    "VerifiedTableFormerFallback",
    "evaluate_prediction",
    "unmatched_layout_regions",
]
