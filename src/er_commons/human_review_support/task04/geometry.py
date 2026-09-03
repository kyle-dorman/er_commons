"""Page-coordinate transforms used only by the Task 04 review presentation."""

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)

BBox = tuple[float, float, float, float]


def source_page_transforms(
    source_pdf: Path, selected_pages: set[int]
) -> dict[int, DisplayedPageTransform]:
    """Load source-page rotations needed to align native text with rendered pages."""
    from pypdf import PdfReader

    reader = PdfReader(source_pdf, strict=False)
    result: dict[int, DisplayedPageTransform] = {}
    for physical_page in sorted(selected_pages):
        if physical_page > len(reader.pages):
            raise ValueError(
                f"selected physical page {physical_page} exceeds {source_pdf} page count "
                f"{len(reader.pages)}"
            )
        page = reader.pages[physical_page - 1]
        box = page.cropbox
        page_bbox = (float(box.left), float(box.bottom), float(box.right), float(box.top))
        width = page_bbox[2] - page_bbox[0]
        height = page_bbox[3] - page_bbox[1]
        rotation = int(page.rotation or 0) % 360
        displayed_size = (height, width) if rotation in {90, 270} else (width, height)
        result[physical_page] = DisplayedPageTransform.create(displayed_size, page_bbox, rotation)
    return result


def review_display_bbox(bbox: object, transform: DisplayedPageTransform | None) -> BBox | None:
    """Map a producer text box into the rendered page frame when required."""
    values = parse_bbox(bbox)
    if values is None or transform is None or transform.rotation_degrees == 0:
        return values
    left, bottom, right, top = transform.to_displayed_rectangle_unclipped(values)
    return float(left), float(bottom), float(right), float(top)


def canonical_region_display_bbox(
    region: Mapping[str, object],
    displayed_width: float,
    displayed_height: float,
    transform: DisplayedPageTransform | None,
) -> BBox | None:
    """Avoid rotating canonical regions already normalized to the display frame."""
    bbox = parse_bbox(region.get("bbox"))
    region_width = _number(region.get("page_width"))
    region_height = _number(region.get("page_height"))
    region_rotation_value = _number(region.get("rotation_degrees", 0))
    if region_width is None or region_height is None or region_rotation_value is None:
        return review_display_bbox(bbox, transform)
    region_rotation = int(region_rotation_value) % 360
    already_displayed = (
        region_rotation == 0
        and math.isclose(region_width, displayed_width, abs_tol=0.01)
        and math.isclose(region_height, displayed_height, abs_tol=0.01)
    )
    return bbox if already_displayed else review_display_bbox(bbox, transform)


def _number(value: object) -> float | None:
    """Parse one finite scalar while rejecting structured and boolean values."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def parse_bbox(value: object) -> BBox | None:
    """Return one finite, ordered four-value box or no usable geometry."""
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        values = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        return None
    left, bottom, right, top = values
    if right < left or top < bottom:
        return None
    return float(left), float(bottom), float(right), float(top)


def bboxes_overlap(first: BBox | None, second: BBox | None) -> bool:
    """Return whether two valid boxes overlap by positive area."""
    if first is None or second is None:
        return False
    return min(first[2], second[2]) > max(first[0], second[0]) and min(first[3], second[3]) > max(
        first[1], second[1]
    )


__all__ = [
    "BBox",
    "bboxes_overlap",
    "canonical_region_display_bbox",
    "parse_bbox",
    "review_display_bbox",
]
