"""Supervise one offline command with persistent, external attempt accounting."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import signal
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ExecutionLimits:
    """Finite sampled ceilings; output includes both payload and attempt logs."""

    max_seconds: float
    max_rss_bytes: int
    max_output_bytes: int
    min_free_bytes: int
    max_swap_growth_bytes: int = 0
    sample_seconds: float = 0.1
    disk_sample_seconds: float = 1.0
    termination_grace_seconds: float = 15.0

    def validate(self) -> None:
        """Reject unbounded or invalid limits before creating any output."""
        for name, value in asdict(self).items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"invalid execution limit: {name}")
            if value == 0 and name not in {"min_free_bytes", "max_swap_growth_bytes"}:
                raise ValueError(f"execution limit must be positive: {name}")


def offline_environment() -> dict[str, str]:
    """Override inherited download and numerical thread settings for all children."""
    environment = dict(os.environ)
    environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1")
    for name in ("OMP", "MKL", "OPENBLAS", "VECLIB", "NUMEXPR"):
        environment[f"{name}_NUM_THREADS" if name != "VECLIB" else "VECLIB_MAXIMUM_THREADS"] = "4"
    return environment


def _write_record(path: Path, record: dict[str, Any]) -> None:
    """Replace the mutable status atomically, never touching sealed pipeline files."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def _tree_bytes(root: Path) -> int:
    """Count actual files once; allow internal links but reject unaccounted targets."""
    total = 0
    for directory, folders, files in os.walk(root):
        for name in folders + files:
            path = Path(directory) / name
            try:
                stat = path.lstat()
                if path.is_symlink():
                    if not path.resolve().is_relative_to(root.resolve()):
                        raise ValueError(f"output symlink escapes accounting root: {path}")
                    continue
                if name in files:
                    total += stat.st_size
            except FileNotFoundError:
                continue  # Atomic publication may rename files during a sample.
    return total


class ProcessTree:
    """Retain process identities after reparenting, including new-session workers."""

    def __init__(self, pid: int) -> None:
        """Start tracking a command while retaining identities against PID reuse."""
        self.processes: dict[int, Any] = {pid: psutil.Process(pid)}

    def live(self) -> list[Any]:
        """Discover children of every surviving tracked process, across sessions."""
        for process in list(self.processes.values()):
            try:
                if process.is_running():
                    for child in process.children(recursive=True):
                        self.processes[child.pid] = child
            except psutil.NoSuchProcess:
                continue
        result = []
        for process in self.processes.values():
            try:
                if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                    result.append(process)
            except psutil.NoSuchProcess:
                continue
        return result

    def rss(self) -> int:
        """Sum resident memory over observed surviving descendants."""
        total = 0
        for process in self.live():
            try:
                total += process.memory_info().rss
            except psutil.NoSuchProcess:
                continue
        return total

    def terminate(self, grace: float) -> list[int]:
        """Stop forks, signal each descendant across sessions, then kill survivors."""
        processes = self.live()
        for process in processes:
            try:
                process.suspend()
            except psutil.NoSuchProcess:
                pass
        processes = self.live()
        for process in reversed(processes):
            try:
                process.terminate()
                process.resume()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(processes, timeout=grace)
        for process in alive:
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(alive, timeout=grace)
        return [process.pid for process in self.live()]


def _prepare(attempt_root: Path, output_root: Path, limits: ExecutionLimits) -> None:
    """Require disjoint accounting roots and adequate initial free disk."""
    limits.validate()
    if attempt_root == output_root or attempt_root.is_relative_to(output_root):
        raise ValueError("attempt root must be outside the pipeline output root")
    if output_root.is_relative_to(attempt_root):
        raise ValueError("pipeline output root must be outside the attempt root")
    if not output_root.is_dir():
        raise ValueError("output root must be an existing dedicated directory")
    if attempt_root.exists():
        raise FileExistsError(attempt_root)
    for path in (output_root, attempt_root.parent):
        if shutil.disk_usage(path).free < limits.min_free_bytes:
            raise ValueError(f"insufficient initial free disk: {path}")
    if _tree_bytes(output_root) > limits.max_output_bytes:
        raise ValueError("output budget already exceeded")
    attempt_root.mkdir()


def _observe(record: dict[str, Any], tree: ProcessTree, started: float, swap_baseline: int) -> None:
    """Update finite timing, process memory, and system swap growth observations."""
    record["elapsed_seconds"] = time.monotonic() - started
    record["peak_rss_bytes"] = max(record["peak_rss_bytes"], tree.rss())
    growth = max(0, psutil.swap_memory().used - swap_baseline)
    record["peak_swap_growth_bytes"] = max(record["peak_swap_growth_bytes"], growth)


def _budget_reason(record: dict[str, Any], limits: ExecutionLimits) -> str | None:
    """Select the first exceeded ceiling without retry or implicit relaxation."""
    for key, maximum in (
        ("elapsed_seconds", limits.max_seconds),
        ("peak_rss_bytes", limits.max_rss_bytes),
        ("peak_output_bytes", limits.max_output_bytes),
        ("peak_swap_growth_bytes", limits.max_swap_growth_bytes),
    ):
        if record[key] > maximum:
            return f"budget_exceeded:{key}"
    return None


