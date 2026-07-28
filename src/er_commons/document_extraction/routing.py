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

TableRoute = Literal["full_page_numeric", "layout_regions", "no_table_route"]
COORDINATE_KEY = re.compile(r"\b\d{6}\.\d+_\d{7}\.\d+_?")


class StrictTableThresholds(BaseModel):
    """Reviewed thresholds for pages dominated by native-text tables."""

    minimum_text_width_fraction: float = Field(ge=0, le=1)
    minimum_text_height_fraction: float = Field(ge=0, le=1)
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
        width, height = (float(value) for value in page.get_size())
        text_page = page.get_textpage()
        try:
            text = text_page.get_text_range()
            rectangles = [
                tuple(float(value) for value in text_page.get_rect(index))
                for index in range(text_page.count_rects())
            ]
        finally:
            text_page.close()
        page.close()
    finally:
        document.close()

    nonspace = "".join(text.split())
    if rectangles:
        left = min(rectangle[0] for rectangle in rectangles)
        bottom = min(rectangle[1] for rectangle in rectangles)
        right = max(rectangle[2] for rectangle in rectangles)
        top = max(rectangle[3] for rectangle in rectangles)
        width_span = (right - left) / width
        height_span = (top - bottom) / height
    else:
        width_span = height_span = 0.0
    return {
        "physical_pdf_page": page_number,
        "page_size_pdf_points": [width, height],
        "native_character_count": len(text),
        "nonspace_character_count": len(nonspace),
        "native_text_rectangle_count": len(rectangles),
        "nonempty_line_count": sum(bool(line.strip()) for line in text.splitlines()),
        "text_width_fraction": width_span,
        "text_height_fraction": height_span,
        "nonspace_characters_per_square_point": len(nonspace) / (width * height),
        "digit_fraction": (
            sum(character.isdigit() for character in nonspace) / len(nonspace) if nonspace else 0.0
        ),
        "coordinate_key_count": len(COORDINATE_KEY.findall(text)),
    }


def classify_page(
    features: dict[str, Any],
    layout_table_regions: list[list[float]],
    strict: StrictTableThresholds,
    numeric: NumericTableThresholds,
) -> dict[str, Any]:
    """Choose a table route from page content, then layout table regions."""
    strict_checks = {
        "width": features["text_width_fraction"] >= strict.minimum_text_width_fraction,
        "height": features["text_height_fraction"] >= strict.minimum_text_height_fraction,
        "lines": features["nonempty_line_count"] >= strict.minimum_nonempty_line_count,
        "density": (
            features["nonspace_characters_per_square_point"]
            >= strict.minimum_nonspace_characters_per_square_point
        ),
        "digits": features["digit_fraction"] >= strict.minimum_digit_fraction,
    }
    numeric_checks = {
        "width": features["text_width_fraction"] >= numeric.minimum_text_width_fraction,
        "lines": features["nonempty_line_count"] >= numeric.minimum_nonempty_line_count,
        "density": (
            features["nonspace_characters_per_square_point"]
            >= numeric.minimum_nonspace_characters_per_square_point
        ),
        "digits": features["digit_fraction"] >= numeric.minimum_digit_fraction,
    }
    strict_positive = all(strict_checks.values())
    numeric_positive = all(numeric_checks.values())
    if strict_positive or numeric_positive:
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
        "layout_table_region_count": len(layout_table_regions),
        "layout_table_regions_pdf_points_bottom_left": layout_table_regions,
        "route": route,
    }


def layout_table_regions(document_payload: dict[str, Any], page_number: int) -> list[list[float]]:
    """Read Heron's table-labeled regions without consuming TableFormer cells."""
    regions: list[list[float]] = []
    for table in document_payload.get("tables", []):
        for provenance in table.get("prov", []):
            if int(provenance.get("page_no", -1)) != page_number:
                continue
            bbox = provenance.get("bbox", {})
            regions.append(
                [
                    float(bbox["l"]),
                    float(bbox["b"]),
                    float(bbox["r"]),
                    float(bbox["t"]),
                ]
            )
    return regions
