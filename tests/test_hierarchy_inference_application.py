"""Focused no-PDF tests for the one-build hierarchy application shell."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import er_commons.hierarchy_inference.application as application
from er_commons.hierarchy_inference.candidate_publication import CandidateWorkspace
from er_commons.hierarchy_inference.failures import RunStage
from er_commons.hierarchy_inference.publication_authorization import (
    VerifiedMachinePublication,
)
from er_commons.hierarchy_inference.single_build import SingleBuildResult

CANDIDATE_ID = "hcorv1-" + "a" * 64


def _run(tmp_path: Path, *, final_exists: bool = False) -> Any:
    final_root = tmp_path / CANDIDATE_ID
    if final_exists:
        final_root.mkdir()
    return SimpleNamespace(
        candidate_id=CANDIDATE_ID,
        final_root=final_root,
        task_root=tmp_path,
        schema_path=tmp_path / "schema.json",
        config=SimpleNamespace(publication_authorization="machine_validation"),
        inputs=object(),
        project_root=tmp_path,
        data_root=tmp_path,
        bounded_acceptance_policy=None,
        bounded_acceptance_path=None,
    )


def _result() -> SingleBuildResult:
    return SingleBuildResult(
        semantic={"features": []},
        wall_seconds=1.25,
        stage_wall_time_seconds={"features": 1.0},
        peak_rss_bytes=123,
    )


def test_existing_candidate_uses_verified_reuse_without_build(
    tmp_path: Path,
) -> None:
    run = _run(tmp_path, final_exists=True)
    completion = run.final_root / "records/completion_record.json"
    services = application.HierarchyWorkflowServices(
        prepare=lambda *_args: run,
        reuse=lambda _run: completion,
        build_and_publish=lambda _run: pytest.fail("reuse must not build"),
    )

    assert (
        application.infer_document_hierarchy(tmp_path, tmp_path / "config.json", services=services)
        == completion
    )


def test_new_candidate_builds_exactly_once_then_authorizes_and_publishes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _run(tmp_path)
    workspace = CandidateWorkspace(tmp_path / ".tmp/candidate", run.final_root)
    calls: list[str] = []

    def build(_inputs: object) -> SingleBuildResult:
        calls.append("build")
        return _result()

    def write(_run: object, _workspace: object, result: SingleBuildResult) -> None:
        assert result.wall_seconds == 1.25
        calls.append("validate_and_seal")

    authorization = VerifiedMachinePublication(CANDIDATE_ID, "b" * 64)

    def authorize(*_args: object) -> VerifiedMachinePublication:
        calls.append("authorize")
        return authorization

    def publish(*_args: object) -> Path:
        calls.append("publish")
        return Path(run.final_root) / "records/completion_record.json"

    monkeypatch.setattr(application, "reserve_workspace", lambda *_args: workspace)
    monkeypatch.setattr(application, "build_single_semantic_candidate", build)
    monkeypatch.setattr(application, "_write_staged_candidate", write)
    monkeypatch.setattr(
        application,
        "_new_authorization",
        authorize,
    )
    monkeypatch.setattr(
        application,
        "publish_workspace",
        publish,
    )

    application.infer_document_hierarchy(
        tmp_path,
        tmp_path / "config.json",
        services=application.HierarchyWorkflowServices(
            prepare=lambda *_args: run,
            reuse=lambda _run: pytest.fail("new candidate must not reuse"),
            build_and_publish=application._build_and_publish,
        ),
    )

    assert calls == ["build", "validate_and_seal", "authorize", "publish"]


def test_bounded_publication_does_not_create_missing_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A normal run may consume bounded evidence but cannot create the decision."""
    run = _run(tmp_path)
    run.config.publication_authorization = "bounded_acceptance"
    run.bounded_acceptance_policy = object()
    run.bounded_acceptance_path = tmp_path / CANDIDATE_ID / "bounded_acceptance.json"
    workspace = CandidateWorkspace(tmp_path / ".tmp/candidate", run.final_root)
    monkeypatch.setattr(
        application,
        "verify_bounded_acceptance",
        lambda **_kwargs: pytest.fail("missing authorization must not be verified"),
    )

    with pytest.raises(ValueError, match="requires separately supplied candidate authorization"):
        application._new_authorization(run, workspace)

    assert not run.bounded_acceptance_path.exists()


