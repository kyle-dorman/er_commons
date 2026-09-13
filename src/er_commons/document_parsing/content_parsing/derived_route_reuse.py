"""Rebuild derived routes from the compact projection sealed by aggregation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.document_parsing.content_parsing.accepted_aggregate import (
    accepted_aggregate_inventory,
)
from er_commons.document_parsing.content_parsing.config import ContentParsingConfig
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.derived_publication_support import (
    rebind_aggregate_references,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_complete_document,
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


def routes_for_conversion(
    prepared: PreparedContentParsing,
    sealed_conversion: SealedConversion,
    range_run_root: Path | None,
    range_plan_path: Path | None,
    *,
    route_document: Callable[..., list[PageRouteRecord]] = route_complete_document,
) -> tuple[list[PageRouteRecord], bool, dict[str, Any] | None]:
    """Select source-free aggregate routing or the ordinary PDF-aware route."""
    accepted_inventory = (
        accepted_aggregate_inventory(sealed_conversion)
        if prepared.config.accepted_conversion_id is not None
        else None
    )
    if accepted_inventory is None and (range_run_root is None or range_plan_path is None):
        routes = route_document(
            prepared.source,
            sealed_conversion.output.document_payload,
            prepared.config,
        )
        reuse_aggregate_tables = False
    else:
        routes = routes_from_aggregate_projection(
            sealed_conversion.root / "records" / "ordering_projection.json",
            prepared.config,
            source_id=prepared.source.source_id,
            source_page_count=prepared.source.source_page_count,
        )
        routes = rebind_aggregate_references(routes, sealed_conversion.output.document_payload)
        expected_pages = list(range(1, prepared.source.source_page_count + 1))
        if [record.physical_pdf_page for record in routes] != expected_pages:
            raise ValueError("page projections do not cover the complete source")
        reuse_aggregate_tables = True
    return routes, reuse_aggregate_tables, accepted_inventory


__all__ = ["routes_for_conversion", "routes_from_aggregate_projection"]
