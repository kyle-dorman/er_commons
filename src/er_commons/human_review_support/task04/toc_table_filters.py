"""Table-shape filters for the Task 04A possible-TOC review queue."""

from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from er_commons.human_review_support.task04.canonical_evidence import (
    canonical_files,
    page_number,
    page_rows,
)
from er_commons.human_review_support.task04.json_io import read_jsonl_objects
from er_commons.human_review_support.task04.models import JsonObject
from er_commons.human_review_support.task04.toc_models import PageKey

WHITESPACE_RE = re.compile(r"\s+")


def full_page_table_pages(
    candidates: dict[str, Path], *, minimum_area_fraction: float = 0.5
) -> set[PageKey]:
    """Find page-dominant tables after numeric and repeated-column exclusions."""
    selected: set[PageKey] = set()
    for source_id, candidate in candidates.items():
        dimensions = {
            _integer(row.get("physical_page_number")): (
                _float(row.get("width_pdf_points")),
                _float(row.get("height_pdf_points")),
            )
            for row in page_rows(candidate)
        }
        tables_path = canonical_files(candidate).get("tables.jsonl")
        if tables_path is None:
            continue
        dominant = _dominant_tables(tables_path, dimensions, minimum_area_fraction)
        signature_counts = Counter(
            signature for _, _, signature in dominant if signature is not None
        )
        selected.update(
            (source_id, page)
            for page, numeric_two_column, signature in dominant
            if not numeric_two_column and (signature is None or signature_counts[signature] == 1)
        )
    return selected


def _dominant_tables(
    tables_path: Path,
    page_dimensions: dict[int, tuple[float, float]],
    minimum_area_fraction: float,
) -> list[tuple[int, bool, tuple[str, ...] | None]]:
    """Describe tables occupying at least the configured fraction of a page."""
    dominant: list[tuple[int, bool, tuple[str, ...] | None]] = []
    for table in read_jsonl_objects(tables_path):
        regions = table.get("regions")
        for region in regions if isinstance(regions, list) else []:
            if not isinstance(region, dict):
                continue
            page = page_number(str(region.get("page_id") or ""))
            bbox = region.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4 or page not in page_dimensions:
                continue
            left, bottom, right, top = (_float(value) for value in bbox)
            width, height = page_dimensions[page]
            area_fraction = (right - left) * (top - bottom) / (width * height)
            if area_fraction >= minimum_area_fraction:
                dominant.append((page, is_two_column_decimal_table(table), left_column(table)))
    return dominant


def is_two_column_decimal_table(table: JsonObject) -> bool:
    """Identify two-column tables whose second column is decimal numeric data."""
    shape = table.get("shape")
    if not isinstance(shape, list) or len(shape) < 2 or _integer(shape[1]) != 2:
        return False
    values = _column_values(table, 1)
    if len(values) < 3 or sum("." in value for value in values) < 2:
        return False
    try:
        return all(Decimal(value.replace(",", "")).is_finite() for value in values)
    except InvalidOperation:
        return False


def left_column(table: JsonObject) -> tuple[str, ...] | None:
    """Return a normalized left-column signature when it has useful specificity."""
    values = tuple(
        WHITESPACE_RE.sub(" ", value).strip().casefold()
        for value in _column_values(table, 0)
        if value.strip()
    )
    return values if len(values) >= 3 else None


def _column_values(table: JsonObject, column: int) -> list[str]:
    """Read populated cells in one canonical table column in row order."""
    cells = table.get("cells")
    if not isinstance(cells, list):
        return []
    rows: list[tuple[int, str]] = []
    for cell in cells:
        if not isinstance(cell, dict) or _integer(cell.get("column_index", -1)) != column:
            continue
        text = str(cell.get("text") or "").strip()
        if text:
            rows.append((_integer(cell.get("row_index", 0)), text))
    return [text for _, text in sorted(rows)]


def _float(value: object) -> float:
    """Read one numeric JSON value used by canonical geometry."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"expected numeric value, got {value!r}")
    return float(value)


def _integer(value: object) -> int:
    """Read one integer-valued canonical field."""
    return int(_float(value))


__all__ = ["full_page_table_pages", "is_two_column_decimal_table", "left_column"]
