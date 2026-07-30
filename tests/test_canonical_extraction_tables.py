"""Focused tests for saved producer-table reconciliation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.tables import load_producer_table_bundle


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{json.dumps(record)}\n" for record in records),
        encoding="utf-8",
    )


def _producer_fixture(tmp_path: Path) -> Path:
    producer = tmp_path / "producer"
    tables = producer / "tables"
    table_id = "appendix_p_p00084_t001"
    table_dir = tables / "pages/page_00084/tables" / table_id
    raw_cells = [
        {
            "row_index": row,
            "column_index": column,
            "text": value,
            "bbox_pdf_points_bottom_left": [
                float(column),
                float(2 - row),
                float(column + 1),
                float(3 - row),
            ],
        }
        for row, values in enumerate(
            [
                ["drop", "A", "B"],
                ["drop", "1", "2"],
                ["footer", "1 of 1", ""],
            ]
        )
        for column, value in enumerate(values)
    ]
    _write_json(table_dir / "cells.json", raw_cells)
    with (table_dir / "table.csv").open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows([["A", "B"], ["1", "2"]])
    _write_json(
        table_dir / "table.json",
        {"table_id": table_id},
    )
    table_record = {
        "table_id": table_id,
        "physical_pdf_page": 84,
        "page_table_index": 1,
        "region_id": "layout_001",
        "parser": "camelot_lattice",
        "shape_raw": [3, 3],
        "shape_clean": [2, 2],
        "bbox_pdf_points_bottom_left": [0.0, 0.0, 3.0, 3.0],
        "cleanup": {
            "removed_footer_row_indices": [2],
            "removed_filename_row_indices": [],
            "retained_column_indices": [1, 2],
            "effective_column_count": 2,
        },
        "clean_csv": {
            "path": f"pages/page_00084/tables/{table_id}/table.csv",
            "sha256": "fixture",
        },
        "raw_csv": {
            "path": f"pages/page_00084/tables/{table_id}/raw.csv",
            "sha256": "fixture",
        },
        "cells": {
            "path": f"pages/page_00084/tables/{table_id}/cells.json",
            "sha256": "fixture",
        },
        "table_record": f"pages/page_00084/tables/{table_id}/table.json",
    }
    _write_jsonl(tables / "tables.jsonl", [table_record])
    _write_jsonl(
        tables / "family_assignments.jsonl",
        [{"table_id": table_id, "family_id": "appendix_p_table_family_0015"}],
    )
    _write_json(
        tables / "table_families.json",
        {
            "families": [
                {
                    "family_id": "appendix_p_table_family_0015",
                    "table_ids": [table_id],
                    "evidence": ["singleton"],
                }
            ]
        },
    )
    _write_json(
        tables / "pages/page_00084/result.json",
        {
            "parser_evidence": {
                "region_matches": [
                    {"region_id": "layout_001", "matched": True, "matched_iou": 0.99},
                    {"region_id": "layout_002", "matched": False, "matched_iou": 0.0},
                ]
            },
            "tables": [{"table_id": table_id, "region_id": "layout_001"}],
        },
    )
    _write_jsonl(
        producer / "routing/page_routes.jsonl",
        [
            {
                "physical_pdf_page": 84,
                "layout_table_observations": [
                    {
                        "raw_object_ref": "#/tables/21",
                        "provenance_index": 0,
                        "bbox_pdf_points_bottom_left": [49.0, 188.0, 561.0, 663.0],
                    },
                    {
                        "raw_object_ref": "#/tables/22",
                        "provenance_index": 0,
                        "bbox_pdf_points_bottom_left": [51.0, 83.0, 509.0, 171.0],
                    },
                ],
            }
        ],
    )
    return producer


def test_loads_clean_grid_page84_crosswalk_and_exact_family(tmp_path: Path) -> None:
    bundle = load_producer_table_bundle(_producer_fixture(tmp_path))

    assert len(bundle.tables) == 1
    table = bundle.tables[0]
    assert table.shape_clean == (2, 2)
    assert [(cell.row_index, cell.column_index, cell.text) for cell in table.cells] == [
        (0, 0, "A"),
        (0, 1, "B"),
        (1, 0, "1"),
        (1, 1, "2"),
    ]
    assert table.cells[0].bbox_pdf_points_bottom_left == (1.0, 2.0, 2.0, 3.0)
    assert table.family_id == "appendix_p_table_family_0015"
    assert table.parser == "camelot_lattice"
    assert table.shape_raw == (3, 3)
    assert table.cleanup.removed_footer_row_indices == (2,)
    assert table.cleanup.retained_column_indices == (1, 2)
    assert table.raw_csv_path.endswith("/raw.csv")
    assert table.clean_csv_sha256 == "fixture"
    assert bundle.families[0].table_ids == ("appendix_p_p00084_t001",)
    assert bundle.families[0].evidence == ("singleton",)

    assert len(bundle.region_mappings) == 2
    mapped, zero = bundle.region_mappings
    assert mapped.raw_object_ref == "#/tables/21"
    assert mapped.clean_table_ids == ("appendix_p_p00084_t001",)
    assert mapped.unmapped_reason is None
    assert zero.raw_object_ref == "#/tables/22"
    assert zero.clean_table_ids == ()
    assert zero.unmapped_reason == "no_clean_table_match"


def test_rejects_missing_raw_cell_position(tmp_path: Path) -> None:
    producer = _producer_fixture(tmp_path)
    cells_path = producer / "tables/pages/page_00084/tables/appendix_p_p00084_t001/cells.json"
    cells = json.loads(cells_path.read_text(encoding="utf-8"))
    _write_json(cells_path, cells[:-1])

    with pytest.raises(ContractError, match="raw cells do not match shape_raw"):
        load_producer_table_bundle(producer)


def test_rejects_clean_csv_text_that_differs_from_projected_cells(tmp_path: Path) -> None:
    producer = _producer_fixture(tmp_path)
    csv_path = producer / "tables/pages/page_00084/tables/appendix_p_p00084_t001/table.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows([["A", "WRONG"], ["1", "2"]])

    with pytest.raises(ContractError, match="clean CSV text differs"):
        load_producer_table_bundle(producer)


def test_rejects_family_definition_assignment_mismatch(tmp_path: Path) -> None:
    producer = _producer_fixture(tmp_path)
    _write_json(
        producer / "tables/table_families.json",
        {
            "families": [
                {
                    "family_id": "different_family",
                    "table_ids": ["appendix_p_p00084_t001"],
                    "evidence": ["singleton"],
                }
            ]
        },
    )

    with pytest.raises(ContractError, match="family assignments differ"):
        load_producer_table_bundle(producer)


def test_rejects_page_result_that_differs_from_table_jsonl(tmp_path: Path) -> None:
    producer = _producer_fixture(tmp_path)
    result_path = producer / "tables/pages/page_00084/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["tables"][0]["region_id"] = "layout_002"
    _write_json(result_path, result)

    with pytest.raises(ContractError, match="page result differs from tables.jsonl"):
        load_producer_table_bundle(producer)
