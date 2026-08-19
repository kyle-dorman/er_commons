"""Discover numbering scopes and expose their hierarchy lifecycle events."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Any, cast

from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    NumberingEvidence,
    parse_numbering,
)
from er_commons.document_parsing.heading_evidence_parsing.types import TocClassifiedItem
from er_commons.hierarchy_inference.semantic_types import NumberingScopeRecord, ScopedItem

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class NumberingScopeAnalysis:
    """Numbering scopes and items assigned to their innermost scope."""

    features: tuple[ScopedItem, ...]
    regimes: tuple[NumberingScopeRecord, ...]

    @property
    def scoped_items(self) -> tuple[ScopedItem, ...]:
        """Expose typed items to the human-owned semantic core."""
        return self.features

    @property
    def numbering_scopes(self) -> tuple[NumberingScopeRecord, ...]:
        """Expose typed scope records to the human-owned semantic core."""
        return self.regimes


@dataclass(frozen=True)
class NumberingScopeCandidate:
    """Evidence-supported half-open scope proposed before ID assignment."""

    start: int
    end: int
    anchor_key: str
    article: bool


@dataclass(frozen=True)
class NumberedHeader:
    """One parsed body heading available as a local-scope start."""

    order: int
    feature: TocClassifiedItem
    evidence: NumberingEvidence


@dataclass(frozen=True)
class NumberingCandidateIndex:
    """Linear-pass indexes used to discover local numbering scopes."""

    anchors: tuple[TocClassifiedItem, ...]
    numbered_headers: tuple[NumberedHeader, ...]
    numbered_orders: tuple[int, ...]
    top_level_markers: tuple[tuple[int, tuple[str, str | None]], ...]
    outline_positions: dict[tuple[int, str], tuple[int, ...]]
    next_outline_boundary: tuple[int | None, ...]
    feature_orders: dict[tuple[int, str], tuple[int, ...]]


@dataclass(frozen=True)
class MaterializedRegimes:
    """Stable scope records plus their assignment-only interval indexes."""

    regimes: tuple[NumberingScopeRecord, ...]
    intervals_by_id: dict[str, tuple[int, int]]
    article_regime_ids: frozenset[str]


def build_numbering_regimes(
    features: list[TocClassifiedItem], outline_observations: tuple[JsonObject, ...]
) -> NumberingScopeAnalysis:
    """Build the initial regime and evidence-supported nested local regimes."""
    body = [feature for feature in features if feature["content_layer"] == "body"]
    if not body:
        raise ValueError("numbering regimes require one body item")
    initial_start = min(feature["reading_order_index"] for feature in features)
    after_last = max(feature["reading_order_index"] for feature in features) + 1
    candidate_index = _build_candidate_index(features, outline_observations)
    candidates = _discover_nested_candidates(candidate_index, outline_observations, after_last)
    initial_id = _regime_id({"start": body[0]["stable_item_key"], "kind": "initial"})
    materialized = _materialize_regimes(
        features=features,
        candidates=candidates,
        initial_start=initial_start,
        after_last=after_last,
        initial_id=initial_id,
        initial_item_key=body[0]["stable_item_key"],
    )
    projected = _assign_innermost_regimes(
        features,
        materialized.intervals_by_id,
        materialized.article_regime_ids,
    )
    return NumberingScopeAnalysis(
        features=projected,
        regimes=materialized.regimes,
    )


def _materialize_regimes(
    *,
    features: list[TocClassifiedItem],
    candidates: list[NumberingScopeCandidate],
    initial_start: int,
    after_last: int,
    initial_id: str,
    initial_item_key: str,
) -> MaterializedRegimes:
    """Assign deterministic IDs and parent relationships to candidate scopes."""
    regimes: list[NumberingScopeRecord] = [
        NumberingScopeRecord(
            regime_id=initial_id,
            parent_regime_id=None,
            root_level=1,
            start_item_key=initial_item_key,
            end_item_key=None,
            outline_anchor_key=None,
            page_label_reset=False,
        )
    ]
    interval_by_id = {initial_id: (initial_start, after_last)}
    parent_stack = [(initial_id, initial_start, after_last)]
    article_regimes: set[str] = set()
    feature_by_order = {feature["reading_order_index"]: feature for feature in features}
    for candidate in sorted(candidates, key=lambda item: (item.start, -item.end)):
        while parent_stack and not (
            parent_stack[-1][1] < candidate.start < candidate.end <= parent_stack[-1][2]
        ):
            parent_stack.pop()
        if not parent_stack:
            raise ValueError(
                f"numbering scope candidate lacks a containing parent: "
                f"[{candidate.start}, {candidate.end})"
            )
        parent_id = parent_stack[-1][0]
        start_feature = feature_by_order[candidate.start]
        end_feature = feature_by_order.get(candidate.end)
        regime_id = _regime_id(
            {
                "anchor": candidate.anchor_key,
                "start": start_feature["stable_item_key"],
                "end": end_feature["stable_item_key"] if end_feature else None,
            }
        )
        regimes.append(
            NumberingScopeRecord(
                regime_id=regime_id,
                parent_regime_id=parent_id,
                root_level=1,
                start_item_key=start_feature["stable_item_key"],
                end_item_key=end_feature["stable_item_key"] if end_feature else None,
                outline_anchor_key=candidate.anchor_key,
                page_label_reset=start_feature.get("printed_page_label") == "1",
            )
        )
        interval_by_id[regime_id] = (candidate.start, candidate.end)
        parent_stack.append((regime_id, candidate.start, candidate.end))
        if candidate.article:
            article_regimes.add(regime_id)
    return MaterializedRegimes(
        regimes=tuple(regimes),
        intervals_by_id=interval_by_id,
        article_regime_ids=frozenset(article_regimes),
    )


def _assign_innermost_regimes(
    features: list[TocClassifiedItem],
    intervals_by_id: dict[str, tuple[int, int]],
    article_regime_ids: frozenset[str],
) -> tuple[ScopedItem, ...]:
    """Project each item into the deepest active scope in one ordered sweep."""
    interval_entries = [
        (start, end, sequence, regime_id)
        for sequence, (regime_id, (start, end)) in enumerate(intervals_by_id.items())
    ]
    interval_entries.sort(key=lambda item: (item[0], item[2]))
    interval_cursor = 0
    active_intervals: list[tuple[int, int, int, str]] = []
    projected: list[ScopedItem] = []
    for feature in features:
        order = feature["reading_order_index"]
        while (
            interval_cursor < len(interval_entries)
            and interval_entries[interval_cursor][0] <= order
        ):
            start, end, sequence, regime_id = interval_entries[interval_cursor]
            heappush(active_intervals, (-start, sequence, end, regime_id))
            interval_cursor += 1
        while active_intervals and active_intervals[0][2] <= order:
            heappop(active_intervals)
        if not active_intervals:
            raise ValueError(f"numbering regime coverage is missing at order {order}")
        regime_id = active_intervals[0][3]
        copy = cast(ScopedItem, dict(feature, regime_id=regime_id))
        if regime_id in article_regime_ids and copy["raw_role"] == "section_header":
            evidence = parse_numbering(copy["text"], raw_role=copy["raw_role"], article_regime=True)
            copy["numbering_kind"] = evidence.kind
            copy["numbering_token"] = evidence.token
            copy["numbering_depth"] = evidence.depth
        projected.append(copy)
    return tuple(projected)


def _nested_candidates(
    features: list[TocClassifiedItem], outlines: tuple[JsonObject, ...], after_last: int
) -> list[NumberingScopeCandidate]:
    """Discover candidates through the same typed indexes used by the public builder."""
    return _discover_nested_candidates(
        _build_candidate_index(features, outlines), outlines, after_last
    )


def _build_candidate_index(
    features: list[TocClassifiedItem], outlines: tuple[JsonObject, ...]
) -> NumberingCandidateIndex:
    """Parse headings and construct lookup indexes in linear passes."""
    anchors = [
        feature
        for feature in features
        if feature["content_layer"] == "body"
        and not feature.get("toc_region", False)
        and feature["outline_state"] == "unique_exact"
    ]
    numbered_headers: list[NumberedHeader] = []
    top_level_markers: list[tuple[int, tuple[str, str | None]]] = []
    for feature in features:
        if feature["raw_role"] != "section_header":
            continue
        evidence = parse_numbering(feature["text"], raw_role=feature["raw_role"])
        if feature["content_layer"] == "body" and evidence.kind not in {"none", "bullet"}:
            numbered_headers.append(
                NumberedHeader(feature["reading_order_index"], feature, evidence)
            )
        if not feature.get("toc_region", False) and evidence.kind in {"article", "decimal"}:
            if evidence.depth == 1:
                top_level_markers.append(
                    (feature["reading_order_index"], (evidence.kind, evidence.token))
                )

    numbered_orders = [item.order for item in numbered_headers]
    outline_positions: dict[tuple[int, str], list[int]] = {}
    for position, item in enumerate(outlines):
        outline_positions.setdefault((item["physical_page"], item["normalized_title"]), []).append(
            position
        )
    next_outline_boundary = _next_equal_or_shallower_positions(outlines)
    feature_orders: dict[tuple[int, str], list[int]] = {}
    for feature in features:
        if feature["outline_state"] == "unique_exact":
            feature_orders.setdefault(
                (feature["physical_page"], feature["normalized_text"]), []
            ).append(feature["reading_order_index"])

    return NumberingCandidateIndex(
        anchors=tuple(anchors),
        numbered_headers=tuple(numbered_headers),
        numbered_orders=tuple(numbered_orders),
        top_level_markers=tuple(top_level_markers),
        outline_positions={key: tuple(value) for key, value in outline_positions.items()},
        next_outline_boundary=tuple(next_outline_boundary),
        feature_orders={key: tuple(value) for key, value in feature_orders.items()},
    )


def _discover_nested_candidates(
    index: NumberingCandidateIndex,
    outlines: tuple[JsonObject, ...],
    after_last: int,
) -> list[NumberingScopeCandidate]:
    """Evaluate indexed anchors while maintaining prefix marker counts."""
    candidates: list[NumberingScopeCandidate] = []
    marker_cursor = 0
    marker_total = 0
    marker_counts: dict[tuple[str, str | None], int] = {}
    for anchor_index, anchor in enumerate(index.anchors):
        anchor_order = anchor["reading_order_index"]
        while (
            marker_cursor < len(index.top_level_markers)
            and index.top_level_markers[marker_cursor][0] < anchor_order
        ):
            marker = index.top_level_markers[marker_cursor][1]
            marker_total += 1
            marker_counts[marker] = marker_counts.get(marker, 0) + 1
            marker_cursor += 1
        next_anchor_order = (
            index.anchors[anchor_index + 1]["reading_order_index"]
            if anchor_index + 1 < len(index.anchors)
            else after_last
        )
        numbered_position = bisect_right(index.numbered_orders, anchor_order)
        if numbered_position >= len(index.numbered_headers):
            continue
        numbered_header = index.numbered_headers[numbered_position]
        if numbered_header.order >= next_anchor_order:
            continue
        numbered = numbered_header.feature
        evidence = numbered_header.evidence
        is_start = (evidence.kind == "article" and evidence.token == "1") or (
            evidence.kind == "decimal" and evidence.token == "1" and evidence.depth == 1
        )
        proposed_marker = (evidence.kind, evidence.token)
        if not is_start or marker_total == marker_counts.get(proposed_marker, 0):
            continue
        matching_positions = index.outline_positions.get(
            (anchor["physical_page"], anchor["normalized_text"]), ()
        )
        if len(matching_positions) != 1:
            continue
        outline_position = matching_positions[0]
        boundary_position = index.next_outline_boundary[outline_position]
        if boundary_position is None:
            end = after_last
        else:
            later_boundary = outlines[boundary_position]
            end_matches = index.feature_orders.get(
                (later_boundary["physical_page"], later_boundary["normalized_title"]), ()
            )
            if len(end_matches) != 1:
                continue
            end = end_matches[0]
        if numbered["reading_order_index"] < end:
            candidates.append(
                NumberingScopeCandidate(
                    start=numbered["reading_order_index"],
                    end=end,
                    anchor_key=anchor["stable_item_key"],
                    article=evidence.kind == "article",
                )
            )
    return candidates


def _next_equal_or_shallower_positions(
    outlines: tuple[JsonObject, ...],
) -> list[int | None]:
    """Return the nearest later outline at the same or a shallower raw depth."""
    result: list[int | None] = [None] * len(outlines)
    stack: list[int] = []
    for position in range(len(outlines) - 1, -1, -1):
        depth = outlines[position]["raw_depth"]
        while stack and outlines[stack[-1]]["raw_depth"] > depth:
            stack.pop()
        result[position] = stack[-1] if stack else None
        stack.append(position)
    return result


def _regime_id(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"reg-{hashlib.sha256(data).hexdigest()[:16]}"
