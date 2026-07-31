"""Apply each named correction rule after eligibility and precedence are fixed."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from er_commons.hierarchy_correction.constants import RULE_ORDER
from er_commons.hierarchy_correction.rule_context import ItemRuleContext
from er_commons.hierarchy_correction.semantic_types import (
    CorrectionDecisionRecord,
    DiagnosticRecord,
)

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class RuleApplication:
    """One selected decision and any terminal ambiguity it emits."""

    decision: CorrectionDecisionRecord
    ambiguities: tuple[DiagnosticRecord, ...] = ()


RuleApplicationFunction = Callable[[ItemRuleContext], RuleApplication]


def apply_selected_rule(context: ItemRuleContext) -> RuleApplication:
    """Dispatch one item to the first eligible rule's explicit implementation."""
    return _APPLICATIONS[context.selected_rule_id](context)


def _r01_exclude(context: ItemRuleContext) -> RuleApplication:
    return RuleApplication(_decision(context, role="excluded", level=None, outcome="applied"))


def _r02_demote_bullet(context: ItemRuleContext) -> RuleApplication:
    feature = context.feature
    features = context.policy.features
    raw_level = feature["raw_level"]
    boundary = next(
        (
            cursor
            for cursor in range(context.index + 1, len(features))
            if features[cursor]["physical_page"] != feature["physical_page"]
            or (
                features[cursor]["raw_role"] == "section_header"
                and isinstance((candidate_level := features[cursor]["raw_level"]), int)
                and isinstance(raw_level, int)
                and candidate_level <= raw_level
            )
        ),
        len(features),
    )
    indented = next(
        (
            item
            for item in features[context.index + 1 : boundary]
            if item["raw_role"] == "list_item" and item["left_pt"] - feature["left_pt"] >= 18
        ),
        None,
    )
    evidence = context.evidence
    evidence["next_item_key"] = indented and indented["stable_item_key"]
    evidence["next_list_indent_delta_pt"] = (
        indented["left_pt"] - feature["left_pt"] if indented else None
    )
    evidence["source_item_keys"] += [indented["stable_item_key"]] if indented else []
    if indented:
        return RuleApplication(_decision(context, role="content", level=None, outcome="applied"))
    evidence["conflict_codes"] = ["SIBLING_EVIDENCE_CONFLICT"]
    ambiguity = _diagnostic(
        context,
        "SIBLING_EVIDENCE_CONFLICT",
        "bullet heading lacks the required indented list evidence",
    )
    return RuleApplication(
        _decision(context, role="content", level=None, outcome="ambiguous"),
        (ambiguity,),
    )


def _r03_apply_outline(context: ItemRuleContext) -> RuleApplication:
    level = context.policy.levels.supported_levels[context.feature["stable_item_key"]]
    context.evidence["outline_level"] = level
    return RuleApplication(_decision(context, role="heading", level=level, outcome="applied"))


def _r04_apply_toc(context: ItemRuleContext) -> RuleApplication:
    toc_id, depth = context.policy.toc_targets[context.feature["stable_item_key"]]
    context.evidence["toc_entry_id"] = toc_id
    return RuleApplication(_decision(context, role="heading", level=depth, outcome="applied"))


def _r05_apply_numbering(context: ItemRuleContext) -> RuleApplication:
    feature = context.feature
    numbering_level = context.numbering_level
    assert numbering_level is not None
    numbering_levels = context.policy.levels.numbering_levels
    previous_numbered = next(
        (
            item
            for item in reversed(context.policy.features[: context.index])
            if item["regime_id"] == feature["regime_id"]
            and item["stable_item_key"] in numbering_levels
        ),
        None,
    )
    previous_level = (
        numbering_levels[previous_numbered["stable_item_key"]] if previous_numbered else None
    )
    invalid_jump = (
        previous_level is None
        and numbering_level != context.policy.regimes_by_id[feature["regime_id"]]["root_level"]
    ) or (previous_level is not None and numbering_level > previous_level + 1)
    if not invalid_jump:
        return RuleApplication(
            _decision(context, role="heading", level=numbering_level, outcome="applied")
        )
    context.evidence["conflict_codes"] = ["NUMBERING_JUMP_UNSUPPORTED"]
    ambiguity = _diagnostic(
        context,
        "NUMBERING_JUMP_UNSUPPORTED",
        "numbering proposal creates an unsupported forward level jump",
    )
    return RuleApplication(
        _decision(context, role="content", level=None, outcome="ambiguous"),
        (ambiguity,),
    )


def _r06_flag_sibling(context: ItemRuleContext) -> RuleApplication:
    context.evidence["conflict_codes"] = ["SIBLING_EVIDENCE_CONFLICT"]
    ambiguity = _diagnostic(
        context,
        "SIBLING_EVIDENCE_CONFLICT",
        "plain text matches the structural-sibling pattern without an anchor",
    )
    return RuleApplication(
        _decision(context, role="content", level=None, outcome="ambiguous"),
        (ambiguity,),
    )


def _r07_transfer_level(context: ItemRuleContext) -> RuleApplication:
    transferred, detail = context.policy.levels.transfers[context.feature["stable_item_key"]]
    if transferred is not None:
        context.evidence["transferred_level"] = transferred
        return RuleApplication(
            _decision(context, role="heading", level=transferred, outcome="applied")
        )
    context.evidence["conflict_codes"] = ["LOCAL_LEVEL_TRANSFER_CONFLICT"]
    ambiguity = _diagnostic(context, "LOCAL_LEVEL_TRANSFER_CONFLICT", detail)
    return RuleApplication(
        _decision(context, role="content", level=None, outcome="ambiguous"),
        (ambiguity,),
    )


def _r08_preserve(context: ItemRuleContext) -> RuleApplication:
    feature = context.feature
    preserve_heading = bool(
        feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and isinstance(feature["raw_level"], int)
        and 1 <= feature["raw_level"] <= 6
    )
    return RuleApplication(
        _decision(
            context,
            role="heading" if preserve_heading else "content",
            level=feature["raw_level"] if preserve_heading else None,
            outcome="unchanged",
        )
    )


def _decision(
    context: ItemRuleContext,
    *,
    role: str,
    level: int | None,
    outcome: str,
) -> CorrectionDecisionRecord:
    feature = context.feature
    return cast(
        CorrectionDecisionRecord,
        {
            "stable_item_key": feature["stable_item_key"],
            "raw_role": feature["raw_role"],
            "corrected_role": role,
            "raw_level": feature["raw_level"],
            "corrected_level": level,
            "outcome": outcome,
            "selected_rule_id": context.selected_rule_id,
            "eligible_rule_ids": context.eligible_rule_ids,
            "evidence": context.evidence,
        },
    )


def _diagnostic(context: ItemRuleContext, code: str, detail: str) -> DiagnosticRecord:
    feature = context.feature
    return DiagnosticRecord(
        reading_order_index=feature["reading_order_index"],
        stable_item_key=feature["stable_item_key"],
        code=code,
        detail=detail,
    )


_APPLICATIONS: dict[str, RuleApplicationFunction] = {
    RULE_ORDER[0]: _r01_exclude,
    RULE_ORDER[1]: _r02_demote_bullet,
    RULE_ORDER[2]: _r03_apply_outline,
    RULE_ORDER[3]: _r04_apply_toc,
    RULE_ORDER[4]: _r05_apply_numbering,
    RULE_ORDER[5]: _r06_flag_sibling,
    RULE_ORDER[6]: _r07_transfer_level,
    RULE_ORDER[7]: _r08_preserve,
}
