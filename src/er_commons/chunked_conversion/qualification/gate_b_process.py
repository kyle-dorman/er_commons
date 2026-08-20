"""Bounded subprocess control for isolated Gate B seam workers."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

from er_commons.chunked_conversion.qualification.gate_b_contracts import GateBContractError
from er_commons.chunked_conversion.qualification.gate_b_worker import write_failure


def run_isolated_worker(
    spec_path: Path,
    seam_root: Path,
    *,
    worker_entrypoint: Path,
    max_rss_bytes: int,
    timeout_seconds: float,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> dict[str, Any]:
    """Run one worker under RSS, swap, available-memory, and wall-time limits."""
    stdout_path = seam_root / "records/worker.stdout.log"
    stderr_path = seam_root / "records/worker.stderr.log"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(worker_entrypoint), "--worker-spec", str(spec_path)]
    started = time.monotonic()
    peak = 0
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        observed = psutil.Process(process.pid)
        swap_started = psutil.swap_memory().used
        while process.poll() is None:
            peak = max(peak, _process_tree_rss(observed))
            breach = _resource_breach(
                peak=peak,
                max_rss_bytes=max_rss_bytes,
                swap_started=swap_started,
                elapsed=time.monotonic() - started,
                timeout_seconds=timeout_seconds,
            )
            if breach is not None:
                _terminate(process)
                error = GateBContractError("resource_breach", seam_root.as_posix(), breach)
                write_failure(seam_root, error, stage="worker_monitor")
                raise error
            time.sleep(0.1)
    elapsed = time.monotonic() - started
    if process.returncode != 0:
        raise GateBContractError(
            "worker_failed",
            seam_root.as_posix(),
            f"return_code={process.returncode}; retained evidence={seam_root}",
        )
    return {
        "peak_process_tree_rss_bytes": peak,
        "wall_seconds": elapsed,
        "swap_delta_bytes": psutil.swap_memory().used - swap_started,
        "available_memory_bytes_after": psutil.virtual_memory().available,
    }


def _process_tree_rss(process: psutil.Process) -> int:
    try:
        return int(
            process.memory_info().rss
            + sum(child.memory_info().rss for child in process.children(recursive=True))
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def _resource_breach(
    *, peak: int, max_rss_bytes: int, swap_started: int, elapsed: float, timeout_seconds: float
) -> str | None:
    if peak > max_rss_bytes:
        return f"rss {peak} exceeds {max_rss_bytes}"
    if psutil.virtual_memory().available < 4 * 1024**3:
        return "system available memory fell below 4 GiB"
    if psutil.swap_memory().used - swap_started > 512 * 1024**2:
        return "system swap grew by more than 512 MiB"
    if elapsed > timeout_seconds:
        return f"wall time {elapsed:.3f}s exceeds {timeout_seconds:.3f}s"
    return None


def _terminate(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


__all__ = ["run_isolated_worker"]
