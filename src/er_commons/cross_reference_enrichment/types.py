"""Small domain types used by the human-owned cross-reference pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

JsonObject = dict[str, Any]
SECTION_NUMBER_PREFIX = re.compile(r"^([1-9][0-9]*(?:\.[0-9]+)*)\b")


class MentionKind(StrEnum):
    """Supported classes of literal cross-reference mentions."""

    SECTION = "section"
    APPENDIX = "appendix"
    TABLE = "table"
    FIGURE = "figure"
    PRINTED_PAGE = "printed_page"
    DOCUMENT = "document"


class ResolutionStatus(StrEnum):
    """Mechanical status determined only by the number of candidates."""

    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"

    @classmethod
    def from_candidate_count(cls, count: int) -> ResolutionStatus:
        """Map zero, one, or several candidates to the contract status."""
        if count == 0:
            return cls.UNRESOLVED
        if count == 1:
            return cls.RESOLVED
        return cls.AMBIGUOUS


class UnresolvedReason(StrEnum):
    """Closed reasons for a supported mention with no local candidate."""

    NO_LOCAL_ALIAS = "no_local_alias"
    DEFERRED_CROSS_DOCUMENT = "deferred_cross_document"
    EXTERNAL_DOCUMENT = "external_document_outside_corpus"
    TARGET_TYPE_UNAVAILABLE = "accepted_target_type_unavailable"
    OUTSIDE_TABLE_WINDOW = "outside_table_page_window"
    QUALIFIED_EXTERNAL_TABLE = "qualified_external_table_reference"
    MALFORMED_SUPPORTED_FORM = "malformed_supported_form"


@dataclass(frozen=True)
class TextSpan:
    """Half-open Unicode-code-point offsets within one canonical block."""

    start: int
    end: int

    def slice(self, text: str) -> str:
        """Return the literal source substring selected by this span."""
        return text[self.start : self.end]

    def as_json(self) -> list[int]:
        """Serialize the span in canonical schema order."""
        return [self.start, self.end]


@dataclass(frozen=True)
class DetectedMention:
    """One supported literal mention before target lookup."""

    kind: MentionKind
    raw_text: str
    span: TextSpan
    lookup_key: str


@dataclass(frozen=True)
class Diagnostic:
    """One excluded or unsupported surface retained only as a count."""

    category: str
    raw_text: str


@dataclass(frozen=True)
class TargetIndexEntry:
    """One alias-to-target row with independently established evidence."""

    lookup_key: str
    target_type: str
    alias_origin: str
    alias_record_id: str
    target_record_id: str
    upstream_alias_record_id: str | None
    upstream_target_record_id: str
    evidence_kind: str
    evidence_source_record_id: str | None
    evidence_page_id: str | None

    def structural_lookup_keys(self) -> frozenset[str]:
        """Return exact plus explicitly authorized structural keys."""
        keys = {self.lookup_key}
        if self.target_type == "section":
            prefix = _numeric_prefix(self.lookup_key)
            if prefix is not None:
                keys.add(prefix)
        if self.target_type == "page" and self.lookup_key.startswith("page "):
            keys.add(self.lookup_key.removeprefix("page "))
        return frozenset(keys)

    def as_json(self) -> JsonObject:
        """Serialize one target-index row to the frozen schema."""
        return {
            "lookup_key": self.lookup_key,
            "target_type": self.target_type,
            "alias_origin": self.alias_origin,
            "alias_record_id": self.alias_record_id,
            "target_record_id": self.target_record_id,
            "upstream_alias_record_id": self.upstream_alias_record_id,
            "upstream_target_record_id": self.upstream_target_record_id,
            "evidence_kind": self.evidence_kind,
            "evidence_source_record_id": self.evidence_source_record_id,
            "evidence_page_id": self.evidence_page_id,
        }


@dataclass(frozen=True)
class Resolution:
    """Ordered local candidates plus the reason when none exists."""

    candidates: tuple[JsonObject, ...]
    unresolved_reason: UnresolvedReason | None

    @property
    def status(self) -> ResolutionStatus:
        """Derive status mechanically from the candidate count."""
        return ResolutionStatus.from_candidate_count(len(self.candidates))


def _numeric_prefix(value: str) -> str | None:
    """Read a leading dot-delimited key, excluding trailing heading punctuation."""
    match = SECTION_NUMBER_PREFIX.match(value)
    return match.group(1) if match is not None else None
