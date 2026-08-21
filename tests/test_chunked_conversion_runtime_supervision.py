"""Behavior tests for isolated chunk worker resource supervision."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pytest

from er_commons.chunked_conversion.runtime.contracts import ResourceLimits
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.supervision import (
    ProcessServices,
    ProcessSupervisor,
)


class FakeProcess:
    """Deterministic child whose first poll is running and second is complete."""

    pid = 42

    def __init__(self, return_code: int = 0) -> None:
        self.return_code = return_code
        self.polls = 0

    def poll(self) -> int | None:
        self.polls += 1
        return None if self.polls == 1 else self.return_code

    def wait(self, timeout: float | None = None) -> int:
        return self.return_code


def _services(
    process: FakeProcess,
    *,
    rss: int = 10,
    available: int = 100,
    swap: int = 0,
) -> tuple[ProcessServices, list[tuple[int, float]]]:
    terminated: list[tuple[int, float]] = []
    ticks = iter((0.0, 0.1, 0.2, 0.3, 0.4))

    def start(command: object, stdout: BinaryIO, stderr: BinaryIO, cwd: Path) -> FakeProcess:
        return process

    return (
        ProcessServices(
            start=start,
            terminate=lambda child, grace: terminated.append((child.pid, grace)),
            tree_rss=lambda pid: rss,
            available_memory=lambda: available,
            swap_used=lambda: swap,
            monotonic=lambda: next(ticks),
            sleep=lambda seconds: None,
        ),
        terminated,
    )


def _limits(**updates: int | float) -> ResourceLimits:
    values: dict[str, int | float] = {
        "max_rss_bytes": 50,
        "max_wall_seconds": 5.0,
        "minimum_available_bytes": 20,
        "max_swap_growth_bytes": 10,
        "sample_interval_seconds": 0.1,
        "termination_grace_seconds": 2.0,
    }
    values.update(updates)
    return ResourceLimits.model_validate(values)


def test_supervisor_returns_closed_resource_observation(tmp_path: Path) -> None:
    services, terminated = _services(FakeProcess())
    result = ProcessSupervisor(services).run(
        ["fake"], cwd=tmp_path, log_root=tmp_path / "logs", limits=_limits(), stage="range"
    )

    assert result.process_tree_peak_rss_bytes == 10
    assert result.minimum_system_available_bytes == 100
    assert result.stdout.endswith("stdout.log")
    assert terminated == []


def test_supervisor_stops_rss_breach_with_contextual_logs(tmp_path: Path) -> None:
    services, terminated = _services(FakeProcess(), rss=51)

    with pytest.raises(ChunkedConversionError) as raised:
        ProcessSupervisor(services).run(
            ["fake"],
            cwd=tmp_path,
            log_root=tmp_path / "logs",
            limits=_limits(),
            stage="aggregate",
        )

    assert raised.value.code == "rss_limit"
    assert raised.value.stage == "aggregate"
    assert raised.value.expected == 50
    assert raised.value.actual == 51
    stderr = raised.value.context["stderr"]
    assert isinstance(stderr, str) and stderr.endswith("stderr.log")
    assert terminated == [(42, 2.0)]


def test_supervisor_reports_nonzero_exit_without_termination(tmp_path: Path) -> None:
    services, terminated = _services(FakeProcess(return_code=7))

    with pytest.raises(ChunkedConversionError) as raised:
        ProcessSupervisor(services).run(
            ["fake"], cwd=tmp_path, log_root=tmp_path / "logs", limits=_limits(), stage="range"
        )

    assert raised.value.code == "child_nonzero_exit"
    assert raised.value.actual == 7
    assert terminated == []
