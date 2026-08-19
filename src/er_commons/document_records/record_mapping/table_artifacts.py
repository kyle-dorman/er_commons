"""Load and reconcile individual clean-table producer artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.table_cleanup import (
    clean_table_cells,
    validate_clean_csv,
)
from er_commons.document_records.record_mapping.table_records import (
    ProducerTable,
    TableCleanupEvidence,
    TableParser,
    parse_bbox,
    parse_int_list,
    parse_shape,
    read_jsonl_objects,
)

_TABLE_PARSERS = {
    "camelot_stream",
    "camelot_lattice",
    "camelot_network",
    "tableformer_accurate",
}


def _artifact_paths(record: dict[str, object], table_id: str) -> tuple[str, str, str, str, str]:
    """Validate and return cells, raw CSV, clean CSV, hash, and record paths."""
    artifacts = (record.get("cells"), record.get("raw_csv"), record.get("clean_csv"))
    if not all(isinstance(artifact, dict) for artifact in artifacts):
        raise MappingContractError(f"table artifacts are missing for {table_id}")
    cells_artifact, raw_csv_artifact, clean_csv_artifact = artifacts
    assert isinstance(cells_artifact, dict)
    assert isinstance(raw_csv_artifact, dict)
    assert isinstance(clean_csv_artifact, dict)
    values = (
        cells_artifact.get("path"),
        raw_csv_artifact.get("path"),
        clean_csv_artifact.get("path"),
        clean_csv_artifact.get("sha256"),
        record.get("table_record"),
    )
    if not all(isinstance(value, str) for value in values):
        raise MappingContractError(f"table artifact path is invalid for {table_id}")
    return cast(tuple[str, str, str, str, str], values)


def _cleanup_evidence(record: dict[str, object], table_id: str) -> TableCleanupEvidence:
    """Parse the exact producer cleanup record for one table."""
    cleanup = record.get("cleanup")
    if not isinstance(cleanup, dict):
        raise MappingContractError(f"cleanup record is invalid for {table_id}")
    effective_count = cleanup.get("effective_column_count")
    if not isinstance(effective_count, int) or isinstance(effective_count, bool):
        raise MappingContractError(f"effective column count is invalid for {table_id}")

    def indices(field: str) -> tuple[int, ...]:
        return tuple(parse_int_list(cleanup.get(field), field=field, table_id=table_id))

    return TableCleanupEvidence(
        removed_footer_row_indices=indices("removed_footer_row_indices"),
        removed_filename_row_indices=indices("removed_filename_row_indices"),
        retained_column_indices=indices("retained_column_indices"),
        effective_column_count=effective_count,
    )


def _placement(
    record: dict[str, object], table_id: str
) -> tuple[int, int, str | None, TableParser]:
    """Validate one table's page, route, region, and parser placement."""
    page = record.get("physical_pdf_page")
    page_table_index = record.get("page_table_index")
    route = record.get("route")
    region_id = record.get("region_id")
    parser = record.get("parser")
    valid_region = (route == "layout_regions" and isinstance(region_id, str)) or (
        route == "full_page_numeric" and region_id is None
    )
    if (
        not isinstance(page, int)
        or isinstance(page, bool)
        or not isinstance(page_table_index, int)
        or isinstance(page_table_index, bool)
        or not valid_region
        or parser not in _TABLE_PARSERS
    ):
        raise MappingContractError(f"table placement is invalid for {table_id}")
    return page, page_table_index, cast(str | None, region_id), cast(TableParser, parser)


def load_producer_tables(
    table_root: Path,
    assignment_by_table: dict[str, str],
) -> tuple[ProducerTable, ...]:
    """Load table artifacts and require exact family and clean-grid agreement."""
    records = read_jsonl_objects(table_root / "tables.jsonl")
    tables: list[ProducerTable] = []
    seen: set[str] = set()
    for record in records:
        table_id = record.get("table_id")
        if not isinstance(table_id, str) or table_id in seen:
            raise MappingContractError(f"invalid or duplicate table ID: {table_id}")
        seen.add(table_id)
        family_id = assignment_by_table.get(table_id)
        if family_id is None:
            raise MappingContractError(f"table lacks exact family assignment: {table_id}")
        (
            cells_relative,
            raw_csv_relative,
            csv_relative,
            clean_csv_sha256,
            table_record_relative,
        ) = _artifact_paths(record, table_id)
        raw_cells_payload = json.loads((table_root / cells_relative).read_text(encoding="utf-8"))
        if not isinstance(raw_cells_payload, list) or not all(
            isinstance(cell, dict) for cell in raw_cells_payload
        ):
            raise MappingContractError(f"cells artifact is invalid for {table_id}")
        shape_raw = parse_shape(record.get("shape_raw"), field="shape_raw", table_id=table_id)
        shape_clean = parse_shape(record.get("shape_clean"), field="shape_clean", table_id=table_id)
        cleanup_evidence = _cleanup_evidence(record, table_id)
        cells = clean_table_cells(
            raw_cells_payload,
            shape_raw=shape_raw,
            shape_clean=shape_clean,
            cleanup=cleanup_evidence.as_json(),
            table_id=table_id,
        )
        validate_clean_csv(
            table_root / csv_relative,
            cells=cells,
            shape=shape_clean,
            table_id=table_id,
        )
        page, page_table_index, region_id, parser = _placement(record, table_id)
        tables.append(
            ProducerTable(
                table_id=table_id,
                physical_pdf_page=page,
                page_table_index=page_table_index,
                region_id=region_id,
                parser=parser,
                shape_raw=shape_raw,
                shape_clean=shape_clean,
                bbox_pdf_points_bottom_left=parse_bbox(
                    record.get("bbox_pdf_points_bottom_left"), owner=table_id
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
        raise MappingContractError("family assignments do not exactly cover clean tables")
    return tuple(tables)
