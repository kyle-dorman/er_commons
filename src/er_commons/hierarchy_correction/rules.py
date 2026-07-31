"""Named validators for the eight deterministic correction rules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from er_commons.hierarchy_correction.bundle import CorrectionBundleView, JsonRecord
from er_commons.hierarchy_correction.checks import require
from er_commons.hierarchy_correction.constants import ANCHOR_RULES
from er_commons.hierarchy_correction.level_evidence import calibrated_numbering_levels


@dataclass(frozen=True)
class RuleContext:
    """Shared indexes needed to audit one selected rule."""

    view: CorrectionBundleView
    exact_toc_targets: frozenset[str]
    exact_reconciliations_by_toc: dict[str, JsonRecord]
    numbering_levels_by_key: dict[str, int]


RuleValidator = Callable[[JsonRecord, JsonRecord, RuleContext], None]


def _validate_r01(feature: JsonRecord, decision: JsonRecord, _: RuleContext) -> None:
    """R01 excludes furniture, TOC items, and non-caption picture text."""
    key = decision["stable_item_key"]
    picture_owned = feature["raw_parent_ref"].startswith("#/pictures/")
    picture_caption = picture_owned and feature["raw_role"] == "caption"
    must_exclude = (
        feature["content_layer"] == "furniture"
        or feature["toc_region"]
        or (picture_owned and not picture_caption)
    )
    require(must_exclude, f"R01 selected for body item: {key}")
    require(decision["corrected_role"] == "excluded", f"R01 role differs: {key}")


def _validate_r02(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R02 demotes only unsupported bullet-shaped raw headings."""
    key = decision["stable_item_key"]
    evidence = decision["evidence"]
    require(feature["raw_role"] == "section_header", f"R02 raw role differs: {key}")
    require(feature["numbering_kind"] == "bullet", f"R02 marker differs: {key}")
    require(evidence["numbering_kind"] == "bullet", f"R02 evidence differs: {key}")
    require(feature["outline_state"] != "unique_exact", f"R02 outline anchor exists: {key}")
    require(key not in context.exact_toc_targets, f"R02 TOC anchor exists: {key}")
    require(decision["corrected_role"] == "content", f"R02 role differs: {key}")
    if decision["outcome"] == "applied":
        indent = evidence["next_list_indent_delta_pt"]
        require(indent is not None and indent >= 18, f"R02 indent evidence differs: {key}")


def _validate_r03(feature: JsonRecord, decision: JsonRecord, _: RuleContext) -> None:
    """R03 applies one unique outline anchor and its effective depth."""
    key = decision["stable_item_key"]
    outline_level = decision["evidence"]["outline_level"]
    require(feature["outline_state"] == "unique_exact", f"R03 outline differs: {key}")
    require(outline_level is not None, f"R03 evidence absent: {key}")
    require(decision["corrected_role"] == "heading", f"R03 role differs: {key}")
    require(decision["corrected_level"] == outline_level, f"R03 level differs: {key}")


