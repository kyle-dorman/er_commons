"""Project producer cells through cleanup and validate the clean CSV view."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.table_records import (
    CleanTableCell,
    JsonObject,
    parse_bbox,
    parse_int_list,
)


@dataclass(frozen=True)
class _GridExtent:
    """One logical cell's exclusive raw-grid rectangle."""

    start_row: int
    end_row: int
    start_column: int
    end_column: int

    @classmethod
    def from_record(
        cls,
        cell: JsonObject,
        *,
        shape: tuple[int, int],
        table_id: str,
    ) -> _GridExtent:
        values = [
            cell.get("start_row_offset_idx"),
            cell.get("end_row_offset_idx"),
            cell.get("start_col_offset_idx"),
            cell.get("end_col_offset_idx"),
        ]
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            raise MappingContractError(f"non-integer learned-cell offsets for {table_id}")
        start_row, end_row, start_column, end_column = (int(cast(int, value)) for value in values)
        row_count, column_count = shape
        if not (
            0 <= start_row < end_row <= row_count and 0 <= start_column < end_column <= column_count
        ):
            raise MappingContractError(f"learned cell is outside shape_raw for {table_id}")
        return cls(start_row, end_row, start_column, end_column)

    def positions(self) -> set[tuple[int, int]]:
        return {
            (row, column)
            for row in range(self.start_row, self.end_row)
            for column in range(self.start_column, self.end_column)
        }


def _complete_grid(shape: tuple[int, int]) -> set[tuple[int, int]]:
    row_count, column_count = shape
    return {(row, column) for row in range(row_count) for column in range(column_count)}


def _rectangular_extent(positions: set[tuple[int, int]]) -> _GridExtent | None:
    if not positions:
        return None
    rows = sorted({row for row, _column in positions})
    columns = sorted({column for _row, column in positions})
    expected = {
        (row, column)
        for row in range(rows[0], rows[-1] + 1)
        for column in range(columns[0], columns[-1] + 1)
    }
    if positions != expected:
        return None
    return _GridExtent(rows[0], rows[-1] + 1, columns[0], columns[-1] + 1)


def clean_table_cells(
    raw_cells: list[JsonObject],
    *,
    shape_raw: tuple[int, int],
    shape_clean: tuple[int, int],
    cleanup: JsonObject,
    table_id: str,
) -> tuple[CleanTableCell, ...]:
    """Filter rectangular or span-aware producer cells through cleanup evidence."""
    retained_rows, retained_columns = _retained_axes(
        shape_raw=shape_raw,
        shape_clean=shape_clean,
        cleanup=cleanup,
        table_id=table_id,
    )
    if raw_cells and "start_row_offset_idx" in raw_cells[0]:
        return _clean_logical_cells(
            raw_cells,
            shape_raw=shape_raw,
            retained_rows=retained_rows,
            retained_columns=retained_columns,
            table_id=table_id,
        )
    return _clean_rectangular_cells(
        raw_cells,
        shape_raw=shape_raw,
        retained_rows=retained_rows,
        retained_columns=retained_columns,
        table_id=table_id,
    )


def _retained_axes(
    *,
    shape_raw: tuple[int, int],
    shape_clean: tuple[int, int],
    cleanup: JsonObject,
    table_id: str,
) -> tuple[list[int], list[int]]:
    """Validate cleanup indices and return retained raw-grid axes."""
    raw_rows, raw_columns = shape_raw
    removed_rows = set(
        parse_int_list(
            cleanup.get("removed_footer_row_indices"),
            field="removed_footer_row_indices",
            table_id=table_id,
        )
    )
    removed_rows.update(
        parse_int_list(
            cleanup.get("removed_filename_row_indices"),
            field="removed_filename_row_indices",
            table_id=table_id,
        )
    )
    if any(row < 0 or row >= raw_rows for row in removed_rows):
        raise MappingContractError(f"removed row is outside shape_raw for {table_id}")
    retained_columns = parse_int_list(
        cleanup.get("retained_column_indices"),
        field="retained_column_indices",
        table_id=table_id,
    )
    if (
        len(retained_columns) != len(set(retained_columns))
        or retained_columns != sorted(retained_columns)
        or any(column < 0 or column >= raw_columns for column in retained_columns)
    ):
        raise MappingContractError(f"invalid retained columns for {table_id}")
    if cleanup.get("effective_column_count") != len(retained_columns):
        raise MappingContractError(f"effective column count differs for {table_id}")
    retained_rows = [row for row in range(raw_rows) if row not in removed_rows]
    if shape_clean != (len(retained_rows), len(retained_columns)):
        raise MappingContractError(f"cleanup indices differ from shape_clean for {table_id}")
    return retained_rows, retained_columns