@pytest.mark.parametrize(
    ("failing_owner", "expected_stage"),
    [
        ("build", RunStage.BUILD),
        ("validate_and_seal", RunStage.CANDIDATE_ASSEMBLY),
        ("authorize", RunStage.AUTHORIZATION),
        ("publish", RunStage.PUBLICATION),
    ],
)
def test_failure_retention_names_the_responsible_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failing_owner: str,
    expected_stage: RunStage,
) -> None:
    run = _run(tmp_path)
    workspace = CandidateWorkspace(tmp_path / ".tmp/candidate", run.final_root)
    seen: list[RunStage] = []

    def maybe_fail(name: str, result: Any) -> Any:
        if name == failing_owner:
            raise ValueError(f"{name} failed")
        return result

    monkeypatch.setattr(application, "reserve_workspace", lambda *_args: workspace)
    monkeypatch.setattr(
        application,
        "build_single_semantic_candidate",
        lambda *_args: maybe_fail("build", _result()),
    )
    monkeypatch.setattr(
        application,
        "_write_staged_candidate",
        lambda *_args: maybe_fail("validate_and_seal", None),
    )
    monkeypatch.setattr(
        application,
        "_new_authorization",
        lambda *_args: maybe_fail("authorize", VerifiedMachinePublication(CANDIDATE_ID, "b" * 64)),
    )
    monkeypatch.setattr(
        application,
        "publish_workspace",
        lambda *_args: maybe_fail("publish", Path("completion.json")),
    )
    monkeypatch.setattr(
        application,
        "_retain_failure",
        lambda _run, _workspace, stage, _error: seen.append(stage),
    )

    with pytest.raises(ValueError, match=failing_owner):
        application._build_and_publish(run)

    assert seen == [expected_stage]


def test_failure_retention_error_does_not_mask_hierarchy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attempt-retention diagnostics supplement the original owner failure."""
    run = _run(tmp_path)
    workspace = CandidateWorkspace(tmp_path / ".tmp/candidate", run.final_root)
    monkeypatch.setattr(application, "reserve_workspace", lambda *_args: workspace)
    monkeypatch.setattr(
        application,
        "build_single_semantic_candidate",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("original hierarchy failure")),
    )
    monkeypatch.setattr(
        application,
        "_retain_failure",
        lambda *_args: (_ for _ in ()).throw(OSError("retention failure")),
    )

    with pytest.raises(RuntimeError, match="original hierarchy failure") as captured:
        application._build_and_publish(run)

    assert captured.value.__notes__ == ["failed to retain hierarchy attempt: retention failure"]


def test_candidate_payload_preserves_all_eight_semantic_families() -> None:
    semantic = {
        "features": [{"id": "feature"}],
        "toc_entries": [{"id": "toc"}],
        "reconciliations": [{"id": "reconciliation"}],
        "regimes": [{"id": "regime"}],
        "decisions": [{"id": "decision"}],
        "hierarchy": {"roots": []},
        "ambiguities": [{"id": "ambiguity"}],
        "warnings": [{"id": "warning"}],
    }

    payload = application._candidate_payload(
        identity={"candidate_id": CANDIDATE_ID},
        input_inventory={"source": "fixture"},
        environment={"python": "fixture"},
        semantic=semantic,
    )

    assert payload.features == ({"id": "feature"},)
    assert payload.toc_entries == ({"id": "toc"},)
    assert payload.reconciliations == ({"id": "reconciliation"},)
    assert payload.regimes == ({"id": "regime"},)
    assert payload.decisions == ({"id": "decision"},)
    assert payload.hierarchy == {"roots": []}
    assert payload.ambiguities == ({"id": "ambiguity"},)
    assert payload.warnings == ({"id": "warning"},)
