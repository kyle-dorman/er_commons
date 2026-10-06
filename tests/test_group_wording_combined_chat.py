"""Exercise combined queue boundaries with invented comment-only sources."""

import copy

import pytest

from er_commons.group_wording import digest, encoded
from er_commons.group_wording_combined_chat import append_event, new_journal, validate_journal


def inputs():
    """Provide synthetic global queue and explicit byte bindings."""
    rows = []
    for index in range(1, 58):
        text = f"Please explain issue {index}."
        rows.append(
            {
                "neutral_id": f"C{index:03d}",
                "original_comment": text,
                "original_comment_sha256": digest(encoded({"text": text})),
                "comment_text_sha256": digest(text.encode()),
                "comment_source_warnings": [],
            }
        )
    packet = {"schema_version": "task08c.comment_only.v2", "records": rows}
    bindings = {"packet_sha256": digest(encoded(packet)), "prompt_sha256": digest(b"prompt")}
    return packet, bindings


def display(packet, bindings, *, index=0, question="What explains issue 1?", version=1):
    """Bind one lazily generated proposal to its exact comment."""
    source = packet["records"][index]
    proposal = {
        key: source[key] for key in ("neutral_id", "original_comment_sha256", "comment_text_sha256")
    }
    proposal.update(
        **bindings,
        question=question,
        stop_reason=None if question else "Ambiguous ask",
        origin="astra",
        model="gpt-6-astra",
        source_artifact_sha256=None,
    )
    return {
        "event_id": 1,
        "timestamp": "2026-10-01T12:00:00-07:00",
        "chat_reference": "fixture",
        "neutral_id": source["neutral_id"],
        "kind": "display",
        "display_version": f"{source['neutral_id']}-v{version}",
        "question": question,
        "question_sha256": digest(question.encode()) if question else None,
        "unsupported_content": False,
        "source_support_note": "Uses original comment only.",
        "support_resolution": "none",
        "proposal": proposal,
        "proposal_sha256": digest(encoded(proposal)),
    }


def decision(shown, *, choice="approve"):
    """Create explicit synthetic human disposition against a displayed version."""
    event = {
        key: shown[key] for key in ("timestamp", "chat_reference", "neutral_id", "display_version")
    }
    event.update(
        event_id=2,
        kind="disposition",
        actor="Synthetic reviewer",
        statement="I approve this exact version.",
        decision=choice,
        explicit_approval=choice == "approve",
        approved_question=shown["question"] if choice == "approve" else None,
        approved_question_sha256=shown["question_sha256"] if choice == "approve" else None,
    )
    return event


def replay(events):
    """Replay one initial snapshot for convenient corruption tests."""
    packet, bindings = inputs()
    journal = new_journal(packet, **bindings, namespace="fixture")
    journal["events"] = events
    return validate_journal(journal, packet, **bindings)


def test_lazy_sequential_approval_and_deterministic_export():
    packet, bindings = inputs()
    first = display(packet, bindings)
    pending = replay([first])
    assert pending["current_position"] == 1
    assert not pending["records"][1]["display_history"]
    events = [first, decision(first)]
    result = replay(events)
    assert result == replay(events)
    assert result["current_position"] == 2
    assert result["advancing_neutral_ids"] == ["C001"]
    assert result["records"][0]["frozen_question"]["text"] == first["question"]


@pytest.mark.parametrize("choice", ["exclude", "defer"])
def test_null_is_pending_until_explicit_disposition(choice):
    packet, bindings = inputs()
    first = display(packet, bindings, question=None)
    assert replay([first])["current_position"] == 1
    result = replay([first, decision(first, choice=choice)])
    assert result["current_position"] == 2
    assert not result["advancing_neutral_ids"]


@pytest.mark.parametrize(
    "mutation", ["stale", "blank", "unsupported", "null", "hash", "not_explicit"]
)
def test_invalid_approvals_rejected(mutation):
    packet, bindings = inputs()
    first = display(
        packet, bindings, question=None if mutation == "null" else "What explains issue 1?"
    )
    approved = decision(first)
    if mutation == "stale":
        approved["display_version"] = "C001-v0"
    elif mutation == "blank":
        approved["statement"] = " "
    elif mutation == "unsupported":
        first["unsupported_content"] = True
    elif mutation == "hash":
        approved["approved_question_sha256"] = "0" * 64
    elif mutation == "not_explicit":
        approved["explicit_approval"] = False
    with pytest.raises(ValueError):
        replay([first, approved])


