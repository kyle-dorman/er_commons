"""Small exact-byte helpers shared by replay orchestration and auditing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]


def read_json(path: Path) -> JsonObject:
    """Read one JSON object with its path in any parse error."""
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact is not an object: {path}")
    return cast(JsonObject, value)


def read_jsonl(path: Path) -> list[JsonObject]:
    """Read ordered JSON objects from one JSONL stream."""
    rows: list[JsonObject] = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row is not an object: {path}:{number}")
        rows.append(cast(JsonObject, value))
    return rows


def json_bytes(value: object) -> bytes:
    """Return stable, reviewable JSON bytes."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_exact(path: Path, value: bytes) -> None:
    """Create an immutable artifact or verify exact existing bytes."""
    if path.exists():
        if path.read_bytes() != value:
            raise ValueError(f"immutable replay artifact differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()
