"""Synthetic continuation classification preserves attempts and active clocks."""

from pathlib import Path
from typing import Any

import pytest

from er_commons import minimax_continue as run
from er_commons.target_generation import save


def setup(
    directory: Path, status: str, *, attempted: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one invented target result and an optional settled wire reservation."""
    save(
        directory / "generation/result.json", {"status": status, "generation_calls": int(attempted)}
    )
    save(directory / "judgments.json", [])
    row = {
        "run_id": "slot",
        "status": "generation_failed" if status == "execution_error" else "evaluation_incomplete",
    }
    request = {"key": "slot/target/generation", "kind": "generation", "slot_id": "slot"}
    verified = {
        "requests": [request] if attempted else [],
        "settlements": {request["key"]: {"finished_at": 100.0}},
        "source_end": 500.0,
    }
    return row, verified


@pytest.mark.parametrize("status", ["execution_error", "invalid_output"])
def test_attempted_generation_never_replaced(tmp_path: Path, status: str) -> None:
    """429/error attempts and malformed outputs remain preserved without selection."""
    row, verified = setup(tmp_path, status, attempted=True)
    assert run.classify_slot(tmp_path, row, verified) == {"action": "preserve"}


def test_verified_no_wire_failure_can_generate(tmp_path: Path) -> None:
    """Only absence of every reservation permits a fresh generation."""
    row, verified = setup(tmp_path, "execution_error", attempted=False)
    assert run.classify_slot(tmp_path, row, verified)["action"] == "generate"
    verified["requests"] = [{"key": "count-only", "kind": "count", "slot_id": "slot"}]
    with pytest.raises(ValueError, match="no-wire"):
        run.classify_slot(tmp_path, row, verified)


def test_partial_fallback_clock_is_not_reset(tmp_path: Path) -> None:
    """A valid target without judge calls retains elapsed time from generation settlement."""
    row, verified = setup(tmp_path, "valid", attempted=True)
    state = run.classify_slot(tmp_path, row, verified)
    assert state["action"] == "evaluate"
    assert state["original_evaluation_started_at"] == 100
    assert state["evaluation_elapsed_seconds"] == 400


def test_only_zero_wire_judge_failures_are_discarded(tmp_path: Path) -> None:
    """A reserved judge attempt can never be silently reissued after an amendment."""
    row, verified = setup(tmp_path, "valid", attempted=True)
    (tmp_path / "judgments.json").unlink()
    judgment = {
        "sample_id": "judge",
        "status": "execution_error",
        "judge_calls": 0,
        "count_calls": 0,
    }
    save(tmp_path / "judgments.json", [judgment])
    assert run.classify_slot(tmp_path, row, verified)["discard_judgments"] == ["judge"]
    verified["requests"].append({"key": "slot/judge/judge", "slot_id": "slot", "kind": "judge"})
    assert run.classify_slot(tmp_path, row, verified) == {"action": "preserve"}


def test_partial_earliest_judge_clock_and_count_join(tmp_path: Path) -> None:
    """Native judge/count linkage must remain one-to-one and earlier elapsed survives."""
    row, verified = setup(tmp_path, "valid", attempted=True)
    verified["requests"] += [
        {"key": "slot/j/judge", "slot_id": "slot", "kind": "judge", "evaluation_started_at": 125.0},
        {
            "key": "slot/j/count",
            "slot_id": "slot",
            "kind": "count",
            "parent_key": "slot/j/judge",
            "evaluation_started_at": 120.0,
        },
    ]
    state = run.classify_slot(tmp_path, row, verified)
    assert state["original_evaluation_started_at"] == 120
    assert state["evaluation_elapsed_seconds"] == 380
    verified["requests"].pop()
    with pytest.raises(ValueError, match="uncounted"):
        run.classify_slot(tmp_path, row, verified)


def test_archive_cannot_shadow_changed_active_reservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A forged matching history copy cannot conceal tampered active ledger bytes."""
    from er_commons.artifact_io import artifact_inventory

    source, output = tmp_path / "source", tmp_path / "output"
    source.mkdir()
    output.mkdir()
    save(source / "ledger/example.reservation.json", {"cost": "original"})
    save(source / "completion.json", artifact_inventory(source, {"completion.json"}))
    save(output / "ledger/example.reservation.json", {"cost": "changed"})
    save(output / "ancestor_history/ledger/example.reservation.json", {"cost": "original"})
    claim = {"namespace": "original"}
    save(tmp_path / run.minimax_run.ROOT / "paid_run_claim.json", claim)
    save(
        output / "continuation_preflight.json",
        {
            "source": str(source),
            "source_completion_sha256": "synthetic",
            "implementation_sha256": {},
            "evaluation_seconds": 5400,
            "workers": 1,
            "partial_first": True,
            "exclude_sealed_pause": True,
            "pause_authorization": "yes exclude and continue",
            "original_paid_claim": claim,
        },
    )
    monkeypatch.setattr(run, "verify_source", lambda *_: {})
    monkeypatch.setattr(run.run, "implementation", lambda *_: {})
    with pytest.raises(ValueError, match="Copied ancestor bytes changed"):
        run.verify_preflight(tmp_path, output)


def test_dispatch_partial_first_preserves_clocks_generations_and_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise coordinator archiving and ordering with no provider construction or calls."""
    import asyncio

    from er_commons.artifact_io import stable_json_sha256

    output = tmp_path / run.minimax_run.ROOT / "continuation"
    output.mkdir(parents=True)
    slots = [
        {"model": "minimax", "case_id": case, "repeat": 1}
        for case in ("fresh", "preserved", "partial1", "partial2")
    ]
    preflight = {
        "slots": slots,
        "cumulative_basis": {
            "cap_usd": "8",
            "request_caps": {"generation": 90, "judge": 1354, "count": 1354},
        },
    }
    save(output / "preflight.json", preflight)
    save(output / "inputs.json", {s["case_id"]: {} for s in slots})
    states = {}
    for slot in slots:
        identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
        directory = output / "observations/minimax_repeat1" / slot["case_id"]
        save(directory / "manifest.json", identity)
        save(directory / "summary.json", {**identity, "status": "old"})
        for name in ("report.json", "judgments.json", "completion.json"):
            save(directory / name, {})
        if slot["case_id"].startswith("partial"):
            elapsed = 400 if slot["case_id"] == "partial1" else 300
            states[identity["run_id"]] = {
                "action": "evaluate",
                "generation": {"saved": slot["case_id"]},
                "judgments": [],
                "discard_judgments": ["no_wire"],
                "evaluation_elapsed_seconds": elapsed,
            }
            save(directory / "judgments/no_wire/judgment.json", {"judge_calls": 0})
        else:
            states[identity["run_id"]] = {
                "action": "preserve" if slot["case_id"] == "preserved" else "generate",
                "generation": None,
                "judgments": [],
            }
    manifest = {"source_completion_sha256": "invented-seal", "slots": states}
    save(output / "continuation_preflight.json", manifest)
    monkeypatch.setattr(run, "verify_preflight", lambda *_: manifest)
    clock = {"now": 1000.0}
    monkeypatch.setattr(run.time, "time", lambda: clock["now"])
    calls = []

    async def fake_slot(slot, frozen, destination, data, dispatcher, state, **kwargs):
        """Record orchestration only while simulating time spent processing the first partial."""
        assert frozen == preflight
        assert destination == output
        assert dispatcher.evaluation_seconds == 5400
        calls.append((slot["case_id"], state))
        clock["now"] += 100
        return {
            **slot,
            "run_id": stable_json_sha256({"slot": slot, "preflight": preflight}),
            "status": "fixture_completed",
        }

    monkeypatch.setattr(run.run, "run_slot", fake_slot)
    result = asyncio.run(run.dispatch(tmp_path, output))
    assert result["slots"] == 4
    assert [case for case, _ in calls] == ["partial1", "partial2", "fresh"]
    assert calls[0][1]["evaluation_started_at"] == 600
    assert calls[1][1]["evaluation_started_at"] == 700
    assert calls[0][1]["generation"] == {"saved": "partial1"}
    assert calls[1][1]["generation"] == {"saved": "partial2"}
    assert calls[2][1]["generation"] is None
    rows = run.run.read(output / "slot_results.json")
    assert [row["case_id"] for row in rows] == [slot["case_id"] for slot in slots]
    assert rows[1]["status"] == "old"
    assert (output / "ancestor_history/observations/minimax_repeat1/fresh/summary.json").exists()
    assert (
        output
        / "ancestor_history/observations/minimax_repeat1/partial1/judgments/no_wire/judgment.json"
    ).exists()
    with pytest.raises(ValueError, match="sealed"):
        asyncio.run(run.dispatch(tmp_path, output))
    other = output.with_name("forked_budget")
    other.mkdir()
    save(other / "continuation_preflight.json", manifest)
    with pytest.raises(FileExistsError):
        asyncio.run(run.dispatch(tmp_path, other))