def _clean_rectangular_cells(
    raw_cells: list[JsonObject],
    *,
    shape_raw: tuple[int, int],
    retained_rows: list[int],
    retained_columns: list[int],
    table_id: str,
) -> tuple[CleanTableCell, ...]:
    """Project one-cell-per-position artifacts through retained axes."""
    positions: dict[tuple[int, int], JsonObject] = {}
    for cell in raw_cells:
        row = cell.get("row_index")
        column = cell.get("column_index")
        if (
            not isinstance(row, int)
            or isinstance(row, bool)
            or not isinstance(column, int)
            or isinstance(column, bool)
        ):
            raise MappingContractError(f"non-integer raw cell position for {table_id}")
        position = (row, column)
        if position in positions:
            raise MappingContractError(f"duplicate raw cell position for {table_id}: {position}")
        positions[position] = cell
    if set(positions) != _complete_grid(shape_raw):
        raise MappingContractError(f"raw cells do not match shape_raw for {table_id}")
    cleaned: list[CleanTableCell] = []
    for clean_row, raw_row in enumerate(retained_rows):
        for clean_column, raw_column in enumerate(retained_columns):
            cell = positions[(raw_row, raw_column)]
            text = cell.get("text")
            if not isinstance(text, str):
                raise MappingContractError(f"non-string cell text for {table_id}")
            cleaned.append(
                CleanTableCell(
                    row_index=clean_row,
                    column_index=clean_column,
                    end_row_offset_idx=clean_row + 1,
                    end_column_offset_idx=clean_column + 1,
                    text=text,
                    bbox_pdf_points_bottom_left=parse_bbox(
                        cell.get("bbox_pdf_points_bottom_left"),
                        owner=f"{table_id} cell {raw_row},{raw_column}",
                    ),
                )
            )
    return tuple(cleaned)


def _clean_logical_cells(
    raw_cells: list[JsonObject],
    *,
    shape_raw: tuple[int, int],
    retained_rows: list[int],
    retained_columns: list[int],
    table_id: str,
) -> tuple[CleanTableCell, ...]:
    raw_coverage: set[tuple[int, int]] = set()
    row_map = {raw: clean for clean, raw in enumerate(retained_rows)}
    column_map = {raw: clean for clean, raw in enumerate(retained_columns)}
    cleaned: list[CleanTableCell] = []
    clean_coverage: set[tuple[int, int]] = set()
    for cell in raw_cells:
        raw_extent = _GridExtent.from_record(cell, shape=shape_raw, table_id=table_id)
        raw_positions = raw_extent.positions()
        if raw_coverage & raw_positions:
            raise MappingContractError(f"learned cells overlap for {table_id}")
        raw_coverage |= raw_positions
        retained_positions = {
            (row_map[row], column_map[column])
            for row, column in raw_positions
            if row in row_map and column in column_map
        }
        if not retained_positions:
            continue
        clean_extent = _rectangular_extent(retained_positions)
        if clean_extent is None or clean_coverage & retained_positions:
            raise MappingContractError(f"cleanup fragments learned spans for {table_id}")
        clean_coverage |= retained_positions
        text = cell.get("text")
        if not isinstance(text, str):
            raise MappingContractError(f"non-string learned cell text for {table_id}")
        cleaned.append(
            CleanTableCell(
                row_index=clean_extent.start_row,
                column_index=clean_extent.start_column,
                end_row_offset_idx=clean_extent.end_row,
                end_column_offset_idx=clean_extent.end_column,
                text=text,
                bbox_pdf_points_bottom_left=parse_bbox(
                    cell.get("bbox_pdf_points_bottom_left"),
                    owner=f"{table_id} learned cell",
                ),
            )
        )
    if raw_coverage != _complete_grid(shape_raw):
        raise MappingContractError(f"learned cells do not cover shape_raw for {table_id}")
    clean_shape = (len(retained_rows), len(retained_columns))
    if clean_coverage != _complete_grid(clean_shape):
        raise MappingContractError(f"learned cells do not cover shape_clean for {table_id}")
    return tuple(cleaned)


def validate_clean_csv(
    path: Path,
    *,
    cells: tuple[CleanTableCell, ...],
    shape: tuple[int, int],
    table_id: str,
) -> None:
    """Require the clean CSV grid to exactly match cleaned logical cells."""
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    row_count, column_count = shape
    if len(rows) != row_count or any(len(row) != column_count for row in rows):
        raise MappingContractError(f"clean CSV differs from shape_clean for {table_id}")
    expected = [["" for _column in range(column_count)] for _row in range(row_count)]
    for cell in cells:
        expected[cell.row_index][cell.column_index] = cell.text
    if rows != expected:
        raise MappingContractError(f"clean CSV text differs from cleaned cells for {table_id}")
