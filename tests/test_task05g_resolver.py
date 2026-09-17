"""Synthetic resolver and comparison controls without accepted source access."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from er_commons.response_inventory.reference_replay_comparison import (
    compare_outcomes,
    validate_result,
)
from er_commons.response_inventory.reference_replay_resolver import (
    DEPENDENCY_ROLES,
    resolve_references,
)

type JsonObject = dict[str, Any]


def fixture(label: str = "Draft EIR Section 4.1", target_type: str = "section") -> JsonObject:
    """Build one full synthetic invocation; the frozen population remains fixture-local."""
    mention = {
        "record_type": "reference_mention",
        "mention_id": "mention-1",
        "mention_span_id": "span-1",
        "source_unit_id": "unit-1",
        "raw_text_sha256": "a" * 64,
        "reference_domain": "draft_eir",
        "target_labels": [label],
    }
    old = {
        **{
            key: mention[key]
            for key in (
                "mention_id",
                "mention_span_id",
                "source_unit_id",
                "raw_text_sha256",
                "reference_domain",
            )
        },
        "source_kind": "response",
        "outcome": "terminal_nonlink",
        "terminal_reason": "exact_target_absent",
        "requested_target_type": target_type,
        "routed_source_ids": ["deir_main"],
        "compatible_target_ids": [],
        "global_candidate_target_ids": [],
        "source_candidate_target_ids": [],
    }
    return {
        "source_records": [
            mention,
            {"record_type": "source_unit", "unit_id": "unit-1", "unit_kind": "response"},
        ],
        "target_rows": [
            {
                "lookup_key": label.removeprefix("Draft EIR ").lower(),
                "target_id": "target-1",
                "source_id": "deir_main",
                "target_type": target_type,
            }
        ],
        "direct_section_children": {},
        "catalog": {"sources": []},
        "registry": {
            "entries": [
                {
                    "selected_source_id": "deir_main",
                    "status": "usable_with_limitation",
                    "limitations": ["sampled only"],
                }
            ]
        },
        "target_limitations": {"entries": []},
        "handoff": {"coverage_boundary": "706 proved; 51 sampled-stratum carry-forward"},
        "activity": {
            "activity_id": "activity-synthetic",
            "input_refs": [
                {
                    "role": role,
                    "identity": role + "-id",
                    "authority": "artifact_root",
                    "path": role + ".json",
                    "sha256": "d" * 64,
                }
                for role in DEPENDENCY_ROLES
            ],
        },
        "baseline_outcomes": [old],
    }


def population(args: JsonObject) -> JsonObject:
    """Freeze exact fixture baseline IDs and status, not just aggregate counts."""
    old = args["baseline_outcomes"]
    return {
        "baseline_outcomes": copy.deepcopy(old),
        "baseline_counts": {
            "total": len(old),
            "links": sum(row["outcome"] == "resolved" for row in old),
            "explicit_nonlinks": sum(row["outcome"] == "terminal_nonlink" for row in old),
        },
        "reconciliation": {
            "f1_mentions": [
                row["mention_id"]
                for row in old
                if row["terminal_reason"] == "upstream_source_identity_repair_required"
            ]
        },
        "final_f1_warning_binding": args["handoff"].get("final_f1_warning_binding"),
        "collision_candidates": {},
    }


def test_exact_resolution_retains_sampled_source_limitation() -> None:
    """A structural link does not promote its missing target-review status or eligibility."""
    args = fixture()
    result = resolve_references(**args)
    row = result["outcomes"][0]
    assert row["outcome"] == "resolved"
    assert row["target_annotations"][0]["source_usability"]["limitations"] == ["sampled only"]
    assert row["target_annotations"][0]["fresh_review_status"] == "no_fresh_task06h_target_review"
    assert row["target_annotations"][0]["text_only_model_eligibility"] is None
    validate_result(result, args["baseline_outcomes"], population(args), expected_result=result)


@pytest.mark.parametrize(
    "label,target",
    [
        ("Draft EIR Figure 4.8", "figure 4.8-5"),
        ("Draft EIR Chapter 8", "8.1 introduction"),
        ("Draft EIR Section 4.1.a", "4.1"),
    ],
)
def test_specific_targets_never_use_prefix_or_parent(label: str, target: str) -> None:
    """Missing figure, whole chapter and subsection remain explicit nonlinks."""
    args = fixture(label, "figure" if "Figure" in label else "section")
    args["target_rows"][0]["lookup_key"] = target
    assert resolve_references(**args)["outcomes"][0]["outcome"] == "terminal_nonlink"


def test_direct_appendix_alias_cannot_bypass_specific_baseline_guard() -> None:
    """Protect document-typed mentions whose accepted reason records an attached inner target."""
    args = fixture("Draft EIR Appendix A", "document")
    args["catalog"] = {
        "sources": [{"source": {"source_id": "deir_main"}, "reference_aliases": ["Appendix A"]}]
    }
    args["baseline_outcomes"][0]["terminal_reason"] = (
        "more_specific_appendix_target_requires_resolution"
    )
    row = resolve_references(**args)["outcomes"][0]
    assert row["outcome"] == "terminal_nonlink"
    assert row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"


def test_specific_guard_retains_exact_global_and_source_diagnostics() -> None:
    """A protected nonlink keeps exact options, but none becomes a generic compatible target."""
    args = fixture("Draft EIR Appendix A", "document")
    args["catalog"] = {
        "sources": [{"source": {"source_id": "deir_main"}, "reference_aliases": ["Appendix A"]}]
    }
    args["baseline_outcomes"][0]["terminal_reason"] = (
        "more_specific_appendix_target_requires_resolution"
    )
    args["target_rows"].append(
        {
            "lookup_key": "appendix a",
            "target_id": "outside-section",
            "source_id": "outside",
            "target_type": "section",
        }
    )
    result = resolve_references(**args)
    row = result["outcomes"][0]
    assert row["global_candidate_target_ids"] == ["outside-section", "target-1"]
    assert row["source_candidate_target_ids"] == ["target-1"]
    assert row["compatible_target_ids"] == []
    assert row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
    assert result["links"] == []


@pytest.mark.parametrize("status", ["sampled_visual_review_complete", "not_freshly_reviewed"])
def test_figure_review_never_promotes_text_only_eligibility(status: str) -> None:
    """Both visually sampled and unviewed caption targets require an explicit false flag."""
    args = fixture("Draft EIR Figure 4.8-5", "figure")
    args["target_limitations"]["entries"] = [
        {
            "target_id": "target-1",
            "fresh_review_status": status,
            "text_only_model_eligibility": False,
        }
    ]
    result = resolve_references(**args)
    assert result["outcomes"][0]["target_annotations"][0]["text_only_model_eligibility"] is False
    args["target_limitations"]["entries"][0]["text_only_model_eligibility"] = True
    with pytest.raises(ValueError, match="text-only exclusion"):
        resolve_references(**args)
    args["target_limitations"]["entries"] = []
    with pytest.raises(ValueError, match="text-only exclusion"):
        resolve_references(**args)


def f1_fixture() -> JsonObject:
    """Model the declared substitution with three named warnings and literal inherited 64."""
    args = fixture("Draft EIR Appendix F1", "document")
    args["catalog"] = {
        "sources": [
            {"source": {"source_id": "deir_appendix_f1"}, "reference_aliases": ["Appendix F1"]}
        ]
    }
    args["target_rows"][0]["source_id"] = "feir_appendix_f1"
    args["registry"]["entries"][0].update(
        selected_source_id="feir_appendix_f1",
        logical_source_id="deir_appendix_f1",
        selected_candidate_id="selected-final-f1-candidate",
    )
    args["baseline_outcomes"][0].update(
        routed_source_ids=["deir_appendix_f1"],
        terminal_reason="upstream_source_identity_repair_required",
    )
    args["handoff"]["final_f1_warning_binding"] = {
        "general_warning": "edition warning",
        "response_specific": [
            {"unit_id": "unit-1", "mention_ids": ["mention-1"], "material": "Table 6 revision"}
        ],
        "other_mentions_not_proven_draft_final_equivalent": 64,
        "source_substitution": {
            "logical_source_id": "deir_appendix_f1",
            "selected": {
                "source_id": "feir_appendix_f1",
                "candidate_id": "selected-final-f1-candidate",
            },
            "draft_final_equivalence_proven": False,
            "semantic_equivalence": False,
        },
        "limitations_sha256": "b" * 64,
        "source_substitution_sha256": "c" * 64,
    }
    return args


def test_f1_binding_is_complete_and_scope_is_not_recomputed() -> None:
    """Keep exact inherited warning bindings on links and nonlinks without equivalence claims."""
    args = f1_fixture()
    result = resolve_references(**args)
    warning = result["outcomes"][0]["final_f1_warning"]
    assert result["outcomes"][0]["routed_source_ids"] == ["feir_appendix_f1"]
    assert warning["binding"] == args["handoff"]["final_f1_warning_binding"]
    assert warning["binding"]["other_mentions_not_proven_draft_final_equivalent"] == 64
    args["target_rows"] = []
    assert resolve_references(**args)["outcomes"][0]["final_f1_warning"] == warning
    args["handoff"]["final_f1_warning_binding"]["source_substitution"]["semantic_equivalence"] = (
        True
    )
    with pytest.raises(ValueError, match="unverified"):
        resolve_references(**args)


@pytest.mark.parametrize("mutation", ["warning", "reverse", "conflict", "missing", "population"])
def test_validator_rejects_mutated_or_incomplete_outputs(mutation: str) -> None:
    """Loaded rows must satisfy closure and match a fresh deterministic resolution."""
    args = f1_fixture()
    expected = resolve_references(**args)
    result = copy.deepcopy(expected)
    if mutation == "warning":
        result["outcomes"][0]["final_f1_warning"] = None
    elif mutation == "reverse":
        result["reverse"] = []
    elif mutation == "conflict":
        result["diagnostics"] = [{"mention_id": "mention-1"}]
    elif mutation == "missing":
        result["outcomes"] = []
    else:
        result["outcomes"][0]["mention_id"] = "same-count-other-id"
    with pytest.raises(ValueError):
        validate_result(
            result, args["baseline_outcomes"], population(args), expected_result=expected
        )


def test_comparison_requires_sealed_repair_authority() -> None:
    """A link gain needs the exact selected target in authorized additions."""
    args = fixture()
    result = resolve_references(**args)
    with pytest.raises(ValueError, match="unexplained"):
        compare_outcomes(
            args["baseline_outcomes"],
            result["outcomes"],
            population=population(args),
            correspondence={"target_mapping": []},
        )
    compared = compare_outcomes(
        args["baseline_outcomes"],
        result["outcomes"],
        population=population(args),
        correspondence={"target_mapping": [], "authorized_added_target_ids": ["target-1"]},
    )
    assert compared["link_gains"] == 1
    assert compared["rows"][0]["classification"] == "accepted_structural_repair"


def test_comparison_preserves_every_collision_option() -> None:
    """A same-count collision swap has no namespace authority and cannot pass."""
    args = fixture()
    args["target_rows"].append({**args["target_rows"][0], "target_id": "target-2"})
    args["baseline_outcomes"][0].update(
        global_candidate_target_ids=["old-1", "old-2"],
        source_candidate_target_ids=["old-1", "old-2"],
        compatible_target_ids=["old-1", "old-2"],
        terminal_reason="exact_target_collision",
    )
    frozen = population(args)
    frozen["collision_candidates"] = {"mention-1": ["old-1", "old-2"]}
    result = resolve_references(**args)
    mapping = {
        "target_mapping": [
            {"baseline_target_id": "old-1", "selected_target_id": "target-1"},
            {"baseline_target_id": "old-2", "selected_target_id": "target-2"},
        ]
    }
    compared = compare_outcomes(
        args["baseline_outcomes"], result["outcomes"], population=frozen, correspondence=mapping
    )
    assert compared["rows"][0]["baseline_collision_options"] == ["old-1", "old-2"]
    mapping["target_mapping"].pop()
    with pytest.raises(ValueError, match="unexplained"):
        compare_outcomes(
            args["baseline_outcomes"], result["outcomes"], population=frozen, correspondence=mapping
        )


def test_activity_binds_identical_ordered_dependencies_to_all_views() -> None:
    """A schema-valid provenance rewrite cannot diverge between activity and derived rows."""
    from er_commons.response_inventory.reference_replay_comparison import validate_activity

    args = fixture()
    result = resolve_references(**args)
    activity = {
        **args["activity"],
        "schema_version": "er_commons.response_inventory.v2",
        "record_type": "activity",
        "policy": "accepted_05f_rules_with_verified_final_f1_substitution",
    }
    validate_activity(
        activity,
        result,
        expected_input_refs=args["activity"]["input_refs"],
        expected_activity_id="activity-synthetic",
    )
    result["links"][0]["activity_id"] = "activity-other"
    with pytest.raises(ValueError, match="activity identity"):
        validate_activity(
            activity,
            result,
            expected_input_refs=args["activity"]["input_refs"],
            expected_activity_id="activity-synthetic",
        )


@pytest.mark.parametrize("label", ["Draft EIR Appendix F1", "Draft EIR Appendix F.1"])
def test_selected_physical_f1_catalog_restores_only_verified_logical_route(label: str) -> None:
    """Physical and historical logical catalogs produce identical warning-bearing rows."""
    logical = f1_fixture()
    logical["source_records"][0]["target_labels"] = [label]
    expected = resolve_references(**logical)
    physical = copy.deepcopy(logical)
    physical["catalog"]["sources"][0]["source"]["source_id"] = "feir_appendix_f1"
    assert resolve_references(**physical) == expected
    assert expected["outcomes"][0]["logical_source_ids"] == ["deir_appendix_f1"]
    assert expected["outcomes"][0]["final_f1_warning"] is not None
    physical["registry"]["entries"][0]["selected_candidate_id"] = "unbound-other-final-candidate"
    with pytest.raises(ValueError, match="unverified Final F1"):
        resolve_references(**physical)
    physical["registry"]["entries"][0]["selected_candidate_id"] = "selected-final-f1-candidate"
    del physical["handoff"]["final_f1_warning_binding"]
    with pytest.raises(ValueError, match="unverified Final F1"):
        resolve_references(**physical)
