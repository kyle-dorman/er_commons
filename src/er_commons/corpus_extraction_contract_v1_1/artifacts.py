"""Contained fixture artifact access and exact serialized-record parsing."""

from __future__ import annotations

import json
from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.checks import fail
from er_commons.corpus_extraction_contract_v1_1.model import JsonObject


class DirectoryArtifactReader:
    """Read artifact references below one fixed fixture or runtime root."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def read_bytes(self, reference: JsonObject) -> bytes:
        """Return contained bytes without trusting the reference checksum."""
        relative = reference.get("path")
        if not isinstance(relative, str):
            fail("artifact_reference", "artifact path must be a string")
        path = (self._root / relative).resolve()
        if not path.is_relative_to(self._root) or not path.is_file():
            fail("artifact_path", "artifact path is absent or escapes its root", subject=relative)
        return path.read_bytes()


def parse_json_object(value: bytes, *, subject: str) -> JsonObject:
    """Parse one serialized JSON object with contextual contract errors."""
    try:
        parsed = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"invalid JSON object: {error}", subject=subject)
    if not isinstance(parsed, dict):
        fail("artifact_json", "artifact root must be an object", subject=subject)
    return parsed


def parse_jsonl(value: bytes, *, subject: str) -> list[JsonObject]:
    """Parse nonblank JSONL rows while preserving serialized row order."""
    try:
        lines = value.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        fail("artifact_jsonl", f"invalid UTF-8: {error}", subject=subject)
    rows: list[JsonObject] = []
    for number, line in enumerate(lines, start=1):
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            fail("artifact_jsonl", f"invalid row {number}: {error}", subject=subject)
        if not isinstance(row, dict):
            fail("artifact_jsonl", f"row {number} is not an object", subject=subject)
        rows.append(row)
    return rows
