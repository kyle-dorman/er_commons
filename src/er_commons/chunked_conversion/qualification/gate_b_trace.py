"""Page-local trace extraction and comparison for Gate B."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, Never

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256, iter_jsonl, read_json_object
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    DOCUMENT_COLLECTIONS,
    SOURCE_ID,
)


class GateBTraceError(ValueError):
    """A baseline or live page trace violates an exact comparison invariant."""

    def __init__(self, code: str, path: str, detail: str) -> None:
        self.code = code
        self.path = path
        self.detail = detail
        super().__init__(f"code={code} path={path} detail={detail}")


def _fail(code: str, path: str, detail: str) -> Never:
    raise GateBTraceError(code, path, detail)


def sealed_page_trace(source_root: Path, pages: set[int]) -> dict[str, Any]:
    """Stream the selected page-local projection from the sealed G1 baseline."""
    producer = source_root / "documents" / SOURCE_ID / "producer"
    document_path = producer / "docling/document.json"
    overlay = tuple(iter_jsonl(producer / "docling/heading_overlay.jsonl"))
    alignment = tuple(iter_jsonl(producer / "docling/alignment_pages.jsonl"))
    assets_payload = read_json_object(producer / "asset_inventory.json")
    collections: dict[str, list[dict[str, Any]]] = {}
    headings: list[dict[str, Any]] = []
    levels = {str(row["raw_self_ref"]): required_int(row, "level") for row in overlay}
    for collection in DOCUMENT_COLLECTIONS:
        selected: list[dict[str, Any]] = []
        with document_path.open("rb") as stream:
            for raw_item in ijson.items(stream, f"{collection}.item"):
                item = required_dict_value(raw_item, f"{collection}.item")
                if item_pages(item) & pages:
                    selected.append(normalize_item(item))
                    raw_ref = item.get("self_ref")
                    if collection == "texts" and item.get("label") == "section_header":
                        headings.append(heading_trace(item, levels.get(str(raw_ref), 1)))
        collections[collection] = sorted_dicts(selected)
    return {
        "schema_version": "er_commons.task03h2_gate_b_page_trace.v1",
        "pages": sorted(pages),
        "collections": collections,
        "headings": sorted_dicts(headings),
        "alignment_pages": [row for row in alignment if required_int(row, "page_no") in pages],
        "assets": asset_trace(assets_payload.get("assets", []), pages),
    }


def trace_from_outputs(
    document: dict[str, Any],
    overlay: tuple[dict[str, Any], ...],
    alignment: tuple[dict[str, Any], ...],
    assets: tuple[dict[str, Any], ...],
    pages: set[int],
) -> dict[str, Any]:
    """Build the same page-local projection from one live bounded output."""
    levels = {str(row["raw_self_ref"]): required_int(row, "level") for row in overlay}
    collections: dict[str, list[dict[str, Any]]] = {}
    headings: list[dict[str, Any]] = []
    for collection in DOCUMENT_COLLECTIONS:
        selected: list[dict[str, Any]] = []
        raw_items = document.get(collection, [])
        if not isinstance(raw_items, list):
            _fail("invalid_collection", collection, "live document collection is not a list")
        for index, raw_item in enumerate(raw_items):
            item = required_dict_value(raw_item, f"{collection}[{index}]")
            if item_pages(item) & pages:
                selected.append(normalize_item(item))
                raw_ref = item.get("self_ref")
                if collection == "texts" and item.get("label") == "section_header":
                    headings.append(heading_trace(item, levels.get(str(raw_ref), 1)))
        collections[collection] = sorted_dicts(selected)
    return {
        "schema_version": "er_commons.task03h2_gate_b_page_trace.v1",
        "pages": sorted(pages),
        "collections": collections,
        "headings": sorted_dicts(headings),
        "alignment_pages": [row for row in alignment if required_int(row, "page_no") in pages],
        "assets": asset_trace(assets, pages),
    }


def subset_trace(trace: dict[str, Any], pages: set[int]) -> dict[str, Any]:
    """Restrict a validated trace to the pages at one seam."""
    if set(trace.get("pages", [])) == pages:
        return trace
    raw_collections = required_dict(trace, "collections")
    collections = {
        name: [item for item in rows if set(item["_trace_pages"]) & pages]
        for name, rows in raw_collections.items()
    }
    headings = required_list(trace, "headings")
    alignment = required_list(trace, "alignment_pages")
    assets = required_list(trace, "assets")
    return {
        **trace,
        "pages": sorted(pages),
        "collections": collections,
        "headings": [item for item in headings if item["page_no"] in pages],
        "alignment_pages": [item for item in alignment if int(item["page_no"]) in pages],
        "assets": [item for item in assets if item["physical_pdf_page"] in pages],
    }


def compare_sealed_page_trace(
    expected: dict[str, Any], actual: dict[str, Any], *, seam_id: str
) -> list[dict[str, Any]]:
    """Require exact local evidence and one explainable heading-level compression."""
    expected_headings = headings_by_semantic_key(expected.get("headings"), seam_id)
    actual_headings = headings_by_semantic_key(actual.get("headings"), seam_id)
    if expected_headings.keys() != actual_headings.keys():
        _fail("heading_targets_differ", seam_id, "sealed and live heading keys differ")
    level_pairs = {
        key: (
            required_int(expected_headings[key], "level"),
            required_int(actual_headings[key], "level"),
        )
        for key in sorted(expected_headings)
    }
    if any(not 1 <= level <= 6 for pair in level_pairs.values() for level in pair):
        _fail("heading_level_out_of_range", seam_id, "heading level must be in 1..6")
    changed_offsets = {left - right for left, right in level_pairs.values() if left != right}
    if len(changed_offsets) > 1 or any(offset <= 0 for offset in changed_offsets):
        _fail("heading_compression_inconsistent", seam_id, "levels need one positive offset")
    compression = next(iter(changed_offsets), 0)
    if any(right != max(1, left - compression) for left, right in level_pairs.values()):
        _fail("heading_compression_not_floor_preserving", seam_id, "levels violate floor")
    differences = _heading_differences(expected_headings, level_pairs, compression)
    expected_without_levels = {**expected, "headings": sorted(expected_headings)}
    actual_without_levels = {**actual, "headings": sorted(actual_headings)}
    if expected_without_levels != actual_without_levels:
        _fail("page_local_trace_differs", seam_id, "difference exists outside heading levels")
    return differences


def _heading_differences(
    headings: dict[str, dict[str, Any]],
    levels: dict[str, tuple[int, int]],
    compression: int,
) -> list[dict[str, Any]]:
    return [
        {
            "semantic_key": key,
            "page_no": required_int(headings[key], "page_no"),
            "text": required_dict(headings[key], "item").get("text"),
            "sealed_whole_document_level": expected,
            "bounded_window_level": actual,
            "compression_offset": compression,
            "classification": "expected_whole_document_heading_context",
        }
        for key, (expected, actual) in levels.items()
        if expected != actual
    ]


def headings_by_semantic_key(value: Any, seam_id: str) -> dict[str, dict[str, Any]]:
    """Index headings after removing the only allowed differing field."""
    if not isinstance(value, list):
        _fail("invalid_heading_trace", seam_id, "headings must be a list")
    keyed: dict[str, dict[str, Any]] = {}
    for index, raw_heading in enumerate(value):
        heading = required_dict_value(raw_heading, f"{seam_id}.headings[{index}]")
        semantic = {key: item for key, item in heading.items() if key != "level"}
        key = canonical_json_sha256(semantic)
        if key in keyed:
            _fail("duplicate_heading", f"{seam_id}/{key}", "semantic heading key repeated")
        keyed[key] = heading
    return keyed


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    """Remove unstable local refs while preserving page provenance."""
    normalized = normalize_refs(item)
    if not isinstance(normalized, dict):
        _fail("invalid_item", "item", "normalized item is not an object")
    normalized.pop("self_ref", None)
    normalized["_trace_pages"] = sorted(item_pages(item))
    return normalized


def normalize_refs(value: Any) -> Any:
    """Canonicalize bounded object references and ijson decimal values."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: normalize_refs(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_refs(item) for item in value]
    if isinstance(value, str) and value.startswith("#/") and value.count("/") == 2:
        collection, _, index = value[2:].partition("/")
        if index.isdigit():
            return f"#/{collection}/*"
    return value


