"""Exact comparison of stable table-pipeline outputs.

Runtime fields and artifact paths intentionally do not participate. The
comparison asks whether changing the environment boundary changed any logical
table decision or cleaned table content.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSON Lines artifact into records."""
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def stable_table_records(path: Path) -> list[dict[str, Any]]:
    """Expose cleaned CSV content hashes without comparing artifact paths."""
    records = read_jsonl(path)
    return [
        {
            **record,
            "clean_csv_sha256": record["clean_csv"]["sha256"],
        }
        for record in records
    ]


def keyed(records: list[dict[str, Any]], key: str) -> dict[Any, dict[str, Any]]:
    """Index records by a required unique field."""
    indexed = {record[key]: record for record in records}
    if len(indexed) != len(records):
        raise ValueError(f"records contain duplicate {key} values")
    return indexed


def compare_records(
    *,
    artifact: str,
    baseline_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
    key: str,
    fields: tuple[str, ...],
) -> dict[str, Any]:
    """Compare selected fields for records that must have identical keys."""
    baseline = keyed(baseline_records, key)
    candidate = keyed(candidate_records, key)
    baseline_keys = set(baseline)
    candidate_keys = set(candidate)
    mismatches = []
    for record_key in sorted(baseline_keys & candidate_keys):
        for field in fields:
            before = baseline[record_key].get(field)
            after = candidate[record_key].get(field)
            if before != after:
                mismatches.append(
                    {
                        "key": record_key,
                        "field": field,
                        "baseline": before,
                        "candidate": after,
                    }
                )
    missing = sorted(baseline_keys - candidate_keys)
    extra = sorted(candidate_keys - baseline_keys)
    return {
        "artifact": artifact,
        "key": key,
        "stable_fields": list(fields),
        "baseline_record_count": len(baseline),
        "candidate_record_count": len(candidate),
        "missing_keys": missing,
        "extra_keys": extra,
        "field_mismatches": mismatches,
        "exact_match": not missing and not extra and not mismatches,
    }


def compare_pipeline_outputs(
    baseline_root: Path,
    candidate_root: Path,
    *,
    baseline_pages_only: bool = False,
) -> dict[str, Any]:
    """Compare stable contracts exactly or only on baseline physical pages."""
    baseline_pages = read_jsonl(baseline_root / "pages.jsonl")
    candidate_pages = read_jsonl(candidate_root / "pages.jsonl")
    baseline_tables = stable_table_records(baseline_root / "tables.jsonl")
    candidate_tables = stable_table_records(candidate_root / "tables.jsonl")
    baseline_assignments = read_jsonl(baseline_root / "family_assignments.jsonl")
    candidate_assignments = read_jsonl(candidate_root / "family_assignments.jsonl")
    assignment_fields: tuple[str, ...] = ("family_id", "footer_owned")
    if baseline_pages_only:
        review_pages = {record["physical_pdf_page"] for record in baseline_pages}
        review_tables = {record["table_id"] for record in baseline_tables}
        candidate_pages = [
            record for record in candidate_pages if record["physical_pdf_page"] in review_pages
        ]
        candidate_tables = [
            record for record in candidate_tables if record["physical_pdf_page"] in review_pages
        ]
        baseline_assignments = [
            record for record in baseline_assignments if record["table_id"] in review_tables
        ]
        candidate_assignments = [
            record for record in candidate_assignments if record["table_id"] in review_tables
        ]
        assignment_fields = ("footer_owned",)

    comparisons = [
        compare_records(
            artifact="pages.jsonl",
            baseline_records=baseline_pages,
            candidate_records=candidate_pages,
            key="physical_pdf_page",
            fields=(
                "route",
                "complex_page",
                "ruling_region_count",
                "table_count",
                "footer",
                "footer_owner_table_id",
            ),
        ),
        compare_records(
            artifact="tables.jsonl",
            baseline_records=baseline_tables,
            candidate_records=candidate_tables,
            key="table_id",
            fields=(
                "physical_pdf_page",
                "page_table_index",
                "route",
                "parser",
                "parser_order",
                "region_id",
                "bbox_pdf_points_bottom_left",
                "shape_raw",
                "shape_clean",
                "columns_pdf_points",
                "cleanup",
                "header_matrix",
                "clean_csv_sha256",
            ),
        ),
        compare_records(
            artifact="family_assignments.jsonl",
            baseline_records=baseline_assignments,
            candidate_records=candidate_assignments,
            key="table_id",
            fields=assignment_fields,
        ),
    ]
    exact = all(item["exact_match"] for item in comparisons)
    return {
        "schema_version": "1.0.0",
        "baseline_root": baseline_root.as_posix(),
        "candidate_root": candidate_root.as_posix(),
        "comparison_scope": "baseline_pages" if baseline_pages_only else "exact",
        "comparisons": comparisons,
        "stable_field_mismatch_count": sum(len(item["field_mismatches"]) for item in comparisons),
        "missing_key_count": sum(len(item["missing_keys"]) for item in comparisons),
        "extra_key_count": sum(len(item["extra_keys"]) for item in comparisons),
        "exact_semantic_match": exact,
    }
