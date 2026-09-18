"""First byte seals must match reviewed data and retained supervised completion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory import release_execution, release_workflow
from er_commons.response_inventory.release_storage import (
    digest,
    encode,
    publish_container,
    read_container,
)


def test_first_seal_checks_same_consumed_json_bytes(tmp_path: Path) -> None:
    """Same-size content drift after loading cannot become the first publication seal."""
    path = tmp_path / "task05/working/05d/revision/inventory/source_records.jsonl"
    path.parent.mkdir(parents=True)
    original = [{"record_type": "page", "raw_text": "original"}]
    path.write_bytes(b"".join(encode(row) for row in original))
    component = {
        "role": "source_records",
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": None,
        "size_bytes": path.stat().st_size,
        "record_semantic_digest": canonical_json_sha256(original),
        "check_mode": "accepted_semantic_digest_and_size",
    }
    sealed = release_workflow._seal_components([component], tmp_path)
    assert sealed[0]["sha256"] == digest(path.read_bytes())
    path.write_bytes(encode({"record_type": "page", "raw_text": "modified"}))
    assert path.stat().st_size == component["size_bytes"]
    with pytest.raises(ValueError, match="changed between semantic validation and first seal"):
        release_workflow._seal_components([component], tmp_path)


def test_self_consistent_completion_cannot_replace_supervised_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recomputed valid manifest still fails against independently retained worker output."""
    run = release_workflow.ReleaseRun(
        {}, "plan05hv1-" + "a" * 64, tmp_path / "repo", tmp_path, tmp_path / "working/05h", 1
    )
    original = publish_container(
        tmp_path / "original",
        {"inventory/components.json": encode([{"sha256": "a" * 64}])},
        plan_id=run.plan_id,
        semantic_digest="b" * 64,
        status="complete_with_limitations",
    )
    forged = publish_container(
        tmp_path / "forged",
        {"inventory/components.json": encode([{"sha256": "0" * 64}])},
        plan_id=run.plan_id,
        semantic_digest="c" * 64,
        status="complete_with_limitations",
    )
    read_container(tmp_path / "forged", plan_id=run.plan_id)
    log = (
        run.root.parent
        / "05h_execution_attempts"
        / run.plan_id
        / "attempt-001-finalize/command.log"
    )
    log.parent.mkdir(parents=True)
    log.write_bytes(encode({"completion": original}))
    monkeypatch.setattr(
        release_execution, "verify_terminal_execution", lambda *args: {"status": "succeeded"}
    )
    release_execution.verify_finalized_result(run, original)
    with pytest.raises(ValueError, match="differs from supervised worker result"):
        release_execution.verify_finalized_result(run, forged)


def test_identical_ledger_repeats_and_order_do_not_change_quality_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Append-only ledger repetition produces one sorted immutable decision payload."""
    decisions = [{"decision_id": "b", "value": 2}, {"decision_id": "a", "value": 1}]
    normalized = release_workflow.canonical_decisions([*decisions, decisions[0]])
    assert [row["decision_id"] for row in normalized] == ["a", "b"]
    monkeypatch.setattr(
        release_workflow, "_base_payloads", lambda *args: {"records/base.json": b"{}\n"}
    )
    unused = cast(Any, None)
    first = release_workflow.review_payload_digest(unused, unused, {}, decisions, {})
    second = release_workflow.review_payload_digest(
        unused, unused, {}, [decisions[1], decisions[0], decisions[1]], {}
    )
    assert first == second
    assert json.loads(encode(normalized))[0]["decision_id"] == "a"


def test_normalization_rejects_conflicting_same_id_before_resume() -> None:
    """Resume must not hide an earlier conflicting ledger row behind last-write-wins."""
    with pytest.raises(ValueError, match="conflict"):
        release_workflow.canonical_decisions(
            [
                {"decision_id": "d1", "disposition": "correction_required"},
                {"decision_id": "d1", "disposition": "confirmed_composition"},
            ]
        )
