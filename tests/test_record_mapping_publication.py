"""Failure-safe publication tests for document-scoped candidates."""

from __future__ import annotations

from pathlib import Path

import pytest

from er_commons.document_records.record_mapping import MappingContractError
from er_commons.document_records.record_mapping.publication import (
    CandidateWorkspace,
    publish_workspace,
    reserve_workspace,
    sha256_file,
    verify_completed_candidate,
    write_inventory,
    write_json,
)

CANDIDATE_ID = "exv1-" + "a" * 64


def _complete_workspace(task_root: Path) -> tuple[Path, CandidateWorkspace]:
    workspace = reserve_workspace(task_root, CANDIDATE_ID, "token")
    write_json(workspace.staging_root / "canonical" / "documents.jsonl", {"id": "fixture"})
    inventory_path = write_inventory(workspace.staging_root)
    write_json(
        workspace.staging_root / "records" / "completion_record.json",
        {
            "candidate_id": CANDIDATE_ID,
            "release_candidate": False,
            "artifact_inventory_sha256": sha256_file(inventory_path),
        },
    )
    return workspace.staging_root, workspace


def test_completed_candidate_publishes_and_reuses_by_checksum(tmp_path: Path) -> None:
    _staging, workspace = _complete_workspace(tmp_path)
    completion = publish_workspace(workspace)

    assert completion == tmp_path / CANDIDATE_ID / "records" / "completion_record.json"
    assert verify_completed_candidate(tmp_path / CANDIDATE_ID, CANDIDATE_ID) == completion


def test_publication_never_clobbers_existing_candidate(tmp_path: Path) -> None:
    _staging, workspace = _complete_workspace(tmp_path)
    workspace.final_root.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="already exists"):
        publish_workspace(workspace)


def test_reuse_rejects_uninventoried_or_changed_bytes(tmp_path: Path) -> None:
    _staging, workspace = _complete_workspace(tmp_path)
    publish_workspace(workspace)
    root = tmp_path / CANDIDATE_ID
    (root / "canonical" / "documents.jsonl").write_text("changed")

    with pytest.raises(MappingContractError, match="checksum differs"):
        verify_completed_candidate(root, CANDIDATE_ID)
