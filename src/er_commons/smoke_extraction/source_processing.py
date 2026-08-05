"""Bounded conversion, routing, and table-state transitions for one source."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.smoke_extraction.config import SmokeSpec
from er_commons.smoke_extraction.conversion import RangeDiagnostic
from er_commons.smoke_extraction.records import PageOutcome, RouteRecord, TableOutcome
from er_commons.smoke_extraction.routing import route_page
from er_commons.smoke_extraction.services import SmokeServices
from er_commons.smoke_extraction.warnings import retain_source_warnings


def contiguous_ranges(pages: list[int]) -> list[tuple[int, int]]:
    """Collapse sorted selected pages into the minimum contiguous calls."""
    if not pages:
        return []
    ranges: list[tuple[int, int]] = []
    start = previous = pages[0]
    for page in pages[1:]:
        if page != previous + 1:
            ranges.append((start, previous))
            start = page
        previous = page
    ranges.append((start, previous))
    return ranges


def failed_page(source_id: str, page: int, status: str, message: str) -> PageOutcome:
    """Build one explicit terminal failure without complete-document semantics."""
    conversion = "conversion_failed" if status == "conversion_failed" else "not_run"
    if status in {"routing_failed", "table_failed"}:
        conversion = "complete"
    return {
        "source_id": source_id,
        "physical_pdf_page": page,
        "status": status,
        "conversion": conversion,
        "routing": status if status == "routing_failed" else "not_run",
        "table_stage": status if status == "table_failed" else "not_run",
        "warnings": [],
        "errors": [message],
    }


def _exception_message(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"


def _record_conversion_failure(
    outcomes: dict[int, PageOutcome],
    source_id: str,
    first_page: int,
    last_page: int,
    message: str,
) -> None:
    for page in range(first_page, last_page + 1):
        outcomes[page] = failed_page(source_id, page, "conversion_failed", message)


def _record_converted_range(
    outcomes: dict[int, PageOutcome],
    routes: list[RouteRecord],
    source: CompleteResolvedSource,
    diagnostic: RangeDiagnostic,
    first_page: int,
    last_page: int,
    range_root: Path,
    source_root: Path,
    spec: SmokeSpec,
    services: SmokeServices,
) -> None:
    """Validate exact range coverage, then route every successfully converted page."""
    expected = set(range(first_page, last_page + 1))
    converted = set(diagnostic.converted_pages)
    extra = converted - expected
    if extra:
        _record_conversion_failure(
            outcomes,
            source.source_id,
            first_page,
            last_page,
            f"Docling returned pages outside requested range: {sorted(extra)}",
        )
        return
    for page in sorted(expected - converted):
        outcomes[page] = failed_page(
            source.source_id, page, "conversion_failed", "Docling omitted requested page"
        )
    for page in sorted(expected & converted):
        if diagnostic.status not in {"complete", "complete_with_warnings"}:
            outcomes[page] = failed_page(
                source.source_id,
                page,
                "conversion_failed",
                f"Docling status: {diagnostic.raw_status}",
            )
            continue
        try:
            route = route_page(source, diagnostic.document_payload, page, spec, services.route)
        except Exception as error:  # diagnostic boundary retains ordinary context
            outcomes[page] = failed_page(
                source.source_id, page, "routing_failed", _exception_message(error)
            )
            continue
        routes.append(route)
        outcomes[page] = {
            "source_id": source.source_id,
            "physical_pdf_page": page,
            "status": "complete",
            "conversion": "complete",
            "conversion_range": range_root.relative_to(source_root).as_posix(),
            "routing": "complete",
            "route": route["route"],
            "table_stage": ("not_applicable" if route["route"] == "no_table_route" else "pending"),
            "warnings": [],
            "errors": [],
        }


def _attach_table_results(
    data_root: Path,
    run_id: str,
    source: CompleteResolvedSource,
    source_root: Path,
    spec: SmokeSpec,
    services: SmokeServices,
    routes: list[RouteRecord],
    outcomes: dict[int, PageOutcome],
) -> None:
    positive = [route for route in routes if route["route"] != "no_table_route"]
    if not positive:
        return
    try:
        table_outcomes = services.run_tables(data_root, run_id, source, positive, source_root, spec)
        expected_pages = {int(route["physical_pdf_page"]) for route in positive}
        unexpected = set(table_outcomes) - expected_pages
        if unexpected:
            raise ValueError(f"table stage returned unrequested pages: {sorted(unexpected)}")
        for page in sorted(expected_pages):
            table_outcome = table_outcomes.get(page)
            if table_outcome is None:
                outcomes[page]["status"] = "table_failed"
                outcomes[page]["table_stage"] = "table_failed"
                outcomes[page]["errors"].append("table stage omitted routed page")
                continue
            outcomes[page]["table_stage"] = table_outcome["status"]
            outcomes[page]["tables"] = cast(TableOutcome, table_outcome)
    except Exception as error:  # source-local table failure remains page-explicit
        message = _exception_message(error)
        for route in positive:
            page = int(route["physical_pdf_page"])
            outcomes[page]["status"] = "table_failed"
            outcomes[page]["table_stage"] = "table_failed"
            outcomes[page]["errors"].append(message)


def process_source(
    data_root: Path,
    run_id: str,
    source: CompleteResolvedSource,
    pages: list[int],
    source_root: Path,
    converter: Any,
    spec: SmokeSpec,
    services: SmokeServices,
) -> list[PageOutcome]:
    """Process one source while retaining one terminal outcome per requested page."""
    outcomes: dict[int, PageOutcome] = {}
    routes: list[RouteRecord] = []
    producer_services = ProducerServices()
    retain_source_warnings(source_root, source.source_id, source.warnings)
    for first_page, last_page in contiguous_ranges(pages):
        range_root = source_root / "conversion" / f"pages_{first_page:05d}_{last_page:05d}"
        try:
            diagnostic = services.convert(
                converter,
                source,
                first_page,
                last_page,
                range_root,
                producer_services,
            )
        except Exception as error:  # conversion failure belongs to this requested range
            _record_conversion_failure(
                outcomes,
                source.source_id,
                first_page,
                last_page,
                _exception_message(error),
            )
            continue
        _record_converted_range(
            outcomes,
            routes,
            source,
            diagnostic,
            first_page,
            last_page,
            range_root,
            source_root,
            spec,
            services,
        )
    _attach_table_results(data_root, run_id, source, source_root, spec, services, routes, outcomes)
    return [outcomes[page] for page in pages]
