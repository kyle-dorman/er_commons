"""Publication-boundary tests for Task 03E.4 semantic candidates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.document_structure.publication import (
    deep_audit_completed_document_structure,
    preserve_failed_attempt,
    verify_completed_document_structure,
)
from er_commons.document_records.document_structure.support import SUPPORT_PATHS
from er_commons.document_records.record_mapping.publication import (
    sha256_file,
    write_inventory,
    write_json,
)


def _write_completed_candidate(
    root: Path,
    candidate_id: str,
    *,
    disposition: str = "accepted_with_known_limitations",
    status: str = "complete_with_warnings",
    semantic_payload: bytes | None = None,
) -> None:
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
        {
            "extraction_id": candidate_id,
            "source_semantic_disposition": disposition,
            "support_files": support_files,
        },
    )
    if semantic_payload is not None:
        payload_path = root / "canonical" / "blocks.jsonl"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_bytes(semantic_payload)
    inventory_path = write_inventory(root)
    write_json(
        root / "records" / "completion_record.json",
        {
            "schema_version": "er_commons.canonical_extraction_completion.v2",
            "extraction_id": candidate_id,
            "status": status,
            "source_semantic_disposition": disposition,
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "support_files_verified": True,
            "undeclared_difference_count": 0,
        },
    )


def test_completed_candidate_verifier_fails_closed_on_tamper(tmp_path: Path) -> None:
    """Reuse is allowed only while every inventory and support checksum is exact."""
    candidate_id = "exv1-" + "a" * 64
    _write_completed_candidate(tmp_path, candidate_id)

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()

    support_path = tmp_path / SUPPORT_PATHS["cross_producer_bridge"]
    support_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.stage == "candidate reuse verification"
    assert (
        error.value.invariant
        == "semantic candidate inventory metadata matches the managed file set"
    )
    assert error.value.subject.endswith("records/artifact_inventory.json")


def test_fast_reuse_skips_semantic_hash_and_deep_audit_detects_same_size_tamper(
    tmp_path: Path,
) -> None:
    """Normal restart trusts immutable large bytes; explicit audit reauthenticates them."""
    candidate_id = "exv1-" + "e" * 64
    original = b'{"block":"one"}\n'
    changed = b'{"block":"two"}\n'
    assert len(original) == len(changed)
    _write_completed_candidate(tmp_path, candidate_id, semantic_payload=original)
    payload_path = tmp_path / "canonical" / "blocks.jsonl"
    payload_path.write_bytes(changed)

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()
    with pytest.raises(DocumentStructureInvariantError) as error:
        deep_audit_completed_document_structure(tmp_path, candidate_id)
    assert error.value.stage == "candidate deep audit"
    assert error.value.subject == payload_path.as_posix()


@pytest.mark.parametrize("status", ["complete", "complete_with_warnings"])
def test_completed_candidate_verifier_supports_strict_control(tmp_path: Path, status: str) -> None:
    """Strict hierarchy inputs may complete with or without inherited warnings."""
    candidate_id = "exv1-" + "c" * 64
    _write_completed_candidate(
        tmp_path,
        candidate_id,
        disposition="strict_quality_gate",
        status=status,
    )

    assert verify_completed_document_structure(tmp_path, candidate_id).is_file()


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

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)
    assert error.value.invariant == "semantic completion seals its inventory"
    assert error.value.expected == sha256_file(tmp_path / "records" / "artifact_inventory.json")
    assert error.value.observed == "0" * 64


def test_malformed_terminal_record_has_structured_evidence(tmp_path: Path) -> None:
    """A malformed reuse record names the failed invariant and exact subject."""
    candidate_id = "exv1-" + "d" * 64
    _write_completed_candidate(tmp_path, candidate_id)
    manifest_path = tmp_path / "records" / "manifest.json"
    manifest_path.write_text("{", encoding="utf-8")

    with pytest.raises(DocumentStructureInvariantError) as error:
        verify_completed_document_structure(tmp_path, candidate_id)

    assert error.value.invariant == "candidate record contains valid JSON"
    assert error.value.expected == "valid JSON"
    assert error.value.subject == manifest_path.as_posix()
