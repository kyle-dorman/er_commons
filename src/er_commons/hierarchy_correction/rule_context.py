"""Precompute immutable indexes and per-item eligibility for R01-R08."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.hierarchy_correction.constants import RULE_ORDER
from er_commons.hierarchy_correction.level_evidence import LevelEvidence, derive_level_evidence
from er_commons.hierarchy_correction.semantic_types import NumberingScopeRecord, ScopedItem

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class RulePolicyContext:
    """Document-wide immutable evidence used by every rule evaluation."""

    features: tuple[ScopedItem, ...]
    regimes_by_id: dict[str, NumberingScopeRecord]
    toc_targets: dict[str, tuple[str, int]]
    levels: LevelEvidence


@dataclass(frozen=True)
class ItemRuleContext:
    """One item's complete ordered eligibility and initial evidence record."""

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
    return RulePolicyContext(
        features=features,
        regimes_by_id=regimes_by_id,
        toc_targets=toc_targets,
        levels=derive_level_evidence(
            features=features,
            toc_targets=toc_targets,
            regimes=regimes_by_id,
        ),
    )


def build_item_rule_context(policy: RulePolicyContext, index: int) -> ItemRuleContext:
    """Evaluate all rule predicates and preserve their frozen precedence."""
    feature = policy.features[index]
    key = feature["stable_item_key"]
    evidence = _base_evidence(feature)
    earlier, later = raw_heading_neighbors(policy.features, index)
    evidence["previous_heading_key"] = earlier and earlier["stable_item_key"]
    evidence["next_heading_key"] = later and later["stable_item_key"]

    picture_owned = feature["raw_parent_ref"].startswith("#/pictures/")
    picture_caption = picture_owned and feature["raw_role"] == "caption"
    body_eligible = bool(
        feature["content_layer"] == "body" and not feature["toc_region"] and not picture_owned
    )
    numbering_level = policy.levels.numbering_levels.get(key)
    predicates = {
        RULE_ORDER[0]: (
            feature["content_layer"] == "furniture"
            or feature["toc_region"]
            or (picture_owned and not picture_caption)
        ),
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
        RULE_ORDER[5]: body_eligible and structural_sibling_pattern(policy.features, index),
        RULE_ORDER[6]: body_eligible and key in policy.levels.transfers,
        RULE_ORDER[7]: True,
    }
    eligible = [rule_id for rule_id in RULE_ORDER if predicates[rule_id]]
    return ItemRuleContext(
        policy=policy,
        index=index,
        feature=feature,
        evidence=evidence,
        eligible_rule_ids=eligible,
        selected_rule_id=eligible[0],
        numbering_level=numbering_level,
    )


def raw_heading_neighbors(
    features: tuple[ScopedItem, ...], index: int
) -> tuple[ScopedItem | None, ScopedItem | None]:
    """Return nearest earlier and later raw section headers."""
    earlier = next(
        (item for item in reversed(features[:index]) if item["raw_role"] == "section_header"),
        None,
    )
    later = next(
        (item for item in features[index + 1 :] if item["raw_role"] == "section_header"),
        None,
    )
    return earlier, later


def structural_sibling_pattern(features: tuple[ScopedItem, ...], index: int) -> bool:
    """Evaluate the complete frozen R06 structural-sibling predicate."""
    feature = features[index]
    if feature["raw_role"] != "text" or index == 0 or index == len(features) - 1:
        return False
    previous_item, next_item = features[index - 1], features[index + 1]
    earlier, later = raw_heading_neighbors(features, index)
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
