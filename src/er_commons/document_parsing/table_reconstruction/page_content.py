"""Normalize, clean, and serialize reconstructed table content."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from er_commons.document_parsing.table_reconstruction.page_types import CandidatePayload

NUMERIC_CELL = re.compile(
    r"^[\s$()<>+\-–—]*(?:\d[\d,]*(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-]?\d+)?(?:\s*[%a-zA-Z/³².-]+)?[\s*†‡]*$"
)
MISSING_VALUE_CELL = re.compile(r"^(?:-|–|—|−)+$")
COORDINATE_KEY = re.compile(r"\b\d{6}\.\d+_\d{7}\.\d+_?")


def sha256_file(path: Path) -> str:
    """Return one file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    """Write stable UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def normalize_text(value: str) -> str:
    """Normalize text for comparison without changing substantive characters."""
    return " ".join(unicodedata.normalize("NFKC", value).split()).strip()


def table_rows(table: Any) -> list[list[str]]:
    """Return a rectangular normalized row matrix from one Camelot table."""
    return [
        [normalize_text(str(value)) for value in row]
        for row in table.df.fillna("").astype(str).values.tolist()
    ]


def serialize_cells(table: Any) -> list[dict[str, Any]]:
    """Preserve Camelot cell text and geometry for later inspection."""
    return [
        {
            "row_index": row_index,
            "column_index": column_index,
            "text": normalize_text(str(cell.text)),
            "bbox_pdf_points_bottom_left": [
                float(cell.x1),
                float(cell.y1),
                float(cell.x2),
                float(cell.y2),
            ],
        }
        for row_index, row in enumerate(table.cells)
        for column_index, cell in enumerate(row)
    ]


def candidate_payload(candidate: dict[str, Any]) -> CandidatePayload:
    """Adapt Camelot or TableFormer output without mutating the candidate."""
    excluded = {"table", "raw_rows", "serialized_cells", "columns_pdf_points"}
    metadata = {key: value for key, value in candidate.items() if key not in excluded}
    if candidate["parser"] == "tableformer_accurate":
        return CandidatePayload(
            metadata=metadata,
            raw_rows=[list(row) for row in candidate["raw_rows"]],
            serialized_cells=list(candidate["serialized_cells"]),
            columns_pdf_points=list(candidate["columns_pdf_points"]),
        )
    table = candidate.get("table")
    if table is None:
        raise ValueError("Camelot candidate is missing its parser table")
    return CandidatePayload(
        metadata=metadata,
        raw_rows=table_rows(table),
        serialized_cells=serialize_cells(table),
        columns_pdf_points=[
            {"left": float(left), "right": float(right)} for left, right in table.cols
        ],
    )


def clean_rows(
    rows: list[list[str]],
    cleanup: dict[str, Any],
) -> tuple[list[list[str]], dict[str, Any]]:
    """Remove page furniture while preserving a rectangular native-text table."""
    footer_counter = re.compile(str(cleanup["footer_counter_pattern"]), re.IGNORECASE)
    filename = re.compile(str(cleanup["leading_filename_pattern"]), re.IGNORECASE)
    removed_footer_rows = [
        index
        for index, row in enumerate(rows)
        if footer_counter.search(" ".join(cell for cell in row if cell))
    ]
    removed_set = set(removed_footer_rows)
    retained = [row for index, row in enumerate(rows) if index not in removed_set]

    removed_filename_rows = []
    while retained:
        nonempty = [cell for cell in retained[0] if cell]
        if len(nonempty) != 1 or not filename.fullmatch(nonempty[0].lower()):
            break
        original_index = next(
            index for index, row in enumerate(rows) if row is retained[0] or row == retained[0]
        )
        removed_filename_rows.append(original_index)
        retained.pop(0)

    width = max((len(row) for row in retained), default=0)
    rectangular = [row + [""] * (width - len(row)) for row in retained]
    retained_columns = [
        column for column in range(width) if any(row[column] for row in rectangular)
    ]
    cleaned = [[row[column] for column in retained_columns] for row in rectangular]
    return cleaned, {
        "removed_footer_row_indices": removed_footer_rows,
        "removed_filename_row_indices": removed_filename_rows,
        "retained_column_indices": retained_columns,
        "effective_column_count": len(retained_columns),
    }


def header_matrix(rows: list[list[str]], cleanup: dict[str, Any]) -> list[list[str]]:
    """Return leading non-data rows as an exact native header signature."""
    header = []
    for row in rows[: int(cleanup["maximum_header_rows"])]:
        nonempty = [cell for cell in row if cell]
        numeric_fraction = (
            sum(bool(NUMERIC_CELL.fullmatch(cell)) for cell in nonempty) / len(nonempty)
            if nonempty
            else 0.0
        )
        if COORDINATE_KEY.search(" ".join(nonempty)) or (
            nonempty
            and numeric_fraction >= float(cleanup["minimum_numeric_cell_fraction_for_data_row"])
        ):
            break
        header.append(row)
    return header if any(cell for row in header for cell in row) else []


def column_type_signatures(rows: list[list[str]]) -> list[dict[str, Any]]:
    """Summarize text, numeric, explicit-missing, and empty column evidence."""
    width = max((len(row) for row in rows), default=0)
    signatures = []
    type_order = ("text", "numeric", "missing", "empty")
    for column in range(width):
        counts = {kind: 0 for kind in type_order}
        for row in rows:
            value = row[column] if column < len(row) else ""
            kind = (
                "empty"
                if not value
                else "missing"
                if MISSING_VALUE_CELL.fullmatch(value)
                else "numeric"
                if NUMERIC_CELL.fullmatch(value)
                else "text"
            )
            counts[kind] += 1
        total = len(rows)
        dominant = max(type_order, key=lambda kind: (counts[kind], -type_order.index(kind)))
        signatures.append(
            {
                "column_index": column,
                "dominant_type": dominant,
                "counts": counts,
                "fractions": {kind: counts[kind] / total if total else 0.0 for kind in type_order},
            }
        )
    return signatures


def parse_footer(text: str, cleanup: dict[str, Any]) -> dict[str, Any] | None:
    """Return the final worksheet footer found in native page text."""
    pattern = re.compile(str(cleanup["footer_pattern"]), re.IGNORECASE)
    matches = list(pattern.finditer(" ".join(text.split())))
    if not matches:
        return None
    match = matches[-1]
    return {
        "sheet_id": normalize_text(match.group("sheet")).lower(),
        "internal_page": int(match.group("page")),
        "internal_total": int(match.group("total")),
        "matched_text": match.group(0),
    }


def write_csv(path: Path, rows: list[list[str]]) -> None:
    """Write one rectangular CSV with explicit UTF-8 and newline handling."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows(rows)
