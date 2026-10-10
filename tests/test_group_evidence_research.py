"""Separate synthetic research packets exercise coverage and fail-closed provenance."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from er_commons.group_evidence_research import (
    TRACKS,
    create_plan,
    new_packet,
    save_plan,
    validate_packet,
)
from er_commons.pilot_evidence import digest


def fixture(tmp_path: Path) -> tuple[dict, dict, dict]:
    """Use an invented question with no found citations, never production evidence."""
    case = {
        "case_id": "SYNTHETIC",
        "question": "What remains unknown?",
        "approved_claims": [{"claim_id": "A1", "version": 1, "text": "Synthetic claim"}],
        "required_context": {"exclusions": ["Chapter 16"]},
    }
    plan = create_plan(
        case,
        {
            track: {"queries": 2, "follow_up_queries": 1, "objective": "Inspect " + track}
            for track in TRACKS
        },
        "One short synthetic question with independent checks",
    )
    packet = new_packet(case, plan)
    packet.update(
        status="prepared, awaiting human review",
        model_provenance={
            "model": "gpt-6-astra",
            "input_sha256": digest(case),
            "prompt_sha256": "prompt",
            "output_sha256": "output",
        },
        limitations=["Bounded synthetic search found no citation; evidence may exist."],
        claim_findings=[
            {
                "finding_id": "F1",
                "claim": case["approved_claims"][0],
                "citations": [],
                "limitations": [],
                "remaining_gaps": ["No citation found within this search budget."],
            }
        ],
    )
    packet["track_results"] = {
        track: {
            "query_receipts": [
                {
                    "query_id": track,
                    "expression": "synthetic",
                    "purpose": track,
                    "index_identity": "synthetic-index",
                    "status": "completed",
                    "hits": [],
                    "inspected_hits": [],
                }
            ],
            "stop_reason": "Saved budget complete",
            "remaining_leads": [],
        }
        for track in TRACKS
    }
    for key, payload in (
        ("input", json.dumps(case)),
        ("prompt", "Synthetic prompt"),
        ("output", "Synthetic raw output"),
    ):
        path = tmp_path / (key + ".json")
        path.write_text(payload)
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        packet["model_provenance"][key + "_ref"] = {"path": path.name, "sha256": checksum}
        if key != "input":
            packet["model_provenance"][key + "_sha256"] = checksum
    return case, plan, packet


def test_restart_and_missing_citation(tmp_path: Path) -> None:
    """Saved plans and exact reloaded packets retain honest negative-search results."""
    case, plan, packet = fixture(tmp_path)
    path = tmp_path / "plan.json"
    save_plan(path, plan)
    with pytest.raises(FileExistsError):
        save_plan(path, plan)
    reloaded = json.loads(json.dumps(packet))
    assert validate_packet(reloaded, case, json.loads(path.read_text()), tmp_path)["claims"] == 1


def test_returned_hit_cannot_disappear(tmp_path: Path) -> None:
    """Returned material needs a disposition even when the worker cannot inspect it."""
    case, plan, packet = fixture(tmp_path)
    receipt = packet["track_results"][TRACKS[0]]["query_receipts"][0]
    receipt["hits"] = [{"source_id": "synthetic", "record_id": "one"}]
    with pytest.raises(ValueError, match="Every returned hit"):
        validate_packet(packet, case, plan, tmp_path)


@pytest.mark.parametrize("mutation", ["human", "claim", "context", "track", "budget", "model"])
def test_reject_incomplete_or_changed_inputs(tmp_path: Path, mutation: str) -> None:
    """Independent corruptions cannot pass by retaining a valid packet status string."""
    case, plan, original = fixture(tmp_path)
    packet = copy.deepcopy(original)
    if mutation == "human":
        packet["human_decisions"] = [{"decision": "accept"}]
    elif mutation == "claim":
        packet["claim_findings"][0]["claim"]["text"] = "Rewritten"
    elif mutation == "context":
        packet["frozen_input"]["required_context"] = {}
    elif mutation == "track":
        del packet["track_results"]["counterevidence"]
    elif mutation == "budget":
        packet["track_results"]["direct_claims"]["query_receipts"] *= 4
    else:
        packet["model_provenance"]["model"] = "other"
    with pytest.raises(ValueError):
        validate_packet(packet, case, plan, tmp_path)


def test_beyond_claim_findings_cannot_be_unsupported(tmp_path: Path) -> None:
    """Definitions, gap findings and conflicts cannot smuggle uncited new assertions."""
    case, plan, packet = fixture(tmp_path)
    for track in TRACKS[1:]:
        packet["beyond_claim_findings"] = [
            {
                "finding_id": "F2",
                "track": track,
                "summary": "Invented assertion",
                "citations": [],
                "limitations": [],
            }
        ]
        with pytest.raises(ValueError, match="grounded"):
            validate_packet(packet, case, plan, tmp_path)


def test_source_bindings_are_not_optional(tmp_path: Path) -> None:
    """A plausible excerpt without canonical unit bindings cannot enter review."""
    case, plan, packet = fixture(tmp_path)
    packet["sources"] = [
        {"candidate_id": "invented", "occurrence_id": "O1", "quote": "Unbound text"}
    ]
    with pytest.raises(ValueError):
        validate_packet(packet, case, plan, tmp_path)


@pytest.mark.parametrize("candidate_number", [0, 1])
def test_exact_source_occurrences_and_beyond_findings(
    tmp_path: Path, candidate_number: int
) -> None:
    """Narrative and table fixtures support independent repeated source occurrences."""
    from er_commons.group_evidence_fixtures import prepare_qualification

    root = tmp_path / "canonical"
    tasks = prepare_qualification(root)
    case, plan, packet = fixture(root)
    candidate = tasks[candidate_number]["data"]["packet"]["candidates"][0]
    packet["sources"] = [{**candidate, "occurrence_id": "O1"}, {**candidate, "occurrence_id": "O2"}]
    if candidate_number == 1:
        render = root / "synthetic.png"
        render.write_bytes(b"synthetic-render-only")
        ref = {"path": render.name, "sha256": hashlib.sha256(render.read_bytes()).hexdigest()}
        packet["table_render_checks"] = [
            {
                "occurrence_id": oid,
                "candidate_id": candidate["candidate_id"],
                "status": "agent_checked",
                "actor": "synthetic agent",
                "comparison": "Invented table fixture matches",
                "limitations": ["Synthetic only"],
                "human_usability_decision": None,
                "renders": [
                    {"physical_page": page, "ref": ref} for page in candidate["physical_pages"]
                ],
            }
            for oid in ("O1", "O2")
        ]
    citation = {
        "occurrence_id": "O1",
        "candidate_id": candidate["candidate_id"],
        "relationship": "Partial",
        "reason": "Synthetic limited support",
        "excerpt": candidate["quote"],
    }
    packet["claim_findings"][0]["citations"] = [citation]
    packet["beyond_claim_findings"] = [
        {
            "finding_id": "F2",
            "track": "definitions_methods",
            "summary": "Synthetic definition",
            "citations": [{**citation, "occurrence_id": "O2"}],
            "limitations": ["Synthetic source only"],
        }
    ]
    assert validate_packet(packet, case, plan, root)["sources"] == 2
    packet["beyond_claim_findings"][0]["citations"][0]["occurrence_id"] = "O1"
    with pytest.raises(ValueError, match="pooled"):
        validate_packet(packet, case, plan, root)
    packet["beyond_claim_findings"][0]["citations"][0]["occurrence_id"] = "O2"
    if candidate_number == 1:
        saved = copy.deepcopy(packet["table_render_checks"])
        packet["table_render_checks"][0]["renders"] = []
        with pytest.raises(ValueError, match="Every table-family page"):
            validate_packet(packet, case, plan, root)
        packet["table_render_checks"] = saved
    packet["beyond_claim_findings"][0]["citations"][0]["excerpt"] = "Fabricated"
    with pytest.raises(ValueError, match="verbatim"):
        validate_packet(packet, case, plan, root)
