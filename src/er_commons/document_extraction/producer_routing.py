"""Apply the accepted table router to every converted physical page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import write_jsonl
from er_commons.document_extraction.producer_config import ProducerConfig
from er_commons.document_extraction.producer_records import (
    PageRouteRecord,
    RoutingSummary,
)
from er_commons.document_extraction.routing import (
    TableRoute,
    classify_page,
    layout_table_observations,
    page_features,
)
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.source_freeze import write_json_atomic

ROUTES: tuple[TableRoute, ...] = (
    "no_table_route",
    "layout_regions",
    "full_page_numeric",
)


def route_complete_document(
    source: CompleteResolvedSource,
    document_payload: dict[str, Any],
    config: ProducerConfig,
) -> list[PageRouteRecord]:
    """Return one typed routing decision for every expected physical page."""
    records: list[PageRouteRecord] = []
    for page_number in range(1, source.source_page_count + 1):
        observations = layout_table_observations(document_payload, page_number)
        decision = classify_page(
            page_features(source.source_path, page_number),
            [item["bbox_pdf_points_bottom_left"] for item in observations],
            config.strict_table_dominant_thresholds,
            config.numeric_table_bearing_thresholds,
        )
        records.append(
            PageRouteRecord.model_validate(
                {
                    **decision,
                    "source_id": source.source_id,
                    "layout_table_observations": observations,
                    "status": "complete",
                }
            )
        )

    actual_pages = [record.physical_pdf_page for record in records]
    expected_pages = list(range(1, source.source_page_count + 1))
    if actual_pages != expected_pages:
        raise ValueError("routing observations do not cover the complete document")
    return records


def summarize_routes(records: list[PageRouteRecord]) -> RoutingSummary:
    """Count typed routes after confirming complete page ordering."""
    return RoutingSummary(
        status="complete",
        document_scope_complete=True,
        page_count=len(records),
        route_counts={route: sum(record.route == route for record in records) for route in ROUTES},
    )


def write_routing_artifacts(
    routing_root: Path,
    records: list[PageRouteRecord],
) -> RoutingSummary:
    """Persist complete route evidence and its compact summary."""
    routing_root.mkdir(parents=True, exist_ok=False)
    write_jsonl(
        routing_root / "page_routes.jsonl",
        [record.model_dump(mode="json") for record in records],
    )
    summary = summarize_routes(records)
    write_json_atomic(routing_root / "summary.json", summary.model_dump(mode="json"))
    return summary
