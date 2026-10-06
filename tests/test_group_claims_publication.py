"""Synthetic negative gates for completion-last Task08D publication."""

import copy
import json

import pytest
from test_group_claims_chat import fixture

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_batch import assemble, publish


def saved(path, value):
    """Write one synthetic deterministic artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def preparation(root):
    """Invent 53 independent cases without any production data or decisions."""
    queue, _ = fixture()
    ids = [f"S{i:03}" for i in range(1, 54)]
    sources = []
    for cid in ids:
        packet = copy.deepcopy(queue["packet"])
        source = packet["cases"][0]
        source["case_id"] = source["question"]["neutral_id"] = cid
        inventory = copy.deepcopy(queue["inventory"])
        inventory["cases"][0]["case_id"] = cid
        inventory["packet_sha256"] = digest(encoded(packet))
        proposal = copy.deepcopy(queue["proposal"])
        proposal["cases"][0]["case_id"] = cid
        proposal["packet_sha256"] = digest(encoded(packet))
        proposal["inventory_sha256"] = digest(encoded(inventory))
        saved(root / f"input/cases/{cid}/packet.json", packet)
        directory = root / "cases" / cid
        for name, value in (
            ("model_input", packet),
            ("inventory", inventory),
            ("proposal", proposal),
        ):
            saved(directory / f"{name}.json", value)
        saved(
            directory / "invocation.json",
            {
                "actual_model": "gpt-6-astra",
                "case_id": cid,
                "worker": "synthetic-author",
                "human_decisions_generated": False,
                "files": {
                    name: digest((directory / name).read_bytes())
                    for name in ("model_input.json", "inventory.json", "proposal.json")
                },
            },
        )
        sources.append(source)
    saved(root / "input/packet.json", {**queue["packet"], "cases": sources})
    saved(
        root / "input/context_notes.json",
        {
            "all_57_decisions": {"advancing_neutral_ids": ids},
            "deferred_ids": ["C013", "C023", "C038", "C057"],
            "scope_hold": "Synthetic unresolved reconciliation retained",
        },
    )
    output = root / "assembled"
    assemble(root, output)
    review = root / "review/review.json"
    saved(
        review,
        {
            "reviewer": "synthetic-independent-reviewer",
            "cases": [
                {
                    "case_id": cid,
                    "status": "pass",
                    **{
                        f"{kind}_sha256": digest((root / f"cases/{cid}/{kind}.json").read_bytes())
                        for kind in ("inventory", "proposal")
                    },
                }
                for cid in ids
            ],
        },
    )
    validation = root / "validation.json"
    saved(validation, {"ready": True, "queue_sha256": digest((output / "queue.json").read_bytes())})
    for path in (
        "input/manifest.json",
        "preservation_baseline.json",
    ):
        saved(root / path, {"synthetic": True})
    saved(
        root / "review/independent_source_check.json",
        {"valid": True, "input_sha256": digest((root / "input/packet.json").read_bytes())},
    )
    (output / "RESUME.md").write_text("Synthetic review resume instructions.\n")
    return output, review, validation


@pytest.mark.parametrize(
    "fault",
    [
        "stale_assembly",
        "inventory_hash",
        "self_review",
        "unfinished",
        "unreviewed",
        "context_drift",
    ],
)
def test_publication_rejects_unqualified_or_stale_inputs(tmp_path, fault):
    output, review, validation = preparation(tmp_path)
    record = json.loads(review.read_bytes())
    if fault == "stale_assembly":
        path = tmp_path / "cases/S001/proposal.json"
        proposal = json.loads(path.read_bytes())
        proposal["cases"][0]["claims"][0]["rationale"] += " Revised after assembly."
        saved(path, proposal)
        record["cases"][0]["proposal_sha256"] = digest(path.read_bytes())
        saved(review, record)
    elif fault == "inventory_hash":
        record["cases"][0]["inventory_sha256"] = "0" * 64
        saved(review, record)
    elif fault == "self_review":
        record["reviewer"] = "synthetic-author"
        saved(review, record)
    elif fault == "unfinished":
        saved(validation, {"ready": False})
    elif fault == "unreviewed":
        record["cases"].pop()
        saved(review, record)
    else:
        path = tmp_path / "input/context_notes.json"
        context = json.loads(path.read_bytes())
        context["scope_hold"] = "New unresolved scope requirement"
        saved(path, context)
    with pytest.raises(ValueError):
        publish(tmp_path, output, [review], validation)
    assert not (output / "handoff.json").exists()


def test_publication_seals_blank_synthetic_queue(tmp_path):
    output, review, validation = preparation(tmp_path)
    handoff = publish(tmp_path, output, [review], validation)
    assert handoff["status"] == "prepared, awaiting human review"
    assert handoff["case_count"] == 53
    assert handoff["human_decisions"] == 0
    assert handoff["advancing_claims"] == []
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert all(row["sha256"] for row in manifest["files"])
