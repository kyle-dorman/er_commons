"""Source-free checks of current claim cards, anchored inputs and immutable replay."""

import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from er_commons import group_claims as claims
from er_commons.group_claims_input import passages


def packet_proposal() -> tuple[dict[str, Any], dict[str, Any]]:
    """Invent source content independent of all historical benchmark cases."""
    original = {"unit_id": "fictional-comment", "text": "Will the garden open?"}
    question = {
        "text": original["text"],
        "text_sha256": claims.digest(original["text"].encode()),
        "neutral_id": "S001",
        "question_id": "synthetic-question",
        "question_version": "synthetic-v1",
        "display_version": "S001-v1",
        "comment_id": original["unit_id"],
        "original_comment_sha256": claims.digest(claims.encoded(original)),
        "comment_text_sha256": claims.digest(original["text"].encode()),
    }
    question["approval"] = {
        "approved_question": question["text"],
        "approved_question_sha256": question["text_sha256"],
        "decision": "approve",
        "explicit_approval": True,
        "display_version": question["display_version"],
    }
    response = {
        "unit_id": "fictional-response",
        "unit_kind": "response",
        "text": "The garden will open after inspection.\n\nInspection is scheduled for spring.",
    }
    source = {
        "case_id": "S001",
        "question": question,
        "original_comment": original,
        "responses": [response],
        "passages": passages(response),
        "closure": {"context_unit_ids": [original["unit_id"], response["unit_id"]]},
        "supplements": [],
        "outcomes": [],
        "warnings": ["Invented qualification only"],
    }
    packet = {"schema_version": "task08d.input.v1", "cases": [source]}
    proposal = {
        "schema_version": "task08d.proposal.v1",
        "model": "gpt-6-astra",
        "packet_sha256": claims.digest(claims.encoded(packet)),
        "inventory_sha256": "a" * 64,
        "cases": [
            {
                "case_id": "S001",
                "claims": [
                    {
                        "claim_id": "A002",
                        "text": "Inspection is scheduled for spring.",
                        "passage_ids": [source["passages"][1]["passage_id"]],
                        "assertion_ids": ["I002"],
                        "relationship": "supporting",
                        "targets": ["A001"],
                        "rationale": "Explains when the opening condition can be fulfilled.",
                    },
                    {
                        "claim_id": "A001",
                        "text": "The garden will open after inspection.",
                        "passage_ids": [source["passages"][0]["passage_id"]],
                        "assertion_ids": ["I001"],
                        "relationship": "direct",
                        "targets": ["Q1"],
                        "rationale": "Addresses opening and its condition.",
                    },
                ],
                "question_parts": [
                    {
                        "part_id": "Q1",
                        "text": question["text"],
                        "claim_ids": ["A001"],
                        "status": "addressed",
                        "essential": True,
                        "explanation": "The response states a condition.",
                    }
                ],
            }
        ],
    }
    return packet, proposal


def tasks() -> list[dict[str, Any]]:
    """Build a synthetic queue from independent trusted inputs."""
    packet, proposal = packet_proposal()
    return claims.build_tasks(
        packet,
        proposal,
        packet_sha256=claims.digest(claims.encoded(packet)),
        proposal_sha256=claims.digest(claims.encoded(proposal)),
    )


def test_card_order_and_blank_human_decisions() -> None:
    """Direct cards lead without changing identities or importing approval defaults."""
    task = tasks()[0]
    assert [b["claim_id"] for b in task["data"]["slot_bindings"]] == [
        "A001",
        "A002",
        "A003",
        "A004",
        "A005",
        "A006",
    ]
    results = task["predictions"][0]["result"]
    assert not any(r["from_name"].endswith("decision") for r in results)
    assert not any(
        r["from_name"] in {"case_status", "links_confirmed", "gaps_status"} for r in results
    )
    assert next(r for r in results if r["from_name"] == "s002_targets")["value"] == {
        "text": ["A001"]
    }
    root = ET.fromstring(claims.build_form(6))
    values = [choice.attrib["value"] for choice in root.iter("Choice")]
    assert len(values) == len(set(values))
    assert all(choice.attrib.get("alias") for choice in root.iter("Choice"))


