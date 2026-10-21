"""Invented fixtures exercise independent roster and cumulative admission limits."""

import asyncio
from decimal import Decimal
from pathlib import Path

import pytest

from er_commons import minimax_run as run
from er_commons.locked_dispatch import DispatchStopped, Request


def test_roster_is_exactly_ninety_without_original_conditions() -> None:
    """Keep every question and repeat exactly once in the separate condition."""
    rows = run.planned_slots([f"fixture-{i}" for i in range(30)])
    assert len(rows) == 90
    assert len({(row["case_id"], row["repeat"]) for row in rows}) == 90
    assert {row["model"] for row in rows} == {"minimax"}
    with pytest.raises(ValueError, match="thirty"):
        run.planned_slots(["duplicate"] * 30)


def test_tighter_call_ceiling_is_durable_and_atomic(tmp_path: Path) -> None:
    """Concurrent requests cannot cross the remaining cumulative judge allowance."""
    basis = {"cap_usd": "8.995824450", "request_caps": {"generation": 90, "judge": 1, "count": 1}}
    attempts = []

    async def exercise() -> None:
        """Launch two competing requests against one remaining judge slot."""
        with run.ComparisonDispatcher(tmp_path / "ledger", basis) as dispatcher:

            async def operation() -> tuple[str, Decimal]:
                """Record actual wire-equivalent admission, then yield."""
                attempts.append(True)
                await asyncio.sleep(0)
                return "ok", Decimal("0.01")

            outcomes = await asyncio.gather(
                *[
                    dispatcher.invoke_async(
                        Request(
                            key=f"judge-{i}",
                            slot_id=f"slot-{i}",
                            kind="judge",
                            maximum_cost_usd=Decimal("0.02"),
                            input_tokens=1,
                            output_tokens=1,
                        ),
                        operation,
                    )
                    for i in range(2)
                ],
                return_exceptions=True,
            )
            assert sum(isinstance(value, DispatchStopped) for value in outcomes) == 1
            assert dispatcher.snapshot()["counts"]["judge"] == 1
        with run.ComparisonDispatcher(tmp_path / "ledger", basis) as resumed:
            assert resumed.snapshot()["counts"]["judge"] == 1
            assert resumed.snapshot()["stop_reason"]

    asyncio.run(exercise())
    assert len(attempts) == 1


def test_changed_cumulative_policy_cannot_resume(tmp_path: Path) -> None:
    """A fresh process cannot increase the allowance or call budget."""
    basis = {"cap_usd": "8", "request_caps": {"generation": 90, "judge": 1, "count": 1}}
    with run.ComparisonDispatcher(tmp_path, basis):
        pass
    changed = {**basis, "request_caps": {"generation": 90, "judge": 2, "count": 1}}
    with pytest.raises(ValueError, match="policy changed"):
        run.ComparisonDispatcher(tmp_path, changed)


def test_stop_preserves_all_ninety_slots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A global stop still publishes every planned answer without remote calls."""
    from er_commons import minimax_provider
    from er_commons.target_generation import save

    output = tmp_path / run.ROOT / "invented"
    output.mkdir(parents=True)
    cases = [f"fixture-{i}" for i in range(30)]
    preflight = {
        "slots": run.planned_slots(cases),
        "cumulative_basis": {
            "cap_usd": "8.995824450",
            "request_caps": {"generation": 90, "judge": 1354, "count": 1354},
        },
    }
    save(output / "preflight.json", preflight)
    save(output / "inputs.json", {case: {} for case in cases})
    save(output / "frozen_configuration.json", {})
    monkeypatch.setattr(run, "verify_preflight", lambda *_: preflight)
    monkeypatch.setattr(minimax_provider, "generate_one", lambda *_: pytest.fail("remote call"))

    class StoppedDispatcher(run.ComparisonDispatcher):
        """Stop before any remote admission while exercising real slot handling."""

        def __init__(self, directory: Path, basis: dict) -> None:
            super().__init__(directory, basis)
            self.stop("invented pre-dispatch stop")

    monkeypatch.setattr(run, "ComparisonDispatcher", StoppedDispatcher)
    result = asyncio.run(run.dispatch(tmp_path, output))
    rows = run.locked_run.read(output / "slot_results.json")
    assert result["slots"] == len(rows) == 90
    assert {row["status"] for row in rows} == {"not_dispatched"}
    assert result["accounting"]["counts"] == {"generation": 0, "judge": 0, "count": 0}
    assert (output / "completion.json").exists()
    with pytest.raises(ValueError, match="sealed"):
        asyncio.run(run.dispatch(tmp_path, output))


def test_saturated_sync_waiters_recheck_remaining_cap(tmp_path: Path) -> None:
    """Condition waiters cannot reuse stale admission counts after capacity returns."""
    import threading
    from concurrent.futures import ThreadPoolExecutor

    basis = {"cap_usd": "8", "request_caps": {"generation": 90, "judge": 2, "count": 2}}
    entered = threading.Event()
    release = threading.Event()
    attempts: list[int] = []
    with run.ComparisonDispatcher(tmp_path, basis) as dispatcher:
        dispatcher.concurrency = 1
        waiting = threading.Event()
        waiting_count = 0
        original_wait = dispatcher._condition.wait

        def observe_wait(timeout: float | None = None) -> bool:
            """Release the holder only after both contenders actually enter wait."""
            nonlocal waiting_count
            waiting_count += 1
            if waiting_count >= 2:
                waiting.set()
            return original_wait(timeout)

        dispatcher._condition.wait = observe_wait

        def invoke(index: int) -> object:
            """Hold the first slot while two contenders wait for the same capacity."""

            def operation() -> tuple[str, Decimal]:
                """Expose wire-equivalent admissions and hold only the first."""
                attempts.append(index)
                if index == 0:
                    entered.set()
                    assert release.wait(timeout=5)
                return "ok", Decimal("0")

            request = Request(
                key=f"request-{index}",
                slot_id=f"slot-{index}",
                kind="judge",
                maximum_cost_usd=Decimal("0.01"),
                input_tokens=1,
                output_tokens=1,
            )
            try:
                return dispatcher.invoke(request, operation)
            except DispatchStopped as error:
                return error

        with ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(invoke, 0)
            assert entered.wait(timeout=5)
            rest = [pool.submit(invoke, index) for index in (1, 2)]
            assert waiting.wait(timeout=5)
            release.set()
            outcomes = [first.result(), *(future.result() for future in rest)]
        assert len(attempts) == 2
        assert sum(isinstance(result, DispatchStopped) for result in outcomes) == 1


def test_serialized_input_preflight_checks_inclusive_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check UTF-8 serialized payload bytes at the exact admission boundary."""
    inputs = {"invented": {"record": {"payload": {"question": "café"}}}}
    bound = run.input_bounds(inputs, "Invented instruction")["invented"]
    monkeypatch.setattr(run.minimax_provider, "INPUT_LIMIT", bound)
    assert run.input_bounds(inputs, "Invented instruction") == {"invented": bound}
    monkeypatch.setattr(run.minimax_provider, "INPUT_LIMIT", bound - 1)
    with pytest.raises(ValueError, match="input bound exceeded: invented"):
        run.input_bounds(inputs, "Invented instruction")
