"""Admission and cumulative-budget checks using synthetic local output only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory import release_launch as launch
from er_commons.response_inventory.release_spec import current_runtime_versions
from er_commons.response_inventory.release_storage import publish_container
from er_commons.response_inventory.release_workflow import ReleaseRun


@pytest.fixture
def context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, ReleaseRun]:
    """Replace only request loading; all accounting uses real synthetic files."""
    repo, data = tmp_path / "repo", tmp_path / "data"
    repo.mkdir()
    data.mkdir()
    request = repo / "request.json"
    request.write_text("{}")
    spec: dict[str, Any] = {
        "runtime_versions": current_runtime_versions(),
        "authorization": dict.fromkeys(
            ("execution", "finalization", "publication", "acceptance"), False
        ),
        "limits": {
            "workers": 1,
            "cpu_threads": 2,
            "max_seconds": 1800,
            "max_rss_bytes": 4294967296,
            "max_output_bytes": 2147483648,
            "min_free_bytes": 8589934592,
            "max_swap_growth_bytes": 0,
            "sample_seconds": 0.1,
            "disk_sample_seconds": 1.0,
            "termination_grace_seconds": 15.0,
        },
        "binding_freeze": {"path": "bindings.json", "sha256": "a" * 64},
        "selection_freeze": {"path": "selection.json", "sha256": "b" * 64},
        "repository_bindings": [],
    }
    root = data / "pipelines/test/working/05h"
    run = ReleaseRun(spec, "plan05hv1-" + "a" * 64, repo, data, root, 1)
    monkeypatch.setattr(launch, "open_run", lambda *args: run)
    monkeypatch.chdir(repo)
    return request, repo, data, run


def put(path: Path, size: int) -> None:
    """Create tiny retained output fixtures with known byte counts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_preview_false_authorizations_is_read_only(context: Any) -> None:
    """No directory creation or production execution occurs during preview."""
    request, repo, data, run = context
    packet = launch.build_launch_packet(request, repo, data)
    assert not run.root.parent.exists()
    assert packet["prior_bytes"] == dict.fromkeys(
        ("working", "cache", "supervisor", "published"), 0
    )
    assert f"ER_COMMONS_DATA_ROOT={data}" in packet["command"]
    assert packet["selection_freeze"] == run.spec["selection_freeze"]
    with pytest.raises(ValueError, match="authorization"):
        launch.launch_release(request, repo, data)
    assert not run.root.parent.exists()


def test_all_retained_namespaces_reduce_budget(context: Any) -> None:
    """Cache, attempts, incomplete releases and other plans all remain charged."""
    request, repo, data, run = context
    put(run.root / "old-plan/file", 11)
    put(run.root.parent / "cache/05h/old/file", 13)
    put(run.root.parent / "05h_execution_attempts/old/log", 17)
    put(run.root.parent.parent / "inventoryv1-partial/file", 19)
    put(run.root.parent / "05g/accepted/file", 1000)
    packet = launch.build_launch_packet(request, repo, data, operation="review")
    assert packet["prior_bytes"] == {"working": 11, "cache": 13, "supervisor": 17, "published": 19}
    assert packet["output_root"] == str(run.root.parent / "cache/05h")
    assert packet["supervisor_limits"]["max_output_bytes"] == 2147483648 - 47 - 65536


def test_symlink_accounting_rejected(context: Any, tmp_path: Path) -> None:
    """Output accounting must never follow a link into upstream payloads."""
    request, repo, data, run = context
    run.root.mkdir(parents=True)
    (run.root / "escape").symlink_to(tmp_path)
    with pytest.raises(ValueError, match="symlink"):
        launch.build_launch_packet(request, repo, data)


