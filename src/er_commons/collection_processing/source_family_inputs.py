"""Verified source-family catalog and immutable collection inputs."""

from __future__ import annotations

from pathlib import Path

from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.storage import bytes_ref


class CollectionInputStore:
    """Publish checksum-addressed inputs shared across collection stages."""

    def __init__(self, extraction_root: Path, scope_id: str) -> None:
        self._extraction_root = extraction_root
        self._scope_id = scope_id

    def publish(self, label: str, value: bytes) -> JsonObject:
        """Write or exactly reuse one immutable input and return its reference."""
        digest = bytes_ref("unused", value)["sha256"]
        relative = f"scopes/{self._scope_id}/inputs/{label}-{digest}.json"
        path = self._extraction_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != value:
            raise ValueError(f"conflicting immutable scope input: {path}")
        if not path.exists():
            path.write_bytes(value)
        return bytes_ref(relative, value)
