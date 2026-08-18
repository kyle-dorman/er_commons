"""Adapt maintained page routing to diagnostic source records."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.document_parsing.content_parsing.routing import (
    classify_page,
    layout_table_observations,
    page_features,
)
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_markers import markers_before_first_table
from er_commons.parser_smoke.config import SmokeSpec
from er_commons.parser_smoke.records import RouteRecord

RouteService = Callable[[Path, dict[str, Any], int, SmokeSpec], RouteRecord]


def maintained_route(
    source_path: Path,
    document_payload: dict[str, Any],
    physical_page: int,
    spec: SmokeSpec,
) -> RouteRecord:
    """Run the production native-text and Heron-region routing policy."""
    observations = layout_table_observations(document_payload, physical_page)
    return {
        **classify_page(
            page_features(source_path, physical_page),
            [item["bbox_pdf_points_bottom_left"] for item in observations],
            spec.strict_table_dominant_thresholds,
            spec.numeric_table_bearing_thresholds,
        ),
        "layout_table_observations": observations,
        "boundary_markers_before_first_table": markers_before_first_table(
            document_payload, physical_page, observations
        ),
    }


def route_page(
    source: CompleteResolvedSource,
    document_payload: dict[str, Any],
    physical_page: int,
    spec: SmokeSpec,
    override: RouteService | None,
) -> RouteRecord:
    """Route one page and attach the source identity used by table extraction."""
    service = override or maintained_route
    return {
        **service(source.source_path, document_payload, physical_page, spec),
        "source_id": source.source_id,
    }
