"""Offline invented Task 13 orchestration and pure evaluation boundary checks."""

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from test_development_evaluation import fixture

from er_commons import development_evaluation as evaluation
from er_commons import locked_run as run
from er_commons.artifact_io import sha256_bytes, stable_json_sha256
from er_commons.locked_dispatch import LockedDispatcher, Request
from er_commons.locked_inputs import planned_slots
from er_commons.target_generation import save


def setup_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, Any]]:
    """Create an invented complete roster without loading actual benchmark content."""
    output = tmp_path / "pipelines/brisbane_baylands/task_13/fixture"
    output.mkdir(parents=True)
    cases = [f"C{i:03}" for i in range(30)]
    preflight = {"slots": planned_slots(cases), "pricing": {}}
    save(output / "preflight.json", preflight)
    save(output / "inputs.json", {case: {} for case in cases})
    save(output / "frozen_configuration.json", {})
    monkeypatch.setattr(run, "verify_preflight", lambda *_: preflight)
    return output, preflight


def test_global_stop_preserves_all_180_slots_without_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, preflight = setup_run(tmp_path, monkeypatch)

    class StoppedDispatcher(LockedDispatcher):
        """Start with a persisted stop, exercising real slot publication."""

        def __init__(self, path: Path) -> None:
            super().__init__(path)
            self.stop("fixture stop before first call")

    monkeypatch.setattr(run, "LockedDispatcher", StoppedDispatcher)
    monkeypatch.setattr(run.locked_provider, "generate_one", lambda *_: pytest.fail("paid call"))
    result = asyncio.run(run.dispatch(tmp_path, output))
    rows = json.loads((output / "slot_results.json").read_text())
    assert result["slots"] == len(rows) == 180
    assert all(row["status"] == "not_dispatched" for row in rows)
    assert [(r["model"], r["case_id"], r["repeat"]) for r in rows] == [
        (r["model"], r["case_id"], r["repeat"]) for r in preflight["slots"]
    ]
    assert result["accounting"]["counts"] == {"generation": 0, "judge": 0, "count": 0}
    assert (output / "completion.json").exists()


def test_unknown_billing_blocks_before_provider_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = {"slots": [], "provenance": [], "inputs": {}, "frozen_configuration": {}}
    preflight = {
        **loaded,
        "implementation_sha256": {},
        "source_sha256": stable_json_sha256({}),
        "pricing": {
            "openai": {"verified": False, "count_max_usd": None},
            "anthropic": {"verified": True, "count_max_usd": 0},
        },
    }
    save(tmp_path / "preflight.json", preflight)
    save(tmp_path / "inputs.json", {})
    save(tmp_path / "frozen_configuration.json", {})
    monkeypatch.setattr(run, "implementation", lambda *_: {})
    monkeypatch.setattr(run, "load_locked", lambda *_: loaded)
    monkeypatch.setattr(run.locked_provider, "generate_one", lambda *_: pytest.fail("paid call"))
    with pytest.raises(ValueError, match="verified upper bound"):
        run.verify_preflight(tmp_path, tmp_path)
    assert not (tmp_path / "ledger").exists()


def test_worker_failure_drains_inflight_before_unlock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, _ = setup_run(tmp_path, monkeypatch)
    calls = 0
    settled = []

    async def slot(
        slot: dict[str, Any],
        preflight: dict[str, Any],
        output: Path,
        data: dict[str, Any],
        dispatcher: LockedDispatcher,
    ) -> dict[str, Any]:
        """Keep one real gate admission active while another worker fails."""
        nonlocal calls
        calls += 1
        if calls == 1:

            async def operation() -> tuple[None, Decimal]:
                await asyncio.sleep(0.03)
                settled.append(True)
                return None, Decimal("0.001")

            await dispatcher.invoke_async(
                Request("first", "first", "generation", Decimal("0.01"), 10, 10), operation
            )
        elif calls == 2:
            await asyncio.sleep(0.001)
            raise ValueError("invented integrity error")
        return {**slot, "status": "not_dispatched"}

    monkeypatch.setattr(run, "run_slot", slot)
    with pytest.raises(RuntimeError, match="Worker failed"):
        asyncio.run(asyncio.wait_for(run.dispatch(tmp_path, output), timeout=2))
    assert settled == [True]
    with LockedDispatcher(output / "ledger") as dispatcher:
        assert dispatcher.liability_usd == Decimal("0.001")
    assert not (output / "completion.json").exists()


