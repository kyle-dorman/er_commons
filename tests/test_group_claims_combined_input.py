"""Production combined-input boundaries use synthetic data, never human labels."""

import copy
from pathlib import Path

import pytest

from er_commons.group_claims_combined_input import DEFERRED, verify_decisions, write_once
from er_commons.group_ranking import digest


def decision_fixture():
    """Create ordered synthetic question decisions with the required deferred set."""
    records = []
    for number in range(1, 58):
        cid = f"C{number:03d}"
        q = {"text": f"Question {number}?", "display_version": cid + "-v1"}
        q["text_sha256"] = digest(q["text"].encode())
        records.append(
            {
                "neutral_id": cid,
                "state": "deferred" if cid in DEFERRED else "approved",
                "frozen_question": q,
                "disposition": {
                    "decision": "approve",
                    "explicit_approval": True,
                    "approved_question": q["text"],
                    "approved_question_sha256": q["text_sha256"],
                    "display_version": q["display_version"],
                },
            }
        )
    result = {
        "status": "review_pass_complete",
        "approved": 53,
        "deferred": 4,
        "pending": 0,
        "selected": 57,
        "excluded": 0,
    }
    decisions = {
        "records": records,
        "status": "review_pass_complete",
        "deferred_neutral_ids": DEFERRED,
        "advancing_neutral_ids": [r["neutral_id"] for r in records if r["state"] == "approved"],
    }
    return result, decisions


def test_exact_decisions():
    """All ordered exact approvals are accepted without importing claim decisions."""
    verify_decisions(*decision_fixture())


@pytest.mark.parametrize(
    "mutation", ["order", "text", "approval", "deferred", "pending", "membership"]
)
def test_decision_corruption_fails(mutation):
    """Reject loss of order, frozen text, explicit decisions, or deferral boundaries."""
    result, decisions = copy.deepcopy(decision_fixture())
    if mutation == "order":
        decisions["records"].reverse()
    elif mutation == "text":
        decisions["records"][0]["frozen_question"]["text"] += " changed"
    elif mutation == "approval":
        decisions["records"][0]["disposition"]["explicit_approval"] = False
    elif mutation == "deferred":
        decisions["records"][12]["state"] = "approved"
    elif mutation == "pending":
        result["pending"] = 1
    else:
        decisions["advancing_neutral_ids"].pop()
    with pytest.raises(ValueError):
        verify_decisions(result, decisions)


def test_restart_never_overwrites(tmp_path: Path):
    """Identical checkpoints resume; a changed record cannot clobber saved work."""
    path = tmp_path / "case" / "packet.json"
    expected = write_once(path, {"source": "exact"})
    assert write_once(path, {"source": "exact"}) == expected
    with pytest.raises(ValueError, match="Existing checkpoint differs"):
        write_once(path, {"source": "changed"})
    assert digest(path.read_bytes()) == expected["sha256"]