@pytest.mark.parametrize("mutation", ["question", "passage", "support", "membership"])
def test_source_and_relationship_corruption_rejected(mutation: str) -> None:
    """Reject drift in frozen questions, exact spans, closure and support targets."""
    packet, proposal = packet_proposal()
    if mutation == "question":
        packet["cases"][0]["question"]["text"] = "Changed question"
    elif mutation == "passage":
        packet["cases"][0]["passages"][0]["text"] = "Changed source"
    elif mutation == "support":
        proposal["cases"][0]["claims"][0]["targets"] = ["A002"]
    else:
        packet["cases"][0]["responses"] = []
    proposal["packet_sha256"] = claims.digest(claims.encoded(packet))
    with pytest.raises(ValueError):
        claims.build_tasks(
            packet,
            proposal,
            packet_sha256=proposal["packet_sha256"],
            proposal_sha256=claims.digest(claims.encoded(proposal)),
        )


def test_prepare_replay_and_no_clobber(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Preparation replays exactly and rejects both overwrites and corrupted files."""
    packet, proposal = packet_proposal()
    source, proposed = tmp_path / "input.json", tmp_path / "proposal.json"
    (tmp_path / "inventory.json").write_bytes(b"{}")
    monkeypatch.setattr(claims, "validate_inventory", lambda *args: {})
    source.write_bytes(claims.encoded(packet))
    proposed.write_bytes(claims.encoded(proposal))
    monkeypatch.setattr(claims, "_snapshots", lambda: {"interface.txt": b"test interface"})
    output = tmp_path / "prepared"
    claims.prepare(source, proposed, output)
    assert claims.load_prepared(output) == tasks()
    with pytest.raises(FileExistsError):
        claims.prepare(source, proposed, output)
    edited = copy.deepcopy(tasks())
    edited[0]["data"]["case_id"] = "foreign"
    (output / "tasks.json").write_bytes(claims.encoded(edited))
    with pytest.raises(ValueError, match="differs"):
        claims.load_prepared(output)


def test_nested_source_warnings_and_exact_card_quotes() -> None:
    """Display every real-shaped warning value plus exact referenced source text."""
    packet, proposal = packet_proposal()
    packet["cases"][0]["warnings"] = {
        "inherited_limits": ["Only the supplied response is represented."],
        "source_flags": {"extraction": ["A <table> has a reading-order warning."]},
        "comment_source_warnings": ["An unclear source mark remains unchanged."],
    }
    proposal["packet_sha256"] = claims.digest(claims.encoded(packet))
    task = claims.build_tasks(
        packet,
        proposal,
        packet_sha256=proposal["packet_sha256"],
        proposal_sha256=claims.digest(claims.encoded(proposal)),
    )[0]
    display = task["data"]["source_html"]
    assert "Only the supplied response is represented." in display
    assert "A &lt;table&gt; has a reading-order warning." in display
    assert "An unclear source mark remains unchanged." in display
    assert packet["cases"][0]["passages"][0]["text"] in task["data"]["s001_html"]
    assert packet["cases"][0]["passages"][1]["text"] in task["data"]["s002_html"]


@pytest.mark.parametrize("binding", ["packet_sha256", "proposal_sha256"])
def test_content_digest_binding_cannot_be_arbitrary(binding: str) -> None:
    """Reject syntactically valid hashes that do not identify the supplied content."""
    packet, proposal = packet_proposal()
    bindings = {
        "packet_sha256": claims.digest(claims.encoded(packet)),
        "proposal_sha256": claims.digest(claims.encoded(proposal)),
    }
    bindings[binding] = "f" * 64
    with pytest.raises(ValueError, match="content hash differs"):
        claims.build_tasks(packet, proposal, **bindings)
