"""Source-agnostic page routing for table reconstruction.

PDFium supplies cheap native-text signals.  Heron supplies layout regions.
Neither reconstructs cells here: the clean Camelot pipeline owns that job.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from er_commons.document_extraction.routing_geometry import measure_routing_geometry

TableRoute = Literal["full_page_numeric", "layout_regions", "no_table_route"]
COORDINATE_KEY = re.compile(r"\b\d{6}\.\d+_\d{7}\.\d+_?")


class StrictTableThresholds(BaseModel):
    """Reviewed thresholds for pages dominated by native-text tables."""

    minimum_text_width_fraction: float = Field(ge=0, le=1)
    minimum_text_height_fraction: float = Field(ge=0, le=1)
    minimum_partial_text_height_fraction: float = Field(default=0.35, ge=0, le=1)
    minimum_nonempty_line_count: int = Field(gt=0)
    minimum_nonspace_characters_per_square_point: float = Field(gt=0)
    minimum_digit_fraction: float = Field(ge=0, le=1)


class NumericTableThresholds(BaseModel):
    """Reviewed thresholds for pages bearing substantial numeric tables."""

    minimum_text_width_fraction: float = Field(ge=0, le=1)
    minimum_nonempty_line_count: int = Field(gt=0)
    minimum_nonspace_characters_per_square_point: float = Field(gt=0)
    minimum_digit_fraction: float = Field(ge=0, le=1)


def page_features(pdf_path: Path, page_number: int) -> dict[str, Any]:
    """Measure deterministic native-text coverage and numeric-density features."""
    document = pdfium.PdfDocument(pdf_path)
    try:
        page = document[page_number - 1]
        displayed_values = tuple(float(value) for value in page.get_size())
        displayed_size = (displayed_values[0], displayed_values[1])
        bbox_values = tuple(float(value) for value in page.get_bbox())
        page_bbox = (bbox_values[0], bbox_values[1], bbox_values[2], bbox_values[3])
        rotation_degrees = int(page.get_rotation())
        text_page = page.get_textpage()
        try:
            text = text_page.get_text_range()
            rectangles = []
            for index in range(text_page.count_rects()):
                values = tuple(float(value) for value in text_page.get_rect(index))
                rectangles.append((values[0], values[1], values[2], values[3]))
        finally:
            text_page.close()
        page.close()
    finally:
        document.close()

    nonspace = "".join(text.split())
    geometry = measure_routing_geometry(
        displayed_size,
        page_bbox,
        rotation_degrees,
        rectangles,
    )
    page_area = (page_bbox[2] - page_bbox[0]) * (page_bbox[3] - page_bbox[1])
    return {
        "physical_pdf_page": page_number,
        "page_size_pdf_points": geometry["displayed_page_size_pdf_points"],
        **geometry,
        "native_character_count": len(text),
        "nonspace_character_count": len(nonspace),
        "native_text_rectangle_count": len(rectangles),
        "nonempty_line_count": sum(bool(line.strip()) for line in text.splitlines()),
        "nonspace_characters_per_square_point": len(nonspace) / page_area,
        "digit_fraction": (
            sum(character.isdigit() for character in nonspace) / len(nonspace) if nonspace else 0.0
        ),
        "coordinate_key_count": len(COORDINATE_KEY.findall(text)),
    }


def _strict_route_checks(
    features: dict[str, Any],
    thresholds: StrictTableThresholds,
) -> dict[str, bool]:
    """Evaluate the full-page table-dominance policy one signal at a time."""
    return {
        "width": features["text_width_fraction"] >= thresholds.minimum_text_width_fraction,
        "height": features["text_height_fraction"] >= thresholds.minimum_text_height_fraction,
        "lines": features["nonempty_line_count"] >= thresholds.minimum_nonempty_line_count,
        "density": (
            features["nonspace_characters_per_square_point"]
            >= thresholds.minimum_nonspace_characters_per_square_point
        ),
        "digits": features["digit_fraction"] >= thresholds.minimum_digit_fraction,
    }


def _numeric_route_checks(
    features: dict[str, Any],
    thresholds: NumericTableThresholds,
) -> dict[str, bool]:
    """Evaluate the broader numeric-table-bearing policy."""
    return {
        "width": features["text_width_fraction"] >= thresholds.minimum_text_width_fraction,
        "lines": features["nonempty_line_count"] >= thresholds.minimum_nonempty_line_count,
        "density": (
            features["nonspace_characters_per_square_point"]
            >= thresholds.minimum_nonspace_characters_per_square_point
        ),
        "digits": features["digit_fraction"] >= thresholds.minimum_digit_fraction,
    }


def _dense_partial_checks(
    features: dict[str, Any],
    strict_checks: dict[str, bool],
    thresholds: StrictTableThresholds,
) -> dict[str, bool]:
    """Replace only the full-height signal for a dense partial continuation sheet."""
    checks = {name: passed for name, passed in strict_checks.items() if name != "height"}
    checks["partial_height"] = (
        features["text_height_fraction"] >= thresholds.minimum_partial_text_height_fraction
    )
    return checks


def classify_page(
    features: dict[str, Any],
    layout_table_regions: list[list[float]],
    strict: StrictTableThresholds,
    numeric: NumericTableThresholds,
) -> dict[str, Any]:
    """Choose a table route from page content, then layout table regions."""
    strict_checks = _strict_route_checks(features, strict)
    numeric_checks = _numeric_route_checks(features, numeric)
    strict_positive = all(strict_checks.values())
    numeric_positive = all(numeric_checks.values())
    # A continuation sheet can legitimately occupy only part of the displayed
    # page height. Keep the policy orientation-independent and narrow: require
    # a declared minimum partial height plus every strict signal other than the
    # full-page height gate.
    dense_partial_checks = _dense_partial_checks(features, strict_checks, strict)
    dense_partial_table = (
        not strict_positive and not strict_checks["height"] and all(dense_partial_checks.values())
    )
    if strict_positive or numeric_positive or dense_partial_table:
        route: TableRoute = "full_page_numeric"
    elif layout_table_regions:
        route = "layout_regions"
    else:
        route = "no_table_route"
    return {
        **features,
        "strict_table_dominant": strict_positive,
        "strict_checks": strict_checks,
        "numeric_table_bearing": numeric_positive,
        "numeric_checks": numeric_checks,
        "dense_partial_table": dense_partial_table,
        "dense_partial_checks": dense_partial_checks,
        "layout_table_region_count": len(layout_table_regions),
        "layout_table_regions_pdf_points_bottom_left": layout_table_regions,
        "route": route,
    }


def layout_table_regions(document_payload: dict[str, Any], page_number: int) -> list[list[float]]:
    """Read Heron's table-labeled regions without consuming TableFormer cells."""
    return [
        observation["bbox_pdf_points_bottom_left"]
        for observation in layout_table_observations(document_payload, page_number)
    ]


def layout_table_observations(
    document_payload: dict[str, Any],
    page_number: int,
) -> list[dict[str, Any]]:
    """Retain raw Docling pointers for every routed Heron table observation."""
    observations: list[dict[str, Any]] = []
    for table_index, table in enumerate(document_payload.get("tables", [])):
        for provenance_index, provenance in enumerate(table.get("prov", [])):
            if int(provenance.get("page_no", -1)) != page_number:
                continue
            bbox = provenance.get("bbox", {})
            observations.append(
                {
                    "raw_object_ref": f"#/tables/{table_index}",
                    "provenance_index": provenance_index,
                    "bbox_pdf_points_bottom_left": [
                        float(bbox["l"]),
                        float(bbox["b"]),
                        float(bbox["r"]),
                        float(bbox["t"]),
                    ],
                }
            )
    return observations
