"""Synthetic section-collision resolution and comparison scope controls."""

import copy

import pytest
from test_task05g_resolver import fixture, population

from er_commons.response_inventory.reference_replay_comparison import compare_outcomes
from er_commons.response_inventory.reference_replay_cycle import compare_rule_cycle
from er_commons.response_inventory.reference_replay_resolver import resolve_references


def collision_args():
    """Keep two distinct section identities with one qualified header artifact."""
    args = fixture()
    args["target_rows"].append(
        {
            **args["target_rows"][0],
            "target_id": "header-1",
            "header_qualification": {"evidence_record_ids": ["heading", "header-example"]},
        }
    )
    args["baseline_outcomes"] = resolve_references(**args)["outcomes"]
    return args


def test_header_policy_preserves_diagnostics_and_review_limits():
    """A collision can resolve without deleting original candidate evidence."""
    args = collision_args()
    original = copy.deepcopy(args)
    result = resolve_references(**args, header_qualification=True)
    row = result["outcomes"][0]
    assert row["compatible_target_ids"] == ["target-1"]
    assert row["global_candidate_target_ids"] == ["header-1", "target-1"]
    assert row["header_qualification_evidence"]["fresh_human_review"] is False
    assert row["target_annotations"][0]["fresh_review_status"] == "no_fresh_task06h_target_review"
    assert args == original
    comparison = compare_outcomes(
        args["baseline_outcomes"],
        result["outcomes"],
        population=population(args),
        correspondence={"target_mapping": []},
        approved_header_rules=True,
    )
    assert comparison["classifications"] == {"approved_header_qualification": 1}
    with pytest.raises(ValueError):
        compare_outcomes(
            args["baseline_outcomes"],
            result["outcomes"],
            population=population(args),
            correspondence={"target_mapping": []},
        )
    assert (
        compare_rule_cycle(args["baseline_outcomes"], result["outcomes"], ["mention-1"])[
            "link_gains"
        ]
        == 1
    )
    with pytest.raises(ValueError, match="out-of-scope"):
        compare_rule_cycle(args["baseline_outcomes"], result["outcomes"], [])


@pytest.mark.parametrize("case", ["no_evidence", "two_remaining", "none_remaining", "comment"])
def test_header_policy_fails_closed(case):
    """Never select arbitrarily, erase all candidates, or link comment mentions."""
    args = collision_args()
    if case == "no_evidence":
        args["target_rows"][1].pop("header_qualification")
    elif case == "two_remaining":
        args["target_rows"].append({**args["target_rows"][0], "target_id": "other-body"})
    elif case == "none_remaining":
        args["target_rows"][0]["header_qualification"] = {"evidence_record_ids": ["other"]}
    else:
        args["source_records"][1]["unit_kind"] = "comment"
        args["baseline_outcomes"][0]["source_kind"] = "comment"
    old = resolve_references(**args)
    new = resolve_references(**args, header_qualification=True)
    assert old == new
    assert new["outcomes"][0]["outcome"] == "terminal_nonlink"


def test_unique_existing_link_never_filtered():
    """Header qualification only examines collisions, protecting prior links."""
    args = fixture()
    args["target_rows"][0]["header_qualification"] = {"evidence_record_ids": ["example"]}
    assert resolve_references(**args) == resolve_references(**args, header_qualification=True)
