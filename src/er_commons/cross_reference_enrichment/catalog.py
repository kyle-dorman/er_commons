"""Sealed model-corpus catalog used only for unresolved document disposition."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from er_commons.cross_reference_enrichment.storage import read_json


@dataclass(frozen=True)
class CorpusDocumentCatalog:
    """Normalized identifiers and official titles from the sealed source manifest."""

    lookup_keys: frozenset[str]

    @classmethod
    def from_source_manifest(cls, path: Path) -> CorpusDocumentCatalog:
        """Load only the manifest's model-corpus documents."""
        manifest = read_json(path)
        keys: set[str] = set()
        for source in manifest["sources"]:
            if source.get("source_role") != "model_corpus":
                continue
            keys.update(_catalog_keys(source["source_id"], source["official_title"]))
        return cls(frozenset(keys))


def _normalize_document_name(value: str) -> str:
    """Normalize catalog labels without inventing aliases from mention text."""
    without_pdf_suffix = re.sub(r"\s*\(PDF\)\s*$", "", value, flags=re.IGNORECASE)
    return " ".join(without_pdf_suffix.casefold().replace("_", " ").split())


def _catalog_keys(source_id: str, official_title: str) -> set[str]:
    """Derive conservative target-side keys from sealed catalog fields."""
    normalized_title = _normalize_document_name(official_title)
    keys = {_normalize_document_name(source_id), normalized_title}
    if normalized_title.endswith(" deir"):
        project_name = normalized_title.removesuffix(" deir").removeprefix("complete ")
        keys.add(f"draft eir for {project_name}")
        keys.add(f"draft eir for the {project_name}")
    return keys
