"""Task 13's durable, zero-retry admission boundary for every remote operation.

Callers configure transport timeouts and disable SDK retries. A request is never
replayed: even a reservation without a settlement is an uncertain paid attempt.
"""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, TypeVar

T = TypeVar("T")
Kind = Literal["generation", "judge", "count"]


class DispatchStopped(RuntimeError):
    """New requests cannot be admitted under the frozen limits."""


@dataclass(frozen=True)
class Request:
    """One uniquely identified native attempt with a conservative liability."""

    key: str
    slot_id: str
    kind: Kind
    maximum_cost_usd: Decimal
    input_tokens: int
    output_tokens: int
    parent_key: str | None = None
    evaluation_started_at: float | None = None
    request_sha256: str | None = None
    accounting_basis: str | None = None


def _save(path: Path, value: dict[str, Any]) -> None:
    """Publish and flush a create-only receipt before any remote admission."""
    import os

    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _money(value: Decimal) -> Decimal:
    """Reject negative, non-Decimal and nonfinite liability declarations."""
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("Liability must be a finite nonnegative Decimal")
    return value


class LockedDispatcher:
    """Serialize admission and ledger mutations while remote calls overlap."""

    def __init__(
        self,
        directory: Path,
        *,
        cap_usd: Decimal = Decimal("10"),
        concurrency: int = 10,
        judge_per_answer: int = 16,
        evaluation_seconds: int = 1800,
        clock: Callable[[], float] = time.time,
        policy_version: str = "task13",
    ) -> None:
        """Acquire exclusive process ownership and recover cumulative liabilities."""
        if policy_version not in ("task13", "task15s", "task15t", "task15v", "task15w"):
            raise ValueError("Unknown dispatcher policy")
        expanded = policy_version in ("task15s", "task15t", "task15v", "task15w")
        recovery = policy_version == "task15t"
        high_comparison = policy_version == "task15v"
        high_recovery = policy_version == "task15w"
        max_cap, max_concurrency = (Decimal("40"), 32) if expanded else (Decimal("10"), 10)
        if recovery:
            max_cap = Decimal("37.394200565")
        if high_comparison:
            max_cap, max_concurrency = Decimal("37.370634635"), 16
        if high_recovery:
            max_cap, max_concurrency = Decimal("37.117295000"), 16
        if not 1 <= concurrency <= max_concurrency or not Decimal("0") < _money(cap_usd) <= max_cap:
            raise ValueError("Dispatcher cap or concurrency exceeds authorization")
        if judge_per_answer not in ((64,) if expanded else (16, 30)):
            raise ValueError("Judge ceiling must match an authorized policy")
        if type(evaluation_seconds) is not int or evaluation_seconds not in (1800, 5400):
            raise ValueError("Evaluation deadline must match an authorized policy")
        directory.mkdir(parents=True, exist_ok=True)
        self._policy_request_caps = (
            {"generation": 294, "judge": 294 * 64, "count": 294 * 65}
            if expanded
            else {"generation": 180, "judge": 2880, "count": 3060}
        )
        if recovery:
            self._policy_request_caps = {"generation": 2, "judge": 129, "count": 131}
        if high_comparison:
            self._policy_request_caps = {"generation": 36, "judge": 36 * 64, "count": 36 * 65}
        if high_recovery:
            self._policy_request_caps = {"generation": 3, "judge": 192, "count": 195}
        self.policy_version = policy_version
        self.directory = directory
        self.cap_usd = cap_usd
        self.concurrency = concurrency
        self.judge_per_answer = judge_per_answer
        self.evaluation_seconds = evaluation_seconds
        self.clock = clock
        self._condition = threading.Condition()
        self._active = 0
        self._closed = False
        self._lock = (directory / "writer.lock").open("a+")
        try:
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self._lock.close()
            raise
        self._rate_limit_events = 0
        self._requests: dict[str, dict[str, Any]] = {}
        self._settled: dict[str, dict[str, Any]] = {}
        self._first_dispatch: float | None = None
        self._stop: str | None = None
        try:
            policy = {"cap_usd": str(cap_usd), "concurrency": concurrency, "version": 1}
            if judge_per_answer == 30:
                policy.update(version=2, judge_per_answer=30)
            if evaluation_seconds == 5400:
                policy.update(version=3, evaluation_seconds=5400)
            if expanded:
                policy.update(
                    version=4,
                    policy_version=policy_version,
                    judge_per_answer=judge_per_answer,
                    evaluation_seconds=evaluation_seconds,
                    request_caps=self._policy_request_caps,
                )
            if recovery:
                policy.update(
                    version=5, judge_output_tokens=6144, prior_liability_usd="2.605799435"
                )
            if high_comparison:
                policy.update(
                    version=6, judge_output_tokens=6144, prior_liability_usd="2.629365365"
                )
            if high_recovery:
                policy.update(
                    version=7,
                    judge_output_tokens=6144,
                    generation_output_tokens=16384,
                    prior_liability_usd="2.882705000",
                )
            policy_path = directory / "policy.json"
            if policy_path.exists():
                if json.loads(policy_path.read_text()) != policy:
                    raise ValueError("Cannot change frozen dispatcher policy on resume")
            else:
                _save(policy_path, policy)
            for path in sorted(directory.glob("*.json")):
                row = json.loads(path.read_text())
                if path.name == "policy.json":
                    continue
                if path.name.startswith("rate-limit-"):
                    self._rate_limit_events += 1
                    self.concurrency = max(1, self.concurrency // 2)
                elif path.name == "stop.json":
                    self._stop = row["reason"]
                elif path.name.endswith(".reservation.json"):
                    digest = hashlib.sha256(row["key"].encode()).hexdigest()
                    if path.name != f"{digest}.reservation.json" or row["key"] in self._requests:
                        raise ValueError("Invalid reservation identity")
                    _money(Decimal(row["maximum_cost_usd"]))
                    self._requests[row["key"]] = row
                    started = float(row["started_at"])
                    self._first_dispatch = min(self._first_dispatch or started, started)
                elif path.name.endswith(".settlement.json"):
                    digest = hashlib.sha256(row["key"].encode()).hexdigest()
                    if path.name != f"{digest}.settlement.json" or row["key"] in self._settled:
                        raise ValueError("Invalid settlement identity")
                    self._settled[row["key"]] = row
                    if row.get("rate_limited"):
                        self.concurrency = max(1, self.concurrency // 2)
            if not self._settled.keys() <= self._requests.keys():
                raise ValueError("Settlement has no reservation")
            parents = [r["parent_key"] for r in self._requests.values() if r["kind"] == "count"]
            if None in parents or len(parents) != len(set(parents)):
                raise ValueError("Invalid recovered count parent linkage")
            for key, settlement in self._settled.items():
                actual = settlement["actual_cost_usd"]
                if actual is not None and _money(Decimal(actual)) > Decimal(
                    self._requests[key]["maximum_cost_usd"]
                ):
                    raise ValueError("Settlement exceeds reservation")
            if self.liability_usd > cap_usd:
                raise ValueError("Cumulative ledger already exceeds spending cap")
        except BaseException:
            self.close()
            raise

    def __enter__(self) -> LockedDispatcher:
        """Return the exclusively owned dispatcher."""
        return self

    def __exit__(self, *args: object) -> None:
        """Release ownership only after all running calls have settled."""
        self.close()

    def close(self) -> None:
        """Drain active requests and release the process lock."""
        with self._condition:
            self._closed = True
            self._condition.notify_all()
            while self._active:
                self._condition.wait()
            self._lock.close()

    @property
    def liability_usd(self) -> Decimal:
        """Include full reserves for every uncertain or currently running request."""
        total = Decimal("0")
        for key, request in self._requests.items():
            actual = self._settled.get(key, {}).get("actual_cost_usd")
            total += _money(Decimal(actual if actual is not None else request["maximum_cost_usd"]))
        return total

    def snapshot(self) -> dict[str, Any]:
        """Expose cumulative accounting without exposing request payloads."""
        with self._condition:
            return {
                "liability_usd": str(self.liability_usd),
                "counts": {kind: self._count(kind) for kind in ("generation", "judge", "count")},
                "uncertain_keys": sorted(self._requests.keys() - self._settled.keys()),
                "held_keys": sorted(
                    k for k, v in self._settled.items() if v["actual_cost_usd"] is None
                ),
                "accepted_unknown_count_keys": sorted(
                    k
                    for k, request in self._requests.items()
                    if request.get("accounting_basis") == "user_accepted_unknown_openai_count_fee"
                ),
                "stop_reason": self._stop,
                "effective_concurrency": self.concurrency,
                "first_dispatch_at": self._first_dispatch,
            }

    def rate_limit(self) -> None:
        """Persist a reduced ceiling after a transport returns HTTP 429 directly."""
        with self._condition:
            _save(
                self.directory / f"rate-limit-{self._rate_limit_events:05d}.json",
                {"at": self.clock()},
            )
            self._rate_limit_events += 1
            self.concurrency = max(1, self.concurrency // 2)
            self._condition.notify_all()

    def stop(self, reason: str) -> None:
        """Stop new admissions while letting already dispatched work settle."""
        with self._condition:
            if self._stop is None:
                _save(self.directory / "stop.json", {"reason": reason, "at": self.clock()})
                self._stop = reason
            self._condition.notify_all()

    async def invoke_async(
        self, request: Request, operation: Callable[[], Awaitable[tuple[T, Decimal | None]]]
    ) -> T:
        """Apply the shared admission gate and a hard 900-second async timeout."""
        while True:
            with self._condition:
                if self._active < self.concurrency or self._closed or self._stop:
                    digest = self._admit(request)
                    break
            await asyncio.sleep(0.01)
        actual: Decimal | None = None
        error: str | None = None
        rate_limited = False
        try:
            result, actual = await asyncio.wait_for(operation(), timeout=900)
            if actual is not None:
                _money(actual)
                if actual > request.maximum_cost_usd:
                    self.stop("Actual charge exceeds declared liability; accounting uncertain")
                    actual = None
                    raise ValueError("Actual charge exceeds declared liability")
            return result
        except BaseException as exc:
            actual = None
            error = type(exc).__name__
            rate_limited = getattr(exc, "status_code", None) == 429
            raise
        finally:
            self._finish(request, digest, actual, error, rate_limited)

    def _count(self, kind: str, slot: str | None = None) -> int:
        """Count reservations, including failed and uncertain attempts."""
        return sum(
            r["kind"] == kind and (slot is None or r["slot_id"] == slot)
            for r in self._requests.values()
        )

    def _stop_dispatch(self, reason: str) -> None:
        """Persist the first stop reason and deny all subsequent admissions."""
        if self._stop is None:
            _save(self.directory / "stop.json", {"reason": reason, "at": self.clock()})
            self._stop = reason
        raise DispatchStopped(self._stop)

    def _admit(self, request: Request) -> str:
        """Check and durably reserve budget and counters as one critical section."""
        with self._condition:
            while self._active >= self.concurrency and not self._closed and not self._stop:
                self._condition.wait(timeout=1)
            if self._closed:
                raise DispatchStopped("Dispatcher closed")
            if self._stop:
                raise DispatchStopped(self._stop)
            if request.key in self._requests:
                raise DispatchStopped("Request already attempted or uncertain; zero retries")
            now = self.clock()
            if self._first_dispatch is not None and now - self._first_dispatch >= 21600:
                self._stop_dispatch("Global six-hour dispatch window exhausted")
            if (
                request.evaluation_started_at is not None
                and now - request.evaluation_started_at >= self.evaluation_seconds
            ):
                self._stop_dispatch("Per-answer evaluation deadline exhausted")
            if request.kind not in ("generation", "judge", "count"):
                raise ValueError("Unknown remote request kind")
            _money(request.maximum_cost_usd)
            judge_cap = 6144 if self.policy_version in ("task15t", "task15v", "task15w") else 4096
            generation_cap = 16384 if self.policy_version == "task15w" else 12288
            output_cap = generation_cap if request.kind == "generation" else judge_cap
            if (
                not 0 <= request.input_tokens <= 100000
                or not 0 <= request.output_tokens <= output_cap
            ):
                self._stop_dispatch("Input or output token ceiling exceeded")
            if self._count(request.kind) >= self._policy_request_caps[request.kind]:
                self._stop_dispatch("Global request ceiling exhausted")
            if (
                request.kind == "judge"
                and self._count("judge", request.slot_id) >= self.judge_per_answer
            ):
                self._stop_dispatch("Per-answer judge ceiling exhausted")
            if request.kind == "generation" and self._count("generation", request.slot_id):
                raise DispatchStopped("Slot already attempted; no replacement")
            if request.kind == "count":
                if not request.parent_key or any(
                    r["kind"] == "count" and r["parent_key"] == request.parent_key
                    for r in self._requests.values()
                ):
                    raise DispatchStopped("At most one count per parent request")
            if self.liability_usd + request.maximum_cost_usd > self.cap_usd:
                self._stop_dispatch("Atomic spending reservation would exceed cap")
            digest = hashlib.sha256(request.key.encode()).hexdigest()
            row = asdict(request) | {
                "maximum_cost_usd": str(request.maximum_cost_usd),
                "started_at": now,
            }
            _save(self.directory / f"{digest}.reservation.json", row)
            self._requests[request.key] = row
            self._first_dispatch = self._first_dispatch if self._first_dispatch is not None else now
            self._active += 1
            return digest

    def invoke(self, request: Request, operation: Callable[[], tuple[T, Decimal | None]]) -> T:
        """Run exactly once after admission; errors retain their full reserved liability.

        The callable must use a <=900-second native timeout and no SDK retries.
        Returning None for cost preserves the full reserve, never assumes free use.
        """
        digest = self._admit(request)
        actual: Decimal | None = None
        error: str | None = None
        rate_limited = False
        try:
            result, actual = operation()
            if actual is not None:
                _money(actual)
                if actual > request.maximum_cost_usd:
                    self.stop("Actual charge exceeds declared liability; accounting uncertain")
                    actual = None
                    raise ValueError(
                        "Actual charge exceeds declared liability; accounting uncertain"
                    )
            return result
        except BaseException as exc:
            actual = None
            error = type(exc).__name__
            rate_limited = getattr(exc, "status_code", None) == 429
            raise
        finally:
            self._finish(request, digest, actual, error, rate_limited)

    def _finish(
        self,
        request: Request,
        digest: str,
        actual: Decimal | None,
        error: str | None,
        rate_limited: bool,
    ) -> None:
        """Durably reconcile the reservation before releasing its concurrency slot."""
        with self._condition:
            try:
                row = {
                    "key": request.key,
                    "actual_cost_usd": str(actual) if actual is not None else None,
                    "error": error,
                    "rate_limited": rate_limited,
                    "finished_at": self.clock(),
                }
                _save(self.directory / f"{digest}.settlement.json", row)
                self._settled[request.key] = row
                if rate_limited:
                    self.concurrency = max(1, self.concurrency // 2)
            except BaseException:
                self._stop = "Settlement persistence failed; accounting uncertain"
                raise
            finally:
                self._active -= 1
                self._condition.notify_all()
