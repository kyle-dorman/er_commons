"""Typed table handoff records and primitive JSON field validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.document_records.record_mapping.errors import MappingContractError

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
        """Return the exclusive row end, defaulting unspanned cells to one row."""
        return self.end_row_offset_idx or self.row_index + 1

    @property
    def column_end(self) -> int:
        """Return the exclusive column end, defaulting unspanned cells to one column."""
        return self.end_column_offset_idx or self.column_index + 1

    def span_fields(self) -> JsonObject:
        """Return persisted exclusive offsets and redundant review spans."""
        return {
            "end_row_offset_idx": self.row_end,
            "end_column_offset_idx": self.column_end,
            "row_span": self.row_end - self.row_index,
            "column_span": self.column_end - self.column_index,
        }


@dataclass(frozen=True)
class TableCleanupEvidence:
    """Exact producer-owned row and column cleanup applied to one table."""

    removed_footer_row_indices: tuple[int, ...]
    removed_filename_row_indices: tuple[int, ...]
    retained_column_indices: tuple[int, ...]
    effective_column_count: int

    def as_json(self) -> JsonObject:
        """Return the producer-compatible JSON representation."""
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
    region_id: str | None
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


def read_json_object(path: Path) -> JsonObject:
    """Read one table artifact JSON object with contextual errors."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MappingContractError(f"expected JSON object: {path}")
    return payload


def read_jsonl_objects(path: Path) -> list[JsonObject]:
    """Read ordered table artifact JSON objects with line context."""
    records: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise MappingContractError(
                f"invalid JSONL artifact {path}:{line_number}: {error.msg}"
            ) from error
        if not isinstance(payload, dict):
            raise MappingContractError(f"expected JSON object in artifact {path}:{line_number}")
        records.append(payload)
    return records


def parse_shape(value: Any, *, field: str, table_id: str) -> tuple[int, int]:
    """Parse one non-negative two-dimensional table shape."""
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in value)
    ):
        raise MappingContractError(f"invalid {field} for {table_id}")
    rows, columns = value
    if rows < 0 or columns < 0:
        raise MappingContractError(f"negative {field} for {table_id}")
    return rows, columns


def parse_bbox(value: Any, *, owner: str) -> BoundingBox:
    """Parse one four-coordinate PDF bounding box."""
    if (
        not isinstance(value, list)
        or len(value) != 4
        or not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    ):
        raise MappingContractError(f"invalid bounding box for {owner}")
    return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def parse_int_list(value: Any, *, field: str, table_id: str) -> list[int]:
    """Parse one integer-only cleanup index list."""
    if not isinstance(value, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise MappingContractError(f"invalid {field} for {table_id}")
    return value
