"""Apply source-faithful acceptance policy to one TableFormer prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.document_parsing.table_reconstruction.learned_table_cells import (
    build_logical_cells,
    derive_grid_boundaries,
    record_text_coverage,
    rectangular_rows,
)
from er_commons.document_parsing.table_reconstruction.learned_table_geometry import (
    normalized_characters,
)
from er_commons.document_parsing.table_reconstruction.learned_table_text import (
    NativeTextMatch,
    match_native_text,
    top_boundary_fringe_token_ids,
    unmatched_leading_tokens,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import (
    AbstentionReason,
    BoundingBox,
    FallbackAttempt,
    JsonObject,
    Position,
    abstain,
)
from er_commons.document_parsing.table_reconstruction.models import LearnedFallbackConfig
from er_commons.document_parsing.table_reconstruction.otsl import (
    OtslTopology,
    parse_otsl_topology,
    structural_bboxes,
)


@dataclass(frozen=True)
class PredictionStructure:
    """Validated structural inputs needed by the acceptance policy."""

    details: JsonObject
    responses: list[JsonObject]
    otsl_sequence: list[str]
    topology: OtslTopology
    boxes: dict[Position, BoundingBox]


@dataclass(frozen=True)
class MeasuredText:
    """Native-text assignment plus tokens excluded as clipped crop fringe."""

    match: NativeTextMatch
    fringe_token_ids: set[int]


def _prediction_otsl(details: JsonObject) -> Any:
    structure = details.get("prediction")
    return structure.get("rs_seq") if isinstance(structure, dict) else None


def _prediction_structure(
    prediction: JsonObject,
    *,
    policy: LearnedFallbackConfig,
    measurements: JsonObject,
) -> PredictionStructure | AbstentionReason:
    """Validate shape, OTSL topology, and structural cell geometry."""
    details = prediction.get("predict_details")
    responses = prediction.get("tf_responses")
    if not isinstance(details, dict) or not isinstance(responses, list):
        return "invalid_shape"
    otsl_sequence = _prediction_otsl(details)
    topology = parse_otsl_topology(otsl_sequence)
    if topology is None:
        return "invalid_otsl"
    if topology.rows < policy.minimum_rows or topology.columns < policy.minimum_columns:
        return "invalid_shape"
    measurements.update(
        {
            "predicted_rows": details.get("num_rows"),
            "predicted_columns": details.get("num_cols"),
            "otsl_rows": topology.rows,
            "otsl_columns": topology.columns,
        }
    )
    boxes = structural_bboxes(details, topology)
    if boxes is None:
        return "invalid_otsl"
    if not isinstance(otsl_sequence, list) or not all(
        isinstance(token, str) for token in otsl_sequence
    ):
        return "invalid_otsl"
    return PredictionStructure(details, responses, otsl_sequence, topology, boxes)


def _maximum_bbox_overshoot(
    boxes: dict[Position, BoundingBox],
    crop_size: tuple[int, int],
) -> float:
    width, height = crop_size
    return max(
        (
            max(0.0, -left, -top, right - width, bottom - height)
            for left, top, right, bottom in boxes.values()
        ),
        default=0.0,
    )


def _measure_prediction_text(
    *,
    structure: PredictionStructure,
    native_tokens: list[JsonObject],
    crop_size: tuple[int, int],
    policy: LearnedFallbackConfig,
    measurements: JsonObject,
) -> MeasuredText | AbstentionReason:
    """Assign native text and reject geometry or missing leading content."""
    text_match = match_native_text(
        details=structure.details,
        responses=structure.responses,
        native_tokens=native_tokens,
        topology=structure.topology,
        structural_bboxes=structure.boxes,
    )
    if text_match is None:
        return "invalid_grid_coverage"
    measurements.update(text_match.measurements())

    overshoot = _maximum_bbox_overshoot(structure.boxes, crop_size)
    measurements.update(
        {
            "maximum_bbox_overshoot_pixels": overshoot,
            "maximum_allowed_bbox_overshoot_pixels": policy.maximum_bbox_overshoot_pixels,
        }
    )
    if overshoot > policy.maximum_bbox_overshoot_pixels:
        return "out_of_bounds_geometry"

    fringe_ids = top_boundary_fringe_token_ids(
        native_tokens=native_tokens,
        structural_bboxes=structure.boxes,
        boundary_tolerance=policy.maximum_bbox_overshoot_pixels,
    )
    leading_tokens = unmatched_leading_tokens(
        native_tokens=native_tokens,
        unmatched_ids=text_match.unmatched_token_ids,
        topology=structure.topology,
        structural_bboxes=structure.boxes,
        crop_size=crop_size,
        boundary_tolerance=policy.maximum_bbox_overshoot_pixels,
        ignored_ids=fringe_ids,
    )
    measurements.update(
        {
            "unmatched_native_token_count": len(text_match.unmatched_token_ids),
            "top_boundary_fringe_native_token_ids": sorted(fringe_ids),
            "top_boundary_fringe_native_token_count": len(fringe_ids),
            "table_scope_unmatched_native_token_count": len(
                set(text_match.unmatched_token_ids) - fringe_ids
            ),
            "unmatched_leading_token_count": len(leading_tokens),
            "unmatched_leading_character_count": sum(
                len(normalized_characters(str(token.get("text", "")))) for token in leading_tokens
            ),
        }
    )
    return "unmatched_leading_text" if leading_tokens else MeasuredText(text_match, fringe_ids)


def _materialize_candidate(
    *,
    region_id: str,
    region_bbox: list[float],
    crop_size: tuple[int, int],
    native_tokens: list[JsonObject],
    structure: PredictionStructure,
    measured_text: MeasuredText,
    policy: LearnedFallbackConfig,
    measurements: JsonObject,
) -> FallbackAttempt:
    """Build cells, enforce text conservation, and project the accepted grid."""
    cell_build = build_logical_cells(
        topology=structure.topology,
        boxes=structure.boxes,
        text_by_owner=measured_text.match.text_by_owner,
        crop_size=crop_size,
        region_bbox=region_bbox,
        render_scale=policy.render_scale,
    )
    if cell_build is None:
        return abstain(region_id, "out_of_bounds_geometry", measurements)
    coverage, duplicated_characters = record_text_coverage(
        native_tokens=native_tokens,
        ignored_token_ids=measured_text.fringe_token_ids,
        cell_build=cell_build,
        measurements=measurements,
    )
    if duplicated_characters:
        return abstain(region_id, "duplicate_native_text", measurements)
    if coverage < policy.minimum_native_text_coverage:
        return abstain(region_id, "native_text_coverage_below_threshold", measurements)

    topology = structure.topology
    grid = derive_grid_boundaries(
        cell_build.cells,
        row_count=topology.rows,
        column_count=topology.columns,
    )
    if isinstance(grid, str):
        return abstain(region_id, grid, measurements)
    rows = rectangular_rows(
        cell_build.cells,
        row_count=topology.rows,
        column_count=topology.columns,
    )
    if not any(cell for row in rows for cell in row):
        return abstain(region_id, "cleanup_empty", measurements)
    candidate = {
        "parser": "tableformer_accurate",
        "parser_order": 0,
        "region_id": region_id,
        "bbox_pdf_points_bottom_left": region_bbox,
        "raw_rows": rows,
        "serialized_cells": cell_build.cells,
        "logical_cells": cell_build.cells,
        "otsl_sequence": structure.otsl_sequence,
        "columns_pdf_points": [
            {"left": grid.columns[index], "right": grid.columns[index + 1]}
            for index in range(topology.columns)
        ],
    }
    return FallbackAttempt(region_id, "accepted", None, measurements, candidate)


def evaluate_prediction(
    *,
    region_id: str,
    region_bbox: list[float],
    crop_size: tuple[int, int],
    native_tokens: list[JsonObject],
    prediction: JsonObject,
    policy: LearnedFallbackConfig,
) -> FallbackAttempt:
    """Apply the ordered structural, text, and materialization policy gates."""
    measurements: JsonObject = {
        "native_token_count": len(native_tokens),
        "minimum_native_text_coverage": policy.minimum_native_text_coverage,
    }
    if not native_tokens:
        return abstain(region_id, "insufficient_native_tokens", measurements)
    structure = _prediction_structure(
        prediction,
        policy=policy,
        measurements=measurements,
    )
    if isinstance(structure, str):
        return abstain(region_id, structure, measurements)
    measured_text = _measure_prediction_text(
        structure=structure,
        native_tokens=native_tokens,
        crop_size=crop_size,
        policy=policy,
        measurements=measurements,
    )
    if isinstance(measured_text, str):
        return abstain(region_id, measured_text, measurements)
    return _materialize_candidate(
        region_id=region_id,
        region_bbox=region_bbox,
        crop_size=crop_size,
        native_tokens=native_tokens,
        structure=structure,
        measured_text=measured_text,
        policy=policy,
        measurements=measurements,
    )


def unmatched_layout_regions(
    parser_evidence: JsonObject,
    layout_regions: list[JsonObject],
) -> list[JsonObject]:
    """Select only Heron regions that did not produce a Camelot table."""
    matches = parser_evidence.get("region_matches", [])
    if not isinstance(matches, list):
        return []
    matched_by_region = {
        str(item.get("region_id")): item.get("matched")
        for item in matches
        if isinstance(item, dict)
    }
    return [
        region
        for region in layout_regions
        if matched_by_region.get(str(region.get("region_id"))) is False
    ]
