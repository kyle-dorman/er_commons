"""Parse source-owned visible-TOC items into deterministic row records."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    normalize_text,
    parse_numbering,
)
from er_commons.hierarchy_inference.toc_regions import TocRegion
from er_commons.hierarchy_inference.toc_text import typographic_canonical

JsonObject = dict[str, Any]

_CONTINUED = "table of contents (continued)"
_ROW_MARKER = re.compile(
    r"^(?:(?:Article|ARTICLE) [0-9IVXLCDM]+\.?|[0-9]+(?:\.[0-9]+){0,5}\.?|Appendix [A-Z])$"
)
_LEADER = re.compile(r"^\.+$")
_PAGE_TOKEN = re.compile(r"^[A-Za-z]?[0-9]+(?:-[0-9]+)?$")
_TRAILING_DIGITS = re.compile(r"\S[0-9]+$")
_APPENDIX_MARKER = re.compile(r"^Appendix [A-Z]$")


def parse_toc_region(
    features: list[JsonObject],
    region: TocRegion,
    outlines: tuple[JsonObject, ...],
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Parse one detected region with an explicit marker/title/leader state."""
    items = [
        item for item in features[region.start + 1 : region.end] if item["content_layer"] == "body"
    ]
    entries: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    current: list[JsonObject] = []
    marker: str | None = None
    titles: list[JsonObject] = []
    in_leader = False

    def abandon(detail: str) -> None:
        nonlocal current, marker, titles, in_leader
        diagnostics.extend(_diagnostic(item, "TOC_ROW_UNPARSEABLE", detail) for item in current)
        current, marker, titles, in_leader = [], None, [], False

    def emit(page: str | None) -> None:
        nonlocal current, marker, titles, in_leader
        if not titles:
            abandon("TOC row has no title")
            return
        if marker is None and page is None and not in_leader:
            abandon("unmarked TOC row lacks leader and terminal page")
            return
        if _APPENDIX_MARKER.fullmatch(marker or "") is None and any(
            _TRAILING_DIGITS.search(normalize_text(item["text"], casefold=False)) for item in titles
        ):
            abandon("TOC title contains inseparable trailing digits")
            return
        entries.append(_entry(current, marker, titles, page, outlines))
        current, marker, titles, in_leader = [], None, [], False

    for offset, item in enumerate(items):
        normalized = normalize_text(item["text"], casefold=False)
        if item["raw_role"] == "section_header":
            if normalize_text(item["text"]) == _CONTINUED:
                if current:
                    abandon("continued TOC heading interrupts a row")
                continue
            if _APPENDIX_MARKER.fullmatch(normalized):
                if current:
                    emit(None)
                current = [item]
                marker = normalized
                continue
            if current:
                emit(None)
            diagnostics.append(
                _diagnostic(item, "TOC_ROW_UNPARSEABLE", "unexpected heading in TOC")
            )
            continue
        is_marker = _ROW_MARKER.fullmatch(normalized) is not None and _marker_has_title_ahead(
            items, offset, current=bool(current), in_leader=in_leader
        )
        is_leader = _LEADER.fullmatch(normalized) is not None
        is_page = _PAGE_TOKEN.fullmatch(normalized) is not None
        if not current:
            current = [item]
            if is_marker:
                marker = normalized
            elif not is_leader and not is_page:
                titles = [item]
            else:
                abandon("TOC row starts without marker or title")
            continue
        if (
            marker is not None
            and not titles
            and normalized == "."
            and _is_adjacent_marker_period(current[-1], item, marker)
        ):
            current.append(item)
            marker = f"{marker}."
            continue
        if in_leader:
            current.append(item)
            if is_leader:
                continue
            if is_page:
                emit(normalized)
            else:
                abandon("TOC leader is not followed by one page token")
            continue
        if is_marker:
            emit(None)
            current = [item]
            marker = normalized
        elif is_leader:
            current.append(item)
            in_leader = True
        elif is_page:
            current.append(item)
            abandon("TOC row has a page token before its leader")
        else:
            current.append(item)
            titles.append(item)
    if current:
        emit(None)
    return entries, diagnostics


