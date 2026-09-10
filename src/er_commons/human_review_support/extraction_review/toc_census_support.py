"""Small parsing helpers shared by the source-free TOC census."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

_STRING_FIELDS = {
    field: re.compile(rf'"{field}"\s*:\s*("(?:\\.|[^"\\])*")')
    for field in (
        "id",
        "canonical_text",
        "raw_text",
        "semantic_placement",
        "section_id",
        "table_family_id",
    )
}
_BOOL_FIELDS = {field: re.compile(rf'"{field}"\s*:\s*(true|false)') for field in ("is_toc_row",)}
_PAGE_ID_RE = re.compile(r'"page_id"\s*:\s*("(?:\\.|[^"\\])*")')
_TEXT_RE = re.compile(r'"text"\s*:\s*("(?:\\.|[^"\\])*")')


def iter_jsonl_lines(path: Path) -> Iterator[str]:
    """Yield non-empty JSONL lines without decoding large nested objects."""
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield line


def string_field(line: str, field: str) -> str | None:
    """Extract one compact JSON string field from a controlled machine row."""
    match = _STRING_FIELDS[field].search(line)
    if match is None:
        return None
    value = json.loads(match.group(1))
    return value if isinstance(value, str) else None


def bool_field(line: str, field: str) -> bool | None:
    """Extract one compact JSON boolean field from a controlled machine row."""
    match = _BOOL_FIELDS[field].search(line)
    return None if match is None else match.group(1) == "true"


def page_ids(line: str) -> set[str]:
    """Extract page IDs from region objects without decoding cell payloads."""
    return {str(json.loads(match)) for match in _PAGE_ID_RE.findall(line)}


def cell_text(line: str) -> str:
    """Flatten cell text only when a row is relevant to navigation heuristics."""
    values = [json.loads(match) for match in _TEXT_RE.findall(line)]
    return " ".join(value.strip() for value in values if isinstance(value, str) and value.strip())


def object_pointers(value: object) -> set[str]:
    """Collect raw Docling object pointers embedded in one object."""
    if isinstance(value, dict):
        return {item for child in value.values() for item in object_pointers(child)}
    if isinstance(value, list):
        return {item for child in value for item in object_pointers(child)}
    return {value} if isinstance(value, str) and value.startswith("#/") else set()


def raw_page_numbers(value: object) -> set[int]:
    """Collect raw Docling provenance page numbers from one object."""
    if isinstance(value, dict):
        values = set()
        for key, child in value.items():
            if key == "page_no" and isinstance(child, int) and child > 0:
                values.add(child)
            values.update(raw_page_numbers(child))
        return values
    if isinstance(value, list):
        return {page for child in value for page in raw_page_numbers(child)}
    return set()


def text(row: dict[str, Any]) -> str:
    """Prefer canonical text while retaining producer text as a fallback."""
    return str(row.get("canonical_text") or row.get("raw_text") or "").strip()


def snippet(value: str) -> str:
    """Keep evidence context readable and bounded in the census."""
    return " ".join(value.split())[:240]


def string(value: object, path: str) -> str:
    """Require a non-empty string at an artifact boundary."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"expected non-empty string at {path}")
    return value


def integer(value: object, path: str) -> int:
    """Require a positive integer at an artifact boundary."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"expected positive integer at {path}")
    return value


def sha256_json(value: object) -> str:
    """Hash a small JSON preimage deterministically for candidate page IDs."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
