"""Fresh invented proposals exercise staged author labels without prior answers."""

import copy
from typing import Any

import pytest

from er_commons.synthetic_records import materialize_records, validate_proposal
from er_commons.synthetic_stage_expectations import ANNOTATION_VERSION


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """Use a small invented source and separate conclusion/supporting point."""
    evidence = [{"citation_id": "s", "locator": "u", "excerpt": "Water is limited."}]
    answer = {
        "status": "answered",
        "conclusion": {"point_id": "c", "text": "Water is limited.", "citation_ids": ["s"]},
        "supporting_points": [
            {"point_id": "p", "text": "Water is limited.", "citation_ids": ["s"]}
        ],
        "qualifications": [],
        "optional_context": [],
    }
    grounding = {
        "score": 2,
        "rationale": "The cited source establishes the conclusion.",
        "evidence": copy.deepcopy(evidence),
        "clean_abstention": False,
        "conclusion_supported": True,
        "not_supported": False,
        "insufficient_evidence_response": False,
        "unsupported_premise_point_ids": [],
        "point_expectations": [
            {
                "point_id": "p",
                "supported": True,
                "rationale": "The source says this.",
                "evidence": copy.deepcopy(evidence),
                "unsupported_assertions": [],
            }
        ],
    }
    proposal = {
        "case_id": "invented",
        "coverage": [
            {"perturbation_id": "P01", "disposition": "generated", "reason": "Applicable."}
        ],
        "discovery": {
            "queries": [],
            "candidates": [],
            "supplemental_pass_used": False,
            "limitations": [],
        },
        "variants": [
            {
                "perturbation_id": "P01",
                "severity": "invariance",
                "answer": answer,
                "point_mapping": [],
                "intended_effect": "Preserve support.",
                "secondary_effects": [],
                "expected_invalid_citation_ids": [],
                "expectation": {
                    "grounding": grounding,
                    "adequacy": {
                        "score": 2,
                        "rationale": "Answers scope.",
                        "evidence": copy.deepcopy(evidence),
                    },
                    "verification_status": "model_verified",
                    "ambiguity": "",
                },
            }
        ],
    }
    packet = {
        "annotation_version": ANNOTATION_VERSION,
        "case_id": "invented",
        "requested_categories": ["P01"],
        "regeneration_slots": {"P01": "metadata-only-slot"},
        "reference_answer": copy.deepcopy(answer),
        "sources": [
            {
                "occurrence_id": "s",
                "canonical_target": {"unit_id": "u"},
                "full_source_text": "Water is limited.",
            }
        ],
    }
    return proposal, packet


def test_supported_and_versioned_materialization() -> None:
    proposal, packet = fixture()
    result = materialize_records(proposal, packet, {"model": "invented"})
    assert result["answers"][0]["variant_id"].startswith("task09a2-")
    assert result["expectations"][0]["grounding"]["point_expectations"][0]["supported"]


@pytest.mark.parametrize("conclusion,score", [(True, 1), (False, 0)])
def test_unsupported_compound_span_and_score(conclusion: bool, score: int) -> None:
    proposal, packet = fixture()
    v = proposal["variants"][0]
    v["answer"]["supporting_points"][0]["text"] += " Supply is unlimited."
    g = v["expectation"]["grounding"]
    g.update(conclusion_supported=conclusion, not_supported=True, score=score)
    g["point_expectations"][0].update(
        supported=False,
        unsupported_assertions=[
            {"assertion_span": "Supply is unlimited.", "reason": "Unsupported addition."}
        ],
    )
    assert validate_proposal(proposal, packet)["valid"]
    g["score"] = 2
    assert not validate_proposal(proposal, packet)["valid"]
    g["score"] = score
    g["point_expectations"][0]["unsupported_assertions"][0]["assertion_span"] = "invented span"
    assert not validate_proposal(proposal, packet)["valid"]


def test_unknown_preserved_and_excluded() -> None:
    proposal, packet = fixture()
    e = proposal["variants"][0]["expectation"]
    e.update(verification_status="unresolved", ambiguity="Point implication uncertain.")
    g = e["grounding"]
    g.update(score=None, not_supported=None)
    g["point_expectations"][0]["supported"] = None
    records = materialize_records(proposal, packet, {})
    assert not records["expectations"][0]["agreement_eligible"]
    e["verification_status"] = "model_verified"
    assert not validate_proposal(proposal, packet)["valid"]


def test_point_evidence_cannot_borrow_other_source() -> None:
    proposal, packet = fixture()
    packet["sources"].append(
        {
            "occurrence_id": "other",
            "canonical_target": {"unit_id": "v"},
            "full_source_text": "Water is limited.",
        }
    )
    g = proposal["variants"][0]["expectation"]["grounding"]
    g["point_expectations"][0]["evidence"][0].update(citation_id="other", locator="v")
    assert not validate_proposal(proposal, packet)["valid"]