def test_jump_and_revisit_after_disposition_rejected():
    packet, bindings = inputs()
    first = display(packet, bindings)
    second = display(packet, bindings, index=1)
    with pytest.raises(ValueError, match="current queue"):
        replay([second])
    first_again = copy.deepcopy(first)
    first_again["event_id"] = 3
    with pytest.raises(ValueError, match="current queue"):
        replay([first, decision(first), first_again])


def test_feedback_requires_redisplay_and_new_exact_approval():
    packet, bindings = inputs()
    first = display(packet, bindings)
    feedback = {
        key: first[key] for key in ("timestamp", "chat_reference", "neutral_id", "display_version")
    }
    feedback.update(
        event_id=2,
        kind="feedback",
        actor="Reviewer",
        statement="Please clarify issue.",
        unsupported_content=False,
    )
    old = decision(first)
    old["event_id"] = 3
    with pytest.raises(ValueError, match="redisplayed"):
        replay([first, feedback, old])
    revised = display(packet, bindings, question="Why does issue 1 occur?", version=2)
    revised["event_id"] = 3
    approved = decision(revised)
    approved["event_id"] = 4
    result = replay([first, feedback, revised, approved])
    assert len(result["records"][0]["display_history"]) == 2
    assert result["records"][0]["feedback_history"] == [feedback]
    assert result["records"][0]["frozen_question"]["text"] == revised["question"]


def test_historical_wording_requires_new_approval():
    packet, bindings = inputs()
    first = display(packet, bindings)
    first["proposal"].update(
        origin="historical_approved_wording",
        model=None,
        source_artifact_sha256=digest(b"historical export"),
    )
    first["proposal_sha256"] = digest(encoded(first["proposal"]))
    assert replay([first])["advancing_neutral_ids"] == []
    assert replay([first, decision(first)])["advancing_neutral_ids"] == ["C001"]


def test_snapshot_chain_rejects_prefix_mutation_and_binding_changes():
    packet, bindings = inputs()
    previous = new_journal(packet, **bindings, namespace="fixture")
    first = append_event(previous, display(packet, bindings))
    validate_journal(first, packet, **bindings, previous=previous)
    second = append_event(first, decision(first["events"][0]))
    validate_journal(second, packet, **bindings, previous=first)
    second["events"][0]["source_support_note"] = "changed"
    with pytest.raises(ValueError, match="prefix"):
        validate_journal(second, packet, **bindings, previous=first)
    with pytest.raises(ValueError, match="Previous snapshot required"):
        validate_journal(first, packet, **bindings)


def test_proposal_source_and_input_hash_corruption_rejected():
    packet, bindings = inputs()
    for key in ("original_comment_sha256", "packet_sha256", "prompt_sha256"):
        first = display(packet, bindings)
        first["proposal"][key] = "0" * 64
        first["proposal_sha256"] = digest(encoded(first["proposal"]))
        with pytest.raises(ValueError, match="binding"):
            replay([first])


def test_unsupported_feedback_requires_explicit_resolution():
    packet, bindings = inputs()
    first = display(packet, bindings)
    feedback = {
        key: first[key] for key in ("timestamp", "chat_reference", "neutral_id", "display_version")
    }
    feedback.update(
        event_id=2,
        kind="feedback",
        actor="Reviewer",
        statement="Add an unsupported fact.",
        unsupported_content=True,
    )
    revised = display(packet, bindings, version=2)
    revised["event_id"] = 3
    with pytest.raises(ValueError, match="explicit source resolution"):
        replay([first, feedback, revised])
    revised["support_resolution"] = "declined_unsupported_clarification"
    assert replay([first, feedback, revised])["current_position"] == 1


def test_packet_warning_mutation_rejected():
    packet, bindings = inputs()
    journal = new_journal(packet, **bindings, namespace="fixture")
    packet["records"][0]["comment_source_warnings"] = ["Changed warning"]
    with pytest.raises(ValueError, match="packet checksum"):
        validate_journal(journal, packet, **bindings)
