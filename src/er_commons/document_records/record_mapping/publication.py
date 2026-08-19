"""Atomic publication and checksum-verified reuse for canonical candidates."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_records.record_mapping.errors import MappingContractError

_INVENTORY_EXCLUDED = frozenset(
    {"records/artifact_inventory.json", "records/completion_record.json"}
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class CandidateWorkspace:
    """One private staging directory and its deterministic final destination."""

    staging_root: Path
    final_root: Path


@dataclass(frozen=True)
class ManagedCandidateFile:
    """One validated inventory row resolved below its candidate root."""

    relative_path: str
    path: Path
    sha256: str
    byte_size: int


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
    excluded: frozenset[str] = _INVENTORY_EXCLUDED,
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
    """Verify terminal closure and every exact inventory byte before reuse."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    if not completion_path.is_file() or not inventory_path.is_file():
        raise MappingContractError(f"candidate terminal records are missing below {root}")
    completion = _read_json_object(completion_path)
    inventory = _read_json_object(inventory_path)
    if completion.get("candidate_id") != candidate_id:
        raise MappingContractError("candidate completion identity differs")
    if completion.get("release_candidate") is not False:
        raise MappingContractError("record-mapping completion is not marked non-release")
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise MappingContractError("candidate completion does not seal its inventory")
    managed_files = validate_inventory_metadata(root, inventory)
    for item in managed_files:
        if sha256_file(item.path) != item.sha256:
            raise MappingContractError(
                f"candidate inventory checksum differs: {item.relative_path}"
            )
    return completion_path


def validate_inventory_metadata(
    root: Path, inventory: dict[str, Any]
) -> tuple[ManagedCandidateFile, ...]:
    """Validate exact managed paths, sizes, digests, and aggregate inventory facts."""
    expected_inventory_fields = {"schema_version", "files", "file_count", "byte_size"}
    if set(inventory) != expected_inventory_fields:
        raise MappingContractError("candidate inventory shape differs")
    if inventory.get("schema_version") != "er_commons.candidate_artifact_inventory.v1":
        raise MappingContractError("candidate inventory schema version differs")
    raw_files = inventory.get("files")
    if not isinstance(raw_files, list):
        raise MappingContractError("candidate inventory files are invalid")
    expected: dict[str, int] = {}
    managed: list[ManagedCandidateFile] = []
    total_bytes = 0
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise MappingContractError(f"candidate inventory entry is invalid: index={index}")
        if set(item) != {"path", "sha256", "byte_size"}:
            raise MappingContractError(f"candidate inventory entry shape differs: index={index}")
        relative = _contained_inventory_path(root, item.get("path"))
        relative_string = relative.as_posix()
        if relative_string in expected:
            raise MappingContractError(f"duplicate candidate inventory path: {relative_string}")
        byte_size = item.get("byte_size")
        digest = item.get("sha256")
        if not isinstance(byte_size, int) or isinstance(byte_size, bool) or byte_size < 0:
            raise MappingContractError(
                f"candidate inventory byte size is invalid: {relative_string}"
            )
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise MappingContractError(f"candidate inventory digest is invalid: {relative_string}")
        path = root / relative
        if not path.is_file():
            raise MappingContractError(f"candidate inventory file is missing: {relative}")
        expected[relative_string] = byte_size
        total_bytes += byte_size
        if path.stat().st_size != byte_size:
            raise MappingContractError(f"candidate inventory checksum differs: {relative}")
        managed.append(ManagedCandidateFile(relative_string, path, digest, byte_size))
    if inventory.get("file_count") != len(raw_files):
        raise MappingContractError("candidate inventory file count differs")
    if inventory.get("byte_size") != total_bytes:
        raise MappingContractError("candidate inventory byte total differs")
    symlinks = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink()]
    if symlinks:
        raise MappingContractError(f"unsafe candidate inventory symlink: {symlinks[0]}")
    actual = {
        path.relative_to(root).as_posix(): path.stat().st_size
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in _INVENTORY_EXCLUDED
    }
    if actual != expected:
        raise MappingContractError("candidate inventory differs from the managed file set")
    return tuple(managed)


def deep_audit_completed_candidate(root: Path, candidate_id: str) -> Path:
    """Explicitly rehash every completed candidate byte and rebuild its inventory."""
    completion = verify_completed_candidate(root, candidate_id)
    inventory = _read_json_object(root / "records/artifact_inventory.json")
    if build_inventory(root) != inventory:
        raise MappingContractError("candidate deep audit differs from the sealed inventory")
    return completion


def publish_workspace(workspace: CandidateWorkspace) -> Path:
    """Atomically publish a completed staging tree into an absent destination."""
    if workspace.final_root.exists():
        raise FileExistsError(f"candidate destination already exists: {workspace.final_root}")
    completion = workspace.staging_root / "records" / "completion_record.json"
    if not completion.is_file():
        raise MappingContractError(
            f"candidate completion is required before publication: {completion}"
        )
    _fsync_candidate_tree(workspace.staging_root)
    _fsync_file(completion)
    source_parent = workspace.staging_root.parent
    destination_parent = workspace.final_root.parent
    workspace.staging_root.rename(workspace.final_root)
    _fsync_directory(source_parent)
    _fsync_directory(destination_parent)
    return workspace.final_root / "records" / "completion_record.json"


def retain_workspace_without_completion(
    workspace: CandidateWorkspace, attempts_root: Path
) -> Path | None:
    """Durably retain interrupted staging or publication bytes without a completion seal."""
    source_root = (
        workspace.staging_root
        if workspace.staging_root.exists()
        else workspace.final_root
        if workspace.final_root.exists()
        else None
    )
    if source_root is None:
        return None
    records_root = source_root / "records"
    (records_root / "completion_record.json").unlink(missing_ok=True)
    if records_root.is_dir():
        _fsync_directory(records_root)
    _fsync_candidate_tree(source_root)
    attempts_root.mkdir(parents=True, exist_ok=True)
    _fsync_directory(attempts_root.parent)
    _fsync_directory(attempts_root)
    failed_root = attempts_root / workspace.staging_root.name
    source_parent = source_root.parent
    source_root.rename(failed_root)
    _fsync_directory(source_parent)
    _fsync_directory(attempts_root)
    return failed_root


def _read_json_object(path: Path) -> dict[str, Any]:
    """Load one terminal JSON object with candidate-artifact context."""
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MappingContractError(
            f"candidate JSON artifact is invalid: {path}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise MappingContractError(f"candidate JSON artifact is not an object: {path}")
    return value


def _contained_inventory_path(root: Path, value: object) -> Path:
    """Require one canonical relative POSIX path contained by the candidate root."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise MappingContractError(f"unsafe candidate inventory path: {value}")
    relative = Path(value)
    if (
        relative.is_absolute()
        or relative.as_posix() != value
        or any(part in {"", ".", ".."} for part in relative.parts)
        or value in _INVENTORY_EXCLUDED
    ):
        raise MappingContractError(f"unsafe candidate inventory path: {value}")
    resolved_root = root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise MappingContractError(f"unsafe candidate inventory path: {value}")
    return relative


def _fsync_file(path: Path) -> None:
    """Flush one completed candidate file to stable storage."""
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def _fsync_directory(path: Path) -> None:
    """Flush one directory entry set to stable storage."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_candidate_tree(root: Path) -> None:
    """Flush every candidate file and directory before its publication rename."""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        _fsync_file(path)
    directories = [root, *(item for item in root.rglob("*") if item.is_dir())]
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _fsync_directory(path)
