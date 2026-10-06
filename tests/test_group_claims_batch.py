"""Verify assembly retains source provenance and never imports human approvals."""

import json

import pytest
from test_group_claims_chat import fixture

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_batch import assemble


def prepared_root(root):
    """Build separate synthetic model receipts with a carried reconciliation hold."""
    queue, _ = fixture()
    inp = root / "input"
    case = root / "cases/S001"
    (inp / "cases/S001").mkdir(parents=True)
    case.mkdir(parents=True)
    for p in [inp / "packet.json", inp / "cases/S001/packet.json", case / "model_input.json"]:
        p.write_bytes(encoded(queue["packet"]))
    (inp / "context_notes.json").write_bytes(
        encoded({"hold": "synthetic historical reconciliation"})
    )
    for name in ["inventory", "proposal"]:
        (case / f"{name}.json").write_bytes(encoded(queue[name]))
    (case / "invocation.json").write_bytes(
        encoded(
            {
                "actual_model": "gpt-6-astra",
                "case_id": "S001",
                "worker": "synthetic",
                "human_decisions_generated": False,
                "files": {
                    n: digest((case / n).read_bytes())
                    for n in ["model_input.json", "inventory.json", "proposal.json"]
                },
            }
        )
    )
    return case


def test_assembly_carries_holds_and_is_repeatable(tmp_path):
    prepared_root(tmp_path)
    output = tmp_path / "assembled"
    first = assemble(tmp_path, output)
    assert first == assemble(tmp_path, output)
    queue = json.loads((output / "queue.json").read_bytes())
    assert queue["context_notes"]["hold"] == "synthetic historical reconciliation"
    assert all(c["decision"] is None for c in queue["cards"])
    assert json.loads((output / "journal_initial.json").read_bytes())["events"] == []
    assert first["claim_count"] == 2


@pytest.mark.parametrize("fault", ["invocation", "model_input"])
def test_changed_model_receipts_block_assembly(tmp_path, fault):
    case = prepared_root(tmp_path)
    if fault == "model_input":
        (case / "model_input.json").write_text("{}")
    else:
        d = json.loads((case / "invocation.json").read_bytes())
        d["actual_model"] = "unverified"
        (case / "invocation.json").write_bytes(encoded(d))
    with pytest.raises(ValueError):
        assemble(tmp_path, tmp_path / "assembled")
    assert not (tmp_path / "assembled/assembly.json").exists()
