"""Pure structural rules shared by response production and validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from er_commons.response_inventory.task05d_policy import TASK05D_ALLOWED_WARNING_CODES

type JsonObject = dict[str, Any]

SOURCE_RESPONSE_HEADING_ABSENT: Final = TASK05D_ALLOWED_WARNING_CODES[0]
SOURCE_RESPONSE_HEADING_ABSENT_MESSAGE: Final = (
    "Source lacks the corresponding response heading; no response marker, span, "
    "continuation, or unit was synthesized."
)

_KIND_PREFIX_RE: Final = re.compile(r"^(?:comment|response)\s+(?:no\.\s*)?", re.IGNORECASE)
_TRAILING_NUMBER_RE: Final = re.compile(r"^(?P<prefix>.*?\D)(?P<number>[0-9]+)$")
_RESPONSE_STYLE: Final = {
    "bold": False,
    "italic": True,
    "solid_rule": False,
    "dotted_rule": True,
}


@dataclass(frozen=True)
class MissingResponseHeading:
    """One source-backed gap and the exact records that anchor it."""

    activity_id: str
    comment_unit_id: str
    evidence_ids: tuple[str, ...]


def paired_response_style_comment_marker_ids(
    records: Sequence[Mapping[str, Any]],
) -> frozenset[str]:
    """Return atypical comments proven as starts by an adjacent paired response."""
    pages = {
        str(record["page_id"]): record for record in records if record.get("record_type") == "page"
    }
    markers = sorted(
        (record for record in records if record.get("record_type") == "marker_candidate"),
        key=lambda record: (
            int(pages[str(record["page_id"])]["physical_page"]),
            int(record["text_start"]),
            str(record["marker_id"]),
        ),
    )
    accepted_units = [
        marker
        for marker in markers
        if marker.get("marker_kind") in {"comment", "response", "general_response"}
        and marker.get("disposition") == "unit_start"
    ]
    submission_boundaries = [
        marker
        for marker in markers
        if marker.get("marker_kind") == "submission"
        and marker.get("disposition") == "section_opener"
    ]
    promoted: set[str] = set()
    for marker in markers:
        if not _is_response_style_comment_candidate(marker, pages):
            continue
        page_id = str(marker["page_id"])
        start = int(marker["text_start"])
        following = [
            candidate
            for candidate in accepted_units
            if str(candidate["page_id"]) == page_id and int(candidate["text_start"]) > start
        ]
        if not following:
            continue
        paired = following[0]
        if paired.get("marker_kind") != "response" or _normalized_unit_code(
            str(marker["observed_label"])
        ) != _normalized_unit_code(str(paired["observed_label"])):
            continue
        paired_start = int(paired["text_start"])
        if any(
            str(boundary["page_id"]) == page_id
            and start < int(boundary["text_start"]) < paired_start
            for boundary in submission_boundaries
        ):
            continue
        promoted.add(str(marker["marker_id"]))
    return frozenset(promoted)


def missing_response_heading_gaps(
    records: Sequence[Mapping[str, Any]], activity_id: str
) -> tuple[MissingResponseHeading, ...]:
    """Derive every adjacent numbered comment whose response heading is absent."""
    pages = {
        str(record["page_id"]): record
        for record in records
        if record.get("record_type") == "page" and record.get("activity_id") == activity_id
    }
    markers = {
        str(record["marker_id"]): record
        for record in records
        if record.get("record_type") == "marker_candidate" and str(record.get("page_id")) in pages
    }
    units = [
        record
        for record in records
        if record.get("record_type") == "source_unit"
        and record.get("activity_id") == activity_id
        and record.get("unit_kind") in {"comment", "response"}
    ]

    def position(unit: Mapping[str, Any]) -> tuple[int, int, str]:
        marker = markers[str(unit["start_marker_id"])]
        page = pages[str(marker["page_id"])]
        return (
            int(page["physical_page"]),
            int(marker["text_start"]),
            str(unit["unit_id"]),
        )

    comments = sorted((unit for unit in units if unit["unit_kind"] == "comment"), key=position)
    responses = [unit for unit in units if unit["unit_kind"] == "response"]
    response_details = [
        (unit, _numbered_unit_label(str(unit["official_label"]), "response"), position(unit))
        for unit in responses
    ]
    gaps: list[MissingResponseHeading] = []
    for current, following in zip(comments, comments[1:], strict=False):
        current_label = _numbered_unit_label(str(current["official_label"]), "comment")
        following_label = _numbered_unit_label(str(following["official_label"]), "comment")
        if current_label is None or following_label is None:
            continue
        current_prefix, current_number = current_label
        following_prefix, following_number = following_label
        if current_prefix != following_prefix or following_number != current_number + 1:
            continue
        if current.get("submission_id") != following.get("submission_id"):
            continue
        scoped_responses = [
            (unit, label, unit_position)
            for unit, label, unit_position in response_details
            if label is not None
            and label[0] == current_prefix
            and unit.get("submission_id") == current.get("submission_id")
        ]
        if not scoped_responses:
            continue
        current_position = position(current)
        following_position = position(following)
        if any(
            label[1] == current_number and current_position < unit_position < following_position
            for _unit, label, unit_position in scoped_responses
        ):
            continue
        evidence_ids = tuple(
            sorted(
                {
                    str(current["start_marker_id"]),
                    *(str(span_id) for span_id in current["span_ids"]),
                    str(following["start_marker_id"]),
                }
            )
        )
        gaps.append(
            MissingResponseHeading(
                activity_id=activity_id,
                comment_unit_id=str(current["unit_id"]),
                evidence_ids=evidence_ids,
            )
        )
    return tuple(gaps)


def _is_response_style_comment_candidate(
    marker: Mapping[str, Any], pages: Mapping[str, Mapping[str, Any]]
) -> bool:
    if (
        marker.get("marker_kind") != "comment"
        or marker.get("disposition") not in {"needs_review", "unit_start"}
        or marker.get("line_initial") is not True
        or marker.get("style_evidence") != _RESPONSE_STYLE
    ):
        return False
    page = pages.get(str(marker.get("page_id")))
    if page is None:
        return False
    text = str(page["raw_text"])
    start = int(marker["text_start"])
    end = int(marker["text_end"])
    line_start = text.rfind("\n", 0, start) + 1
    newline = text.find("\n", end)
    line_end = len(text) if newline == -1 else newline
    return text[line_start:line_end].strip() == text[start:end]


def _normalized_unit_code(label: str) -> str:
    """Normalize only the kind prefix, optional No., case, and whitespace."""
    without_kind = _KIND_PREFIX_RE.sub("", label.strip(), count=1)
    return " ".join(without_kind.casefold().split())


def _numbered_unit_label(label: str, kind: str) -> tuple[str, int] | None:
    normalized = " ".join(label.strip().casefold().split())
    prefix = re.compile(rf"^{re.escape(kind)}\s+(?:no\.\s*)?")
    code = prefix.sub("", normalized, count=1)
    match = _TRAILING_NUMBER_RE.fullmatch(code)
    if match is None:
        return None
    return match.group("prefix"), int(match.group("number"))


__all__ = [
    "MissingResponseHeading",
    "SOURCE_RESPONSE_HEADING_ABSENT",
    "SOURCE_RESPONSE_HEADING_ABSENT_MESSAGE",
    "missing_response_heading_gaps",
    "paired_response_style_comment_marker_ids",
]
