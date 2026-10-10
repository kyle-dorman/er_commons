"""Invented evidence-only fixtures qualify Phase A and later chat checkpointing."""

import copy

import pytest

from er_commons import group_evidence_chat as chat


def packet():
    """Keep missing citations, definitions, counterevidence and full tables distinct."""
    claim = {"claim_id": "A001", "version": 2, "text": "The pond retains water."}
    citation = {
        "candidate_id": "S1",
        "occurrence_id": "O1",
        "relationship": "Context",
        "reason": "Defines storage.",
        "excerpt": "Storage means retained water.",
    }
    return {
        "schema_version": "task08e.research_packet.v1",
        "frozen_input": {
            "case_id": "S001",
            "question": {"text": "Does the pond retain water?"},
            "approved_claims": [claim],
            "required_context": ["Do not infer capacity."],
        },
        "claim_findings": [
            {
                "finding_id": "F1",
                "claim": claim,
                "citations": [],
                "limitations": ["Bounded search"],
                "remaining_gaps": ["Capacity"],
            }
        ],
        "beyond_claim_findings": [
            {
                "finding_id": "F2",
                "track": "definitions_methods",
                "summary": "Storage definition",
                "citations": [citation],
                "limitations": [],
            },
            {
                "finding_id": "F3",
                "track": "counterevidence",
                "summary": "Dry-season limit",
                "citations": [{**citation, "relationship": "Contradicts"}],
                "limitations": ["Seasonal"],
            },
        ],
        "sources": [
            {
                "candidate_id": "S1",
                "occurrence_id": "O1",
                "text": "Storage means retained water.",
                "table_family": {
                    "caption": "Invented seasons",
                    "rows": [["dry", "zero"]],
                    "notes": ["Seasonal"],
                    "render_sha256": "invented",
                },
            }
        ],
        "human_decisions": [],
        "eligibility": None,
        "disposition": None,
    }


def event(kind, **kwargs):
    """Attach explicit synthetic reviewer provenance without dataset decisions."""
    return {
        "kind": kind,
        "actor": "Synthetic reviewer",
        "chat_reference": "fixture only",
        "timestamp": "2026-10-06T12:00:00-07:00",
        **kwargs,
    }


def display(p, j, ids):
    """Save actual text and exact source payload before any scoped approval."""
    card = chat.render_display(p, ids)
    return chat.add_event(p, j, event("display", display=card)), card


def decide(p, j, card, ids):
    """Record an invented explicit decision on named displayed findings only."""
    return chat.add_event(
        p,
        j,
        event(
            "decision",
            display_sha256=chat.sha(card),
            finding_ids=ids,
            decision="accept",
            explicit=True,
            feedback="Accept these only.",
        ),
    )


def test_blank_preparation_export_and_source_fidelity():
    p = packet()
    j = chat.new_journal(p, synthetic=True)
    result = chat.export_review(p, j)
    assert result["human_decisions"] == {}
    assert result["eligibility"] is None and result["next_stage"] is None
    assert result["state"]["resume_finding_id"] == "F1"
    card = chat.render_display(p, ["F1", "F2", "F3"])
    assert card["findings"] == p["claim_findings"] + p["beyond_claim_findings"]
    assert card["sources"] == p["sources"]
    assert "Do not infer capacity." in card["text"]
    assert "Does the pond retain water?" in card["text"]
    assert "does not establish" in card["text"]


def test_scoped_acceptance_rejects_hidden_and_malformed_display():
    p = packet()
    j, card = display(p, chat.new_journal(p, synthetic=True, phase="review"), ["F2", "F3"])
    j = decide(p, j, card, ["F2"])
    assert chat.replay(p, j)["pending_finding_ids"] == ["F1", "F3"]
    with pytest.raises(ValueError, match="scope"):
        decide(p, j, card, ["F1"])
    wrong = copy.deepcopy(card)
    wrong["text"] += "unbound extra summary"
    with pytest.raises(ValueError, match="Display"):
        chat.add_event(p, j, event("display", display=wrong))
    with pytest.raises(ValueError, match="blank"):
        chat.export_review(p, j)


def test_revision_reopens_decisions_and_preserves_history():
    p = packet()
    j, card = display(p, chat.new_journal(p, synthetic=True, phase="review"), ["F2", "F3"])
    j = decide(p, j, card, ["F2", "F3"])
    revised = copy.deepcopy(p)
    revised["beyond_claim_findings"][0]["summary"] = "Revised definition limitation."
    j = chat.add_event(
        p,
        j,
        event(
            "revise", packet=revised, replaces_sha256=chat.sha(p), feedback="Retain uncertainty."
        ),
    )
    assert not chat.replay(p, j)["decisions"]
    with pytest.raises(ValueError, match="current display"):
        decide(p, j, card, ["F2"])
    result = chat.export_review(p, j, preparation=False)
    assert result["journal"]["events"][1]["feedback"] == "Accept these only."
    revised["frozen_input"]["question"]["text"] += " changed"
    with pytest.raises(ValueError, match="Frozen|Phase A"):
        chat.add_event(
            p,
            chat.new_journal(p),
            event(
                "revise",
                packet=revised,
                replaces_sha256=chat.sha(p),
                feedback="Forbidden question edit",
            ),
        )


