"""Failure-safe publication tests for document-scoped candidates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_records.record_mapping import MappingContractError, publication
from er_commons.document_records.record_mapping.publication import (
    CandidateWorkspace,
    publish_workspace,
    reserve_workspace,
    retain_workspace_without_completion,
    sha256_file,
    validate_inventory_metadata,
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


def _reseal_inventory(root: Path, inventory: dict[str, object]) -> None:
    inventory_path = root / "records" / "artifact_inventory.json"
    write_json(inventory_path, inventory)
    completion_path = root / "records" / "completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json(completion_path, completion)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("duplicate", "duplicate candidate inventory path"),
        ("unsafe", "unsafe candidate inventory path"),
        ("digest", "inventory digest is invalid"),
        ("file_count", "inventory file count differs"),
        ("byte_total", "inventory byte total differs"),
        ("root_shape", "inventory shape differs"),
        ("entry_shape", "inventory entry shape differs"),
    ],
)
def test_reuse_rejects_noncanonical_inventory_metadata(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    root, _workspace = _complete_workspace(tmp_path)
    inventory_path = root / "records" / "artifact_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    if mutation == "duplicate":
        inventory["files"].append(dict(inventory["files"][0]))
        inventory["file_count"] += 1
        inventory["byte_size"] += inventory["files"][0]["byte_size"]
    elif mutation == "unsafe":
        inventory["files"][0]["path"] = "canonical/../documents.jsonl"
    elif mutation == "digest":
        inventory["files"][0]["sha256"] = "not-a-sha256"
    elif mutation == "file_count":
        inventory["file_count"] += 1
    elif mutation == "root_shape":
        inventory["unexpected"] = True
    elif mutation == "entry_shape":
        inventory["files"][0]["unexpected"] = True
    else:
        inventory["byte_size"] += 1
    _reseal_inventory(root, inventory)

    with pytest.raises(MappingContractError, match=message):
        verify_completed_candidate(root, CANDIDATE_ID)


def test_reuse_rehashes_large_inventory_files(tmp_path: Path) -> None:
    root, _workspace = _complete_workspace(tmp_path)
    large = root / "canonical" / "large.bin"
    with large.open("wb") as stream:
        stream.truncate(64 * 1024 * 1024 + 1)
    inventory_path = write_inventory(root)
    completion = json.loads((root / "records/completion_record.json").read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json(root / "records/completion_record.json", completion)
    with large.open("r+b") as stream:
        stream.write(b"changed")

    with pytest.raises(MappingContractError, match="checksum differs"):
        verify_completed_candidate(root, CANDIDATE_ID)


def test_inventory_metadata_validation_is_typed_and_does_not_hash_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _workspace = _complete_workspace(tmp_path)
    inventory = json.loads((root / "records/artifact_inventory.json").read_text())
    monkeypatch.setattr(
        publication,
        "sha256_file",
        lambda _path: (_ for _ in ()).throw(AssertionError("metadata validation must not hash")),
    )

    managed = validate_inventory_metadata(root, inventory)

    assert [item.relative_path for item in managed] == ["canonical/documents.jsonl"]
    assert managed[0].path == root / "canonical/documents.jsonl"
    assert managed[0].byte_size == managed[0].path.stat().st_size


def test_inventory_metadata_rejects_symlinked_candidate_nodes(tmp_path: Path) -> None:
    root, _workspace = _complete_workspace(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    (external / "hidden.json").write_text("{}\n")
    (root / "linked").symlink_to(external, target_is_directory=True)
    inventory = json.loads((root / "records/artifact_inventory.json").read_text())

    with pytest.raises(MappingContractError, match="unsafe candidate inventory symlink"):
        validate_inventory_metadata(root, inventory)


def test_publish_requires_completion_but_remains_terminal_schema_neutral(tmp_path: Path) -> None:
    workspace = reserve_workspace(tmp_path, "semantic-candidate", "token")
    write_json(workspace.staging_root / "payload.json", {"semantic": True})

    with pytest.raises(MappingContractError, match="completion is required"):
        publish_workspace(workspace)

    write_json(
        workspace.staging_root / "records/completion_record.json",
        {"owner": "document_structure", "status": "complete"},
    )
    completion = publish_workspace(workspace)
    assert completion.is_file()


def test_publish_flushes_tree_and_both_rename_parents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _root, workspace = _complete_workspace(tmp_path)
    events: list[tuple[str, Path]] = []
    monkeypatch.setattr(
        publication,
        "_fsync_candidate_tree",
        lambda path: events.append(("tree", path)),
    )
    monkeypatch.setattr(
        publication,
        "_fsync_file",
        lambda path: events.append(("file", path)),
    )
    monkeypatch.setattr(
        publication,
        "_fsync_directory",
        lambda path: events.append(("directory", path)),
    )

    publish_workspace(workspace)

    assert events == [
        ("tree", workspace.staging_root),
        ("file", workspace.staging_root / "records/completion_record.json"),
        ("directory", workspace.staging_root.parent),
        ("directory", workspace.final_root.parent),
    ]


def test_failure_retention_removes_completion_and_flushes_rename_parents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _root, workspace = _complete_workspace(tmp_path)
    events: list[tuple[str, Path]] = []
    monkeypatch.setattr(
        publication,
        "_fsync_candidate_tree",
        lambda path: events.append(("tree", path)),
    )
    monkeypatch.setattr(
        publication,
        "_fsync_directory",
        lambda path: events.append(("directory", path)),
    )
    attempts_root = tmp_path / "attempts"

    retained = retain_workspace_without_completion(workspace, attempts_root)

    assert retained == attempts_root / workspace.staging_root.name
    assert retained is not None
    assert retained.is_dir()
    assert not (retained / "records/completion_record.json").exists()
    assert events == [
        ("directory", workspace.staging_root / "records"),
        ("tree", workspace.staging_root),
        ("directory", tmp_path),
        ("directory", attempts_root),
        ("directory", workspace.staging_root.parent),
        ("directory", attempts_root),
    ]
