"""Bounded PDFium evidence access for an explicitly authorized page range."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Final

import pypdfium2 as pdfium  # type: ignore[import-untyped]
import pypdfium2.raw as pdfium_c  # type: ignore[import-untyped]

from er_commons.response_inventory.observations import LineObservation, PageObservation

_SECTION_RE: Final = re.compile(
    r"^\s*(?:\d+(?:\.\d+){1,3}\s+)?(?:RESPONSES\s+TO|LETTER\s+|TRANSCRIPT\s+|"
    r"GENERAL\s+RESPONSES?\b|CHAPTER\s+(?:\d+|[IVXLCDM]+)\b|"
    r"CONTENTS(?:\s*\([^\r\n)]+\))?\s*$)",
    re.IGNORECASE,
)
_NUMBERED_HEADING_RE: Final = re.compile(r"^\s*\d+(?:\.\d+){1,4}\s+[A-Z][A-Z\s&/(),'-]+$")
_RUNNING_CONTEXT_RE: Final = re.compile(
    r"\b(?:responses?\s+to|general\s+response|letter|transcript)\b", re.IGNORECASE
)
_TITLE_PAGE_REQUIRED_RE: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?:Final\s+)?Environmental\s+Impact\s+Report", re.IGNORECASE),
    re.compile(r"Prepared\s+for", re.IGNORECASE),
    re.compile(r"Prepared\s+by", re.IGNORECASE),
)
_ZERO_COMMENT_RE: Final = re.compile(r"\bno\s+comments?\s+(?:were\s+)?received\b", re.IGNORECASE)
_LABELED_BLANK_RE: Final = re.compile(r"intentionally\s+(?:left\s+)?blank", re.IGNORECASE)
_FIGURE_TABLE_RE: Final = re.compile(r"^\s*(?:Figure|Table)\s+[A-Z0-9.-]+", re.IGNORECASE)
_MIN_LARGE_IMAGE_PAGE_AREA_RATIO: Final = 0.15

type RuleBox = tuple[tuple[float, float, float, float], bool]

LOGGER = logging.getLogger(__name__)


def read_pdfium_range(pdf_path: Path, first_page: int, last_page: int) -> list[PageObservation]:
    """Read only one authorized inclusive physical-page range and close all handles."""
    if first_page < 1 or last_page < first_page:
        raise ValueError("invalid authorized PDF page range")
    document = pdfium.PdfDocument(pdf_path)
    observations: list[PageObservation] = []
    try:
        if last_page > len(document):
            raise ValueError("authorized PDF page range exceeds the document")
        for physical_page in range(first_page, last_page + 1):
            if physical_page == first_page or physical_page % 25 == 0 or physical_page == last_page:
                LOGGER.info(
                    "PDFium page %d/%d in authorized range %d-%d",
                    physical_page,
                    last_page,
                    first_page,
                    last_page,
                )
            page = document[physical_page - 1]
            text_page = page.get_textpage()
            try:
                observations.append(_observe_page(physical_page, page, text_page))
            finally:
                text_page.close()
                page.close()
    finally:
        document.close()
    return observations


def _observe_page(physical_page: int, page: Any, text_page: Any) -> PageObservation:
    left, bottom, right, top = (float(value) for value in page.get_bbox())
    raw_text = str(text_page.get_text_bounded(left, bottom, right, top))
    rules = tuple(_horizontal_rules(page))
    lines = tuple(_line_observations(raw_text, text_page, rules, (left, bottom, right, top)))
    normalized = " ".join(raw_text.split())
    title_page = all(pattern.search(normalized) for pattern in _TITLE_PAGE_REQUIRED_RE)
    section_opener = _has_bold_section_heading(raw_text, lines)
    running_header_context = any(
        "|" in _line_text(raw_text, line) and _RUNNING_CONTEXT_RE.search(_line_text(raw_text, line))
        for line in lines[:3]
    )
    figure_or_table = _has_styled_figure_table_heading(raw_text, lines) or _has_large_image(
        page, (left, bottom, right, top)
    )
    return PageObservation(
        physical_page=physical_page,
        raw_text=raw_text,
        width_points=right - left,
        height_points=top - bottom,
        rotation=int(page.get_rotation()),
        character_slot_count=int(text_page.count_chars()),
        lines=lines,
        labeled_blank=bool(_LABELED_BLANK_RE.search(normalized)),
        section_opener=section_opener,
        running_header_context=running_header_context,
        zero_comment_section=bool(_ZERO_COMMENT_RE.search(normalized)),
        figure_or_table=figure_or_table,
        revision_markup=any(line.revision_marks for line in lines),
        title_page=title_page,
    )


def _line_observations(
    raw_text: str,
    text_page: Any,
    rules: tuple[RuleBox, ...],
    page_box: tuple[float, float, float, float],
) -> Iterator[LineObservation]:
    search_index = 0
    for line_index, (text_start, text_end) in enumerate(_line_intervals(raw_text)):
        line_text = raw_text[text_start:text_end]
        query = line_text.strip()
        slot_start: int | None = None
        slot_end: int | None = None
        bbox = page_box
        has_character_geometry = False
        bold = italic = False
        if query:
            searcher = text_page.search(query, index=search_index, match_case=True)
            try:
                occurrence = searcher.get_next()
            finally:
                searcher.close()
            if occurrence is not None:
                slot_start, count = (int(value) for value in occurrence)
                slot_end = slot_start + count
                search_index = slot_end
                boxes = tuple(_safe_charboxes(text_page, slot_start, slot_end))
                if boxes:
                    bbox = _union_boxes(boxes)
                    has_character_geometry = True
                bold, italic = _font_style(text_page, slot_start, slot_end)
        solid_rule, dotted_rule = (
            _rule_flags(bbox, rules) if has_character_geometry else (False, False)
        )
        revision_marks = _revision_marks(
            bbox,
            rules,
            solid_rule,
            dotted_rule,
            has_character_geometry=has_character_geometry,
        )
        yield LineObservation(
            line_index=line_index,
            text_start=text_start,
            text_end=text_end,
            bbox=bbox,
            character_slot_start=slot_start,
            character_slot_end=slot_end,
            bold=bold,
            italic=italic,
            solid_rule=solid_rule,
            dotted_rule=dotted_rule,
            revision_marks=revision_marks,
        )


def _line_intervals(text: str) -> Iterator[tuple[int, int]]:
    offset = 0
    for value in text.splitlines(keepends=True):
        content = value.rstrip("\r\n")
        yield offset, offset + len(content)
        offset += len(value)
    if not text:
        return
    if offset < len(text):
        yield offset, len(text)


def _safe_charboxes(
    text_page: Any, start: int, end: int
) -> Iterator[tuple[float, float, float, float]]:
    for index in range(start, end):
        try:
            values = tuple(float(value) for value in text_page.get_charbox(index))
        except Exception:  # pragma: no cover - PDFium defects are source-dependent
            continue
        if len(values) != 4:
            continue
        box = (values[0], values[1], values[2], values[3])
        if box[2] >= box[0] and box[3] >= box[1]:
            yield box


def _union_boxes(
    boxes: Iterable[tuple[float, float, float, float]],
) -> tuple[float, float, float, float]:
    materialized = tuple(boxes)
    return (
        min(box[0] for box in materialized),
        min(box[1] for box in materialized),
        max(box[2] for box in materialized),
        max(box[3] for box in materialized),
    )


def _font_style(text_page: Any, start: int, end: int) -> tuple[bool, bool]:
    bold = italic = False
    indexes = sorted({start, max(start, end - 1), start + max(0, end - start - 1) // 2})
    for index in indexes:
        text_object = text_page.get_textobj(index)
        if text_object is None:
            continue
        font = text_object.get_font()
        name = " ".join(
            str(value) for value in (font.get_base_name(), font.get_family_name()) if value
        ).casefold()
        bold = bold or int(font.get_weight()) >= 600 or "bold" in name
        italic = italic or "italic" in name or "oblique" in name
    return bold, italic


def _horizontal_rules(page: Any) -> Iterator[RuleBox]:
    for item in page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_PATH]):
        try:
            values = tuple(float(value) for value in item.get_bounds())
            dash_count = int(pdfium_c.FPDFPageObj_GetDashCount(item.raw))
        except Exception:  # pragma: no cover - malformed path objects are source-dependent
            continue
        if len(values) != 4:
            continue
        box = (values[0], values[1], values[2], values[3])
        width = box[2] - box[0]
        height = box[3] - box[1]
        if width >= 8.0 and height <= 3.0:
            yield box, dash_count > 0


def _rule_flags(
    text_box: tuple[float, float, float, float], rules: tuple[RuleBox, ...]
) -> tuple[bool, bool]:
    solid = dotted = False
    for rule, is_dotted in rules:
        horizontal_overlap = min(text_box[2], rule[2]) - max(text_box[0], rule[0])
        vertical_distance = min(abs(rule[1] - text_box[1]), abs(rule[3] - text_box[1]))
        if horizontal_overlap > 0 and vertical_distance <= 12.0:
            dotted = dotted or is_dotted
            solid = solid or not is_dotted
    return solid, dotted


def _revision_marks(
    text_box: tuple[float, float, float, float],
    rules: tuple[RuleBox, ...],
    solid_rule: bool,
    dotted_rule: bool,
    *,
    has_character_geometry: bool = True,
) -> tuple[str, ...]:
    """Classify revision rules only against located character geometry."""
    if not has_character_geometry or solid_rule or dotted_rule:
        return ()
    marks: set[str] = set()
    height = max(1.0, text_box[3] - text_box[1])
    for rule, _ in rules:
        overlap = min(text_box[2], rule[2]) - max(text_box[0], rule[0])
        if overlap <= 0:
            continue
        relative_y = (rule[1] - text_box[1]) / height
        if -0.2 <= relative_y <= 0.25:
            marks.add("underline")
        elif 0.3 <= relative_y <= 0.7:
            marks.add("strikethrough")
    return tuple(sorted(marks))


def _has_styled_figure_table_heading(raw_text: str, lines: Iterable[LineObservation]) -> bool:
    """Recognize a styled heading or a dense figure/table listing."""
    matching_lines: list[tuple[LineObservation, str]] = []
    for line in lines:
        text = _line_text(raw_text, line).strip()
        if _FIGURE_TABLE_RE.match(text):
            matching_lines.append((line, text))
    if len(matching_lines) >= 2:
        return True
    for line, text in matching_lines:
        letters = "".join(character for character in text if character.isalpha())
        if line.bold or (letters and letters.isupper()):
            return True
    return False


def _has_bold_section_heading(raw_text: str, lines: Iterable[LineObservation]) -> bool:
    """Require both structural section text and observed bold font evidence."""
    return any(
        line.bold
        and (
            _SECTION_RE.match(_line_text(raw_text, line))
            or _NUMBERED_HEADING_RE.match(_line_text(raw_text, line))
        )
        for line in lines
    )


def _has_large_image(
    page: Any,
    page_box: tuple[float, float, float, float],
    *,
    minimum_area_ratio: float = _MIN_LARGE_IMAGE_PAGE_AREA_RATIO,
) -> bool:
    """Return whether an embedded image covers a meaningful part of the page."""
    page_left, page_bottom, page_right, page_top = page_box
    page_area = max(0.0, page_right - page_left) * max(0.0, page_top - page_bottom)
    if page_area <= 0.0:
        return False
    for item in page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]):
        try:
            left, bottom, right, top = (float(value) for value in item.get_bounds())
        except Exception:  # pragma: no cover - malformed image objects are source-dependent
            continue
        clipped_width = max(0.0, min(right, page_right) - max(left, page_left))
        clipped_height = max(0.0, min(top, page_top) - max(bottom, page_bottom))
        if clipped_width * clipped_height / page_area >= minimum_area_ratio:
            return True
    return False


def _line_text(raw_text: str, line: LineObservation) -> str:
    return raw_text[line.text_start : line.text_end]


__all__ = ["read_pdfium_range"]
