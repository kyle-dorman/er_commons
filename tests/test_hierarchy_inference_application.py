"""Focused no-PDF tests for the one-build hierarchy application shell."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import er_commons.hierarchy_inference.application as application
from er_commons.hierarchy_inference.candidate_publication import CandidateSeal, CandidateWorkspace
from er_commons.hierarchy_inference.failures import RunStage
from er_commons.hierarchy_inference.progress import (
    CandidateAssemblyProgress,
    CandidatePhase,
    ProgressSnapshot,
)
from er_commons.hierarchy_inference.publication_authorization import (
    VerifiedPublicationAuthorization,
)
from er_commons.hierarchy_inference.semantic_types import SemanticCandidate
from er_commons.hierarchy_inference.single_build import SingleBuildResult

CANDIDATE_ID = "hcorv1-" + "a" * 64
SCHEMA_PATH = Path("benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json")


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
        semantic=SemanticCandidate((), (), (), (), (), {"roots": []}, (), ()),
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

    def write(
        _run: object,
        _workspace: object,
        result: SingleBuildResult,
        _progress: object,
    ) -> None:
        assert result.wall_seconds == 1.25
        calls.append("validate_and_seal")

    authorization = cast(VerifiedPublicationAuthorization, object())

    def authorize(*_args: object) -> VerifiedPublicationAuthorization:
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
        application._new_authorization(run, workspace, cast(CandidateSeal, object()))

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
        lambda *_args: maybe_fail(
            "authorize",
            cast(VerifiedPublicationAuthorization, object()),
        ),
    )
    monkeypatch.setattr(
        application,
        "publish_workspace",
        lambda *_args: maybe_fail("publish", Path("completion.json")),
    )
    monkeypatch.setattr(
        application,
        "_retain_failure",
        lambda _run, _workspace, stage, _error, _progress: seen.append(stage),
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


def test_keyboard_interrupt_is_retained_and_reraised(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _run(tmp_path)
    run.schema_path = SCHEMA_PATH.resolve()
    monkeypatch.setattr(
        application,
        "build_single_semantic_candidate",
        lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        application._build_and_publish(run)

    [attempt_path] = list((tmp_path / "attempts").glob("*/records/attempt_record.json"))
    attempt = json.loads(attempt_path.read_text())
    assert attempt["fatal_code"] == "RUN_INTERRUPTED"
    assert attempt["detail"] == "build: KeyboardInterrupt"
    assert not list((tmp_path / ".tmp").glob("*"))


@pytest.mark.parametrize(
    ("checkpoint", "completion_written"),
    [
        ("semantic_validation", False),
        ("mid_streaming", False),
        ("post_inventory", False),
        ("post_completion", True),
    ],
)
def test_candidate_assembly_interruptions_retain_partial_evidence_and_retry_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    checkpoint: str,
    completion_written: bool,
) -> None:
    run = _run(tmp_path)
    run.schema_path = SCHEMA_PATH.resolve()
    monkeypatch.setattr(application, "build_single_semantic_candidate", lambda *_args: _result())
    expected_phase = {
        "semantic_validation": CandidatePhase.SEMANTIC_SCHEMA_VALIDATION,
        "mid_streaming": CandidatePhase.STREAMING_PUBLICATION,
        "post_inventory": CandidatePhase.INVENTORY_SEAL,
        "post_completion": CandidatePhase.COMPLETION_SEAL,
    }[checkpoint]

    def interrupt_write(
        _run: object,
        workspace: CandidateWorkspace,
        _result_value: SingleBuildResult,
        progress: CandidateAssemblyProgress,
    ) -> None:
        phase = expected_phase
        unit = (
            "files"
            if phase in {CandidatePhase.INVENTORY_SEAL, CandidatePhase.COMPLETION_SEAL}
            else "records"
        )
        progress.report(ProgressSnapshot(phase, 1, 2, unit))
        evidence = workspace.staging_root / "artifacts" / f"{checkpoint}.partial"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("inspectable partial evidence\n")
        if checkpoint == "post_inventory":
            records = workspace.staging_root / "records"
            records.mkdir(parents=True, exist_ok=True)
            (records / "artifact_inventory.json").write_text("{}\n")
        if completion_written:
            records = workspace.staging_root / "records"
            records.mkdir(parents=True, exist_ok=True)
            (records / "completion_record.json").write_text("{}\n")
            return
        raise KeyboardInterrupt

    monkeypatch.setattr(application, "_write_staged_candidate", interrupt_write)
    if completion_written:
        monkeypatch.setattr(
            application,
            "_new_authorization",
            lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()),
        )

    with pytest.raises(KeyboardInterrupt):
        application._build_and_publish(run)

    [attempt_root] = list((tmp_path / "attempts").glob(f"{CANDIDATE_ID}.*"))
    assert (attempt_root / "artifacts" / f"{checkpoint}.partial").is_file()
    assert not (attempt_root / "records/completion_record.json").exists()
    attempt = json.loads((attempt_root / "records/attempt_record.json").read_text())
    assert attempt["fatal_code"] == "RUN_INTERRUPTED"
    assert attempt["phase"] == expected_phase.value
    assert (attempt["processed_units"], attempt["total_units"]) == (1, 2)
    retry = application.reserve_workspace(tmp_path, CANDIDATE_ID, f"retry-{checkpoint}")
    assert retry.staging_root.is_dir()


def test_semantic_candidate_names_all_eight_record_families() -> None:
    semantic = SemanticCandidate(
        features=({"id": "feature"},),
        toc_entries=({"id": "toc"},),
        reconciliations=({"id": "reconciliation"},),
        regimes=({"id": "regime"},),
        decisions=({"id": "decision"},),
        hierarchy={"roots": []},
        ambiguities=({"id": "ambiguity"},),
        warnings=({"id": "warning"},),
    )

    assert set(semantic.as_mapping()) == {
        "features",
        "toc_entries",
        "reconciliations",
        "regimes",
        "decisions",
        "hierarchy",
        "ambiguities",
        "warnings",
    }
