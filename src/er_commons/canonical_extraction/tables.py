"""Load and reconcile saved clean-table producer artifacts.

The accepted producer stores Camelot's raw cell geometry separately from its
clean CSV view.  This module projects the raw cells through the recorded
cleanup indices so downstream canonical records receive one exact rectangular
clean grid without importing Camelot or Docling.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from er_commons.canonical_extraction.errors import ContractError

JsonObject = dict[str, Any]
BoundingBox = tuple[float, float, float, float]
TableParser = Literal[
    "camelot_stream",
    "camelot_lattice",
    "camelot_network",
    "tableformer_accurate",
]
FamilyEvidence = Literal[
    "footer_run",
    "exact_cleaned_header",
    "cross_page_continuation",
    "singleton",
]


@dataclass(frozen=True)
class CleanTableCell:
    """One cleaned logical cell with exact grid coverage and producer geometry."""

    row_index: int
    column_index: int
    text: str
    bbox_pdf_points_bottom_left: BoundingBox
    end_row_offset_idx: int | None = None
    end_column_offset_idx: int | None = None

    @property
    def row_end(self) -> int:
        """Return the exclusive row end, defaulting legacy cells to span one."""
        return self.end_row_offset_idx or self.row_index + 1

    @property
    def column_end(self) -> int:
        """Return the exclusive column end, defaulting legacy cells to span one."""
        return self.end_column_offset_idx or self.column_index + 1

    def span_fields(self) -> JsonObject:
        """Return the persisted exclusive offsets and redundant review spans."""
        return {
            "end_row_offset_idx": self.row_end,
            "end_column_offset_idx": self.column_end,
            "row_span": self.row_end - self.row_index,
            "column_span": self.column_end - self.column_index,
        }


@dataclass(frozen=True)
class GridExtent:
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
    ) -> GridExtent:
        """Parse and bounds-check learned-cell offsets."""
        values = [
            cell.get("start_row_offset_idx"),
            cell.get("end_row_offset_idx"),
            cell.get("start_col_offset_idx"),
            cell.get("end_col_offset_idx"),
        ]
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            raise ContractError(f"non-integer learned-cell offsets for {table_id}")
        start_row, end_row, start_column, end_column = (int(cast(int, value)) for value in values)
        row_count, column_count = shape
        if not (
            0 <= start_row < end_row <= row_count and 0 <= start_column < end_column <= column_count
        ):
            raise ContractError(f"learned cell is outside shape_raw for {table_id}")
        return cls(start_row, end_row, start_column, end_column)

    def positions(self) -> set[tuple[int, int]]:
        """Expand the rectangle into covered grid positions."""
        return {
            (row, column)
            for row in range(self.start_row, self.end_row)
            for column in range(self.start_column, self.end_column)
        }


def _complete_grid(shape: tuple[int, int]) -> set[tuple[int, int]]:
    """Return every position in a rectangular grid shape."""
    row_count, column_count = shape
    return {(row, column) for row in range(row_count) for column in range(column_count)}


def _rectangular_extent(positions: set[tuple[int, int]]) -> GridExtent | None:
    """Return the rectangle represented by positions, or None when fragmented."""
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
    return GridExtent(rows[0], rows[-1] + 1, columns[0], columns[-1] + 1)


@dataclass(frozen=True)
class TableCleanupEvidence:
    """Exact producer-owned row and column cleanup applied to one table."""

    removed_footer_row_indices: tuple[int, ...]
    removed_filename_row_indices: tuple[int, ...]
    retained_column_indices: tuple[int, ...]
    effective_column_count: int

    def as_json(self) -> JsonObject:
        """Return the producer-compatible JSON shape during materializer migration."""
        return {
            "removed_footer_row_indices": list(self.removed_footer_row_indices),
            "removed_filename_row_indices": list(self.removed_filename_row_indices),
            "retained_column_indices": list(self.retained_column_indices),
            "effective_column_count": self.effective_column_count,
        }


@dataclass(frozen=True)
class ProducerTable:
    """One reconciled clean table and the producer paths that support it."""

    table_id: str
    physical_pdf_page: int
    page_table_index: int
    region_id: str
    parser: TableParser
    shape_raw: tuple[int, int]
    shape_clean: tuple[int, int]
    bbox_pdf_points_bottom_left: BoundingBox
    cleanup: TableCleanupEvidence
    cells: tuple[CleanTableCell, ...]
    raw_csv_path: str
    clean_csv_path: str
    clean_csv_sha256: str
    cells_path: str
    table_record_path: str
    family_id: str


@dataclass(frozen=True)
class ProducerTableFamily:
    """One exact complete-document family definition."""

    family_id: str
    table_ids: tuple[str, ...]
    evidence: tuple[FamilyEvidence, ...]


@dataclass(frozen=True)
class RegionTableMapping:
    """One Docling layout region mapped to zero or one clean producer table."""

    physical_pdf_page: int
    region_id: str
    raw_object_ref: str
    provenance_index: int
    bbox_pdf_points_bottom_left: BoundingBox
    clean_table_ids: tuple[str, ...]
    unmapped_reason: str | None


@dataclass(frozen=True)
class ProducerTableBundle:
    """Validated table, family, and region-crosswalk inputs for one document."""

    tables: tuple[ProducerTable, ...]
    families: tuple[ProducerTableFamily, ...]
    region_mappings: tuple[RegionTableMapping, ...]


def _read_json(path: Path) -> JsonObject:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[JsonObject]:
    records: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ContractError(f"expected JSON object at {path}:{line_number}")
        records.append(payload)
    return records


def _pair(value: Any, *, field: str, table_id: str) -> tuple[int, int]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in value)
    ):
        raise ContractError(f"invalid {field} for {table_id}")
    rows, columns = value
    if rows < 0 or columns < 0:
        raise ContractError(f"negative {field} for {table_id}")
    return rows, columns


def _bbox(value: Any, *, owner: str) -> BoundingBox:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    ):
        raise ContractError(f"invalid bounding box for {owner}")
    return (
        float(value[0]),
        float(value[1]),
        float(value[2]),
        float(value[3]),
    )


def _int_list(value: Any, *, field: str, table_id: str) -> list[int]:
    if not isinstance(value, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise ContractError(f"invalid {field} for {table_id}")
    return value


def clean_table_cells(
    raw_cells: list[JsonObject],
    *,
    shape_raw: tuple[int, int],
    shape_clean: tuple[int, int],
    cleanup: JsonObject,
    table_id: str,
) -> tuple[CleanTableCell, ...]:
    """Filter rectangular or span-aware producer cells through cleanup evidence."""
    raw_rows, raw_columns = shape_raw
    removed_rows = set(
        _int_list(
            cleanup.get("removed_footer_row_indices"),
            field="removed_footer_row_indices",
            table_id=table_id,
        )
    )
    removed_rows.update(
        _int_list(
            cleanup.get("removed_filename_row_indices"),
            field="removed_filename_row_indices",
            table_id=table_id,
        )
    )
    if any(row < 0 or row >= raw_rows for row in removed_rows):
        raise ContractError(f"removed row is outside shape_raw for {table_id}")

    retained_columns = _int_list(
        cleanup.get("retained_column_indices"),
        field="retained_column_indices",
        table_id=table_id,
    )
    if (
        len(retained_columns) != len(set(retained_columns))
        or retained_columns != sorted(retained_columns)
        or any(column < 0 or column >= raw_columns for column in retained_columns)
    ):
        raise ContractError(f"invalid retained columns for {table_id}")
    if cleanup.get("effective_column_count") != len(retained_columns):
        raise ContractError(f"effective column count differs for {table_id}")

    retained_rows = [row for row in range(raw_rows) if row not in removed_rows]
    if shape_clean != (len(retained_rows), len(retained_columns)):
        raise ContractError(f"cleanup indices differ from shape_clean for {table_id}")

    if raw_cells and "start_row_offset_idx" in raw_cells[0]:
        return _clean_logical_cells(
            raw_cells,
            shape_raw=shape_raw,
            retained_rows=retained_rows,
            retained_columns=retained_columns,
            table_id=table_id,
        )

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
            raise ContractError(f"non-integer raw cell position for {table_id}")
        position = (row, column)
        if position in positions:
            raise ContractError(f"duplicate raw cell position for {table_id}: {position}")
        positions[position] = cell
    expected_raw = {(row, column) for row in range(raw_rows) for column in range(raw_columns)}
    if set(positions) != expected_raw:
        raise ContractError(f"raw cells do not match shape_raw for {table_id}")

    cleaned: list[CleanTableCell] = []
    for clean_row, raw_row in enumerate(retained_rows):
        for clean_column, raw_column in enumerate(retained_columns):
            cell = positions[(raw_row, raw_column)]
            text = cell.get("text")
            if not isinstance(text, str):
                raise ContractError(f"non-string cell text for {table_id}")
            cleaned.append(
                CleanTableCell(
                    row_index=clean_row,
                    column_index=clean_column,
                    end_row_offset_idx=clean_row + 1,
                    end_column_offset_idx=clean_column + 1,
                    text=text,
                    bbox_pdf_points_bottom_left=_bbox(
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
    """Project span-aware logical cells without inventing continuation cells."""
    raw_coverage: set[tuple[int, int]] = set()
    row_map = {raw: clean for clean, raw in enumerate(retained_rows)}
    column_map = {raw: clean for clean, raw in enumerate(retained_columns)}
    cleaned: list[CleanTableCell] = []
    clean_coverage: set[tuple[int, int]] = set()
    for cell in raw_cells:
        raw_extent = GridExtent.from_record(cell, shape=shape_raw, table_id=table_id)
        raw_positions = raw_extent.positions()
        if raw_coverage & raw_positions:
            raise ContractError(f"learned cells overlap for {table_id}")
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
            raise ContractError(f"cleanup fragments learned spans for {table_id}")
        clean_coverage |= retained_positions
        text = cell.get("text")
        if not isinstance(text, str):
            raise ContractError(f"non-string learned cell text for {table_id}")
        cleaned.append(
            CleanTableCell(
                row_index=clean_extent.start_row,
                column_index=clean_extent.start_column,
                end_row_offset_idx=clean_extent.end_row,
                end_column_offset_idx=clean_extent.end_column,
                text=text,
                bbox_pdf_points_bottom_left=_bbox(
                    cell.get("bbox_pdf_points_bottom_left"),
                    owner=f"{table_id} learned cell",
                ),
            )
        )
    if raw_coverage != _complete_grid(shape_raw):
        raise ContractError(f"learned cells do not cover shape_raw for {table_id}")
    clean_shape = (len(retained_rows), len(retained_columns))
    if clean_coverage != _complete_grid(clean_shape):
        raise ContractError(f"learned cells do not cover shape_clean for {table_id}")
    return tuple(cleaned)


def _validate_clean_csv(
    path: Path,
    *,
    cells: tuple[CleanTableCell, ...],
    shape: tuple[int, int],
    table_id: str,
) -> None:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    row_count, column_count = shape
    if len(rows) != row_count or any(len(row) != column_count for row in rows):
        raise ContractError(f"clean CSV differs from shape_clean for {table_id}")
    expected = [["" for _column in range(column_count)] for _row in range(row_count)]
    for cell in cells:
        expected[cell.row_index][cell.column_index] = cell.text
    if rows != expected:
        raise ContractError(f"clean CSV text differs from cleaned cells for {table_id}")


def _validate_continuation_family_evidence(
    family_payload: JsonObject,
    *,
    family_by_id: dict[str, ProducerTableFamily],
    assignment_by_table: dict[str, str],
) -> None:
    """Require accepted decisions to exactly explain continuation families."""
    expected_family_ids = {
        family.family_id
        for family in family_by_id.values()
        if "cross_page_continuation" in family.evidence
    }
    raw_decisions = family_payload.get("continuation_decisions", [])
    if not isinstance(raw_decisions, list) or not all(
        isinstance(decision, dict) for decision in raw_decisions
    ):
        raise ContractError("table_families.json has invalid continuation decisions")
    accepted_family_ids: set[str] = set()
    for decision in raw_decisions:
        if decision.get("status") != "accepted":
            continue
        left_table = decision.get("left_table_id")
        right_table = decision.get("right_table_id")
        inherited = decision.get("inherited_header")
        valid = (
            isinstance(left_table, str)
            and isinstance(right_table, str)
            and assignment_by_table.get(left_table) is not None
            and assignment_by_table.get(left_table) == assignment_by_table.get(right_table)
            and isinstance(inherited, dict)
            and inherited.get("origin") == "inherited"
            and inherited.get("content_status") == "unresolved_no_printed_header_projection"
            and inherited.get("source_table_id") == left_table
        )
        if not valid:
            raise ContractError("invalid accepted continuation evidence")
        assert isinstance(left_table, str)
        accepted_family_ids.add(assignment_by_table[left_table])
    if accepted_family_ids != expected_family_ids:
        raise ContractError("continuation family evidence lacks accepted decisions")


def _load_family_records(
    table_root: Path,
) -> tuple[tuple[ProducerTableFamily, ...], dict[str, str]]:
    assignments = _read_jsonl(table_root / "family_assignments.jsonl")
    family_payload = _read_json(table_root / "table_families.json")
    raw_families = family_payload.get("families")
    if not isinstance(raw_families, list) or not all(
        isinstance(record, dict) for record in raw_families
    ):
        raise ContractError("table_families.json has invalid families")

    family_by_id: dict[str, ProducerTableFamily] = {}
    for record in raw_families:
        family_id = record.get("family_id")
        table_ids = record.get("table_ids")
        evidence = record.get("evidence")
        if (
            not isinstance(family_id, str)
            or not isinstance(table_ids, list)
            or not all(isinstance(table_id, str) for table_id in table_ids)
            or not isinstance(evidence, list)
            or not all(
                item
                in {
                    "footer_run",
                    "exact_cleaned_header",
                    "cross_page_continuation",
                    "singleton",
                }
                for item in evidence
            )
        ):
            raise ContractError("invalid table family record")
        if family_id in family_by_id or len(table_ids) != len(set(table_ids)):
            raise ContractError(f"duplicate table family content: {family_id}")
        family_by_id[family_id] = ProducerTableFamily(
            family_id=family_id,
            table_ids=tuple(table_ids),
            evidence=tuple(cast(FamilyEvidence, item) for item in evidence),
        )

    assignment_by_table: dict[str, str] = {}
    assignment_pairs: set[tuple[str, str]] = set()
    for assignment in assignments:
        table_id = assignment.get("table_id")
        family_id = assignment.get("family_id")
        if not isinstance(table_id, str) or not isinstance(family_id, str):
            raise ContractError("invalid table family assignment")
        if table_id in assignment_by_table:
            raise ContractError(f"duplicate table family assignment: {table_id}")
        assignment_by_table[table_id] = family_id
        assignment_pairs.add((table_id, family_id))

    family_pairs = {
        (table_id, family.family_id)
        for family in family_by_id.values()
        for table_id in family.table_ids
    }
    if assignment_pairs != family_pairs:
        raise ContractError("family assignments differ from family definitions")
    _validate_continuation_family_evidence(
        family_payload,
        family_by_id=family_by_id,
        assignment_by_table=assignment_by_table,
    )
    return tuple(family_by_id.values()), assignment_by_table


def _load_tables(
    table_root: Path,
    assignment_by_table: dict[str, str],
) -> tuple[ProducerTable, ...]:
    records = _read_jsonl(table_root / "tables.jsonl")
    tables: list[ProducerTable] = []
    seen: set[str] = set()
    for record in records:
        table_id = record.get("table_id")
        if not isinstance(table_id, str) or table_id in seen:
            raise ContractError(f"invalid or duplicate table ID: {table_id}")
        seen.add(table_id)
        family_id = assignment_by_table.get(table_id)
        if family_id is None:
            raise ContractError(f"table lacks exact family assignment: {table_id}")

        cells_artifact = record.get("cells")
        raw_csv_artifact = record.get("raw_csv")
        clean_csv_artifact = record.get("clean_csv")
        if (
            not isinstance(cells_artifact, dict)
            or not isinstance(raw_csv_artifact, dict)
            or not isinstance(clean_csv_artifact, dict)
        ):
            raise ContractError(f"table artifacts are missing for {table_id}")
        cells_relative = cells_artifact.get("path")
        raw_csv_relative = raw_csv_artifact.get("path")
        csv_relative = clean_csv_artifact.get("path")
        clean_csv_sha256 = clean_csv_artifact.get("sha256")
        table_record_relative = record.get("table_record")
        if (
            not isinstance(cells_relative, str)
            or not isinstance(raw_csv_relative, str)
            or not isinstance(csv_relative, str)
            or not isinstance(clean_csv_sha256, str)
            or not isinstance(table_record_relative, str)
        ):
            raise ContractError(f"table artifact path is invalid for {table_id}")

        raw_cells_payload = json.loads((table_root / cells_relative).read_text(encoding="utf-8"))
        if not isinstance(raw_cells_payload, list) or not all(
            isinstance(cell, dict) for cell in raw_cells_payload
        ):
            raise ContractError(f"cells artifact is invalid for {table_id}")
        shape_raw = _pair(record.get("shape_raw"), field="shape_raw", table_id=table_id)
        shape_clean = _pair(record.get("shape_clean"), field="shape_clean", table_id=table_id)
        cleanup = record.get("cleanup")
        if not isinstance(cleanup, dict):
            raise ContractError(f"cleanup record is invalid for {table_id}")
        effective_column_count = cleanup.get("effective_column_count")
        if not isinstance(effective_column_count, int) or isinstance(
            effective_column_count,
            bool,
        ):
            raise ContractError(f"effective column count is invalid for {table_id}")
        cleanup_evidence = TableCleanupEvidence(
            removed_footer_row_indices=tuple(
                _int_list(
                    cleanup.get("removed_footer_row_indices"),
                    field="removed_footer_row_indices",
                    table_id=table_id,
                )
            ),
            removed_filename_row_indices=tuple(
                _int_list(
                    cleanup.get("removed_filename_row_indices"),
                    field="removed_filename_row_indices",
                    table_id=table_id,
                )
            ),
            retained_column_indices=tuple(
                _int_list(
                    cleanup.get("retained_column_indices"),
                    field="retained_column_indices",
                    table_id=table_id,
                )
            ),
            effective_column_count=effective_column_count,
        )
        cells = clean_table_cells(
            raw_cells_payload,
            shape_raw=shape_raw,
            shape_clean=shape_clean,
            cleanup=cleanup_evidence.as_json(),
            table_id=table_id,
        )
        _validate_clean_csv(
            table_root / csv_relative,
            cells=cells,
            shape=shape_clean,
            table_id=table_id,
        )

        page = record.get("physical_pdf_page")
        page_table_index = record.get("page_table_index")
        region_id = record.get("region_id")
        parser = record.get("parser")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or not isinstance(page_table_index, int)
            or isinstance(page_table_index, bool)
            or not isinstance(region_id, str)
            or parser
            not in {
                "camelot_stream",
                "camelot_lattice",
                "camelot_network",
                "tableformer_accurate",
            }
        ):
            raise ContractError(f"table placement is invalid for {table_id}")
        tables.append(
            ProducerTable(
                table_id=table_id,
                physical_pdf_page=page,
                page_table_index=page_table_index,
                region_id=region_id,
                parser=cast(TableParser, parser),
                shape_raw=shape_raw,
                shape_clean=shape_clean,
                bbox_pdf_points_bottom_left=_bbox(
                    record.get("bbox_pdf_points_bottom_left"),
                    owner=table_id,
                ),
                cleanup=cleanup_evidence,
                cells=cells,
                raw_csv_path=raw_csv_relative,
                clean_csv_path=csv_relative,
                clean_csv_sha256=clean_csv_sha256,
                cells_path=cells_relative,
                table_record_path=table_record_relative,
                family_id=family_id,
            )
        )

    if set(assignment_by_table) != seen:
        raise ContractError("family assignments do not exactly cover clean tables")
    return tuple(tables)


def _load_region_mappings(
    producer_root: Path,
    tables: tuple[ProducerTable, ...],
) -> tuple[RegionTableMapping, ...]:
    table_root = producer_root / "tables"
    routes = _read_jsonl(producer_root / "routing" / "page_routes.jsonl")
    tables_by_page_region: dict[tuple[int, str], list[str]] = {}
    for table in tables:
        tables_by_page_region.setdefault((table.physical_pdf_page, table.region_id), []).append(
            table.table_id
        )

    mappings: list[RegionTableMapping] = []
    seen_clean_tables: set[str] = set()
    for route in routes:
        page = route.get("physical_pdf_page")
        observations = route.get("layout_table_observations")
        if (
            not isinstance(page, int)
            or isinstance(page, bool)
            or not isinstance(observations, list)
            or not all(isinstance(item, dict) for item in observations)
        ):
            raise ContractError("invalid routing table observations")
        if not observations:
            continue

        result = _read_json(table_root / f"pages/page_{page:05d}/result.json")
        evidence = result.get("parser_evidence")
        result_tables = result.get("tables")
        if not isinstance(evidence, dict) or not isinstance(result_tables, list):
            raise ContractError(f"invalid page table result for page {page}")
        result_pairs = {
            (item.get("table_id"), item.get("region_id"))
            for item in result_tables
            if isinstance(item, dict)
        }
        if len(result_pairs) != len(result_tables) or not all(
            isinstance(table_id, str) and isinstance(region_id, str)
            for table_id, region_id in result_pairs
        ):
            raise ContractError(f"invalid result table references for page {page}")
        expected_pairs = {
            (table.table_id, table.region_id) for table in tables if table.physical_pdf_page == page
        }
        if result_pairs != expected_pairs:
            raise ContractError(f"page result differs from tables.jsonl for page {page}")
        region_matches = evidence.get("region_matches")
        if not isinstance(region_matches, list) or not all(
            isinstance(item, dict) for item in region_matches
        ):
            raise ContractError(f"invalid region matches for page {page}")
        match_by_region = {item.get("region_id"): item.get("matched") for item in region_matches}

        for region_index, observation in enumerate(observations, start=1):
            region_id = f"layout_{region_index:03d}"
            raw_object_ref = observation.get("raw_object_ref")
            provenance_index = observation.get("provenance_index")
            if (
                not isinstance(raw_object_ref, str)
                or not isinstance(provenance_index, int)
                or isinstance(provenance_index, bool)
            ):
                raise ContractError(f"invalid raw table observation on page {page}")
            clean_table_ids = tuple(tables_by_page_region.get((page, region_id), []))
            if len(clean_table_ids) > 1:
                raise ContractError(
                    f"region maps to multiple clean tables: page {page} {region_id}"
                )
            matched = match_by_region.get(region_id)
            if not isinstance(matched, bool) or matched != bool(clean_table_ids):
                raise ContractError(
                    f"region match differs from clean tables: page {page} {region_id}"
                )
            seen_clean_tables.update(clean_table_ids)
            mappings.append(
                RegionTableMapping(
                    physical_pdf_page=page,
                    region_id=region_id,
                    raw_object_ref=raw_object_ref,
                    provenance_index=provenance_index,
                    bbox_pdf_points_bottom_left=_bbox(
                        observation.get("bbox_pdf_points_bottom_left"),
                        owner=f"page {page} {region_id}",
                    ),
                    clean_table_ids=clean_table_ids,
                    unmapped_reason=None if clean_table_ids else "no_clean_table_match",
                )
            )

    expected_tables = {table.table_id for table in tables}
    if seen_clean_tables != expected_tables:
        raise ContractError("region mappings do not exactly cover clean tables")
    return tuple(mappings)


def load_producer_table_bundle(producer_root: Path) -> ProducerTableBundle:
    """Load the verified producer's complete table handoff from plain JSON."""
    table_root = producer_root / "tables"
    families, assignments = _load_family_records(table_root)
    tables = _load_tables(table_root, assignments)
    mappings = _load_region_mappings(producer_root, tables)
    return ProducerTableBundle(
        tables=tables,
        families=families,
        region_mappings=mappings,
    )
