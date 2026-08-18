"""Build and validate canonical cell geometry from accepted learned structure."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import median

from er_commons.document_parsing.table_reconstruction.learned_table_geometry import (
    normalized_characters,
    project_crop_bbox_to_pdf,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import (
    AbstentionReason,
    BoundingBox,
    JsonObject,
    Position,
)
from er_commons.document_parsing.table_reconstruction.otsl import OtslTopology


@dataclass(frozen=True)
class LogicalCellBuild:
    """Materialized logical cells and the text accounting they produced."""

    cells: list[JsonObject]
    normalized_text: str
    explicit_empty_count: int
    unmatched_structure_count: int


@dataclass(frozen=True)
class GridBoundaries:
    """Monotonic PDF-space boundaries for one rectangular review projection."""

    columns: list[float]
    rows: list[float]


def _cell_source(token: str, text: str) -> str:
    if token == "ecel" and not text:
        return "otsl_empty"
    return "matched_native_text" if text else "otsl_unmatched"


def build_logical_cells(
    *,
    topology: OtslTopology,
    boxes: dict[Position, BoundingBox],
    text_by_owner: dict[Position, str],
    crop_size: tuple[int, int],
    region_bbox: list[float],
    render_scale: float,
) -> LogicalCellBuild | None:
    """Build one persisted record per logical OTSL cell."""
    width, height = crop_size
    cells: list[JsonObject] = []
    normalized_text = ""
    explicit_empty_count = 0
    unmatched_structure_count = 0
    for ordinal, owner in enumerate(sorted(topology.positions_by_owner)):
        start_row, start_column = owner
        positions = topology.positions_by_owner[owner]
        end_row = max(position[0] for position in positions) + 1
        end_column = max(position[1] for position in positions) + 1
        otsl_token = topology.grid[start_row][start_column]
        text = text_by_owner.get(owner, "")
        raw_left, raw_top, raw_right, raw_bottom = boxes[owner]
        local_bbox = (
            max(0.0, raw_left),
            max(0.0, raw_top),
            min(float(width), raw_right),
            min(float(height), raw_bottom),
        )
        left, top, right, bottom = local_bbox
        if not (left < right and top < bottom):
            return None
        source = _cell_source(otsl_token, text)
        explicit_empty_count += source == "otsl_empty"
        unmatched_structure_count += source == "otsl_unmatched"
        normalized_text += normalized_characters(text)
        cells.append(
            {
                "logical_cell_index": ordinal,
                "start_row_offset_idx": start_row,
                "end_row_offset_idx": end_row,
                "start_col_offset_idx": start_column,
                "end_col_offset_idx": end_column,
                "row_span": end_row - start_row,
                "column_span": end_column - start_column,
                "text": text,
                "bbox_pdf_points_bottom_left": project_crop_bbox_to_pdf(
                    local_bbox,
                    crop_bbox=region_bbox,
                    scale=render_scale,
                ),
                "column_header": otsl_token == "ched",
                "row_header": otsl_token == "rhed",
                "row_section": otsl_token == "srow",
                "cell_source": source,
            }
        )
    return LogicalCellBuild(
        cells,
        normalized_text,
        explicit_empty_count,
        unmatched_structure_count,
    )


def record_text_coverage(
    *,
    native_tokens: list[JsonObject],
    ignored_token_ids: set[int],
    cell_build: LogicalCellBuild,
    measurements: JsonObject,
) -> tuple[float, int]:
    """Record multiset character coverage over table-scope native tokens."""
    evaluated_tokens = [
        token for token in native_tokens if token.get("id") not in ignored_token_ids
    ]
    native_text = "".join(
        normalized_characters(str(token.get("text", ""))) for token in evaluated_tokens
    )
    native_counts = Counter(native_text)
    predicted_counts = Counter(cell_build.normalized_text)
    matched_characters = sum(
        min(count, predicted_counts[character]) for character, count in native_counts.items()
    )
    coverage = matched_characters / len(native_text) if native_text else 0.0
    duplicated_characters = sum(
        max(0, count - native_counts[character]) for character, count in predicted_counts.items()
    )
    measurements.update(
        {
            "native_character_count": len(native_text),
            "evaluated_native_token_count": len(evaluated_tokens),
            "predicted_character_count": len(cell_build.normalized_text),
            "matched_native_character_count": matched_characters,
            "native_text_coverage": coverage,
            "duplicated_native_character_count": duplicated_characters,
            "logical_cell_count": len(cell_build.cells),
            "otsl_empty_cell_count": cell_build.explicit_empty_count,
            "otsl_unmatched_cell_count": cell_build.unmatched_structure_count,
        }
    )
    return coverage, duplicated_characters


def derive_grid_boundaries(
    logical_cells: list[JsonObject],
    *,
    row_count: int,
    column_count: int,
) -> GridBoundaries | AbstentionReason:
    """Derive complete monotonic row and column boundaries from logical cells."""
    column_values: dict[int, list[float]] = {index: [] for index in range(column_count + 1)}
    row_values: dict[int, list[float]] = {index: [] for index in range(row_count + 1)}
    for cell in logical_cells:
        bbox = cell["bbox_pdf_points_bottom_left"]
        column_values[int(cell["start_col_offset_idx"])].append(float(bbox[0]))
        column_values[int(cell["end_col_offset_idx"])].append(float(bbox[2]))
        row_values[int(cell["start_row_offset_idx"])].append(float(bbox[3]))
        row_values[int(cell["end_row_offset_idx"])].append(float(bbox[1]))
    if any(not values for values in column_values.values()) or any(
        not values for values in row_values.values()
    ):
        return "invalid_grid_coverage"
    columns = [median(column_values[index]) for index in range(column_count + 1)]
    rows = [median(row_values[index]) for index in range(row_count + 1)]
    columns_reverse = any(right <= left for left, right in zip(columns, columns[1:], strict=False))
    rows_reverse = any(lower >= upper for upper, lower in zip(rows, rows[1:], strict=False))
    if columns_reverse or rows_reverse:
        return "non_monotonic_grid_geometry"
    return GridBoundaries(columns, rows)


def rectangular_rows(
    cells: list[JsonObject],
    *,
    row_count: int,
    column_count: int,
) -> list[list[str]]:
    """Project logical anchors into a rectangular review matrix."""
    rows = [["" for _column in range(column_count)] for _row in range(row_count)]
    for cell in cells:
        rows[int(cell["start_row_offset_idx"])][int(cell["start_col_offset_idx"])] = str(
            cell["text"]
        )
    return rows
