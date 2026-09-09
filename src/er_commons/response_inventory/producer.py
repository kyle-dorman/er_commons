"""Deterministic source-unit construction from bounded page observations."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from er_commons.response_inventory.contract import SCHEMA_VERSION, build_record_id
from er_commons.response_inventory.observations import LineObservation, PageObservation
from er_commons.response_inventory.source_structure import (
    SOURCE_RESPONSE_HEADING_ABSENT,
    SOURCE_RESPONSE_HEADING_ABSENT_MESSAGE,
    missing_response_heading_gaps,
    paired_response_style_comment_marker_ids,
)

type JsonObject = dict[str, Any]
type UnitKind = Literal["comment", "response", "general_response"]
type SubmissionKind = Literal["letter", "meeting"]
type PageState = Literal[
    "blank",
    "continuation",
    "figure_or_table",
    "labeled_blank",
    "layout_exception",
    "mixed_markers",
    "revision_markup",
    "section_opener",
    "unit_start",
    "zero_comment_section",
]

_UNIT_PATTERNS: Final[tuple[tuple[UnitKind, re.Pattern[str]], ...]] = (
    (
        "general_response",
        re.compile(
            r"(?:\d+(?:\.\d+)*\s+)?"
            r"(?P<label>General\s+Response(?:\s+No\.)?\s+[1-9]\b)",
            re.IGNORECASE,
        ),
    ),
    ("comment", re.compile(r"Comment\s+(?:No\.\s*)?[A-Z0-9][A-Z0-9._/-]*", re.IGNORECASE)),
    (
        "response",
        re.compile(r"Response\s+(?:No\.\s*)?[A-Z0-9][A-Z0-9._/-]*", re.IGNORECASE),
    ),
)
_REFERENCE_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    (
        "draft_eir",
        re.compile(
            r"(?:Draft\s+EIR|DEIR)\s+(?:Section|Chapter|Appendix|Figure|Table)\s+"
            r"[A-Z0-9](?:[A-Z0-9.-]*[A-Z0-9])?",
            re.IGNORECASE,
        ),
    ),
    ("appendix_q", re.compile(r"Appendix\s+Q\b", re.IGNORECASE)),
    (
        "intra_volume",
        re.compile(
            r"(?:General\s+Response(?:\s+No\.)?\s+[1-9]|Response\s+[A-Z0-9][A-Z0-9._/-]*)",
            re.IGNORECASE,
        ),
    ),
)
_SUBMISSION_PATTERNS: Final[tuple[tuple[SubmissionKind, re.Pattern[str]], ...]] = (
    (
        "letter",
        re.compile(
            r"(?:\d+(?:\.\d+)+\s+)?(?i:LETTER)\s+"
            r"([A-Z0-9]+(?:-[A-Z0-9]+)+)(?![A-Za-z0-9._/-])",
        ),
    ),
    (
        "meeting",
        re.compile(
            r"(?:\d+(?:\.\d+)+\s+)?(?i:TRANSCRIPT)\s+"
            r"([A-Z0-9]+(?:-[A-Z0-9]+)+)(?![A-Za-z0-9._/-])",
        ),
    ),
)
_COMMENTER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:Submitted\s+by|From):\s*([^\r\n]+)", re.IGNORECASE
)
_ROSTER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?P<code>[A-Z][A-Z0-9]*(?:-[A-Za-z0-9]+)+)\s+"
    r"(?P<label>\S(?:.*\S)?)\s*$"
)
_MIN_ROSTER_ROWS_PER_PAGE: Final[int] = 3
_COMMENT_CODE_TEXT: Final[str] = r"[A-Z0-9]+(?:[-./][A-Za-z0-9]+)+"
_COMMENT_MEMBERSHIP_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf"(?i:Comment\s+Letter)\s*:\s*(?P<codes>{_COMMENT_CODE_TEXT}"
    rf"(?:(?:\s*[,;]\s*|\s+){_COMMENT_CODE_TEXT})*)"
)
_COMMENT_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(_COMMENT_CODE_TEXT)
_NUMBERED_UPPERCASE_GR_HEADING_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*\d+(?:\.\d+)*\s+GENERAL\s+RESPONSE(?:\s+NO\.)?\s+[1-8]\s*:\s*"
    r"[A-Z][A-Z0-9\s&/(),.'’–—-]*\s*$"
)
_GENERAL_RESPONSE_NINE_RE: Final[re.Pattern[str]] = re.compile(
    r"General\s+Response(?:\s+No\.)?\s+9\b", re.IGNORECASE
)
_GENERAL_RESPONSE_NINE_ROUTE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?:Chapter\s+16|Volume\s+5)\b", re.IGNORECASE
)
_MAX_PLACEMENT_CONTEXT_CHARACTERS: Final[int] = 240
_MIN_PLACEMENT_TOPIC_WORDS: Final[int] = 3
_PLACEMENT_CONTEXT_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z]{4,}")
_PLACEMENT_CONTEXT_STOP_WORDS: Final[frozenset[str]] = frozenset(
    {"chapter", "comments", "general", "response", "section", "volume"}
)


@dataclass(frozen=True)
class _Marker:
    """Unit-marker candidate paired with its materialized record."""

    page: PageObservation
    line: LineObservation
    kind: UnitKind
    label: str
    record: JsonObject


@dataclass(frozen=True)
class _Submission:
    """Submission opener that closes units and scopes following units."""

    page: PageObservation
    record: JsonObject
    submission_record: JsonObject


@dataclass(frozen=True)
class _RosterCommenter:
    """Commenter named by an official-code roster row."""

    official_code: str
    commenter_id: str


def build_source_records(
    activity: Mapping[str, Any],
    observations: Sequence[PageObservation],
) -> list[JsonObject]:
    """Build 05C/05D-owned semantic records without resolving relationships."""
    source_id = _require_source_activity(activity)
    ordered_pages = _validate_observation_scope(activity, observations)
    activity_record = dict(activity)
    records: list[JsonObject] = [activity_record]
    page_records: dict[int, JsonObject] = {}
    markers: list[_Marker] = []
    submissions: list[_Submission] = []
    roster_commenters: list[_RosterCommenter] = []
    section_pages: set[int] = set()

    for page in ordered_pages:
        page_record = _page_record(source_id, str(activity["activity_id"]), page, "continuation")
        page_records[page.physical_page] = page_record
        records.append(page_record)
        page_markers, marker_records = _markers_for_page(page, page_record)
        markers.extend(page_markers)
        records.extend(marker_records)
        page_commenters, commenter_records = _roster_commenters_for_page(
            source_id, page, page_record
        )
        roster_commenters.extend(page_commenters)
        records.extend(commenter_records)
        if any(record["disposition"] == "section_opener" for record in marker_records):
            section_pages.add(page.physical_page)
        if page_commenters:
            section_pages.add(page.physical_page)

    commenters_by_code: dict[str, list[str]] = {}
    for commenter in roster_commenters:
        commenters_by_code.setdefault(commenter.official_code.casefold(), []).append(
            commenter.commenter_id
        )
    for page in ordered_pages:
        page_record = page_records[page.physical_page]
        page_submissions, submission_records = _submissions_for_page(
            source_id, page, page_record, commenters_by_code
        )
        submissions.extend(page_submissions)
        records.extend(submission_records)
        if page_submissions:
            section_pages.add(page.physical_page)

    paired_comment_ids = (
        paired_response_style_comment_marker_ids(records)
        if activity["stage"] == "05d"
        else frozenset()
    )
    for marker in markers:
        if marker.record["marker_id"] in paired_comment_ids:
            marker.record["disposition"] = "unit_start"
    accepted = sorted(
        (marker for marker in markers if marker.record["disposition"] == "unit_start"),
        key=lambda marker: (marker.page.physical_page, marker.line.text_start),
    )
    ordered_submissions = sorted(
        submissions,
        key=lambda submission: (
            submission.page.physical_page,
            submission.record["text_start"],
        ),
    )
    boundaries = _structural_boundaries(ordered_pages)
    records.extend(
        _placement_exceptions(source_id, str(activity["activity_id"]), ordered_pages, page_records)
    )
    unit_records = _materialize_units(
        source_id,
        str(activity["activity_id"]),
        str(activity["stage"]),
        ordered_pages,
        page_records,
        accepted,
        boundaries,
        ordered_submissions,
    )
    records.extend(unit_records)
    records.extend(
        _missing_response_heading_diagnostics(
            records,
            activity_id=str(activity["activity_id"]),
            stage=str(activity["stage"]),
        )
    )
    _assign_page_states(ordered_pages, page_records, accepted, section_pages)
    return _deduplicate_records(records)


def _require_source_activity(activity: Mapping[str, Any]) -> str:
    if activity.get("record_type") != "activity" or activity.get("stage") not in {"05c", "05d"}:
        raise ValueError("source record construction requires an 05C/05D activity")
    source_id = activity.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source activity is missing source_id")
    if activity.get("activity_id") != build_record_id(activity):
        raise ValueError("activity_id does not match its identity preimage")
    return source_id


def _validate_observation_scope(
    activity: Mapping[str, Any], observations: Sequence[PageObservation]
) -> list[PageObservation]:
    expected = [
        page for start, end in activity["page_ranges"] for page in range(int(start), int(end) + 1)
    ]
    ordered = sorted(observations, key=lambda page: page.physical_page)
    observed = [page.physical_page for page in ordered]
    if observed != expected:
        raise ValueError("page observations do not close the activity ranges")
    if len(observed) != len(set(observed)):
        raise ValueError("page observations contain duplicate physical pages")
    return ordered


def _page_record(
    source_id: str,
    activity_id: str,
    page: PageObservation,
    initial_state: str,
) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "page",
        "source_id": source_id,
        "physical_page": page.physical_page,
        "page_state": initial_state,
        "raw_text": page.raw_text,
        "raw_text_sha256": hashlib.sha256(page.raw_text.encode("utf-8")).hexdigest(),
        "page_box": {
            "width_points": page.width_points,
            "height_points": page.height_points,
            "rotation": page.rotation,
        },
        "character_slot_count": page.character_slot_count,
        "geometry_ref": None,
        "activity_id": activity_id,
    }
    record["page_id"] = build_record_id(record)
    return record


def _markers_for_page(
    page: PageObservation, page_record: Mapping[str, Any]
) -> tuple[list[_Marker], list[JsonObject]]:
    accepted: list[_Marker] = []
    records: list[JsonObject] = []
    for line in page.lines:
        line_text = page.raw_text[line.text_start : line.text_end]
        stripped_offset = len(line_text) - len(line_text.lstrip())
        for kind, pattern in _UNIT_PATTERNS:
            for match in pattern.finditer(line_text):
                label_group = "label" if kind == "general_response" else 0
                label = match.group(label_group)
                start = line.text_start + match.start(label_group)
                end = line.text_start + match.end(label_group)
                line_initial = match.start() == stripped_offset
                numbered_uppercase_heading = _is_numbered_uppercase_gr_heading(line_text)
                disposition = _marker_disposition(
                    kind,
                    label,
                    line,
                    line_initial,
                    numbered_uppercase_heading=numbered_uppercase_heading,
                )
                record = _marker_record(
                    page_record,
                    line,
                    kind,
                    label,
                    start,
                    end,
                    line_initial,
                    disposition,
                )
                records.append(record)
                accepted.append(_Marker(page, line, kind, label, record))
    return accepted, records


def _marker_disposition(
    kind: UnitKind,
    label: str,
    line: LineObservation,
    line_initial: bool,
    *,
    numbered_uppercase_heading: bool,
) -> str:
    if not line_initial:
        return "inline_reference"
    if kind == "general_response":
        if re.search(r"\b9\b", label):
            return "section_opener"
        return "unit_start" if line.bold or numbered_uppercase_heading else "needs_review"
    if kind == "comment" and line.bold and line.solid_rule:
        return "unit_start"
    if kind == "response" and line.italic and line.dotted_rule:
        return "unit_start"
    return "needs_review"


def _is_numbered_uppercase_gr_heading(line_text: str) -> bool:
    """Recognize a complete numbered GR heading, not a matching TOC prefix.

    The font fallback is intentionally narrower than the ordinary bold-heading
    rule: it requires a colon and an uppercase title through the end of the
    line. Dot leaders or trailing page labels therefore remain review evidence.
    """
    # PDF text layers may encode a discretionary hyphen as a nonprinting C0
    # control character. Ignore those controls for classification only; the raw
    # source text and marker offsets remain untouched.
    classification_text = "".join(
        character for character in line_text if ord(character) >= 32 or character in "\t\r\n"
    )
    if re.search(r"(?:\.{2,}|\s+\d{1,3}-\d{1,3})\s*$", classification_text):
        return False
    return _NUMBERED_UPPERCASE_GR_HEADING_RE.fullmatch(classification_text) is not None


def _submissions_for_page(
    source_id: str,
    page: PageObservation,
    page_record: Mapping[str, Any],
    commenters_by_code: Mapping[str, Sequence[str]],
) -> tuple[list[_Submission], list[JsonObject]]:
    submissions: list[_Submission] = []
    records: list[JsonObject] = []
    for line in page.lines:
        line_text = page.raw_text[line.text_start : line.text_end]
        stripped_offset = len(line_text) - len(line_text.lstrip())
        for submission_kind, pattern in _SUBMISSION_PATTERNS:
            for match in pattern.finditer(line_text):
                start = line.text_start + match.start()
                end = line.text_start + match.end()
                line_initial = match.start() == stripped_offset
                disposition = "section_opener" if line_initial else "inline_reference"
                marker_record = _marker_record(
                    page_record,
                    line,
                    "submission",
                    match.group(0),
                    start,
                    end,
                    line_initial,
                    disposition,
                )
                records.append(marker_record)
                if not line_initial:
                    continue
                opener_span = _single_page_span(
                    source_id, page_record, start, end, line.revision_marks
                )
                records.append(opener_span)
                commenter_records, commenter_ids = _commenters_for_submission(
                    source_id,
                    page,
                    page_record,
                    end,
                    _next_submission_start(page.raw_text, end),
                )
                records.extend(commenter_records)
                commenter_ids = list(
                    dict.fromkeys(
                        [
                            *commenter_ids,
                            *commenters_by_code.get(match.group(1).casefold(), ()),
                        ]
                    )
                )
                submission_record: JsonObject = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "submission",
                    "source_id": source_id,
                    "submission_kind": submission_kind,
                    "official_code": match.group(1),
                    "opener_span_id": opener_span["span_id"],
                    "commenter_ids": commenter_ids,
                }
                submission_record["submission_id"] = build_record_id(submission_record)
                records.append(submission_record)
                submissions.append(
                    _Submission(
                        page=page,
                        record=marker_record,
                        submission_record=submission_record,
                    )
                )
    return submissions, records


def _roster_commenters_for_page(
    source_id: str,
    page: PageObservation,
    page_record: Mapping[str, Any],
) -> tuple[list[_RosterCommenter], list[JsonObject]]:
    """Materialize code roster rows only when their page has table-like density."""
    roster_commenters: list[_RosterCommenter] = []
    records: list[JsonObject] = []
    matches: list[tuple[LineObservation, re.Match[str]]] = []
    for line in page.lines:
        line_text = page.raw_text[line.text_start : line.text_end]
        match = _ROSTER_PATTERN.fullmatch(line_text)
        if match is not None:
            matches.append((line, match))
    if len(matches) < _MIN_ROSTER_ROWS_PER_PAGE:
        return [], []
    for line, match in matches:
        source_label = match.group("label")
        label_start = line.text_start + match.start("label")
        label_end = line.text_start + match.end("label")
        span = _single_page_span(
            source_id, page_record, label_start, label_end, line.revision_marks
        )
        commenter: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "commenter",
            "source_id": source_id,
            "source_label": source_label,
            "opener_span_id": span["span_id"],
        }
        commenter["commenter_id"] = build_record_id(commenter)
        records.extend((span, commenter))
        roster_commenters.append(
            _RosterCommenter(
                official_code=match.group("code"),
                commenter_id=commenter["commenter_id"],
            )
        )
    return roster_commenters, records


def _commenters_for_submission(
    source_id: str,
    page: PageObservation,
    page_record: Mapping[str, Any],
    opener_end: int,
    boundary: int,
) -> tuple[list[JsonObject], list[str]]:
    """Capture only explicit same-page source labels after an opener."""
    records: list[JsonObject] = []
    commenter_ids: list[str] = []
    following_text = page.raw_text[opener_end:boundary]
    for match in _COMMENTER_PATTERN.finditer(following_text):
        raw_label = match.group(1)
        source_label = raw_label.strip()
        if not source_label:
            continue
        leading = len(raw_label) - len(raw_label.lstrip())
        absolute_start = opener_end + match.start(1) + leading
        absolute_end = absolute_start + len(source_label)
        span = _single_page_span(source_id, page_record, absolute_start, absolute_end, ())
        commenter: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "commenter",
            "source_id": source_id,
            "source_label": source_label,
            "opener_span_id": span["span_id"],
        }
        commenter["commenter_id"] = build_record_id(commenter)
        records.extend((span, commenter))
        commenter_ids.append(commenter["commenter_id"])
    return records, commenter_ids


def _next_submission_start(text: str, after: int) -> int:
    starts = [
        match.start()
        for _, pattern in _SUBMISSION_PATTERNS
        for match in pattern.finditer(text, after)
        if match.start() > after
    ]
    return min(starts, default=len(text))


def _single_page_span(
    source_id: str,
    page_record: Mapping[str, Any],
    start: int,
    end: int,
    revision_marks: Sequence[str],
) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "source_span",
        "source_id": source_id,
        "fragments": [
            {
                "page_id": page_record["page_id"],
                "text_start": start,
                "text_end": end,
                "character_slot_start": None,
                "character_slot_end": None,
                "bbox": None,
                "revision_marks": sorted(set(revision_marks)),
            }
        ],
    }
    record["span_id"] = build_record_id(record)
    return record


def _marker_record(
    page_record: Mapping[str, Any],
    line: LineObservation,
    kind: UnitKind | Literal["submission", "section"],
    label: str,
    start: int,
    end: int,
    line_initial: bool,
    disposition: str,
) -> JsonObject:
    slot_start, slot_end = _subinterval_slots(line, start, end)
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "marker_candidate",
        "page_id": page_record["page_id"],
        "marker_kind": kind,
        "observed_label": label,
        "line_index": line.line_index,
        "line_initial": line_initial,
        "text_start": start,
        "text_end": end,
        "character_slot_start": slot_start,
        "character_slot_end": slot_end,
        "bbox": list(line.bbox),
        "style_evidence": {
            "bold": line.bold,
            "italic": line.italic,
            "solid_rule": line.solid_rule,
            "dotted_rule": line.dotted_rule,
        },
        "disposition": disposition,
    }
    record["marker_id"] = build_record_id(record)
    return record


def _subinterval_slots(
    line: LineObservation, start: int, end: int
) -> tuple[int | None, int | None]:
    if line.character_slot_start is None or line.character_slot_end is None:
        return None, None
    if line.text_end - line.text_start != line.character_slot_end - line.character_slot_start:
        return None, None
    return (
        line.character_slot_start + start - line.text_start,
        line.character_slot_start + end - line.text_start,
    )


def _structural_boundaries(pages: Sequence[PageObservation]) -> set[tuple[int, int]]:
    return {(page.physical_page, len(page.raw_text)) for page in pages if page.closes_open_unit}


def _materialize_units(
    source_id: str,
    activity_id: str,
    stage: str,
    pages: Sequence[PageObservation],
    page_records: Mapping[int, JsonObject],
    markers: Sequence[_Marker],
    structural_boundaries: set[tuple[int, int]],
    submissions: Sequence[_Submission],
) -> list[JsonObject]:
    records: list[JsonObject] = []
    ranges = _page_ranges(pages)
    for start, end in ranges:
        range_pages = [page for page in pages if start <= page.physical_page <= end]
        range_markers = [marker for marker in markers if start <= marker.page.physical_page <= end]
        range_submissions = [
            submission
            for submission in submissions
            if start <= submission.page.physical_page <= end
        ]
        for index, marker in enumerate(range_markers):
            next_marker = range_markers[index + 1] if index + 1 < len(range_markers) else None
            next_submission = next(
                (
                    submission
                    for submission in range_submissions
                    if (
                        submission.page.physical_page,
                        submission.record["text_start"],
                    )
                    > (marker.page.physical_page, marker.record["text_start"])
                ),
                None,
            )
            candidate_boundaries = []
            if next_marker is not None:
                candidate_boundaries.append(
                    (next_marker.page.physical_page, next_marker.record["text_start"])
                )
            if next_submission is not None:
                candidate_boundaries.append(
                    (
                        next_submission.page.physical_page,
                        next_submission.record["text_start"],
                    )
                )
            boundary = (
                min(candidate_boundaries)
                if candidate_boundaries
                else _explicit_range_boundary(range_pages, structural_boundaries)
            )
            span = _span_to_boundary(source_id, range_pages, page_records, marker, boundary)
            records.append(span)
            records.extend(_continuations(span, marker.kind, marker.record["marker_id"]))
            if boundary is None:
                records.append(_open_boundary_diagnostic(activity_id, stage, marker, span))
                continue
            submission = _active_submission(marker, range_submissions)
            unit = _unit_record(source_id, activity_id, marker, span, submission)
            records.append(unit)
            records.extend(_reference_records(source_id, unit, span, page_records))
            records.extend(_membership_records(source_id, unit, span, page_records))
    return records


def _page_ranges(pages: Sequence[PageObservation]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start = previous = pages[0].physical_page
    for page in pages[1:]:
        if page.physical_page != previous + 1:
            ranges.append((start, previous))
            start = page.physical_page
        previous = page.physical_page
    ranges.append((start, previous))
    return ranges


def _explicit_range_boundary(
    pages: Sequence[PageObservation], boundaries: set[tuple[int, int]]
) -> tuple[int, int] | None:
    candidate = (pages[-1].physical_page, len(pages[-1].raw_text))
    return candidate if candidate in boundaries else None


def _span_to_boundary(
    source_id: str,
    pages: Sequence[PageObservation],
    page_records: Mapping[int, JsonObject],
    marker: _Marker,
    boundary: tuple[int, int] | None,
) -> JsonObject:
    end_page, end_offset = boundary or (pages[-1].physical_page, len(pages[-1].raw_text))
    fragments: list[JsonObject] = []
    for page in pages:
        if page.physical_page < marker.page.physical_page or page.physical_page > end_page:
            continue
        text_start = (
            marker.record["text_start"] if page.physical_page == marker.page.physical_page else 0
        )
        text_end = end_offset if page.physical_page == end_page else len(page.raw_text)
        if text_end <= text_start:
            continue
        fragments.append(
            {
                "page_id": page_records[page.physical_page]["page_id"],
                "text_start": text_start,
                "text_end": text_end,
                "character_slot_start": None,
                "character_slot_end": None,
                "bbox": None,
                "revision_marks": sorted(
                    {mark for line in page.lines for mark in line.revision_marks}
                ),
            }
        )
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "source_span",
        "source_id": source_id,
        "fragments": fragments,
    }
    record["span_id"] = build_record_id(record)
    return record


def _continuations(span: Mapping[str, Any], kind: UnitKind, marker_id: str) -> list[JsonObject]:
    fragments = span["fragments"]
    records: list[JsonObject] = []
    for left, right in zip(fragments, fragments[1:], strict=False):
        record: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "page_continuation",
            "from_page_id": left["page_id"],
            "to_page_id": right["page_id"],
            "continuation_kind": kind,
            "evidence_ids": [marker_id],
        }
        record["continuation_id"] = build_record_id(record)
        records.append(record)
    return records


def _unit_record(
    source_id: str,
    activity_id: str,
    marker: _Marker,
    span: Mapping[str, Any],
    submission: _Submission | None,
) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "source_unit",
        "source_id": source_id,
        "unit_kind": marker.kind,
        "official_label": marker.label,
        "start_marker_id": marker.record["marker_id"],
        "span_ids": [span["span_id"]],
        "submission_id": (
            submission.submission_record["submission_id"] if submission is not None else None
        ),
        "activity_id": activity_id,
    }
    record["unit_id"] = build_record_id(record)
    return record


def _active_submission(marker: _Marker, submissions: Sequence[_Submission]) -> _Submission | None:
    marker_position = (marker.page.physical_page, marker.record["text_start"])
    eligible = [
        submission
        for submission in submissions
        if (submission.page.physical_page, submission.record["text_start"]) < marker_position
    ]
    return eligible[-1] if eligible else None


def _open_boundary_diagnostic(
    activity_id: str, stage: str, marker: _Marker, span: Mapping[str, Any]
) -> JsonObject:
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "diagnostic",
        "stage": stage,
        "activity_id": activity_id,
        "code": "unit_boundary_ambiguous",
        "severity": "warning",
        "terminal": True,
        "subject_ids": [marker.record["marker_id"]],
        "evidence_ids": [span["span_id"]],
        "message": "Unit start is retained, but its closing boundary falls outside the range.",
    }
    record["diagnostic_id"] = build_record_id(record)
    return record


def _missing_response_heading_diagnostics(
    records: Sequence[JsonObject], *, activity_id: str, stage: str
) -> list[JsonObject]:
    """Materialize every source-backed missing response heading for Task 05D."""
    if stage != "05d":
        return []
    diagnostics: list[JsonObject] = []
    for gap in missing_response_heading_gaps(records, activity_id):
        record: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "diagnostic",
            "stage": stage,
            "activity_id": activity_id,
            "code": SOURCE_RESPONSE_HEADING_ABSENT,
            "severity": "warning",
            "terminal": True,
            "subject_ids": [gap.comment_unit_id],
            "evidence_ids": list(gap.evidence_ids),
            "message": SOURCE_RESPONSE_HEADING_ABSENT_MESSAGE,
        }
        record["diagnostic_id"] = build_record_id(record)
        diagnostics.append(record)
    return diagnostics


def _reference_records(
    source_id: str,
    unit: Mapping[str, Any],
    unit_span: Mapping[str, Any],
    pages: Mapping[int, JsonObject],
) -> list[JsonObject]:
    records: list[JsonObject] = []
    for fragment in unit_span["fragments"]:
        page = next(record for record in pages.values() if record["page_id"] == fragment["page_id"])
        text = page["raw_text"][fragment["text_start"] : fragment["text_end"]]
        for domain, pattern in _REFERENCE_PATTERNS:
            for match in pattern.finditer(text):
                start = fragment["text_start"] + match.start()
                end = fragment["text_start"] + match.end()
                first_fragment = unit_span["fragments"][0]
                if (
                    page["page_id"] == first_fragment["page_id"]
                    and start == first_fragment["text_start"]
                    and match.group(0).casefold() == unit["official_label"].casefold()
                ):
                    continue
                mention_span: JsonObject = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "source_span",
                    "source_id": source_id,
                    "fragments": [
                        {
                            "page_id": page["page_id"],
                            "text_start": start,
                            "text_end": end,
                            "character_slot_start": None,
                            "character_slot_end": None,
                            "bbox": None,
                            "revision_marks": [],
                        }
                    ],
                }
                mention_span["span_id"] = build_record_id(mention_span)
                mention: JsonObject = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "reference_mention",
                    "source_unit_id": unit["unit_id"],
                    "mention_span_id": mention_span["span_id"],
                    "raw_text_sha256": hashlib.sha256(match.group(0).encode("utf-8")).hexdigest(),
                    "target_labels": [match.group(0)],
                    "reference_domain": domain,
                }
                mention["mention_id"] = build_record_id(mention)
                records.extend((mention_span, mention))
    return records


def _membership_records(
    source_id: str,
    unit: Mapping[str, Any],
    unit_span: Mapping[str, Any],
    pages: Mapping[int, JsonObject],
) -> list[JsonObject]:
    if unit["unit_kind"] != "general_response":
        return []
    records: list[JsonObject] = []
    first_fragment = unit_span["fragments"][0]
    for fragment in unit_span["fragments"]:
        page = next(record for record in pages.values() if record["page_id"] == fragment["page_id"])
        text = page["raw_text"][fragment["text_start"] : fragment["text_end"]]
        for membership_match in _COMMENT_MEMBERSHIP_PATTERN.finditer(text):
            codes = membership_match.group("codes")
            for code_match in _COMMENT_CODE_PATTERN.finditer(codes):
                start = (
                    fragment["text_start"] + membership_match.start("codes") + code_match.start()
                )
                end = start + len(code_match.group(0))
                if (
                    page["page_id"] == first_fragment["page_id"]
                    and start == first_fragment["text_start"]
                ):
                    continue
                mention_span = _single_page_span(source_id, page, start, end, ())
                membership: JsonObject = {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "membership_claim",
                    "general_response_unit_id": unit["unit_id"],
                    "mention_span_id": mention_span["span_id"],
                    "target_label": code_match.group(0),
                }
                membership["membership_id"] = build_record_id(membership)
                records.extend((mention_span, membership))
    return records


def _placement_exceptions(
    source_id: str,
    activity_id: str,
    pages: Sequence[PageObservation],
    page_records: Mapping[int, JsonObject],
) -> list[JsonObject]:
    placement = _gr9_placement_evidence(pages)
    if placement is None:
        return []
    evidence_records: list[JsonObject] = []
    advertised_page, advertised, routed_page, routed = placement
    for page, match in ((advertised_page, advertised), (routed_page, routed)):
        evidence_record: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "source_span",
            "source_id": source_id,
            "fragments": [
                {
                    "page_id": page_records[page.physical_page]["page_id"],
                    "text_start": match.start(),
                    "text_end": match.end(),
                    "character_slot_start": None,
                    "character_slot_end": None,
                    "bbox": None,
                    "revision_marks": [],
                }
            ],
        }
        evidence_record["span_id"] = build_record_id(evidence_record)
        evidence_records.append(evidence_record)
    exception: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "source_placement_exception",
        "source_id": source_id,
        "activity_id": activity_id,
        "exception_code": "general_response_9_not_in_volume_4",
        "advertised_label": "General Response 9",
        "routed_volume": 5,
        "disposition": "cross_volume_scope_exception",
        "evidence_ids": sorted(record["span_id"] for record in evidence_records),
    }
    exception["exception_id"] = build_record_id(exception)
    return [*evidence_records, exception]


def _gr9_placement_evidence(
    pages: Sequence[PageObservation],
) -> tuple[PageObservation, re.Match[str], PageObservation, re.Match[str]] | None:
    """Pair GR9 and routing evidence only through local or shared topic context."""
    advertised_items = [
        (page, match, _placement_topic_words(page.raw_text, match))
        for page in pages
        for match in _GENERAL_RESPONSE_NINE_RE.finditer(page.raw_text)
    ]
    routed_items = [
        (page, match, _placement_topic_words(page.raw_text, match))
        for page in pages
        for match in _GENERAL_RESPONSE_NINE_ROUTE_RE.finditer(page.raw_text)
    ]
    for advertised_page, advertised, advertised_words in advertised_items:
        local_end = advertised.end() + len(_forward_context(advertised_page.raw_text, advertised))
        for routed_page, routed, routed_words in routed_items:
            same_context = (
                advertised_page.physical_page == routed_page.physical_page
                and advertised.end() <= routed.start() <= local_end
            )
            shared_topic = len(advertised_words & routed_words) >= _MIN_PLACEMENT_TOPIC_WORDS
            if same_context or shared_topic:
                return advertised_page, advertised, routed_page, routed
    return None


def _placement_topic_words(text: str, match: re.Match[str]) -> frozenset[str]:
    """Return distinctive normalized words following placement evidence."""
    return frozenset(
        word
        for word in (
            token.casefold()
            for token in _PLACEMENT_CONTEXT_WORD_RE.findall(_forward_context(text, match))
        )
        if word not in _PLACEMENT_CONTEXT_STOP_WORDS
    )


def _forward_context(text: str, match: re.Match[str]) -> str:
    """Return a bounded sentence or paragraph fragment following a match."""
    context_end = min(len(text), match.end() + _MAX_PLACEMENT_CONTEXT_CHARACTERS)
    context = text[match.end() : context_end]
    boundary = re.search(r"[.!?]|\r?\n\s*\r?\n", context)
    return context if boundary is None else context[: boundary.start()]


def _deduplicate_records(records: Sequence[JsonObject]) -> list[JsonObject]:
    """Remove identical shared spans while rejecting identity collisions."""
    by_identity: dict[tuple[str, str], JsonObject] = {}
    ordered: list[JsonObject] = []
    for record in records:
        record_type = str(record["record_type"])
        identity_field = {
            "activity": "activity_id",
            "page": "page_id",
            "page_continuation": "continuation_id",
            "marker_candidate": "marker_id",
            "source_span": "span_id",
            "commenter": "commenter_id",
            "submission": "submission_id",
            "source_unit": "unit_id",
            "membership_claim": "membership_id",
            "reference_mention": "mention_id",
            "diagnostic": "diagnostic_id",
            "source_placement_exception": "exception_id",
        }.get(record_type)
        if identity_field is None:
            ordered.append(record)
            continue
        key = (record_type, str(record[identity_field]))
        previous = by_identity.get(key)
        if previous is not None:
            if previous != record:
                raise ValueError(f"record identity collision: {key[1]}")
            continue
        by_identity[key] = record
        ordered.append(record)
    return ordered


def _assign_page_states(
    pages: Sequence[PageObservation],
    records: Mapping[int, JsonObject],
    markers: Sequence[_Marker],
    section_pages: set[int],
) -> None:
    accepted_by_page: dict[int, list[_Marker]] = {}
    for marker in markers:
        accepted_by_page.setdefault(marker.page.physical_page, []).append(marker)
    open_unit = False
    open_structure = False
    previous_page: int | None = None
    for page in pages:
        if previous_page is not None and page.physical_page != previous_page + 1:
            open_unit = False
            open_structure = False
        page_markers = accepted_by_page.get(page.physical_page, [])
        state = _classify_page_state(
            page,
            accepted_marker_count=len(page_markers),
            section_evidence=page.physical_page in section_pages,
            open_unit=open_unit,
            open_structure=open_structure,
        )
        records[page.physical_page]["page_state"] = state
        if page_markers:
            open_unit = not page.closes_open_unit
        elif page.closes_open_unit:
            open_unit = False
        if state in {"section_opener", "figure_or_table"}:
            open_structure = True
        elif state in {"blank", "labeled_blank", "layout_exception"}:
            open_structure = False
        previous_page = page.physical_page


def _classify_page_state(
    page: PageObservation,
    *,
    accepted_marker_count: int,
    section_evidence: bool,
    open_unit: bool,
    open_structure: bool,
) -> PageState:
    """Select one primary page state using the documented precedence order.

    Explicit page evidence wins over semantic markers, and semantic markers win
    over inherited continuation context. This keeps state changes local and
    makes precedence independently testable without constructing record bundles.
    """
    if accepted_marker_count < 0:
        raise ValueError("accepted marker count must be nonnegative")
    explicit_states: tuple[tuple[bool, PageState], ...] = (
        (page.labeled_blank, "labeled_blank"),
        (page.title_page, "layout_exception"),
        (page.revision_markup, "revision_markup"),
        (page.figure_or_table, "figure_or_table"),
        (not page.raw_text.strip(), "blank"),
    )
    for applies, state in explicit_states:
        if applies:
            return state
    if accepted_marker_count > 1:
        return "mixed_markers"
    if accepted_marker_count == 1:
        return "unit_start"
    contextual_states: tuple[tuple[bool, PageState], ...] = (
        (page.zero_comment_section, "zero_comment_section"),
        (page.section_opener or section_evidence, "section_opener"),
        (open_unit or open_structure or page.running_header_context, "continuation"),
    )
    for applies, state in contextual_states:
        if applies:
            return state
    raise ValueError(f"unclassified nonempty page requires explicit evidence: {page.physical_page}")


__all__ = ["build_source_records"]
