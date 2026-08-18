"""Contained exact-byte reads for collection contract validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from er_commons.collection_processing.contract import JsonObject


class CollectionArtifactReader:
    """Read exact artifact references contained by one collection root."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def read(self, reference: JsonObject) -> bytes:
        """Verify a closed path, byte count, and digest before returning bytes."""
        if set(reference) != {"path", "sha256", "byte_size"}:
            raise ValueError("collection artifact reference fields differ")
        relative = reference.get("path")
        if not isinstance(relative, str) or not relative:
            raise ValueError("collection artifact reference path is invalid")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError("collection artifact reference escapes its root")
        path = (self._root / relative).resolve()
        if not path.is_relative_to(self._root) or not path.is_file():
            raise ValueError(f"collection artifact is absent: {relative}")
        value = path.read_bytes()
        if len(value) != reference.get("byte_size"):
            raise ValueError(f"collection artifact byte size differs: {relative}")
        if hashlib.sha256(value).hexdigest() != reference.get("sha256"):
            raise ValueError(f"collection artifact checksum differs: {relative}")
        return value

    def read_json(self, reference: JsonObject) -> JsonObject:
        """Read one verified JSON object artifact."""
        value = json.loads(self.read(reference))
        if not isinstance(value, dict):
            raise ValueError("collection artifact must contain a JSON object")
        return value


__all__ = ["CollectionArtifactReader"]
