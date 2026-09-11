"""Pure repeated chapter-heading classification policy and persisted decisions."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Any, Literal

JsonObject = dict[str, Any]
DecisionStatus = Literal["eligible", "rejected", "review_required"]

_CHAPTER_HEADING = re.compile(
    r"^[ \t\n\r\f\v]*(?P<marker>\d{1,2})[ \t\n\r\f\v]*"
    r"(?P<separator>\|[ \t\n\r\f\v]*)?(?P<title>[^|]+?)[ \t\n\r\f\v]*$"
)
_ASCII_WHITESPACE = re.compile(r"[ \t\n\r\f\v]+")


@dataclass(frozen=True)
class HeadingTopology:
    """Small source-free view of one accepted semantic heading and its extent."""

    section_id: str
    heading_block_id: str
    stable_item_key: str
    raw_text: str
    physical_page: int
    section_sequence: int
    sibling_index: int
    parent_section_id: str
    semantic_level: int
    content_layer: str = "body"
    corrected_role: str = "heading"
    is_toc_row: bool = False
    direct_content_ids: tuple[str, ...] = ()
    child_section_ids: tuple[str, ...] = ()
    ordered_child_ids: tuple[str, ...] = ()
    descendant_page_extent: tuple[int, int] | None = None


@dataclass(frozen=True)
class TocHeadingEvidence:
    """Accepted TOC title plus optional resolved destination observations."""

    evidence_ids: tuple[str, ...]
    raw_text: str
    destination_physical_pages: tuple[int, ...] = ()
    terminal_destination_token: str | None = None


@dataclass(frozen=True)
class RepeatedHeadingDecision:
    """One explainable repeated-heading classification and projection recipe."""

    status: DecisionStatus
    reason_codes: tuple[str, ...]
    chapter_marker: str | None
    chapter_title: str | None
    heading_section_ids: tuple[str, ...]
    heading_stable_keys: tuple[str, ...]
    heading_block_ids: tuple[str, ...]
    heading_raw_texts: tuple[str, ...]
    heading_physical_pages: tuple[int, ...]
    parent_section_id: str | None
    semantic_level: int | None
    ordered_child_refs: tuple[tuple[str, ...], ...]
    source_page_extents: tuple[tuple[int, int] | None, ...]
    anchor_heading_key: str | None
    absorbed_heading_key: str | None
    toc_evidence_ids: tuple[str, ...]
    destination_physical_pages: tuple[int, ...]
    unresolved_toc_tokens: tuple[str, ...]
    extent_start_page: int | None
    following_boundary_section_id: str | None
    following_boundary_stable_key: str | None
    following_boundary_raw_text: str | None
    following_boundary_page: int | None

    @classmethod
    def from_record(cls, record: JsonObject) -> RepeatedHeadingDecision:
        """Load the policy fields needed for projection from a validated record."""
        return cls(
            status=record["status"],
            reason_codes=tuple(record["reason_codes"]),
            chapter_marker=record["chapter_marker"],
            chapter_title=record["chapter_title"],
            heading_section_ids=tuple(record["heading_section_ids"]),
            heading_stable_keys=tuple(record["heading_stable_keys"]),
            heading_block_ids=tuple(record["heading_block_ids"]),
            heading_raw_texts=tuple(record["heading_raw_texts"]),
            heading_physical_pages=tuple(record["heading_physical_pages"]),
            parent_section_id=record["parent_ref"],
            semantic_level=record["semantic_level"],
            ordered_child_refs=tuple(tuple(items) for items in record["ordered_child_refs"]),
            source_page_extents=tuple(
                tuple(item) if item is not None else None for item in record["source_page_extents"]
            ),
            anchor_heading_key=record["anchor_heading_key"],
            absorbed_heading_key=record["absorbed_heading_key"],
            toc_evidence_ids=tuple(record["toc_evidence_ids"]),
            destination_physical_pages=tuple(record["destination_physical_pages"]),
            unresolved_toc_tokens=tuple(record["unresolved_toc_tokens"]),
            extent_start_page=record["extent_start_page"],
            following_boundary_section_id=record["following_boundary_section_id"],
            following_boundary_stable_key=record["following_boundary_stable_key"],
            following_boundary_raw_text=record["following_boundary_raw_text"],
            following_boundary_page=record["following_boundary_page"],
        )

    def as_record(
        self,
        *,
        source_ref: JsonObject,
        new_target_ref: JsonObject | None,
        human_decision_ref: JsonObject | None = None,
    ) -> JsonObject:
        """Return the versioned source-free decision/correspondence record."""
        return {
            "schema_version": "er_commons.recovery.chapter_decision.v1",
            "rule_version": "repeated_chapter_divider_opening_v1",
            "decision_kind": "repeated_chapter_heading",
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "chapter_marker": self.chapter_marker,
            "chapter_title": self.chapter_title,
            "heading_section_ids": list(self.heading_section_ids),
            "heading_stable_keys": list(self.heading_stable_keys),
            "heading_block_ids": list(self.heading_block_ids),
            "heading_raw_texts": list(self.heading_raw_texts),
            "heading_physical_pages": list(self.heading_physical_pages),
            "parent_ref": self.parent_section_id,
            "semantic_level": self.semantic_level,
            "ordered_child_refs": [list(items) for items in self.ordered_child_refs],
            "source_page_extents": [
                list(item) if item is not None else None for item in self.source_page_extents
            ],
            "anchor_heading_key": self.anchor_heading_key,
            "absorbed_heading_key": self.absorbed_heading_key,
            "toc_evidence_ids": list(self.toc_evidence_ids),
            "destination_physical_pages": list(self.destination_physical_pages),
            "unresolved_toc_tokens": list(self.unresolved_toc_tokens),
            "extent_start_page": self.extent_start_page,
            "following_boundary_section_id": self.following_boundary_section_id,
            "following_boundary_stable_key": self.following_boundary_stable_key,
            "following_boundary_raw_text": self.following_boundary_raw_text,
            "following_boundary_page": self.following_boundary_page,
            "extent_basis": "anchor_through_before_following_same_level_sibling",
            "inference_method": "accepted_topology_and_toc_correspondence",
            "source_ref": source_ref,
            "new_target_ref": new_target_ref,
            "human_decision_ref": human_decision_ref,
        }


def classify_repeated_heading_group(
    headings: tuple[HeadingTopology, ...],
    *,
    toc_evidence: tuple[TocHeadingEvidence, ...],
    following_sibling: HeadingTopology | None,
) -> RepeatedHeadingDecision:
    """Classify one candidate group without mutating or rescanning projected output."""
    base = _decision_base(headings, toc_evidence, following_sibling)
    if len(headings) != 2:
        return replace(base, status="review_required", reason_codes=("unsupported_cardinality",))
    first, second = headings
    parsed = tuple(_parse_heading(item.raw_text) for item in headings)
    rejected = _eligibility_rejections(first, second, parsed)
    if rejected:
        return replace(base, status="rejected", reason_codes=tuple(rejected))

    assert parsed[0] is not None and parsed[1] is not None
    marker, _, title = parsed[0]
    review_reasons = _review_reasons(
        first,
        second,
        marker=marker,
        title=title,
        toc_evidence=toc_evidence,
        following_sibling=following_sibling,
    )
    matching_toc = _matching_toc(toc_evidence, marker, title)
    destinations = tuple(
        sorted({page for item in matching_toc for page in item.destination_physical_pages})
    )
    return replace(
        base,
        status="review_required" if review_reasons else "eligible",
        reason_codes=tuple(review_reasons or ["adjacent_divider_opening_logical_chapter"]),
        chapter_marker=marker,
        chapter_title=title,
        anchor_heading_key=first.stable_item_key if not review_reasons else None,
        absorbed_heading_key=second.stable_item_key if not review_reasons else None,
        toc_evidence_ids=tuple(
            evidence_id for item in toc_evidence for evidence_id in item.evidence_ids
        ),
        destination_physical_pages=destinations,
        extent_start_page=first.physical_page,
    )


def _parse_heading(raw_text: str) -> tuple[str, bool, str] | None:
    match = _CHAPTER_HEADING.fullmatch(raw_text)
    if match is None:
        return None
    title = _normalize_heading_title(match.group("title"))
    if not title:
        return None
    return match.group("marker"), match.group("separator") is not None, title


def _normalize_heading_title(value: str) -> str:
    """Apply NFC, NBSP replacement, ASCII whitespace folding, and casefold only."""
    normalized = unicodedata.normalize("NFC", value).replace("\N{NO-BREAK SPACE}", " ")
    return _ASCII_WHITESPACE.sub(" ", normalized).strip().casefold()


def _eligibility_rejections(
    first: HeadingTopology,
    second: HeadingTopology,
    parsed: tuple[tuple[str, bool, str] | None, ...],
) -> list[str]:
    reasons: list[str] = []
    if any(
        item.content_layer != "body" or item.corrected_role != "heading" for item in (first, second)
    ):
        reasons.append("not_body_accepted_headings")
    if first.is_toc_row or second.is_toc_row:
        reasons.append("toc_or_furniture_ineligible")
    if first.parent_section_id != second.parent_section_id:
        reasons.append("different_parents")
    if first.semantic_level != second.semantic_level:
        reasons.append("different_semantic_levels")
    if second.sibling_index != first.sibling_index + 1:
        reasons.append("nonconsecutive_siblings")
    if second.physical_page != first.physical_page + 1:
        reasons.append("nonadjacent_physical_pages")
    if parsed[0] is None or parsed[1] is None:
        reasons.append("unsupported_heading_syntax")
    elif parsed[0][0] != parsed[1][0]:
        reasons.append("chapter_marker_disagreement")
    elif parsed[0][2] != parsed[1][2]:
        reasons.append("chapter_title_disagreement")
    elif parsed[0][1] or not parsed[1][1]:
        reasons.append("not_divider_then_opening_typography")
    return reasons


def _review_reasons(
    first: HeadingTopology,
    second: HeadingTopology,
    *,
    marker: str,
    title: str,
    toc_evidence: tuple[TocHeadingEvidence, ...],
    following_sibling: HeadingTopology | None,
) -> list[str]:
    reasons: list[str] = []
    first_records = set(first.direct_content_ids) | set(first.child_section_ids)
    second_records = set(second.direct_content_ids) | set(second.child_section_ids)
    if first_records.intersection(second_records):
        reasons.append("overlapping_child_ownership")
    if first.descendant_page_extent is None or second.descendant_page_extent is None:
        reasons.append("descendant_page_extent_absent")
    elif _extents_overlap(first.descendant_page_extent, second.descendant_page_extent):
        reasons.append("overlapping_child_ranges")
    matching_toc = _matching_toc(toc_evidence, marker, title)
    if not matching_toc:
        reasons.append("matching_toc_evidence_absent")
    contradictory = [
        item
        for item in toc_evidence
        if (parsed := _parse_heading(item.raw_text)) is not None
        and parsed[0] == marker
        and parsed[2] != title
    ]
    if contradictory:
        reasons.append("contradictory_toc_title")
    allowed_pages = {first.physical_page, second.physical_page}
    destinations = {page for item in matching_toc for page in item.destination_physical_pages}
    if destinations - allowed_pages:
        reasons.append("conflicting_toc_destinations")
    if following_sibling is None:
        reasons.append("following_chapter_boundary_absent")
    elif (
        following_sibling.parent_section_id != first.parent_section_id
        or following_sibling.semantic_level != first.semantic_level
        or following_sibling.sibling_index != second.sibling_index + 1
        or following_sibling.physical_page <= second.physical_page
    ):
        reasons.append("following_chapter_boundary_incompatible")
    else:
        following = _parse_heading(following_sibling.raw_text)
        if following is None or following[0] == marker:
            reasons.append("following_boundary_not_distinct_chapter")
        if (
            first.descendant_page_extent is not None
            and second.descendant_page_extent is not None
            and max(first.descendant_page_extent[1], second.descendant_page_extent[1])
            >= following_sibling.physical_page
        ):
            reasons.append("descendant_extent_reaches_following_boundary")
    return reasons


def _matching_toc(
    toc_evidence: tuple[TocHeadingEvidence, ...], marker: str, title: str
) -> tuple[TocHeadingEvidence, ...]:
    return tuple(
        item
        for item in toc_evidence
        if (parsed := _parse_heading(item.raw_text)) is not None
        and parsed[0] == marker
        and parsed[2] == title
    )


def _extents_overlap(first: tuple[int, int] | None, second: tuple[int, int] | None) -> bool:
    if first is None or second is None:
        return False
    return max(first[0], second[0]) <= min(first[1], second[1])


def _decision_base(
    headings: tuple[HeadingTopology, ...],
    toc_evidence: tuple[TocHeadingEvidence, ...],
    following_sibling: HeadingTopology | None,
) -> RepeatedHeadingDecision:
    return RepeatedHeadingDecision(
        status="rejected",
        reason_codes=(),
        chapter_marker=None,
        chapter_title=None,
        heading_section_ids=tuple(item.section_id for item in headings),
        heading_stable_keys=tuple(item.stable_item_key for item in headings),
        heading_block_ids=tuple(item.heading_block_id for item in headings),
        heading_raw_texts=tuple(item.raw_text for item in headings),
        heading_physical_pages=tuple(item.physical_page for item in headings),
        parent_section_id=(headings[0].parent_section_id if headings else None),
        semantic_level=(headings[0].semantic_level if headings else None),
        ordered_child_refs=tuple(
            item.ordered_child_ids or (*item.direct_content_ids, *item.child_section_ids)
            for item in headings
        ),
        source_page_extents=tuple(item.descendant_page_extent for item in headings),
        anchor_heading_key=None,
        absorbed_heading_key=None,
        toc_evidence_ids=tuple(
            evidence_id for item in toc_evidence for evidence_id in item.evidence_ids
        ),
        destination_physical_pages=(),
        unresolved_toc_tokens=tuple(
            item.terminal_destination_token
            for item in toc_evidence
            if item.terminal_destination_token is not None and not item.destination_physical_pages
        ),
        extent_start_page=min((item.physical_page for item in headings), default=None),
        following_boundary_section_id=(
            following_sibling.section_id if following_sibling is not None else None
        ),
        following_boundary_stable_key=(
            following_sibling.stable_item_key if following_sibling is not None else None
        ),
        following_boundary_raw_text=(
            following_sibling.raw_text if following_sibling is not None else None
        ),
        following_boundary_page=(
            following_sibling.physical_page if following_sibling is not None else None
        ),
    )
