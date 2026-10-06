"""Exercise advisory ordering, source anchors, warnings, and immutable publication."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema.exceptions import ValidationError  # type: ignore[import-untyped]

from er_commons import group_ranking as ranking


def fixture() -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    """Provide two source-free comments with independent response context."""
    packet = {
        "group": {"group": "fixture"},
        "inventory_id": "fixture-inventory",
        "candidates": [
            {
                "comment_id": cid,
                "context_unit_ids": [cid, "r" + cid],
                "challenge_signals": ["visual_target"],
                "planning_record": {"revision_flag": True},
            }
            for cid in ("a", "b")
        ],
        "source_units": [
            {"unit_id": uid, "text": f"Exact source {uid}."} for uid in ("a", "b", "ra", "rb")
        ],
    }
    content, prompt = ranking.encoded(packet), b"Versioned ranking policy"
    proposal = {
        "schema_version": "task08a.proposal.v1",
        "input_sha256": ranking.digest(content),
        "prompt_version": ranking.VERSION,
        "prompt_sha256": ranking.digest(prompt),
        "model": "gpt-6-astra",
        "proposal_version": 1,
        "reranking_reason": None,
        "tie_groups": [],
        "ranking": [
            {
                "comment_id": cid,
                "rank": rank,
                "question_quality": "Clear independent concern.",
                "response_quality": "Substantive qualified rebuttal.",
                "question_anchors": [{"unit_id": cid, "quote": f"Exact source {cid}."}],
                "response_anchors": [{"unit_id": "r" + cid, "quote": f"Exact source r{cid}."}],
                "concerns": ["Retain visual target limitation."],
            }
            for rank, cid in enumerate(("a", "b"), 1)
        ],
    }
    return packet, proposal, content, prompt


def test_complete_advisory_proposal_and_stable_tie() -> None:
    """A complete anchored ordering accepts an explicitly stable-ID tie."""
    packet, proposal, content, prompt = fixture()
    proposal["tie_groups"] = [["a", "b"]]
    ranking.validate_proposal(packet, proposal, content, prompt)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "rank",
        "rewrite",
        "eligibility",
        "quote",
        "cross_context",
        "blank",
        "stale",
        "model",
        "tie",
        "rerank",
    ],
)
def test_invalid_advisory_proposals_fail(mutation: str) -> None:
    """Reject drops, decisions, unsupported anchors, stale lineage and unstable ties."""
    packet, proposal, content, prompt = fixture()
    first = proposal["ranking"][0]
    if mutation == "missing":
        proposal["ranking"].pop()
    elif mutation == "duplicate":
        proposal["ranking"][1]["comment_id"] = "a"
    elif mutation == "rank":
        first["rank"] = 2
    elif mutation == "rewrite":
        first["rewritten_question"] = "Invented rewrite"
    elif mutation == "eligibility":
        first["eligible"] = True
    elif mutation == "quote":
        first["response_anchors"][0]["quote"] = "Invented evidence"
    elif mutation == "cross_context":
        first["response_anchors"] = [{"unit_id": "rb", "quote": "Exact source rb."}]
    elif mutation == "blank":
        first["question_quality"] = "   "
    elif mutation == "stale":
        proposal["input_sha256"] = "0" * 64
    elif mutation == "model":
        proposal["model"] = "unspecified-model"
    elif mutation == "tie":
        proposal["tie_groups"] = [["b", "a"]]
    elif mutation == "rerank":
        proposal["proposal_version"] = 2
    with pytest.raises((ValueError, ValidationError)):
        ranking.validate_proposal(packet, proposal, content, prompt)


def test_independent_closure_rejects_missing_or_extra_unit() -> None:
    """Reachability respects directed cycles and never accepts a partial closure."""
    case = {"comment_id": "c", "direct_response_ids": ["r"], "context_unit_ids": ["c", "r", "g"]}
    edges = [
        {
            "source_unit_id": "r",
            "target_unit_id": "g",
            "relation_type": "response_general_response",
        },
        {
            "source_unit_id": "g",
            "target_unit_id": "r",
            "relation_type": "general_response_response",
        },
        {
            "source_unit_id": "g",
            "target_unit_id": "other",
            "relation_type": "general_response_comment",
        },
    ]
    edges.insert(
        0, {"source_unit_id": "c", "target_unit_id": "r", "relation_type": "comment_response"}
    )
    for number, edge in enumerate(edges):
        edge["edge_id"] = str(number)
    case["relationship_ids"] = ["0", "1", "2"]
    ranking.validate_closure(case, edges)
    with pytest.raises(ValueError, match="Direct response"):
        ranking.validate_closure({**case, "direct_response_ids": []}, edges)
    with pytest.raises(ValueError, match="relationship"):
        ranking.validate_closure({**case, "relationship_ids": ["0", "1"]}, edges)
    for ids in (["c", "r"], ["c", "r", "g", "other"]):
        with pytest.raises(ValueError, match="reachability"):
            ranking.validate_closure({**case, "context_unit_ids": ids}, edges)


def test_supplements_preserve_exact_page_text_and_membership() -> None:
    """Only exact on-page supplemental source slices may augment reading context."""
    unit = {"unit_id": "r", "source_pages": [2]}
    pages = {"p": {"physical_page": 2, "raw_text": "Body. 62 Footnote."}}
    row = {
        "unit_id": "r",
        "page_id": "p",
        "text_start": 6,
        "text_end": 18,
        "text": "62 Footnote.",
        "reason": "Omitted from accepted span",
    }
    ranking.validate_supplements([row], [unit], pages)
    for changed in (
        {**row, "text": "Made up"},
        {**row, "unit_id": "other"},
        {**row, "text_end": 99},
    ):
        with pytest.raises(ValueError):
            ranking.validate_supplements([changed], [unit], pages)


def test_publication_no_clobber_and_warning_preservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publication preserves all input warning data and rejects output mutations."""
    packet, proposal, content, prompt = fixture()
    monkeypatch.setattr(ranking, "replay", lambda packet: None)
    paths = {name: tmp_path / name for name in ("input", "proposal", "prompt", "spec")}
    paths["input"].write_bytes(content)
    paths["proposal"].write_bytes(ranking.encoded(proposal))
    paths["prompt"].write_bytes(prompt)
    paths["spec"].write_text("Shared v1 contract")
    output = tmp_path / "published"
    handoff = ranking.publish(
        paths["input"], paths["proposal"], paths["prompt"], paths["spec"], output
    )
    assert handoff["human_selection"] == "pending"
    saved = json.loads((output / "ranked_candidates.json").read_bytes())
    assert saved[0]["candidate"] == packet["candidates"][0]
    with pytest.raises(FileExistsError):
        ranking.publish(paths["input"], paths["proposal"], paths["prompt"], paths["spec"], output)
    original_manifest = (output / "manifest.json").read_bytes()
    original_completion = (output / "completion.json").read_bytes()
    manifest = json.loads(original_manifest)
    manifest["ranking_policy"] = "Rank determines eligibility"
    (output / "manifest.json").write_bytes(ranking.encoded(manifest))
    completion = json.loads(original_completion)
    completion["manifest_sha256"] = ranking.digest(ranking.encoded(manifest))
    (output / "completion.json").write_bytes(ranking.encoded(completion))
    with pytest.raises(ValueError, match="policy"):
        ranking.validate(output)
    (output / "manifest.json").write_bytes(original_manifest)
    (output / "completion.json").write_bytes(original_completion)
    (output / "unexpected").write_text("unmanaged")
    with pytest.raises(ValueError, match="closure"):
        ranking.validate(output)
    (output / "unexpected").unlink()
    altered = copy.deepcopy(saved)
    altered[0]["candidate"]["challenge_signals"] = []
    (output / "ranked_candidates.json").write_bytes(ranking.encoded(altered))
    with pytest.raises(ValueError, match="Checksum"):
        ranking.validate(output)
