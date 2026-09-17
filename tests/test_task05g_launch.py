"""Synthetic-only launch packet, gate, retry-budget and supervisor tests."""

from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory import reference_replay_launch as launch
from er_commons.response_inventory.reference_replay_spec import ReplayLimits


@pytest.fixture
def synthetic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, Any]]:
    spec: dict[str, Any] = {
        "output_relative_root": "pipelines/working/05g",
        "inputs": {"synthetic": True},
        "repository_bindings": [],
        "authorization": {"replay": False},
        "limits": ReplayLimits().model_dump(),
    }
    monkeypatch.setattr(launch, "load_replay_spec", lambda *args: (spec, "a" * 64))
    (tmp_path / "spec.json").write_text("{}\n")
    monkeypatch.chdir(tmp_path)
    return tmp_path, spec


def test_packet_is_read_only_and_overrides_all_threads(
    synthetic: tuple[Path, dict[str, Any]],
) -> None:
    root, _ = synthetic
    packet = launch.build_launch_packet(root / "spec.json", root, root / "data")
    assert not (root / "data").exists()
    assert packet["command"][0] == "/usr/bin/env"
    for key in launch.THREAD_ENVIRONMENT:
        assert f"{key}=2" in packet["command"]
    output = Path(packet["output_root"])
    attempt = Path(packet["attempt_root"])
    assert not attempt.is_relative_to(output)
    assert not output.is_relative_to(attempt)
    assert packet["supervisor_limits"]["max_seconds"] == 1800
    assert packet["supervisor_limits"]["max_rss_bytes"] == 4 * 1024**3
    assert packet["supervisor_limits"]["min_free_bytes"] == 8 * 1024**3
    assert packet["supervisor_limits"]["max_swap_growth_bytes"] == 0


