"""No-clobber, completion-last storage for the four source-free 05G stages.

The invocation supervisor owns the one-worker/two-thread, 4 GiB RSS, zero-swap,
1,800-second, cumulative 2 GiB output and 8 GiB free-space launch limits.
An optional guard is checked before each write and immediately before completion.
It must raise on cancellation or a resource stop; unfinished evidence is retained.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "er_commons.task05g.checkpoint.v1"
_RESERVED = {"completion.json", "failure.json", ".pending"}


def _json_bytes(value: Any) -> bytes:
    """Serialize only finite JSON with deterministic key ordering."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha(data: bytes) -> str:
    """Digest a small owned stage payload, never an upstream source artifact."""
    return hashlib.sha256(data).hexdigest()


def _root(root: Path) -> Path:
    """Require an explicit new working/05g namespace without symlink traversal."""
    root = root.absolute()
    if ".." in root.parts or not any(
        root.parts[index : index + 2] == ("working", "05g") for index in range(len(root.parts) - 2)
    ):
        raise ValueError("05G checkpoint must be below working/05g")
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("05G checkpoint path may not traverse symlinks")
    return root


def _path(name: str) -> PurePosixPath:
    """Reject ambiguous, escaping, or writer-reserved managed paths."""
    path = PurePosixPath(name)
    if (
        not name
        or str(path) != name
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or path.parts[0] in _RESERVED
        or path.suffix not in {".json", ".jsonl"}
    ):
        raise ValueError(f"invalid 05G payload path: {name!r}")
    return path


def _inventory(payloads: Mapping[str, bytes]) -> list[dict[str, Any]]:
    """Bind every supplied path to its byte length and content digest."""
    if not payloads:
        raise ValueError("05G checkpoint requires payloads")
    for name, data in payloads.items():
        _path(name)
        if not isinstance(data, bytes):
            raise ValueError("05G checkpoint payloads must be immutable bytes")
    return [
        {"path": name, "size_bytes": len(data), "sha256": _sha(data)}
        for name, data in sorted(payloads.items())
    ]


def _completion(bindings: Mapping[str, Any], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    """Construct a deterministic checkpoint seal including the entire binding set."""
    body = {
        "schema_version": SCHEMA_VERSION,
        "status": "complete",
        "bindings": json.loads(_json_bytes(dict(bindings))),
        "inventory": inventory,
    }
    return {**body, "checkpoint_id": "checkpoint05gv1-" + _sha(_json_bytes(body))}


def read_checkpoint(root: Path, expected_bindings: Mapping[str, Any]) -> dict[str, Any]:
    """Verify exact bindings, byte digests and managed tree closure before reuse."""
    root = _root(root)
    completion_path = root / "completion.json"
    if not completion_path.is_file() or completion_path.is_symlink():
        raise ValueError(
            f"05G checkpoint is incomplete at {root}; preserve it and use a new attempt"
        )
    completion = json.loads(completion_path.read_bytes())
    if not isinstance(completion, dict) or not isinstance(completion.get("inventory"), list):
        raise ValueError(f"malformed 05G checkpoint completion: {completion_path}")
    payloads: dict[str, bytes] = {}
    for item in completion["inventory"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError(f"malformed 05G checkpoint inventory: {completion_path}")
        name = item["path"]
        _path(name)
        path = root / name
        if (
            name in payloads
            or not path.is_file()
            or any(part.is_symlink() for part in (path, *path.parents))
        ):
            raise ValueError(f"duplicate or missing 05G checkpoint payload: {path}")
        payloads[name] = path.read_bytes()
    expected = _completion(expected_bindings, _inventory(payloads))
    if completion != expected or completion_path.read_bytes() != _json_bytes(expected):
        fields = sorted(
            key
            for key in set(completion) | set(expected)
            if completion.get(key) != expected.get(key)
        )
        details = ", ".join(fields) if fields else "completion serialization"
        raise ValueError(
            f"05G checkpoint binding, digest, size or completion mismatch at {root}: {details}"
        )
    _check_tree(root, set(payloads), completed=True)
    return expected


def _check_tree(root: Path, names: set[str], *, completed: bool) -> None:
    """Reject unowned entries including empty directories and symbolic links."""
    allowed_files = set(names) | ({"completion.json"} if completed else set())
    allowed_dirs = {
        str(parent)
        for name in names
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if (
            path.is_symlink()
            or (path.is_dir() and relative not in allowed_dirs)
            or (not path.is_dir() and relative not in allowed_files)
        ):
            raise ValueError(f"unexpected 05G checkpoint entry: {relative}")


def _write_owned(path: Path, data: bytes) -> None:
    """Create and flush one previously nonexistent privately owned file."""
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def publish_checkpoint(
    root: Path,
    payloads: Mapping[str, bytes],
    bindings: Mapping[str, Any],
    *,
    before_completion: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Publish exact owned payloads, retaining failures and sealing completion last.

    Existing complete content is verified and returned without a write. Existing
    partial or conflicting content fails closed; callers use a fresh attempt.
    A guard exception, including KeyboardInterrupt, can never produce completion.
    """
    root = _root(root)
    payloads = dict(payloads)
    completion = _completion(bindings, _inventory(payloads))
    completion_bytes = _json_bytes(completion)
    if root.exists():
        existing = read_checkpoint(root, bindings)
        if existing != completion:
            raise ValueError("conflicting 05G checkpoint payloads; use a new identity")
        return existing
    if before_completion is not None:
        before_completion()
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir()  # Exclusive reservation: a concurrent publisher cannot replace this path.
    pending = root / ".pending"
    try:
        pending.mkdir()
        for name, data in sorted(payloads.items()):
            if before_completion is not None:
                before_completion()
            temporary = pending / name
            temporary.parent.mkdir(parents=True, exist_ok=True)
            _write_owned(temporary, data)
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.rename(target)
        # Remove only empty directories created by this successful writer.
        for directory in sorted(pending.rglob("*"), reverse=True):
            directory.rmdir()
        pending.rmdir()
        if before_completion is not None:
            before_completion()
        _check_tree(root, set(payloads), completed=False)
        if any((root / name).read_bytes() != data for name, data in payloads.items()):
            raise ValueError("05G private payload closure changed before completion")
        _write_owned(root / ".pending", completion_bytes)
        (root / ".pending").rename(root / "completion.json")
    except BaseException as exc:
        failure = {"status": "incomplete", "error_type": type(exc).__name__, "message": str(exc)}
        try:
            _write_owned(root / "failure.json", _json_bytes(failure))
        except OSError:
            pass  # A full disk must not hide the original failure or remove its evidence.
        raise
    return completion
