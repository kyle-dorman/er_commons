"""Policy for reducing aggregate ordering input after table extraction."""

from __future__ import annotations

from typing import Any

from er_commons.document_parsing.content_parsing.ordering_projection_records import (
    ConfirmedTableRegion,
    OrderingProjection,
    OrderingProjectionArtifact,
    OrderingProjectionPage,
    OrderingTableStageObservation,
    RoutingFeatures,
    TableEvidenceDecision,
    TableEvidenceOutcome,
)
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection
from er_commons.document_parsing.content_parsing.table_stage_reference import (
    TableArtifactSeal,
    TableStageReference,
    capture_table_stage_reference,
    verify_table_stage_reference,
)


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
    refs = tuple(
        str(item["table_id"])
        for item in table_records
        if isinstance(item, dict) and item.get("table_id")
    )
    regions = _confirmed_regions(route, table_records)
    declared_count = page_record.get("table_count")
    if (
        isinstance(declared_count, int)
        and not isinstance(declared_count, bool)
        and declared_count == len(table_records)
        and bool(refs)
        and len(regions) == len(refs)
    ):
        return TableEvidenceDecision(
            physical_pdf_page=physical_pdf_page,
            outcome=TableEvidenceOutcome.CONFIRMED,
            confirmed_table_refs=refs,
            confirmed_table_regions=regions,
            reason="validated page count, table records, and suppression geometry agree",
        )
    return _unconfirmed_decision(
        physical_pdf_page=physical_pdf_page,
        route=route,
        status=str(page_record.get("status", "")),
        has_table_records=bool(refs),
    )


def _confirmed_regions(
    route: str, table_records: list[dict[str, Any]]
) -> tuple[ConfirmedTableRegion, ...]:
    """Build complete region evidence or reject the entire page-local set."""
    try:
        return tuple(
            ConfirmedTableRegion(
                table_ref=str(item["table_id"]),
                bbox_pdf_points_bottom_left=tuple(item["bbox_pdf_points_bottom_left"]),
                page_size_pdf_points=tuple(item["page_size_pdf_points"]),
                suppression_scope=("page" if route == "full_page_numeric" else "region"),
            )
            for item in table_records
        )
    except (KeyError, TypeError, ValueError):
        return ()


def _unconfirmed_decision(
    *, physical_pdf_page: int, route: str, status: str, has_table_records: bool
) -> TableEvidenceDecision:
    """Return the explicit fallback disposition for unconfirmed evidence."""
    if has_table_records or status in {"partial", "complete_with_warnings"}:
        outcome = TableEvidenceOutcome.PARTIAL
        reason = "table records are incomplete or lack valid suppression geometry"
    elif status in {"failed", "error"}:
        outcome = TableEvidenceOutcome.FAILED
        reason = "table extraction failed"
    elif route != "no_table_route":
        outcome = TableEvidenceOutcome.ROUTE_ONLY
        reason = "route is not extraction evidence"
    else:
        outcome = TableEvidenceOutcome.UNMATCHED
        reason = "no matching extraction outcome"
    return TableEvidenceDecision(
        physical_pdf_page=physical_pdf_page,
        outcome=outcome,
        reason=reason,
    )


def build_ordering_projection(
    pages: list[PageEvidenceProjection],
    decisions: list[TableEvidenceDecision],
) -> OrderingProjection:
    """Suppress only confirmed table elements while preserving all other pages."""
    page_numbers = [page.physical_pdf_page for page in pages]
    decision_numbers = [decision.physical_pdf_page for decision in decisions]
    if page_numbers != sorted(page_numbers):
        raise ValueError("ordering projection pages must be ordered")
    if page_numbers != decision_numbers:
        raise ValueError("ordering projection pages and decisions must have exact coverage")
    projected = [
        _project_page(page, decision) for page, decision in zip(pages, decisions, strict=True)
    ]
    return OrderingProjection(pages=tuple(projected), decisions=tuple(decisions))


def _project_page(
    page: PageEvidenceProjection, decision: TableEvidenceDecision
) -> OrderingProjectionPage:
    """Attach confirmed suppression evidence to one typed page projection."""
    refs = decision.confirmed_table_refs if decision.may_suppress_table_text else ()
    regions = decision.confirmed_table_regions if decision.may_suppress_table_text else ()
    return OrderingProjectionPage(
        page_no=page.physical_pdf_page,
        **page.model_dump(mode="python"),
        ordering_suppressed_table_refs=refs,
        ordering_suppressed_table_regions=regions,
    )


__all__ = [
    "ConfirmedTableRegion",
    "OrderingProjection",
    "OrderingProjectionArtifact",
    "OrderingProjectionPage",
    "OrderingTableStageObservation",
    "RoutingFeatures",
    "TableArtifactSeal",
    "TableEvidenceDecision",
    "TableEvidenceOutcome",
    "TableStageReference",
    "build_ordering_projection",
    "capture_table_stage_reference",
    "classify_table_evidence",
    "verify_table_stage_reference",
]
