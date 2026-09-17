"""Source-free v6 dispatch, operational identity, and later publication gate controls."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import ValidationError
from test_task05g_workflow import run as run_fixture

from er_commons.response_inventory import cli
from er_commons.response_inventory import reference_replay_acceptance as acceptance
from er_commons.response_inventory import reference_replay_workflow as workflow
from er_commons.response_inventory.reference_replay_spec import (
    SCHEMA_PATH,
    ReferenceReplaySpec,
    load_replay_spec,
    replay_identity,
)
from er_commons.response_inventory.reference_replay_storage import read_checkpoint

run = run_fixture
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/brisbane_baylands_2025_feir_task05g_replay_v6.json"


def test_review_ready_request_is_strict_and_publication_gated() -> None:
    """The real request can validate without touching a single external artifact."""
    payload = json.loads(CONFIG.read_text())
    schema = json.loads((ROOT / SCHEMA_PATH).read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    ReferenceReplaySpec.model_validate_json(CONFIG.read_bytes())
    assert payload["authorization"]["finalization"] is False
    assert payload["authorization"]["acceptance"] is False
    phase2 = json.loads((ROOT / "docs/specs/task05g_phase2_launch_packet.json").read_text())
    assert phase2["authorization"] == {"replay": False, "finalization": False, "acceptance": False}


@pytest.mark.parametrize("kind", ["path", "policy", "resources", "source", "unknown"])
def test_request_rejects_scope_expansion(kind: str) -> None:
    """Invalid routes, relaxed limits and undeclared behavior cannot enter a v6 request."""
    data = json.loads(CONFIG.read_text())
    if kind == "path":
        data["inputs"]["task06h_pointer"] = "../accepted.json"
    elif kind == "policy":
        data["policy"] = "fuzzy_fallback"
    elif kind == "resources":
        data["limits"]["max_swap_growth_bytes"] = 1
    elif kind == "source":
        data["source_pdf_access"] = True
    else:
        data["guess_missing_targets"] = True
    with pytest.raises((ValueError, ValidationError)):
        ReferenceReplaySpec.model_validate_json(json.dumps(data))


def test_operational_approval_does_not_change_candidate_identity() -> None:
    """Later approval changes cannot make the already reviewed candidate unreachable."""
    before = json.loads(CONFIG.read_text())
    after = copy.deepcopy(before)
    after["authorization"] = {"replay": True, "finalization": True, "acceptance": True}
    assert replay_identity(before) == replay_identity(after)
    after["inputs"]["task05f"]["semantic_digest"] = "0" * 64
    assert replay_identity(before) != replay_identity(after)


def test_v6_writer_rejects_missing_code_binding(tmp_path: Path) -> None:
    """A stale owned-code inventory stops before any accepted input is read."""
    data = json.loads(CONFIG.read_text())
    data["repository_bindings"] = data["repository_bindings"][:-1]
    path = tmp_path / "request.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="inventory differs"):
        load_replay_spec(path, ROOT)


@pytest.mark.parametrize("command", ["prepare-05g", "build", "compare-05g", "validate-05g"])
def test_public_commands_use_supervisor(
    command: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No documented replay command can bypass the exclusive resource supervisor."""
    from er_commons.response_inventory import reference_replay_launch as launch

    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(cli, "_is_reference_replay", lambda path: True)
    monkeypatch.setattr(
        workflow, "open_run", lambda *a, **k: workflow.ReplayRun({}, "a" * 64, ROOT, tmp_path, 2, 1)
    )
    observed: list[str] = []

    def supervised(*args: Any, **kwargs: Any) -> dict[str, Any]:
        observed.append(kwargs["operation"])
        assert kwargs["attempt"] == 2 and kwargs["resume_from"] == 1
        return {"status": "synthetic_supervised"}

    monkeypatch.setattr(launch, "launch_replay", supervised)
    assert (
        cli.main([command, "--run-spec", str(CONFIG), "--attempt", "2", "--resume-from", "1"]) == 0
    )
    assert observed == [
        {
            "prepare-05g": "prepare",
            "build": "build",
            "compare-05g": "compare",
            "validate-05g": "validate",
        }[command]
    ]


