"""Stable serialization and contained artifact references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject


def json_bytes(value: object) -> bytes:
    """Serialize one stable, newline-terminated JSON value."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def jsonl_bytes(rows: list[JsonObject]) -> bytes:
    """Serialize ordered compact JSONL rows."""
    return b"".join(json_bytes(row) for row in rows)


def bytes_ref(path: str, value: bytes) -> JsonObject:
    """Describe exact bytes at a repository-independent relative path."""
    return {"path": path, "sha256": hashlib.sha256(value).hexdigest(), "byte_size": len(value)}


def file_ref(path: Path, root: Path) -> JsonObject:
    """Describe one existing file contained beneath ``root``."""
    resolved_root = root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise ValueError(f"artifact reference escapes or is absent: {path}")
    return bytes_ref(resolved.relative_to(resolved_root).as_posix(), resolved.read_bytes())


def read_json(path: Path) -> JsonObject:
    """Read one JSON object and reject other root shapes."""
    value: Any = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[JsonObject]:
    """Read an ordered JSONL stream of objects."""
    rows: list[JsonObject] = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        value: Any = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {path}:{number}")
        rows.append(value)
    return rows


def managed_inventory(payloads: dict[str, bytes]) -> JsonObject:
    """Build the persisted inventory, excluding self-referential identity evidence."""
    return {
        "files": [
            {
                "path": path,
                "sha256": bytes_ref(path, value)["sha256"],
                "byte_size": len(value),
            }
            for path, value in sorted(payloads.items())
            if path != "records/identity_preimage.json"
        ]
    }


def inventory_ref(final_relative_root: str, payloads: dict[str, bytes]) -> JsonObject:
    """Describe the deterministic managed-inventory record."""
    return bytes_ref(
        f"{final_relative_root}/records/artifact_inventory.json",
        json_bytes(managed_inventory(payloads)),
    )
