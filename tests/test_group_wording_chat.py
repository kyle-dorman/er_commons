"""Synthetic chat journals prove exact approval and append-only review boundaries."""

import copy
from typing import Any

import pytest

from er_commons.group_wording import digest, encoded
from er_commons.group_wording_chat import new_journal, validate_journal


def inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Create invented clean comments and proposals without historical case content."""
    texts = ["Will the fictional garden remain accessible?", "What about noise and lighting?"]
    records = [
        {
            "neutral_id": f"C{i:03d}",
            "original_comment": text,
            "original_comment_sha256": digest(("source" + text).encode()),
            "comment_text_sha256": digest(text.encode()),
            "comment_source_warnings": [],
        }
        for i, text in enumerate(texts, 1)
    ]
    packet = {"schema_version": "task08c.comment_only.v1", "records": records}
    proposal = {
        "schema_version": "task08c.proposal.v1",
        "model": "gpt-6-astra",
        "prompt_version": "task08c.wording.v1",
        "packet_sha256": digest(encoded(packet)),
        "records": [
            {
                "neutral_id": r["neutral_id"],
                "comment_text_sha256": r["comment_text_sha256"],
                "question": texts[0] if i == 0 else None,
                "rewrite_reason": "Synthetic",
                "stop_reason": None if i == 0 else "Multiple independent asks.",
            }
            for i, r in enumerate(records)
        ],
    }
    return (
        packet,
        proposal,
        {
            "packet_sha256": digest(encoded(packet)),
            "proposal_sha256": digest(encoded(proposal)),
            "prompt_sha256": "a" * 64,
        },
    )


def initial() -> dict[str, Any]:
    """Construct pending source-bound state with two actual display events."""
    packet, proposal, bindings = inputs()
    journal = new_journal(packet, proposal, **bindings, namespace="synthetic")
    for i, row in enumerate(proposal["records"], 1):
        journal["events"].append(
            {
                "event_id": i,
                "kind": "display",
                "neutral_id": row["neutral_id"],
                "display_version": row["neutral_id"] + "-v1",
                "question": row["question"],
                "question_sha256": digest(row["question"].encode()) if row["question"] else None,
                "origin": "original_proposal",
                "unsupported_content": False,
                "source_support_note": "",
                "support_resolution": "none",
                "chat_reference": "synthetic:display",
                "timestamp": "2026-09-30T12:00:00Z",
            }
        )
    return journal


def approve(journal: dict[str, Any], cid: str = "C001") -> None:
    """Append explicitly transcribed synthetic approval for the latest display."""
    display = [e for e in journal["events"] if e["kind"] == "display" and e["neutral_id"] == cid][
        -1
    ]
    journal["events"].append(
        {
            "event_id": len(journal["events"]) + 1,
            "kind": "disposition",
            "neutral_id": cid,
            "chat_reference": "synthetic:approval",
            "timestamp": "2026-09-30T12:01:00Z",
            "actor": "Kyle",
            "statement": f"I approve the exact wording of {display['display_version']}.",
            "display_version": display["display_version"],
            "decision": "approve",
            "explicit_approval": True,
            "approved_question": display["question"],
            "approved_question_sha256": display["question_sha256"],
        }
    )


def validate(journal: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Replay against independently constructed source/proposal hashes."""
    packet, proposal, bindings = inputs()
    return validate_journal(journal, packet, proposal, **bindings, previous=previous)


def feedback(journal: dict[str, Any], unsupported: bool = False) -> None:
    """Record a clarification as feedback, never as an implicit decision."""
    journal["events"].append(
        {
            "event_id": len(journal["events"]) + 1,
            "kind": "feedback",
            "display_version": [
                e["display_version"]
                for e in journal["events"]
                if e["kind"] == "display" and e["neutral_id"] == "C001"
            ][-1],
            "neutral_id": "C001",
            "chat_reference": "synthetic:feedback",
            "timestamp": "2026-09-30T12:02:00Z",
            "actor": "Kyle",
            "statement": "Please clarify the proposed wording.",
            "unsupported_content": unsupported,
        }
    )


def revision(journal: dict[str, Any], question: str) -> None:
    """Present an exact replacement as a new version without approving it."""
    event = copy.deepcopy(journal["events"][0])
    event.update(
        event_id=len(journal["events"]) + 1,
        display_version="C001-v2",
        question=question,
        question_sha256=digest(question.encode()),
        origin="revision",
        source_support_note="Synthetic revision stays within the source's accessibility issue.",
    )
    journal["events"].append(event)


def test_initial_null_proposal_is_pending_not_exclusion() -> None:
    result = validate(initial())
    assert [r["state"] for r in result["records"]] == ["pending", "pending"]
    assert result["advancing_neutral_ids"] == []
    assert result["records"][1]["display_history"][0]["question"] is None


