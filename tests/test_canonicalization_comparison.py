"""Focused tests for independent canonical-candidate semantic comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.comparison import (
    SEMANTIC_JSONL_PATHS,
    compare_completed_candidates,
)
from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_inventory,
    write_json,
    write_jsonl,
)


def _replace_id(value: Any, old_id: str, new_id: str) -> Any:
    if isinstance(value, str):
        return value.replace(old_id, new_id)
    if isinstance(value, list):
        return [_replace_id(item, old_id, new_id) for item in value]
    if isinstance(value, dict):
        return {key: _replace_id(item, old_id, new_id) for key, item in value.items()}
    return value


def _candidate(tmp_path: Path, candidate_id: str) -> Path:
    root = tmp_path / candidate_id
    records_by_path = {
        path: (
            [{"id": f"{candidate_id}/block/source/000001", "canonical_text": "same"}]
            if path == "canonical/blocks.jsonl"
            else []
        )
        for path in SEMANTIC_JSONL_PATHS
    }
    record_files = []
    for relative, records in records_by_path.items():
        path = root / relative
        write_jsonl(path, records)
        record_files.append(
            {
                "record_type": relative,
                "path": relative,
                "sha256": sha256_file(path),
                "record_count": len(records),
            }
        )
    identity = {
        "extraction_id": candidate_id,
        "identity_sha256": candidate_id.removeprefix("exv1-"),
        "source_release": {"version": "same"},
        "project_code": {
            "git_commit": candidate_id[-40:],
            "git_dirty": candidate_id.endswith("b"),
            "owned_code_bundle_sha256": candidate_id.removeprefix("exv1-"),
        },
    }
    write_json(root / "records" / "extraction_identity.json", identity)
    write_json(
        root / "records" / "manifest.json",
        {
            "extraction_id": candidate_id,
            "identity_sha256": candidate_id.removeprefix("exv1-"),
            "ordered_document_ids": [f"{candidate_id}/document/source"],
            "record_files": record_files,
            "canonicalization_warnings": ["same"],
            "canonicalization_errors": [],
        },
    )
    write_json(
        root / "records" / "canonicalization_summary.json",
        {"candidate_id": candidate_id, "text_accounting": {"emitted": 1}},
    )
    table_root = root / "documents" / "source" / "assets" / "tables" / "table-1"
    write_json(table_root / "cells.json", [{"text": "same"}])
    write_json(table_root / "table.json", {"producer": "same"})
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "candidate_id": candidate_id,
            "release_candidate": False,
            "status": "complete_with_warnings",
            "manifest_sha256": sha256_file(root / "records" / "manifest.json"),
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "warning_count": 1,
            "error_count": 0,
        },
    )
    return root


def _reseal(root: Path) -> None:
    inventory_path = write_inventory(root)
    completion = json.loads((root / "records" / "completion_record.json").read_text())
    completion["manifest_sha256"] = sha256_file(root / "records" / "manifest.json")
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json(root / "records" / "completion_record.json", completion)


def test_comparison_accepts_only_declared_identity_differences(tmp_path: Path) -> None:
    old_id = "exv1-" + "a" * 64
    new_id = "exv1-" + "b" * 64
    old = _candidate(tmp_path, old_id)
    new = _candidate(tmp_path, new_id)
    report_path = tmp_path / "comparison.json"

    report = compare_completed_candidates(old, new, report_path=report_path)

    assert report.status == "equivalent"
    assert report.mismatches == ()
    assert json.loads(report_path.read_text())["status"] == "equivalent"
    assert {item.path for item in report.compared_paths} >= set(SEMANTIC_JSONL_PATHS)


def test_comparison_reports_exact_ordered_record_path(tmp_path: Path) -> None:
    old = _candidate(tmp_path, "exv1-" + "a" * 64)
    new = _candidate(tmp_path, "exv1-" + "b" * 64)
    block_path = new / "canonical" / "blocks.jsonl"
    block = json.loads(block_path.read_text())
    block["canonical_text"] = "changed"
    write_json(block_path, block)
    _reseal(new)

    report = compare_completed_candidates(old, new)

    assert report.status == "mismatch"
    assert "/canonical/blocks.jsonl/0/canonical_text" in {
        mismatch.path for mismatch in report.mismatches
    }


def test_comparison_reports_clean_asset_bytes_separately(tmp_path: Path) -> None:
    old = _candidate(tmp_path, "exv1-" + "a" * 64)
    new = _candidate(tmp_path, "exv1-" + "b" * 64)
    clean_path = new / "documents" / "source" / "assets" / "tables" / "table-1" / "cells.json"
    write_json(clean_path, [{"text": "changed"}])
    _reseal(new)

    report = compare_completed_candidates(old, new)

    assert report.status == "mismatch"
    assert any(
        mismatch.path.endswith("/assets/tables/table-1/cells.json")
        and mismatch.kind == "byte_content"
        for mismatch in report.mismatches
    )


def test_comparison_stops_on_failed_candidate_verification(tmp_path: Path) -> None:
    old = _candidate(tmp_path, "exv1-" + "a" * 64)
    new = _candidate(tmp_path, "exv1-" + "b" * 64)
    (new / "canonical" / "blocks.jsonl").write_text("corrupt")

    report = compare_completed_candidates(old, new)

    assert report.status == "mismatch"
    assert report.mismatches[0].path == "/verification/candidate"