def _monitor(
    child: subprocess.Popen[bytes],
    tree: ProcessTree,
    record: dict[str, Any],
    attempt_root: Path,
    output_root: Path,
    limits: ExecutionLimits,
    started: float,
) -> None:
    """Sample a command until exit or the first exceeded resource ceiling."""
    next_disk = 0.0
    while True:
        _observe(record, tree, started, record["swap_baseline_bytes"])
        done = child.poll() is not None
        if time.monotonic() >= next_disk or done:
            size = _tree_bytes(output_root) + _tree_bytes(attempt_root)
            record["peak_output_bytes"] = max(record["peak_output_bytes"], size)
            next_disk = time.monotonic() + limits.disk_sample_seconds
            _write_record(attempt_root / "status.json", record)
        reason = _budget_reason(record, limits)
        if reason or done:
            record.update(
                status="failed" if reason or child.returncode else "succeeded",
                reason=reason,
                returncode=child.returncode,
            )
            break
        time.sleep(limits.sample_seconds)


def supervise(
    command: list[str], *, attempt_root: Path, output_root: Path, limits: ExecutionLimits
) -> dict[str, Any]:
    """Run once, retain accounting, and terminate the entire observed tree on failure."""
    if not command:
        raise ValueError("command is required")
    attempt_root, output_root = attempt_root.resolve(), output_root.resolve()
    _prepare(attempt_root, output_root, limits)
    started = time.monotonic()
    record: dict[str, Any] = {
        "schema_version": "background_execution_v1",
        "status": "starting",
        "started_at": datetime.now(UTC).isoformat(),
        "command": command,
        "output_root": str(output_root),
        "attempt_root": str(attempt_root),
        "limits": asdict(limits),
        "swap_baseline_bytes": psutil.swap_memory().used,
        "elapsed_seconds": 0.0,
        "peak_rss_bytes": 0,
        "peak_output_bytes": 0,
        "peak_swap_growth_bytes": 0,
        "returncode": None,
        "offline_environment": {
            k: v
            for k, v in offline_environment().items()
            if k
            in {
                "HF_HUB_OFFLINE",
                "HF_DATASETS_OFFLINE",
                "TRANSFORMERS_OFFLINE",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            }
        },
    }
    _write_record(attempt_root / "status.json", record)
    tree: ProcessTree | None = None
    child: subprocess.Popen[bytes] | None = None
    old_handlers: dict[int, Any] = {}

    def interrupted(signum: int, frame: Any) -> None:
        """Route termination requests through the same descendant cleanup path."""
        raise InterruptedError(f"received signal {signum}")

    try:
        for interrupt_signal in (signal.SIGTERM, signal.SIGINT):
            old_handlers[interrupt_signal] = signal.signal(interrupt_signal, interrupted)
        with (attempt_root / "command.log").open("xb") as log:
            child = subprocess.Popen(
                command, stdout=log, stderr=log, env=offline_environment(), start_new_session=True
            )
            tree = ProcessTree(child.pid)
            record.update(status="running", pid=child.pid)
            _monitor(child, tree, record, attempt_root, output_root, limits, started)
    except (Exception, KeyboardInterrupt) as error:
        record.update(status="failed", reason=f"{type(error).__name__}: {error}")
    finally:
        # Ignore further interrupts while completing mandatory cleanup/accounting.
        for signum in old_handlers:
            signal.signal(signum, signal.SIG_IGN)
        if tree is not None and tree.live():
            if record["status"] == "succeeded":
                record.update(status="failed", reason="command left running descendants")
            record["surviving_pids"] = tree.terminate(limits.termination_grace_seconds)
        if child is not None:
            record["returncode"] = child.wait()
        record["elapsed_seconds"] = time.monotonic() - started
        record["finished_at"] = datetime.now(UTC).isoformat()
        try:
            size = _tree_bytes(output_root) + _tree_bytes(attempt_root)
            # Reserve bounded terminal metadata before declaring success.
            record["terminal_metadata_reservation_bytes"] = 65536
            record["peak_output_bytes"] = max(record["peak_output_bytes"], size + 65536)
            reason = _budget_reason(record, limits)
            if record["status"] == "succeeded" and reason:
                record.update(status="failed", reason=reason)
        except Exception as error:
            record.update(status="failed", reason=f"output accounting failed: {error}")
        try:
            _write_record(attempt_root / "execution.json", record)
            _write_record(attempt_root / "status.json", record)
        finally:
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
    return record


def main() -> None:
    """Expose explicit resource settings and a command after the -- separator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    for name, kind in (
        ("max_seconds", float),
        ("max_rss_bytes", int),
        ("max_output_bytes", int),
        ("min_free_bytes", int),
        ("max_swap_growth_bytes", int),
        ("sample_seconds", float),
        ("disk_sample_seconds", float),
        ("termination_grace_seconds", float),
    ):
        parser.add_argument("--" + name.replace("_", "-"), type=kind, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = vars(parser.parse_args())
    command = arguments.pop("command")
    if command[:1] == ["--"]:
        command = command[1:]
    attempt_root, output_root = arguments.pop("attempt_root"), arguments.pop("output_root")
    record = supervise(
        command,
        attempt_root=attempt_root,
        output_root=output_root,
        limits=ExecutionLimits(**arguments),
    )
    raise SystemExit(0 if record["status"] == "succeeded" else 1)


if __name__ == "__main__":
    main()
