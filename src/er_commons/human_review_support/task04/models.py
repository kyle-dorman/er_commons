"""Typed internal contracts for the Task 04 review-bundle application."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from er_commons.human_review_support.task04.scope_policy import InputScopePolicy

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]


class ReviewQueue(StrEnum):
    """The four user-visible Task 04 review queues."""

    FAILURE = "failure"
    WARNING = "warning"
    VALID_PAGE = "valid_page"
    TABLE = "table"


@dataclass(frozen=True)
class BuildRequest:
    """Filesystem inputs for one immutable first-pass review build."""

    retained_root: Path
    data_root: Path
    output_root: Path
    input_scope: InputScopePolicy = field(default_factory=InputScopePolicy.production)


@dataclass(frozen=True)
class IdentityDependency:
    """One inspectable maintained-code, asset, schema, or package identity input."""

    name: str
    kind: str
    path: str | None
    sha256: str | None
    version: str | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize the dependency with all identity fields explicit."""
        return {
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "version": self.version,
        }


@dataclass(frozen=True)
class BuildIdentity:
    """Content-bound identity and policy for one review run."""

    review_run_id: str
    policy: Mapping[str, JsonValue]
    policy_sha256: str
    implementation_sha256: str
    input_sha256: str
    dependencies: tuple[IdentityDependency, ...]


@dataclass(frozen=True)
class SourceEvidence:
    """Resolved source and selected-candidate evidence used by queue builders."""

    source_id: str
    document_role: str | None
    parent_source_id: str | None
    sha256: str
    byte_size: int
    pdf_page_count: int
    source_relative_path: str
    source_pdf: Path
    source_pdf_sha256: str | None
    candidate_ids: tuple[str, ...]
    selected_candidate: Path | None
    selected_completion_sha256: str | None
    selected_inventory_sha256: str | None

    @property
    def selected_candidate_id(self) -> str | None:
        """Return the selected candidate identity without exposing path conventions."""
        return self.selected_candidate.name if self.selected_candidate is not None else None

    def inventory_record(self) -> dict[str, JsonValue]:
        """Serialize the source into the strict input-inventory contract."""
        return {
            "source_id": self.source_id,
            "document_role": self.document_role,
            "parent_source_id": self.parent_source_id,
            "sha256": self.sha256,
            "byte_size": self.byte_size,
            "pdf_page_count": self.pdf_page_count,
            "source_relative_path": self.source_relative_path,
            "source_exists": self.source_pdf.is_file(),
            "source_pdf_sha256": self.source_pdf_sha256,
            "candidate_ids": list(self.candidate_ids),
            "selected_candidate_id": self.selected_candidate_id,
            "selected_completion_sha256": self.selected_completion_sha256,
            "selected_inventory_sha256": self.selected_inventory_sha256,
            "evidence_status": (
                "available"
                if self.selected_candidate is not None
                else "missing_publication_evidence"
            ),
        }


@dataclass(frozen=True)
class PageProfile:
    """Compact page evidence used for content-aware review selection."""

    physical_page: int
    body_text_chars: int = 0
    body_block_count: int = 0
    heading_count: int = 0
    list_item_count: int = 0
    table_count: int = 0
    table_text_chars: int = 0

    def __post_init__(self) -> None:
        values = (
            self.physical_page,
            self.body_text_chars,
            self.body_block_count,
            self.heading_count,
            self.list_item_count,
            self.table_count,
            self.table_text_chars,
        )
        if self.physical_page < 1 or any(value < 0 for value in values[1:]):
            raise ValueError("page profile values must be non-negative")

    @property
    def review_score(self) -> int:
        """Rank substantial body content while leaving tables to their own queue."""
        return (
            min(self.body_text_chars, 6_000)
            + min(self.body_block_count, 30) * 20
            + self.heading_count * 120
            + self.list_item_count * 35
            + min(self.table_text_chars, 2_000) // 10
            - self.table_count * 100
        )

    @property
    def is_content_bearing(self) -> bool:
        """Return whether the page has enough evidence for useful visual review."""
        return (
            self.body_text_chars >= 200
            or self.body_block_count >= 4
            or self.table_text_chars >= 200
        )


@dataclass(frozen=True)
class WarningInstance:
    """One retained warning occurrence before class-based sampling."""

    source_id: str
    owner: str
    code: str
    message: str
    evidence_id: str = ""

    def __post_init__(self) -> None:
        if not all((self.source_id, self.owner, self.code, self.message)):
            raise ValueError("warning instances require source, owner, code, and message")


