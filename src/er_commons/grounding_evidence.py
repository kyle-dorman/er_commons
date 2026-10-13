"""Literal source surfaces shared by strict validation and quotation diagnostics."""

from __future__ import annotations

from typing import Any


def source_texts(source: dict[str, Any]) -> list[str]:
    """Return a validated resolved source's full text, table cells and captions unchanged."""
    texts = [source["full_source_text"]]
    for table in source["tables"]:
        texts.extend(cell["text"] for cell in table["cells"])
        if table.get("caption"):
            texts.append(table["caption"])
    return texts
