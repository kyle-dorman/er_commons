"""Precompute immutable indexes and per-item eligibility for R01-R08."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.hierarchy_inference.constants import RULE_ORDER
from er_commons.hierarchy_inference.level_evidence import LevelEvidence, derive_level_evidence
from er_commons.hierarchy_inference.semantic_types import NumberingScopeRecord, ScopedItem

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class RulePolicyContext:
    """Document-wide immutable evidence used by every rule evaluation."""

    features: tuple[ScopedItem, ...]
    regimes_by_id: dict[str, NumberingScopeRecord]
    toc_targets: dict[str, tuple[str, int]]
    levels: LevelEvidence
    previous_raw_headings: tuple[ScopedItem | None, ...]
    next_raw_headings: tuple[ScopedItem | None, ...]
    previous_numbering_levels: dict[str, int | None]


@dataclass
class RuleEvaluationState:
    """Mutable evidence and fixed eligibility while one rule is applied."""

    policy: RulePolicyContext
    index: int
    feature: ScopedItem
    evidence: JsonRecord
    eligible_rule_ids: list[str]
    selected_rule_id: str
    numbering_level: int | None


def build_rule_policy_context(
    *,
    features: tuple[ScopedItem, ...],
    toc_entries: tuple[JsonRecord, ...],
    reconciliations: tuple[JsonRecord, ...],
    regimes: tuple[NumberingScopeRecord, ...],
) -> RulePolicyContext:
    """Build document-wide indexes without consulting corrected decisions."""
    regimes_by_id = {item["regime_id"]: item for item in regimes}
    toc_targets = _exact_toc_targets(toc_entries, reconciliations)
    levels = derive_level_evidence(
        features=features,
        toc_targets=toc_targets,
        regimes=regimes_by_id,
    )
    previous_headings, next_headings = _raw_heading_neighbor_indexes(features)
    return RulePolicyContext(
        features=features,
        regimes_by_id=regimes_by_id,
        toc_targets=toc_targets,
        levels=levels,
        previous_raw_headings=previous_headings,
        next_raw_headings=next_headings,
        previous_numbering_levels=_previous_numbering_levels(features, levels.numbering_levels),
    )


def build_item_rule_context(policy: RulePolicyContext, index: int) -> RuleEvaluationState:
    """Evaluate all rule predicates and preserve their frozen precedence."""
    feature = policy.features[index]
    key = feature["stable_item_key"]
    evidence = _base_evidence(feature)
    earlier = policy.previous_raw_headings[index]
    later = policy.next_raw_headings[index]
    evidence["previous_heading_key"] = earlier and earlier["stable_item_key"]
    evidence["next_heading_key"] = later and later["stable_item_key"]

    picture_owned = feature["raw_parent_ref"].startswith("#/pictures/")
    picture_caption = picture_owned and feature["raw_role"] == "caption"
    body_eligible = bool(
        feature["content_layer"] == "body" and not feature["toc_region"] and not picture_owned
    )
    numbering_level = policy.levels.numbering_levels.get(key)
    predicates = {
        RULE_ORDER[0]: not picture_caption
        and (feature["content_layer"] == "furniture" or feature["toc_region"] or picture_owned),
        RULE_ORDER[1]: bool(
            body_eligible
            and feature["raw_role"] == "section_header"
            and feature["numbering_kind"] == "bullet"
            and feature["outline_state"] != "unique_exact"
            and key not in policy.toc_targets
        ),
        RULE_ORDER[2]: body_eligible and feature["outline_state"] == "unique_exact",
        RULE_ORDER[3]: body_eligible and key in policy.toc_targets,
        RULE_ORDER[4]: body_eligible and numbering_level is not None,
        RULE_ORDER[5]: body_eligible
        and structural_sibling_pattern(policy.features, index, earlier=earlier, later=later),
        RULE_ORDER[6]: body_eligible and key in policy.levels.transfers,
        RULE_ORDER[7]: True,
    }
    eligible = [rule_id for rule_id in RULE_ORDER if predicates[rule_id]]
    return RuleEvaluationState(
        policy=policy,
        index=index,
        feature=feature,
        evidence=evidence,
        eligible_rule_ids=eligible,
        selected_rule_id=eligible[0],
        numbering_level=numbering_level,
    )


def _raw_heading_neighbor_indexes(
    features: tuple[ScopedItem, ...],
) -> tuple[tuple[ScopedItem | None, ...], tuple[ScopedItem | None, ...]]:
    """Build nearest-heading references with one forward and one reverse pass."""
    previous: list[ScopedItem | None] = []
    heading: ScopedItem | None = None
    for feature in features:
        previous.append(heading)
        if feature["raw_role"] == "section_header":
            heading = feature

    following: list[ScopedItem | None] = [None] * len(features)
    heading = None
    for index in range(len(features) - 1, -1, -1):
        following[index] = heading
        feature = features[index]
        if feature["raw_role"] == "section_header":
            heading = feature
    return tuple(previous), tuple(following)


def _previous_numbering_levels(
    features: tuple[ScopedItem, ...], numbering_levels: dict[str, int]
) -> dict[str, int | None]:
    """Index the previous numbered level inside each regime for R05."""
    previous_by_key: dict[str, int | None] = {}
    latest_by_regime: dict[str, int] = {}
    for feature in features:
        key = feature["stable_item_key"]
        if key not in numbering_levels:
            continue
        regime_id = feature["regime_id"]
        previous_by_key[key] = latest_by_regime.get(regime_id)
        latest_by_regime[regime_id] = numbering_levels[key]
    return previous_by_key


def structural_sibling_pattern(
    features: tuple[ScopedItem, ...],
    index: int,
    *,
    earlier: ScopedItem | None,
    later: ScopedItem | None,
) -> bool:
    """Evaluate the complete frozen R06 structural-sibling predicate."""
    feature = features[index]
    if feature["raw_role"] != "text" or index == 0 or index == len(features) - 1:
        return False
    previous_item, next_item = features[index - 1], features[index + 1]
    return bool(
        earlier
        and later
        and earlier["physical_page"] == feature["physical_page"] == later["physical_page"]
        and earlier["raw_level"] == later["raw_level"]
        and abs(earlier["left_pt"] - feature["left_pt"]) <= 1
        and abs(later["left_pt"] - feature["left_pt"]) <= 1
        and previous_item["content_layer"] == next_item["content_layer"] == "body"
        and previous_item["raw_role"] == next_item["raw_role"] == "text"
        and bool(previous_item["normalized_text"])
        and bool(next_item["normalized_text"])
        and feature["layout_state"] == "unique_aligned"
        and len(feature["text"]) <= 160
        and feature["numbering_kind"] == "none"
        and feature["outline_state"] == "absent"
        and not feature["toc_region"]
    )


def _base_evidence(feature: ScopedItem) -> JsonRecord:
    return {
        "source_item_keys": [feature["stable_item_key"]],
        "outline_level": None,
        "toc_entry_id": None,
        "numbering_kind": feature["numbering_kind"],
        "numbering_depth": feature["numbering_depth"],
        "previous_heading_key": None,
        "next_heading_key": None,
        "next_item_key": None,
        "left_delta_before_pt": None,
        "left_delta_after_pt": None,
        "next_list_indent_delta_pt": None,
        "transferred_level": None,
        "conflict_codes": [],
    }


def _exact_toc_targets(
    toc_entries: tuple[JsonRecord, ...], reconciliations: tuple[JsonRecord, ...]
) -> dict[str, tuple[str, int]]:
    entries = {item["toc_entry_id"]: item for item in toc_entries}
    targets: dict[str, tuple[str, int]] = {}
    for reconciliation in reconciliations:
        if reconciliation["state"] != "exact":
            continue
        target = reconciliation["target_key"]
        entry_id = reconciliation["toc_entry_id"]
        if target in targets:
            raise ValueError(f"multiple exact TOC anchors target one item: {target}")
        targets[target] = (entry_id, entries[entry_id]["depth"])
    return targets
