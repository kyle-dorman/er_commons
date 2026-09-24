"""Bounded full-ID response lists with independently verifiable prefix evidence."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

LIST_ITEM_RULE = "explicit_response_list_item_v1"
# A full individual ID has a letter-led submission code and a numbered suffix.
_ID = r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z][A-Za-z0-9]*)*-\d+[A-Za-z]?"
_PREFIX = re.compile(r"\bResponses?\s+", re.IGNORECASE)
_ITEM = re.compile(rf"{_ID}(?![A-Za-z0-9_/-]|\.[A-Za-z0-9])")
_RANGE = re.compile(r"\s*(?:(?:through|to)\b|[-–—])", re.IGNORECASE)
_SEPARATOR = re.compile(r"(?:\s*,\s*(?:(?:and|or)\s+)?|\s+(?:and|or)\s+)", re.IGNORECASE)


@dataclass(frozen=True)
class ResponseListItem:
    """Raw offsets into one source fragment; no invented prefix or target text."""

    prefix_start: int
    prefix_end: int
    item_start: int
    item_end: int


def response_list_items(text: str) -> Iterator[ResponseListItem]:
    """Yield new plural/shared-prefix items; leave existing singular first items alone.

    Commas, and/or conjunctions, and line wrapping are supported. Bare numbers,
    ranges, abbreviations, and prose never supply inferred endpoints.
    """
    for prefix in _PREFIX.finditer(text):
        item = _ITEM.match(text, prefix.end())
        first = True
        while item is not None:
            if _RANGE.match(text, item.end()):
                break
            if not first or prefix.group().strip().casefold() == "responses":
                yield ResponseListItem(*prefix.span(), *item.span())
            first = False
            separator = _SEPARATOR.match(text, item.end())
            item = _ITEM.match(text, separator.end()) if separator else None


def response_list_target(
    mention: Mapping[str, Any],
    spans: Mapping[str, Mapping[str, Any]],
    pages: Mapping[str, Mapping[str, Any]],
) -> str | None:
    """Verify two raw fragments belong to the same explicit list and name its item."""
    span = spans.get(str(mention.get("mention_span_id", "")))
    if span is None:
        return None
    fragments = span["fragments"]
    if len(fragments) != 2:
        return None
    prefix, item = fragments
    if prefix["page_id"] != item["page_id"]:
        return None
    text = str(pages[prefix["page_id"]]["raw_text"])
    expected = ResponseListItem(
        prefix["text_start"], prefix["text_end"], item["text_start"], item["text_end"]
    )
    if expected not in response_list_items(text):
        return None
    prefix_text = text[expected.prefix_start : expected.prefix_end]
    item_text = text[expected.item_start : expected.item_end]
    if mention["target_labels"] != [prefix_text + item_text]:
        return None
    return "Response " + item_text
