"""Compatibility facade for item observation and text-evidence APIs."""

from er_commons.hierarchy_correction.source_features import (
    TraversedText,
    build_feature_seeds,
    extract_item_observations,
    traverse_provenance_text,
    unique_footer_labels,
)
from er_commons.hierarchy_correction.text_evidence import (
    LayoutEvidence,
    NumberingEvidence,
    align_parsed_line,
    normalize_text,
    parse_numbering,
)

__all__ = [
    "LayoutEvidence",
    "NumberingEvidence",
    "TraversedText",
    "align_parsed_line",
    "build_feature_seeds",
    "extract_item_observations",
    "normalize_text",
    "parse_numbering",
    "traverse_provenance_text",
    "unique_footer_labels",
]