def test_exact_edited_version_approval_preserves_every_character() -> None:
    journal = initial()
    question = "  Will access to the fictional garden remain?\n"
    revision(journal, question)
    approve(journal)
    result = validate(journal)
    frozen = result["records"][0]["frozen_question"]
    assert frozen["text"] == question
    assert frozen["text_sha256"] == digest(question.encode())
    assert frozen["display_version"] == "C001-v2"
    assert result["advancing_neutral_ids"] == ["C001"]
    assert result["records"][1]["state"] == "pending"
    assert len(result["records"][0]["display_history"]) == 2


@pytest.mark.parametrize("mutation", ["stale", "text", "hash", "implicit", "null"])
def test_bad_approval_fails(mutation: str) -> None:
    journal = initial()
    revision(journal, "Is access to the fictional garden preserved?")
    approve(journal, "C002" if mutation == "null" else "C001")
    event = journal["events"][-1]
    if mutation == "stale":
        event["display_version"] = "C001-v1"
    elif mutation == "text":
        event["approved_question"] += " changed"
    elif mutation == "hash":
        event["approved_question_sha256"] = "b" * 64
    elif mutation == "implicit":
        event["explicit_approval"] = False
    with pytest.raises(ValueError):
        validate(journal)


def test_feedback_invalidates_approval_and_requires_redisplay() -> None:
    journal = initial()
    approve(journal)
    assert validate(journal)["advancing_neutral_ids"] == ["C001"]
    feedback(journal)
    result = validate(journal)
    assert result["advancing_neutral_ids"] == []
    assert result["records"][0]["state"] == "pending"
    approve(journal)
    with pytest.raises(ValueError, match="fresh display"):
        validate(journal)


def test_unsupported_clarification_cannot_be_overridden_by_approval() -> None:
    journal = initial()
    feedback(journal, unsupported=True)
    revision(journal, journal["events"][0]["question"])
    with pytest.raises(ValueError, match="explicit source-grounded resolution"):
        validate(journal)
    journal["events"].pop()
    revision(journal, "Will access to the fictional garden remain?")
    journal["events"][-1]["unsupported_content"] = True
    approve(journal)
    with pytest.raises(ValueError, match="Unsupported content"):
        validate(journal)
    journal["events"].pop()
    journal["events"][-1]["unsupported_content"] = False
    journal["events"][-1]["support_resolution"] = "removed_unsupported_content"
    approve(journal)
    assert validate(journal)["advancing_neutral_ids"] == ["C001"]


@pytest.mark.parametrize("decision,state", [("exclude", "excluded"), ("unresolved", "unresolved")])
def test_explicit_nonapproval_never_advances(decision: str, state: str) -> None:
    journal = initial()
    approve(journal, "C002")
    journal["events"][-1].update(
        decision=decision,
        explicit_approval=False,
        approved_question=None,
        approved_question_sha256=None,
    )
    assert validate(journal)["records"][1]["state"] == state
    assert validate(journal)["advancing_neutral_ids"] == []


def test_append_only_snapshots_and_original_proposal_fidelity() -> None:
    previous = initial()
    journal = copy.deepcopy(previous)
    journal["previous_snapshot_sha256"] = digest(encoded(previous))
    approve(journal)
    assert validate(journal, previous)["advancing_neutral_ids"] == ["C001"]
    with pytest.raises(ValueError, match="Previous snapshot required"):
        validate(journal)
    journal["events"][0]["source_support_note"] = "changed history"
    with pytest.raises(ValueError, match="append-only"):
        validate(journal, previous)
    journal = initial()
    journal["events"][0]["question"] = "Unintended edit?"
    journal["events"][0]["question_sha256"] = digest(b"Unintended edit?")
    with pytest.raises(ValueError, match="original proposal exactly"):
        validate(journal)


def test_declined_unsupported_suggestion_preserves_supported_wording() -> None:
    journal = initial()
    original = journal["events"][0]["question"]
    feedback(journal, unsupported=True)
    revision(journal, original)
    journal["events"][-1].update(
        support_resolution="declined_unsupported_clarification",
        source_support_note=(
            "The added assumption is declined; the original supported question is unchanged."
        ),
    )
    approve(journal)
    assert validate(journal)["records"][0]["frozen_question"]["text"] == original


def test_declining_feedback_cannot_override_flagged_displayed_wording() -> None:
    journal = initial()
    journal["events"][0]["unsupported_content"] = True
    revision(journal, journal["events"][0]["question"])
    journal["events"][-1]["support_resolution"] = "declined_unsupported_clarification"
    journal["events"][-1]["unsupported_content"] = False
    approve(journal)
    with pytest.raises(ValueError, match="cannot clear flagged"):
        validate(journal)
