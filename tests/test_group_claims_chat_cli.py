"""Exercise the production persisted journal path, cursor and export."""

import json
import subprocess
import sys

import pytest
from test_group_claims_chat import approve, conclude, fixture

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_batch import reference
from er_commons.group_claims_chat import append_event, replay
from er_commons.group_claims_chat_cli import load_journal, next_review


def test_real_cli_resume_export_and_blank_gate(tmp_path):
    queue, journal = fixture()
    qp = tmp_path / "queue.json"
    qp.write_bytes(encoded(queue))
    ref = tmp_path / "queue_ref.json"
    ref.write_bytes(encoded(reference(qp)))
    jp = tmp_path / "events.jsonl"
    base = [sys.executable, "-m", "er_commons.group_claims_chat_cli"]
    args = ["--queue-reference", str(ref), "--journal", str(jp)]
    first = subprocess.run(base + ["next", *args], capture_output=True, check=True)
    assert json.loads(first.stdout)["claim_id"] == "A001"
    assert not jp.exists()
    failed = subprocess.run(
        base + ["export", *args, "--output", str(tmp_path / "no.json")], capture_output=True
    )
    assert failed.returncode != 0 and not (tmp_path / "no.json").exists()
    completed = conclude(queue, approve(queue, approve(queue, journal), "A002"))
    for row in completed["events"]:
        event = {
            k: v for k, v in row.items() if k not in {"sequence", "previous_sha256", "event_sha256"}
        }
        ep = tmp_path / "event.json"
        ep.write_bytes(encoded(event))
        subprocess.run(
            base + ["record", *args, "--event", str(ep)], capture_output=True, check=True
        )
    saved = load_journal(jp, queue)
    assert saved == completed
    assert next_review(queue, replay(queue, saved))["kind"] == "complete"
    out = tmp_path / "export.json"
    subprocess.run(base + ["export", *args, "--output", str(out)], capture_output=True, check=True)
    first_hash = digest(out.read_bytes())
    subprocess.run(base + ["export", *args, "--output", str(out)], capture_output=True, check=True)
    assert digest(out.read_bytes()) == first_hash
    assert len(json.loads(out.read_bytes())["advancing"]) == 2


def test_cursor_requires_case_disposition_and_rejects_torn_records(tmp_path):
    queue, journal = fixture()
    journal = approve(queue, approve(queue, journal), "A002")
    assert next_review(queue, replay(queue, journal))["kind"] == "case_summary"
    path = tmp_path / "torn.jsonl"
    path.write_text('{"kind":')
    with pytest.raises(ValueError, match="Incomplete"):
        load_journal(path, queue)
    event = {
        "kind": "discussion",
        "case_id": "S001",
        "feedback": "question",
        "actor": "synthetic",
        "chat_reference": "fixture",
        "timestamp": "2026-10-05T00:00:00Z",
    }
    with pytest.raises(ValueError):
        append_event(path, queue, event)
    assert path.read_text() == '{"kind":'


def test_cursor_does_not_hide_missing_claim_decisions():
    queue, journal = fixture()
    journal = conclude(queue, journal)
    current = next_review(queue, replay(queue, journal))
    assert current["kind"] == "claim"
    assert current["claim_id"] == "A001"
