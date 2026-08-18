"""Named-invariant tests for complete clean-table reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.artifact_io import read_jsonl, write_json_atomic, write_jsonl
from er_commons.document_parsing.content_parsing.table_processing import (
    TableStageInvariantError,
    validate_table_artifacts,
)


def _valid_table_root(tmp_path: Path) -> Path:
    root = tmp_path / "documents" / "document" / "producer" / "tables"
    root.mkdir(parents=True)
    write_json_atomic(
        root / "summary.json",
        {
            "physical_pdf_pages": [1, 2],
            "page_count": 2,
            "logical_table_count": 1,
            "family_count": 1,
            "zero_table_pages": [2],
            "review_derivatives_retained": False,
        },
    )
    write_jsonl(
        root / "pages.jsonl",
        [
            {"physical_pdf_page": 1, "table_count": 1},
            {"physical_pdf_page": 2, "table_count": 0},
        ],
    )
    write_jsonl(
        root / "tables.jsonl",
        [{"table_id": "document_p00001_t001", "physical_pdf_page": 1}],
    )
    write_jsonl(
        root / "family_assignments.jsonl",
        [
            {
                "table_id": "document_p00001_t001",
                "family_id": "document_table_family_0001",
            }
        ],
    )
    write_json_atomic(
        root / "table_families.json",
        {
            "families": [
                {
                    "family_id": "document_table_family_0001",
                    "table_ids": ["document_p00001_t001"],
                }
            ]
        },
    )
    return root


def test_valid_table_artifacts_preserve_explicit_zero_table_mapping(
    tmp_path: Path,
) -> None:
    result = validate_table_artifacts(_valid_table_root(tmp_path), [1, 2])

    assert result.status == "complete_with_warnings"
    assert result.logical_table_count == 1
    assert result.zero_table_pages == [2]
    assert result.manifest == "documents/document/producer/tables/manifest.json"


@pytest.mark.parametrize(
    ("corruption", "expected_invariant"),
    [
        ("page_order", "page_records"),
        ("duplicate_table_id", "unique_table_ids"),
        ("wrong_family_pair", "assignments_cover_families"),
        ("review_derivative", "no_review_derivatives"),
    ],
)
def test_table_corruption_reports_the_failed_named_invariant(
    tmp_path: Path,
    corruption: str,
    expected_invariant: str,
) -> None:
    root = _valid_table_root(tmp_path)
    if corruption == "page_order":
        pages = read_jsonl(root / "pages.jsonl")
        write_jsonl(root / "pages.jsonl", list(reversed(pages)))
    elif corruption == "duplicate_table_id":
        tables = read_jsonl(root / "tables.jsonl")
        write_jsonl(root / "tables.jsonl", [*tables, tables[0]])
        pages = read_jsonl(root / "pages.jsonl")
        pages[0]["table_count"] = 2
        write_jsonl(root / "pages.jsonl", pages)
        summary = json.loads((root / "summary.json").read_text())
        summary["logical_table_count"] = 2
        write_json_atomic(root / "summary.json", summary)
    elif corruption == "wrong_family_pair":
        assignments = read_jsonl(root / "family_assignments.jsonl")
        assignments[0]["family_id"] = "wrong_family"
        write_jsonl(root / "family_assignments.jsonl", assignments)
    elif corruption == "review_derivative":
        summary = json.loads((root / "summary.json").read_text())
        summary["review_derivatives_retained"] = True
        write_json_atomic(root / "summary.json", summary)
    else:
        raise AssertionError(f"unhandled corruption: {corruption}")

    with pytest.raises(TableStageInvariantError) as captured:
        validate_table_artifacts(root, [1, 2])

    assert captured.value.invariant == expected_invariant
