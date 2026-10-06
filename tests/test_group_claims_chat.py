"""Synthetic qualification of display-bound production chat journal and export."""

import copy

import pytest
from test_group_claims import packet_proposal

from er_commons import group_claims_chat as chat


def fixture():
    """Invent independent packet, inventory and proposals with no real approvals."""
    packet, proposal = packet_proposal()
    case = proposal["cases"][0]
    assertions = [
        {"assertion_id": c["assertion_ids"][0], "text": c["text"], "passage_ids": c["passage_ids"]}
        for c in case["claims"]
    ]
    inventory = {
        "schema_version": "task08d.inventory.v1",
        "model": "gpt-6-astra",
        "packet_sha256": chat._sha(packet),
        "cases": [
            {
                "case_id": "S001",
                "assertions": assertions,
                "passage_coverage": [
                    {
                        "passage_id": a["passage_ids"][0],
                        "assertion_ids": [a["assertion_id"]],
                        "note": "Complete synthetic statement.",
                    }
                    for a in assertions
                ],
            }
        ],
    }
    proposal["inventory_sha256"] = chat._sha(inventory)
    queue = chat.prepare_queue(packet, inventory, proposal)
    return queue, chat.new_journal(queue)


def event_add(queue, journal, event):
    """Attach synthetic provenance to each invented event."""
    return chat.add_event(
        queue,
        journal,
        {
            **event,
            "actor": "synthetic reviewer",
            "chat_reference": "synthetic qualification only",
            "timestamp": "2026-10-05T12:00:00-07:00",
        },
    )


def approve(queue, journal, cid="A001", decision="approve"):
    """Record explicit synthetic display then separate decision."""
    state = chat.replay(queue, journal)
    card = chat.render_card(
        queue["packet"]["cases"][0], state["cases"]["S001"], cid, case_position=1, case_count=1
    )
    sha = chat.digest(card.encode())
    journal = event_add(
        queue, journal, {"kind": "display", "case_id": "S001", "claim_id": cid, "card_sha256": sha}
    )
    return event_add(
        queue,
        journal,
        {
            "kind": "decision",
            "case_id": "S001",
            "claim_id": cid,
            "card_sha256": sha,
            "decision": decision,
            "feedback": "Approved" if decision == "approve" else decision,
            "explicit": True,
        },
    )


def conclude(queue, journal, decision="investigate"):
    """Bind a distinct case-level choice to the complete current snapshot."""
    case = chat.replay(queue, journal)["cases"]["S001"]
    return event_add(
        queue,
        journal,
        {
            "kind": "case_decision",
            "case_id": "S001",
            "case_sha256": chat._current_hash(case),
            "decision": decision,
            "explicit": True,
            "feedback": "Synthetic case disposition",
            "links_confirmed": True,
            "gaps_status": "unresolved",
        },
    )


def test_blank_order_cards_and_deterministic_export():
    queue, journal = fixture()
    assert [c["claim_id"] for c in queue["cards"]] == ["A001", "A002"]
    assert all(c["decision"] is None for c in queue["cards"])
    card = queue["cards"][1]["card"]
    assert "The garden will open after inspection." in card
    assert "Will the garden open?" in card
    assert "Inspection is scheduled for spring." in card
    with pytest.raises(ValueError, match="whole-case"):
        chat.export_review(queue, journal)
    journal = conclude(queue, approve(queue, approve(queue, journal), "A002"))
    result = chat.export_review(queue, journal)
    assert len(result["advancing"]) == 2
    assert result == chat.export_review(queue, copy.deepcopy(journal))
    assert result["cases"]["S001"]["case_decision"]["gaps_status"] == "unresolved"


@pytest.mark.parametrize("mutation", ["source", "card", "inventory", "question"])
def test_tampering_fails(mutation):
    queue, journal = fixture()
    if mutation == "source":
        queue["packet"]["cases"][0]["responses"][0]["text"] += " invented"
    elif mutation == "card":
        queue["cards"][0]["card"] += " changed"
    elif mutation == "inventory":
        queue["inventory"]["cases"][0]["assertions"].pop()
    else:
        queue["packet"]["cases"][0]["question"]["text"] += " changed"
    with pytest.raises(ValueError):
        chat.replay(queue, journal)


