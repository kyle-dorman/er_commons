"""Normalize native PDF geometry into the displayed routing coordinate system."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypedDict

Point = tuple[float, float]
Rectangle = tuple[float, float, float, float]
SUPPORTED_ROTATIONS = frozenset({0, 90, 180, 270})


class RoutingGeometry(TypedDict):
    """Coverage measurements in the displayed PDF page coordinate system."""

    displayed_page_size_pdf_points: list[float]
    source_page_bbox_pdf_points_bottom_left: list[float]
    routing_page_bbox_pdf_points_bottom_left: list[float]
    routing_coordinate_system: str
    page_rotation_degrees: int
    text_width_fraction: float
    text_height_fraction: float


def _validated_rectangle(rectangle: Rectangle, *, label: str) -> Rectangle:
    values = tuple(float(value) for value in rectangle)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{label} contains a non-finite coordinate")
    left, bottom, right, top = values
    if right <= left or top <= bottom:
        raise ValueError(f"{label} has a non-positive span")
    return left, bottom, right, top


@dataclass(frozen=True)
class DisplayedPageTransform:
    """Validated mapping from source PDF canvas points to displayed points."""

    displayed_width: float
    displayed_height: float
    page_bbox: Rectangle
    rotation_degrees: int

    @classmethod
    def create(
        cls,
        displayed_page_size: tuple[float, float],
        page_bbox: Rectangle,
        rotation_degrees: int,
    ) -> DisplayedPageTransform:
        """Validate one page transform before any routing measurement uses it."""
        if rotation_degrees not in SUPPORTED_ROTATIONS:
            raise ValueError(f"unsupported PDF page rotation: {rotation_degrees}")
        displayed_width, displayed_height = (float(value) for value in displayed_page_size)
        if not all(math.isfinite(value) and value > 0 for value in displayed_page_size):
            raise ValueError("displayed page size must be finite and positive")
        ordered_bbox = _validated_rectangle(page_bbox, label="page bbox")
        left, bottom, right, top = ordered_bbox
        canvas_size = (right - left, top - bottom)
        expected_size = (
            (canvas_size[1], canvas_size[0]) if rotation_degrees in {90, 270} else canvas_size
        )
        if not all(
            math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-4)
            for actual, expected in zip(
                (displayed_width, displayed_height), expected_size, strict=True
            )
        ):
            raise ValueError("displayed page size disagrees with bbox and rotation")
        return cls(displayed_width, displayed_height, ordered_bbox, rotation_degrees)

    @property
    def canvas_width(self) -> float:
        return self.page_bbox[2] - self.page_bbox[0]

    @property
    def canvas_height(self) -> float:
        return self.page_bbox[3] - self.page_bbox[1]

    def to_displayed_point(self, point: Point) -> Point:
        """Rotate one page-local source point into displayed orientation."""
        x, y = point
        if self.rotation_degrees == 0:
            return x, y
        if self.rotation_degrees == 90:
            return y, self.canvas_width - x
        if self.rotation_degrees == 180:
            return self.canvas_width - x, self.canvas_height - y
        return self.canvas_height - y, x

    def to_displayed_rectangle(self, rectangle: Rectangle) -> Rectangle | None:
        """Clip visible source geometry and transform it into displayed coordinates."""
        left, bottom, right, top = _validated_rectangle(rectangle, label="text rectangle")
        page_left, page_bottom, page_right, page_top = self.page_bbox
        left = max(left, page_left)
        bottom = max(bottom, page_bottom)
        right = min(right, page_right)
        top = min(top, page_top)
        if right <= left or top <= bottom:
            return None
        local_corners = (
            (left - page_left, bottom - page_bottom),
            (left - page_left, top - page_bottom),
            (right - page_left, bottom - page_bottom),
            (right - page_left, top - page_bottom),
        )
        displayed = [self.to_displayed_point(point) for point in local_corners]
        return (
            min(point[0] for point in displayed),
            min(point[1] for point in displayed),
            max(point[0] for point in displayed),
            max(point[1] for point in displayed),
        )


def _coverage_fractions(
    rectangles: list[Rectangle],
    *,
    displayed_width: float,
    displayed_height: float,
) -> tuple[float, float]:
    """Measure the bounding extent of displayed text rectangles."""
    if not rectangles:
        return 0.0, 0.0
    text_left = min(rectangle[0] for rectangle in rectangles)
    text_bottom = min(rectangle[1] for rectangle in rectangles)
    text_right = max(rectangle[2] for rectangle in rectangles)
    text_top = max(rectangle[3] for rectangle in rectangles)
    width_fraction = (text_right - text_left) / displayed_width
    height_fraction = (text_top - text_bottom) / displayed_height
    if not (0.0 <= width_fraction <= 1.0 and 0.0 <= height_fraction <= 1.0):
        raise ValueError("normalized text coverage lies outside [0, 1]")
    return width_fraction, height_fraction


def measure_routing_geometry(
    displayed_page_size: tuple[float, float],
    page_bbox: Rectangle,
    rotation_degrees: int,
    text_rectangles: list[Rectangle],
) -> RoutingGeometry:
    """Measure native-text coverage in the displayed page orientation."""
    transform = DisplayedPageTransform.create(
        displayed_page_size,
        page_bbox,
        rotation_degrees,
    )
    displayed_rectangles = [
        displayed
        for rectangle in text_rectangles
        if (displayed := transform.to_displayed_rectangle(rectangle)) is not None
    ]
    width_fraction, height_fraction = _coverage_fractions(
        displayed_rectangles,
        displayed_width=transform.displayed_width,
        displayed_height=transform.displayed_height,
    )
    page_left, page_bottom, page_right, page_top = transform.page_bbox
    return {
        "displayed_page_size_pdf_points": [
            transform.displayed_width,
            transform.displayed_height,
        ],
        "source_page_bbox_pdf_points_bottom_left": [
            page_left,
            page_bottom,
            page_right,
            page_top,
        ],
        "routing_page_bbox_pdf_points_bottom_left": [
            0.0,
            0.0,
            transform.displayed_width,
            transform.displayed_height,
        ],
        "routing_coordinate_system": "displayed_pdf_points_bottom_left",
        "page_rotation_degrees": rotation_degrees,
        "text_width_fraction": width_fraction,
        "text_height_fraction": height_fraction,
    }
