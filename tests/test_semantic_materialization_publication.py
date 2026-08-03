"""Publication-boundary tests for Task 03E.4 semantic candidates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_inventory,
    write_json,
)
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.publication import (
    preserve_failed_attempt,
    verify_completed_semantic_candidate,
)
from er_commons.semantic_materialization.review import _candidate_id
from er_commons.semantic_materialization.support import SUPPORT_PATHS


def _write_completed_candidate(root: Path, candidate_id: str) -> None:
    """Write the smallest checksum-valid semantic candidate fixture."""
    support_files = []
    for role, relative in SUPPORT_PATHS.items():
        write_json(root / relative, {"role": role})
        support_files.append(
            {
                "role": role,
                "path": relative,
                "sha256": sha256_file(root / relative),
                "schema_version": "2.0.0",
            }
        )
    write_json(
        root / "records" / "manifest.json",
        {"extraction_id": candidate_id, "support_files": support_files},
    )
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonical_extraction_completion.v2",
            "extraction_id": candidate_id,
            "status": "complete_with_warnings",
            "source_semantic_disposition": "accepted_with_known_limitations",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "support_files_verified": True,
            "undeclared_difference_count": 0,
        },
    )


def test_completed_candidate_verifier_fails_closed_on_tamper(tmp_path: Path) -> None:
    """Reuse is allowed only while every inventory and support checksum is exact."""
    candidate_id = "exv1-" + "a" * 64
    _write_completed_candidate(tmp_path, candidate_id)

    assert verify_completed_semantic_candidate(tmp_path, candidate_id).is_file()

    support_path = tmp_path / SUPPORT_PATHS["cross_producer_bridge"]
    support_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SemanticMaterializationInvariantError) as error:
        verify_completed_semantic_candidate(tmp_path, candidate_id)
    assert error.value.stage == "candidate reuse verification"
    assert error.value.invariant == "semantic candidate inventory matches the managed file set"
    assert error.value.subject.endswith("records/artifact_inventory.json")


def test_failed_attempt_is_retained_without_completion(tmp_path: Path) -> None:
    """A simulated failed build remains inspectable but cannot look complete."""
    task_root = tmp_path / "task"
    staging_root = task_root / ".tmp" / "simulated-failure"
    write_json(staging_root / "records" / "partial.json", {"stage": "application"})
    write_json(staging_root / "records" / "completion_record.json", {"status": "complete"})

    failed = preserve_failed_attempt(task_root, staging_root)

    assert failed == task_root / "attempts" / "simulated-failure"
    assert (failed / "records" / "partial.json").is_file()
    assert not (failed / "records" / "completion_record.json").exists()
    assert not staging_root.exists()


def test_completion_inventory_digest_is_rechecked(tmp_path: Path) -> None:
    """A completion record cannot point at a substituted inventory."""
    candidate_id = "exv1-" + "b" * 64
    _write_completed_candidate(tmp_path, candidate_id)
    completion_path = tmp_path / "records" / "completion_record.json"
    completion = json.loads(completion_path.read_bytes())
    completion["artifact_inventory_sha256"] = "0" * 64
    write_json(completion_path, completion)

    with pytest.raises(SemanticMaterializationInvariantError) as error:
        verify_completed_semantic_candidate(tmp_path, candidate_id)
    assert error.value.invariant == "semantic completion seals its inventory"
    assert error.value.expected == sha256_file(tmp_path / "records" / "artifact_inventory.json")
    assert error.value.observed == "0" * 64


def test_malformed_terminal_record_has_structured_evidence(tmp_path: Path) -> None:
    """A malformed reuse record names the failed invariant and exact subject."""
    candidate_id = "exv1-" + "d" * 64
    _write_completed_candidate(tmp_path, candidate_id)
    manifest_path = tmp_path / "records" / "manifest.json"
    manifest_path.write_text("{", encoding="utf-8")

    with pytest.raises(SemanticMaterializationInvariantError) as error:
        verify_completed_semantic_candidate(tmp_path, candidate_id)

    assert error.value.invariant == "candidate record contains valid JSON"
    assert error.value.expected == "valid JSON"
    assert error.value.subject == manifest_path.as_posix()


def test_review_candidate_id_comes_from_identity_not_staging_name(tmp_path: Path) -> None:
    """Disposable review provenance cannot inherit a temporary workspace suffix."""
    candidate_id = "exv1-" + "c" * 64
    staging = tmp_path / f"{candidate_id}.temporary-suffix"
    write_json(
        staging / "records" / "extraction_identity.json",
        {"extraction_id": candidate_id},
    )

    assert _candidate_id(staging) == candidate_id