def test_unauthorized_launch_never_creates_dirs(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = synthetic
    monkeypatch.setattr(launch, "supervise", lambda *args, **kwargs: pytest.fail("launched"))
    with pytest.raises(ValueError, match="authorization"):
        launch.launch_replay(root / "spec.json", root, root / "data")
    assert not (root / "data").exists()


def test_all_prior_attempt_logs_reduce_supervisor_budget(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, spec = synthetic
    spec["authorization"]["replay"] = True
    old = root / "data/pipelines/working/05g_execution_attempts/older-plan/attempt-001"
    old.mkdir(parents=True)
    (old / "command.log").write_bytes(b"x" * 1234)
    observed: dict[str, Any] = {}

    def supervisor(command: list[str], **kwargs: Any) -> dict[str, Any]:
        observed.update(kwargs)
        assert command[0] == "/usr/bin/env"
        return {"status": "succeeded"}

    monkeypatch.setattr(launch, "supervise", supervisor)
    assert launch.launch_replay(root / "spec.json", root, root / "data")["status"] == "succeeded"
    assert observed["limits"].max_output_bytes == 2 * 1024**3 - 1234
    assert (old / "command.log").stat().st_size == 1234


def test_low_synthetic_budget_stops_before_launch(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, spec = synthetic
    spec["authorization"]["replay"] = True
    spec["limits"]["max_output_bytes"] = 65540
    output = root / "data/pipelines/working/05g"
    output.mkdir(parents=True)
    (output / "failed-attempt.json").write_bytes(b"preserved")
    monkeypatch.setattr(launch, "supervise", lambda *args, **kwargs: pytest.fail("launched"))
    with pytest.raises(ValueError, match="budget exhausted"):
        launch.launch_replay(root / "spec.json", root, root / "data")
    assert not (output / "completion.json").exists()
    assert (output / "failed-attempt.json").read_bytes() == b"preserved"


def test_supervisor_failure_is_not_promoted(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, spec = synthetic
    spec["authorization"]["replay"] = True
    monkeypatch.setattr(
        launch,
        "supervise",
        lambda *args, **kwargs: {"status": "failed", "reason": "budget_exceeded:peak_rss_bytes"},
    )
    result = launch.launch_replay(root / "spec.json", root, root / "data")
    assert result["status"] == "failed"
    assert not list((root / "data").rglob("completion.json"))


def test_retry_cannot_reuse_existing_attempt(synthetic: tuple[Path, dict[str, Any]]) -> None:
    root, spec = synthetic
    spec["authorization"]["replay"] = True
    packet = launch.build_launch_packet(root / "spec.json", root, root / "data")
    Path(packet["attempt_root"]).mkdir(parents=True)
    with pytest.raises(FileExistsError):
        launch.launch_replay(root / "spec.json", root, root / "data")


def test_accounting_rejects_symlinks(synthetic: tuple[Path, dict[str, Any]]) -> None:
    root, _ = synthetic
    output = root / "data/pipelines/working/05g"
    output.mkdir(parents=True)
    (output / "hidden").symlink_to(root)
    with pytest.raises(ValueError, match="symlink"):
        launch.build_launch_packet(root / "spec.json", root, root / "data")


@pytest.mark.parametrize("attempt", [0, -1, True])
def test_attempt_requires_positive_integer(
    synthetic: tuple[Path, dict[str, Any]], attempt: int
) -> None:
    root, _ = synthetic
    with pytest.raises(ValueError, match="positive integer"):
        launch.build_launch_packet(root / "spec.json", root, root / "data", attempt=attempt)


def test_single_worker_lock_blocks_concurrent_launch(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    import fcntl

    root, spec = synthetic
    spec["authorization"]["replay"] = True
    attempts = root / "data/pipelines/working/05g_execution_attempts"
    attempts.mkdir(parents=True)
    monkeypatch.setattr(launch, "supervise", lambda *args, **kwargs: pytest.fail("launched"))
    with (attempts / "single-worker.lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="another Task 05G worker"):
            launch.launch_replay(root / "spec.json", root, root / "data")


def test_retry_packet_binds_exact_worker_attempt_and_resume(
    synthetic: tuple[Path, dict[str, Any]],
) -> None:
    import hashlib

    root, _ = synthetic
    packet = launch.build_launch_packet(
        root / "spec.json", root, root / "data", attempt=3, resume_from=1
    )
    command = packet["command"]
    assert command[command.index("--attempt") + 1] == "3"
    assert command[command.index("--resume-from") + 1] == "1"
    assert "--resume-from 1" in packet["launch_command"][-1]
    assert packet["request_sha256"] == hashlib.sha256(b"{}\n").hexdigest()
    for name in ("candidate_root", "comparison_root", "prepared_root"):
        assert packet[name].endswith("/attempt-003")
    assert packet["resolved_root"].endswith("/attempt-003/resolved")


@pytest.mark.parametrize("resume_from", [0, 2, 3, True])
def test_resume_must_name_earlier_attempt(
    synthetic: tuple[Path, dict[str, Any]],
    resume_from: int,
) -> None:
    root, _ = synthetic
    with pytest.raises(ValueError, match="earlier positive"):
        launch.build_launch_packet(
            root / "spec.json", root, root / "data", attempt=2, resume_from=resume_from
        )


def test_immutable_packet_precedes_supervisor_and_survives_failure(
    synthetic: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    root, spec = synthetic
    spec["authorization"]["replay"] = True
    packet = launch.build_launch_packet(root / "spec.json", root, root / "data")
    path = Path(packet["launch_packet_path"])

    def failed_supervisor(*args: Any, **kwargs: Any) -> dict[str, Any]:
        receipt = json.loads(path.read_bytes())
        assert receipt["request_text"] == "{}\n"
        assert receipt["command"] == packet["command"]
        raise RuntimeError("synthetic supervisor failure")

    monkeypatch.setattr(launch, "supervise", failed_supervisor)
    with pytest.raises(RuntimeError, match="synthetic supervisor failure"):
        launch.launch_replay(root / "spec.json", root, root / "data")
    preserved = path.read_bytes()
    with pytest.raises(FileExistsError):
        launch.launch_replay(root / "spec.json", root, root / "data")
    assert path.read_bytes() == preserved


def test_oversized_request_packet_rejected_without_writes(
    synthetic: tuple[Path, dict[str, Any]],
) -> None:
    root, _ = synthetic
    (root / "spec.json").write_text(" " * 65537)
    with pytest.raises(ValueError, match="64 KiB"):
        launch.build_launch_packet(root / "spec.json", root, root / "data")
    assert not (root / "data").exists()


@pytest.mark.parametrize("operation", launch.OPERATIONS)
def test_each_public_operation_uses_supervised_worker(
    synthetic: tuple[Path, dict[str, Any]],
    operation: str,
) -> None:
    root, _ = synthetic
    packet = launch.build_launch_packet(
        root / "spec.json",
        root,
        root / "data",
        operation=operation,
    )
    assert packet["operation"] == operation
    command = packet["command"]
    assert command[command.index("--operation") + 1] == operation
    assert "er_commons.response_inventory.reference_replay_workflow" in command
    assert "--execute-stages" in command
    assert (
        "er_commons.document_publication.background_execution"
        in packet["maintained_supervisor_command"]
    )
    assert f"--operation {operation}" in packet["launch_command"][-1]


def test_unknown_operation_rejected_before_load(
    synthetic: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = synthetic
    monkeypatch.setattr(launch, "load_replay_spec", lambda *args: pytest.fail("loaded spec"))
    with pytest.raises(ValueError, match="unknown supervised"):
        launch.build_launch_packet(root / "spec.json", root, root / "data", operation="unbounded")
    assert not (root / "data").exists()
