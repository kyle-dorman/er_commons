"""Conservative cross-page continuation decisions over immutable page tables."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]
MAX_LEFT_BOTTOM_FRACTION = 0.20
MAX_CORROBORATED_LEFT_BOTTOM_FRACTION = 0.22
MIN_RIGHT_TOP_FRACTION = 0.80
MAX_HORIZONTAL_DELTA = 0.03
MAX_COLUMN_BOUNDARY_DELTA = 0.02


@dataclass(frozen=True)
class TableEdge:
    """One page-edge table with normalized geometry used for comparison."""

    record: JsonObject
    table_id: str
    bottom_fraction: float
    top_fraction: float
    horizontal_span: tuple[float, float]
    columns: list[tuple[float, float]]

    @classmethod
    def from_record(cls, table: JsonObject) -> TableEdge:
        """Read and normalize one persisted table record."""
        page_width, page_height = (float(value) for value in table["page_size_pdf_points"])
        left, bottom, right, top = (float(value) for value in table["bbox_pdf_points_bottom_left"])
        columns = [
            (float(column["left"]) / page_width, float(column["right"]) / page_width)
            for column in table["columns_pdf_points"]
        ]
        return cls(
            record=table,
            table_id=str(table["table_id"]),
            bottom_fraction=bottom / page_height,
            top_fraction=top / page_height,
            horizontal_span=(left / page_width, right / page_width),
            columns=columns,
        )


@dataclass(frozen=True)
class ColumnTypeCompatibility:
    """Compatibility result for target-retained raw columns."""

    compatible: bool
    comparisons: list[JsonObject]


@dataclass(frozen=True)
class ContinuationSignals:
    """All independent signals used to decide one adjacent-page boundary."""

    left_bottom_fraction: float
    right_top_fraction: float
    horizontal_span_delta: float
    left_raw_column_count: int
    right_raw_column_count: int
    maximum_column_boundary_delta: float | None
    column_types: ColumnTypeCompatibility
    exact_nonempty_header_match: bool
    left_body_row_count: int
    right_body_row_count: int

    def measurements(self) -> JsonObject:
        """Serialize diagnostic signals without embedding policy conclusions."""
        return {
            "left_bottom_fraction": self.left_bottom_fraction,
            "right_top_fraction": self.right_top_fraction,
            "horizontal_span_delta": self.horizontal_span_delta,
            "left_raw_column_count": self.left_raw_column_count,
            "right_raw_column_count": self.right_raw_column_count,
            "maximum_column_boundary_delta": self.maximum_column_boundary_delta,
            "compatible_retained_column_types": self.column_types.compatible,
            "retained_column_type_comparisons": self.column_types.comparisons,
            "exact_nonempty_header_match": self.exact_nonempty_header_match,
            "left_body_row_count": self.left_body_row_count,
            "right_body_row_count": self.right_body_row_count,
        }


def body_row_count(table: JsonObject) -> int:
    """Return cleaned rows not already identified as printed header rows."""
    shape = table.get("shape_clean")
    matrix = table.get("header_matrix")
    if (
        not isinstance(shape, list)
        or len(shape) != 2
        or not isinstance(shape[0], int)
        or not isinstance(matrix, list)
    ):
        return 0
    return max(0, int(shape[0]) - len(matrix))


def exact_nonempty_headers_match(left: JsonObject, right: JsonObject) -> bool:
    """Return whether two records carry the same non-empty printed header."""
    left_header = left.get("header_matrix")
    return bool(left_header and left_header == right.get("header_matrix"))


def edge_geometry_compatible(
    left: TableEdge,
    right: TableEdge,
    *,
    maximum_left_bottom_fraction: float = MAX_LEFT_BOTTOM_FRACTION,
) -> bool:
    """Require page-edge placement, span, and raw-column geometry to agree."""
    span_delta = max(
        abs(left_value - right_value)
        for left_value, right_value in zip(
            left.horizontal_span,
            right.horizontal_span,
            strict=True,
        )
    )
    column_delta = _maximum_column_delta(left, right)
    return bool(
        left.bottom_fraction <= maximum_left_bottom_fraction
        and right.top_fraction >= MIN_RIGHT_TOP_FRACTION
        and span_delta <= MAX_HORIZONTAL_DELTA
        and column_delta is not None
        and column_delta <= MAX_COLUMN_BOUNDARY_DELTA
    )


def _tables_on_page(tables: list[JsonObject], page: int) -> list[JsonObject]:
    """Return tables in their visual page order."""
    return sorted(
        (table for table in tables if int(table["physical_pdf_page"]) == page),
        key=lambda table: int(table["page_table_index"]),
    )


def _inherited_header_evidence(left: TableEdge, right: TableEdge) -> JsonObject:
    """Reference a source header heuristic without fabricating inherited text."""
    matrix = left.record.get("header_matrix", [])
    encoded = json.dumps(matrix, ensure_ascii=False, sort_keys=True).encode()
    source_columns = [int(value) for value in left.record["cleanup"]["retained_column_indices"]]
    target_columns = [int(value) for value in right.record["cleanup"]["retained_column_indices"]]
    return {
        "origin": "inherited",
        "content_status": "unresolved_no_printed_header_projection",
        "source_table_id": left.table_id,
        "source_leading_rows_heuristic_sha256": hashlib.sha256(encoded).hexdigest(),
        "column_basis": "raw_parser_geometry",
        "target_clean_to_source_column": target_columns,
        "unrepresented_source_columns": [
            column for column in source_columns if column not in target_columns
        ],
    }


def _dominant_types_are_compatible(left: JsonObject, right: JsonObject) -> bool:
    """Allow equal types and the documented numeric/missing mixtures."""
    left_type = left.get("dominant_type")
    right_type = right.get("dominant_type")
    left_counts = left.get("counts", {})
    right_counts = right.get("counts", {})
    if left_type == right_type:
        return True
    left_numeric = int(left_counts.get("numeric", 0)) > 0
    right_numeric = int(right_counts.get("numeric", 0)) > 0
    left_missing = int(left_counts.get("missing", 0)) > 0
    right_missing = int(right_counts.get("missing", 0)) > 0
    return (
        (left_missing and right_numeric)
        or (right_missing and left_numeric)
        or (left_numeric and right_numeric)
        or (left_missing and right_missing)
    )


def _column_type_compatibility(left: TableEdge, right: TableEdge) -> ColumnTypeCompatibility:
    """Compare source and target types for target-retained raw columns."""
    left_signatures = left.record.get("raw_column_type_signatures", [])
    right_signatures = right.record.get("raw_column_type_signatures", [])
    retained = [int(value) for value in right.record["cleanup"]["retained_column_indices"]]
    valid_shapes = (
        isinstance(left_signatures, list)
        and isinstance(right_signatures, list)
        and bool(left_signatures)
        and len(left_signatures) == len(right_signatures)
        and all(index < len(left_signatures) for index in retained)
    )
    if not valid_shapes:
        return ColumnTypeCompatibility(False, [])
    comparisons: list[JsonObject] = []
    for index in retained:
        left_signature = left_signatures[index]
        right_signature = right_signatures[index]
        compatible = _dominant_types_are_compatible(left_signature, right_signature)
        comparisons.append(
            {
                "raw_column_index": index,
                "left_dominant_type": left_signature.get("dominant_type"),
                "right_dominant_type": right_signature.get("dominant_type"),
                "compatible": compatible,
            }
        )
    return ColumnTypeCompatibility(
        compatible=bool(comparisons) and all(item["compatible"] for item in comparisons),
        comparisons=comparisons,
    )


def _maximum_column_delta(left: TableEdge, right: TableEdge) -> float | None:
    """Return the largest corresponding normalized boundary difference."""
    if len(left.columns) != len(right.columns) or not left.columns:
        return None
    return max(
        abs(left_value - right_value)
        for left_column, right_column in zip(left.columns, right.columns, strict=True)
        for left_value, right_value in zip(left_column, right_column, strict=True)
    )


def _continuation_signals(left: TableEdge, right: TableEdge) -> ContinuationSignals:
    """Measure geometry and column types without assigning a disposition."""
    span_delta = max(
        abs(left_value - right_value)
        for left_value, right_value in zip(
            left.horizontal_span,
            right.horizontal_span,
            strict=True,
        )
    )
    return ContinuationSignals(
        left_bottom_fraction=left.bottom_fraction,
        right_top_fraction=right.top_fraction,
        horizontal_span_delta=span_delta,
        left_raw_column_count=len(left.columns),
        right_raw_column_count=len(right.columns),
        maximum_column_boundary_delta=_maximum_column_delta(left, right),
        column_types=_column_type_compatibility(left, right),
        exact_nonempty_header_match=exact_nonempty_headers_match(left.record, right.record),
        left_body_row_count=body_row_count(left.record),
        right_body_row_count=body_row_count(right.record),
    )


def _ambiguity_reasons(signals: ContinuationSignals) -> list[str]:
    """Apply the conservative continuation thresholds to measured signals."""
    reasons: list[str] = []
    corroborated_bottom_gap = bool(
        signals.left_bottom_fraction <= MAX_CORROBORATED_LEFT_BOTTOM_FRACTION
        and signals.exact_nonempty_header_match
        and signals.left_body_row_count > 0
        and signals.right_body_row_count > 0
    )
    if signals.left_bottom_fraction > MAX_LEFT_BOTTOM_FRACTION and not corroborated_bottom_gap:
        reasons.append("left_table_not_at_page_bottom")
    if signals.right_top_fraction < MIN_RIGHT_TOP_FRACTION:
        reasons.append("right_table_not_at_page_top")
    if signals.horizontal_span_delta > MAX_HORIZONTAL_DELTA:
        reasons.append("horizontal_extent_mismatch")
    if (
        signals.maximum_column_boundary_delta is None
        or signals.maximum_column_boundary_delta > MAX_COLUMN_BOUNDARY_DELTA
    ):
        reasons.append("raw_column_geometry_mismatch")
    if not signals.column_types.compatible:
        reasons.append("retained_column_type_mismatch")
    return reasons


def _acceptance_reason(signals: ContinuationSignals) -> str:
    """Name the positive policy basis, including any narrow threshold waiver."""
    if signals.left_bottom_fraction > MAX_LEFT_BOTTOM_FRACTION:
        return "exact_header_corroborated_left_bottom_gap"
    return "all_continuation_signals_passed"


def _evaluate_edge_pair(
    *,
    left_page: int,
    right_page: int,
    left: TableEdge,
    right: TableEdge,
    markers: list[JsonObject],
) -> JsonObject:
    """Build one terminal decision from page markers and measured signals."""
    signals = _continuation_signals(left, right)
    if markers:
        status = "rejected"
        reasons = ["new_table_marker"]
    else:
        reasons = _ambiguity_reasons(signals)
        status = "accepted" if not reasons else "ambiguous"
    return {
        "left_page": left_page,
        "right_page": right_page,
        "left_table_id": left.table_id,
        "right_table_id": right.table_id,
        "status": status,
        "reasons": reasons or [_acceptance_reason(signals)],
        "measurements": signals.measurements(),
        "right_page_markers": markers,
        "inherited_header": (
            _inherited_header_evidence(left, right) if status == "accepted" else None
        ),
    }


def continuation_decisions(
    page_records: list[JsonObject],
    tables: list[JsonObject],
) -> list[JsonObject]:
    """Evaluate only the last/first table pair on adjacent physical pages."""
    decisions: list[JsonObject] = []
    ordered_pages = sorted(page_records, key=lambda record: int(record["physical_pdf_page"]))
    for left_page, right_page in zip(ordered_pages, ordered_pages[1:], strict=False):
        left_number = int(left_page["physical_pdf_page"])
        right_number = int(right_page["physical_pdf_page"])
        if right_number != left_number + 1:
            continue
        left_tables = _tables_on_page(tables, left_number)
        right_tables = _tables_on_page(tables, right_number)
        if not left_tables or not right_tables:
            decisions.append(
                {
                    "left_page": left_number,
                    "right_page": right_number,
                    "status": "not_evaluable_missing_table",
                    "reasons": ["missing_edge_table"],
                }
            )
            continue
        markers = list(right_page.get("boundary_markers_before_first_table", []))
        decisions.append(
            _evaluate_edge_pair(
                left_page=left_number,
                right_page=right_number,
                left=TableEdge.from_record(left_tables[-1]),
                right=TableEdge.from_record(right_tables[0]),
                markers=markers,
            )
        )
    return decisions
