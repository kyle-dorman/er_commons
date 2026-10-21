"""Offline checks for global Task 13 admission and interrupted-attempt accounting."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest

from er_commons.locked_dispatch import DispatchStopped, Kind, LockedDispatcher, Request


def request(key: str, cost: str = "0.1", **kwargs: object) -> Request:
    """Create an invented native request without accessing benchmark payloads."""
    return Request(key, key, "generation", Decimal(cost), 20, 100, **kwargs)  # type: ignore[arg-type]


def test_atomic_parallel_budget(tmp_path: Path) -> None:
    """Competing requests cannot reserve the same remaining dollars."""
    with LockedDispatcher(tmp_path, cap_usd=Decimal("1")) as dispatcher:

        def submit(i: int) -> bool:
            try:
                dispatcher.invoke(request(str(i), "0.6"), lambda: (None, None))
                return True
            except DispatchStopped:
                return False

        with ThreadPoolExecutor(max_workers=10) as pool:
            assert sum(pool.map(submit, range(30))) == 1
        assert dispatcher.liability_usd == Decimal("0.6")
        assert len(list(tmp_path.glob("*.reservation.json"))) == 1


def test_shared_async_concurrency(tmp_path: Path) -> None:
    """Counters, generations and judges contend for the same ten slots."""

    async def run() -> None:
        with LockedDispatcher(tmp_path) as dispatcher:
            active = peak = 0

            async def operation() -> tuple[None, Decimal]:
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.01)
                active -= 1
                return None, Decimal("0.001")

            kinds: list[Kind] = ["count", "generation", "judge"] * 20
            items = [
                Request(str(i), str(i), kind, Decimal("0.1"), 20, 0, parent_key=f"parent-{i}")
                for i, kind in enumerate(kinds)
            ]
            await asyncio.gather(*(dispatcher.invoke_async(item, operation) for item in items))
            assert peak == 10
            assert dispatcher.liability_usd == Decimal("0.060")

    asyncio.run(run())


def test_unknown_and_interrupted_never_replayed(tmp_path: Path) -> None:
    """Durable reservations survive interruption and continue to consume budget."""
    with LockedDispatcher(tmp_path) as dispatcher:
        dispatcher.invoke(request("unknown", "0.8"), lambda: (None, None))
        dispatcher._admit(request("interrupted", "0.7"))
        # Simulate abrupt process loss after reservation and before settlement.
        dispatcher._active = 0
    with LockedDispatcher(tmp_path) as dispatcher:
        assert dispatcher.liability_usd == Decimal("1.5")
        for key in ("unknown", "interrupted"):
            with pytest.raises(DispatchStopped, match="already attempted"):
                dispatcher.invoke(request(key), lambda: pytest.fail("replayed"))
        assert dispatcher.snapshot()["uncertain_keys"] == ["interrupted"]


def test_process_exclusion(tmp_path: Path) -> None:
    """A second owner cannot race admission even in the same Python process."""
    with LockedDispatcher(tmp_path):
        with pytest.raises(BlockingIOError):
            LockedDispatcher(tmp_path)


@pytest.mark.parametrize("kind", ["window", "answer", "tokens", "output"])
def test_deadline_and_token_stops(tmp_path: Path, kind: str) -> None:
    """Violations stop future work before invoking any prohibited operation."""
    now = [100.0]
    with LockedDispatcher(tmp_path, clock=lambda: now[0]) as dispatcher:
        dispatcher.invoke(request("first"), lambda: (None, Decimal("0")))
        now[0] += 21600 if kind == "window" else 1800
        item = Request(
            "second",
            "second",
            "generation",
            Decimal("0.1"),
            100001 if kind == "tokens" else 20,
            12289 if kind == "output" else 100,
            evaluation_started_at=100 if kind == "answer" else None,
        )
        with pytest.raises(DispatchStopped):
            dispatcher.invoke(item, lambda: pytest.fail("dispatched"))
        assert dispatcher.snapshot()["stop_reason"]


def test_rate_limit_reduces_future_concurrency_and_holds_cost(tmp_path: Path) -> None:
    """A 429 is one failed attempt, with no retry and persistent lower concurrency."""

    class RateLimit(Exception):
        status_code = 429

    def operation() -> tuple[None, Decimal]:
        raise RateLimit

    with LockedDispatcher(tmp_path) as dispatcher:
        with pytest.raises(RateLimit):
            dispatcher.invoke(request("limited"), operation)
        assert dispatcher.concurrency == 5
        assert dispatcher.liability_usd == Decimal("0.1")
    with LockedDispatcher(tmp_path) as dispatcher:
        assert dispatcher.concurrency == 5


def test_stop_allows_inflight_to_settle(tmp_path: Path) -> None:
    """A stop blocks admission while preserving the result of an active request."""
    started = threading.Event()
    release = threading.Event()
    with LockedDispatcher(tmp_path) as dispatcher:

        def operation() -> tuple[str, Decimal]:
            started.set()
            assert release.wait(2)
            return "result", Decimal("0.02")

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(dispatcher.invoke, request("active"), operation)
            assert started.wait(2)
            dispatcher.stop("fixture stop")
            with pytest.raises(DispatchStopped, match="fixture stop"):
                dispatcher.invoke(request("new"), lambda: pytest.fail("dispatched"))
            release.set()
            assert future.result() == "result"
        assert dispatcher.liability_usd == Decimal("0.02")


def test_one_count_and_sixteen_judges(tmp_path: Path) -> None:
    """Count parent IDs and per-answer ceilings cannot be bypassed with fresh keys."""
    with LockedDispatcher(tmp_path) as dispatcher:
        first = Request("count", "slot", "count", Decimal("0"), 20, 0, parent_key="parent")
        dispatcher.invoke(first, lambda: (None, Decimal("0")))
        duplicate = Request("count2", "slot", "count", Decimal("0"), 20, 0, parent_key="parent")
        with pytest.raises(DispatchStopped, match="one count"):
            dispatcher.invoke(duplicate, lambda: pytest.fail("duplicate count"))
        for i in range(16):
            dispatcher.invoke(
                Request(str(i), "slot", "judge", Decimal("0"), 20, 10), lambda: (None, Decimal("0"))
            )
        with pytest.raises(DispatchStopped, match="judge ceiling"):
            dispatcher.invoke(
                Request("extra", "slot", "judge", Decimal("0"), 20, 10),
                lambda: pytest.fail("extra judge"),
            )


def test_async_cancellation_retains_liability(tmp_path: Path) -> None:
    """Cancellation creates an uncertain settlement and never frees its reserve."""

    async def run() -> None:
        with LockedDispatcher(tmp_path) as dispatcher:

            async def operation() -> tuple[None, Decimal]:
                await asyncio.sleep(20)
                return None, Decimal("0")

            task = asyncio.create_task(dispatcher.invoke_async(request("cancel"), operation))
            await asyncio.sleep(0.01)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert dispatcher.liability_usd == Decimal("0.1")
            assert dispatcher.snapshot()["held_keys"] == ["cancel"]

    asyncio.run(run())


def test_persistent_rate_limit_and_policy(tmp_path: Path) -> None:
    """Direct HTTP rate-limit pressure and budget identity survive restart."""
    with LockedDispatcher(tmp_path) as dispatcher:
        dispatcher.rate_limit()
        dispatcher.rate_limit()
        assert dispatcher.concurrency == 2
    with pytest.raises(ValueError, match="policy"):
        LockedDispatcher(tmp_path, cap_usd=Decimal("9"))
    with LockedDispatcher(tmp_path) as dispatcher:
        assert dispatcher.concurrency == 2


def test_invalid_recovered_identity_fails_closed(tmp_path: Path) -> None:
    """Copied receipts cannot create a second valid reservation for one key."""
    with LockedDispatcher(tmp_path) as dispatcher:
        dispatcher.invoke(request("first"), lambda: (None, None))
    reservation = next(tmp_path.glob("*.reservation.json"))
    (tmp_path / "bogus.reservation.json").write_bytes(reservation.read_bytes())
    with pytest.raises(ValueError, match="identity"):
        LockedDispatcher(tmp_path)


def test_stop_wakes_async_queue_without_event_loop_deadlock(tmp_path: Path) -> None:
    """Stopped queued work leaves a saturated gate while admitted work drains."""

    async def run() -> None:
        with LockedDispatcher(tmp_path, concurrency=1) as dispatcher:
            release = asyncio.Event()

            async def operation() -> tuple[None, Decimal]:
                await release.wait()
                return None, Decimal("0")

            active = asyncio.create_task(dispatcher.invoke_async(request("first"), operation))
            await asyncio.sleep(0.01)
            queued = asyncio.create_task(dispatcher.invoke_async(request("second"), operation))
            await asyncio.sleep(0.01)
            dispatcher.stop("fixture saturated stop")
            with pytest.raises(DispatchStopped, match="saturated stop"):
                await asyncio.wait_for(queued, timeout=1)
            release.set()
            await active

    asyncio.run(run())


def test_thirty_judge_amendment_preserves_cumulative_limits(tmp_path: Path) -> None:
    """The explicit amended policy permits thirty unique items, never a replay or reset."""
    with LockedDispatcher(tmp_path, judge_per_answer=30) as dispatcher:
        for i in range(17):
            dispatcher.invoke(
                Request(str(i), "slot", "judge", Decimal("0.1"), 20, 10),
                lambda: (None, Decimal("0.01")),
            )
    with pytest.raises(ValueError, match="policy"):
        LockedDispatcher(tmp_path)
    with LockedDispatcher(tmp_path, judge_per_answer=30) as dispatcher:
        assert dispatcher.liability_usd == Decimal("0.17")
        with pytest.raises(DispatchStopped, match="already attempted"):
            dispatcher.invoke(
                Request("0", "slot", "judge", Decimal("0"), 20, 10), lambda: pytest.fail("retry")
            )
        for i in range(17, 30):
            dispatcher.invoke(
                Request(str(i), "slot", "judge", Decimal("0"), 20, 10), lambda: (None, Decimal("0"))
            )
        with pytest.raises(DispatchStopped, match="judge ceiling"):
            dispatcher.invoke(
                Request("31", "slot", "judge", Decimal("0"), 20, 10),
                lambda: pytest.fail("over limit"),
            )


@pytest.mark.parametrize("judge_limit,version", [(16, 1), (30, 2)])
def test_original_evaluation_policy_bytes_unchanged(
    tmp_path: Path, judge_limit: int, version: int
) -> None:
    """The optional deadline amendment does not rewrite either historical policy."""
    import json

    expected = {"cap_usd": "10", "concurrency": 10, "version": version}
    if judge_limit == 30:
        expected["judge_per_answer"] = 30
    with LockedDispatcher(tmp_path, judge_per_answer=judge_limit):
        assert (tmp_path / "policy.json").read_text() == (
            json.dumps(expected, sort_keys=True, indent=2) + "\n"
        )
    before = (tmp_path / "policy.json").read_bytes()
    with LockedDispatcher(tmp_path, judge_per_answer=judge_limit, evaluation_seconds=1800):
        assert (tmp_path / "policy.json").read_bytes() == before


def test_extended_evaluation_deadline_keeps_elapsed_time_and_exact_boundary(tmp_path: Path) -> None:
    """The amendment permits old elapsed time without resetting it or allowing the boundary."""
    import json

    now = [1900.0]
    with LockedDispatcher(
        tmp_path, judge_per_answer=30, evaluation_seconds=5400, clock=lambda: now[0]
    ) as dispatcher:
        policy = json.loads((tmp_path / "policy.json").read_text())
        assert policy == {
            "cap_usd": "10",
            "concurrency": 10,
            "version": 3,
            "judge_per_answer": 30,
            "evaluation_seconds": 5400,
        }
        dispatcher.invoke(
            Request("first", "slot", "judge", Decimal("0.1"), 20, 10, evaluation_started_at=100),
            lambda: (None, Decimal("0.01")),
        )
        now[0] = 5499
        dispatcher.invoke(
            Request("second", "slot", "judge", Decimal("0.1"), 20, 10, evaluation_started_at=100),
            lambda: (None, Decimal("0.01")),
        )
    with pytest.raises(ValueError, match="policy"):
        LockedDispatcher(tmp_path, judge_per_answer=30)
    with LockedDispatcher(
        tmp_path, judge_per_answer=30, evaluation_seconds=5400, clock=lambda: now[0]
    ) as dispatcher:
        assert dispatcher.liability_usd == Decimal("0.02")
        with pytest.raises(DispatchStopped, match="already attempted"):
            dispatcher.invoke(
                Request("first", "slot", "judge", Decimal("0"), 20, 10),
                lambda: pytest.fail("Previously attempted request replayed"),
            )
        now[0] = 5500
        with pytest.raises(DispatchStopped, match="evaluation deadline"):
            dispatcher.invoke(
                Request("third", "slot", "judge", Decimal("0"), 20, 10, evaluation_started_at=100),
                lambda: pytest.fail("Exact deadline admitted"),
            )


def test_extended_evaluation_preserves_global_dispatch_deadline(tmp_path: Path) -> None:
    """The per-answer extension leaves the original six-hour dispatch window intact."""
    now = [100.0]
    with LockedDispatcher(tmp_path, evaluation_seconds=5400, clock=lambda: now[0]) as dispatcher:
        dispatcher.invoke(request("first"), lambda: (None, Decimal("0")))
        now[0] += 21600
        with pytest.raises(DispatchStopped, match="six-hour"):
            dispatcher.invoke(
                Request(
                    "second",
                    "slot",
                    "judge",
                    Decimal("0"),
                    20,
                    10,
                    evaluation_started_at=now[0] - 1,
                ),
                lambda: pytest.fail("Global dispatch deadline extended"),
            )


@pytest.mark.parametrize("seconds", [0, 1801, 5401, 5400.0, True])
def test_unapproved_evaluation_deadlines_rejected(tmp_path: Path, seconds: object) -> None:
    """Only exact integer versions explicitly authorized by the user are accepted."""
    with pytest.raises(ValueError, match="Evaluation deadline"):
        LockedDispatcher(tmp_path, evaluation_seconds=seconds)  # type: ignore[arg-type]
    assert not (tmp_path / "policy.json").exists()
