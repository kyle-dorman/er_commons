"""Small completion-last containers for Task 05H owned JSON payloads."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from jsonschema.exceptions import best_match  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256

VERSION = "er_commons.response_inventory_release.v1"
MANIFEST = "records/managed_file_inventory.json"
COMPLETION = "records/completion.json"


@lru_cache(maxsize=1)
def _record_validator() -> Any:
    """Load the pinned small record schema once; cross-record rules remain in Python."""
    path = (
        Path(__file__).resolve().parents[3]
        / "benchmarks/er_bench/schemas/response_inventory/release_v1/records.schema.json"
    )
    return Draft202012Validator(json.loads(path.read_bytes()), format_checker=FormatChecker())


def validate_owned_record(record: dict[str, Any]) -> None:
    """Reject malformed decision and closure records before using their values."""
    error = best_match(_record_validator().iter_errors(record))
    if error is not None:
        field = ".".join(str(part) for part in error.absolute_path) or "record"
        # The schema uses oneOf. Its top-level error would dump the entire record;
        # report the most specific failing field and keep terminal output readable.
        message = error.message
        if len(message) > 300:
            message = message[:297] + "..."
        raise ValueError(f"05H record schema violation at {field}: {message}")


def encode(value: Any) -> bytes:
    """Encode finite JSON deterministically, independent of dictionary discovery order."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def encode_rows(rows: list[dict[str, Any]]) -> bytes:
    """Serialize already ordered JSONL records without materializing copied source text."""
    return b"".join(encode(row) for row in rows)


def digest(data: bytes) -> str:
    """Hash only bytes deliberately supplied by the caller."""
    return hashlib.sha256(data).hexdigest()


def relative_name(name: str) -> str:
    """Reject ambiguous or escaping managed paths before file access."""
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or str(path) != name or "\\" in name:
        raise ValueError(f"invalid managed path: {name!r}")
    return name


def no_symlinks(path: Path) -> None:
    """Keep an artifact's authority at its declared location."""
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"artifact path traverses a symbolic link: {path}")


def _records(
    payloads: Mapping[str, bytes], plan_id: str, semantic_digest: str, status: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive manifest then completion, with no self-referential identity fields."""
    if not payloads or status not in {"prepared", "complete_with_limitations"}:
        raise ValueError("05H container requires payloads and a recognized status")
    files = []
    for name, data in sorted(payloads.items()):
        relative_name(name)
        if name in {MANIFEST, COMPLETION} or PurePosixPath(name).suffix not in {".json", ".jsonl"}:
            raise ValueError(f"reserved or unsupported release payload: {name}")
        files.append({"path": name, "size_bytes": len(data), "sha256": digest(data)})
    manifest = {
        "schema_version": VERSION,
        "record_type": "managed_file_inventory",
        "plan_id": plan_id,
        "files": files,
    }
    manifest["inventory_id"] = "files05hv1-" + canonical_json_sha256(manifest)
    completion = {
        "schema_version": VERSION,
        "record_type": "completion",
        "stage": "05h",
        "status": status,
        "plan_id": plan_id,
        "semantic_digest": semantic_digest,
        "inventory_id": manifest["inventory_id"],
        "manifest_sha256": digest(encode(manifest)),
    }
    completion["completion_id"] = "completion05hv1-" + canonical_json_sha256(completion)
    validate_owned_record(manifest)
    validate_owned_record(completion)
    return manifest, completion


def inventory_identity(completion: dict[str, Any]) -> str:
    """Only a closed 05H completion may name the sole final inventory."""
    if completion.get("status") != "complete_with_limitations" or completion.get("stage") != "05h":
        raise ValueError("only a finalized Task 05H candidate has an inventory identity")
    return "inventoryv1-" + canonical_json_sha256(
        {
            "schema_version": VERSION,
            "stage": "05h",
            "completion_id": completion["completion_id"],
            "managed_file_inventory_id": completion["inventory_id"],
        }
    )


def _tree(root: Path, names: set[str]) -> None:
    """Require exact file and directory closure, including empty-directory rejection."""
    allowed_dirs = {str(p) for n in names for p in PurePosixPath(n).parents if str(p) != "."}
    for path in root.rglob("*"):
        name = path.relative_to(root).as_posix()
        if (
            path.is_symlink()
            or (path.is_dir() and name not in allowed_dirs)
            or (not path.is_dir() and name not in names)
        ):
            raise ValueError(f"unexpected release entry: {name}")


def read_container(
    root: Path, *, plan_id: str | None = None
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Revalidate small owned payload bytes and exact closure before any reuse."""
    no_symlinks(root)
    if not (root / COMPLETION).is_file():
        raise ValueError(f"incomplete 05H container; preserve and use a fresh attempt: {root}")
    completion = json.loads((root / COMPLETION).read_bytes())
    manifest = json.loads((root / MANIFEST).read_bytes())
    payloads: dict[str, bytes] = {}
    for item in manifest["files"]:
        name = relative_name(item["path"])
        if name in payloads:
            raise ValueError(f"duplicate managed release file: {name}")
        no_symlinks(root / name)
        payloads[name] = (root / name).read_bytes()
    expected_manifest, expected_completion = _records(
        payloads, completion["plan_id"], completion["semantic_digest"], completion["status"]
    )
    if manifest != expected_manifest or completion != expected_completion:
        raise ValueError(f"05H manifest/completion digest or identity mismatch: {root}")
    if plan_id is not None and completion["plan_id"] != plan_id:
        raise ValueError(f"05H checkpoint plan mismatch: {root}")
    if (root / MANIFEST).read_bytes() != encode(manifest) or (
        root / COMPLETION
    ).read_bytes() != encode(completion):
        raise ValueError("05H control record serialization mismatch")
    _tree(root, set(payloads) | {MANIFEST, COMPLETION})
    return completion, payloads


def write_file(path: Path, data: bytes) -> None:
    """Exclusively create and flush one privately owned file."""
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def publish_container(
    root: Path,
    payloads: Mapping[str, bytes],
    *,
    plan_id: str,
    semantic_digest: str,
    status: str,
    guard: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Seal only complete private stages; retain partial output rather than overwrite it."""
    no_symlinks(root)
    manifest, completion = _records(payloads, plan_id, semantic_digest, status)
    if root.exists():
        existing, old = read_container(root, plan_id=plan_id)
        if old != payloads or existing != completion:
            raise ValueError(f"conflicting 05H checkpoint; use a fresh attempt: {root}")
        return existing
    if guard:
        guard()
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir()
    staging = root / ".pending"
    staging.mkdir()
    owned = {**payloads, MANIFEST: encode(manifest)}
    for name, data in sorted(owned.items()):
        if guard:
            guard()
        temporary = staging / name
        temporary.parent.mkdir(parents=True, exist_ok=True)
        write_file(temporary, data)
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.rename(target)
    for directory in sorted(staging.rglob("*"), reverse=True):
        directory.rmdir()
    staging.rmdir()
    _tree(root, set(owned))
    if guard:
        guard()
    write_file(root / COMPLETION, encode(completion))
    read_container(root, plan_id=plan_id)
    return completion
