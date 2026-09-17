"""Check the frozen Phase 1 population without external artifacts or resolver execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def population() -> dict[str, Any]:
    """Read only the checked-in, text-free baseline projection."""
    return json.loads((_ROOT / "tests/fixtures/task05g_population_plan.json").read_text())


@pytest.fixture
def bindings() -> dict[str, Any]:
    """Read only the checked-in accepted metadata snapshot."""
    return json.loads((_ROOT / "docs/specs/task05g_phase1_bindings.json").read_text())


def test_baseline_is_one_complete_partition(population: dict[str, Any]) -> None:
    """Reject duplicate, missing, conflicting, and unaccounted baseline rows."""
    rows = population["baseline_outcomes"]
    assert len(rows) == len({row["mention_id"] for row in rows}) == 511
    assert Counter(row["outcome"] for row in rows) == {
        "resolved": 295,
        "terminal_nonlink": 216,
    }
    assert population["baseline_counts"] == {"total": 511, "links": 295, "explicit_nonlinks": 216}
    assert all((row["terminal_reason"] is None) == (row["outcome"] == "resolved") for row in rows)
    assert Counter(row["terminal_reason"] for row in rows) == {
        None: 295,
        "exact_figure_target_absent": 79,
        "upstream_source_identity_repair_required": 66,
        "exact_alias_only_outside_routed_source": 19,
        "exact_target_absent": 19,
        "exact_target_collision": 12,
        "comment_authored_reference_no_official_response_link": 11,
        "more_specific_appendix_target_requires_resolution": 6,
        "appendix_source_route_absent": 2,
        "appendix_q_verification_required": 2,
    }


def test_reconciliation_has_exact_membership(
    population: dict[str, Any], bindings: dict[str, Any]
) -> None:
    """Counts alone cannot substitute a different mention into a reconciliation stratum."""
    groups = population["reconciliation"]
    rows = population["baseline_outcomes"]
    all_ids = {row["mention_id"] for row in rows}
    assert {name: len(ids) for name, ids in groups.items()} == bindings["task05g_handoff"][
        "required_reconciliation"
    ]
    for ids in groups.values():
        assert len(ids) == len(set(ids))
        assert set(ids) <= all_ids
    reasons = {
        "f1_mentions": "upstream_source_identity_repair_required",
        "figure_mentions": "exact_figure_target_absent",
        "chapter_8_9_mentions": "exact_alias_only_outside_routed_source",
        "collision_sets": "exact_target_collision",
        "comment_authored_exclusions": "comment_authored_reference_no_official_response_link",
        "appendix_q_outcomes": "appendix_q_verification_required",
    }
    for name, reason in reasons.items():
        assert set(groups[name]) == {
            row["mention_id"] for row in rows if row["terminal_reason"] == reason
        }
    assert set(groups["draft_response_mentions"]) == all_ids - set(groups["appendix_q_outcomes"])
    assert set(groups["appendix_a_impacts"]) == {
        row["mention_id"]
        for row in rows
        if row["routed_source_ids"] == ["deir_appendix_a"]
        and row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
    }


def test_all_collision_options_remain_specific(population: dict[str, Any]) -> None:
    """Preserve all twelve option sets; no ambiguous set becomes a selected target."""
    candidates = population["collision_candidates"]
    assert set(candidates) == set(population["reconciliation"]["collision_sets"])
    assert sorted(len(options) for options in candidates.values()) == [
        2,
        2,
        2,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        5,
        7,
    ]
    for options in candidates.values():
        assert len(options) == len(set(options))
        assert all(option.startswith("exv1-") for option in options)
    collisions = [row for row in population["baseline_outcomes"] if row["mention_id"] in candidates]
    assert all(row["outcome"] == "terminal_nonlink" for row in collisions)


def test_specificity_includes_hidden_appendix_subtargets(
    population: dict[str, Any], bindings: dict[str, Any]
) -> None:
    """The legacy document type does not erase an explicitly more-specific request."""
    protected = set(population["specific_target_protection"])
    rows = population["baseline_outcomes"]
    assert protected == {
        row["mention_id"]
        for row in rows
        if row["requested_target_type"] != "document"
        or row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
    }
    appendix_a = set(population["reconciliation"]["appendix_a_impacts"])
    assert len(appendix_a) == 2
    assert appendix_a <= protected
    assert all(
        row["requested_target_type"] == "document"
        for row in rows
        if row["mention_id"] in appendix_a
    )
    assert bindings["task05g_handoff"]["specific_target_downgrade_allowed"] is False


def test_final_f1_preserves_warning_scope_without_inventing_a_partition(
    population: dict[str, Any], bindings: dict[str, Any]
) -> None:
    """Keep the literal 64 limitation separate from the three exact warning IDs."""
    warning = population["final_f1_warning_binding"]
    assert warning == bindings["task05g_handoff"]["final_f1_warning_binding"]
    responses = warning["response_specific"]
    assert len(responses) == len({row["unit_id"] for row in responses}) == 2
    warning_ids = [mention for row in responses for mention in row["mention_ids"]]
    assert len(warning_ids) == len(set(warning_ids)) == 3
    f1_ids = set(population["reconciliation"]["f1_mentions"])
    assert set(warning_ids) <= f1_ids
    assert len(f1_ids - set(warning_ids)) == 63
    assert warning["other_mentions_not_proven_draft_final_equivalent"] == 64
    assert warning["source_substitution"]["draft_final_equivalence_proven"] is False
    assert warning["source_substitution"]["semantic_equivalence"] is False


def test_acceptance_handoff_and_population_bind_to_one_chain(
    population: dict[str, Any], bindings: dict[str, Any]
) -> None:
    """An accepted mechanical handoff alone cannot authorize a 05G replay."""
    pointer = bindings["acceptance_pointer"]
    acceptance = bindings["acceptance"]
    accepted = acceptance["bindings"]
    handoff = bindings["task05g_handoff"]
    assert pointer["acceptance_id"] == acceptance["acceptance_id"]
    assert pointer["finalization_id"] == accepted["finalization_id"]
    assert (
        pointer["task05g_handoff_id"]
        == accepted["task05g_handoff_id"]
        == handoff["task05g_handoff_id"]
    )
    for key in (
        "mechanical_handoff_id",
        "sampled_review_merge_id",
        "toc_merge_id",
        "target_limitations_id",
    ):
        assert accepted[key] == handoff[key]
    assert accepted["registry_id"] == handoff["usability_registry_id"]
    for key in ("task05f_rules", "task05f_semantic_digest"):
        assert population[key] == handoff[key]
    assert population["baseline_counts"] == handoff["outcomes"]
    digest = population["evidence"]["task06h_handoff"]["sha256"]
    assert digest == accepted["task05g_handoff_sha256"]
    sealed_handoff = next(
        entry
        for entry in bindings["finalization_inventory"]["files"]
        if entry["path"] == "task05g_handoff.json"
    )
    assert digest == sealed_handoff["sha256"]
    assert pointer["status"] == acceptance["status"] == "accepted_with_limitations"
    assert pointer["task05g_execution_authorized"] is False
    assert acceptance["task05g_execution_authorized"] is False
    assert handoff["execution_authorized"] is False
    assert acceptance["task05g_requires_separate_user_authorization"] is True


def test_review_projection_preserves_sampled_limits(bindings: dict[str, Any]) -> None:
    """Keep sampled carry-forward and figure visibility separate from eligibility."""
    coverage = bindings["review_coverage_projection"]
    assert coverage["decision_origin_counts"] == {
        "accepted_task04_proved_correspondence": 706,
        "accepted_task04_repaired_source_sample_confirmed": 51,
    }
    strata = coverage["sample_strata"]
    assert len(strata) == 4
    assert sum(row["population_count"] for row in strata) == 51
    assert sum(row["sample_count"] for row in strata) == 11
    assert all(row["result"] == "confirmed_for_bounded_carry_forward" for row in strata)
    targets = coverage["targets"]
    assert len(targets) == len({row["target_id"] for row in targets}) == 185
    figures = [row for row in targets if row["target_kind"] == "caption_backed_figure"]
    assert len(figures) == 178
    assert all(row["text_only_model_eligibility"] is False for row in figures)
    assert Counter(row["fresh_review_status"] for row in figures) == {
        "sampled_visual_review_complete": 12,
        "not_freshly_reviewed": 166,
    }
    assert Counter(row["fresh_review_status"] for row in targets if row not in figures) == {
        "sampled_source_review_complete": 1,
        "sampled_boundary_review_complete": 6,
    }
