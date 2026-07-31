"""Checksum snapshots for producer and canonical-reference preservation gates."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.canonical_extraction.publication import verify_completed_candidate
from er_commons.document_extraction.producer_artifacts import verify_completed_run
from er_commons.source_freeze import sha256_file


@dataclass(frozen=True)
class ManagedFile:
    """One inventory-managed path at a verified point in time."""

    path: str
    byte_size: int
    sha256: str


@dataclass(frozen=True)
class ManagedArtifactSnapshot:
    """Terminal seals and exact managed-file state for one immutable artifact."""

    kind: Literal["producer", "task03d1_reference"]
    identity: str
    completion_sha256: str
    inventory_sha256: str
    files: tuple[ManagedFile, ...]


def _load_inventory(root: Path) -> tuple[ManagedFile, ...]:
    inventory_path = root / "records/artifact_inventory.json"
    payload: dict[str, Any] = json.loads(inventory_path.read_bytes())
    return tuple(
        ManagedFile(
            path=item["path"],
            byte_size=item["byte_size"],
            sha256=item["sha256"],
        )
        for item in payload["files"]
    )


def snapshot_verified_producer(root: Path, producer_run_id: str) -> ManagedArtifactSnapshot:
    """Verify the complete producer and capture every managed checksum."""
    completion_path = verify_completed_run(root, producer_run_id)
    inventory_path = root / "records/artifact_inventory.json"
    return ManagedArtifactSnapshot(
        kind="producer",
        identity=producer_run_id,
        completion_sha256=sha256_file(completion_path),
        inventory_sha256=sha256_file(inventory_path),
        files=_load_inventory(root),
    )


def snapshot_verified_task03d1_reference(
    root: Path,
    candidate_id: str,
) -> ManagedArtifactSnapshot:
    """Verify the accepted Task 03D.1 candidate and capture managed checksums."""
    completion_path = verify_completed_candidate(root, candidate_id)
    inventory_path = root / "records/artifact_inventory.json"
    return ManagedArtifactSnapshot(
        kind="task03d1_reference",
        identity=candidate_id,
        completion_sha256=sha256_file(completion_path),
        inventory_sha256=sha256_file(inventory_path),
        files=_load_inventory(root),
    )


def assert_artifacts_preserved(
    before: tuple[ManagedArtifactSnapshot, ...],
    after: tuple[ManagedArtifactSnapshot, ...],
) -> None:
    """Fail when any terminal seal, managed byte count, or checksum changed."""
    before_by_identity = {(item.kind, item.identity): item for item in before}
    after_by_identity = {(item.kind, item.identity): item for item in after}
    if before_by_identity.keys() != after_by_identity.keys():
        raise ValueError("preservation artifact set differs")
    for identity, earlier in before_by_identity.items():
        if after_by_identity[identity] != earlier:
            raise ValueError(f"preservation snapshot differs: {identity[0]} {identity[1]}")
