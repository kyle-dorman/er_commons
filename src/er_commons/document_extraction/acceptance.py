"""Explicit acceptance policy for the mixed document and table pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal


def evaluate_acceptance(
    docling_comparison: dict[str, Any],
    range_pages: dict[str, set[tuple[str, int]]],
    route_records: list[dict[str, Any]],
    expected_routes: dict[str, Literal["full_page_numeric", "layout_regions"]],
    table_stage: dict[str, Any],
) -> dict[str, Any]:
    """Combine independent Docling, routing, and table-stage gates."""
    positive_routes = {
        (str(record["source_id"]), int(record["physical_pdf_page"])): str(record["route"])
        for record in route_records
        if record["route"] != "no_table_route"
    }
    actual_routes = {
        f"{source_id}:{page_number}": route
        for (source_id, page_number), route in positive_routes.items()
    }
    routed_range_names = {
        name
        for name, members in range_pages.items()
        if any(page in members for page in positive_routes)
    }
    non_table_ranges_match = all(
        item["equal"]
        for item in docling_comparison["ranges"]
        if item["range_name"] not in routed_range_names
    )
    routes_match = actual_routes == expected_routes
    tables_complete = bool(table_stage["all_complete"])
    return {
        "accepted": non_table_ranges_match and routes_match and tables_complete,
        "policy": (
            "Exact Docling comparison gates ranges without routed tables. "
            "Routed table ranges remain informational. Positive routes must "
            "match the fixed pilot assertion and complete the full table pipeline."
        ),
        "docling_non_table_ranges_match": non_table_ranges_match,
        "routed_table_ranges_excluded_from_docling_gate": sorted(routed_range_names),
        "full_docling_match_informational": docling_comparison["exact_semantic_match"],
        "routing": {
            "expected": expected_routes,
            "actual": actual_routes,
            "exact_match": routes_match,
        },
        "table_stage_complete": tables_complete,
    }


def require_acceptance(acceptance: dict[str, Any], report_path: Path) -> None:
    """Stop promotion after a failed acceptance report has been written."""
    if not acceptance["accepted"]:
        raise RuntimeError(f"document pipeline acceptance failed; review {report_path}")