def _is_adjacent_marker_period(
    marker_item: JsonObject, period_item: JsonObject, marker: str
) -> bool:
    """Accept one split terminal period only with tight baseline geometry."""
    if marker.endswith(".") or re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,5}", marker) is None:
        return False
    marker_box = marker_item["bbox"]
    period_box = period_item["bbox"]
    return bool(
        marker_item["physical_page"] == period_item["physical_page"]
        and marker_item["reading_order_index"] + 1 == period_item["reading_order_index"]
        and 0 <= period_box["l"] - marker_box["r"] <= 3.0
        and abs(period_box["b"] - marker_box["b"]) <= 1.0
    )


def _entry(
    source: list[JsonObject],
    marker: str | None,
    titles: list[JsonObject],
    page: str | None,
    outlines: tuple[JsonObject, ...],
) -> JsonObject:
    title = normalize_text(" ".join(item["text"] for item in titles))
    title_with_marker = normalize_text(" ".join(filter(None, (marker, title))))
    outline_levels = {
        item["effective_level"]
        for item in outlines
        if item["normalized_title"] == title_with_marker
    }
    if not outline_levels:
        outline_levels = {
            item["effective_level"]
            for item in outlines
            if typographic_canonical(item["normalized_title"])
            == typographic_canonical(title_with_marker)
        }
    numbering = parse_numbering(f"{marker} title", raw_role="section_header") if marker else None
    if len(outline_levels) == 1:
        depth, depth_source = next(iter(outline_levels)), "outline"
    elif numbering is not None and numbering.depth is not None:
        depth, depth_source = numbering.depth, "numbering"
    else:
        depth, depth_source = 1, "default"
    identity = {
        "source_item_keys": [item["stable_item_key"] for item in source],
        "reading_order_index": source[0]["reading_order_index"],
    }
    return {
        "toc_entry_id": f"toc-{_digest16(identity)}",
        "source_item_keys": identity["source_item_keys"],
        "reading_order_index": identity["reading_order_index"],
        "physical_page": source[0]["physical_page"],
        "bbox": _union_bbox(source),
        "title_with_marker_normalized": title_with_marker,
        "title_without_marker_normalized": title,
        "numbering_token": _marker_token(marker) if marker is not None else None,
        "depth": depth,
        "depth_source": depth_source,
        "printed_page": page,
        "parser_state": "complete" if page is not None else "missing_printed_page",
        "boundary_eligible": False,
    }


def _marker_has_title_ahead(
    items: list[JsonObject],
    offset: int,
    *,
    current: bool,
    in_leader: bool,
) -> bool:
    """Disambiguate numeric markers from page tokens using complete row lookahead."""
    marker_text = normalize_text(items[offset]["text"], casefold=False)
    if current and in_leader and _PAGE_TOKEN.fullmatch(marker_text):
        return False
    numeric_marker = re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,5}\.?", marker_text) is not None
    appendix_marker = _APPENDIX_MARKER.fullmatch(marker_text) is not None
    saw_title = False
    for later_offset, later in enumerate(items[offset + 1 :], start=offset + 1):
        text = normalize_text(later["text"], casefold=False)
        if (
            later_offset == offset + 1
            and text == "."
            and _is_adjacent_marker_period(items[offset], later, marker_text)
        ):
            continue
        if _LEADER.fullmatch(text):
            return saw_title
        if _PAGE_TOKEN.fullmatch(text):
            return False
        if _ROW_MARKER.fullmatch(text):
            return saw_title and not numeric_marker
        if later["raw_role"] == "section_header":
            return saw_title and appendix_marker
        saw_title = True
    return saw_title and not numeric_marker


def _marker_token(marker: str) -> str:
    evidence = parse_numbering(f"{marker} title", raw_role="section_header")
    return evidence.token if evidence.token is not None else marker


def _union_bbox(source: list[JsonObject]) -> JsonObject:
    boxes = [item["bbox"] for item in source]
    return {
        "l": min(item["l"] for item in boxes),
        "t": max(item["t"] for item in boxes),
        "r": max(item["r"] for item in boxes),
        "b": min(item["b"] for item in boxes),
        "coord_origin": "BOTTOMLEFT",
    }


def _diagnostic(feature: JsonObject, code: str, detail: str) -> JsonObject:
    return {
        "reading_order_index": feature["reading_order_index"],
        "stable_item_key": feature["stable_item_key"],
        "code": code,
        "detail": detail,
    }


def _digest16(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()[:16]
