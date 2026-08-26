"""Rebuild derived routes from the compact projection sealed by aggregation."""

from __future__ import annotations

from pathlib import Path

from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
)
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_page_projections,
)


def routes_from_aggregate_projection(
    projection_path: Path,
    config: ContentParsingConfig,
    *,
    source_id: str,
    source_page_count: int,
) -> list[PageRouteRecord]:
    """Route the sealed compact page records without reopening range bundles."""
    artifact = OrderingProjectionArtifact.model_validate_json(projection_path.read_bytes())
    projections = [page.as_page_evidence() for page in artifact.pages]
    expected_pages = list(range(1, source_page_count + 1))
    actual_pages = [projection.physical_pdf_page for projection in projections]
    if actual_pages != expected_pages:
        raise ValueError("aggregate ordering projection does not cover the complete source")
    if any(projection.source_id != source_id for projection in projections):
        raise ValueError("aggregate ordering projection source identity differs")
    return route_page_projections(projections, config)


__all__ = ["routes_from_aggregate_projection"]