def item_pages(item: dict[str, Any]) -> set[int]:
    """Return every physical page named by one item's provenance."""
    pages: set[int] = set()
    for provenance in item.get("prov") or []:
        page_no = provenance.get("page_no") if isinstance(provenance, dict) else None
        if isinstance(page_no, int):
            pages.add(page_no)
    return pages


def heading_trace(item: dict[str, Any], level: int) -> dict[str, Any]:
    """Project one section-header item into the comparison trace."""
    pages = sorted(item_pages(item))
    return {"page_no": pages[0] if pages else 0, "level": level, "item": normalize_item(item)}


def asset_trace(assets: Any, pages: set[int]) -> list[dict[str, Any]]:
    """Project figure assets on selected pages into stable comparison fields."""
    if not isinstance(assets, (list, tuple)):
        _fail("invalid_assets", "asset_inventory.assets", "expected list or tuple")
    projected = []
    for index, raw_item in enumerate(assets):
        item = required_dict_value(raw_item, f"assets[{index}]")
        page = required_int(item, "physical_pdf_page")
        if page in pages:
            projected.append(
                {
                    "asset_role": item["asset_role"],
                    "physical_pdf_page": page,
                    "byte_size": required_int(item, "byte_size"),
                    "sha256": item["sha256"],
                }
            )
    return sorted_dicts(projected)


def sorted_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort JSON objects by canonical digest."""
    return sorted(items, key=canonical_json_sha256)


def required_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    """Read one required object field with diagnostic context."""
    return required_dict_value(payload.get(key), key)


def required_dict_value(value: Any, path: str) -> dict[str, Any]:
    """Validate an arbitrary value as a JSON object."""
    if not isinstance(value, dict):
        _fail("expected_object", path, f"observed {type(value).__name__}")
    return value


def required_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Read one required list of objects with diagnostic context."""
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        _fail("expected_object_list", key, f"observed {type(value).__name__}")
    return value


def required_int(payload: dict[str, Any], key: str) -> int:
    """Read one required non-boolean integer field."""
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        _fail("expected_integer", key, f"observed {value!r}")
    return value


__all__ = [
    "GateBTraceError",
    "compare_sealed_page_trace",
    "sealed_page_trace",
    "subset_trace",
    "trace_from_outputs",
]
