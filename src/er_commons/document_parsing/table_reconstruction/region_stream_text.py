"""Native-text conservation and cleanup qualification for Stream candidates."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)
from er_commons.document_parsing.table_reconstruction.learned_table_geometry import (
    normalized_characters,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import JsonObject
from er_commons.document_parsing.table_reconstruction.native_text import native_word_tokens
from er_commons.document_parsing.table_reconstruction.region_stream_types import (
    RegionStreamContext,
)


def native_tokens(
    pdf_path: Path,
    page_number: int,
    region_bbox: list[float],
    *,
    scale: float,
) -> list[JsonObject]:
    """Read native words from one displayed-page region and release PDFium handles."""
    document = pdfium.PdfDocument(pdf_path)
    page = document[page_number - 1]
    try:
        width, height = (float(value) for value in page.get_size())
        bbox_values = [float(value) for value in page.get_bbox()]
        transform = DisplayedPageTransform.create(
            (width, height),
            (bbox_values[0], bbox_values[1], bbox_values[2], bbox_values[3]),
            int(page.get_rotation()),
        )
        text_page = page.get_textpage()
        try:
            return native_word_tokens(
                text_page,
                region_bbox,
                scale=scale,
                transform=transform,
            )
        finally:
            text_page.close()
    finally:
        page.close()
        document.close()


def text_measurements(table: Any, tokens: list[JsonObject]) -> JsonObject:
    """Measure character conservation using the existing order-insensitive policy."""
    native_text = "".join(
        _native_comparison_characters(str(token.get("text", ""))) for token in tokens
    )
    parsed_text = _normalized_table_text(table)
    native_counts = Counter(native_text)
    parsed_counts = Counter(parsed_text)
    matched = sum(
        min(count, parsed_counts[character]) for character, count in native_counts.items()
    )
    duplicated = sum(
        max(0, count - native_counts[character]) for character, count in parsed_counts.items()
    )
    return {
        "native_token_count": len(tokens),
        "native_character_count": len(native_text),
        "parsed_character_count": len(parsed_text),
        "matched_native_character_count": matched,
        "native_text_coverage": matched / len(native_text) if native_text else 0.0,
        "duplicated_native_character_count": duplicated,
    }


def qualify_text_and_cleanup(
    table: Any,
    region_bbox: list[float],
    context: RegionStreamContext,
) -> tuple[str | None, JsonObject]:
    """Apply the unchanged text-conservation gate before cleanup-shape checks."""
    tokens = native_tokens(
        context.pdf_path,
        context.page_number,
        region_bbox,
        scale=float(context.detection["render_scale"]),
    )
    measurements = text_measurements(table, tokens)
    minimum_coverage = float(context.detection["minimum_region_stream_native_text_coverage"])
    measurements["minimum_native_text_coverage"] = minimum_coverage
    if int(measurements["duplicated_native_character_count"]):
        return "duplicate_native_text", measurements
    if float(measurements["native_text_coverage"]) < minimum_coverage:
        return "native_text_coverage_below_threshold", measurements
    cleanup_reason, cleanup_measurements = _qualify_cleanup(table, context)
    measurements.update(cleanup_measurements)
    return cleanup_reason, measurements


def _qualify_cleanup(
    table: Any,
    context: RegionStreamContext,
) -> tuple[str | None, JsonObject]:
    """Require a cleaned result with at least two populated rows and columns."""
    cleaned, _cleanup = context.clean_rows(context.table_rows(table), context.cleanup)
    clean_shape = [len(cleaned), max((len(row) for row in cleaned), default=0)]
    populated_rows = sum(any(cell for cell in row) for row in cleaned)
    populated_columns = sum(
        any(column < len(row) and row[column] for row in cleaned)
        for column in range(clean_shape[1])
    )
    multi_cell_rows = sum(sum(bool(cell) for cell in row) >= 2 for row in cleaned)
    measurements: JsonObject = {
        "clean_rows": clean_shape[0],
        "clean_columns": clean_shape[1],
        "populated_row_count": populated_rows,
        "populated_column_count": populated_columns,
        "multi_cell_row_count": multi_cell_rows,
    }
    accepted = (
        min(clean_shape) >= 2
        and populated_rows >= 2
        and populated_columns >= 2
        and multi_cell_rows >= 2
    )
    return (None if accepted else "cleanup_empty"), measurements


def _native_comparison_characters(text: str) -> str:
    """Restore PDFium's removed discretionary hyphens for comparison only."""
    return normalized_characters(text).replace("\ufffe", "-")


def _normalized_table_text(table: Any) -> str:
    """Normalize every parsed cell using the established comparison policy."""
    return "".join(
        normalized_characters(str(value))
        for row in table.df.fillna("").astype(str).values.tolist()
        for value in row
    )


__all__ = ["native_tokens", "qualify_text_and_cleanup", "text_measurements"]
