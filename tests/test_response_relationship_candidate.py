"""Source-free closure tests for the Task 05E terminal candidate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes
from er_commons.response_inventory.relationship_candidate import (
    _completion_record,
    _inventory_record,
    _load_quality_report,
    _validate_review_pass,
    publish_task05e_acceptance,
)

type JsonObject = dict[str, Any]

_PAYLOAD_PATHS = (
    "diagnostics/individual_diagnostics.jsonl",
    "diagnostics/review_census.json",
    "graph/review_edges.jsonl",
    "records/activity.json",
    "review_views/review_views.jsonl",
)


def _closed_review(root: Path) -> JsonObject:
    payloads = {path: f"{path}\n".encode() for path in _PAYLOAD_PATHS}
    census = {
        "status": "bounded_review_complete_review_required",
        "gate2_authorized": True,
        "source_pdf_accessed": False,
        "counts": {
            "intra_volume_mentions": 2,
            "resolved_mentions": 1,
            "terminal_unresolved_mentions": 1,
            "membership_claims": 1,
            "resolved_memberships": 0,
            "terminal_unresolved_memberships": 1,
        },
        "mention_failure_categories": {
            "ordinary_prose": 251,
            "response_section_heading": 8,
            "reviewed_source_label_typo_unresolved": 1,
            "running_header": 44,
            "self_mention": 7,
        },
        "membership_failure_categories": {"exact_comment_target_absent": 1},
        "direct_pair_failure_labels": [
            "Comment SA-CHSRA-29",
            "Comment SA-Caltrans-48",
            "Response SA-Caltrans-48a",
        ],
    }
    payloads["diagnostics/review_census.json"] = json_bytes(census)
    for relative, content in payloads.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    receipt: JsonObject = {
        "schema_version": "er_commons.task05e.bounded_review.v1",
        "status": "bounded_review_complete_review_required",
        "activity_id": "activityv1-" + "a" * 64,
        "semantic_digest": "b" * 64,
        "completion_written": False,
        "source_pdf_accessed": False,
        "files": [
            {
                "path": path,
                "byte_size": len(payloads[path]),
                "sha256": hashlib.sha256(payloads[path]).hexdigest(),
            }
            for path in _PAYLOAD_PATHS
        ],
    }
    receipt_path = root / "records/review_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(json_bytes(receipt))
    return receipt


def test_review_pass_requires_exact_closed_bytes(tmp_path: Path) -> None:
    receipt = _closed_review(tmp_path)

    assert _validate_review_pass(tmp_path) == receipt

    (tmp_path / "graph/review_edges.jsonl").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="review payload differs"):
        _validate_review_pass(tmp_path)


def test_quality_report_is_bound_to_reviewed_repository_files(tmp_path: Path) -> None:
    receipt = _closed_review(tmp_path / "review")
    reviewed = tmp_path / "resolver.py"
    reviewed.write_text("VALUE = 1\n", encoding="utf-8")
    report: JsonObject = {
        "schema_version": "er_commons.task05e.code_quality_review.v1",
        "status": "pass",
        "activity_id": receipt["activity_id"],
        "semantic_digest": receipt["semantic_digest"],
        "reviewed_at": "2026-09-09T12:00:00Z",
        "material_findings": [],
        "criteria": [
            {"name": name, "status": "pass", "finding": "bounded evidence"}
            for name in ("readability", "editability", "debugging", "operations", "testing")
        ],
        "reviewed_files": [
            {
                "path": "resolver.py",
                "sha256": hashlib.sha256(reviewed.read_bytes()).hexdigest(),
            }
        ],
    }
    report_path = tmp_path / "quality.json"
    report_path.write_bytes(json_bytes(report))

    assert _load_quality_report(report_path, tmp_path, receipt) == report

    reviewed.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after quality review"):
        _load_quality_report(report_path, tmp_path, receipt)


def test_terminal_records_are_deterministic_and_preserve_dependencies() -> None:
    activity: JsonObject = {
        "activity_id": "activityv1-" + "a" * 64,
        "input_refs": [
            {
                "role": "task05d_completion",
                "identity": "completionv1-" + "b" * 64,
                "authority": "artifact_root",
                "path": "working/05d/records/stage_completion.json",
            }
        ],
    }
    census: JsonObject = {
        "counts": {"semantic_edges": 2},
        "edge_counts_by_relation": {"comment_response": 2},
    }
    quality: JsonObject = {"reviewed_at": "2026-09-09T12:00:00Z"}
    payloads = {"graph/review_edges.jsonl": b"{}\n"}

    inventory = _inventory_record(activity, payloads)
    completion = _completion_record(activity, inventory, census, quality)

    assert inventory["dependencies"] == activity["input_refs"]
    assert completion["counts"] == {"semantic_edges": 2, "comment_response_edges": 2}
    assert completion == _completion_record(activity, inventory, census, quality)


def test_acceptance_is_adjacent_and_bound_to_validated_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / ("revisionv1-" + "a" * 64)
    candidate.mkdir()
    published: dict[str, Any] = {}
    validation = {
        "working_revision": "working/05e/" + candidate.name,
        "activity_id": "activityv1-" + "b" * 64,
        "completion_id": "completionv1-" + "c" * 64,
        "completion_status": "complete_with_warnings",
        "inventory_id": "fileinventoryv1-" + "d" * 64,
        "semantic_digest": "e" * 64,
        "quality_gate": "pass",
    }
    monkeypatch.setattr(
        "er_commons.response_inventory.relationship_candidate.validate_task05e_candidate",
        lambda *_args: validation,
    )

    def capture(path: Path, payload: bytes) -> None:
        published["path"] = path
        published["payload"] = payload

    monkeypatch.setattr(
        "er_commons.response_inventory.relationship_candidate.publish_bytes_no_clobber",
        capture,
    )

    result = publish_task05e_acceptance(
        candidate,
        tmp_path,
        tmp_path,
        accepted_by="project_owner",
        accepted_at="2026-09-09T20:00:00Z",
    )

    assert result["status"] == "accepted"
    assert result["accepted_downstream_consumer"] == "task05f"
    assert result["acceptance_id"].startswith("acceptancev1-")
    assert published["path"] == candidate.parent / f"{candidate.name}.acceptance.json"


def test_acceptance_rejects_invalid_reviewer_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    monkeypatch.setattr(
        "er_commons.response_inventory.relationship_candidate.validate_task05e_candidate",
        lambda *_args: {
            "working_revision": "working/05e/candidate",
            "activity_id": "activity",
            "completion_id": "completion",
            "completion_status": "complete",
            "inventory_id": "inventory",
            "semantic_digest": "a" * 64,
            "quality_gate": "pass",
        },
    )

    with pytest.raises(ValueError, match="nonempty reviewer"):
        publish_task05e_acceptance(
            candidate,
            tmp_path,
            tmp_path,
            accepted_by=" ",
            accepted_at="2026-09-09T20:00:00Z",
        )
    with pytest.raises(ValueError, match="ISO 8601"):
        publish_task05e_acceptance(
            candidate,
            tmp_path,
            tmp_path,
            accepted_by="project_owner",
            accepted_at="not-a-date",
        )
    with pytest.raises(ValueError, match="timezone"):
        publish_task05e_acceptance(
            candidate,
            tmp_path,
            tmp_path,
            accepted_by="project_owner",
            accepted_at="2026-09-09T20:00:00",
        )
