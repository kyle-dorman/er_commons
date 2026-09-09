"""Source-free tests for the explicit Task 05D acceptance boundary."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from er_commons.artifact_io import canonical_json_sha256, json_bytes
from er_commons.response_inventory.acceptance import (
    _acceptance_record,
    publish_task05d_acceptance,
    validate_task05d_candidate,
)
from er_commons.response_inventory.contract import (
    SCHEMA_VERSION,
    build_record_id,
    semantic_bundle_digest,
    task05d_completion_counts,
)
from er_commons.response_inventory.source_structure import SOURCE_RESPONSE_HEADING_ABSENT

type JsonObject = dict[str, Any]


def test_acceptance_names_unchanged_candidate_and_only_task05e() -> None:
    record = _acceptance_record(
        Path("pipelines/project/working/05d/revisionv1-abc"),
        {
            "activity_id": "activityv1-a",
            "completion_id": "completionv1-c",
            "status": "complete",
        },
        {"inventory_id": "fileinventoryv1-i"},
        {"semantic_digest": "d" * 64, "diagnostic_counts": {}},
        accepted_by="reviewer",
        accepted_at="2026-09-08T12:00:00Z",
    )

    assert record["working_revision"].endswith("revisionv1-abc")
    assert record["downstream_consumers"] == ["05E"]
    assert record["completion_status"] == "complete"
    assert record["accepted_warning_counts"] == {}
    assert record["acceptance_id"].startswith("acceptancev1-")


def test_public_validation_is_read_only_and_returns_identity_summary(tmp_path: Path) -> None:
    artifact_root, candidate = _candidate(tmp_path)
    before = _tree_snapshot(artifact_root)

    result = validate_task05d_candidate(candidate, artifact_root)

    assert result == {
        "schema_version": "er_commons.task05d.candidate_validation.v1",
        "status": "valid",
        "candidate_root": candidate.resolve().as_posix(),
        "working_revision": candidate.relative_to(artifact_root).as_posix(),
        "activity_id": _read(candidate / "inventory/source_records.jsonl")["activity_id"],
        "completion_id": _read(candidate / "records/stage_completion.json")["completion_id"],
        "completion_status": "complete",
        "inventory_id": _read(candidate / "records/managed_file_inventory.json")["inventory_id"],
        "semantic_digest": _read(candidate / "diagnostics/build_summary.json")["semantic_digest"],
        "diagnostic_counts": {},
        "managed_file_count": 4,
    }
    assert _tree_snapshot(artifact_root) == before
    assert not candidate.with_name(f"{candidate.name}.acceptance.json").exists()


def test_publish_calls_validation_and_is_no_clobber(tmp_path: Path) -> None:
    artifact_root, candidate = _candidate(tmp_path)

    first = publish_task05d_acceptance(
        candidate,
        artifact_root,
        accepted_by="reviewer",
        accepted_at="2026-09-09T12:00:00Z",
    )
    second = publish_task05d_acceptance(
        candidate,
        artifact_root,
        accepted_by="reviewer",
        accepted_at="2026-09-09T12:00:00Z",
    )

    assert second == first
    with pytest.raises(FileExistsError, match="refusing to overwrite changed file"):
        publish_task05d_acceptance(
            candidate,
            artifact_root,
            accepted_by="another-reviewer",
            accepted_at="2026-09-09T12:00:00Z",
        )


@pytest.mark.parametrize(
    ("relative_path", "mutate", "expected_error"),
    [
        (
            "records/stage_completion.json",
            lambda value: value.update(status="failed"),
            "terminal Task 05D candidate",
        ),
        (
            "diagnostics/build_summary.json",
            lambda value: value.update(semantic_digest="0" * 64),
            "semantic digest differs",
        ),
        (
            "diagnostics/build_summary.json",
            lambda value: value.update(allowed_terminal_warning_codes=[]),
            "warning policy differs",
        ),
        (
            "diagnostics/structural_accounting.json",
            lambda value: value.update(report_digest="0" * 64),
            "structural-accounting digest differs",
        ),
        (
            "diagnostics/qualification.json",
            lambda value: value.update(review_population_digest="0" * 64),
            "review-population digest differs",
        ),
        (
            "records/managed_file_inventory.json",
            lambda value: value["files"][0].update(byte_size=999_999),
            "managed file size differs",
        ),
    ],
)
def test_public_validation_rejects_mutated_candidate_components(
    tmp_path: Path,
    relative_path: str,
    mutate: Callable[[JsonObject], object],
    expected_error: str,
) -> None:
    artifact_root, candidate = _candidate(tmp_path)
    _mutate_json(candidate / relative_path, mutate)

    with pytest.raises(ValueError, match=expected_error):
        validate_task05d_candidate(candidate, artifact_root)


def test_public_validation_localizes_nonaccepted_review_pages(tmp_path: Path) -> None:
    artifact_root, candidate = _candidate(tmp_path)

    def reopen_pages(value: JsonObject) -> None:
        value["pages"][0]["visual_disposition"] = None
        value["pages"][1]["visual_disposition"] = {"status": "requires_followup"}
        value["review_complete"] = False
        value["unresolved_review_pages"] = [10, 20]

    _mutate_json(candidate / "diagnostics/qualification.json", reopen_pages)

    with pytest.raises(
        ValueError,
        match=r"missing_or_nonaccepted_pages=\[10, 20\].*reported_unresolved_pages=\[10, 20\]",
    ):
        validate_task05d_candidate(candidate, artifact_root)


def test_public_validation_rejects_unmanaged_file(tmp_path: Path) -> None:
    artifact_root, candidate = _candidate(tmp_path)
    (candidate / "unexpected.txt").write_text("unmanaged", encoding="utf-8")

    with pytest.raises(ValueError, match="does not close the exact file set"):
        validate_task05d_candidate(candidate, artifact_root)


def test_public_validation_rejects_candidate_outside_artifact_root(tmp_path: Path) -> None:
    artifact_root, _candidate_path = _candidate(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    with pytest.raises(ValueError, match="missing or escapes"):
        validate_task05d_candidate(outside, artifact_root)


def _candidate(tmp_path: Path) -> tuple[Path, Path]:
    artifact_root = tmp_path / "artifacts"
    candidate = artifact_root / "pipelines/project/working/05d/revisionv1-test"
    activity: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05d",
        "source_id": "source",
        "page_ranges": [[1, 744]],
        "config_sha256": "1" * 64,
        "schema_sha256": "2" * 64,
        "code_sha256": "3" * 64,
        "tool_versions": {"test": "1"},
        "input_refs": [],
    }
    activity["activity_id"] = build_record_id(activity)
    records = [activity]
    records_bytes = json_bytes(activity)
    counts = task05d_completion_counts(activity, records)
    population = [
        {"physical_page": 10, "page_id": "pagev1-10", "reasons": ["control"]},
        {"physical_page": 20, "page_id": "pagev1-20", "reasons": ["control"]},
    ]
    qualification = {
        "review_population": population,
        "review_population_digest": canonical_json_sha256(population),
        "review_complete": True,
        "unresolved_review_pages": [],
        "pages": [
            {"physical_page": page, "visual_disposition": {"status": "accepted"}}
            for page in (10, 20)
        ],
    }
    structural_payload = {
        "schema_version": "er_commons.response_inventory.structural_accounting.v2",
        "diagnostic_instances": [],
    }
    structural = {
        **structural_payload,
        "report_digest": canonical_json_sha256(structural_payload),
    }
    summary = {
        "activity_id": activity["activity_id"],
        "semantic_digest": semantic_bundle_digest(records),
        "allowed_terminal_warning_codes": [SOURCE_RESPONSE_HEADING_ABSENT],
        "diagnostic_counts": {},
        "structural_accounting_digest": structural["report_digest"],
        "review_population_digest": qualification["review_population_digest"],
    }
    payloads = {
        "inventory/source_records.jsonl": records_bytes,
        "diagnostics/build_summary.json": json_bytes(summary),
        "diagnostics/qualification.json": json_bytes(qualification),
        "diagnostics/structural_accounting.json": json_bytes(structural),
    }
    inventory: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "managed_file_inventory",
        "stage": "05d",
        "activity_id": activity["activity_id"],
        "dependencies": activity["input_refs"],
        "files": [
            {"authority": "bundle", "path": path, "sha256": None, "byte_size": len(content)}
            for path, content in sorted(payloads.items())
        ],
    }
    inventory["inventory_id"] = build_record_id(inventory)
    completion: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "stage_completion",
        "stage": "05d",
        "status": "complete",
        "activity_id": activity["activity_id"],
        "inventory_id": inventory["inventory_id"],
        "counts": counts,
        "warnings": [],
        "completed_at": "2026-09-09T12:00:00Z",
    }
    completion["completion_id"] = build_record_id(completion)
    for relative_path, content in payloads.items():
        path = candidate / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    for relative_path, value in {
        "records/managed_file_inventory.json": inventory,
        "records/stage_completion.json": completion,
    }.items():
        path = candidate / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(value))
    return artifact_root, candidate


def _mutate_json(path: Path, mutate: Callable[[JsonObject], object]) -> None:
    value = _read(path)
    mutate(value)
    path.write_bytes(json_bytes(value))


def _read(path: Path) -> JsonObject:
    if path.suffix == ".jsonl":
        value = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in test candidate: {path}")
    return cast(JsonObject, value)


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
