"""General inner-rule integration and the sealed previous-result comparison gate."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from test_task05g_resolver import fixture, population

from er_commons.response_inventory import reference_baseline as baseline
from er_commons.response_inventory.reference_replay_comparison import (
    compare_outcomes,
    validate_result,
)
from er_commons.response_inventory.reference_replay_cycle import compare_rule_cycle
from er_commons.response_inventory.reference_replay_resolver import resolve_references


def appendix_args() -> dict[str, Any]:
    """Provide an arbitrary appendix and an exact named child, without real document IDs."""
    args = fixture("Draft EIR Appendix Z", "document")
    args["catalog"] = {
        "sources": [{"source": {"source_id": "deir_main"}, "reference_aliases": ["Appendix Z"]}]
    }
    args["baseline_outcomes"][0]["terminal_reason"] = (
        "more_specific_appendix_target_requires_resolution"
    )
    args["target_rows"] = [
        {
            "lookup_key": "appendix z",
            "target_id": "document",
            "source_id": "deir_main",
            "target_type": "document",
        },
        {
            "lookup_key": "09 utilities",
            "target_id": "chapter",
            "source_id": "deir_main",
            "target_type": "section",
        },
    ]
    return args


def test_inner_policy_resolves_child_and_preserves_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New policy selects an existing exact child; the old policy remains a protected nonlink."""
    args = appendix_args()
    monkeypatch.setattr(
        baseline,
        "_mention_contexts",
        lambda rows: {
            "span-1": baseline._MentionContext("Chapter 09, Utilities, was included in ", "")
        },
    )
    old = resolve_references(**args)
    assert old["outcomes"][0]["outcome"] == "terminal_nonlink"
    result = resolve_references(**args, inner_references=True)
    assert result["outcomes"][0]["compatible_target_ids"] == ["chapter"]
    assert result["outcomes"][0]["requested_target_type"] == "section"
    assert (
        result["links"][0]["target_annotation"]["fresh_review_status"]
        == "no_fresh_task06h_target_review"
    )
    validate_result(result, args["baseline_outcomes"], population(args), expected_result=result)
    comparison = compare_outcomes(
        args["baseline_outcomes"],
        result["outcomes"],
        population=population(args),
        correspondence={"target_mapping": []},
        approved_inner_rules=True,
    )
    assert comparison["classifications"] == {"approved_general_inner_reference": 1}
    with pytest.raises(ValueError, match="delta"):
        compare_outcomes(
            args["baseline_outcomes"],
            result["outcomes"],
            population=population(args),
            correspondence={"target_mapping": []},
        )


def test_general_guard_does_not_treat_ordinary_word_as_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The new guard fixes prose, while true identifiers still block generic fallback."""
    args = appendix_args()
    args["baseline_outcomes"][0]["terminal_reason"] = "upstream_source_identity_repair_required"
    for text, expected in [
        ("The projects in that table are included in ", "resolved"),
        ("Table A of ", "terminal_nonlink"),
        ("Figure 7 of ", "terminal_nonlink"),
    ]:
        monkeypatch.setattr(
            baseline,
            "_mention_contexts",
            lambda rows, text=text: {"span-1": baseline._MentionContext(text, "")},
        )
        result = resolve_references(**args, inner_references=True)
        assert result["outcomes"][0]["outcome"] == expected


@pytest.mark.parametrize("mutation", ["outside", "warning", "lost_link", "target_changed"])
def test_rule_cycle_rejects_out_of_scope_or_inherited_changes(mutation: str) -> None:
    """The selected rule cycle cannot silently broaden scope or weaken previous links."""
    args = fixture()
    before = resolve_references(**args)["outcomes"]
    after = copy.deepcopy(before)
    allowed = ["mention-1"]
    if mutation == "outside":
        allowed = []
        after[0]["terminal_reason"] = "changed"
    elif mutation == "warning":
        after[0]["final_f1_warning"] = {"changed": True}
    elif mutation == "lost_link":
        after[0]["outcome"] = "terminal_nonlink"
    else:
        after[0]["compatible_target_ids"] = ["wrong-target"]
    with pytest.raises(ValueError):
        compare_rule_cycle(before, after, allowed)


def test_rule_cycle_ignores_only_content_address_changes() -> None:
    """A new activity changes link IDs but preserves the exact selected target and policy."""
    rows = resolve_references(**fixture())["outcomes"]
    after = copy.deepcopy(rows)
    after[0]["outcome_id"] = "new-outcome"
    after[0]["link_id"] = "new-link"
    result = compare_rule_cycle(rows, after, [])
    assert result["changed_count"] == 0


def test_existing_outer_links_are_not_reinterpreted_by_nonlink_trial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The general prior guard scopes this trial without changing existing outer links."""
    args = appendix_args()
    args["baseline_outcomes"][0]["terminal_reason"] = "upstream_source_identity_repair_required"
    args["target_rows"].append(
        {
            "lookup_key": "appendix k: detail",
            "target_id": "nested",
            "target_type": "section",
            "source_id": "deir_main",
        }
    )
    monkeypatch.setattr(
        baseline,
        "_mention_contexts",
        lambda rows: {"span-1": baseline._MentionContext("Appendix K to ", "")},
    )
    old = resolve_references(**args)
    new = resolve_references(**args, inner_references=True)
    assert old == new
    assert new["outcomes"][0]["compatible_target_ids"] == ["document"]