def test_malformed_test_answer_plan_is_preserved(tmp_path: Path) -> None:
    _, identity, record, mapping, receipt, reference = fixture()
    mapping["split"] = "test"
    raw = b"not JSON"
    identity.pop("candidate_id")
    identity["candidate_sha256"] = sha256_bytes(raw)
    identity["candidate_id"] = stable_json_sha256(identity)
    generation = {**identity, "provider": "openai"}
    save(tmp_path / "native_request.json", receipt)
    save(tmp_path / "delivery_projection.json", receipt)
    (tmp_path / "raw_output.txt").write_bytes(raw)
    plan = run.prepare_plan(
        {"record": record, "mapping": mapping, "reference": reference}, generation, tmp_path
    )
    assert plan["automatic"]["schema"] == "invalid"
    assert plan["identity"]["candidate_sha256"] == sha256_bytes(raw)
    assert plan["items"] == []


def test_default_evaluator_rejects_test_but_explicit_test_preserves_scoring() -> None:
    values = list(fixture())
    expected = evaluation.prepare_candidate(*values)
    values[3]["split"] = "test"
    with pytest.raises(ValueError, match="mapping"):
        evaluation.prepare_candidate(*values)
    actual = evaluation.prepare_candidate(*values, expected_split="test")
    assert actual["items"] == expected["items"]
    assert actual["automatic"] == expected["automatic"]


def test_partial_slot_resume_never_replays(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, preflight = setup_run(tmp_path, monkeypatch)
    slot = preflight["slots"][0]
    partial = output / "observations" / f"{slot['model']}_repeat{slot['repeat']}" / slot["case_id"]
    partial.mkdir(parents=True)
    (partial / "saved_unknown_response.txt").write_text("Preserve me")
    monkeypatch.setattr(run.locked_provider, "generate_one", lambda *_: pytest.fail("replayed"))
    with LockedDispatcher(output / "ledger") as dispatcher:
        result = asyncio.run(run.run_slot(slot, preflight, output, {}, dispatcher))
    assert result["status"] == "interrupted_uncertain"
    assert (partial / "saved_unknown_response.txt").read_text() == "Preserve me"


@pytest.mark.parametrize("rate_limited", [True, False])
def test_generation_rate_limit_keeps_next_slot_eligible_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rate_limited: bool
) -> None:
    """HTTP 429 preserves its failed slot and lowers concurrency for untouched work."""
    output, preflight = setup_run(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(run, "arm_prompt", lambda *_: "Invented prompt")

    async def generation(*args: Any) -> dict[str, Any]:
        identity, dispatcher = args[5], args[6]
        calls.append(identity["run_id"])
        if rate_limited:
            dispatcher.rate_limit()
        return {
            "status": "execution_error",
            "rate_limited": rate_limited,
            "generation_calls": 1,
            "count_calls": 1,
        }

    monkeypatch.setattr(run.locked_provider, "generate_one", generation)

    async def exercise() -> None:
        with LockedDispatcher(output / "ledger") as dispatcher:
            first, second = preflight["slots"][:2]
            failed = await run.run_slot(first, preflight, output, {"record": {}}, dispatcher)
            assert failed["status"] == "generation_failed"
            assert bool(dispatcher.snapshot()["stop_reason"]) is not rate_limited
            if rate_limited:
                assert dispatcher.concurrency == 5
            # A sealed failed slot is never attempted again.
            await run.run_slot(first, preflight, output, {"record": {}}, dispatcher)
            await run.run_slot(second, preflight, output, {"record": {}}, dispatcher)
            assert len(calls) == (2 if rate_limited else 1)
            assert len(calls) == len(set(calls))

    asyncio.run(exercise())
