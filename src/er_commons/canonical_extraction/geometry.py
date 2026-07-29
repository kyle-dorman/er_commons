"""Coordinate transforms shared by extraction and visual review."""

from __future__ import annotations

from er_commons.canonical_extraction.errors import ContractError

BoundingBox = tuple[float, float, float, float]


def pdf_bbox_to_render_pixels(
    bbox: BoundingBox,
    page_height: float,
    render_scale: float,
) -> BoundingBox:
    """Transform a bottom-left PDF box into top-left render pixels."""
    if page_height <= 0 or render_scale <= 0:
        raise ContractError("page height and render scale must be positive")

    left, bottom, right, top = bbox
    return (
        left * render_scale,
        (page_height - top) * render_scale,
        right * render_scale,
        (page_height - bottom) * render_scale,
    )
