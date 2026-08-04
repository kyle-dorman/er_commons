"""Internal record shapes and terminal invariants for smoke diagnostics."""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class TableOutcome(TypedDict):
    """One routed page's retained clean-table result."""

    status: str
    table_count: int
    route: str
    result: str
    manifest: str


class PageOutcome(TypedDict):
    """Terminal diagnostic state for one requested physical page."""

    source_id: str
    physical_pdf_page: int
    status: str
    conversion: str
    routing: str
    table_stage: str
    warnings: list[str]
    errors: list[Any]
    conversion_range: NotRequired[str]
    route: NotRequired[str]
    tables: NotRequired[TableOutcome]


RouteRecord = dict[str, Any]
SourceSummary = dict[str, Any]

TERMINAL_PAGE_STATUSES = frozenset(
    {
        "complete",
        "complete_with_warnings",
        "conversion_failed",
        "routing_failed",
        "table_failed",
        "source_verification_failed",
        "not_run_resource_stop",
    }
)

FORBIDDEN_PUBLICATION_NAMES = frozenset(
    {
        "completion_record.json",
        "accounting_completion.json",
        "target_index_completion.json",
        "resolution_completion.json",
        "handoff.json",
    }
)
