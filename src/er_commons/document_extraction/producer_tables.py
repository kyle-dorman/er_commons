"""Run and validate the complete clean table stage."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
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


@dataclass(frozen=True)
class PersistedTableStage:
    """The six persisted views reconciled by complete-table validation."""

    summary: dict[str, Any]
    pages: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    assignments: list[dict[str, Any]]
    families: list[dict[str, Any]]
    continuation_decisions: list[dict[str, Any]]

    @classmethod
    def load(cls, table_root: Path) -> PersistedTableStage:
        """Load table artifacts once before applying cross-file invariants."""
        family_payload = json.loads((table_root / "table_families.json").read_text())
        return cls(
            summary=json.loads((table_root / "summary.json").read_text()),
            pages=read_jsonl(table_root / "pages.jsonl"),
            tables=read_jsonl(table_root / "tables.jsonl"),
            assignments=read_jsonl(table_root / "family_assignments.jsonl"),
            families=family_payload["families"],
            continuation_decisions=family_payload.get("continuation_decisions", []),
        )


def _validate_page_accounting(
    stage: PersistedTableStage,
    expected_pages: list[int],
) -> list[int]:
    """Reconcile routed pages, page table counts, and zero-table pages."""
    actual_pages = [int(record["physical_pdf_page"]) for record in stage.pages]
    _require("page_records", actual_pages == expected_pages, "routed pages differ")
    _require(
        "summary_pages",
        [int(value) for value in stage.summary["physical_pdf_pages"]] == expected_pages,
        "summary physical pages differ",
    )
    _require(
        "summary_page_count",
        int(stage.summary["page_count"]) == len(expected_pages),
        "summary page count differs",
    )
    tables_per_page = {
        page: sum(int(table["physical_pdf_page"]) == page for table in stage.tables)
        for page in actual_pages
    }
    for page_record in stage.pages:
        page = int(page_record["physical_pdf_page"])
        _require(
            f"page_{page}_table_count",
            int(page_record["table_count"]) == tables_per_page[page],
            "page record differs from tables.jsonl",
        )
    return [
        int(record["physical_pdf_page"])
        for record in stage.pages
        if int(record["table_count"]) == 0
    ]


@dataclass(frozen=True)
class FamilyIndexes:
    """Cross-file table/family indexes used by continuation validation."""

    family_by_table: dict[str, str]
    continuation_family_ids: set[str]


def _validate_family_accounting(stage: PersistedTableStage) -> FamilyIndexes:
    """Require tables, assignments, and family definitions to agree exactly."""
    table_ids = [str(record["table_id"]) for record in stage.tables]
    assignment_table_ids = [str(record["table_id"]) for record in stage.assignments]
    family_ids = [str(record["family_id"]) for record in stage.families]
    assignment_family_ids = [str(record["family_id"]) for record in stage.assignments]
    family_table_ids = [
        str(table_id) for family in stage.families for table_id in family["table_ids"]
    ]
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
    family_pairs = {
        (str(table_id), str(family["family_id"]))
        for family in stage.families
        for table_id in family["table_ids"]
    }
    assignment_pairs = {
        (str(record["table_id"]), str(record["family_id"])) for record in stage.assignments
    }
    _require(
        "assignment_pairs",
        family_pairs == assignment_pairs,
        "table-to-family pairs differ between artifacts",
    )
    return FamilyIndexes(
        family_by_table={table_id: family_id for table_id, family_id in assignment_pairs},
        continuation_family_ids={
            str(family["family_id"])
            for family in stage.families
            if "cross_page_continuation" in family.get("evidence", [])
        },
    )


def _validate_inherited_header(decision: dict[str, Any], left_table: str) -> None:
    """Require accepted continuation evidence to remain an unresolved pointer."""
    inherited = decision.get("inherited_header")
    _require(
        "continuation_inherited_header",
        isinstance(inherited, dict)
        and inherited.get("origin") == "inherited"
        and inherited.get("content_status") == "unresolved_no_printed_header_projection"
        and inherited.get("source_table_id") == left_table
        and isinstance(inherited.get("source_leading_rows_heuristic_sha256"), str)
        and len(inherited["source_leading_rows_heuristic_sha256"]) == 64
        and isinstance(inherited.get("target_clean_to_source_column"), list)
        and isinstance(inherited.get("unrepresented_source_columns"), list),
        "accepted continuation lacks explicit inherited-header evidence",
    )


def _validate_continuations(stage: PersistedTableStage, indexes: FamilyIndexes) -> None:
    """Reconcile boundary dispositions with family unions and summary counts."""
    accepted_family_ids: set[str] = set()
    seen_boundaries: set[tuple[int, int]] = set()
    for decision in stage.continuation_decisions:
        status = str(decision["status"])
        boundary = (int(decision["left_page"]), int(decision["right_page"]))
        _require(
            "unique_continuation_boundary",
            boundary not in seen_boundaries,
            f"duplicate continuation boundary: {boundary}",
        )
        seen_boundaries.add(boundary)
        _require(
            "adjacent_continuation_boundary",
            boundary[1] == boundary[0] + 1,
            f"non-adjacent continuation boundary: {boundary}",
        )
        if status == "not_evaluable_missing_table":
            continue
        left_table = decision.get("left_table_id")
        right_table = decision.get("right_table_id")
        references_known_tables = (
            isinstance(left_table, str)
            and isinstance(right_table, str)
            and left_table in indexes.family_by_table
            and right_table in indexes.family_by_table
        )
        _require(
            "continuation_table_references",
            references_known_tables,
            "continuation decision references unknown tables",
        )
        assert isinstance(left_table, str) and isinstance(right_table, str)
        same_family = indexes.family_by_table[left_table] == indexes.family_by_table[right_table]
        _require(
            "continuation_family_disposition",
            same_family if status == "accepted" else not same_family,
            f"continuation {status} disposition differs from family assignment",
        )
        if status == "accepted":
            accepted_family_ids.add(indexes.family_by_table[left_table])
            _validate_inherited_header(decision, left_table)
    _require(
        "continuation_family_evidence",
        indexes.continuation_family_ids == accepted_family_ids,
        "cross-page family evidence does not exactly match accepted decisions",
    )
    if stage.continuation_decisions:
        statuses = ("accepted", "rejected", "ambiguous", "not_evaluable_missing_table")
        expected_counts = {
            status: sum(decision["status"] == status for decision in stage.continuation_decisions)
            for status in statuses
        }
        _require(
            "summary_continuation_counts",
            stage.summary.get("continuation_decision_counts") == expected_counts,
            "summary continuation counts differ",
        )


def _validate_summary(
    stage: PersistedTableStage,
    *,
    zero_table_pages: list[int],
) -> None:
    """Reconcile terminal aggregate counts and publication boundaries."""
    _require(
        "summary_table_count",
        int(stage.summary["logical_table_count"]) == len(stage.tables),
        "summary logical table count differs",
    )
    _require(
        "summary_family_count",
        int(stage.summary["family_count"]) == len(stage.families),
        "summary family count differs",
    )
    _require(
        "zero_table_pages",
        [int(value) for value in stage.summary["zero_table_pages"]] == zero_table_pages,
        "summary zero-table mapping differs",
    )
    _require(
        "no_review_derivatives",
        not bool(stage.summary["review_derivatives_retained"]),
        "producer table stage retained disposable review images",
    )


def validate_table_artifacts(
    table_root: Path,
    expected_pages: list[int],
) -> TableStageObservation:
    """Validate page, table, assignment, family, and summary reconciliation."""
    stage = PersistedTableStage.load(table_root)
    zero_table_pages = _validate_page_accounting(stage, expected_pages)
    family_indexes = _validate_family_accounting(stage)
    _validate_continuations(stage, family_indexes)
    _validate_summary(stage, zero_table_pages=zero_table_pages)

    return TableStageObservation(
        status="complete_with_warnings" if zero_table_pages else "complete",
        document_scope_complete=True,
        routed_pages=expected_pages,
        routed_page_count=len(expected_pages),
        logical_table_count=len(stage.tables),
        family_assignment_count=len(stage.assignments),
        family_count=len(stage.families),
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
        learned_fallback=config.learned_table_fallback,
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
