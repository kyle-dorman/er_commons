"""Project saved producer geometry and lineage without repairing raw evidence."""

from __future__ import annotations

import math
from dataclasses import dataclass

from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.record_sets import JsonRecord


@dataclass(frozen=True)
class ProvenanceProjection:
    """Valid canonical regions and rejected producer provenance for one item."""

    regions: tuple[JsonRecord, ...]
    rejected: tuple[JsonRecord, ...]


def project_regions(
    *,
    item: JsonRecord,
    pointer: str,
    page_ids: dict[int, str],
    page_sizes: dict[int, tuple[float, float]],
) -> ProvenanceProjection:
    """Retain valid regions and report invalid entries verbatim."""
    regions: list[JsonRecord] = []
    rejected: list[JsonRecord] = []
    for index, provenance in enumerate(item.get("prov", [])):
        page = provenance.get("page_no")
        bbox = provenance.get("bbox", {})
        reason: str | None = None
        if page not in page_sizes:
            reason = "unknown_page"
        values = [bbox.get(name) for name in ("l", "b", "r", "t")]
        if reason is None and not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            for value in values
        ):
            reason = "non_finite_or_missing_bbox"
        if reason is None:
            left, lower, right, upper = (float(value) for value in values)
            width, height = page_sizes[int(page)]
            if not (0 <= left < right <= width and 0 <= lower < upper <= height):
                reason = "out_of_page_bounds"
        if reason is not None:
            rejected.append(
                {
                    "raw_object_pointer": pointer,
                    "provenance_index": index,
                    "rejection_reason": reason,
                    "raw_provenance": provenance,
                }
            )
            continue
        regions.append(
            {
                "page_id": page_ids[int(page)],
                "coordinate_space": "producer_pdf",
                "origin": "bottom_left",
                "units": "pdf_points",
                "bbox": [left, lower, right, upper],
                "page_width": width,
                "page_height": height,
                "rotation_degrees": 0,
                "render_scale": None,
                "affine_transform": None,
            }
        )
    return ProvenanceProjection(tuple(regions), tuple(rejected))


def table_region(
    bbox: tuple[float, float, float, float] | list[float],
    physical_page: int,
    page_ids: dict[int, str],
    page_sizes: dict[int, tuple[float, float]],
) -> JsonRecord:
    """Build one bottom-left table or cell region in canonical shape."""
    width, height = page_sizes[physical_page]
    return {
        "page_id": page_ids[physical_page],
        "coordinate_space": "producer_pdf",
        "origin": "bottom_left",
        "units": "pdf_points",
        "bbox": [float(value) for value in bbox],
        "page_width": width,
        "page_height": height,
        "rotation_degrees": 0,
        "render_scale": None,
        "affine_transform": None,
    }


def descendant_text_pointers(
    document: JsonRecord,
    roots: list[JsonRecord],
) -> set[str]:
    """Collect descendant text pointers while rejecting producer graph cycles."""
    texts: set[str] = set()
    active: set[str] = set()

    def visit(pointer: str) -> None:
        parts = pointer.split("/")
        if len(parts) != 3 or parts[0] != "#" or not parts[2].isdigit():
            raise ContractError(f"unsupported descendant pointer: {pointer}")
        collection, index = parts[1], int(parts[2])
        if collection == "texts":
            texts.add(pointer)
            return
        values = document.get(collection)
        if not isinstance(values, list) or index >= len(values):
            raise ContractError(f"unknown descendant pointer: {pointer}")
        if pointer in active:
            raise ContractError(f"descendant cycle: {pointer}")
        active.add(pointer)
        for child in values[index].get("children", []):
            visit(child["$ref"])
        active.remove(pointer)

    for root in roots:
        visit(root["$ref"])
    return texts
