"""Aggregate-only restoration that separates reading-order and style evidence."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.chunked_conversion.page_evidence import PageEvidence, PageEvidenceError
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionPage,
)
from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)


@dataclass(frozen=True)
class AggregatePageSource:
    """Small path-backed page record retained after decoded range JSON is released."""

    page_no: int
    payload_path: Path
    image_path: Path
    image_scale: float
    image_mode: str
    image_size: tuple[int, int]
    image_pixels_sha256: str
    page_height: float
    image_png: bytes | None = None


PhaseObserver = Callable[[str], None]


def restore_ordering_page(evidence: PageEvidence) -> Any:
    """Restore only the page state consumed by Docling reading order."""
    from docling.datamodel.base_models import (
        AssembledUnit,
        ContainerElement,
        FigureElement,
        Page,
        Table,
        TextElement,
    )
    from docling_core.types.doc import Size  # type: ignore[attr-defined]

    payload = evidence.page_payload
    assembled = payload.get("assembled")
    size_payload = payload.get("size")
    if not isinstance(assembled, dict) or not isinstance(assembled.get("elements"), list):
        raise PageEvidenceError(f"assembled evidence is invalid: {evidence.page_no}")
    if not isinstance(size_payload, dict):
        raise PageEvidenceError(f"page size evidence is invalid: {evidence.page_no}")
    classes = {cls.__name__: cls for cls in (TextElement, Table, FigureElement, ContainerElement)}
    raw_elements = assembled["elements"]
    if len(raw_elements) != len(evidence.assembled_element_types):
        raise PageEvidenceError(f"typed element count differs: {evidence.page_no}")
    elements = []
    for raw, class_name in zip(raw_elements, evidence.assembled_element_types, strict=True):
        cls = classes.get(class_name)
        if cls is None:
            raise PageEvidenceError(f"unknown assembled element type: {class_name}")
        elements.append(cls.model_validate(raw))
    try:
        unit = AssembledUnit(
            elements=elements,
            body=[elements[index] for index in evidence.assembled_body_indices],
            headers=[elements[index] for index in evidence.assembled_header_indices],
        )
    except IndexError as error:
        raise PageEvidenceError(f"assembled membership differs: {evidence.page_no}") from error
    return Page(
        page_no=evidence.page_no,
        size=Size.model_validate(size_payload),
        assembled=unit,
        parsed_page=None,
    )


def suppress_confirmed_table_regions(page: Any, projection: OrderingProjectionPage) -> Any:
    """Remove only raw assembled elements covered by validated custom tables."""
    confirmed_regions = projection.ordering_suppressed_table_regions
    if not confirmed_regions:
        return page
    try:
        features = projection.features
        displayed_size = features.displayed_page_size_pdf_points
        source_bbox = features.source_page_bbox_pdf_points_bottom_left
        rotation = features.page_rotation_degrees
        regions = [item.bbox_pdf_points_bottom_left for item in confirmed_regions]
        transform = DisplayedPageTransform.create(displayed_size, source_bbox, rotation)
    except ValueError as error:
        raise PageEvidenceError(f"ordering page geometry is invalid: {page.page_no}") from error

    from docling.datamodel.base_models import AssembledUnit, Table, TextElement

    suppress_unlocated_text = any(item.suppression_scope == "page" for item in confirmed_regions)
    retained = [
        item
        for item in page.assembled.elements
        if not _element_is_suppressed(
            item,
            transform,
            regions,
            native_table=Table,
            text_element=TextElement,
            suppress_unlocated_text=suppress_unlocated_text,
        )
    ]
    retained_ids = {id(item) for item in retained}
    page.assembled = AssembledUnit(
        elements=retained,
        body=[item for item in page.assembled.body if id(item) in retained_ids],
        headers=[item for item in page.assembled.headers if id(item) in retained_ids],
    )
    return page


def _element_is_suppressed(
    item: Any,
    transform: DisplayedPageTransform,
    regions: Sequence[tuple[float, ...]],
    *,
    native_table: type[Any],
    text_element: type[Any],
    suppress_unlocated_text: bool,
) -> bool:
    """Match one assembled element to a custom table footprint, failing closed."""
    displayed_bbox = _element_displayed_bbox(item, transform)
    if displayed_bbox is None:
        return isinstance(item, native_table) or (
            suppress_unlocated_text and isinstance(item, text_element)
        )
    return any(_substantially_overlaps(displayed_bbox, region) for region in regions)


def _element_displayed_bbox(
    item: Any, transform: DisplayedPageTransform
) -> tuple[float, float, float, float] | None:
    """Read one normalized Docling cluster box in displayed coordinates."""
    cluster = getattr(item, "cluster", None)
    bbox = getattr(cluster, "bbox", None)
    if bbox is None:
        return None
    try:
        left = float(bbox.l)
        right = float(bbox.r)
        first_y = float(bbox.t)
        second_y = float(bbox.b)
        origin = getattr(getattr(bbox, "coord_origin", None), "value", None)
        if origin is None:
            origin = str(getattr(bbox, "coord_origin", ""))
        if str(origin).upper().endswith("TOPLEFT"):
            source_height = transform.displayed_height
            bottom = source_height - max(first_y, second_y)
            top = source_height - min(first_y, second_y)
        elif str(origin).upper().endswith("BOTTOMLEFT"):
            bottom = min(first_y, second_y)
            top = max(first_y, second_y)
        else:
            return None
        return (min(left, right), bottom, max(left, right), top)
    except (TypeError, ValueError):
        return None


def _substantially_overlaps(
    element: tuple[float, float, float, float],
    region: tuple[float, ...],
) -> bool:
    """Suppress elements centered in or predominantly covered by a table region."""
    if len(region) != 4:
        return False
    left, bottom, right, top = element
    region_left, region_bottom, region_right, region_top = region
    center_x = (left + right) / 2
    center_y = (bottom + top) / 2
    if region_left <= center_x <= region_right and region_bottom <= center_y <= region_top:
        return True
    overlap_width = max(0.0, min(right, region_right) - max(left, region_left))
    overlap_height = max(0.0, min(top, region_top) - max(bottom, region_bottom))
    element_area = max(0.0, right - left) * max(0.0, top - bottom)
    return element_area > 0 and (overlap_width * overlap_height) / element_area >= 0.25


def page_source(evidence: PageEvidence, payload_path: Path) -> AggregatePageSource:
    """Detach the raster and style paths needed after range payload release."""
    size = evidence.page_payload.get("size")
    if not isinstance(size, dict) or not isinstance(size.get("height"), int | float):
        raise PageEvidenceError(f"page size evidence is invalid: {evidence.page_no}")
    if evidence.image_path is None:
        raise PageEvidenceError(f"page raster location is missing: {evidence.page_no}")
    return AggregatePageSource(
        page_no=evidence.page_no,
        payload_path=payload_path,
        image_path=evidence.image_path,
        image_scale=evidence.image_scale,
        image_mode=evidence.image_mode,
        image_size=evidence.image_size,
        image_pixels_sha256=evidence.image_pixels_sha256,
        page_height=float(size["height"]),
    )


__all__ = [
    "AggregatePageSource",
    "page_source",
    "restore_ordering_page",
]