@dataclass(frozen=True)
class WarningClass:
    """A normalized warning population with one deterministic representative."""

    fingerprint: str
    occurrence_count: int
    raw_occurrence_count: int
    source_counts: tuple[tuple[str, int], ...]
    owner_code_counts: tuple[tuple[str, str, int], ...]
    representative: WarningInstance

    @property
    def owners(self) -> tuple[str, ...]:
        """Return structured owner labels without flattening their identity."""
        return tuple(sorted({owner for owner, _, _ in self.owner_code_counts}))

    @property
    def codes(self) -> tuple[str, ...]:
        """Return structured diagnostic codes without flattening their identity."""
        return tuple(sorted({code for _, code, _ in self.owner_code_counts}))


@dataclass(frozen=True)
class TableFamilyCandidate:
    """A source-free table-family summary eligible for bounded selection."""

    source_id: str
    family_id: str
    page_count: int
    table_count: int = 0

    def __post_init__(self) -> None:
        if not self.source_id or not self.family_id:
            raise ValueError("table candidates require source and family IDs")
        if self.page_count < 1 or self.table_count < 0:
            raise ValueError("table candidate counts are invalid")


@dataclass(frozen=True)
class AttemptEvidence:
    """One retained non-success document-processing attempt."""

    attempt_id: str
    disposition: str
    failure_class: str | None
    stage: str
    detail: str
    relative_path: str

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize this attempt for a failure review item."""
        return {
            "attempt_id": self.attempt_id,
            "disposition": self.disposition,
            "failure_class": self.failure_class,
            "stage": self.stage,
            "detail": self.detail,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True)
class FailureHistory:
    """All retained non-success attempts for one source and its current outcome."""

    source_id: str
    current_status: str
    selected_candidate_id: str | None
    attempts: tuple[AttemptEvidence, ...]

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize the complete source-level attempt history."""
        return {
            "source_id": self.source_id,
            "current_status": self.current_status,
            "selected_candidate_id": self.selected_candidate_id,
            "attempts": [attempt.to_record() for attempt in self.attempts],
        }


@dataclass(frozen=True)
class ParserAttempt:
    """One human-readable retained table-parser attempt."""

    parser: str
    status: str
    details: Mapping[str, JsonValue] = field(default_factory=dict)

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize parser name, status, and parser-specific measurements."""
        return {"parser": self.parser, "status": self.status, **self.details}


@dataclass(frozen=True)
class ParserPageEvidence:
    """Parser attempts and retained outputs for one physical page."""

    physical_page: int
    route: str | None
    detected_table_count: int | None
    producer_table_count: int | None
    selected_parser_counts: tuple[tuple[str, int], ...]
    attempts: tuple[ParserAttempt, ...]

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize one page of parser evidence."""
        return {
            "physical_page": self.physical_page,
            "route": self.route,
            "detected_table_count": self.detected_table_count,
            "producer_table_count": self.producer_table_count,
            "selected_parser_counts": dict(self.selected_parser_counts),
            "attempts": [attempt.to_record() for attempt in self.attempts],
        }


@dataclass(frozen=True)
class TableParserEvidence:
    """Parser evidence attached to one warning or sampled table family."""

    pages: tuple[ParserPageEvidence, ...]
    scope: str
    page_details_open: bool = True

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize the bounded parser-evidence group."""
        return {
            "pages": [page.to_record() for page in self.pages],
            "scope": self.scope,
            "page_details_open": self.page_details_open,
        }


@dataclass(frozen=True)
class WarningEvidence:
    """Selected warning-class evidence stored in the durable selection record."""

    warning_class: WarningClass
    page_anchor_kind: str
    table_parser_evidence: TableParserEvidence | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize the warning class without disposable page render evidence."""
        warning = self.warning_class
        return {
            "owners": list(warning.owners),
            "codes": list(warning.codes),
            "fingerprint": warning.fingerprint,
            "occurrence_count": warning.occurrence_count,
            "raw_occurrence_count": warning.raw_occurrence_count,
            "source_counts": dict(warning.source_counts),
            "owner_code_counts": [
                {"owner": owner, "code": code, "count": count}
                for owner, code, count in warning.owner_code_counts
            ],
            "representative_message": warning.representative.message,
            "page_anchor_kind": self.page_anchor_kind,
            "table_parser_evidence": (
                self.table_parser_evidence.to_record()
                if self.table_parser_evidence is not None
                else None
            ),
        }


