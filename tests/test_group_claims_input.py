"""Source-free verification of frozen questions and exact response provenance."""

import copy

import pytest

from er_commons.group_claims_input import VERSION, passages, validate_packet
from er_commons.group_ranking import digest, encoded, validate_closure


def packet():
    """Build a synthetic approved question and two exact source paragraphs."""
    original = {"unit_id": "comment", "unit_kind": "comment", "text": "Synthetic concern."}
    response = {
        "unit_id": "response",
        "unit_kind": "response",
        "text": "First assertion.\r\nWrapped line.\r\n\r\nSecond assertion.",
    }
    text = "Synthetic question?"
    sha = digest(text.encode())
    question = {
        "neutral_id": "C001",
        "text": text,
        "text_sha256": sha,
        "comment_id": "comment",
        "original_comment_sha256": digest(encoded(original)),
        "comment_text_sha256": digest(original["text"].encode()),
        "display_version": "v1",
        "approval": {
            "approved_question": text,
            "approved_question_sha256": sha,
            "decision": "approve",
            "explicit_approval": True,
            "display_version": "v1",
        },
    }
    return {
        "schema_version": VERSION,
        "cases": [
            {
                "case_id": "C001",
                "question": question,
                "original_comment": original,
                "responses": [response],
                "passages": passages(response),
                "closure": {"context_unit_ids": ["comment", "response"]},
            }
        ],
    }


def test_paragraph_coordinates_preserve_wrapping_and_crlf():
    """Paragraph spans round-trip exact characters without newline normalization."""
    data = packet()
    validate_packet(data)
    case = data["cases"][0]
    assert len(case["passages"]) == 3
    assert case["passages"][0]["text"] == "First assertion."
    for row in case["passages"]:
        assert case["responses"][0]["text"][row["start"] : row["end"]] == row["text"]


@pytest.mark.parametrize(
    "mutation", ["approval", "question", "comment", "missing_response", "span", "missing_passage"]
)
def test_rejects_stale_approvals_and_incomplete_source(mutation):
    """Mutations cannot preserve a valid frozen or source-bound claim packet."""
    data = copy.deepcopy(packet())
    case = data["cases"][0]
    if mutation == "approval":
        case["question"]["approval"]["explicit_approval"] = False
    elif mutation == "question":
        case["question"]["text"] += " Changed"
    elif mutation == "comment":
        case["original_comment"]["text"] += " Changed"
    elif mutation == "missing_response":
        case["responses"] = []
    elif mutation == "span":
        case["passages"][0]["start"] += 1
    else:
        case["passages"].pop()
    with pytest.raises(ValueError):
        validate_packet(data)


def test_graph_reconciliation_detects_omitted_reachable_response():
    """A local-looking packet cannot hide a reachable official response."""
    case = {
        "comment_id": "c",
        "direct_response_ids": ["r"],
        "context_unit_ids": ["c", "r"],
        "relationship_ids": ["e1"],
    }
    edges = [
        {
            "edge_id": "e1",
            "source_unit_id": "c",
            "target_unit_id": "r",
            "relation_type": "comment_response",
        },
        {
            "edge_id": "e2",
            "source_unit_id": "r",
            "target_unit_id": "r2",
            "relation_type": "response_cross_reference",
        },
    ]
    # Use the maintained inventory relation vocabulary.
    from er_commons.group_ranking import DIRECTED

    edges[1]["relation_type"] = sorted(DIRECTED)[0]
    with pytest.raises(ValueError, match="closure differs"):
        validate_closure(case, edges)
