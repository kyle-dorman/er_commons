"""Optional raw Docling machine-artifact scan for the TOC census."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.artifact_io import iter_jsonl
from er_commons.human_review_support.task04.toc_census_support import (
    object_pointers,
    raw_page_numbers,
)

try:
    import ijson  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - exercised by the CLI environment check
    ijson = None


def load_raw_document_indexes(
    assets_path: Path,
    data_root: Path,
    pages: dict[str, Any],
    *,
    enabled: bool,
) -> list[dict[str, Any]]:
    """Stream raw Docling tables and retain document-index pointers only."""
    if not enabled or not assets_path.is_file():
        return []
    if ijson is None:
        raise RuntimeError("raw Docling census requires the project ijson dependency")
    assets = [row for row in iter_jsonl(assets_path) if row.get("role") == "raw_docling_json"]
    results: list[dict[str, Any]] = []
    for asset in assets:
        raw_path_value = asset.get("path")
        if not isinstance(raw_path_value, str):
            continue
        raw_path = Path(raw_path_value)
        if not raw_path.is_absolute():
            raw_path = data_root / raw_path
        with raw_path.open("rb") as stream:
            for index, table in enumerate(ijson.items(stream, "tables.item")):
                if not isinstance(table, dict) or table.get("label") != "document_index":
                    continue
                pointer = f"#/tables/{index}"
                page_numbers = sorted(raw_page_numbers(table))
                results.append(
                    {
                        "asset_id": str(asset.get("id") or ""),
                        "asset_path": raw_path_value,
                        "object_pointer": pointer,
                        "page_numbers": page_numbers,
                        "descendant_pointers": sorted(object_pointers(table)),
                    }
                )
                for page in pages.values():
                    if page.physical_page in page_numbers:
                        page.add("raw_docling_document_index", pointer)
    return sorted(results, key=lambda item: (str(item["asset_path"]), str(item["object_pointer"])))


__all__ = ["load_raw_document_indexes"]
