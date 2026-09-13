"""Deterministic JSON storage at the pipeline boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.document_records.document_references.types import JsonObject


def read_json(path: Path) -> JsonObject:
    """Read one JSON object with an explicit root-type check."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[JsonObject]:
    """Read an ordered stream without retaining a second whole-file text copy."""
    records: list[JsonObject] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.rstrip("\r\n"):
                records.append(json.loads(line))
    if any(not isinstance(record, dict) for record in records):
        raise TypeError(f"expected JSON object records in {path}")
    return records


def write_json(path: Path, value: Any) -> None:
    """Write stable, reviewable JSON with one terminal newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_pretty_json(value))


def write_jsonl(path: Path, records: list[JsonObject]) -> None:
    """Write stable compact JSONL without assembling a whole-file payload."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            stream.write("\n")


def serialized_json_sha256(value: Any) -> str:
    """Hash the exact bytes produced by :func:`write_json`."""
    return hashlib.sha256(_pretty_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a complete file SHA-256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
