"""Application shell for the diagnostic-only Task 03G.1 smoke."""

from __future__ import annotations

from pathlib import Path

from er_commons.smoke_extraction.config import SmokeSource
from er_commons.smoke_extraction.publication import (
    PreparedSmoke,
    allocate_attempt,
    inventory_attempt,
    prepare_smoke,
    publish_summary,
)
from er_commons.smoke_extraction.records import PageOutcome, SourceSummary
from er_commons.smoke_extraction.reporting import (
    build_run_summary,
    build_source_summary,
    validate_terminal_run,
    write_jsonl,
)
from er_commons.smoke_extraction.services import SmokeServices
from er_commons.smoke_extraction.source_processing import failed_page, process_source
from er_commons.source_freeze import write_json_atomic


def _resource_stop_outcomes(selected: SmokeSource) -> list[PageOutcome]:
    return [
        failed_page(
            selected.source_id,
            page,
            "not_run_resource_stop",
            "minimum free-disk stop condition reached",
        )
        for page in selected.selected_physical_pages
    ]


def _source_verification_outcomes(
    selected: SmokeSource,
    error: Exception,
) -> list[PageOutcome]:
    message = f"{type(error).__name__}: {error}"
    return [
        failed_page(selected.source_id, page, "source_verification_failed", message)
        for page in selected.selected_physical_pages
    ]


def _run_selected_source(
    data_root: Path,
    prepared: PreparedSmoke,
    selected: SmokeSource,
    source_root: Path,
    services: SmokeServices,
    resource_stopped: bool,
) -> tuple[list[PageOutcome], bool]:
    free_bytes = services.disk_usage(data_root).free
    below_minimum = free_bytes < prepared.spec.resource_policy.minimum_free_bytes_before_source
    if resource_stopped or below_minimum:
        return _resource_stop_outcomes(selected), True
    try:
        source = services.resolve_source(data_root, prepared.spec, selected.source_id)
    except Exception as error:  # source-local verification failure does not stop the scope
        return _source_verification_outcomes(selected, error), False
    return (
        process_source(
            data_root,
            prepared.run_id,
            source,
            selected.selected_physical_pages,
            source_root,
            prepared.converter,
            prepared.spec,
            services,
        ),
        False,
    )


def run_smoke(
    data_root: Path,
    spec_path: Path,
    *,
    services: SmokeServices | None = None,
) -> Path:
    """Run one fresh diagnostic smoke; never publish complete-document artifacts."""
    active_services = services or SmokeServices()
    started = active_services.monotonic()
    prepared = prepare_smoke(data_root, spec_path, active_services)
    attempt_id, attempt_root = allocate_attempt(prepared, active_services)

    all_outcomes: list[PageOutcome] = []
    source_summaries: list[SourceSummary] = []
    resource_stopped = False
    for selected in prepared.spec.sources:
        source_started = active_services.monotonic()
        source_root = attempt_root / "sources" / selected.source_id
        source_root.mkdir(parents=True)
        outcomes, source_stopped = _run_selected_source(
            data_root,
            prepared,
            selected,
            source_root,
            active_services,
            resource_stopped,
        )
        resource_stopped = resource_stopped or source_stopped
        write_jsonl(source_root / "page_outcomes.jsonl", outcomes)
        source_summary = build_source_summary(
            selected.source_id,
            outcomes,
            source_root,
            active_services.monotonic() - source_started,
        )
        write_json_atomic(source_root / "summary.json", source_summary)
        all_outcomes.extend(outcomes)
        source_summaries.append(source_summary)

    validate_terminal_run(
        all_outcomes, prepared.spec.expected_selected_page_count, prepared.smoke_root
    )
    inventory = inventory_attempt(attempt_root)
    summary = build_run_summary(
        run_id=prepared.run_id,
        attempt_id=attempt_id,
        outcomes=all_outcomes,
        source_summaries=source_summaries,
        source_count=len(prepared.spec.sources),
        wall_seconds=active_services.monotonic() - started,
        inventory=inventory,
    )
    return publish_summary(prepared, attempt_root, summary)
