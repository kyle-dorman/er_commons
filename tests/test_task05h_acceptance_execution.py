"""Acceptance designation follows successful, exactly associated supervision."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory import release_launch as launch
from er_commons.response_inventory.release_publication import accept_inventory, publish_inventory
from er_commons.response_inventory.release_storage import encode, publish_container
from er_commons.response_inventory.release_workflow import ReleaseRun


def receipt(packet: dict[str, Any], status: str = "succeeded") -> dict[str, Any]:
    """Build only the terminal fields that the maintained supervisor produces."""
    return {
        "status": status,
        "returncode": 0 if status == "succeeded" else 1,
        "command": packet["command"],
        "limits": packet["supervisor_limits"],
        "attempt_root": packet["attempt_root"],
        "output_root": packet["output_root"],
        "elapsed_seconds": 0.1,
        "peak_rss_bytes": 1,
        "peak_swap_growth_bytes": 0,
        "peak_output_bytes": 1,
    }


@pytest.fixture
def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    """Create a synthetic published release with successful publication evidence."""
    repo, data = tmp_path / "repo", tmp_path / "data"
    repo.mkdir()
    data.mkdir()
    request = repo / "request.json"
    request.write_text("{}")
    spec: dict[str, Any] = {
        "authorization": dict.fromkeys(
            ("execution", "finalization", "publication", "acceptance"), True
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
    run = ReleaseRun(spec, "plan05hv1-" + "a" * 64, repo, data, data / "task05/working/05h", 1)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launch, "open_run", lambda *args: run)
    source = run.attempt_root / "finalized"
    completion = publish_container(
        source,
        {"records/task07_task08_handoff.json": b"{}\n"},
        plan_id=run.plan_id,
        semantic_digest="b" * 64,
        status="complete_with_limitations",
    )
    final_packet = launch.build_launch_packet(request, repo, data, operation="finalize")
    Path(final_packet["launch_packet_path"]).parent.mkdir(parents=True)
    Path(final_packet["launch_packet_path"]).write_bytes(encode(final_packet))
    final_attempt = Path(final_packet["attempt_root"])
    final_attempt.mkdir()
    (final_attempt / "execution.json").write_bytes(encode(receipt(final_packet)))
    (final_attempt / "command.log").write_bytes(encode({"completion": completion}))
    packet = launch.build_launch_packet(request, repo, data, operation="publish", candidate=source)
    published = publish_inventory(source, run.root.parent.parent, spec, plan_id=run.plan_id)
    Path(packet["launch_packet_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(packet["launch_packet_path"]).write_bytes(encode(packet))
    Path(packet["attempt_root"]).mkdir()
    (Path(packet["attempt_root"]) / "execution.json").write_bytes(encode(receipt(packet)))
    return request, repo, data, run, Path(published["inventory_root"])


def supervisor(
    monkeypatch: pytest.MonkeyPatch, run: ReleaseRun, inventory: Path, status: str = "succeeded"
) -> None:
    """Execute acceptance preparation, then report the specified terminal outcome."""

    def execute(command: list[str], **kwargs: Any) -> dict[str, Any]:
        accept_inventory(
            inventory,
            run.root,
            run.spec,
            plan_id=run.plan_id,
            accepted_by="Curator",
            accepted_at="2026-09-17T20:00:00Z",
        )
        assert not (run.root / "accepted.json").exists()
        packet = {
            "command": command,
            "supervisor_limits": asdict(kwargs["limits"]),
            "attempt_root": str(kwargs["attempt_root"]),
            "output_root": str(kwargs["output_root"]),
        }
        result = receipt(packet, status)
        kwargs["attempt_root"].mkdir()
        (kwargs["attempt_root"] / "execution.json").write_bytes(encode(result))
        return result

    monkeypatch.setattr(launch, "supervise", execute)


def invoke(prepared: tuple[Any, ...]) -> dict[str, Any]:
    """Launch the exact synthetic acceptance under test."""
    request, repo, data, _, inventory = prepared
    return launch.launch_release(
        request,
        repo,
        data,
        operation="accept",
        candidate=inventory,
        accepted_by="Curator",
        accepted_at="2026-09-17T20:00:00Z",
    )


def test_success_designates_after_terminal_and_identical_repeat_is_noop(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, run, inventory = prepared
    supervisor(monkeypatch, run, inventory)
    result = invoke(prepared)
    pointer = run.root / "accepted.json"
    assert result["acceptance"] == json.loads(pointer.read_bytes())
    before = pointer.stat().st_mtime_ns
    assert invoke(prepared) == result
    assert pointer.stat().st_mtime_ns == before
    evidence = run.root / "acceptances" / result["acceptance"]["acceptance_id"] / "execution.json"
    assert json.loads(evidence.read_bytes())["execution"]["accept"]["operation"] == "accept"


def test_failure_after_worker_output_never_designates(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, run, inventory = prepared
    supervisor(monkeypatch, run, inventory, "failed")
    assert invoke(prepared)["status"] == "failed"
    assert not (run.root / "accepted.json").exists()
    with pytest.raises(ValueError, match="did not complete"):
        invoke(prepared)
    assert not (run.root / "accepted.json").exists()


def test_changed_request_cannot_finish_interrupted_designation(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, _, _, run, inventory = prepared
    supervisor(monkeypatch, run, inventory)
    from er_commons.response_inventory import release_publication

    original = release_publication.designate_acceptance

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        raise InterruptedError("after supervisor success")

    monkeypatch.setattr(release_publication, "designate_acceptance", interrupted)
    with pytest.raises(InterruptedError):
        invoke(prepared)
    monkeypatch.setattr(release_publication, "designate_acceptance", original)
    request.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="request changed"):
        invoke(prepared)
    assert not (run.root / "accepted.json").exists()


def test_mismatched_publication_source_blocks_designation(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, _, run, inventory = prepared
    supervisor(monkeypatch, run, inventory)
    path = run.root.parent / "05h_execution_attempts" / run.plan_id / "launch-001-publish.json"
    packet = json.loads(path.read_bytes())
    packet["candidate_root"] = str(run.attempt_root / "other")
    path.write_bytes(encode(packet))
    with pytest.raises(ValueError, match="different finalized"):
        invoke(prepared)
    assert not (run.root / "accepted.json").exists()


def test_designated_inventory_rejects_conflicting_acceptance(
    prepared: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later attribution cannot silently replace the designated acceptance."""
    _, _, _, run, inventory = prepared
    supervisor(monkeypatch, run, inventory)
    invoke(prepared)
    before = (run.root / "accepted.json").read_bytes()
    with pytest.raises(ValueError, match="supersession"):
        accept_inventory(
            inventory,
            run.root,
            run.spec,
            plan_id=run.plan_id,
            accepted_by="Different curator",
            accepted_at="2026-09-17T20:00:00Z",
        )
    assert (run.root / "accepted.json").read_bytes() == before
