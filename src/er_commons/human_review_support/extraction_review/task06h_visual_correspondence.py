"""Complete-page non-text evidence closure for Task 06H correspondence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

JsonObject = dict[str, Any]


def page_visual_evidence(
    index: Mapping[str, Mapping[str, list[JsonObject]]], page: JsonObject
) -> dict[str, list[JsonObject]]:
    """Close page-resident figures through their image and asset attachments."""
    page_id = _text(page, "id")
    ordered = page.get("ordered_content_ids")
    if not isinstance(ordered, list):
        raise ValueError(f"page ordered content is invalid: {page_id}")
    figure_suffixes = {
        _stable_suffix(value) for value in ordered if isinstance(value, str) and "/figure/" in value
    }
    figure_suffixes.update(
        suffix
        for suffix, rows in index["figures"].items()
        if any(_has_page(row, page_id) for row in rows)
    )
    figures = [_one(index["figures"].get(suffix, ()), suffix) for suffix in figure_suffixes]
    image_ids = {value for figure in figures for value in _string_list(figure, "image_ids")}
    images = [_one(index["images"].get(_stable_suffix(value), ()), value) for value in image_ids]
    asset_ids = {_text(image, "asset_id") for image in images}
    assets = [_one(index["assets"].get(_stable_suffix(value), ()), value) for value in asset_ids]
    return {"figures": figures, "images": images, "assets": assets}


def normalized_records(records: Iterable[JsonObject], kind: str) -> dict[str, object]:
    """Normalize namespaces while comparing content-image seals rather than lineage paths."""
    if kind == "assets":
        fields = ("byte_size", "media_type", "producer", "role", "sha256")
        return {
            _stable_suffix(_text(row, "id")): {field: row.get(field) for field in fields}
            for row in records
        }
    return {_stable_suffix(_text(row, "id")): _normalize(row) for row in records}


def _normalize(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _normalize(item) for key, item in sorted(value.items()) if key != "extraction_id"
        }
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, str) and value.startswith(("exv1-", "figqualv1-")):
        return _stable_suffix(value)
    return value


def _has_page(record: JsonObject, page_id: str) -> bool:
    regions = record.get("regions")
    return isinstance(regions, list) and any(
        isinstance(region, dict)
        and isinstance(region.get("page_id"), str)
        and _stable_suffix(region["page_id"]) == _stable_suffix(page_id)
        for region in regions
    )


def _one(values: Iterable[JsonObject], label: str) -> JsonObject:
    rows = list(values)
    if len(rows) != 1:
        raise ValueError(f"visual correspondence is not one-to-one: {label}")
    return rows[0]


def _stable_suffix(entity_id: str) -> str:
    namespace, separator, suffix = entity_id.partition("/")
    if not namespace or not separator or "/" not in suffix:
        raise ValueError(f"canonical entity ID has no stable suffix: {entity_id}")
    return suffix


def _text(value: Mapping[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise ValueError(f"visual correspondence field is invalid: {field}")
    return result


def _string_list(value: Mapping[str, Any], field: str) -> list[str]:
    result = value.get(field)
    if not isinstance(result, list) or any(not isinstance(item, str) for item in result):
        raise ValueError(f"visual correspondence list is invalid: {field}")
    return result


__all__ = ["normalized_records", "page_visual_evidence"]
