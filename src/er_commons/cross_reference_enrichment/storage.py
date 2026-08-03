"""Deterministic JSON storage at the pipeline boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.cross_reference_enrichment.types import JsonObject


def read_json(path: Path) -> JsonObject:
    """Read one JSON object with an explicit root-type check."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[JsonObject]:
    """Read an ordered stream of JSON objects."""
    records = [json.loads(line) for line in path.read_text().splitlines() if line]
    if any(not isinstance(record, dict) for record in records):
        raise TypeError(f"expected JSON object records in {path}")
    return records


def write_json(path: Path, value: Any) -> None:
    """Write stable, reviewable JSON with one terminal newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_pretty_json(value))


def write_jsonl(path: Path, records: list[JsonObject]) -> None:
    """Write stable compact JSONL in supplied record order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records
    )
    path.write_text(payload)


def serialized_json_sha256(value: Any) -> str:
    """Hash the exact bytes produced by :func:`write_json`."""
    return hashlib.sha256(_pretty_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a complete file SHA-256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
