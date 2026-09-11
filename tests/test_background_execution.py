"""Synthetic command supervision without PDF/model/network access."""

import json
import sys
from pathlib import Path

import psutil  # type: ignore[import-untyped]
import pytest

from er_commons.document_publication.background_execution import ExecutionLimits, supervise


def run(tmp_path: Path, script: str, **overrides: float | int) -> dict:
    """Give each synthetic command a separate output and diagnostic namespace."""
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    values = dict(
        max_seconds=5,
        max_rss_bytes=2**30,
        max_output_bytes=2**20,
        min_free_bytes=0,
        max_swap_growth_bytes=2**40,
        sample_seconds=0.01,
        disk_sample_seconds=0.02,
        termination_grace_seconds=0.1,
    )
    values.update(overrides)
    return supervise(
        [sys.executable, "-c", script],
        attempt_root=tmp_path / "attempt",
        output_root=output,
        limits=ExecutionLimits(**values),
    )


@pytest.mark.parametrize("code, status", [(0, "succeeded"), (7, "failed")])
def test_command_terminal_status(tmp_path: Path, code: int, status: str) -> None:
    record = run(tmp_path, f"print('retained log'); raise SystemExit({code})")
    assert record["status"] == status
    assert record["returncode"] == code
    assert "retained log" in (tmp_path / "attempt/command.log").read_text()
    assert json.loads((tmp_path / "attempt/execution.json").read_text()) == record


def test_environment_is_offline_and_four_threads(tmp_path: Path) -> None:
    record = run(
        tmp_path,
        "import os; assert os.environ['HF_HUB_OFFLINE']=='1'; "
        "assert os.environ['OMP_NUM_THREADS']=='4'; "
        "assert os.environ['VECLIB_MAXIMUM_THREADS']=='4'",
    )
    assert record["status"] == "succeeded"


@pytest.mark.parametrize(
    "limit, value, reason",
    [
        ("max_seconds", 0.05, "elapsed_seconds"),
        ("max_rss_bytes", 1, "peak_rss_bytes"),
        ("max_output_bytes", 10, "peak_output_bytes"),
    ],
)
def test_budget_stops_child(tmp_path: Path, limit: str, value: float, reason: str) -> None:
    record = run(tmp_path, "import time; time.sleep(10)", **{limit: value})
    assert record["status"] == "failed"
    assert record["reason"] == f"budget_exceeded:{reason}"
    assert not record["surviving_pids"]


def test_swap_growth_stops_child(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    observations = iter([0, 1])
    monkeypatch.setattr(psutil, "swap_memory", lambda: SimpleNamespace(used=next(observations, 1)))
    record = run(tmp_path, "import time; time.sleep(10)", max_swap_growth_bytes=0)
    assert record["reason"] == "budget_exceeded:peak_swap_growth_bytes"


def test_attempt_is_never_overwritten(tmp_path: Path) -> None:
    run(tmp_path, "pass")
    original = (tmp_path / "attempt/execution.json").read_bytes()
    with pytest.raises(FileExistsError):
        run(tmp_path, "raise AssertionError('must not run')")
    assert (tmp_path / "attempt/execution.json").read_bytes() == original


def test_detached_descendant_is_killed(tmp_path: Path) -> None:
    pidfile = tmp_path / "detached.pid"
    detached = (
        "import os,time,signal; from pathlib import Path; "
        f"Path({str(pidfile)!r}).write_text(str(os.getpid())); "
        "signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)"
    )
    script = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{detached!r}],start_new_session=True); "
        "time.sleep(30)"
    )
    record = run(tmp_path, script, max_seconds=0.5)
    assert record["reason"] == "budget_exceeded:elapsed_seconds"
    pid = int(pidfile.read_text())
    assert not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
    assert not record["surviving_pids"]


def test_partial_output_is_counted(tmp_path: Path) -> None:
    output_file = tmp_path / "output/partial.bin"
    record = run(
        tmp_path,
        f"from pathlib import Path; Path({str(output_file)!r}).write_bytes(b'x'*20000)",
        max_output_bytes=10000,
    )
    assert record["reason"] == "budget_exceeded:peak_output_bytes"
    assert output_file.stat().st_size == 20000


def test_insufficient_disk_prevents_launch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="initial free disk"):
        run(tmp_path, "raise AssertionError('must not run')", min_free_bytes=2**60)
    assert not (tmp_path / "attempt").exists()


def test_nonfinite_limit_prevents_launch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid execution limit"):
        run(tmp_path, "pass", max_seconds=float("inf"))
    assert not (tmp_path / "attempt").exists()


def test_status_never_records_inherited_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HF_TOKEN", "synthetic-sensitive-value")
    record = run(tmp_path, "pass")
    assert "synthetic-sensitive-value" not in json.dumps(record)


def test_internal_output_links_are_not_double_counted(tmp_path: Path) -> None:
    from er_commons.document_publication.background_execution import _tree_bytes

    output = tmp_path / "output"
    (output / "plans/ranges").mkdir(parents=True)
    (output / "plans/ranges/partial").write_bytes(b"data")
    (output / "ranges").symlink_to(output / "plans/ranges", target_is_directory=True)
    assert _tree_bytes(output) == 4
    assert run(tmp_path, "pass")["status"] == "succeeded"


def test_escaping_link_preserves_terminal_failure(tmp_path: Path) -> None:
    link = tmp_path / "output/escaped"
    script = f"from pathlib import Path; Path({str(link)!r}).symlink_to({str(tmp_path)!r})"
    record = run(tmp_path, script)
    assert record["status"] == "failed"
    assert "escapes accounting root" in record["reason"]
    assert json.loads((tmp_path / "attempt/execution.json").read_text()) == record
