"""Read-only semantic comparison outside production candidate construction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


def compare_candidate_files(
    baseline_root: Path,
    candidate_root: Path,
    *,
    ignored_paths: frozenset[str] = frozenset(),
    identifier_replacements: tuple[tuple[str, str], ...] = (),
) -> JsonObject:
    """Compare complete file maps without authorizing or mutating publication."""
    baseline = _file_map(baseline_root, ignored_paths, identifier_replacements)
    candidate = _file_map(candidate_root, ignored_paths, identifier_replacements)
    shared = baseline.keys() & candidate.keys()
    changed = sorted(path for path in shared if baseline[path] != candidate[path])
    return {
        "schema_version": "er_commons.candidate_comparison.v1",
        "baseline_root": baseline_root.as_posix(),
        "candidate_root": candidate_root.as_posix(),
        "ignored_paths": sorted(ignored_paths),
        "identifier_replacements": [
            {"value": value, "replacement": replacement}
            for value, replacement in identifier_replacements
        ],
        "missing_paths": sorted(baseline.keys() - candidate.keys()),
        "extra_paths": sorted(candidate.keys() - baseline.keys()),
        "changed_paths": changed,
        "equivalent": baseline.keys() == candidate.keys() and not changed,
    }


def compare_table_evidence(
    baseline_root: Path,
    candidate_root: Path,
    *,
    physical_pages: frozenset[int] | None = None,
) -> JsonObject:
    """Compare stable page, logical-table, family, and region-mapping evidence."""
    pages = _compare_records(
        baseline_root / "pages.jsonl",
        candidate_root / "pages.jsonl",
        key="physical_pdf_page",
        fields=(
            "route",
            "complex_page",
            "ruling_region_count",
            "table_count",
            "footer",
            "footer_owner_table_id",
        ),
        physical_pages=physical_pages,
    )
    tables = _compare_records(
        baseline_root / "tables.jsonl",
        candidate_root / "tables.jsonl",
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
            "clean_csv",
        ),
        physical_pages=physical_pages,
    )
    assignment_table_ids = _table_ids_on_pages(baseline_root, candidate_root, physical_pages)
    assignments = _compare_records(
        baseline_root / "family_assignments.jsonl",
        candidate_root / "family_assignments.jsonl",
        key="table_id",
        fields=("family_id", "footer_owned"),
        included_keys=assignment_table_ids,
    )
    comparisons = [pages, tables, assignments]
    return {
        "schema_version": "er_commons.table_evidence_comparison.v1",
        "comparison_scope": "requested_pages" if physical_pages is not None else "exact",
        "physical_pages": sorted(physical_pages or ()),
        "comparisons": comparisons,
        "exact_semantic_match": all(item["exact_match"] for item in comparisons),
    }


def _compare_records(
    baseline_path: Path,
    candidate_path: Path,
    *,
    key: str,
    fields: tuple[str, ...],
    physical_pages: frozenset[int] | None = None,
    included_keys: frozenset[Any] | None = None,
) -> JsonObject:
    baseline = _records(baseline_path, physical_pages)
    candidate = _records(candidate_path, physical_pages)
    before = _keyed(baseline, key)
    after = _keyed(candidate, key)
    if included_keys is not None:
        before = {
            record_key: record
            for record_key, record in before.items()
            if record_key in included_keys
        }
        after = {
            record_key: record
            for record_key, record in after.items()
            if record_key in included_keys
        }
    mismatches = [
        {
            "key": record_key,
            "field": field,
            "baseline": before[record_key].get(field),
            "candidate": after[record_key].get(field),
        }
        for record_key in sorted(before.keys() & after.keys())
        for field in fields
        if before[record_key].get(field) != after[record_key].get(field)
    ]
    missing = sorted(before.keys() - after.keys())
    extra = sorted(after.keys() - before.keys())
    return {
        "artifact": baseline_path.name,
        "key": key,
        "stable_fields": list(fields),
        "missing_keys": missing,
        "extra_keys": extra,
        "field_mismatches": mismatches,
        "exact_match": not missing and not extra and not mismatches,
    }


def _records(path: Path, pages: frozenset[int] | None) -> list[JsonObject]:
    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    if pages is None:
        return records
    return [record for record in records if record.get("physical_pdf_page") in pages]


def _keyed(records: list[JsonObject], key: str) -> dict[Any, JsonObject]:
    indexed = {record[key]: record for record in records}
    if len(indexed) != len(records):
        raise ValueError(f"records contain duplicate {key} values")
    return indexed


def _table_ids_on_pages(
    baseline_root: Path,
    candidate_root: Path,
    physical_pages: frozenset[int] | None,
) -> frozenset[Any] | None:
    """Return the union of table IDs visible in a requested-page comparison."""
    if physical_pages is None:
        return None
    return frozenset(
        record["table_id"]
        for root in (baseline_root, candidate_root)
        for record in _records(root / "tables.jsonl", physical_pages)
    )


def _file_map(
    root: Path,
    ignored: frozenset[str],
    replacements: tuple[tuple[str, str], ...],
) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): _normalize(path.read_bytes(), replacements)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in ignored
    }


def _normalize(value: bytes, replacements: tuple[tuple[str, str], ...]) -> bytes:
    normalized = value
    for identifier, replacement in replacements:
        normalized = normalized.replace(identifier.encode(), replacement.encode())
    return normalized
