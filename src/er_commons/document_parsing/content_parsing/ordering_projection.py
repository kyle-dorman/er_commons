"""Policy for reducing aggregate ordering input after table extraction."""

from __future__ import annotations

from copy import deepcopy
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectionRecord(BaseModel):
    """Strict persisted contract for pre-aggregate ordering records."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _page_number(page: dict[str, Any]) -> int:
    """Validate and return the physical page number in one projection page."""
    value = page.get("page_no")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("ordering projection pages require positive integer page_no values")
    return value


def _validate_page_coverage(
    pages: tuple[dict[str, Any], ...], decisions: tuple[TableEvidenceDecision, ...]
) -> None:
    """Require one ordered, unique decision for each projection page."""
    page_numbers = [_page_number(page) for page in pages]
    if len(set(page_numbers)) != len(page_numbers):
        raise ValueError("ordering projection pages must have unique page_no values")
    decision_numbers = [decision.physical_pdf_page for decision in decisions]
    if page_numbers != sorted(page_numbers):
        raise ValueError("ordering projection pages must be ordered")
    if page_numbers != decision_numbers:
        raise ValueError("ordering projection pages and decisions must have exact coverage")


def _validate_page_records(pages: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """Validate the suppression field that the aggregate worker consumes."""
    for page in pages:
        _page_number(page)
        refs = page.get("ordering_suppressed_table_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
            raise ValueError(
                "ordering projection pages require a list of non-empty table references"
            )
        if len(set(refs)) != len(refs):
            raise ValueError("ordering projection pages must have unique table references")
    return pages


class TableEvidenceOutcome(StrEnum):
    """Page-local extraction outcomes used by the suppression policy."""

    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    FAILED = "failed"
    ROUTE_ONLY = "route_only"
    UNMATCHED = "unmatched"


class TableEvidenceDecision(ProjectionRecord):
    """One explicit page-local disposition for ordering projection."""

    physical_pdf_page: int = Field(gt=0)
    outcome: TableEvidenceOutcome
    confirmed_table_refs: tuple[str, ...] = ()
    reason: str = ""

    @model_validator(mode="after")
    def validate_refs(self) -> TableEvidenceDecision:
        """Reject duplicate or empty confirmed table references."""
        if any(not ref for ref in self.confirmed_table_refs):
            raise ValueError("confirmed table references must be non-empty")
        if len(set(self.confirmed_table_refs)) != len(self.confirmed_table_refs):
            raise ValueError("confirmed table references must be unique")
        return self

    @property
    def may_suppress_table_text(self) -> bool:
        """Only complete confirmed extraction can authorize suppression."""
        return self.outcome is TableEvidenceOutcome.CONFIRMED and bool(self.confirmed_table_refs)

    def as_record(self) -> dict[str, Any]:
        """Return the stable JSON representation used by the aggregate worker."""
        return self.model_dump(mode="json")


class OrderingProjection(ProjectionRecord):
    """Reduced ordering input plus immutable provenance for every page."""

    pages: tuple[dict[str, Any], ...]
    decisions: tuple[TableEvidenceDecision, ...]

    _validate_pages = field_validator("pages")(_validate_page_records)

    @model_validator(mode="after")
    def validate_page_coverage(self) -> OrderingProjection:
        """Require one ordered decision for each ordered projection page."""
        _validate_page_coverage(self.pages, self.decisions)
        return self


class OrderingProjectionArtifact(ProjectionRecord):
    """Complete persisted envelope consumed by the aggregate worker."""

    schema_version: Literal["er_commons.ordering_projection.v1"] = (
        "er_commons.ordering_projection.v1"
    )
    table_stage_observation: dict[str, Any]
    table_stage_root: str = Field(min_length=1)
    pages: tuple[dict[str, Any], ...]
    decisions: tuple[TableEvidenceDecision, ...]

    _validate_pages = field_validator("pages")(_validate_page_records)

    @field_validator("table_stage_root")
    @classmethod
    def validate_table_stage_root(cls, value: str) -> str:
        """Keep the copied table-stage provenance unambiguous across workers."""
        if not Path(value).is_absolute():
            raise ValueError("table stage root must be an absolute path")
        return value

    @model_validator(mode="after")
    def validate_page_coverage(self) -> OrderingProjectionArtifact:
        """Require one ordered decision for each ordered projection page."""
        _validate_page_coverage(self.pages, self.decisions)
        return self


def classify_table_evidence(
    *,
    physical_pdf_page: int,
    route: str,
    page_record: dict[str, Any] | None,
    table_records: list[dict[str, Any]],
) -> TableEvidenceDecision:
    """Classify one page without treating a route as extraction success."""
    if physical_pdf_page < 1:
        raise ValueError("table evidence requires a positive physical page")
    if page_record is None:
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.UNMATCHED,
            reason="no table-stage page record",
        )
    status = str(page_record.get("status", ""))
    refs = tuple(
        str(item["table_id"])
        for item in table_records
        if isinstance(item, dict) and item.get("table_id")
    )
    if status == "complete" and refs:
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.CONFIRMED,
            confirmed_table_refs=refs,
            reason="complete table records",
        )
    if status in {"partial", "complete_with_warnings"}:
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.PARTIAL,
            confirmed_table_refs=refs,
            reason="non-terminal or warning table record",
        )
    if status in {"failed", "error"}:
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.FAILED,
            confirmed_table_refs=refs,
            reason="table extraction failed",
        )
    if route != "no_table_route":
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.ROUTE_ONLY,
            confirmed_table_refs=refs,
            reason="route is not extraction evidence",
        )
    return TableEvidenceDecision(
        physical_pdf_page=physical_pdf_page,
        outcome=TableEvidenceOutcome.UNMATCHED,
        confirmed_table_refs=refs,
        reason="no matching extraction outcome",
    )


def build_ordering_projection(
    pages: list[dict[str, Any]],
    decisions: list[TableEvidenceDecision],
) -> OrderingProjection:
    """Suppress only confirmed table elements while preserving all other pages."""
    page_numbers = [_page_number(page) for page in pages]
    decision_numbers = [decision.physical_pdf_page for decision in decisions]
    if page_numbers != sorted(page_numbers):
        raise ValueError("ordering projection pages must be ordered")
    if page_numbers != decision_numbers:
        raise ValueError("ordering projection pages and decisions must have exact coverage")
    by_page = dict(zip(decision_numbers, decisions, strict=True))
    projected: list[dict[str, Any]] = []
    for page in pages:
        page_number = int(page["page_no"])
        decision = by_page.get(page_number)
        if decision is None:
            raise ValueError(f"missing table evidence decision for page {page_number}")
        copy = deepcopy(page)
        if decision.may_suppress_table_text:
            copy["ordering_suppressed_table_refs"] = list(decision.confirmed_table_refs)
        else:
            copy["ordering_suppressed_table_refs"] = []
        projected.append(copy)
    return OrderingProjection(pages=tuple(projected), decisions=tuple(decisions))


__all__ = [
    "OrderingProjection",
    "OrderingProjectionArtifact",
    "TableEvidenceDecision",
    "TableEvidenceOutcome",
    "build_ordering_projection",
    "classify_table_evidence",
]
