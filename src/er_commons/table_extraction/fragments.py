"""Project repeated header-only edge detections out of logical table views."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from er_commons.table_extraction.continuations import (
    TableEdge,
    body_row_count,
    edge_geometry_compatible,
    exact_nonempty_headers_match,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class LogicalTableProjection:
    """Detached page and table views plus retained fragment evidence."""

    page_results: list[JsonObject]
    page_records: list[JsonObject]
    tables: list[JsonObject]
    fragments: list[JsonObject]


def _integer(record: JsonObject, key: str, *, fallback: str | None = None) -> int:
    """Read one required non-boolean integer from a persisted record."""
    value = record.get(key, record.get(fallback) if fallback is not None else None)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"invalid integer field: {key}")
    return value


def _tables_by_page(tables: list[JsonObject]) -> dict[int, list[JsonObject]]:
    by_page: dict[int, list[JsonObject]] = {}
    for table in tables:
        by_page.setdefault(int(table["physical_pdf_page"]), []).append(table)
    for records in by_page.values():
        records.sort(key=lambda item: int(item["page_table_index"]))
    return by_page


def _fragment_candidates(
    page_records: list[JsonObject], tables: list[JsonObject]
) -> list[JsonObject]:
    """Recognize only contextual repeated headers with no cleaned body rows."""
    by_page = _tables_by_page(tables)
    ordered = sorted(page_records, key=lambda item: int(item["physical_pdf_page"]))
    fragments: list[JsonObject] = []
    for left_page, right_page in zip(ordered, ordered[1:], strict=False):
        left_number = int(left_page["physical_pdf_page"])
        right_number = int(right_page["physical_pdf_page"])
        if right_number != left_number + 1:
            continue
        left_tables = by_page.get(left_number, [])
        right_tables = by_page.get(right_number, [])
        if (
            not left_tables
            or len(right_tables) != 1
            or right_page.get("boundary_markers_before_first_table")
        ):
            continue
        left = left_tables[-1]
        right = right_tables[0]
        if (
            body_row_count(left) <= 0
            or body_row_count(right) != 0
            or not exact_nonempty_headers_match(left, right)
            or not edge_geometry_compatible(
                TableEdge.from_record(left), TableEdge.from_record(right)
            )
        ):
            continue
        fragments.append(
            {
                "schema_version": "er_commons.header_only_continuation_fragment.v1",
                "physical_pdf_page": right_number,
                "fragment_table_id": str(right["table_id"]),
                "source_table_id": str(left["table_id"]),
                "reason": "exact_repeated_header_with_zero_body_rows",
                "shape_clean": list(right["shape_clean"]),
                "header_row_count": len(right["header_matrix"]),
                "table_record": str(right["table_record"]),
                "region_id": str(right["region_id"]),
            }
        )
    return fragments


def project_logical_tables(
    page_results: list[JsonObject],
    page_records: list[JsonObject],
    tables: list[JsonObject],
) -> LogicalTableProjection:
    """Preserve parser artifacts while removing header-only fragments from tables."""
    results = deepcopy(page_results)
    records = deepcopy(page_records)
    logical_tables = deepcopy(tables)
    existing_fragments = [
        fragment
        for result in results
        for fragment in result.get("header_only_continuation_fragments", [])
        if isinstance(fragment, dict)
    ]
    fresh_fragments = _fragment_candidates(records, logical_tables)
    fragments_by_id = {
        str(fragment["fragment_table_id"]): fragment
        for fragment in [*existing_fragments, *fresh_fragments]
    }
    fragments = [fragments_by_id[key] for key in sorted(fragments_by_id)]
    suppressed_ids = {str(item["fragment_table_id"]) for item in fragments}
    logical_tables = [
        table for table in logical_tables if str(table["table_id"]) not in suppressed_ids
    ]
    fragments_by_page = {
        page: [item for item in fragments if int(item["physical_pdf_page"]) == page]
        for page in {int(item["physical_pdf_page"]) for item in fragments}
    }

    for result in results:
        page = int(result["physical_pdf_page"])
        page_fragments = fragments_by_page.get(page, [])
        result["detected_table_count"] = _integer(
            result, "detected_table_count", fallback="table_count"
        )
        result["tables"] = [
            table for table in result["tables"] if str(table["table_id"]) not in suppressed_ids
        ]
        result["table_count"] = len(result["tables"])
        result["header_only_continuation_fragments"] = page_fragments
        suppressed_regions = {str(item["region_id"]) for item in page_fragments}
        for match in result["parser_evidence"].get("region_matches", []):
            if str(match.get("region_id")) in suppressed_regions:
                match["matched"] = False
                match["disposition"] = "header_only_continuation_fragment"

    detected_by_page = {
        int(result["physical_pdf_page"]): int(result["detected_table_count"]) for result in results
    }
    for record in records:
        page = int(record["physical_pdf_page"])
        page_fragments = fragments_by_page.get(page, [])
        record["detected_table_count"] = detected_by_page.get(
            page, _integer(record, "detected_table_count", fallback="table_count")
        )
        record["table_count"] = sum(
            int(table["physical_pdf_page"]) == page for table in logical_tables
        )
        record["header_only_continuation_fragments"] = page_fragments
        if str(record.get("footer_owner_table_id")) in suppressed_ids:
            record["footer_owner_table_id"] = None

    return LogicalTableProjection(results, records, logical_tables, fragments)
