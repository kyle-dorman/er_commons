"""Public Task 06E missing whole-chapter policy and projection API."""

from er_commons.document_records.document_structure.missing_chapter_policy import (
    ChapterBoundaryEvidence,
    ChapterChildEvidence,
    ChapterHeadingComponent,
    ChapterTocEvidence,
    MissingChapterDecision,
    MissingChapterEvidence,
    classify_missing_chapter,
)
from er_commons.document_records.document_structure.missing_chapter_projection import (
    MissingChapterProjection,
    build_missing_chapter_alias_seeds,
    build_missing_chapter_correspondence,
    prefer_missing_chapter_alias_evidence,
    project_missing_chapter_decisions,
)

__all__ = [
    "ChapterBoundaryEvidence",
    "ChapterChildEvidence",
    "ChapterHeadingComponent",
    "ChapterTocEvidence",
    "MissingChapterDecision",
    "MissingChapterEvidence",
    "classify_missing_chapter",
    "MissingChapterProjection",
    "build_missing_chapter_alias_seeds",
    "build_missing_chapter_correspondence",
    "prefer_missing_chapter_alias_evidence",
    "project_missing_chapter_decisions",
]