def _reviews(run: workflow.ReplayRun) -> tuple[Path, Path]:
    """Create exact synthetic quality/decision receipts over all changed mention IDs."""
    inputs = workflow._load_inputs(run)
    candidate = read_checkpoint(
        run.stage_root("candidate"), workflow._bindings(run, "candidate", inputs.dependencies)
    )
    comparison = read_checkpoint(
        run.stage_root("comparison"), workflow._bindings(run, "comparison", inputs.dependencies)
    )
    common = {
        "candidate_id": run.candidate_id,
        "run_spec_sha256": run.digest,
        "candidate_checkpoint_id": candidate["checkpoint_id"],
        "comparison_checkpoint_id": comparison["checkpoint_id"],
        "material_findings": [],
        "reviewer": "synthetic-reviewer",
    }
    quality = run.root / "quality-input.json"
    review = run.root / "review-input.json"
    quality.write_text(json.dumps({**common, "status": "passed"}))
    review.write_text(
        json.dumps(
            {
                **common,
                "decision": "approved",
                "reviewed_mention_ids": ["mention-1"],
                "limitations_acknowledged": True,
            }
        )
    )
    return quality, review


def test_separate_finalization_acceptance_and_exact_repeat(
    run: workflow.ReplayRun, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A synthetic accepted candidate keeps its bytes and idempotent adjacent pointer."""
    run.spec["authorization"].update(finalization=True, acceptance=True)
    workflow.build_replay(run)
    workflow.compare_replay(run)
    monkeypatch.setattr(acceptance, "_load_inputs", workflow._load_inputs)
    monkeypatch.setattr(acceptance, "_execution_receipt", lambda selected: {"synthetic": "passed"})
    quality, review = _reviews(run)
    first = acceptance.finalize_replay(run, quality, review)
    assert acceptance.finalize_replay(run, quality, review) == first
    selected = run.stage_root("candidate")
    before = {p: p.read_bytes() for p in selected.rglob("*") if p.is_file()}
    result = acceptance.accept_replay(
        run, selected, review, accepted_by="test-user", accepted_at="2026-09-17T12:00:00+00:00"
    )
    assert result["task05h_execution_authorized"] is False
    assert (
        acceptance.accept_replay(
            run, selected, review, accepted_by="test-user", accepted_at="2026-09-17T12:00:00+00:00"
        )
        == result
    )
    assert before == {p: p.read_bytes() for p in selected.rglob("*") if p.is_file()}
    with pytest.raises((ValueError, FileExistsError)):
        acceptance.accept_replay(
            run,
            selected,
            review,
            accepted_by="different-user",
            accepted_at="2026-09-17T12:00:00+00:00",
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision", "rejected"),
        ("reviewed_mention_ids", []),
        ("limitations_acknowledged", False),
        ("material_findings", ["open"]),
        ("candidate_checkpoint_id", "wrong"),
    ],
)
def test_finalization_rejects_conflicting_or_incomplete_review(
    run: workflow.ReplayRun, monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    """Review closure is semantic and cannot be replaced by a single approved flag."""
    run.spec["authorization"]["finalization"] = True
    workflow.build_replay(run)
    workflow.compare_replay(run)
    monkeypatch.setattr(acceptance, "_load_inputs", workflow._load_inputs)
    monkeypatch.setattr(
        acceptance,
        "_execution_receipt",
        lambda r: pytest.fail("read execution before review closure"),
    )
    quality, review = _reviews(run)
    record = json.loads(review.read_text())
    record[field] = value
    review.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        acceptance.finalize_replay(run, quality, review)
    assert not (run.root / "finalizations").exists()


def test_later_gates_are_closed_before_any_input_read(
    run: workflow.ReplayRun, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase 2 cannot publish a finalization or acceptance via an unreviewed path."""
    run.spec["authorization"].update(finalization=False, acceptance=False)
    monkeypatch.setattr(acceptance, "_load_inputs", lambda r: pytest.fail("input read"))
    with pytest.raises(ValueError, match="not authorized"):
        acceptance.finalize_replay(run, Path("absent.json"), Path("absent.json"))
    with pytest.raises(ValueError, match="not authorized"):
        acceptance.accept_replay(
            run, Path("absent"), Path("absent.json"), accepted_by="test", accepted_at="bad"
        )


@pytest.mark.parametrize(
    "mutation", [None, "status", "command", "limits", "output", "survivor", "request"]
)
def test_original_execution_receipt_is_bound_and_resource_checked(
    tmp_path: Path, mutation: str | None
) -> None:
    """Actual receipt verifier rejects failed, mismatched, loose or incomplete supervision."""
    import hashlib

    spec = json.loads(CONFIG.read_text())
    spec["authorization"]["replay"] = True
    selected = workflow.ReplayRun(spec, replay_identity(spec), ROOT, tmp_path)
    request = json.dumps(spec)
    limits = {
        key: value for key, value in spec["limits"].items() if key not in {"workers", "cpu_threads"}
    }
    command = ["synthetic-command", "--attempt", "1"]
    packet = {
        "request_text": request,
        "request_sha256": hashlib.sha256(request.encode()).hexdigest(),
        "spec_sha256": selected.digest,
        "command": command,
        "supervisor_limits": limits,
        "prior_supervisor_bytes": 0,
    }
    execution_root = (
        selected.root.parent / "05g_execution_attempts" / selected.digest / "attempt-001"
    )
    execution_root.mkdir(parents=True)
    packet_path = selected.root / "plans" / selected.digest / "launch-attempt-001.json"
    packet_path.parent.mkdir(parents=True)
    record = {
        "status": "succeeded",
        "returncode": 0,
        "command": command,
        "limits": limits.copy(),
        "output_root": str(selected.root),
        "attempt_root": str(execution_root),
        "elapsed_seconds": 1.0,
        "peak_rss_bytes": 1024,
        "peak_swap_growth_bytes": 0,
        "peak_output_bytes": 2048,
        "surviving_pids": [],
    }
    if mutation == "status":
        record["status"] = "failed"
    elif mutation == "command":
        record["command"] = ["different-command"]
    elif mutation == "limits":
        record["limits"]["max_seconds"] = 3600
    elif mutation == "output":
        record["peak_output_bytes"] = limits["max_output_bytes"] + 1
    elif mutation == "survivor":
        record["surviving_pids"] = [42]
    elif mutation == "request":
        packet["request_text"] = "{}"
    packet_path.write_text(json.dumps(packet))
    (execution_root / "execution.json").write_text(json.dumps(record))
    if mutation is None:
        assert acceptance._execution_receipt(selected)["supervisor"] == record
    else:
        with pytest.raises(ValueError):
            acceptance._execution_receipt(selected)


@pytest.mark.parametrize("command", ["prepare-05g", "build", "compare-05g", "validate-05g"])
def test_public_supervisor_failure_returns_nonzero(
    command: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A terminal resource failure must not become shell success at the public boundary."""
    from er_commons.response_inventory import reference_replay_launch as launch

    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(cli, "_is_reference_replay", lambda path: True)
    monkeypatch.setattr(
        workflow, "open_run", lambda *a, **k: workflow.ReplayRun({}, "a" * 64, ROOT, tmp_path)
    )
    monkeypatch.setattr(
        launch, "launch_replay", lambda *a, **k: {"status": "failed", "reason": "budget_exceeded"}
    )
    assert cli.main([command, "--run-spec", str(CONFIG)]) == 1
