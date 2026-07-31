"""Discover numbering scopes and expose their hierarchy lifecycle events."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from er_commons.hierarchy_correction.semantic_types import (
    NumberingScopeRecord,
    ScopedItem,
    TocClassifiedItem,
)
from er_commons.hierarchy_correction.text_evidence import parse_numbering

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class NumberingScopeAnalysis:
    """Numbering scopes and items assigned to their innermost scope."""

    features: tuple[JsonObject, ...]
    regimes: tuple[JsonObject, ...]

    @property
    def scoped_items(self) -> tuple[ScopedItem, ...]:
        """Expose typed items to the human-owned semantic core."""
        return cast(tuple[ScopedItem, ...], self.features)

    @property
    def numbering_scopes(self) -> tuple[NumberingScopeRecord, ...]:
        """Expose typed scope records to the human-owned semantic core."""
        return cast(tuple[NumberingScopeRecord, ...], self.regimes)


@dataclass(frozen=True)
class NumberingScopeCandidate:
    """Evidence-supported half-open scope proposed before ID assignment."""

    start: int
    end: int
    anchor_key: str
    article: bool


def build_numbering_regimes(
    features: list[TocClassifiedItem], outline_observations: tuple[JsonObject, ...]
) -> NumberingScopeAnalysis:
    """Build the initial regime and evidence-supported nested local regimes."""
    body = [feature for feature in features if feature["content_layer"] == "body"]
    if not body:
        raise ValueError("numbering regimes require one body item")
    initial_start = min(feature["reading_order_index"] for feature in features)
    after_last = max(feature["reading_order_index"] for feature in features) + 1
    candidates = _nested_candidates(features, outline_observations, after_last)
    initial_id = _regime_id({"start": body[0]["stable_item_key"], "kind": "initial"})
    regimes: list[NumberingScopeRecord] = [
        NumberingScopeRecord(
            regime_id=initial_id,
            parent_regime_id=None,
            root_level=1,
            start_item_key=body[0]["stable_item_key"],
            end_item_key=None,
            outline_anchor_key=None,
            page_label_reset=False,
        )
    ]
    interval_by_id = {initial_id: (initial_start, after_last)}
    article_regimes: set[str] = set()
    feature_by_order = {feature["reading_order_index"]: feature for feature in features}
    for candidate in sorted(candidates, key=lambda item: (item.start, -item.end)):
        containing = [
            (regime_id, interval)
            for regime_id, interval in interval_by_id.items()
            if interval[0] < candidate.start < candidate.end <= interval[1]
        ]
        parent_id = max(containing, key=lambda item: item[1][0])[0]
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
        if candidate.article:
            article_regimes.add(regime_id)

    projected: list[ScopedItem] = []
    for feature in features:
        order = feature["reading_order_index"]
        active = [
            (regime_id, interval)
            for regime_id, interval in interval_by_id.items()
            if interval[0] <= order < interval[1]
        ]
        regime_id = max(active, key=lambda item: item[1][0])[0]
        copy = cast(ScopedItem, dict(feature, regime_id=regime_id))
        if regime_id in article_regimes and copy["raw_role"] == "section_header":
            evidence = parse_numbering(copy["text"], raw_role=copy["raw_role"], article_regime=True)
            copy["numbering_kind"] = evidence.kind
            copy["numbering_token"] = evidence.token
            copy["numbering_depth"] = evidence.depth
        projected.append(copy)
    return NumberingScopeAnalysis(
        features=cast(tuple[JsonObject, ...], tuple(projected)),
        regimes=cast(tuple[JsonObject, ...], tuple(regimes)),
    )


def _nested_candidates(
    features: list[TocClassifiedItem], outlines: tuple[JsonObject, ...], after_last: int
) -> list[NumberingScopeCandidate]:
    anchors = [
        feature
        for feature in features
        if feature["content_layer"] == "body"
        and not feature.get("toc_region", False)
        and feature["outline_state"] == "unique_exact"
    ]
    candidates: list[NumberingScopeCandidate] = []
    for anchor_index, anchor in enumerate(anchors):
        next_anchor_order = (
            anchors[anchor_index + 1]["reading_order_index"]
            if anchor_index + 1 < len(anchors)
            else after_last
        )
        numbered = next(
            (
                feature
                for feature in features
                if (
                    anchor["reading_order_index"]
                    < feature["reading_order_index"]
                    < next_anchor_order
                )
                and feature["content_layer"] == "body"
                and feature["raw_role"] == "section_header"
                and _is_nonbullet_numbered(feature)
            ),
            None,
        )
        if numbered is None:
            continue
        evidence = parse_numbering(numbered["text"], raw_role=numbered["raw_role"])
        is_start = (evidence.kind == "article" and evidence.token == "1") or (
            evidence.kind == "decimal" and evidence.token == "1" and evidence.depth == 1
        )
        if not is_start or not _active_regime_has_different_marker(features, anchor, numbered):
            continue
        outline_matches = [
            item
            for item in outlines
            if item["physical_page"] == anchor["physical_page"]
            and item["normalized_title"] == anchor["normalized_text"]
        ]
        if len(outline_matches) != 1:
            continue
        outline = outline_matches[0]
        outline_position = next(
            index
            for index, item in enumerate(outlines)
            if item["outline_id"] == outline["outline_id"]
        )
        later_boundary = next(
            (
                item
                for item in outlines[outline_position + 1 :]
                if item["raw_depth"] <= outline["raw_depth"]
            ),
            None,
        )
        if later_boundary is None:
            end = after_last
        else:
            end_matches = [
                feature
                for feature in features
                if feature["physical_page"] == later_boundary["physical_page"]
                and feature["normalized_text"] == later_boundary["normalized_title"]
                and feature["outline_state"] == "unique_exact"
            ]
            if len(end_matches) != 1:
                continue
            end = end_matches[0]["reading_order_index"]
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


def _active_regime_has_different_marker(
    features: list[TocClassifiedItem],
    anchor: TocClassifiedItem,
    start: TocClassifiedItem,
) -> bool:
    proposed = parse_numbering(start["text"], raw_role=start["raw_role"])
    for feature in features:
        if feature["reading_order_index"] >= anchor["reading_order_index"]:
            break
        if feature["raw_role"] != "section_header" or feature.get("toc_region", False):
            continue
        evidence = parse_numbering(feature["text"], raw_role=feature["raw_role"])
        if evidence.kind in {"article", "decimal"} and evidence.depth == 1:
            if (evidence.kind, evidence.token) != (proposed.kind, proposed.token):
                return True
    return False


def _is_nonbullet_numbered(feature: TocClassifiedItem) -> bool:
    evidence = parse_numbering(feature["text"], raw_role=feature["raw_role"])
    return evidence.kind not in {"none", "bullet"}


def _regime_id(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"reg-{hashlib.sha256(data).hexdigest()[:16]}"
