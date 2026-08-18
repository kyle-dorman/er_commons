"""Small domain types used by the human-owned cross-reference pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from er_commons.document_records.document_references.errors import ContractViolation

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
class TargetCandidate:
    """One typed reference target before frozen-schema serialization."""

    target_type: str
    alias_origin: str
    alias_record_ids: tuple[str, ...]
    target_record_id: str
    upstream_alias_record_ids: tuple[str, ...]
    upstream_target_record_id: str
    evidence: tuple[JsonObject, ...]
    page_distance: int | None = None

    @classmethod
    def from_json(cls, value: JsonObject, *, path: str, record_id: str) -> TargetCandidate:
        """Validate a persisted target at the document-reference boundary."""
        required_lists = ("alias_record_ids", "upstream_alias_record_ids", "evidence")
        if any(not isinstance(value.get(key), list) for key in required_lists):
            raise ContractViolation(
                stage="read_target_candidate",
                invariant="candidate list fields are present",
                path=path,
                record_id=record_id,
            )
        try:
            return cls(
                target_type=str(value["target_type"]),
                alias_origin=str(value["alias_origin"]),
                alias_record_ids=tuple(str(item) for item in value["alias_record_ids"]),
                target_record_id=str(value["target_record_id"]),
                upstream_alias_record_ids=tuple(
                    str(item) for item in value["upstream_alias_record_ids"]
                ),
                upstream_target_record_id=str(value["upstream_target_record_id"]),
                evidence=tuple(value["evidence"]),
                page_distance=(
                    int(value["page_distance"]) if value.get("page_distance") is not None else None
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ContractViolation(
                stage="read_target_candidate",
                invariant="candidate fields match the accepted shape",
                path=path,
                record_id=record_id,
                detail=str(error),
            ) from error

    def as_json(self) -> JsonObject:
        """Serialize without changing the accepted candidate record shape."""
        value: JsonObject = {
            "target_type": self.target_type,
            "alias_origin": self.alias_origin,
            "alias_record_ids": list(self.alias_record_ids),
            "target_record_id": self.target_record_id,
            "upstream_alias_record_ids": list(self.upstream_alias_record_ids),
            "upstream_target_record_id": self.upstream_target_record_id,
            "evidence": list(self.evidence),
        }
        if self.page_distance is not None:
            value["page_distance"] = self.page_distance
        return value


@dataclass(frozen=True)
class Resolution:
    """Ordered local candidates plus the reason when none exists."""

    candidates: tuple[TargetCandidate, ...]
    unresolved_reason: UnresolvedReason | None
    cross_document_evidence: JsonObject | None = None

    @property
    def status(self) -> ResolutionStatus:
        """Derive status mechanically from the candidate count."""
        return ResolutionStatus.from_candidate_count(len(self.candidates))


@dataclass(frozen=True)
class DocumentReferenceMention:
    """Validated persisted mention at the construction/validation boundary."""

    record: JsonObject
    record_id: str
    source_record_id: str
    sequence: int
    kind: MentionKind
    span: TextSpan
    candidates: tuple[TargetCandidate, ...]

    @classmethod
    def from_json(cls, value: JsonObject, *, path: str) -> DocumentReferenceMention:
        """Read fields used by cross-record policy with path and record context."""
        record_id = str(value.get("id", "<missing-id>"))
        try:
            start, end = value["source_charspan"]
            candidates = value["candidates"]
            if not isinstance(candidates, list):
                raise TypeError("candidates is not a list")
            return cls(
                record=dict(value),
                record_id=record_id,
                source_record_id=str(value["source_record_id"]),
                sequence=int(value["sequence"]),
                kind=MentionKind(value["mention_class"]),
                span=TextSpan(int(start), int(end)),
                candidates=tuple(
                    TargetCandidate.from_json(item, path=path, record_id=record_id)
                    for item in candidates
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            if isinstance(error, ContractViolation):
                raise
            raise ContractViolation(
                stage="read_mention",
                invariant="mention fields match the accepted shape",
                path=path,
                record_id=record_id,
                detail=str(error),
            ) from error


def _numeric_prefix(value: str) -> str | None:
    """Read a leading dot-delimited key, excluding trailing heading punctuation."""
    match = SECTION_NUMBER_PREFIX.match(value)
    return match.group(1) if match is not None else None
