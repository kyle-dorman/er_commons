"""Detect half-open visible-TOC regions from outline and page-label evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    normalize_text,
    parse_numbering,
)
from er_commons.hierarchy_inference.errors import HierarchyInferenceContractError
from er_commons.hierarchy_inference.toc_text import split_body_title, split_inline_leader

JsonObject = dict[str, Any]

_TOC_START = re.compile(r"^table of contents(?: \(continued\))?$")
_PAGE_OF = re.compile(r"^Page (?P<label>[A-Za-z]?[0-9]+) of [0-9]+$")
_STANDALONE_PAGE = re.compile(r"^(?:[ivxlcdm]+|[A-Za-z]?[0-9]+)$")


@dataclass(frozen=True)
class TocRegion:
    """One half-open visible-TOC interval and its optional outline owner."""

    start: int
    end: int
    candidate_end: int
    start_key: str
    outline_id: str | None
    outline_parent_id: str | None


def printed_page_observations(features: list[JsonObject]) -> dict[int, str]:
    """Resolve the contract's primary and fallback producer footer tokens."""
    primary: dict[int, set[str]] = {}
    fallback: dict[int, set[str]] = {}
    for feature in features:
        if feature["raw_role"] != "page_footer" or feature["content_layer"] != "furniture":
            continue
        page = feature["physical_page"]
        text = normalize_text(feature["text"], casefold=False)
        match = _PAGE_OF.fullmatch(text)
        if match is not None:
            primary.setdefault(page, set()).add(match.group("label"))
        elif _STANDALONE_PAGE.fullmatch(text):
            fallback.setdefault(page, set()).add(text)
    observations: dict[int, str] = {}
    for page in set(primary) | set(fallback):
        preferred = primary.get(page, set())
        secondary = fallback.get(page, set())
        if len(preferred) == 1:
            observations[page] = next(iter(preferred))
        elif not preferred and len(secondary) == 1:
            observations[page] = next(iter(secondary))
    return observations


def detect_toc_regions(
    features: list[JsonObject],
    outlines: tuple[JsonObject, ...],
    printed_pages: dict[int, str],
) -> tuple[TocRegion, ...]:
    """Locate every visible TOC and its permitted body-candidate interval."""
    regions: list[TocRegion] = []
    index = 0
    while index < len(features):
        feature = features[index]
        if not _is_toc_start(feature):
            index += 1
            continue
        matches = [
            item
            for item in outlines
            if item["normalized_title"] == feature["normalized_text"]
            and item["physical_page"] == feature["physical_page"]
        ]
        if len(matches) > 1:
            raise HierarchyInferenceContractError("visible TOC outline anchor is ambiguous")
        outline = matches[0] if matches else None
        end = (
            _primary_region_end(features, outlines, outline)
            if outline is not None
            else _embedded_region_end(features, index, printed_pages)
        )
        regions.append(
            TocRegion(
                start=index,
                end=end,
                candidate_end=(
                    _outline_subtree_end(features, outlines, outline["parent_outline_id"])
                    if outline is not None and outline["parent_outline_id"] is not None
                    else len(features)
                ),
                start_key=feature["stable_item_key"],
                outline_id=outline["outline_id"] if outline else None,
                outline_parent_id=outline["parent_outline_id"] if outline else None,
            )
        )
        index = end
    return tuple(regions)


def _outline_subtree_end(
    features: list[JsonObject], outlines: tuple[JsonObject, ...], parent_id: str
) -> int:
    parent_position = next(
        (index for index, item in enumerate(outlines) if item["outline_id"] == parent_id),
        None,
    )
    if parent_position is None:
        raise HierarchyInferenceContractError("visible TOC outline parent is missing")
    parent_depth = outlines[parent_position]["raw_depth"]
    boundary = next(
        (item for item in outlines[parent_position + 1 :] if item["raw_depth"] <= parent_depth),
        None,
    )
    if boundary is None:
        return len(features)
    return _first_body_index_on_or_after_page(features, boundary["physical_page"])


def _primary_region_end(
    features: list[JsonObject], outlines: tuple[JsonObject, ...], anchor: JsonObject
) -> int:
    anchor_position = next(
        index for index, item in enumerate(outlines) if item["outline_id"] == anchor["outline_id"]
    )
    later_pages = [
        item["physical_page"]
        for item in outlines[anchor_position + 1 :]
        if item["parent_outline_id"] == anchor["parent_outline_id"]
    ]
    if not later_pages:
        raise HierarchyInferenceContractError("primary visible TOC has no later outline sibling")
    return _first_body_index_on_or_after_page(features, min(later_pages))


def _embedded_region_end(
    features: list[JsonObject], start: int, printed_pages: dict[int, str]
) -> int:
    start_page = features[start]["physical_page"]
    start_label = printed_pages.get(start_page)
    if start_label is not None and re.fullmatch(r"[ivxlcdm]+", start_label):
        later_pages = {
            item["physical_page"] for item in features if item["physical_page"] > start_page
        }
        for page in sorted(later_pages):
            if printed_pages.get(page) == "1" and _page_has_numbered_reset_and_content(
                features, page
            ):
                return _first_body_index_on_or_after_page(features, page)
    provisional_titles = _provisional_row_titles(features, start + 1)
    for feature in features[start + 1 :]:
        if feature["content_layer"] != "body" or feature["raw_role"] != "section_header":
            continue
        _marker, title = split_body_title(feature)
        if title in provisional_titles and _heading_has_following_content(features, feature):
            return _first_body_index_on_or_after_page(features, int(feature["physical_page"]))
    raise HierarchyInferenceContractError("TOC_REGION_UNTERMINATED")


def _provisional_row_titles(features: list[JsonObject], start: int) -> set[str]:
    titles: set[str] = set()
    for feature in features[start:]:
        if _is_toc_start(feature) and feature["reading_order_index"] > start:
            break
        marker, title = split_body_title(feature)
        if marker and title:
            titles.add(title)
        inline_title = split_inline_leader(feature["text"])
        if inline_title is not None:
            titles.add(inline_title)
    return titles


def _page_has_numbered_reset_and_content(features: list[JsonObject], page: int) -> bool:
    """Require a reset heading and independently nonempty body content on the page."""
    page_items = [
        item
        for item in features
        if item["physical_page"] == page and item["content_layer"] == "body"
    ]
    has_reset = any(
        item["raw_role"] == "section_header"
        and (
            (evidence := parse_numbering(item["text"], raw_role=item["raw_role"])).kind == "article"
            or (evidence.kind == "decimal" and evidence.depth == 1)
        )
        for item in page_items
    )
    has_content = any(
        item["raw_role"] != "section_header" and normalize_text(item["text"]) for item in page_items
    )
    return has_reset and has_content


def _heading_has_following_content(features: list[JsonObject], heading: JsonObject) -> bool:
    order = heading["reading_order_index"]
    for item in features:
        if (
            item["reading_order_index"] <= order
            or item["physical_page"] != heading["physical_page"]
        ):
            continue
        if item["raw_role"] == "section_header":
            return False
        if item["content_layer"] == "body" and normalize_text(item["text"]):
            return True
    return False


def _first_body_index_on_or_after_page(features: list[JsonObject], page: int) -> int:
    for index, feature in enumerate(features):
        if feature["physical_page"] >= page and feature["content_layer"] == "body":
            return index
    raise HierarchyInferenceContractError("visible TOC endpoint has no body item")


def _is_toc_start(feature: JsonObject) -> bool:
    return bool(
        feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and _TOC_START.fullmatch(feature["normalized_text"]) is not None
    )