@dataclass(frozen=True)
class ReviewItem:
    """One durable selection anchor and its queue-specific evidence summary."""

    queue: ReviewQueue
    review_item_id: str
    source_id: str | None
    candidate_id: str | None
    physical_pages: tuple[int, ...]
    reasons: tuple[str, ...]
    population: Mapping[str, JsonValue]
    failure: FailureHistory | None = None
    warning: WarningEvidence | None = None
    table_family_id: str | None = None
    table_parser_evidence: TableParserEvidence | None = None

    def __post_init__(self) -> None:
        payloads = {
            ReviewQueue.FAILURE: self.failure is not None,
            ReviewQueue.WARNING: self.warning is not None,
            ReviewQueue.VALID_PAGE: all(
                value is None for value in (self.failure, self.warning, self.table_family_id)
            ),
            ReviewQueue.TABLE: self.table_family_id is not None,
        }
        if not payloads[self.queue]:
            raise ValueError(f"{self.queue.value} review item lacks its required evidence")
        if not self.review_item_id or not self.reasons:
            raise ValueError("review items require an identity and selection reason")
        if self.physical_pages != tuple(sorted(set(self.physical_pages))):
            raise ValueError("review item pages must be sorted and unique")

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize only durable selection evidence, never rendered UI payloads."""
        record: dict[str, JsonValue] = {
            "queue": self.queue.value,
            "review_item_id": self.review_item_id,
            "source_id": self.source_id,
            "candidate_id": self.candidate_id,
            "physical_pages": list(self.physical_pages),
            "reasons": list(self.reasons),
            "population": dict(self.population),
        }
        if self.failure is not None:
            record["failure"] = self.failure.to_record()
        if self.warning is not None:
            record["warning"] = self.warning.to_record()
        if self.table_family_id is not None:
            record["table_family_id"] = self.table_family_id
        if self.table_parser_evidence is not None:
            record["table_parser_evidence"] = self.table_parser_evidence.to_record()
        return record


@dataclass(frozen=True)
class BlockEvidence:
    """One canonical text block prepared for visual comparison."""

    identifier: str
    block_type: str
    text: str
    bbox: tuple[float, float, float, float] | None
    sequence: int | None
    overlaps_table: bool = False


@dataclass(frozen=True)
class TableEvidence:
    """One canonical table prepared for visual comparison."""

    identifier: str
    table_family_id: str | None
    parser: str | None
    shape: tuple[int, ...]
    cells: tuple[Mapping[str, JsonValue], ...]
    bbox: tuple[float, float, float, float] | None
    sequence: int | None


@dataclass(frozen=True)
class PageEvidence:
    """Canonical content and geometry for one disposable rendered page."""

    physical_page: int
    width: float
    height: float
    printed_page_label: str | None
    blocks: tuple[BlockEvidence, ...]
    tables: tuple[TableEvidence, ...]
    geometry_note: str | None = None


@dataclass(frozen=True)
class RenderedPage:
    """Disposable render path and page evidence used only by presentation."""

    physical_page: int
    relative_path: str
    evidence: PageEvidence


@dataclass(frozen=True)
class RenderOutput:
    """One disposable PDF page render before canonical evidence is attached."""

    physical_page: int
    path: Path


@dataclass(frozen=True)
class ReviewCard:
    """Presentation-only combination of a durable selection and disposable renders."""

    item: ReviewItem
    rendered_pages: tuple[RenderedPage, ...]


type ReviewItems = tuple[ReviewItem, ...]


__all__ = [
    "AttemptEvidence",
    "BlockEvidence",
    "BuildIdentity",
    "BuildRequest",
    "FailureHistory",
    "IdentityDependency",
    "InputScopePolicy",
    "PageEvidence",
    "PageProfile",
    "ParserAttempt",
    "ParserPageEvidence",
    "RenderOutput",
    "RenderedPage",
    "ReviewCard",
    "ReviewItem",
    "ReviewItems",
    "ReviewQueue",
    "SourceEvidence",
    "TableEvidence",
    "TableFamilyCandidate",
    "TableParserEvidence",
    "WarningClass",
    "WarningEvidence",
    "WarningInstance",
]