@pytest.mark.parametrize("kind", ["qualifications", "optional_context"])
def test_every_original_point_requires_label(kind: str) -> None:
    proposal, packet = fixture()
    row = {"point_id": "q", "text": "Water is limited.", "citation_ids": ["s"]}
    if kind == "qualifications":
        row["applies_to"] = ["c"]
    proposal["variants"][0]["answer"][kind].append(row)
    assert not validate_proposal(proposal, packet)["valid"]


def test_conclusion_only_and_clean_abstention() -> None:
    proposal, packet = fixture()
    v = proposal["variants"][0]
    v["answer"]["supporting_points"] = []
    g = v["expectation"]["grounding"]
    g["point_expectations"] = []
    assert validate_proposal(proposal, packet)["valid"]
    v["answer"].update(
        status="abstained",
        conclusion={
            "point_id": "c",
            "text": "I cannot answer from available evidence.",
            "citation_ids": [],
        },
    )
    g.update(
        clean_abstention=True,
        conclusion_supported=None,
        score=None,
        evidence=[],
        insufficient_evidence_response=True,
    )
    v["expectation"]["adequacy"]["score"] = 0
    assert validate_proposal(proposal, packet)["valid"]
    g["not_supported"] = True
    assert not validate_proposal(proposal, packet)["valid"]


def test_premise_consistency_and_independent_insufficiency_flag() -> None:
    proposal, packet = fixture()
    g = proposal["variants"][0]["expectation"]["grounding"]
    g["insufficient_evidence_response"] = True
    assert validate_proposal(proposal, packet)["valid"]
    g["unsupported_premise_point_ids"] = ["p"]
    assert not validate_proposal(proposal, packet)["valid"]


def test_failed_citations_need_no_substitute_grounding_evidence() -> None:
    proposal, packet = fixture()
    v = proposal["variants"][0]
    for point in [v["answer"]["conclusion"], *v["answer"]["supporting_points"]]:
        point["citation_ids"] = ["missing"]
    v["expected_invalid_citation_ids"] = ["missing"]
    g = v["expectation"]["grounding"]
    g.update(conclusion_supported=False, not_supported=True, score=0, evidence=[])
    g["point_expectations"][0].update(
        supported=False,
        evidence=[],
        unsupported_assertions=[
            {"assertion_span": "Water is limited.", "reason": "Its citation does not resolve."}
        ],
    )
    assert validate_proposal(proposal, packet)["valid"]


def test_insufficiency_unknown_does_not_mean_support_unknown() -> None:
    proposal, packet = fixture()
    e = proposal["variants"][0]["expectation"]
    e.update(verification_status="unresolved", ambiguity="Response intent is ambiguous.")
    e["grounding"].update(insufficient_evidence_response=None, score=None)
    assert validate_proposal(proposal, packet)["valid"]
    e["grounding"]["not_supported"] = None
    assert not validate_proposal(proposal, packet)["valid"]


def test_unknown_point_and_known_failure_preserve_not_supported() -> None:
    proposal, packet = fixture()
    e = proposal["variants"][0]["expectation"]
    e.update(verification_status="unresolved", ambiguity="Point support is uncertain.")
    e["grounding"].update(conclusion_supported=False, not_supported=True, score=None)
    e["grounding"]["point_expectations"][0]["supported"] = None
    assert validate_proposal(proposal, packet)["valid"]


def test_duplicate_missing_and_extra_labels_fail() -> None:
    proposal, packet = fixture()
    g = proposal["variants"][0]["expectation"]["grounding"]
    row = copy.deepcopy(g["point_expectations"][0])
    g["point_expectations"].append(row)
    assert not validate_proposal(proposal, packet)["valid"]
    g["point_expectations"] = []
    assert not validate_proposal(proposal, packet)["valid"]
    row["point_id"] = "unknown"
    g["point_expectations"] = [row]
    assert not validate_proposal(proposal, packet)["valid"]


def test_false_premise_requires_false_conclusion() -> None:
    proposal, packet = fixture()
    g = proposal["variants"][0]["expectation"]["grounding"]
    g.update(unsupported_premise_point_ids=["p"], not_supported=True, score=1)
    g["point_expectations"][0].update(
        supported=False,
        unsupported_assertions=[
            {"assertion_span": "Water is limited.", "reason": "Unestablished."}
        ],
    )
    assert not validate_proposal(proposal, packet)["valid"]
    g.update(conclusion_supported=False, score=0)
    assert validate_proposal(proposal, packet)["valid"]


def test_one_fresh_variant_per_slot_and_binding() -> None:
    proposal, packet = fixture()
    result = materialize_records(proposal, packet, {})
    assert result["answers"][0]["predecessor_development_variant_id"] == "metadata-only-slot"
    proposal["variants"].append(copy.deepcopy(proposal["variants"][0]))
    assert not validate_proposal(proposal, packet)["valid"]