def test_publish_reserves_exact_final_copy(context: Any) -> None:
    """The outside monitored-tree copy is charged before production admission."""
    request, repo, data, run = context
    candidate = run.attempt_root / "finalized"
    publish_container(
        candidate,
        {"records/sample.json": b"{}\n"},
        plan_id=run.plan_id,
        semantic_digest="c" * 64,
        status="complete_with_limitations",
    )
    packet = launch.build_launch_packet(
        request, repo, data, operation="publish", candidate=candidate
    )
    expected = sum(path.stat().st_size for path in candidate.rglob("*") if path.is_file())
    assert packet["publication_reserve_bytes"] == expected
    assert packet["supervisor_limits"]["max_output_bytes"] == 2147483648 - expected - 65536
    with pytest.raises(ValueError, match="published inventory"):
        launch.build_launch_packet(request, repo, data, operation="accept", candidate=candidate)


def test_launch_uses_exact_limits_receipt_and_operation_gate(
    context: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Execution authorization cannot accidentally authorize finalization."""
    request, repo, data, run = context
    run.spec["authorization"]["execution"] = True
    with pytest.raises(ValueError, match="finalization authorization"):
        launch.launch_release(request, repo, data, operation="finalize")
    assert not run.root.exists()
    observed = {}

    def supervise(command: list[str], **kwargs: Any) -> dict[str, Any]:
        observed.update(command=command, **kwargs)
        return {"status": "succeeded"}

    monkeypatch.setattr(launch, "supervise", supervise)
    assert launch.launch_release(request, repo, data) == {"status": "succeeded"}
    receipt = run.root.parent / "05h_execution_attempts" / run.plan_id / "launch-001-prepare.json"
    packet = json.loads(receipt.read_bytes())
    assert observed["command"] == packet["command"]
    assert observed["limits"].max_output_bytes == packet["supervisor_limits"]["max_output_bytes"]
    with pytest.raises(FileExistsError):
        launch.launch_release(request, repo, data)


def test_exhausted_budget_writes_nothing(context: Any) -> None:
    """Admission failure preserves prior bytes and creates no supervisor records."""
    request, repo, data, run = context
    run.spec["authorization"]["execution"] = True
    run.spec["limits"]["max_output_bytes"] = 65536
    with pytest.raises(ValueError, match="budget exhausted"):
        launch.launch_release(request, repo, data)
    assert not run.root.parent.exists()


def test_resume_is_explicit_earlier_attempt(context: Any) -> None:
    """The exact named checkpoint enters the command and immutable launch receipt."""
    request, repo, data, _ = context
    packet = launch.build_launch_packet(request, repo, data, attempt=2, resume_from=1)
    assert packet["resume_from"] == 1
    index = packet["command"].index("--resume-from")
    assert packet["command"][index + 1] == "1"
    for previous in (True, 0, 2, 3):
        with pytest.raises(ValueError, match="earlier positive"):
            launch.build_launch_packet(request, repo, data, attempt=2, resume_from=previous)


def test_global_lock_blocks_another_worker(context: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Lock contention never invokes a second supervisor or writes a launch receipt."""
    request, repo, data, run = context
    run.spec["authorization"]["execution"] = True

    def locked(*args: Any) -> None:
        raise BlockingIOError

    monkeypatch.setattr(launch.fcntl, "flock", locked)
    with pytest.raises(ValueError, match="another Task 05H worker"):
        launch.launch_release(request, repo, data)
    logs = run.root.parent / "05h_execution_attempts"
    assert list(logs.iterdir()) == [logs / "single-worker.lock"]


def test_historical_release_is_not_recursively_accounted(context: Any) -> None:
    """A historical completion's distinct stage prevents traversal of its payloads."""
    request, repo, data, run = context
    historical = run.root.parent.parent / "inventoryv1-old"
    completion = historical / "records/completion.json"
    completion.parent.mkdir(parents=True)
    completion.write_text(json.dumps({"schema_version": "historical", "stage": "05g"}))
    (historical / "large-upstream-link").symlink_to(data)
    assert launch.build_launch_packet(request, repo, data)["prior_bytes"]["published"] == 0
