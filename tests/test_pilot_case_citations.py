"""Exercise case aggregation without source I/O or fabricated human decisions."""

import copy
from typing import Any

import pytest

from er_commons.pilot_case_citations import aggregate_case_citations


def inputs() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Use two claims sharing one source unit with deliberately conflicting outcomes."""
    candidate = {
        "candidate_id": "e1",
        "source_id": "doc",
        "extraction_id": "ex1",
        "source_sha256": "hash",
        "anchors": [{"record_id": "b1", "text": "exact"}],
        "quote": "exact",
        "title": "Section A",
        "citation_unit": {"kind": "section", "section_id": "s1"},
    }
    claims = [
        {"claim_id": "c1", "text": "Keep exactly.", "relationship": "supporting"},
        {"claim_id": "c2", "text": "Also keep.", "relationship": "direct"},
    ]
    packet = {
        "case_id": "case",
        "claims": claims,
        "candidates": [candidate],
        "claim_candidates": [{"claim_id": c["claim_id"], "candidate_ids": ["e1"]} for c in claims],
    }
    reviews = [
        {
            "case_id": "case",
            "claim_id": claim["claim_id"],
            "task_id": index,
            "annotation_id": index + 100,
            "claim_review": {
                "claim_id": claim["claim_id"],
                "outcome": "no_support_found",
                "pairs": [{"candidate_id": "e1", "relationship": relation, "note": "saved"}],
            },
        }
        for index, (claim, relation) in enumerate(zip(claims, ["supports", "context"], strict=True))
    ]
    return packet, reviews


def test_support_precedence_preserves_claims_and_audit_without_claim_links() -> None:
    packet, reviews = inputs()
    before = copy.deepcopy((packet, reviews))
    result = aggregate_case_citations(packet, reviews)
    assert result["claims"] == packet["claims"]
    assert len(result["citations"]) == 1
    assert result["citations"][0]["level"] == "support"
    assert "claim_ids" not in result["citations"][0]
    assert result["audit"]["reviews"] == reviews
    assert result["audit"]["candidates"] == packet["candidates"]
    assert (packet, reviews) == before
    packet["claims"].reverse()
    packet["claim_candidates"].reverse()
    reviews.reverse()
    assert aggregate_case_citations(packet, reviews) == result


def test_different_sections_and_table_are_distinct_but_display_variants_merge() -> None:
    packet, reviews = inputs()
    for identity, kind, unit_id in [
        ("e2", "section", "s1"),
        ("e3", "section", "s2"),
        ("e4", "table", "s1"),
    ]:
        candidate = copy.deepcopy(packet["candidates"][0])
        candidate.update(candidate_id=identity, title="Another display label")
        candidate["citation_unit"] = {"kind": kind, kind + "_id": unit_id}
        packet["candidates"].append(candidate)
        packet["claim_candidates"][0]["candidate_ids"].append(identity)
        reviews[0]["claim_review"]["pairs"].append(
            {"candidate_id": identity, "relationship": "context", "note": ""}
        )
    result = aggregate_case_citations(packet, reviews)
    assert len(result["citations"]) == 3
    assert sorted(c["level"] for c in result["citations"]) == ["context", "context", "support"]
    packet["candidates"].reverse()
    reviews[0]["claim_review"]["pairs"].reverse()
    reordered = aggregate_case_citations(packet, reviews)
    assert reordered["citations"] == result["citations"]
    assert reordered["audit"]["citation_decisions"] == result["audit"]["citation_decisions"]
    assert reordered["audit"]["reviews"] == reviews


@pytest.mark.parametrize(
    "field,value", [("source_sha256", "other"), ("anchors", []), ("quote", "changed")]
)
def test_conflicting_bindings_rejected(field: str, value: Any) -> None:
    packet, reviews = inputs()
    other = copy.deepcopy(packet["candidates"][0])
    other.update(candidate_id="e2", **{field: value})
    packet["candidates"].append(other)
    with pytest.raises(ValueError, match="Conflicting"):
        aggregate_case_citations(packet, reviews)


@pytest.mark.parametrize("other", ["context", "no_support", "partial"])
def test_partial_without_support_requires_disposition_even_with_context(other: str) -> None:
    packet, reviews = inputs()
    reviews[0]["claim_review"]["pairs"][0]["relationship"] = "partial"
    reviews[1]["claim_review"]["pairs"][0]["relationship"] = other
    with pytest.raises(ValueError, match="explicit disposition"):
        aggregate_case_citations(packet, reviews)


def test_partial_with_separate_support_is_preserved() -> None:
    packet, reviews = inputs()
    reviews[1]["claim_review"]["pairs"][0]["relationship"] = "partial"
    result = aggregate_case_citations(packet, reviews)
    assert result["citations"][0]["level"] == "support"
    assert result["audit"]["reviews"] == reviews


@pytest.mark.parametrize("relation", ["no_support", "contradicts", "unusable"])
def test_rejected_candidates_not_automatically_context(relation: str) -> None:
    packet, reviews = inputs()
    for review in reviews:
        review["claim_review"]["outcome"] = "supported"
        review["claim_review"]["pairs"][0]["relationship"] = relation
    result = aggregate_case_citations(packet, reviews)
    assert result["citations"] == []
    assert len(result["claims"]) == 2
    assert result["audit"]["citation_decisions"][0]["citation_id"] is None
    assert result["audit"]["reviews"] == reviews


def test_context_level_does_not_infer_support_from_claim_outcome() -> None:
    packet, reviews = inputs()
    for review in reviews:
        review["claim_review"]["outcome"] = "supported"
        review["claim_review"]["pairs"][0]["relationship"] = "context"
    assert aggregate_case_citations(packet, reviews)["citations"][0]["level"] == "context"


@pytest.mark.parametrize(
    "problem",
    ["missing_review", "unknown_candidate", "missing_pair", "duplicate_review", "wrong_case"],
)
def test_incomplete_or_misbound_reviews_rejected(problem: str) -> None:
    packet, reviews = inputs()
    if problem == "missing_review":
        reviews.pop()
    elif problem == "unknown_candidate":
        reviews[0]["claim_review"]["pairs"][0]["candidate_id"] = "unknown"
    elif problem == "missing_pair":
        reviews[0]["claim_review"]["pairs"] = []
    elif problem == "duplicate_review":
        reviews.append(copy.deepcopy(reviews[0]))
    else:
        reviews[0]["case_id"] = "wrong"
    with pytest.raises(ValueError):
        aggregate_case_citations(packet, reviews)


def test_citation_label_variants_merge_but_structural_boundaries_must_match() -> None:
    packet, reviews = inputs()
    original = packet["candidates"][0]
    original["citation_unit"]["citation_label"] = "Section A, page 1"
    original["citation_unit"]["member_record_ids"] = ["b1"]
    other = copy.deepcopy(original)
    other["candidate_id"] = "e2"
    other["citation_unit"]["citation_label"] = "Section A (p. 1)"
    packet["candidates"].append(other)
    packet["claim_candidates"][1]["candidate_ids"] = ["e2"]
    reviews[1]["claim_review"]["pairs"][0]["candidate_id"] = "e2"
    result = aggregate_case_citations(packet, reviews)
    assert len(result["citations"]) == 1
    assert result["citations"][0]["level"] == "support"
    assert result["audit"]["candidates"] == [original, other]
    other["citation_unit"]["member_record_ids"] = ["b1", "b2"]
    with pytest.raises(ValueError, match="Conflicting"):
        aggregate_case_citations(packet, reviews)


def test_legacy_identity_derived_from_anchors_without_changing_original() -> None:
    packet, reviews = inputs()
    candidate = packet["candidates"][0]
    candidate.pop("extraction_id")
    candidate["anchors"][0]["record"] = {"extraction_id": "ex1", "document_id": "ex1/document/doc"}
    before = copy.deepcopy(candidate)
    result = aggregate_case_citations(packet, reviews)
    assert result["citations"][0]["extraction_id"] == "ex1"
    assert result["audit"]["candidates"] == [before]
    candidate["extraction_id"] = "ex1"
    assert aggregate_case_citations(packet, reviews)["citations"] == result["citations"]


@pytest.mark.parametrize(
    "extraction,document", [("ex2", "ex2/document/doc"), ("ex1", "ex1/document/other")]
)
def test_mixed_anchor_identities_rejected(extraction: str, document: str) -> None:
    packet, reviews = inputs()
    candidate = packet["candidates"][0]
    candidate["anchors"] = [
        {"record": {"extraction_id": "ex1", "document_id": "ex1/document/doc"}},
        {"record": {"extraction_id": extraction, "document_id": document}},
    ]
    with pytest.raises(ValueError, match="identity"):
        aggregate_case_citations(packet, reviews)
