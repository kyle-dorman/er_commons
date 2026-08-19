"""Neutral, deterministic primitives for repository artifact I/O."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TextIO, TypedDict, cast

import rfc8785
from pydantic import BaseModel

type JsonScalar = None | bool | int | float | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class ArtifactReference(TypedDict):
    """Exact size and streaming checksum for one artifact path."""

    path: str
    sha256: str
    byte_size: int


def sha256_bytes(content: bytes) -> str:
    """Calculate SHA-256 for bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 for a file without loading it into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def file_reference(path: Path, *, root: Path) -> ArtifactReference:
    """Describe one contained file without loading its bytes into memory."""
    resolved_root = root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise ValueError(f"artifact is absent or escapes root: path={path}, root={root}")
    return {
        "path": resolved.relative_to(resolved_root).as_posix(),
        "sha256": sha256_file(resolved),
        "byte_size": resolved.stat().st_size,
    }


def json_bytes(value: object) -> bytes:
    """Serialize one compact, sorted, newline-terminated JSON value."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def jsonl_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    """Serialize a bounded object iterable as compact deterministic JSON Lines."""
    return b"".join(json_bytes(record) for record in records)


def canonical_json_sha256(value: Any) -> str:
    """Hash a JSON-compatible value using RFC 8785 canonical serialization."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def publish_bytes_no_clobber(path: Path, content: bytes) -> None:
    """Publish bytes atomically without overwriting conflicting final bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.stat().st_size == len(content) and sha256_file(path) == sha256_bytes(content):
            return
        raise FileExistsError(f"refusing to overwrite changed file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _link_or_verify_identical(temporary_path, path)
        _fsync_directory(path.parent)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_json_atomic(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    """Write a small indented JSON record through an atomic replacement."""
    if isinstance(payload, BaseModel):
        content = payload.model_dump_json(indent=2).encode() + b"\n"
    else:
        content = json.dumps(payload, indent=2).encode() + b"\n"
    _write_bytes_atomic(path, content)


@contextmanager
def atomic_text_writer(path: Path) -> Iterator[TextIO]:
    """Yield a UTF-8 stream and atomically replace the target after a durable close."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_json_atomic_streaming(path: Path, payload: object) -> None:
    """Serialize a large JSON value without first allocating its encoded bytes."""
    with atomic_text_writer(path) as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Stream deterministic JSONL through an atomic replacement and return its count."""
    return _write_jsonl(path, records, no_clobber=False)


def publish_jsonl_no_clobber(path: Path, records: Iterable[dict[str, Any]]) -> int:
    """Stream and atomically publish JSONL, accepting only identical existing bytes."""
    return _write_jsonl(path, records, no_clobber=True)


def load_json(path: Path) -> JsonValue:
    """Read one JSON value with artifact-path context on malformed input."""
    try:
        with path.open(encoding="utf-8") as stream:
            return cast(JsonValue, json.load(stream))
    except OSError as error:
        raise ValueError(f"cannot read JSON artifact {path}: {error}") from error
    except UnicodeDecodeError as error:
        raise ValueError(f"invalid UTF-8 JSON artifact {path}: byte {error.start}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON artifact {path}:{error.lineno}:{error.colno}: {error.msg}"
        ) from error


def read_json_object(path: Path) -> JsonObject:
    """Read one JSON object and reject arrays or scalar roots."""
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def iter_jsonl(path: Path) -> Iterator[JsonObject]:
    """Yield non-empty JSONL objects with file-and-line failure context."""
    try:
        stream = path.open(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read JSONL artifact {path}: {error}") from error
    try:
        with stream:
            for number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        f"invalid JSONL artifact {path}:{number}: {error.msg}"
                    ) from error
                if not isinstance(value, dict):
                    raise ValueError(f"expected JSON object: {path}:{number}")
                yield cast(JsonObject, value)
    except UnicodeDecodeError as error:
        raise ValueError(f"invalid UTF-8 JSONL artifact {path}: byte {error.start}") from error


def read_jsonl(path: Path) -> list[JsonObject]:
    """Materialize an ordered JSONL object stream for bounded consumers."""
    return list(iter_jsonl(path))


def assert_contained(data_root: Path, relative_path: str) -> Path:
    """Resolve a relative path and reject traversal outside its declared root."""
    candidate = (data_root / relative_path).resolve()
    root = data_root.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"manifest path escapes ER_COMMONS_DATA_ROOT: {relative_path}")
    return candidate


def directory_bytes(path: Path) -> int:
    """Return the total size of regular files below a directory."""
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def artifact_inventory(root: Path, excluded: set[str]) -> dict[str, Any]:
    """Hash generated files except named self-referential seal records."""
    files = [
        file_reference(path, root=root)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in excluded
    ]
    return {
        "file_count": len(files),
        "byte_count": sum(record["byte_size"] for record in files),
        "files": files,
    }


def stable_json_sha256(payload: Any) -> str:
    """Hash one compact JSON value with Unicode preserved."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_jsonl(
    path: Path,
    records: Iterable[dict[str, Any]],
    *,
    no_clobber: bool,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    count = 0
    try:
        with os.fdopen(descriptor, "wb") as stream:
            for record in records:
                stream.write(_jsonl_line(record))
                count += 1
            stream.flush()
            os.fsync(stream.fileno())
        if no_clobber:
            _link_or_verify_identical(temporary_path, path)
        else:
            os.replace(temporary_path, path)
        _fsync_directory(path.parent)
        return count
    finally:
        temporary_path.unlink(missing_ok=True)


def _jsonl_line(record: dict[str, Any]) -> bytes:
    """Preserve the established Unicode, sorted-key JSONL byte contract."""
    return (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode()


def _link_or_verify_identical(temporary_path: Path, path: Path) -> None:
    try:
        os.link(temporary_path, path)
    except FileExistsError as error:
        same_size = path.stat().st_size == temporary_path.stat().st_size
        if same_size and sha256_file(path) == sha256_file(temporary_path):
            return
        raise FileExistsError(f"refusing to overwrite changed file: {path}") from error


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    finally:
        temporary_path.unlink(missing_ok=True)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "ArtifactReference",
    "JsonObject",
    "JsonValue",
    "artifact_inventory",
    "atomic_text_writer",
    "assert_contained",
    "canonical_json_sha256",
    "directory_bytes",
    "file_reference",
    "iter_jsonl",
    "json_bytes",
    "jsonl_bytes",
    "load_json",
    "publish_bytes_no_clobber",
    "publish_jsonl_no_clobber",
    "read_json_object",
    "read_jsonl",
    "sha256_bytes",
    "sha256_file",
    "stable_json_sha256",
    "write_json_atomic",
    "write_jsonl",
    "write_json_atomic_streaming",
]
