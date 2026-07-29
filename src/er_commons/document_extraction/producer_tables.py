"""Run and validate the complete clean table stage."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import read_jsonl
from er_commons.document_extraction.config import PageRange
from er_commons.document_extraction.producer_config import ProducerConfig
from er_commons.document_extraction.producer_records import (
    PageRouteRecord,
    TableStageObservation,
)
from er_commons.document_extraction.producer_services import TableRunner
from er_commons.document_extraction.sources import (
    CompleteResolvedSource,
    ResolvedSource,
)
from er_commons.document_extraction.table_stage import build_complete_table_request
from er_commons.source_freeze import write_json_atomic


class TableStageInvariantError(ValueError):
    """A named clean-table invariant failed."""

    def __init__(self, invariant: str, detail: str) -> None:
        super().__init__(f"table-stage invariant failed [{invariant}]: {detail}")
        self.invariant = invariant


def _require(invariant: str, condition: bool, detail: str) -> None:
    if not condition:
        raise TableStageInvariantError(invariant, detail)


def validate_table_artifacts(
    table_root: Path,
    expected_pages: list[int],
) -> TableStageObservation:
    """Validate page, table, assignment, family, and summary reconciliation."""
    summary = json.loads((table_root / "summary.json").read_text())
    pages = read_jsonl(table_root / "pages.jsonl")
    tables = read_jsonl(table_root / "tables.jsonl")
    assignments = read_jsonl(table_root / "family_assignments.jsonl")
    families = json.loads((table_root / "table_families.json").read_text())["families"]

    actual_pages = [int(record["physical_pdf_page"]) for record in pages]
    table_ids = [str(record["table_id"]) for record in tables]
    assignment_table_ids = [str(record["table_id"]) for record in assignments]
    family_ids = [str(record["family_id"]) for record in families]
    assignment_family_ids = [str(record["family_id"]) for record in assignments]
    family_table_ids = [str(table_id) for family in families for table_id in family["table_ids"]]
    family_pairs = {
        (str(table_id), str(family["family_id"]))
        for family in families
        for table_id in family["table_ids"]
    }
    assignment_pairs = {
        (str(record["table_id"]), str(record["family_id"])) for record in assignments
    }
    zero_table_pages = [
        int(record["physical_pdf_page"]) for record in pages if int(record["table_count"]) == 0
    ]
    tables_per_page = {
        page: sum(int(table["physical_pdf_page"]) == page for table in tables)
        for page in actual_pages
    }

    _require("page_records", actual_pages == expected_pages, "routed pages differ")
    _require(
        "summary_pages",
        [int(value) for value in summary["physical_pdf_pages"]] == expected_pages,
        "summary physical pages differ",
    )
    _require(
        "summary_page_count",
        int(summary["page_count"]) == len(expected_pages),
        "summary page count differs",
    )
    for page in pages:
        page_number = int(page["physical_pdf_page"])
        _require(
            f"page_{page_number}_table_count",
            int(page["table_count"]) == tables_per_page[page_number],
            "page record differs from tables.jsonl",
        )
    _require("unique_table_ids", len(table_ids) == len(set(table_ids)), "duplicate table ID")
    _require(
        "unique_assignment_table_ids",
        len(assignment_table_ids) == len(set(assignment_table_ids)),
        "duplicate table assignment",
    )
    _require(
        "assignments_cover_tables",
        set(assignment_table_ids) == set(table_ids),
        "table assignments do not exactly cover tables",
    )
    _require("unique_family_ids", len(family_ids) == len(set(family_ids)), "duplicate family ID")
    _require(
        "assignments_cover_families",
        set(assignment_family_ids) == set(family_ids),
        "family assignments do not exactly cover families",
    )
    _require(
        "unique_family_members",
        len(family_table_ids) == len(set(family_table_ids)),
        "one table appears in more than one family",
    )
    _require(
        "families_cover_tables",
        set(family_table_ids) == set(table_ids),
        "family members do not exactly cover tables",
    )
    _require(
        "assignment_pairs",
        family_pairs == assignment_pairs,
        "table-to-family pairs differ between artifacts",
    )
    _require(
        "summary_table_count",
        int(summary["logical_table_count"]) == len(tables),
        "summary logical table count differs",
    )
    _require(
        "summary_family_count",
        int(summary["family_count"]) == len(families),
        "summary family count differs",
    )
    _require(
        "zero_table_pages",
        [int(value) for value in summary["zero_table_pages"]] == zero_table_pages,
        "summary zero-table mapping differs",
    )
    _require(
        "no_review_derivatives",
        not bool(summary["review_derivatives_retained"]),
        "producer table stage retained disposable review images",
    )

    return TableStageObservation(
        status="complete_with_warnings" if zero_table_pages else "complete",
        document_scope_complete=True,
        routed_pages=expected_pages,
        routed_page_count=len(expected_pages),
        logical_table_count=len(tables),
        family_assignment_count=len(assignments),
        family_count=len(families),
        zero_table_pages=zero_table_pages,
        manifest=(f"documents/{table_root.parents[1].name}/producer/tables/manifest.json"),
    )


def _table_source(source: CompleteResolvedSource) -> ResolvedSource:
    """Adapt a complete source to the existing table-request contract."""
    return ResolvedSource(
        source_id=source.source_id,
        source_path=source.source_path,
        source_sha256=source.source_sha256,
        source_page_count=source.source_page_count,
        warnings=source.warnings,
        page_ranges=[
            PageRange(
                first_page=1,
                last_page=source.source_page_count,
                expected_printed_labels=[],
                stressors=["complete_document"],
            )
        ],
    )


def _positive_routes(records: Sequence[PageRouteRecord]) -> list[PageRouteRecord]:
    return [record for record in records if record.route != "no_table_route"]


def run_complete_table_stage(
    *,
    data_root: Path,
    staging_root: Path,
    config: ProducerConfig,
    source: CompleteResolvedSource,
    routes: Sequence[PageRouteRecord],
    table_runner: TableRunner,
    producer_run_id: str,
) -> TableStageObservation:
    """Run the public table pipeline or record that no pages required it."""
    positive = _positive_routes(routes)
    table_root = staging_root / "documents" / source.source_id / "producer" / "tables"
    if not positive:
        result = TableStageObservation(
            status="not_applicable",
            document_scope_complete=True,
            verified_no_table_routes=True,
            routed_pages=[],
            routed_page_count=0,
            logical_table_count=0,
            family_assignment_count=0,
            family_count=0,
            zero_table_pages=[],
            manifest=None,
        )
        write_json_atomic(
            table_root / "no_table_stage.json",
            result.model_dump(mode="json", exclude_none=True),
        )
        return result

    route_payloads: list[dict[str, Any]] = [record.model_dump(mode="json") for record in positive]
    request = build_complete_table_request(
        pipeline_id=config.pipeline_id,
        source_release_version=config.source_release_version,
        source=_table_source(source),
        route_records=route_payloads,
        artifact_relative_root=(
            config.artifact_relative_root
            / producer_run_id
            / "documents"
            / source.source_id
            / "producer"
            / "tables"
        ),
        detection=config.table_detection,
        cleanup=config.table_cleanup,
        retain_review_derivatives=False,
    )
    request_path = staging_root / "records" / "table_request.json"
    write_json_atomic(request_path, request.model_dump(mode="json"))
    manifest_path = table_runner(data_root, request_path, table_root)
    expected_manifest = table_root / "manifest.json"
    if manifest_path != expected_manifest:
        raise TableStageInvariantError(
            "manifest_location",
            "table runner published outside the producer staging root",
        )
    return validate_table_artifacts(
        table_root,
        [record.physical_pdf_page for record in positive],
    )