def _validate_r04(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R04 applies one exact visible-TOC reconciliation."""
    key = decision["stable_item_key"]
    toc_id = decision["evidence"]["toc_entry_id"]
    require(feature["outline_state"] != "unique_exact", f"higher outline rule exists: {key}")
    require(toc_id in context.exact_reconciliations_by_toc, f"R04 anchor absent: {key}")
    reconciliation = context.exact_reconciliations_by_toc[toc_id]
    require(reconciliation["target_key"] == key, f"R04 target differs: {key}")
    require(decision["corrected_role"] == "heading", f"R04 role differs: {key}")
    toc_depth = context.view.toc_entries_by_id[toc_id]["depth"]
    require(decision["corrected_level"] == toc_depth, f"R04 level differs: {key}")


def _validate_r05(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R05 applies numbering depth inside the feature's active regime."""
    key = decision["stable_item_key"]
    evidence = decision["evidence"]
    _require_no_higher_anchor(feature, key, context)
    require(feature["raw_role"] == "section_header", f"R05 raw role differs: {key}")
    require(
        evidence["numbering_kind"] == feature["numbering_kind"] != "none",
        f"R05 numbering differs: {key}",
    )
    require(
        evidence["numbering_depth"] == feature["numbering_depth"],
        f"R05 depth differs: {key}",
    )
    require(decision["corrected_role"] == "heading", f"R05 role differs: {key}")
    expected_level = context.numbering_levels_by_key[key]
    require(decision["corrected_level"] == expected_level, f"R05 level differs: {key}")


def _validate_r06(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R06 preserves unsupported plain-text structure as explicit ambiguity."""
    key = decision["stable_item_key"]
    _require_no_higher_anchor(feature, key, context)
    require(feature["raw_role"] == "text", f"R06 raw role differs: {key}")
    require(decision["outcome"] == "ambiguous", f"R06 outcome differs: {key}")
    require(decision["corrected_role"] == "content", f"R06 role differs: {key}")


def _validate_r07(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R07 transfers one evidence-supported local sibling level."""
    key = decision["stable_item_key"]
    transferred_level = decision["evidence"]["transferred_level"]
    _require_no_higher_anchor(feature, key, context)
    require(feature["raw_role"] == "section_header", f"R07 raw role differs: {key}")
    if transferred_level is None:
        require(
            decision["evidence"]["conflict_codes"] == ["LOCAL_LEVEL_TRANSFER_CONFLICT"],
            f"R07 transfer conflict differs: {key}",
        )
        require(decision["outcome"] == "ambiguous", f"R07 conflict outcome differs: {key}")
        require(decision["corrected_role"] == "content", f"R07 conflict role differs: {key}")
        require(decision["corrected_level"] is None, f"R07 conflict level differs: {key}")
        return
    require(decision["corrected_role"] == "heading", f"R07 role differs: {key}")
    require(decision["corrected_level"] == transferred_level, f"R07 level differs: {key}")


def _validate_r08(feature: JsonRecord, decision: JsonRecord, context: RuleContext) -> None:
    """R08 preserves the remaining schema-valid raw role and level."""
    key = decision["stable_item_key"]
    _require_no_higher_anchor(feature, key, context)
    require(decision["outcome"] == "unchanged", f"R08 outcome differs: {key}")
    if feature["content_layer"] == "body" and feature["raw_role"] == "section_header":
        require(decision["corrected_role"] == "heading", f"R08 role differs: {key}")
        require(
            decision["corrected_level"] == feature["raw_level"],
            f"R08 level differs: {key}",
        )
    else:
        require(decision["corrected_role"] == "content", f"R08 role differs: {key}")


def _require_no_higher_anchor(
    feature: JsonRecord,
    key: str,
    context: RuleContext,
) -> None:
    """Reject a lower-precedence rule when R03 or R04 was eligible."""
    require(feature["outline_state"] != "unique_exact", f"higher outline rule exists: {key}")
    require(key not in context.exact_toc_targets, f"higher TOC rule exists: {key}")


RULE_VALIDATORS: dict[str, RuleValidator] = {
    "R01_EXCLUDE_NON_BODY_OR_TOC": _validate_r01,
    "R02_DEMOTE_BULLET_HEADING": _validate_r02,
    "R03_APPLY_EXACT_OUTLINE_ANCHOR": _validate_r03,
    "R04_APPLY_EXACT_TOC_ANCHOR": _validate_r04,
    "R05_APPLY_NUMBERING_REGIME": _validate_r05,
    "R06_FLAG_STRUCTURAL_AMBIGUITY": _validate_r06,
    "R07_TRANSFER_LOCAL_HEADING_LEVEL": _validate_r07,
    "R08_DEFAULT_PRESERVE": _validate_r08,
}


def selected_rules_follow_policy(view: CorrectionBundleView) -> None:
    """Dispatch each decision to its named, auditable rule validator."""
    exact_by_toc = view.exact_reconciliations_by_toc
    context = RuleContext(
        view=view,
        exact_toc_targets=frozenset(item["target_key"] for item in exact_by_toc.values()),
        exact_reconciliations_by_toc=exact_by_toc,
        numbering_levels_by_key=_calibrated_numbering_levels(view),
    )
    for decision in view.decisions:
        key = decision["stable_item_key"]
        feature = view.features_by_key[key]
        selected_rule = decision["selected_rule_id"]
        RULE_VALIDATORS[selected_rule](feature, decision, context)


def _calibrated_numbering_levels(view: CorrectionBundleView) -> dict[str, int]:
    """Derive R05 levels from the shared immutable level-evidence policy."""
    exact_targets = {
        item["target_key"]: (toc_id, view.toc_entries_by_id[toc_id]["depth"])
        for toc_id, item in view.exact_reconciliations_by_toc.items()
    }
    article_regimes = {
        item["regime_id"] for item in view.features if item["numbering_kind"] == "article"
    }
    return calibrated_numbering_levels(
        view.features,
        exact_targets,
        view.regimes_by_id,
        article_regimes,
    )


def exact_toc_targets_use_an_anchor_rule(view: CorrectionBundleView) -> None:
    """Require every successful TOC target to select R03 or R04."""
    for reconciliation in view.exact_reconciliations_by_toc.values():
        target_key = reconciliation["target_key"]
        selected_rule = view.decisions_by_key[target_key]["selected_rule_id"]
        require(
            selected_rule in ANCHOR_RULES,
            f"exact TOC target lacks anchor rule: {target_key}",
        )