def test_follow_up_requires_plan_and_retains_receipts():
    p = packet()
    j = chat.new_journal(p, synthetic=True, phase="review")
    result = event(
        "follow_up_result",
        search_id="search1",
        receipts=[{"query": "pond dry"}],
        remaining_limits="Bounded to one section",
    )
    with pytest.raises(ValueError, match="prior unused"):
        chat.add_event(p, j, result)
    j = chat.add_event(
        p,
        j,
        event(
            "follow_up_plan",
            search_id="search1",
            purpose="Resolve season",
            scope="Pond section",
            effort_budget="Two queries",
            packet_sha256=chat.sha(p),
        ),
    )
    j = chat.add_event(p, j, result)
    assert (
        chat.replay(p, j)["follow_up_searches"]["search1"]["receipt"]["receipts"]
        == result["receipts"]
    )


def test_save_reload_resume_and_tampering(tmp_path):
    p = packet()
    path = tmp_path / "journal.jsonl"
    card = chat.render_display(p, ["F1"])
    chat.append_event(path, p, event("display", display=card), synthetic=True, phase="review")
    j = chat.append_event(
        path,
        p,
        event(
            "decision",
            display_sha256=chat.sha(card),
            finding_ids=["F1"],
            decision="defer",
            explicit=True,
            feedback="More research",
        ),
        synthetic=True,
        phase="review",
    )
    loaded = chat.load_journal(path, p, synthetic=True, phase="review")
    assert chat.export_review(p, loaded, preparation=False) == chat.export_review(
        p, j, preparation=False
    )
    assert chat.replay(p, loaded)["resume_finding_id"] == "F2"
    loaded["events"][0]["display"]["text"] += "tamper"
    with pytest.raises(ValueError, match="chain"):
        chat.replay(p, loaded)
    path.write_text(path.read_text().rstrip())
    with pytest.raises(ValueError, match="Incomplete"):
        chat.load_journal(path, p)


@pytest.mark.parametrize("kind", ["case_decision", "eligibility", "advance"])
def test_phase_a_contract_never_exports_eligibility(kind):
    p = packet()
    with pytest.raises(ValueError, match="Phase A"):
        chat.add_event(p, chat.new_journal(p), event(kind, decision="advance"))


def test_missing_bindings_and_model_decisions_rejected():
    p = packet()
    p["sources"] = []
    with pytest.raises(ValueError, match="Missing source"):
        chat.new_journal(p)
    p = packet()
    p["human_decisions"] = ["accepted by model"]
    with pytest.raises(ValueError, match="human decisions"):
        chat.new_journal(p)


def test_synthetic_case_disposition_requires_current_complete_review():
    p = packet()
    j = chat.new_journal(p, synthetic=True, phase="review")
    j, card = display(p, j, ["F1", "F2", "F3"])
    j = decide(p, j, card, ["F1", "F2", "F3"])
    state = chat.replay(p, j)
    closeout = chat.render_case_display(p, state["decisions"])
    j = chat.add_event(p, j, event("case_display", display=closeout))
    disposition = event(
        "case_decision",
        display_sha256=chat.sha(closeout),
        explicit=True,
        decision="advance_to_08f",
        eligibility={
            "eligible": True,
            "reasons": "Synthetic eligibility only; bounded gaps considered.",
        },
        feedback="Advance this synthetic case only.",
    )
    j = chat.add_event(p, j, disposition)
    result = chat.export_review(p, j, preparation=False)
    assert result["disposition"] == "advance_to_08f"
    assert result["next_stage"] is None
    revised = copy.deepcopy(p)
    revised["claim_findings"][0]["remaining_gaps"].append("Another gap")
    j = chat.add_event(
        p, j, event("revise", packet=revised, replaces_sha256=chat.sha(p), feedback="Gap found")
    )
    assert chat.replay(p, j)["case_decision"] is None
    with pytest.raises(ValueError, match="current case display"):
        chat.add_event(p, j, disposition)


def test_unreviewed_case_can_hold_but_cannot_advance():
    p = packet()
    j = chat.new_journal(p, synthetic=True, phase="review")
    closeout = chat.render_case_display(p, {})
    j = chat.add_event(p, j, event("case_display", display=closeout))
    decision = event(
        "case_decision",
        display_sha256=chat.sha(closeout),
        explicit=True,
        decision="advance_to_08f",
        eligibility={"eligible": True, "reasons": "Test"},
        feedback="Test",
    )
    with pytest.raises(ValueError, match="complete reviewed"):
        chat.add_event(p, j, decision)
    decision["decision"] = "hold"
    decision["eligibility"]["eligible"] = None
    j = chat.add_event(p, j, decision)
    assert chat.export_review(p, j, preparation=False)["disposition"] == "hold"


def test_repeated_source_occurrences_and_readable_locations():
    p = packet()
    p["sources"][0].update(
        title="Invented hydrology appendix",
        edition="Draft EIR",
        printed_labels=["H-2"],
        physical_pages=[7],
    )
    duplicate = copy.deepcopy(p["sources"][0])
    duplicate["occurrence_id"] = "O2"
    p["sources"].append(duplicate)
    p["beyond_claim_findings"][1]["citations"][0]["occurrence_id"] = "O2"
    card = chat.render_display(p, ["F2", "F3"])
    assert len(card["sources"]) == 2
    assert "Invented hydrology appendix" in card["text"]
    assert "printed pages ['H-2']; PDF pages [7]" in card["text"]
    assert "table_family" not in card["text"]
    assert card["sources"][0]["table_family"] == duplicate["table_family"]


def test_journal_mode_cannot_change_after_interactions():
    p = packet()
    j, _ = display(p, chat.new_journal(p, synthetic=True, phase="review"), ["F1"])
    j["phase"] = "preparation"
    with pytest.raises(ValueError, match="chain"):
        chat.replay(p, j)
