"""Atomic publication and checksum-verified reuse for canonical candidates."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_records.record_mapping.errors import MappingContractError


@dataclass(frozen=True)
class CandidateWorkspace:
    """One private staging directory and its deterministic final destination."""

    staging_root: Path
    final_root: Path


def sha256_file(path: Path) -> str:
    """Return the complete SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_bytes(payload: Any) -> bytes:
    """Serialize deterministic, readable UTF-8 JSON with a terminal newline."""
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def write_json(path: Path, payload: Any) -> None:
    """Write one deterministic JSON value, creating only its parent folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stable_json_bytes(payload))


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Stream deterministic JSON records and return their count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("wb") as stream:
        for record in records:
            stream.write(stable_json_bytes(record))
            count += 1
    return count


def reserve_workspace(task_root: Path, candidate_id: str, token: str) -> CandidateWorkspace:
    """Reserve an isolated no-clobber staging tree."""
    task_root.mkdir(parents=True, exist_ok=True)
    staging_root = task_root / ".tmp" / f"{candidate_id}.{token}"
    staging_root.mkdir(parents=True, exist_ok=False)
    return CandidateWorkspace(
        staging_root=staging_root,
        final_root=task_root / candidate_id,
    )


def build_inventory(
    root: Path,
    *,
    excluded: frozenset[str] = frozenset(
        {"records/artifact_inventory.json", "records/completion_record.json"}
    ),
) -> dict[str, Any]:
    """Inventory every candidate-owned file except terminal self-references."""
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        files.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "byte_size": path.stat().st_size,
            }
        )
    return {
        "schema_version": "er_commons.candidate_artifact_inventory.v1",
        "files": files,
        "file_count": len(files),
        "byte_size": sum(item["byte_size"] for item in files),
    }


def write_inventory(root: Path) -> Path:
    """Write the non-self-referential candidate inventory."""
    path = root / "records" / "artifact_inventory.json"
    write_json(path, build_inventory(root))
    return path


def verify_completed_candidate(root: Path, candidate_id: str) -> Path:
    """Fail closed unless an existing completed candidate is byte-exact."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    if not completion_path.is_file() or not inventory_path.is_file():
        raise MappingContractError(f"candidate terminal records are missing below {root}")
    completion = json.loads(completion_path.read_text())
    inventory = json.loads(inventory_path.read_text())
    if completion.get("candidate_id") != candidate_id:
        raise MappingContractError("candidate completion identity differs")
    if completion.get("release_candidate") is not False:
        raise MappingContractError("Task 03D completion is not marked non-release")
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise MappingContractError("candidate completion does not seal its inventory")
    for item in inventory.get("files", []):
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise MappingContractError(f"unsafe candidate inventory path: {relative}")
        path = root / relative
        if not path.is_file():
            raise MappingContractError(f"candidate inventory file is missing: {relative}")
        if path.stat().st_size != item["byte_size"] or sha256_file(path) != item["sha256"]:
            raise MappingContractError(f"candidate inventory checksum differs: {relative}")
    if build_inventory(root) != inventory:
        raise MappingContractError("candidate inventory differs from the managed file set")
    return completion_path


def publish_workspace(workspace: CandidateWorkspace) -> Path:
    """Atomically publish a completed staging tree into an absent destination."""
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    workspace.staging_root.rename(workspace.final_root)
    return workspace.final_root / "records" / "completion_record.json"
