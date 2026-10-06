"""Qualify v2 ordering boundaries, accepted memberships and sealed publication."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from er_commons import group_ranking_v2 as ranking
from er_commons.group_ranking import digest, encoded


def fixture(count: int = 4) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    """Provide inherited source flags without requiring the external release."""
    packet = {
        "group": {"group": "fixture"},
        "inventory_id": "fixture-inventory",
        "candidates": [
            {
                "comment_id": cid,
                "challenge_signals": ["visual_target"],
                "planning_record": {"revision_flag": True},
            }
            for cid in list("dcba")[:count]
        ],
    }
    content, prompt = encoded(packet), b"Shared v2 prompt"
    proposal = {
        "schema_version": "task08a.proposal.v2",
        "input_sha256": digest(content),
        "prompt_sha256": digest(prompt),
        "prompt_version": ranking.VERSION,
        "model": "gpt-6-astra",
        "preparation_mode": "model_ranked",
        "ranking_not_needed_reason": None,
        "proposal_version": 1,
        "reranking_reason": None,
        "tie_groups": [],
        "ranking": [
            {"comment_id": cid, "rank": rank} for rank, cid in enumerate(list("dcba")[:count], 1)
        ],
    }
    return packet, proposal, content, prompt


@pytest.mark.parametrize("count", [1, 2, 3])
def test_small_group_deterministic_bypass(count: int) -> None:
    """Small groups never declare a ranking model and preserve every original candidate."""
    packet, _, content, prompt = fixture(count)
    proposal = ranking.small_group_proposal(packet, content, prompt)
    assert proposal["model"] is None
    assert proposal["preparation_mode"] == "deterministic"
    assert proposal["ranking_not_needed_reason"] == ranking.BYPASS_REASON
    assert [row["comment_id"] for row in proposal["ranking"]] == sorted(
        row["comment_id"] for row in packet["candidates"]
    )
    proposal["model"] = "gpt-6-astra"
    with pytest.raises(ValueError, match="Small groups"):
        ranking.validate_proposal(packet, proposal, content, prompt)


def test_larger_group_cannot_bypass() -> None:
    """Four candidates require actual Astra identity and a model-ranked order."""
    packet, proposal, content, prompt = fixture()
    ranking.validate_proposal(packet, proposal, content, prompt)
    with pytest.raises(ValueError, match="one to three"):
        ranking.small_group_proposal(packet, content, prompt)
    proposal["model"] = None
    with pytest.raises(ValueError, match="actual gpt-6-astra"):
        ranking.validate_proposal(packet, proposal, content, prompt)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "rank",
        "rationale",
        "rewrite",
        "eligibility",
        "input",
        "prompt",
        "model",
        "tie",
        "rerank",
    ],
)
def test_invalid_proposals_fail(mutation: str) -> None:
    """Reject omissions, generated narratives, decisions and stale lineage."""
    packet, proposal, content, prompt = fixture()
    if mutation == "missing":
        proposal["ranking"].pop()
    elif mutation == "duplicate":
        proposal["ranking"][1]["comment_id"] = "d"
    elif mutation == "rank":
        proposal["ranking"][0]["rank"] = 3
    elif mutation in {"rationale", "rewrite", "eligibility"}:
        proposal["ranking"][0][mutation] = "forbidden"
    elif mutation in {"input", "prompt"}:
        proposal[mutation + "_sha256"] = "0" * 64
    elif mutation == "model":
        proposal["model"] = "gpt-6-sol"
    elif mutation == "tie":
        proposal["tie_groups"] = [["d", "c"]]
    elif mutation == "rerank":
        proposal["proposal_version"] = 2
    with pytest.raises((ValueError, ValidationError)):
        ranking.validate_proposal(packet, proposal, content, prompt)


def test_membership_roots_require_full_closure_and_accepted_edges() -> None:
    """A membership root can add general responses but never unrelated graph edges."""
    edges = [
        {
            "edge_id": "direct",
            "source_unit_id": "c",
            "target_unit_id": "r",
            "relation_type": "comment_response",
        },
        {
            "edge_id": "membership",
            "source_unit_id": "g",
            "target_unit_id": "c",
            "relation_type": "general_response_membership",
        },
        {
            "edge_id": "linked",
            "source_unit_id": "g",
            "target_unit_id": "g2",
            "relation_type": "general_response_general_response",
        },
    ]
    case = {
        "comment_id": "c",
        "direct_response_ids": ["r"],
        "context_unit_ids": ["c", "r", "g", "g2"],
        "relationship_ids": ["direct", "membership", "linked"],
    }
    ranking.validate_closure(case, edges, ["direct", "membership"])
    for key, values in [
        ("context_unit_ids", ["c", "r", "g"]),
        ("relationship_ids", ["direct", "membership"]),
    ]:
        with pytest.raises(ValueError):
            ranking.validate_closure({**case, key: values}, edges, ["direct", "membership"])
    with pytest.raises(ValueError, match="omits"):
        ranking.validate_closure(case, edges, ["direct"])
    with pytest.raises(ValueError):
        ranking.validate_closure(case, edges, ["direct", "membership", "invented"])


def test_publication_completion_last_and_no_clobber(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate before sealing, retain warnings, and reject tampering or overwrite."""
    packet, proposal, content, prompt = fixture()
    monkeypatch.setattr(ranking, "replay", lambda packet: None)
    paths = {name: tmp_path / name for name in ("input", "proposal", "prompt", "spec")}
    paths["input"].write_bytes(content)
    paths["proposal"].write_bytes(encoded(proposal))
    paths["prompt"].write_bytes(prompt)
    paths["spec"].write_text("Shared v2")
    output = tmp_path / "published"
    args = (paths["input"], paths["proposal"], paths["prompt"], paths["spec"])
    handoff = ranking.publish(*args, output)
    assert handoff["human_selection"] == handoff["human_eligibility"] == "pending"
    saved = json.loads((output / "ranked_candidates.json").read_bytes())
    assert saved[0]["candidate"] == packet["candidates"][0]
    with pytest.raises(FileExistsError):
        ranking.publish(*args, output)
    altered = copy.deepcopy(saved)
    altered[0]["candidate"]["challenge_signals"] = []
    (output / "ranked_candidates.json").write_bytes(encoded(altered))
    with pytest.raises(ValueError, match="Checksum"):
        ranking.validate(output)

    def fail_validation(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """Simulate failed final replay before a completion marker is written."""
        raise ValueError("injected final validation failure")

    monkeypatch.setattr(ranking, "_validate", fail_validation)
    incomplete = tmp_path / "incomplete"
    with pytest.raises(ValueError, match="injected"):
        ranking.publish(*args, incomplete)
    assert not (incomplete / "completion.json").exists()
