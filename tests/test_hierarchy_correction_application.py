"""Synthetic integration tests for the Task 03E.2 application and CLI."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from typer.testing import CliRunner

import er_commons.cli as cli_module
import er_commons.hierarchy_correction.application as application
import er_commons.hierarchy_correction.preflight as preflight
import er_commons.hierarchy_correction.repeat_builds as repeat_builds
import er_commons.hierarchy_correction.single_build as single_build
from er_commons.cli import app
from er_commons.hierarchy_correction.bounded_acceptance import VerifiedBoundedAcceptance
from er_commons.hierarchy_correction.code_inventory import owned_code_paths
from er_commons.hierarchy_correction.configuration import load_hierarchy_correction_config
from er_commons.hierarchy_correction.failures import (
    QualityGateRejected,
    RunStage,
    disposition_for,
    explicit_failure,
)
from er_commons.hierarchy_correction.quality_gate import (
    VerifiedQualityGatePass,
    candidate_semantic_sha256,
)
from er_commons.hierarchy_correction.repeat_builds import (
    BuildObservation,
    RepeatBuildResult,
)
from er_commons.hierarchy_correction.single_build import build_single_semantic_candidate

ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / "configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json"
FIXTURE_PATH = ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1/valid_bundle.json"


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text())


def _semantic() -> dict[str, Any]:
    fixture = _fixture()
    return {
        "features": fixture["features"],
        "toc_entries": fixture["toc_entries"],
        "reconciliations": fixture["reconciliations"],
        "regimes": fixture["regimes"],
        "decisions": fixture["decisions"],
        "hierarchy": fixture["hierarchy"],
        "ambiguities": fixture["ambiguities"],
        "warnings": fixture["warnings"],
    }


def _build_record(index: int, semantic: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "semantic": copy.deepcopy(semantic or _semantic()),
        "wall_seconds": 1.0 + index,
        "stage_wall_time_seconds": {
            "features": 0.1 + index,
            "toc_reconciliation": 0.2 + index,
            "rules": 0.3 + index,
            "hierarchy": 0.4 + index,
            "publication": 0.01 + index,
        },
        "peak_rss_bytes": 1000 + index,
    }


def test_single_build_orchestrates_each_semantic_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    semantic = _semantic()
    calls: list[str] = []

    monkeypatch.setattr(
        single_build,
        "read_pdf_observations",
        lambda _path: ((), {}),
    )
    monkeypatch.setattr(
        single_build,
        "read_native_heading_observations",
        lambda *_args: {},
    )
    monkeypatch.setattr(
        single_build,
        "build_feature_seeds",
        lambda *_args, **_kwargs: calls.append("features") or semantic["features"],
    )
    monkeypatch.setattr(
        single_build,
        "build_visible_toc",
        lambda *_args, **_kwargs: (
            calls.append("toc")
            or SimpleNamespace(
                features=tuple(semantic["features"]),
                entries=tuple(semantic["toc_entries"]),
                reconciliations=tuple(semantic["reconciliations"]),
                diagnostics=tuple(semantic["warnings"]),
            )
        ),
    )
    monkeypatch.setattr(
        single_build,
        "build_numbering_regimes",
        lambda *_args: (
            calls.append("regimes")
            or SimpleNamespace(
                features=tuple(semantic["features"]),
                regimes=tuple(semantic["regimes"]),
            )
        ),
    )
    monkeypatch.setattr(
        single_build,
        "build_rule_decisions",
        lambda **_kwargs: (
            calls.append("decisions")
            or SimpleNamespace(
                decisions=tuple(semantic["decisions"]),
                ambiguities=tuple(semantic["ambiguities"]),
            )
        ),
    )
    monkeypatch.setattr(
        single_build,
        "build_corrected_hierarchy",
        lambda **_kwargs: (
            calls.append("hierarchy")
            or SimpleNamespace(hierarchy=semantic["hierarchy"], warnings=())
        ),
    )
    inputs = cast(
        Any,
        SimpleNamespace(
            selected_source=SimpleNamespace(source_path=Path("source.pdf")),
            document={},
            conversion_pages={},
        ),
    )

    result = build_single_semantic_candidate(inputs)

    assert calls == ["features", "toc", "regimes", "decisions", "hierarchy"]
    assert result.semantic == semantic
    assert result.wall_seconds >= 0
    assert set(result.stage_wall_time_seconds) == {
        "features",
        "toc_reconciliation",
        "rules",
        "hierarchy",
        "publication",
    }


def test_fresh_runner_invokes_three_independent_module_processes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> None:
        commands.append(command)
        output = Path(command[command.index("--output") + 1])
        output.write_text(json.dumps(_build_record(len(commands))) + "\n")

    monkeypatch.setattr(repeat_builds.subprocess, "run", run)
    evidence_root = tmp_path / "review/repeat"
    result = repeat_builds.run_fresh_builds(
        tmp_path,
        CONFIG_PATH,
        evidence_root,
        _fixture()["identity"]["candidate_id"],
    )

    assert len(result.builds) == 3
    assert len(commands) == 3
    assert all(
        command[1:3] == ["-m", "er_commons.hierarchy_correction.single_build"]
        for command in commands
    )
    assert len({command[command.index("--output") + 1] for command in commands}) == 3
    assert sorted(path.name for path in evidence_root.glob("build-*.json")) == [
        "build-1.json",
        "build-2.json",
        "build-3.json",
    ]
    comparison = json.loads((evidence_root / "repeat_comparison.json").read_text())
    assert comparison["semantic_match"] is True
    assert [item["path"] for item in comparison["builds"]] == [
        "build-1.json",
        "build-2.json",
        "build-3.json",
    ]
    assert comparison["normalization"]["excluded_measurement_fields"] == [
        "peak_rss_bytes",
        "stage_wall_time_seconds",
        "wall_seconds",
    ]


def test_fresh_runner_preserves_named_child_fatal_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_command: list[str], **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(
            1,
            "single-build",
            output="child stdout",
            stderr="HIERARCHY_ORDER_INVALID: fixture order",
        )

    monkeypatch.setattr(repeat_builds.subprocess, "run", fail)

    with pytest.raises(ValueError, match="UNKNOWN_REFERENCE") as caught:
        repeat_builds.run_fresh_builds(
            tmp_path,
            CONFIG_PATH,
            tmp_path / "review/repeat",
            _fixture()["identity"]["candidate_id"],
        )

    failure = disposition_for(caught.value, RunStage.FRESH_BUILDS)
    assert failure.fatal_code == "UNKNOWN_REFERENCE"
    assert failure.stage == RunStage.FRESH_BUILDS


def test_fresh_runner_retains_normalized_mismatch_disposition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def run(command: list[str], **_kwargs: object) -> None:
        nonlocal calls
        calls += 1
        semantic = _semantic()
        if calls == 3:
            semantic["warnings"] = [
                {
                    "reading_order_index": None,
                    "stable_item_key": None,
                    "code": "TOC_ROW_UNPARSEABLE",
                    "detail": "different",
                }
            ]
        output = Path(command[command.index("--output") + 1])
        output.write_text(json.dumps(_build_record(calls, semantic)) + "\n")

    monkeypatch.setattr(repeat_builds.subprocess, "run", run)
    evidence_root = tmp_path / "review/repeat"
    with pytest.raises(ValueError, match="REPEAT_BUILD_MISMATCH"):
        repeat_builds.run_fresh_builds(
            tmp_path,
            CONFIG_PATH,
            evidence_root,
            _fixture()["identity"]["candidate_id"],
        )
    comparison = json.loads((evidence_root / "repeat_comparison.json").read_text())
    assert comparison["semantic_match"] is False
    assert len({item["semantic_sha256"] for item in comparison["builds"]}) == 2


def _patch_application_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    builds: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> None:
    config, config_sha256 = load_hierarchy_correction_config(CONFIG_PATH)
    strict_config = config.model_copy(update={"publication_authorization": "strict_quality_gate"})
    fixture = _fixture()
    inputs = SimpleNamespace(
        producer_run_root=tmp_path / "producer",
        input_inventory=fixture["input_inventory"],
    )
    del config_sha256
    snapshot = SimpleNamespace(identity="producer")
    candidate_id = fixture["identity"]["candidate_id"]
    task_root = tmp_path / config.artifact_relative_root
    quality_config = SimpleNamespace(
        task03d1_reference=SimpleNamespace(extraction_id="fixture-reference")
    )
    quality_gate_pass_path = tmp_path / "review" / candidate_id / "quality_gate_pass.json"
    quality_gate_pass_path.parent.mkdir(parents=True, exist_ok=True)
    quality_gate_pass_path.write_text("{}\n")
    run = SimpleNamespace(
        data_root=tmp_path,
        project_root=ROOT,
        config_path=CONFIG_PATH,
        config=strict_config,
        inputs=inputs,
        schema_path=ROOT / config.schema_relative_path,
        identity=fixture["identity"],
        candidate_id=candidate_id,
        task_root=task_root,
        final_root=task_root / candidate_id,
        quality_gate_config_path=tmp_path / "quality-gate.json",
        quality_gate_config=quality_config,
        quality_gate_pass_path=quality_gate_pass_path,
        producer_before=snapshot,
    )
    new_candidate = SimpleNamespace(
        run=run,
        annotation_seal=SimpleNamespace(status="sealed"),
        task03d1_root=tmp_path / "task03d1",
        preservation_before=(snapshot, snapshot),
    )
    observations = tuple(
        BuildObservation.from_record(record, tmp_path / f"build-{index}.json")
        for index, record in enumerate(builds, start=1)
    )
    comparison_path = tmp_path / "repeat_comparison.json"
    comparison_path.write_text("{}\n")
    repeat_result = RepeatBuildResult(
        builds=cast(Any, observations),
        evidence_root=tmp_path,
        comparison_path=comparison_path,
    )
    monkeypatch.setattr(application, "prepare_run", lambda *_args: run)
    monkeypatch.setattr(application, "prepare_new_candidate", lambda _run: new_candidate)
    monkeypatch.setattr(
        application,
        "build_environment_record",
        lambda **_kwargs: {"python_version": "fixture"},
    )
    monkeypatch.setattr(application, "snapshot_verified_producer", lambda *_args: snapshot)
    monkeypatch.setattr(
        application,
        "snapshot_verified_task03d1_reference",
        lambda *_args: snapshot,
    )
    monkeypatch.setattr(application, "assert_artifacts_preserved", lambda *_args: None)
    monkeypatch.setattr(application, "run_fresh_builds", lambda *_args: repeat_result)
    monkeypatch.setattr(application, "_producer_measurements", lambda _inputs: (60.0, 1_000_000))
    monkeypatch.setattr(application, "_input_bytes", lambda *_args: 10_000)

    def verify_gate(**kwargs: Any) -> VerifiedQualityGatePass:
        candidate_root = kwargs["candidate_root"]
        return VerifiedQualityGatePass(
            path=kwargs.get("pass_path", tmp_path / "quality_gate_pass.json"),
            candidate_id=kwargs["candidate_id"],
            candidate_semantic_sha256=candidate_semantic_sha256(candidate_root),
        )

    monkeypatch.setattr(application, "verify_quality_gate_pass", verify_gate)
    monkeypatch.setattr(application, "produce_quality_gate_pass", verify_gate)


def test_application_publishes_after_repeat_gate_and_then_reuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)

    completion = application.run_hierarchy_correction(tmp_path, CONFIG_PATH)
    reused = application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    assert completion == reused
    assert completion.is_file()
    candidate_root = completion.parents[1]
    metrics = json.loads((candidate_root / "records/metrics.json").read_text())
    assert metrics["fresh_wall_time_seconds"] == [1.0, 2.0, 3.0]
    assert metrics["stage_wall_time_seconds"]["features"] == 1.1
    assert metrics["peak_rss_bytes"] == 1002
    assert not list((candidate_root.parent / "attempts").glob("*"))


def test_strict_mode_is_independent_of_bounded_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    run = application.prepare_run(tmp_path, CONFIG_PATH)
    run.quality_gate_pass_path.unlink()
    monkeypatch.setattr(
        application,
        "assemble_bounded_acceptance",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("bounded assembly called")),
    )
    monkeypatch.setattr(
        application,
        "verify_bounded_acceptance",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("bounded verifier called")),
    )

    completion = application.run_hierarchy_correction(tmp_path, CONFIG_PATH)
    reused = application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    assert completion == reused


def test_strict_preflight_skips_bounded_policy_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_hierarchy_correction_config(CONFIG_PATH)[0].model_copy(
        update={"publication_authorization": "strict_quality_gate"}
    )
    inputs = SimpleNamespace(producer_run_root=tmp_path / "producer")
    monkeypatch.setattr(preflight, "load_hierarchy_correction_config", lambda _path: (config, "a"))
    monkeypatch.setattr(preflight, "load_hierarchy_correction_inputs", lambda *_args: inputs)
    monkeypatch.setattr(preflight, "snapshot_verified_producer", lambda *_args: SimpleNamespace())
    monkeypatch.setattr(
        preflight,
        "build_candidate_identity",
        lambda **_kwargs: {"candidate_id": "hcorv1-" + "a" * 64},
    )
    monkeypatch.setattr(
        preflight,
        "load_quality_gate_config",
        lambda _path: (SimpleNamespace(), "b"),
    )
    monkeypatch.setattr(
        preflight,
        "verify_bounded_acceptance_policy",
        lambda *_args: (_ for _ in ()).throw(AssertionError("bounded preflight called")),
    )

    run = preflight.prepare_run(tmp_path, CONFIG_PATH)

    assert run.bounded_acceptance_policy is None


def test_application_requires_annotation_seal_before_any_semantic_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    semantic_build_called = False

    def build(*_args: object) -> tuple[dict[str, Any], ...]:
        nonlocal semantic_build_called
        semantic_build_called = True
        return builds

    monkeypatch.setattr(application, "run_fresh_builds", build)
    monkeypatch.setattr(
        application,
        "prepare_new_candidate",
        lambda _run: (_ for _ in ()).throw(ValueError("held-out annotations are not sealed")),
    )

    with pytest.raises(ValueError, match="not sealed"):
        application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    assert semantic_build_called is False
    assert not list(tmp_path.rglob(".tmp"))


def test_repeat_failure_is_retained_under_stable_attempts_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed = _semantic()
    changed["warnings"] = [
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "TOC_ROW_UNPARSEABLE",
            "detail": "different",
        }
    ]
    builds = (_build_record(0), _build_record(1), _build_record(2, changed))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    monkeypatch.setattr(
        application,
        "run_fresh_builds",
        lambda *_args: (_ for _ in ()).throw(
            explicit_failure(
                RunStage.FRESH_BUILDS,
                "REPEAT_BUILD_MISMATCH",
                "fresh semantic builds differ",
            )
        ),
    )

    with pytest.raises(ValueError, match="REPEAT_BUILD_MISMATCH"):
        application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    attempts = list(tmp_path.rglob("attempts/*/records/attempt_record.json"))
    assert len(attempts) == 1
    record = json.loads(attempts[0].read_text())
    assert record["fatal_code"] == "REPEAT_BUILD_MISMATCH"
    assert not list(attempts[0].parents[1].rglob("completion_record.json"))


def test_post_completion_publish_failure_becomes_stable_failed_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    monkeypatch.setattr(
        application,
        "publish_workspace",
        lambda _workspace, _quality_gate_pass: (_ for _ in ()).throw(
            ValueError("PUBLICATION_COLLISION: fixture pre-rename failure")
        ),
    )

    with pytest.raises(ValueError, match="PUBLICATION_COLLISION"):
        application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    attempts = list(tmp_path.rglob("attempts/*/records/attempt_record.json"))
    assert len(attempts) == 1
    record = json.loads(attempts[0].read_text())
    assert record["fatal_code"] == "PUBLICATION_COLLISION"
    assert not list(attempts[0].parents[1].rglob("completion_record.json"))


def test_bounded_authorization_publish_failure_preserves_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    run = application.prepare_run(tmp_path, CONFIG_PATH)
    run.quality_gate_pass_path.unlink()
    run.config = load_hierarchy_correction_config(CONFIG_PATH)[0]
    run.bounded_acceptance_policy = SimpleNamespace(status="verified")
    run.bounded_acceptance_path = tmp_path / "review" / run.candidate_id / "bounded_acceptance.json"

    def authorize(**kwargs: Any) -> VerifiedBoundedAcceptance:
        candidate_root = kwargs["candidate_root"]
        return VerifiedBoundedAcceptance(
            path=run.bounded_acceptance_path,
            candidate_id=run.candidate_id,
            candidate_semantic_sha256=candidate_semantic_sha256(candidate_root),
            frozen_semantic_sha256="f" * 64,
        )

    monkeypatch.setattr(application, "assemble_bounded_acceptance", authorize)
    monkeypatch.setattr(
        application,
        "publish_workspace",
        lambda _workspace, _authorization: (_ for _ in ()).throw(
            ValueError("PUBLICATION_COLLISION: bounded fixture failure")
        ),
    )

    with pytest.raises(ValueError, match="PUBLICATION_COLLISION"):
        application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    attempts = list(tmp_path.rglob("attempts/*/records/attempt_record.json"))
    assert len(attempts) == 1
    assert json.loads(attempts[0].read_text())["fatal_code"] == "PUBLICATION_COLLISION"
    assert not list(attempts[0].parents[1].rglob("completion_record.json"))


def test_quality_rejection_becomes_named_stable_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builds = (_build_record(0), _build_record(1), _build_record(2))
    _patch_application_dependencies(monkeypatch, tmp_path, builds)
    application.prepare_run(tmp_path, CONFIG_PATH).quality_gate_pass_path.unlink()
    monkeypatch.setattr(
        application,
        "produce_quality_gate_pass",
        lambda **_kwargs: (_ for _ in ()).throw(QualityGateRejected(("development", "held_out"))),
    )

    with pytest.raises(QualityGateRejected):
        application.run_hierarchy_correction(tmp_path, CONFIG_PATH)

    attempts = list(tmp_path.rglob("attempts/*/records/attempt_record.json"))
    assert len(attempts) == 1
    record = json.loads(attempts[0].read_text())
    assert record["fatal_code"] == "QUALITY_GATE_REJECTED"
    assert record["detail"] == "quality: reports=development,held_out"
    assert not list(attempts[0].parents[1].rglob("completion_record.json"))


def test_owned_code_identity_covers_application_gate_modules() -> None:
    paths = {path.relative_to(ROOT).as_posix() for path in owned_code_paths(ROOT)}
    package_modules = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/er_commons/hierarchy_correction").glob("*.py")
    }

    assert package_modules <= paths
    assert {
        "src/er_commons/hierarchy_correction/evaluation.py",
        "src/er_commons/hierarchy_correction/preservation.py",
        "src/er_commons/hierarchy_correction/quality_evaluation.py",
        "src/er_commons/hierarchy_correction/quality_gate.py",
        "src/er_commons/hierarchy_correction/quality_workflow.py",
        "src/er_commons/hierarchy_correction/review.py",
    } <= paths
    assert {
        "src/er_commons/hierarchy_correction/code_inventory.py",
        "src/er_commons/hierarchy_correction/failures.py",
        "src/er_commons/hierarchy_correction/preflight.py",
        "src/er_commons/hierarchy_correction/repeat_builds.py",
    } <= paths
    assert tuple(sorted(owned_code_paths(ROOT))) == owned_code_paths(ROOT)


def test_failure_disposition_uses_stage_not_exception_wording() -> None:
    checksum_words = ValueError("source checksum completion inventory")

    assert disposition_for(checksum_words, RunStage.PUBLICATION).fatal_code == (
        "PUBLICATION_COLLISION"
    )
    assert disposition_for(checksum_words, RunStage.CANDIDATE_ASSEMBLY).fatal_code == (
        "UNKNOWN_REFERENCE"
    )


def test_quality_rejection_names_reports_and_preserves_frozen_code() -> None:
    error = QualityGateRejected(("development", "held_out"))
    failure = disposition_for(error, RunStage.PUBLICATION)

    assert error.rejected_reports == ("development", "held_out")
    assert failure.stage == RunStage.QUALITY_GATE
    assert failure.fatal_code == "QUALITY_GATE_REJECTED"
    assert failure.detail == "reports=development,held_out"


def test_cli_exposes_hierarchy_correct_document_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completion = tmp_path / "candidate/records/completion_record.json"
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda: SimpleNamespace(data_root=tmp_path),
    )
    monkeypatch.setattr(
        cli_module,
        "run_hierarchy_correction",
        lambda data_root, config: calls.append((data_root, config)) or completion,
    )

    result = CliRunner().invoke(app, ["hierarchy", "correct-document"])

    assert result.exit_code == 0, result.output
    assert calls == [(tmp_path, cli_module.DEFAULT_HIERARCHY_CORRECTION_SPEC)]
    assert f"hierarchy_correction_completion={completion}" in result.output
