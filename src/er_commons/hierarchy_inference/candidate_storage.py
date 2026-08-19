"""Bounded deterministic storage primitives for hierarchy candidates."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ManagedFile:
    """One streamed managed file's exact seal metadata."""

    path: str
    byte_size: int
    sha256: str

    def as_record(self) -> dict[str, object]:
        """Return the schema-owned inventory representation."""
        return {"path": self.path, "byte_size": self.byte_size, "sha256": self.sha256}


_JSON_ENCODER = json.JSONEncoder(
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)


def stable_json_bytes(value: Any) -> bytes:
    """Serialize deterministic compact UTF-8 JSON with one terminal newline."""
    return b"".join(iter_stable_json_bytes(value))


def iter_stable_json_bytes(value: Any) -> Iterator[bytes]:
    """Yield deterministic compact UTF-8 JSON without materializing the document."""
    for chunk in _JSON_ENCODER.iterencode(value):
        yield chunk.encode()
    yield b"\n"


def write_bytes(path: Path, value: bytes) -> None:
    """Create and fsync one small terminal record without clobbering bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(root: Path, relative: str, value: Any) -> ManagedFile:
    """Stream one deterministic JSON value and return its exact file facts."""
    return write_chunks(root, relative, iter_stable_json_bytes(value))


def write_jsonl(
    root: Path,
    relative: str,
    records: Sequence[dict[str, Any]],
    progress: Callable[[int], None] | None = None,
) -> ManagedFile:
    """Stream ordered JSON Lines one record at a time."""

    def chunks() -> Iterable[bytes]:
        for index, record in enumerate(records, start=1):
            yield from iter_stable_json_bytes(record)
            if progress is not None and (index % 10_000 == 0 or index == len(records)):
                progress(index)

    return write_chunks(root, relative, chunks())


def write_chunks(root: Path, relative: str, chunks: Iterable[bytes]) -> ManagedFile:
    """Write and hash a managed file without retaining serialized bytes."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    byte_size = 0
    with path.open("xb") as stream:
        for chunk in chunks:
            stream.write(chunk)
            digest.update(chunk)
            byte_size += len(chunk)
        stream.flush()
        os.fsync(stream.fileno())
    return ManagedFile(relative, byte_size, digest.hexdigest())


def stream_file(
    path: Path,
    relative: str,
    chunk_size: int = 1024 * 1024,
    progress: Callable[[int], None] | None = None,
) -> ManagedFile:
    """Hash one existing file in bounded chunks."""
    digest = hashlib.sha256()
    byte_size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            byte_size += len(chunk)
            if progress is not None:
                progress(byte_size)
    return ManagedFile(relative, byte_size, digest.hexdigest())


def fsync_directory(path: Path) -> None:
    """Durably record directory entries around sealing and atomic renames."""
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
