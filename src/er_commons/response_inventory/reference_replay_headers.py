"""Identify section targets corroborated as running headers by canonical furniture."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, TypeGuard

type JsonObject = dict[str, Any]


def qualify_section_headers(
    *,
    source_id: str,
    candidate_id: str,
    blocks: list[JsonObject],
    sections: list[JsonObject],
    pages: list[JsonObject],
) -> dict[str, JsonObject]:
    """Return exclusion evidence, leaving canonical records and target choice untouched.

    The caller supplies complete, inventory-verified canonical streams and may
    use this evidence only to break an existing section collision when exactly
    one candidate survives. A body heading needs an independently classified
    furniture header on another physical page, with identical normalized text,
    page dimensions and coordinate conventions, and every bbox edge within one
    PDF point. Text equality alone never qualifies a target for exclusion.
    """
    by_block = _unique_records(blocks)
    by_page = _unique_records(pages)
    _unique_records(sections)
    headers: dict[tuple[str, str], list[tuple[JsonObject, JsonObject]]] = defaultdict(list)
    for block in blocks:
        if (
            block.get("block_type") != "page_header"
            or block.get("content_layer") != "furniture"
            or block.get("is_toc_row") is not False
        ):
            continue
        region = _region(block, by_page, source_id)
        text = _normalized_text(block)
        if region is not None and text:
            headers[(block["document_id"], text)].append((block, region))

    qualified: dict[str, JsonObject] = {}
    for section in sections:
        heading = by_block.get(str(section.get("heading_block_id")))
        if (
            heading is None
            or section.get("content_layer") != "body"
            or heading.get("block_type") != "heading"
            or heading.get("content_layer") != "body"
            or heading.get("is_toc_row") is not False
            or heading.get("document_id") != section.get("document_id")
            or heading.get("section_id") != section["id"]
        ):
            continue
        region = _region(heading, by_page, source_id)
        text = _normalized_text(heading)
        if region is None or not text:
            continue
        matches = [
            (header, other)
            for header, other in headers.get((heading["document_id"], text), [])
            if _same_header_geometry(region, other, by_page)
        ]
        if not matches:
            continue
        matches.sort(key=lambda pair: pair[0]["id"])
        qualified[section["id"]] = {
            "rule": "corroborated_canonical_running_header_v1",
            "source_id": source_id,
            "candidate_id": candidate_id,
            "target_id": section["id"],
            "document_id": section["document_id"],
            "heading_block_id": heading["id"],
            "normalized_text": text,
            "heading_region": dict(region),
            "bbox_tolerance_pdf_points": 1.0,
            "corroborating_headers": [
                {"block_id": header["id"], "region": dict(other)} for header, other in matches
            ],
            "evidence_record_ids": sorted(
                {section["id"], heading["id"], region["page_id"]}
                | {header["id"] for header, _ in matches}
                | {other["page_id"] for _, other in matches}
            ),
        }
    return dict(sorted(qualified.items()))


def _unique_records(rows: list[JsonObject]) -> dict[str, JsonObject]:
    """Reject missing or duplicate identities instead of silently replacing evidence."""
    result: dict[str, JsonObject] = {}
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in result:
            raise ValueError("missing or duplicate canonical evidence identity")
        result[record_id] = row
    return result


def _normalized_text(block: JsonObject) -> str:
    """Normalize case and whitespace only, without conflating different headings."""
    value = block.get("canonical_text")
    return " ".join(value.casefold().split()) if isinstance(value, str) else ""


def _finite(value: Any) -> TypeGuard[int | float]:
    """Exclude booleans and nonfinite coordinates from geometric evidence."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _region(block: JsonObject, pages: dict[str, JsonObject], source_id: str) -> JsonObject | None:
    """Require a single bounded PDF region agreeing with its canonical source page."""
    regions = block.get("regions")
    if not isinstance(regions, list) or len(regions) != 1 or not isinstance(regions[0], dict):
        return None
    region = regions[0]
    page = pages.get(str(region.get("page_id")))
    document = block.get("document_id")
    if (
        page is None
        or not isinstance(document, str)
        or not document.endswith("/document/" + source_id)
        or page.get("document_id") != document
        or region.get("coordinate_space") != "producer_pdf"
        or region.get("units") != "pdf_points"
        or region.get("origin") not in {"bottom_left", "top_left"}
        or region.get("affine_transform") is not None
        or region.get("render_scale") is not None
        or not _finite(region.get("rotation_degrees"))
        or region.get("rotation_degrees") != page.get("rotation_degrees")
    ):
        return None
    width, height = region.get("page_width"), region.get("page_height")
    bbox = region.get("bbox")
    if (
        not _finite(width)
        or not _finite(height)
        or width <= 0
        or height <= 0
        or width != page.get("width_pdf_points")
        or height != page.get("height_pdf_points")
        or not isinstance(bbox, list)
        or len(bbox) != 4
        or not all(_finite(value) for value in bbox)
        or not (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height)
    ):
        return None
    return region


def _same_header_geometry(
    left: JsonObject, right: JsonObject, pages: dict[str, JsonObject]
) -> bool:
    """Require independent physical pages and consistent coordinates before proximity."""
    first, second = pages[left["page_id"]], pages[right["page_id"]]
    physical = (first.get("physical_page_number"), second.get("physical_page_number"))
    return (
        left["page_id"] != right["page_id"]
        and all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in physical)
        and physical[0] != physical[1]
        and all(
            left[key] == right[key]
            for key in ("page_width", "page_height", "origin", "rotation_degrees")
        )
        and all(abs(a - b) <= 1.0 for a, b in zip(left["bbox"], right["bbox"], strict=True))
    )
