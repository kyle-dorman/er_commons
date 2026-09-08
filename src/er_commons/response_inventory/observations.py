"""Typed page-local evidence consumed by the response-inventory parser."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LineObservation:
    """One raw-text line with PDF-point and style evidence kept separate."""

    line_index: int
    text_start: int
    text_end: int
    bbox: tuple[float, float, float, float]
    character_slot_start: int | None = None
    character_slot_end: int | None = None
    bold: bool = False
    italic: bool = False
    solid_rule: bool = False
    dotted_rule: bool = False
    revision_marks: tuple[str, ...] = ()


@dataclass(frozen=True)
class PageObservation:
    """Bounded native page evidence without normalized or inferred text."""

    physical_page: int
    raw_text: str
    width_points: float
    height_points: float
    rotation: int
    character_slot_count: int
    lines: tuple[LineObservation, ...]
    labeled_blank: bool = False
    section_opener: bool = False
    running_header_context: bool = False
    zero_comment_section: bool = False
    figure_or_table: bool = False
    revision_markup: bool = False
    title_page: bool = False
    closes_open_unit: bool = False


def observation_to_dict(observation: PageObservation) -> dict[str, Any]:
    """Serialize one observation without normalizing its source text."""
    return {
        "physical_page": observation.physical_page,
        "raw_text": observation.raw_text,
        "width_points": observation.width_points,
        "height_points": observation.height_points,
        "rotation": observation.rotation,
        "character_slot_count": observation.character_slot_count,
        "lines": [
            {
                "line_index": line.line_index,
                "text_start": line.text_start,
                "text_end": line.text_end,
                "bbox": list(line.bbox),
                "character_slot_start": line.character_slot_start,
                "character_slot_end": line.character_slot_end,
                "bold": line.bold,
                "italic": line.italic,
                "solid_rule": line.solid_rule,
                "dotted_rule": line.dotted_rule,
                "revision_marks": list(line.revision_marks),
            }
            for line in observation.lines
        ],
        "labeled_blank": observation.labeled_blank,
        "section_opener": observation.section_opener,
        "running_header_context": observation.running_header_context,
        "zero_comment_section": observation.zero_comment_section,
        "figure_or_table": observation.figure_or_table,
        "revision_markup": observation.revision_markup,
        "title_page": observation.title_page,
        "closes_open_unit": observation.closes_open_unit,
    }


def observation_from_dict(value: dict[str, Any]) -> PageObservation:
    """Load package-written cache evidence without coercing malformed values."""
    raw_text = _string(value, "raw_text")
    character_slot_count = _integer(value, "character_slot_count", minimum=0)
    raw_lines = value.get("lines")
    if not isinstance(raw_lines, list):
        raise ValueError("observation lines must be a list")
    lines = tuple(
        _line_from_dict(
            line,
            expected_index=index,
            raw_text=raw_text,
            slot_count=character_slot_count,
        )
        for index, line in enumerate(raw_lines)
    )
    return PageObservation(
        physical_page=_integer(value, "physical_page", minimum=1),
        raw_text=raw_text,
        width_points=_finite_number(value, "width_points", positive=True),
        height_points=_finite_number(value, "height_points", positive=True),
        rotation=_integer(value, "rotation"),
        character_slot_count=character_slot_count,
        lines=lines,
        labeled_blank=_boolean(value, "labeled_blank"),
        section_opener=_boolean(value, "section_opener"),
        running_header_context=_boolean(value, "running_header_context"),
        zero_comment_section=_boolean(value, "zero_comment_section"),
        figure_or_table=_boolean(value, "figure_or_table"),
        revision_markup=_boolean(value, "revision_markup"),
        title_page=_boolean(value, "title_page"),
        closes_open_unit=_boolean(value, "closes_open_unit"),
    )


def _line_from_dict(
    value: object, *, expected_index: int, raw_text: str, slot_count: int
) -> LineObservation:
    """Validate one cached line and its text/character coordinate intervals."""
    if not isinstance(value, dict):
        raise ValueError("observation line must be an object")
    line_index = _integer(value, "line_index", minimum=0)
    if line_index != expected_index:
        raise ValueError("observation line indices must be contiguous and ordered")
    text_start = _integer(value, "text_start", minimum=0)
    text_end = _integer(value, "text_end", minimum=0)
    if text_end < text_start or text_end > len(raw_text):
        raise ValueError("observation line text interval falls outside raw_text")
    bbox_value = value.get("bbox")
    if not isinstance(bbox_value, list) or len(bbox_value) != 4:
        raise ValueError("observation line bbox must contain four numbers")
    bbox_values = tuple(_finite_value(item, "observation line bbox") for item in bbox_value)
    bbox = (bbox_values[0], bbox_values[1], bbox_values[2], bbox_values[3])
    slot_start = _optional_int(value.get("character_slot_start"))
    slot_end = _optional_int(value.get("character_slot_end"))
    if (slot_start is None) != (slot_end is None):
        raise ValueError("observation character-slot bounds must both be present or null")
    if slot_start is not None and (
        slot_start < 0 or slot_end is None or slot_end < slot_start or slot_end > slot_count
    ):
        raise ValueError("observation character-slot interval is invalid")
    revision_marks = value.get("revision_marks")
    if not isinstance(revision_marks, list) or not all(
        isinstance(item, str) for item in revision_marks
    ):
        raise ValueError("observation revision_marks must be a list of strings")
    return LineObservation(
        line_index=line_index,
        text_start=text_start,
        text_end=text_end,
        bbox=bbox,
        character_slot_start=slot_start,
        character_slot_end=slot_end,
        bold=_boolean(value, "bold"),
        italic=_boolean(value, "italic"),
        solid_rule=_boolean(value, "solid_rule"),
        dotted_rule=_boolean(value, "dotted_rule"),
        revision_marks=tuple(revision_marks),
    )


def _string(value: dict[str, Any], field: str) -> str:
    item = value.get(field)
    if not isinstance(item, str):
        raise ValueError(f"observation {field} must be a string")
    return item


def _integer(value: dict[str, Any], field: str, *, minimum: int | None = None) -> int:
    item = value.get(field)
    if isinstance(item, bool) or not isinstance(item, int):
        raise ValueError(f"observation {field} must be an integer")
    if minimum is not None and item < minimum:
        raise ValueError(f"observation {field} must be at least {minimum}")
    return item


def _boolean(value: dict[str, Any], field: str) -> bool:
    item = value.get(field)
    if not isinstance(item, bool):
        raise ValueError(f"observation {field} must be a boolean")
    return item


def _finite_number(value: dict[str, Any], field: str, *, positive: bool = False) -> float:
    number = _finite_value(value.get(field), f"observation {field}")
    if positive and number <= 0:
        raise ValueError(f"observation {field} must be positive")
    return number


def _finite_value(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("observation character-slot index must be an integer or null")
    return value


__all__ = [
    "LineObservation",
    "PageObservation",
    "observation_from_dict",
    "observation_to_dict",
]
