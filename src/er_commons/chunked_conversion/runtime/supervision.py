"""Isolated child execution with explicit, testable resource-stop policy."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

import psutil  # type: ignore[import-untyped]

from er_commons.chunked_conversion.runtime.contracts import (
    ResourceLimits,
    ResourceObservation,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError


class ChildProcess(Protocol):
    """Small subprocess surface required by the supervisor."""

    pid: int

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...


StartProcess = Callable[[Sequence[str], BinaryIO, BinaryIO, Path], ChildProcess]
TerminateProcess = Callable[[ChildProcess, float], None]


@dataclass(frozen=True)
class ProcessServices:
    """Injectable OS seams for deterministic resource and crash-window tests."""

    start: StartProcess
    terminate: TerminateProcess
    tree_rss: Callable[[int], int]
    available_memory: Callable[[], int]
    swap_used: Callable[[], int]
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


def default_process_services() -> ProcessServices:
    """Return the real process and system-metric adapters used by live workers."""
    return ProcessServices(
        start=_start_process,
        terminate=_terminate_process_group,
        tree_rss=process_tree_rss,
        available_memory=lambda: psutil.virtual_memory().available,
        swap_used=lambda: psutil.swap_memory().used,
    )


class ProcessSupervisor:
    """Run one process group and retain logs for every terminal outcome."""

    def __init__(self, services: ProcessServices | None = None) -> None:
        self._services = services or default_process_services()

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        log_root: Path,
        limits: ResourceLimits,
        stage: str,
    ) -> ResourceObservation:
        """Return measurements or raise a contextual stop/failure diagnostic."""
        log_root.mkdir(parents=True, exist_ok=True)
        stdout_path = log_root / "stdout.log"
        stderr_path = log_root / "stderr.log"
        started = self._services.monotonic()
        peak = 0
        minimum_available = self._services.available_memory()
        swap_start = self._services.swap_used()
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = self._services.start(command, stdout, stderr, cwd)
            stop = self._monitor(
                process,
                limits=limits,
                started=started,
                swap_start=swap_start,
                peak=peak,
                minimum_available=minimum_available,
            )
            if stop.reason is not None:
                self._services.terminate(process, limits.termination_grace_seconds)
                raise ChunkedConversionError(
                    stop.code,
                    stage=stage,
                    path=log_root.as_posix(),
                    expected=stop.expected,
                    actual=stop.actual,
                    context={"stdout": str(stdout_path), "stderr": str(stderr_path)},
                )
            return_code = process.wait()
        if return_code != 0:
            raise ChunkedConversionError(
                "child_nonzero_exit",
                stage=stage,
                path=log_root.as_posix(),
                expected=0,
                actual=return_code,
                context={"stdout": str(stdout_path), "stderr": str(stderr_path)},
            )
        return ResourceObservation(
            process_tree_peak_rss_bytes=stop.peak,
            wall_seconds=self._services.monotonic() - started,
            minimum_system_available_bytes=stop.minimum_available,
            swap_delta_bytes=max(0, self._services.swap_used() - swap_start),
            stdout=stdout_path.as_posix(),
            stderr=stderr_path.as_posix(),
        )

    def _monitor(
        self,
        process: ChildProcess,
        *,
        limits: ResourceLimits,
        started: float,
        swap_start: int,
        peak: int,
        minimum_available: int,
    ) -> _StopDecision:
        while process.poll() is None:
            rss = self._services.tree_rss(process.pid)
            peak = max(peak, rss)
            available = self._services.available_memory()
            minimum_available = min(minimum_available, available)
            decision = _stop_decision(
                rss=rss,
                available=available,
                swap_growth=self._services.swap_used() - swap_start,
                elapsed=self._services.monotonic() - started,
                limits=limits,
            )
            if decision is not None:
                return decision.with_observations(peak, minimum_available)
            self._services.sleep(limits.sample_interval_seconds)
        return _StopDecision(None, "", None, None, peak, minimum_available)


@dataclass(frozen=True)
class _StopDecision:
    reason: str | None
    code: str
    expected: object | None
    actual: object | None
    peak: int = 0
    minimum_available: int = 0

    def with_observations(self, peak: int, minimum_available: int) -> _StopDecision:
        return _StopDecision(
            self.reason,
            self.code,
            self.expected,
            self.actual,
            peak,
            minimum_available,
        )


def _stop_decision(
    *,
    rss: int,
    available: int,
    swap_growth: int,
    elapsed: float,
    limits: ResourceLimits,
) -> _StopDecision | None:
    checks = (
        (rss > limits.max_rss_bytes, "rss_limit", limits.max_rss_bytes, rss),
        (
            available < limits.minimum_available_bytes,
            "available_memory_floor",
            limits.minimum_available_bytes,
            available,
        ),
        (
            swap_growth > limits.max_swap_growth_bytes,
            "swap_growth_limit",
            limits.max_swap_growth_bytes,
            swap_growth,
        ),
        (elapsed > limits.max_wall_seconds, "wall_time_limit", limits.max_wall_seconds, elapsed),
    )
    for failed, code, expected, actual in checks:
        if failed:
            return _StopDecision(code, code, expected, actual)
    return None


def process_tree_rss(pid: int) -> int:
    """Return current resident bytes for a process and all descendants."""
    try:
        parent = psutil.Process(pid)
        processes = [parent, *parent.children(recursive=True)]
        return sum(process.memory_info().rss for process in processes if process.is_running())
    except psutil.Error:
        return 0


def _start_process(
    command: Sequence[str], stdout: BinaryIO, stderr: BinaryIO, cwd: Path
) -> ChildProcess:
    return subprocess.Popen(
        list(command), stdout=stdout, stderr=stderr, start_new_session=True, cwd=cwd
    )


def _terminate_process_group(process: ChildProcess, grace_seconds: float) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
