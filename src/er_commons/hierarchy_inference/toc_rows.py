"""Parse source-owned visible-TOC items into deterministic row records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    normalize_text,
    parse_numbering,
)
from er_commons.hierarchy_inference.toc_regions import TocRegion
from er_commons.hierarchy_inference.toc_text import split_inline_leader, typographic_canonical

JsonObject = dict[str, Any]

_CONTINUED = "table of contents (continued)"
_ROW_MARKER = re.compile(
    r"^(?:(?:Article|ARTICLE) [0-9IVXLCDM]+\.?|[0-9]+(?:\.[0-9]+){0,5}\.?|Appendix [A-Z])$"
)
_LEADER = re.compile(r"^\.+$")
_PAGE_TOKEN = re.compile(r"^[A-Za-z]?[0-9]+(?:-[0-9]+)?$")
_TRAILING_DIGITS = re.compile(r"\S[0-9]+$")
_APPENDIX_MARKER = re.compile(r"^Appendix [A-Z]$")


@dataclass(frozen=True)
class TocItemClassification:
    """Lexical roles relevant to one TOC parser transition."""

    normalized: str
    is_marker: bool
    is_leader: bool
    inline_title: str | None
    is_page: bool


@dataclass
class TocRowParser:
    """Mutable marker/title/leader state for one detected TOC region."""

    items: list[JsonObject]
    outlines: tuple[JsonObject, ...]
    entries: list[JsonObject] = field(default_factory=list)
    diagnostics: list[JsonObject] = field(default_factory=list)
    current: list[JsonObject] = field(default_factory=list)
    marker: str | None = None
    titles: list[JsonObject] = field(default_factory=list)
    in_leader: bool = False

    def parse(self) -> tuple[list[JsonObject], list[JsonObject]]:
        """Consume all region items and flush the terminal partial row."""
        for offset, item in enumerate(self.items):
            self._consume(offset, item)
        if self.current:
            self._emit(None)
        return self.entries, self.diagnostics

    def _consume(self, offset: int, item: JsonObject) -> None:
        """Route one item through heading, row-start, and active-row transitions."""
        normalized = normalize_text(item["text"], casefold=False)
        if item["raw_role"] == "section_header":
            self._consume_heading(item, normalized)
            return
        classification = self._classify(offset, normalized)
        if not self.current:
            self._start_row(item, classification)
        elif self._consume_split_marker_period(item, classification.normalized):
            return
        elif self.in_leader:
            self._consume_leader_item(item, classification)
        else:
            self._consume_row_item(item, classification)

    def _classify(self, offset: int, normalized: str) -> TocItemClassification:
        """Classify one non-heading item using complete-row lookahead."""
        return TocItemClassification(
            normalized=normalized,
            is_marker=_ROW_MARKER.fullmatch(normalized) is not None
            and _marker_has_title_ahead(
                self.items,
                offset,
                current=bool(self.current),
                in_leader=self.in_leader,
            ),
            is_leader=_LEADER.fullmatch(normalized) is not None,
            inline_title=split_inline_leader(normalized),
            is_page=_PAGE_TOKEN.fullmatch(normalized) is not None,
        )

    def _consume_heading(self, item: JsonObject, normalized: str) -> None:
        """Handle continued headings, appendix markers, and invalid headings."""
        if normalize_text(item["text"]) == _CONTINUED:
            if self.current:
                self._abandon("continued TOC heading interrupts a row")
            return
        if _APPENDIX_MARKER.fullmatch(normalized):
            if self.current:
                self._emit(None)
            self.current = [item]
            self.marker = normalized
            return
        if self.current:
            self._emit(None)
        self.diagnostics.append(
            _diagnostic(item, "TOC_ROW_UNPARSEABLE", "unexpected heading in TOC")
        )

    def _start_row(self, item: JsonObject, value: TocItemClassification) -> None:
        """Initialize a row only from a marker or title-bearing item."""
        self.current = [item]
        if value.is_marker:
            self.marker = value.normalized
        elif value.inline_title is not None:
            self.titles = [item]
            self.in_leader = True
        elif not value.is_leader and not value.is_page:
            self.titles = [item]
        else:
            self._abandon("TOC row starts without marker or title")

    def _consume_split_marker_period(self, item: JsonObject, normalized: str) -> bool:
        """Attach a geometrically adjacent period to a numeric marker."""
        if (
            self.marker is not None
            and not self.titles
            and normalized == "."
            and _is_adjacent_marker_period(self.current[-1], item, self.marker)
        ):
            self.current.append(item)
            self.marker = f"{self.marker}."
            return True
        return False

    def _consume_leader_item(self, item: JsonObject, value: TocItemClassification) -> None:
        """Require a leader to terminate in exactly one page token."""
        self.current.append(item)
        if value.is_leader:
            return
        if value.is_page:
            self._emit(value.normalized)
        else:
            self._abandon("TOC leader is not followed by one page token")

    def _consume_row_item(self, item: JsonObject, value: TocItemClassification) -> None:
        """Advance an active marker/title row before its terminal page."""
        if value.is_marker:
            self._emit(None)
            self.current = [item]
            self.marker = value.normalized
        elif value.is_leader:
            self.current.append(item)
            self.in_leader = True
        elif value.inline_title is not None:
            self.current.append(item)
            self.titles.append(item)
            self.in_leader = True
        elif value.is_page:
            self.current.append(item)
            self._abandon("TOC row has a page token before its leader")
        else:
            self.current.append(item)
            self.titles.append(item)

    def _emit(self, page: str | None) -> None:
        """Validate and serialize the current row, or abandon it with evidence."""
        if not self.titles:
            self._abandon("TOC row has no title")
            return
        if self.marker is None and page is None and not self.in_leader:
            self._abandon("unmarked TOC row lacks leader and terminal page")
            return
        if _APPENDIX_MARKER.fullmatch(self.marker or "") is None and any(
            _TRAILING_DIGITS.search(normalize_text(item["text"], casefold=False))
            for item in self.titles
        ):
            self._abandon("TOC title contains inseparable trailing digits")
            return
        self.entries.append(_entry(self.current, self.marker, self.titles, page, self.outlines))
        self._reset()

    def _abandon(self, detail: str) -> None:
        """Emit one contextual diagnostic per source item and reset the row."""
        self.diagnostics.extend(
            _diagnostic(item, "TOC_ROW_UNPARSEABLE", detail) for item in self.current
        )
        self._reset()

    def _reset(self) -> None:
        """Restore the empty parser state after an emitted or rejected row."""
        self.current = []
        self.marker = None
        self.titles = []
        self.in_leader = False


def parse_toc_region(
    features: list[JsonObject],
    region: TocRegion,
    outlines: tuple[JsonObject, ...],
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Parse one detected region with an explicit marker/title/leader state."""
    items = [
        item for item in features[region.start + 1 : region.end] if item["content_layer"] == "body"
    ]
    return TocRowParser(items, outlines).parse()


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
    title = normalize_text(
        " ".join(split_inline_leader(item["text"]) or item["text"] for item in titles)
    )
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
