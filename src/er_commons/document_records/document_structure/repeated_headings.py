"""Public Task 06D repeated chapter-heading policy and projection API."""

from er_commons.document_records.document_structure.repeated_heading_policy import (
    HeadingTopology,
    RepeatedHeadingDecision,
    TocHeadingEvidence,
    classify_repeated_heading_group,
)
from er_commons.document_records.document_structure.repeated_heading_projection import (
    RepeatedHeadingProjection,
    build_repeated_heading_correspondence,
    project_repeated_heading_decisions,
    redirect_repeated_heading_alias_seeds,
)

__all__ = [
    "HeadingTopology",
    "RepeatedHeadingDecision",
    "RepeatedHeadingProjection",
    "TocHeadingEvidence",
    "build_repeated_heading_correspondence",
    "classify_repeated_heading_group",
    "project_repeated_heading_decisions",
    "redirect_repeated_heading_alias_seeds",
]
