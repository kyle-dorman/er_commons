"""Detect and compare page-level table geometry."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from PIL import Image


def bbox_iou(left_box: list[float], right_box: list[float]) -> float:
    """Return intersection-over-union for bottom-left PDF rectangles."""
    left = max(left_box[0], right_box[0])
    bottom = max(left_box[1], right_box[1])
    right = min(left_box[2], right_box[2])
    top = min(left_box[3], right_box[3])
    intersection = max(0.0, right - left) * max(0.0, top - bottom)
    left_area = max(0.0, left_box[2] - left_box[0]) * max(0.0, left_box[3] - left_box[1])
    right_area = max(0.0, right_box[2] - right_box[0]) * max(0.0, right_box[3] - right_box[1])
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0


def visual_order_key(record: dict[str, Any]) -> tuple[float, float, float]:
    """Sort top-to-bottom, then left-to-right in bottom-left coordinates."""
    left, bottom, _right, top = record["bbox_pdf_points_bottom_left"]
    return (-top, left, -bottom)


def detect_ruled_regions(
    image: Image.Image,
    page_height: float,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Find connected table grids from horizontal and vertical ruling lines."""
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (int(config["horizontal_kernel_pixels"]), 1),
        ),
    )
    vertical = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, int(config["vertical_kernel_pixels"])),
        ),
    )
    ruling_mask = cv2.bitwise_or(horizontal, vertical)
    intersections = cv2.bitwise_and(horizontal, vertical)
    _, intersection_labels, _, _ = cv2.connectedComponentsWithStats(intersections, connectivity=8)
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(ruling_mask, connectivity=8)

    scale = float(config["render_scale"])
    regions = []
    for component in range(1, component_count):
        left, top, width, height, foreground_pixels = (
            int(value) for value in stats[component].tolist()
        )
        labels = np.unique(intersection_labels[top : top + height, left : left + width])
        intersection_count = int(np.count_nonzero(labels))
        if (
            width < int(config["minimum_region_width_pixels"])
            or height < int(config["minimum_region_height_pixels"])
            or intersection_count < int(config["minimum_intersections"])
        ):
            continue
        right = left + width
        bottom = top + height
        regions.append(
            {
                "bbox_image_pixels_top_left": [left, top, right, bottom],
                "bbox_pdf_points_bottom_left": [
                    left / scale,
                    page_height - bottom / scale,
                    right / scale,
                    page_height - top / scale,
                ],
                "intersection_count": intersection_count,
                "foreground_pixels": foreground_pixels,
            }
        )
    regions.sort(key=visual_order_key)
    for index, region in enumerate(regions, start=1):
        region["region_id"] = f"ruled_{index:03d}"
    return regions, ruling_mask


def rectangle_union_coverage(
    target: list[float],
    ruled_regions: list[dict[str, Any]],
    scale: float,
) -> float:
    """Measure the share of a parser box already explained by ruled boxes."""
    left, bottom, right, top = target
    width = max(1, round((right - left) * scale))
    height = max(1, round((top - bottom) * scale))
    mask = np.zeros((height, width), dtype=np.uint8)
    for region in ruled_regions:
        r_left, r_bottom, r_right, r_top = region["bbox_pdf_points_bottom_left"]
        i_left = max(left, r_left)
        i_bottom = max(bottom, r_bottom)
        i_right = min(right, r_right)
        i_top = min(top, r_top)
        if i_right <= i_left or i_top <= i_bottom:
            continue
        x1 = max(0, round((i_left - left) * scale))
        x2 = min(width, round((i_right - left) * scale))
        y1 = max(0, round((top - i_top) * scale))
        y2 = min(height, round((top - i_bottom) * scale))
        mask[y1:y2, x1:x2] = 1
    return float(mask.mean())