def test_revision_invalidates_dependents_and_case():
    queue, journal = fixture()
    journal = conclude(queue, approve(queue, approve(queue, journal), "A002"))
    claim = copy.deepcopy(queue["proposal"]["cases"][0]["claims"][1])
    claim["text"] = "The response states that the garden opens after inspection."
    journal = event_add(
        queue,
        journal,
        {
            "kind": "revise",
            "feedback": "Synthetic revision request",
            "case_id": "S001",
            "replaces": ["A001"],
            "claims": [claim],
        },
    )
    case = chat.replay(queue, journal)["cases"]["S001"]
    assert case["decisions"] == {}
    assert case["case_decision"] is None
    assert case["history"][0][1]["text"] == "The garden will open after inspection."
    with pytest.raises(ValueError):
        chat.export_review(queue, conclude(queue, journal))


def test_rejected_target_and_deferred_claim_fail_export():
    queue, journal = fixture()
    for decision in ("reject", "defer"):
        changed = approve(queue, approve(queue, journal, decision=decision), "A002")
        with pytest.raises(ValueError):
            chat.export_review(queue, conclude(queue, changed))
        assert chat.export_review(queue, conclude(queue, changed, "hold"))["advancing"] == []


def test_append_restart_chain_and_discussion(tmp_path):
    queue, _ = fixture()
    path = tmp_path / "journal.jsonl"
    event = {
        "actor": "synthetic",
        "chat_reference": "fixture",
        "timestamp": "2026-10-05T12:00:00-07:00",
        "kind": "discussion",
        "case_id": "S001",
        "feedback": "What does this mean?",
    }
    chat.append_event(path, queue, event)
    journal = chat.append_event(path, queue, event)
    assert chat.replay(queue, journal)["event_count"] == 2
    assert chat.replay(queue, journal)["cases"]["S001"]["decisions"] == {}
    journal["events"][0]["feedback"] = "yes"
    with pytest.raises(ValueError, match="chain"):
        chat.replay(queue, journal)


def test_no_approval_without_display():
    queue, journal = fixture()
    with pytest.raises(ValueError, match="displayed"):
        event_add(
            queue,
            journal,
            {
                "kind": "decision",
                "case_id": "S001",
                "claim_id": "A001",
                "card_sha256": "wrong",
                "decision": "approve",
                "explicit": True,
                "feedback": "approved",
            },
        )


def test_split_merge_and_unanchored_revision():
    queue, journal = fixture()
    first, second = copy.deepcopy(queue["proposal"]["cases"][0]["claims"])
    second["claim_id"] = "A003"
    first["targets"] = ["A003"]
    parts = copy.deepcopy(queue["proposal"]["cases"][0]["question_parts"])
    parts[0]["claim_ids"] = ["A003"]
    journal = event_add(
        queue,
        journal,
        {
            "kind": "revise",
            "feedback": "Synthetic revision request",
            "case_id": "S001",
            "replaces": ["A001", "A002"],
            "claims": [first, second],
            "question_parts": parts,
        },
    )
    assert "A003" in {c["claim_id"] for c in chat.replay(queue, journal)["cases"]["S001"]["claims"]}
    second["passage_ids"] = ["missing"]
    with pytest.raises(ValueError, match="Unanchored"):
        event_add(
            queue,
            journal,
            {
                "kind": "revise",
                "feedback": "Synthetic revision request",
                "case_id": "S001",
                "replaces": ["A003"],
                "claims": [second],
            },
        )


def test_support_cycle_fails():
    queue, journal = fixture()
    claim = copy.deepcopy(queue["proposal"]["cases"][0]["claims"][1])
    claim.update(relationship="supporting", targets=["A002"])
    with pytest.raises(ValueError, match="Cyclic"):
        event_add(
            queue,
            journal,
            {
                "kind": "revise",
                "feedback": "Synthetic revision request",
                "case_id": "S001",
                "replaces": ["A001"],
                "claims": [claim],
            },
        )


