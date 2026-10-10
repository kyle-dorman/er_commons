"""Mechanical synthetic contract checks, including intentionally defective answers."""

import copy
from typing import Any

import pytest

from er_commons.synthetic_records import (
    apply_edits,
    make_edits,
    materialize_records,
    validate_proposal,
)


def fixture(category: str = "P01") -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a dev-only source packet and one complete author proposal."""
    answer = {
        "status": "answered",
        "conclusion": {"point_id": "c", "text": "Water is limited.", "citation_ids": ["S1"]},
        "supporting_points": [],
        "qualifications": [],
        "optional_context": [],
    }
    packet = {
        "case_id": "DEV1",
        "requested_categories": [category],
        "reference_answer": copy.deepcopy(answer),
        "sources": [
            {
                "occurrence_id": "S1",
                "canonical_target": {"unit_id": "u1"},
                "full_source_text": "Water is limited. More study is required.",
            }
        ],
    }
    score = {
        "score": 2,
        "rationale": "The passage establishes the limit.",
        "evidence": [{"citation_id": "S1", "locator": "u1", "excerpt": "Water is limited."}],
    }
    variant = {
        "perturbation_id": category,
        "severity": "invariance",
        "answer": answer,
        "point_mapping": [],
        "intended_effect": "Preserve meaning.",
        "secondary_effects": [],
        "expected_invalid_citation_ids": [],
        "expectation": {
            "grounding": copy.deepcopy(score),
            "adequacy": copy.deepcopy(score),
            "verification_status": "model_verified",
            "ambiguity": "",
        },
    }
    proposal = {
        "case_id": "DEV1",
        "coverage": [
            {"perturbation_id": category, "disposition": "generated", "reason": "Applicable."}
        ],
        "variants": [variant],
        "discovery": {
            "queries": [],
            "candidates": [],
            "supplemental_pass_used": False,
            "limitations": [],
        },
    }
    return proposal, packet


def test_exact_edits_reconstruct_and_reject_wrong_parent() -> None:
    parent = {"a": [1, 2], "b": None}
    answer = {"a": [2, 1], "c": "new"}
    edits = make_edits(parent, answer)
    assert apply_edits(parent, edits) == answer
    with pytest.raises(ValueError, match="precondition"):
        apply_edits({"a": [2], "b": None}, edits)


def test_invalid_citation_is_preserved_but_must_be_declared() -> None:
    proposal, packet = fixture("C05")
    variant = proposal["variants"][0]
    variant["answer"]["conclusion"]["citation_ids"] = ["INVENTED"]
    assert not validate_proposal(proposal, packet)["valid"]
    variant["expected_invalid_citation_ids"] = ["INVENTED"]
    records = materialize_records(proposal, packet, {"model": "fixture"})
    assert records["answers"][0]["answer"]["conclusion"]["citation_ids"] == ["INVENTED"]
    assert "perturbation_id" not in records["answers"][0]


@pytest.mark.parametrize("category", ["P03", "P04"])
def test_split_combine_mapping_required(category: str) -> None:
    proposal, packet = fixture(category)
    packet["reference_answer"]["supporting_points"] = [
        {"point_id": "p1", "text": "Limited.", "citation_ids": ["S1"]},
        {"point_id": "p2", "text": "Study.", "citation_ids": ["S1"]},
    ]
    assert not validate_proposal(proposal, packet)["valid"]
    variant = proposal["variants"][0]
    variant["answer"]["supporting_points"] = [
        {"point_id": "new1", "text": "Limited.", "citation_ids": ["S1"]},
        {"point_id": "new2", "text": "Study.", "citation_ids": ["S1"]},
    ]
    variant["point_mapping"] = [
        {
            "parent_point_ids": ["p1", "p2"] if category == "P03" else ["p1"],
            "variant_point_ids": ["new1"] if category == "P03" else ["new1", "new2"],
        }
    ]
    assert validate_proposal(proposal, packet)["valid"]


def test_unresolved_and_clean_abstention() -> None:
    proposal, packet = fixture("R01")
    variant = proposal["variants"][0]
    variant["answer"]["status"] = "abstained"
    variant["answer"]["conclusion"] = {
        "point_id": "c",
        "text": "Insufficient evidence.",
        "citation_ids": [],
    }
    variant["expectation"]["grounding"].update(score=None, evidence=[])
    variant["expectation"]["adequacy"].update(score=0, evidence=[])
    assert validate_proposal(proposal, packet)["valid"]
    variant["expectation"].update(verification_status="unresolved", ambiguity="Unclear scope.")
    variant["expectation"]["adequacy"]["score"] = None
    assert validate_proposal(proposal, packet)["valid"]


def test_exact_evidence_and_case_binding() -> None:
    proposal, packet = fixture()
    proposal["variants"][0]["expectation"]["grounding"]["evidence"][0]["excerpt"] = "not in source"
    assert not validate_proposal(proposal, packet)["valid"]
    proposal, packet = fixture()
    proposal["case_id"] = "TEST1"
    assert not validate_proposal(proposal, packet)["valid"]


def test_dangling_qualification_and_duplicate_diagnostics() -> None:
    proposal, packet = fixture()
    answer = proposal["variants"][0]["answer"]
    answer["qualifications"] = [
        {
            "point_id": "q",
            "text": "A qualification.",
            "citation_ids": ["S1"],
            "applies_to": ["absent"],
        }
    ]
    assert not validate_proposal(proposal, packet)["valid"]
    answer["qualifications"][0]["applies_to"] = ["c"]
    proposal["variants"].append(copy.deepcopy(proposal["variants"][0]))
    report = validate_proposal(proposal, packet)
    assert report["valid"]
    assert report["diagnostics"] == [{"variant_index": 1, "duplicate_of": 0}]


def test_unresolved_scores_cannot_silently_enter_agreement() -> None:
    proposal, packet = fixture()
    expectation = proposal["variants"][0]["expectation"]
    expectation.update(verification_status="unresolved", ambiguity="Insufficient context.")
    assert not validate_proposal(proposal, packet)["valid"]
    expectation["grounding"]["score"] = None
    records = materialize_records(proposal, packet, {})
    assert records["expectations"][0]["agreement_eligible"] is False


def test_control_duplicate_ignores_reference_locator_metadata() -> None:
    proposal, packet = fixture()
    packet["reference_answer"]["citation_locators"] = [{"occurrence_id": "S1", "excerpt": "Water"}]
    report = validate_proposal(proposal, packet)
    assert report["valid"]
    assert {"variant_index": 0, "duplicate_of_control": True} in report["diagnostics"]
    records = materialize_records(proposal, packet, {})
    assert "citation_locators" in records["control"]["answer"]


def test_substantive_abstention_cannot_hide_behind_empty_point_arrays() -> None:
    proposal, packet = fixture("R02")
    variant = proposal["variants"][0]
    variant["answer"]["status"] = "abstained"
    variant["answer"]["conclusion"] = {
        "point_id": "c",
        "text": "I abstain; the water is unlimited.",
        "citation_ids": [],
    }
    variant["expectation"]["grounding"].update(score=None, evidence=[])
    assert not validate_proposal(proposal, packet)["valid"]


def test_clean_abstention_anchors_are_enforced() -> None:
    proposal, packet = fixture("R01")
    variant = proposal["variants"][0]
    variant["answer"]["status"] = "abstained"
    variant["answer"]["conclusion"] = {
        "point_id": "c",
        "text": "Insufficient evidence.",
        "citation_ids": [],
    }
    assert not validate_proposal(proposal, packet)["valid"]
    variant["expectation"]["grounding"]["score"] = None
    variant["expectation"]["adequacy"]["score"] = 0
    assert validate_proposal(proposal, packet)["valid"]


def test_supplemental_discovery_claim_requires_packet_provenance() -> None:
    proposal, packet = fixture()
    proposal["discovery"]["supplemental_pass_used"] = True
    assert not validate_proposal(proposal, packet)["valid"]
    packet["supplemental_discovery_provenance"] = {"pass_id": "fixture-pass", "sha256": "fixture"}
    assert validate_proposal(proposal, packet)["valid"]
    proposal["discovery"]["supplemental_pass_used"] = False
    assert not validate_proposal(proposal, packet)["valid"]
