"""Verified corpus catalog and immutable scope-input publication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject
from er_commons.corpus_resolution.storage import bytes_ref, read_json


@dataclass(frozen=True)
class CorpusCatalog:
    """Lookup keys joined to their sealed source identities."""

    raw_bytes: bytes
    lookup: dict[str, tuple[JsonObject, ...]]

    @classmethod
    def load(cls, data_root: Path, relative_path: Path) -> CorpusCatalog:
        """Load a contained catalog and validate its human-facing structure."""
        path = (data_root / relative_path).resolve()
        if not path.is_relative_to(data_root.resolve()) or not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        catalog = read_json(path)
        documents = catalog.get("documents")
        if not isinstance(documents, list):
            raise ValueError("corpus catalog lacks documents")
        lookup: dict[str, list[JsonObject]] = {}
        for document in documents:
            if not isinstance(document, dict) or not isinstance(document.get("source"), dict):
                raise ValueError("corpus catalog document is invalid")
            for key in document.get("lookup_keys", []):
                if not isinstance(key, str):
                    raise ValueError("corpus catalog lookup key is invalid")
                lookup.setdefault(key, []).append(document["source"])
        return cls(raw, {key: tuple(values) for key, values in lookup.items()})


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
