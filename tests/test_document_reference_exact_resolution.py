"""Focused tests for the shared exact target-resolution engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    ExactResolutionOutcome,
    TextMatchRule,
    resolve_exact_aliases,
)
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.document_records.document_references.machine_link_resolution import (
    resolve_machine_index_entries,
)
from er_commons.document_records.document_references.types import TargetIndexEntry

ROOT = Path(__file__).parents[1]


def _policy():
    return load_document_linking_policy(
        ROOT / "configs/linking_policies/document_linking_v1.json",
        schema_path=(
            ROOT / "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json"
        ),
    )


def _alias(
    text: str,
    target: str = "section-1",
    *,
    alias_id: str = "alias-1",
    page: str = "page-1",
    parent: str | None = None,
) -> ExactAliasEvidence:
    return ExactAliasEvidence(
        lookup_keys=(text,),
        target_type="section",
        alias_id=alias_id,
        target_id=target,
        target_page_ids=(page,),
        parent_target_id=parent,
    )


@pytest.mark.parametrize(
    ("query", "target", "rule"),
    [
        (
            "0.4.3 Transit Destinations",
            "0.4.3 Transit Destinations.",
            TextMatchRule.TERMINAL_PERIOD,
        ),
        (
            "0.5.3 Active Transportation & Transit",
            "0.5.3 Active Transportation and Transit",
            TextMatchRule.AMPERSAND_AND,
        ),
        (
            "3.4.2 Residential Flex Space",
            "3.4.2 Residential Flex-Space",
            TextMatchRule.ALPHABETIC_HYPHEN,
        ),
        (
            "3.6.5 Duplex/Single Family",
            "3.6.5 Duplex / Single Family",
            TextMatchRule.SLASH_WHITESPACE,
        ),
        ("8.3.9 Traffi c Reduction", "8.3.9 Traffic Reduction", TextMatchRule.SPLIT_FI_LIGATURE),
        (
            "9.3.3 Conditions, Covenants and Restrictions",
            "9.3.3 Conditions, Covenants, and Restrictions",
            TextMatchRule.OPTIONAL_COMMA_BEFORE_AND,
        ),
        (
            "2.2.2 Preserve the City’s Character",
            "2.2.2 Preserve the City's Character.",
            TextMatchRule.APOSTROPHE_AND_TERMINAL_PERIOD,
        ),
    ],
)
def test_each_mechanical_rule_is_a_whole_string_fallback(
    query: str, target: str, rule: TextMatchRule
) -> None:
    decision = resolve_exact_aliases(
        lookup_text=query,
        target_type="section",
        aliases=(_alias(target),),
        fallback_rules=(rule,),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["section-1"]
    assert decision.match_basis == (rule.value,)


def test_exact_match_wins_without_running_fallbacks() -> None:
    decision = resolve_exact_aliases(
        lookup_text="3.4.2 Residential Flex Space",
        target_type="section",
        aliases=(
            _alias("3.4.2 Residential Flex Space", "exact"),
            _alias("3.4.2 Residential Flex-Space", "fallback", alias_id="alias-2"),
        ),
        fallback_rules=tuple(TextMatchRule),
    )

    assert [candidate.target_id for candidate in decision.candidates] == ["exact"]
    assert decision.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert decision.match_basis == ("exact",)


def test_goal_prefix_composes_with_ligature_period_and_apostrophe_fixes() -> None:
    cases = (
        (
            "2.2.1 Development Requirements of the Specifi c Plan",
            "GOAL 2.2.1: Development Requirements of the Specific Plan",
            "goal_prefix+split_fi_ligature",
        ),
        (
            "3.2.1 Create a Mixed-Use District",
            "GOAL 3.2.1: Create a Mixed-Use District.",
            "goal_prefix+terminal_period",
        ),
        (
            "2.2.2 Preserve the City’s Character",
            "GOAL 2.2.2: Preserve the City's Character.",
            "goal_prefix+apostrophe_and_terminal_period",
        ),
    )
    for query, target, basis in cases:
        decision = resolve_exact_aliases(
            lookup_text=query,
            target_type="section",
            aliases=(_alias(target),),
            fallback_rules=tuple(TextMatchRule),
            allow_goal_prefix=True,
        )
        assert [candidate.target_id for candidate in decision.candidates] == ["section-1"]
        assert basis in decision.match_basis


def test_fallback_evidence_is_unioned_before_cardinality_decision() -> None:
    decision = resolve_exact_aliases(
        lookup_text="Heading & Name",
        target_type="section",
        aliases=(
            _alias("Heading and Name", "target-a"),
            _alias("Heading & Name.", "target-b", alias_id="alias-2"),
        ),
        fallback_rules=(TextMatchRule.AMPERSAND_AND, TextMatchRule.TERMINAL_PERIOD),
    )

    assert [candidate.target_id for candidate in decision.candidates] == [
        "target-a",
        "target-b",
    ]
    assert decision.outcome is ExactResolutionOutcome.AMBIGUOUS_TARGET


def test_multiple_alias_rows_for_one_target_remain_one_candidate() -> None:
    decision = resolve_exact_aliases(
        lookup_text="1.2 Same Heading",
        target_type="section",
        aliases=(
            _alias("1.2 Same Heading", alias_id="alias-1"),
            _alias("1.2 Same Heading", alias_id="alias-2"),
        ),
    )

    assert len(decision.candidates) == 1
    assert decision.candidates[0].alias_ids == ("alias-1", "alias-2")


def test_parent_scope_and_page_intersection_only_narrow_candidates() -> None:
    aliases = (
        _alias("a. Existing Conditions", "child-a", parent="parent-a", page="page-1"),
        _alias(
            "a. Existing Conditions",
            "child-b",
            alias_id="alias-2",
            parent="parent-b",
            page="page-2",
        ),
    )
    parent_scoped = resolve_exact_aliases(
        lookup_text="a. Existing Conditions",
        target_type="section",
        aliases=aliases,
        parent_target_ids=("parent-b",),
    )
    page_scoped = resolve_exact_aliases(
        lookup_text="a. Existing Conditions",
        target_type="section",
        aliases=aliases,
        destination_page_ids=("page-1",),
    )

    assert [candidate.target_id for candidate in parent_scoped.candidates] == ["child-b"]
    assert [candidate.target_id for candidate in page_scoped.candidates] == ["child-a"]
    assert parent_scoped.parent_scope_applied is True
    assert page_scoped.destination_page_intersection_applied is True


def test_parent_scope_fails_closed_when_hierarchy_disagrees() -> None:
    decision = resolve_exact_aliases(
        lookup_text="a. Existing Conditions",
        target_type="section",
        aliases=(
            _alias("a. Existing Conditions", "child-a", parent="other-parent"),
            _alias(
                "a. Existing Conditions",
                "child-b",
                alias_id="alias-2",
                parent="another-parent",
            ),
        ),
        parent_target_ids=("expected-parent",),
    )

    assert decision.candidates == ()
    assert decision.outcome is ExactResolutionOutcome.PARENT_SCOPE_MISMATCH
    assert decision.unscoped_text_candidate_count == 2
    assert decision.scoped_text_candidate_count == 0


def test_unique_heading_survives_noisy_parent_relation() -> None:
    decision = resolve_exact_aliases(
        lookup_text="a. Existing Conditions",
        target_type="section",
        aliases=(_alias("a. Existing Conditions", parent="noisy-parent"),),
        parent_target_ids=("expected-parent",),
    )

    assert decision.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert decision.parent_scope_applied is False


def test_destination_mismatch_is_distinct_from_missing_text_alias() -> None:
    mismatch = resolve_exact_aliases(
        lookup_text="4.2.1 Soil Conditions",
        target_type="section",
        aliases=(_alias("4.2.1 Soil Conditions", page="page-38"),),
        destination_page_ids=("page-39",),
    )
    no_alias = resolve_exact_aliases(
        lookup_text="4.2.2 Groundwater",
        target_type="section",
        aliases=(_alias("4.2.1 Soil Conditions", page="page-38"),),
        destination_page_ids=("page-39",),
    )

    assert mismatch.candidates == ()
    assert mismatch.outcome is ExactResolutionOutcome.DESTINATION_PAGE_MISMATCH
    assert mismatch.scoped_text_candidate_count == 1
    assert no_alias.outcome is ExactResolutionOutcome.NO_TEXT_MATCH
    assert no_alias.scoped_text_candidate_count == 0


def test_empty_destination_scope_is_not_the_same_as_no_destination_scope() -> None:
    aliases = (_alias("4.2.1 Soil Conditions", page="page-38"),)

    unscoped = resolve_exact_aliases(
        lookup_text="4.2.1 Soil Conditions",
        target_type="section",
        aliases=aliases,
        destination_page_ids=None,
    )
    empty_scope = resolve_exact_aliases(
        lookup_text="4.2.1 Soil Conditions",
        target_type="section",
        aliases=aliases,
        destination_page_ids=(),
    )

    assert unscoped.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
    assert empty_scope.outcome is ExactResolutionOutcome.DESTINATION_PAGE_MISMATCH


def test_alias_and_fallback_discovery_order_do_not_change_the_decision() -> None:
    aliases = (
        _alias("Heading and Name", "target-a"),
        _alias("Heading & Name.", "target-b", alias_id="alias-2"),
    )
    rules = (TextMatchRule.AMPERSAND_AND, TextMatchRule.TERMINAL_PERIOD)

    forward = resolve_exact_aliases(
        lookup_text="Heading & Name",
        target_type="section",
        aliases=aliases,
        fallback_rules=rules,
    )
    reversed_input = resolve_exact_aliases(
        lookup_text="Heading & Name",
        target_type="section",
        aliases=tuple(reversed(aliases)),
        fallback_rules=tuple(reversed(rules)),
    )

    assert reversed_input == forward


def test_machine_adapter_preserves_structural_lookup_and_target_deduplication() -> None:
    entries = tuple(
        TargetIndexEntry(
            lookup_key="3.1 existing conditions",
            target_type="section",
            alias_origin="upstream_v2",
            alias_record_id=f"alias-{number}",
            target_record_id="section-1",
            upstream_alias_record_id=f"upstream-alias-{number}",
            upstream_target_record_id="upstream-section-1",
            evidence_kind="accepted_v2_alias",
            evidence_source_record_id=None,
            evidence_page_id=None,
        )
        for number in (1, 2)
    )

    decision = resolve_machine_index_entries(
        lookup_key="3.1",
        target_type="section",
        entries=entries,
        policy=_policy(),
    )

    assert len(decision.candidates) == 1
    assert decision.candidates[0].alias_ids == ("alias-1", "alias-2")
