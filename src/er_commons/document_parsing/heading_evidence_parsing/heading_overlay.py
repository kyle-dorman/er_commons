"""Represent Docling heading levels as a small deterministic overlay."""

from __future__ import annotations

import copy
from collections.abc import Iterator
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)

JsonObject = dict[str, Any]
SCHEMA_VERSION = "er_commons.heading_level_overlay.v1"
BASE_LEVEL = 1


def split_heading_overlay(document: JsonObject) -> tuple[JsonObject, list[JsonObject]]:
    """Return one baseline document plus stable-ref level changes."""
    base = copy.deepcopy(document)
    overlay: list[JsonObject] = []
    for item in _objects(base):
        level = item.get("level")
        pointer = item.get("self_ref")
        if not isinstance(level, int):
            continue
        if not isinstance(pointer, str):
            raise HierarchyInferenceContractError("leveled Docling object lacks self_ref")
        item["level"] = BASE_LEVEL
        if level != BASE_LEVEL:
            overlay.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "raw_self_ref": pointer,
                    "level": level,
                }
            )
    overlay.sort(key=lambda record: str(record["raw_self_ref"]))
    return base, overlay


def apply_heading_overlay(
    base_document: JsonObject,
    overlay: list[JsonObject],
) -> JsonObject:
    """Apply one strict overlay to a detached baseline document."""
    document = copy.deepcopy(base_document)
    by_pointer: dict[str, JsonObject] = {}
    for item in _objects(document):
        pointer = item.get("self_ref")
        if isinstance(pointer, str):
            by_pointer[pointer] = item
    seen: set[str] = set()
    for record in overlay:
        if record.get("schema_version") != SCHEMA_VERSION:
            raise HierarchyInferenceContractError("heading overlay schema differs")
        pointer = record.get("raw_self_ref")
        level = record.get("level")
        if (
            not isinstance(pointer, str)
            or pointer in seen
            or pointer not in by_pointer
            or not isinstance(level, int)
            or not 1 <= level <= 6
        ):
            raise HierarchyInferenceContractError("heading overlay entry is invalid")
        if not isinstance(by_pointer[pointer].get("level"), int):
            raise HierarchyInferenceContractError("heading overlay target has no base level")
        by_pointer[pointer]["level"] = level
        seen.add(pointer)
    return document


def _objects(value: Any) -> Iterator[JsonObject]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


__all__ = [
    "BASE_LEVEL",
    "SCHEMA_VERSION",
    "apply_heading_overlay",
    "split_heading_overlay",
]
