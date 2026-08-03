"""Small deterministic JSON helpers for cross-reference materialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


def read_json(path: Path) -> JsonObject:
    """Read one JSON object."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected object in {path}")
    return value


def read_jsonl(path: Path) -> list[JsonObject]:
    """Read an ordered JSONL object stream."""
    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    if any(not isinstance(record, dict) for record in records):
        raise TypeError(f"expected object records in {path}")
    return records


def write_json(path: Path, value: Any) -> None:
    """Write stable, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, records: list[JsonObject]) -> None:
    """Write stable compact JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records
    )
    path.write_text(payload)


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
