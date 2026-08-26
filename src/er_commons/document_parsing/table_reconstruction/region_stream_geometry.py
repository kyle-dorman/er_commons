"""Geometry measurements and acceptance checks for Stream candidates."""

from __future__ import annotations

import math
from typing import Any

from er_commons.document_parsing.table_reconstruction.learned_table_types import JsonObject


def intersection_area(left_box: list[float], right_box: list[float]) -> float:
    """Return the overlap area of two bottom-left coordinate boxes."""
    left = max(left_box[0], right_box[0])
    bottom = max(left_box[1], right_box[1])
    right = min(left_box[2], right_box[2])
    top = min(left_box[3], right_box[3])
    return max(0.0, right - left) * max(0.0, top - bottom)


def intersection_over_union(left_box: list[float], right_box: list[float]) -> float:
    """Return intersection over union for two bottom-left coordinate boxes."""
    intersection = intersection_area(left_box, right_box)
    left_area = (left_box[2] - left_box[0]) * (left_box[3] - left_box[1])
    right_area = (right_box[2] - right_box[0]) * (right_box[3] - right_box[1])
    union = left_area + right_area - intersection
    return intersection / union if union > 0 else 0.0


def candidate_measurements(table: Any, region_bbox: list[float]) -> JsonObject:
    """Collect stable Camelot measurements recorded before qualification."""
    candidate_box = [float(value) for value in table._bbox]
    return {
        "candidate_region_iou": intersection_over_union(candidate_box, region_bbox),
        "raw_rows": int(table.shape[0]),
        "raw_columns": int(table.shape[1]),
        "accuracy": float(table.parsing_report.get("accuracy", 0.0)),
        "whitespace": float(table.parsing_report.get("whitespace", 0.0)),
    }


def geometry_issue(
    table: Any,
    *,
    page_size: tuple[float, float],
    region_bbox: list[float],
    maximum_cell_overshoot: float,
) -> tuple[str | None, float]:
    """Reject malformed grids and cells that materially exceed the candidate box."""
    rows, columns = (int(value) for value in table.shape)
    if rows < 2 or columns < 2 or len(table.cells) != rows:
        return "invalid_shape", 0.0
    if any(len(row) != columns for row in table.cells):
        return "invalid_shape", 0.0
    page_width, page_height = page_size
    candidate = [float(value) for value in table._bbox]
    if not _valid_page_box(candidate, page_width, page_height):
        return "invalid_geometry", 0.0
    if intersection_over_union(candidate, region_bbox) <= 0:
        return "invalid_geometry", 0.0
    issue, maximum_overshoot = _cell_geometry_issue(
        table,
        candidate,
        page_width=page_width,
        page_height=page_height,
    )
    if issue is not None:
        return issue, maximum_overshoot
    if not _grid_axes_are_monotonic(table):
        return "invalid_geometry", maximum_overshoot
    if maximum_overshoot > maximum_cell_overshoot:
        return "cell_bbox_exceeds_region", maximum_overshoot
    return None, maximum_overshoot


def _valid_page_box(box: list[float], page_width: float, page_height: float) -> bool:
    """Return whether a box is finite, ordered, and bounded by the page."""
    if not all(math.isfinite(value) for value in box):
        return False
    left, bottom, right, top = box
    return 0 <= left < right <= page_width and 0 <= bottom < top <= page_height


def _cell_geometry_issue(
    table: Any,
    candidate: list[float],
    *,
    page_width: float,
    page_height: float,
) -> tuple[str | None, float]:
    """Validate every cell and measure its largest candidate-box overshoot."""
    left, bottom, right, top = candidate
    maximum_overshoot = 0.0
    for row in table.cells:
        for cell in row:
            box = [float(cell.x1), float(cell.y1), float(cell.x2), float(cell.y2)]
            if not _valid_page_box(box, page_width, page_height):
                return "invalid_geometry", maximum_overshoot
            maximum_overshoot = max(
                maximum_overshoot,
                left - box[0],
                bottom - box[1],
                box[2] - right,
                box[3] - top,
            )
    return None, maximum_overshoot


def _grid_axes_are_monotonic(table: Any) -> bool:
    """Return whether Camelot's column and row intervals form an ordered grid."""
    columns = all(
        float(first[0]) < float(first[1]) <= float(second[0]) < float(second[1])
        for first, second in zip(table.cols, table.cols[1:], strict=False)
    )
    rows = all(
        float(first[0]) > float(first[1]) >= float(second[0]) > float(second[1])
        for first, second in zip(table.rows, table.rows[1:], strict=False)
    )
    return columns and rows


__all__ = [
    "candidate_measurements",
    "geometry_issue",
    "intersection_area",
    "intersection_over_union",
]
