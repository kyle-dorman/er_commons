"""Verified corpus catalog and immutable scope-input publication."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.storage import bytes_ref


class ScopeInputStore:
    """Publish checksum-addressed inputs shared across corpus stages."""

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
