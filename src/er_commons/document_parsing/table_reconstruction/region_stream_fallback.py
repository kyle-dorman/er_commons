"""Recover unruled Heron table regions with source-faithful Camelot Stream."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.document_parsing.table_reconstruction.learned_table_types import JsonObject
from er_commons.document_parsing.table_reconstruction.region_stream_geometry import (
    candidate_measurements,
    geometry_issue,
    intersection_area,
)
from er_commons.document_parsing.table_reconstruction.region_stream_parser import (
    read_region_tables,
)
from er_commons.document_parsing.table_reconstruction.region_stream_text import (
    qualify_text_and_cleanup,
)
from er_commons.document_parsing.table_reconstruction.region_stream_types import (
    RegionStreamContext,
    RegionStreamResult,
)


def _attempt_region(
    region: JsonObject,
    context: RegionStreamContext,
) -> RegionStreamResult:
    """Coordinate parser, geometry, text, and cleanup owners for one region."""
    region_id = str(region["region_id"])
    region_bbox = [float(value) for value in region["bbox_pdf_points_bottom_left"]]
    try:
        tables = read_region_tables(context.pdf_path, context.page_number, region_bbox)
    except Exception as error:
        return RegionStreamResult.abstained(
            region_id,
            "parser_failure",
            {"error_type": type(error).__name__},
        )
    measurements: JsonObject = {"stream_return_count": len(tables)}
    if len(tables) != 1:
        return RegionStreamResult.abstained(
            region_id,
            "ambiguous_stream_return_count",
            measurements,
        )
    table = tables[0]
    measurements.update(candidate_measurements(table, region_bbox))
    geometry_reason = _qualify_geometry(table, region_bbox, context, measurements)
    if geometry_reason is not None:
        return RegionStreamResult.abstained(region_id, geometry_reason, measurements)
    text_reason, text_values = qualify_text_and_cleanup(table, region_bbox, context)
    measurements.update(text_values)
    if text_reason is not None:
        return RegionStreamResult.abstained(region_id, text_reason, measurements)
    candidate = {
        "parser": "camelot_stream",
        "parser_order": int(table.order),
        "region_id": region_id,
        "table": table,
        "bbox_pdf_points_bottom_left": [float(value) for value in table._bbox],
    }
    return RegionStreamResult.accepted(region_id, measurements, candidate)


def _qualify_geometry(
    table: Any,
    region_bbox: list[float],
    context: RegionStreamContext,
    measurements: JsonObject,
) -> str | None:
    """Record geometry thresholds and return the unchanged abstention reason."""
    maximum_overshoot = float(context.detection["maximum_region_stream_bbox_overshoot_points"])
    reason, measured_overshoot = geometry_issue(
        table,
        page_size=context.page_size,
        region_bbox=region_bbox,
        maximum_cell_overshoot=maximum_overshoot,
    )
    measurements.update(
        {
            "maximum_cell_bbox_overshoot_points": measured_overshoot,
            "maximum_allowed_cell_bbox_overshoot_points": maximum_overshoot,
        }
    )
    if reason is not None:
        return reason
    if measurements["candidate_region_iou"] < float(context.detection["minimum_region_match_iou"]):
        return "region_mismatch"
    return None


def _ownership_result(
    region: JsonObject,
    unmatched: list[JsonObject],
    opencv_ruled_regions: list[JsonObject],
    accepted_candidates: list[JsonObject],
) -> RegionStreamResult | None:
    """Abstain when a region overlaps evidence owned by another table candidate."""
    region_id = str(region["region_id"])
    box = [float(value) for value in region["bbox_pdf_points_bottom_left"]]
    conflicting_regions = _overlapping_layout_regions(region, unmatched)
    ruled_overlap = sum(
        intersection_area(
            box,
            [float(value) for value in ruled["bbox_pdf_points_bottom_left"]],
        )
        for ruled in opencv_ruled_regions
    )
    accepted_overlap = any(
        intersection_area(
            box,
            [float(value) for value in candidate["bbox_pdf_points_bottom_left"]],
        )
        > 0
        for candidate in accepted_candidates
    )
    if ruled_overlap > 0:
        return RegionStreamResult.abstained(
            region_id,
            "ruled_region_overlap",
            {"opencv_ruled_overlap_area": ruled_overlap},
        )
    if conflicting_regions or accepted_overlap:
        return RegionStreamResult.abstained(
            region_id,
            "ambiguous_region_ownership",
            {
                "overlapping_layout_region_count": len(conflicting_regions),
                "overlaps_accepted_candidate": accepted_overlap,
            },
        )
    return None


def _overlapping_layout_regions(
    region: JsonObject,
    unmatched: list[JsonObject],
) -> list[JsonObject]:
    """Return other unmatched layout regions that intersect the current region."""
    box = [float(value) for value in region["bbox_pdf_points_bottom_left"]]
    return [
        other
        for other in unmatched
        if other is not region
        and intersection_area(
            box,
            [float(value) for value in other["bbox_pdf_points_bottom_left"]],
        )
        > 0
    ]


def apply_region_stream_fallbacks(
    *,
    pdf_path: Path,
    page_number: int,
    page_size: tuple[float, float],
    opencv_ruled_regions: list[JsonObject],
    accepted_candidates: list[JsonObject],
    parser_evidence: JsonObject,
    layout_regions: list[JsonObject],
    detection: JsonObject,
    cleanup: JsonObject,
    table_rows: Callable[[Any], list[list[str]]],
    clean_rows: Callable[[list[list[str]], JsonObject], tuple[list[list[str]], JsonObject]],
) -> list[JsonObject]:
    """Attempt Stream only for unruled, unambiguous unmatched Heron regions."""
    matches = parser_evidence.get("region_matches", [])
    matches_by_id = {str(item["region_id"]): item for item in matches if isinstance(item, dict)}
    unmatched = [
        region
        for region in layout_regions
        if matches_by_id.get(str(region["region_id"]), {}).get("matched") is False
    ]
    context = RegionStreamContext(
        pdf_path=pdf_path,
        page_number=page_number,
        page_size=page_size,
        detection=detection,
        cleanup=cleanup,
        table_rows=table_rows,
        clean_rows=clean_rows,
    )
    results = [
        _ownership_result(region, unmatched, opencv_ruled_regions, accepted_candidates)
        or _attempt_region(region, context)
        for region in unmatched
    ]
    _publish_results(results, matches_by_id, parser_evidence)
    return [result.candidate for result in results if result.candidate is not None]


def _publish_results(
    results: list[RegionStreamResult],
    matches_by_id: dict[str, JsonObject],
    parser_evidence: JsonObject,
) -> None:
    """Apply accepted ownership and publish the legacy evidence dictionaries."""
    for result in results:
        match = matches_by_id[result.region_id]
        match["region_stream_status"] = result.status
        match["region_stream_reason"] = result.reason
        if result.candidate is not None:
            match["matched"] = True
    parser_evidence["region_stream_attempts"] = [result.evidence() for result in results]


__all__ = ["apply_region_stream_fallbacks"]
