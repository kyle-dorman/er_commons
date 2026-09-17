"""Synthetic source-free integration of all four Task 05G stages and restart gates."""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.request
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from test_task05g_resolver import fixture, population

from er_commons.response_inventory import reference_replay_storage as storage
from er_commons.response_inventory import reference_replay_workflow as workflow
from er_commons.response_inventory.reference_replay_inputs import ReplayInputs


@pytest.fixture
def run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> workflow.ReplayRun:
    """Substitute only accepted-input loading; exercise actual resolver and validators."""
    args = fixture()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "population.json").write_text(json.dumps(population(args)))
    inputs = ReplayInputs(
        **{key: value for key, value in args.items() if key != "activity"},
        baseline_links=[],
        dependencies=args["activity"]["input_refs"],
        correspondence={"target_mapping": [], "authorized_added_target_ids": ["target-1"]},
    )
    monkeypatch.setattr(workflow, "_load_inputs", lambda run: inputs)
    return workflow.ReplayRun(
        spec={
            "authorization": {"replay": True},
            "output_relative_root": "pipelines/working/05g",
            "population_freeze": "population.json",
            "policy": "accepted_05f_rules_with_verified_final_f1_substitution",
        },
        digest="f" * 64,
        repository_root=repo,
        artifact_root=tmp_path / "data",
    )


def test_all_stages_close_without_source_or_network_access(
    run: workflow.ReplayRun, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use pure synthetic records, real schemas and source-access tripwires."""
    original = Path.open

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".safetensors", ".pt"}:
            pytest.fail(f"forbidden source/model access: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network access"))
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("HTTP access"))
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("renderer/model subprocess")
    )
    assert workflow.prepare_replay(run)["status"] == "prepared"
    result = workflow.build_replay(run)
    assert result["acceptance_published"] is False
    assert result["task05h_execution_authorized"] is False
    comparison = workflow.compare_replay(run)
    assert comparison["status"] == "comparison_complete"
    assert workflow.validate_replay(run)["status"] == "valid"
    for stage in ("prepared", "resolved", "candidate", "comparison"):
        assert (run.stage_root(stage) / "completion.json").is_file()
    assert not list(run.root.rglob("accepted.json"))


def test_completed_repeat_is_read_only(run: workflow.ReplayRun) -> None:
    """Deterministic repeated preparation, build, comparison and validation never write."""
    operations = (
        workflow.prepare_replay,
        workflow.build_replay,
        workflow.compare_replay,
        workflow.validate_replay,
    )
    initial = [operation(run) for operation in operations]
    before = {
        path: (path.stat().st_mtime_ns, path.read_bytes())
        for path in run.root.rglob("*")
        if path.is_file()
    }
    assert [operation(run) for operation in operations] == initial
    assert {
        path: (path.stat().st_mtime_ns, path.read_bytes())
        for path in run.root.rglob("*")
        if path.is_file()
    } == before


def test_interrupted_resolution_resumes_exact_predecessor_in_new_attempt(
    run: workflow.ReplayRun,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the failed stage and reuse only its verified complete prepared predecessor."""
    workflow.prepare_replay(run)
    predecessor = run.stage_root("prepared") / "completion.json"
    before = (predecessor.stat().st_mtime_ns, predecessor.read_bytes())
    original = storage._write_owned

    def interrupt(path: Path, data: bytes) -> None:
        if path.is_relative_to(run.stage_root("resolved")) and path.name != "failure.json":
            raise KeyboardInterrupt("synthetic resolved-stage interruption")
        original(path, data)

    monkeypatch.setattr(storage, "_write_owned", interrupt)
    with pytest.raises(KeyboardInterrupt):
        workflow.build_replay(run)
    assert (run.stage_root("resolved") / "failure.json").is_file()
    assert not (run.stage_root("resolved") / "completion.json").exists()
    with pytest.raises(ValueError, match="incomplete"):
        workflow.build_replay(run)
    monkeypatch.setattr(storage, "_write_owned", original)
    resumed = replace(run, attempt=2, resume_from=1)
    result = workflow.build_replay(resumed)
    assert result["candidate_id"] == run.candidate_id
    assert result["candidate_root"].endswith("attempt-002")
    assert not resumed.stage_root("prepared").exists()
    assert workflow.compare_replay(resumed)["status"] == "comparison_complete"
    assert workflow.validate_replay(resumed)["status"] == "valid"
    assert (predecessor.stat().st_mtime_ns, predecessor.read_bytes()) == before
    assert (run.stage_root("resolved") / "failure.json").is_file()


@pytest.mark.parametrize(
    "operation",
    [
        workflow.prepare_replay,
        workflow.build_replay,
        workflow.compare_replay,
        workflow.validate_replay,
    ],
)
def test_unauthorized_stages_reject_before_input_loading(
    run: workflow.ReplayRun,
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
) -> None:
    """Validation cannot recompute from accepted input without replay approval."""
    run.spec["authorization"]["replay"] = False
    monkeypatch.setattr(workflow, "_load_inputs", lambda *a: pytest.fail("loaded accepted inputs"))
    with pytest.raises(ValueError, match="not authorized"):
        operation(run)
    assert not run.root.exists()


def test_complete_predecessor_tamper_blocks_resume(run: workflow.ReplayRun) -> None:
    """A selected checkpoint with changed bytes is an error, never a silent rebuild."""
    workflow.prepare_replay(run)
    (run.stage_root("prepared") / "prepared_inputs.json").write_text("{}")
    with pytest.raises(ValueError, match="mismatch"):
        workflow.build_replay(replace(run, attempt=2, resume_from=1))
    assert not run.stage_root("candidate", 2).exists()


def test_missing_candidate_prevents_comparison_and_validation(run: workflow.ReplayRun) -> None:
    """Both terminal checks need an exact selected complete candidate."""
    workflow.prepare_replay(run)
    for operation in (workflow.compare_replay, workflow.validate_replay):
        with pytest.raises(ValueError, match="complete selected candidate"):
            operation(run)
    assert not run.stage_root("comparison").exists()
