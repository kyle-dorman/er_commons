"""Parse TableFormer's OTSL sequence into explicit logical-cell topology."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from er_commons.table_extraction.learned_table_geometry import parse_bbox
from er_commons.table_extraction.learned_table_types import BoundingBox, JsonObject, Position

ANCHOR_TOKENS = frozenset({"fcel", "ecel", "ched", "rhed", "srow"})
CONTINUATION_TOKENS = frozenset({"lcel", "ucel", "xcel"})
ALLOWED_TOKENS = ANCHOR_TOKENS | CONTINUATION_TOKENS | {"nl"}
# The pinned matcher consumes one predicted box for every anchor and xcel.
BBOX_TOKENS = ANCHOR_TOKENS | {"xcel"}


@dataclass(frozen=True)
class OtslTopology:
    """A validated rectangular grid and the logical cell owning each position."""

    grid: tuple[tuple[str, ...], ...]
    owner_by_position: dict[Position, Position]
    positions_by_owner: dict[Position, tuple[Position, ...]]

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def columns(self) -> int:
        return len(self.grid[0])


def _rectangular_grid(sequence: Any) -> tuple[tuple[str, ...], ...] | None:
    """Split a legal OTSL sequence into equal-width newline-terminated rows."""
    if not isinstance(sequence, list) or not sequence:
        return None
    if not all(isinstance(item, str) and item in ALLOWED_TOKENS for item in sequence):
        return None
    grid: list[tuple[str, ...]] = []
    current_row: list[str] = []
    for token in sequence:
        if token != "nl":
            current_row.append(token)
            continue
        if not current_row:
            return None
        grid.append(tuple(current_row))
        current_row = []
    if current_row or not grid or len({len(row) for row in grid}) != 1:
        return None
    return tuple(grid)


def _continuation_owner(
    token: str,
    position: Position,
    owner_by_position: dict[Position, Position],
) -> Position | None:
    """Resolve one continuation token from already visited neighbors."""
    row, column = position
    if token == "lcel":
        return owner_by_position.get((row, column - 1)) if column > 0 else None
    if token == "ucel":
        return owner_by_position.get((row - 1, column)) if row > 0 else None
    if row == 0 or column == 0:
        return None
    left_owner = owner_by_position.get((row, column - 1))
    upper_owner = owner_by_position.get((row - 1, column))
    return left_owner if left_owner is not None and left_owner == upper_owner else None


def _rectangular_owner_positions(
    owner_by_position: dict[Position, Position],
) -> dict[Position, tuple[Position, ...]] | None:
    """Require every logical cell to occupy one complete rectangle."""
    grouped: dict[Position, list[Position]] = {}
    for position, owner in owner_by_position.items():
        grouped.setdefault(owner, []).append(position)
    result: dict[Position, tuple[Position, ...]] = {}
    for owner, positions in grouped.items():
        rows = [position[0] for position in positions]
        columns = [position[1] for position in positions]
        expected = {
            (row, column)
            for row in range(min(rows), max(rows) + 1)
            for column in range(min(columns), max(columns) + 1)
        }
        if owner != (min(rows), min(columns)) or any(
            owner_by_position.get(position) != owner for position in expected
        ):
            return None
        result[owner] = tuple(sorted(positions))
    return result


def parse_otsl_topology(sequence: Any) -> OtslTopology | None:
    """Resolve legal OTSL anchors and continuations into logical cells."""
    grid = _rectangular_grid(sequence)
    if grid is None:
        return None
    owner_by_position: dict[Position, Position] = {}
    for row_index, row in enumerate(grid):
        for column_index, token in enumerate(row):
            position = (row_index, column_index)
            owner = (
                position
                if token in ANCHOR_TOKENS
                else _continuation_owner(token, position, owner_by_position)
            )
            if owner is None:
                return None
            owner_by_position[position] = owner
    positions_by_owner = _rectangular_owner_positions(owner_by_position)
    if positions_by_owner is None:
        return None
    return OtslTopology(grid, owner_by_position, positions_by_owner)


def structural_bboxes(
    details: JsonObject,
    topology: OtslTopology,
) -> dict[Position, BoundingBox] | None:
    """Map original predicted boxes to OTSL anchor positions."""
    values = details.get("prediction_bboxes_page")
    if not isinstance(values, list):
        return None
    by_owner: dict[Position, BoundingBox] = {}
    bbox_index = 0
    for row_index, row in enumerate(topology.grid):
        for column_index, token in enumerate(row):
            if token not in BBOX_TOKENS:
                continue
            if bbox_index >= len(values):
                return None
            box = parse_bbox(values[bbox_index])
            bbox_index += 1
            if box is None:
                return None
            if token in ANCHOR_TOKENS:
                by_owner[(row_index, column_index)] = box
    if bbox_index != len(values) or set(by_owner) != set(topology.positions_by_owner):
        return None
    return by_owner


def response_owner(response: JsonObject, topology: OtslTopology) -> Position | None:
    """Return the single logical cell spanned by one matched response."""
    values = [
        response.get("start_row_offset_idx"),
        response.get("end_row_offset_idx"),
        response.get("start_col_offset_idx"),
        response.get("end_col_offset_idx"),
    ]
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        return None
    start_row, end_row, start_column, end_column = cast(list[int], values)
    if not (
        0 <= start_row < end_row <= topology.rows
        and 0 <= start_column < end_column <= topology.columns
    ):
        return None
    owners = {
        topology.owner_by_position[(row, column)]
        for row in range(start_row, end_row)
        for column in range(start_column, end_column)
    }
    return next(iter(owners)) if len(owners) == 1 else None