def test_true_split_merge_and_chain():
    queue, journal = fixture()
    claims = copy.deepcopy(queue["proposal"]["cases"][0]["claims"])
    direct = claims[1]
    split = copy.deepcopy(direct)
    split.update(
        claim_id="A003",
        text="Opening requires inspection.",
        relationship="supporting",
        targets=["A001"],
    )
    journal = event_add(
        queue,
        journal,
        {
            "kind": "revise",
            "feedback": "Synthetic revision request",
            "case_id": "S001",
            "replaces": ["A001"],
            "claims": [direct, split],
        },
    )
    support = claims[0]
    support["targets"] = ["A003"]
    journal = event_add(
        queue,
        journal,
        {
            "kind": "revise",
            "feedback": "Synthetic revision request",
            "case_id": "S001",
            "replaces": ["A002"],
            "claims": [support],
        },
    )
    for cid in ("A001", "A003", "A002"):
        journal = approve(queue, journal, cid)
    journal = conclude(queue, journal)
    result = chat.export_review(queue, journal)
    row = next(r for r in result["advancing"] if r["claim"]["claim_id"] == "A002")
    assert [c["claim_id"] for c in row["support_chain"]] == ["A003", "A001"]
    support["targets"] = ["A001"]
    journal = event_add(
        queue,
        journal,
        {
            "kind": "revise",
            "feedback": "Synthetic revision request",
            "case_id": "S001",
            "replaces": ["A001", "A003", "A002"],
            "claims": [direct, support],
        },
    )
    state = chat.replay(queue, journal)["cases"]["S001"]
    assert len(state["claims"]) == 2
    assert not state["decisions"]
    assert state["case_decision"] is None
    with pytest.raises(ValueError, match="reused"):
        event_add(
            queue,
            journal,
            {
                "kind": "revise",
                "feedback": "Synthetic revision request",
                "case_id": "S001",
                "replaces": ["A001"],
                "claims": [direct, split],
            },
        )


@pytest.mark.parametrize("fault", ["missing_decision", "blank_feedback", "stale_case", "no_actor"])
def test_incomplete_human_receipts_fail(fault):
    queue, journal = fixture()
    if fault == "missing_decision":
        with pytest.raises(ValueError, match="Missing current"):
            chat.export_review(queue, conclude(queue, approve(queue, journal)))
    elif fault == "no_actor":
        with pytest.raises(ValueError, match="actor"):
            chat.add_event(
                queue, journal, {"kind": "discussion", "case_id": "S001", "feedback": "Question?"}
            )
    elif fault == "blank_feedback":
        with pytest.raises(ValueError, match="discussion"):
            event_add(queue, journal, {"kind": "discussion", "case_id": "S001", "feedback": " "})
    else:
        journal = conclude(queue, approve(queue, approve(queue, journal), "A002"))
        journal = approve(queue, journal, "A001", "reject")
        with pytest.raises(ValueError, match="whole-case"):
            chat.export_review(queue, journal)


@pytest.mark.parametrize("status", ["not-applicable", "resolved"])
def test_unanswered_scope_cannot_disappear_in_case_export(status):
    queue, journal = fixture()
    # This is a structural mutation of the synthetic proposal before preparation,
    # not a transferred approval of changed content.
    proposal = copy.deepcopy(queue["proposal"])
    proposal["cases"][0]["question_parts"][0]["status"] = "unanswered"
    queue = chat.prepare_queue(queue["packet"], queue["inventory"], proposal)
    journal = chat.new_journal(queue)
    journal = conclude(queue, approve(queue, approve(queue, journal), "A002"))
    event = {
        k: v
        for k, v in journal["events"][-1].items()
        if k not in {"sequence", "previous_sha256", "event_sha256"}
    }
    event["gaps_status"] = status
    journal["events"].pop()
    journal = chat.add_event(queue, journal, event)
    with pytest.raises(ValueError):
        chat.export_review(queue, journal)


def test_unindexed_source_reference_is_not_reported_absent():
    queue, _ = fixture()
    source = copy.deepcopy(queue["packet"]["cases"][0])
    case = queue["proposal"]["cases"][0]
    claim = next(c for c in case["claims"] if c["claim_id"] == "A001")
    for unit in source["responses"]:
        unit["supplied_citations"] = []
    for passage in source["passages"]:
        if passage["passage_id"] in claim["passage_ids"]:
            passage["text"] = "See Draft EIR Appendix D, pages 12–14."
    card = chat.render_card(source, case, "A001")
    assert "Reference-bearing response text" in card
    assert "See Draft EIR Appendix D, pages 12–14." in card
    assert "None supplied." not in card
