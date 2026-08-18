"""Small geometry and text-normalization primitives for learned tables."""

from __future__ import annotations

import unicodedata
from typing import Any, cast

from er_commons.document_parsing.table_reconstruction.learned_table_types import BoundingBox


def normalized_characters(text: str) -> str:
    """Return comparable source characters without layout-only whitespace."""
    return "".join(unicodedata.normalize("NFKC", text).split())


def parse_bbox(value: Any) -> BoundingBox | None:
    """Parse one positive-area box from Docling dict or sequence form."""
    if isinstance(value, dict):
        values = [value.get(key) for key in ("l", "t", "r", "b")]
    elif isinstance(value, list) and len(value) == 4:
        values = value
    else:
        return None
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in values):
        return None
    left, top, right, bottom = (float(cast(int | float, item)) for item in values)
    if not (left < right and top < bottom):
        return None
    return left, top, right, bottom


def bbox_center(box: BoundingBox) -> tuple[float, float]:
    """Return the center point of a top-left-coordinate bounding box."""
    left, top, right, bottom = box
    return (left + right) / 2, (top + bottom) / 2


def project_crop_bbox_to_pdf(
    local_bbox: BoundingBox,
    *,
    crop_bbox: list[float],
    scale: float,
) -> list[float]:
    """Project top-left crop pixels into bottom-left PDF points."""
    left, top, right, bottom = local_bbox
    crop_left, _crop_bottom, _crop_right, crop_top = crop_bbox
    return [
        crop_left + left / scale,
        crop_top - bottom / scale,
        crop_left + right / scale,
        crop_top - top / scale,
    ]
