"""Readable one-build lifecycle for deterministic hierarchy inference."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.hierarchy_inference.bounded_acceptance import (
    VerifiedBoundedAcceptancePolicy,
    verify_bounded_acceptance,
)
from er_commons.hierarchy_inference.candidate_identity import build_environment_record
from er_commons.hierarchy_inference.candidate_publication import (
    CandidateSeal,
    CandidateWorkspace,
    preserve_failed_workspace,
    publish_workspace,
    reserve_workspace,
    retain_failed_attempt,
    write_validate_and_seal_candidate,
)
from er_commons.hierarchy_inference.candidate_records import (
    CandidatePayload,
    SemanticBuildMeasurements,
)
from er_commons.hierarchy_inference.candidate_verification import (
    machine_authorization_for_verified_candidate,
    reuse_completed_candidate,
)
from er_commons.hierarchy_inference.failures import RunStage, disposition_for
from er_commons.hierarchy_inference.inputs import HierarchyInferenceInputs
from er_commons.hierarchy_inference.preflight import HierarchyRunContext, prepare_run
from er_commons.hierarchy_inference.progress import CandidateAssemblyProgress, ProgressSnapshot
from er_commons.hierarchy_inference.publication_authorization import (
    VerifiedPublicationAuthorization,
)
from er_commons.hierarchy_inference.single_build import (
    SingleBuildResult,
    build_single_semantic_candidate,
)

LOGGER = logging.getLogger(__name__)


def infer_document_hierarchy(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
    services: HierarchyWorkflowServices | None = None,
) -> Path:
    """Verify inputs, reuse an authorized candidate, or build and publish once."""
    active = services or HierarchyWorkflowServices()
    run = active.prepare(data_root, config_path, config_identity_path)
    if run.final_root.exists():
        LOGGER.info(
            "Reusing completion-sealed hierarchy candidate without semantic-byte audit %s",
            run.candidate_id,
        )
        return active.reuse(run)
    LOGGER.info("Building hierarchy candidate %s", run.candidate_id)
    return active.build_and_publish(run)


def _reuse_candidate(run: HierarchyRunContext) -> Path:
    """Verify sealed metadata and authorization under immutable-publication trust."""
    authorization = _existing_authorization(run, run.final_root)
    return reuse_completed_candidate(
        run.final_root,
        run.candidate_id,
        run.schema_path,
        authorization,
    )


def _build_and_publish(run: HierarchyRunContext) -> Path:
    """Build once, validate, authorize, and preserve any failed attempt."""
    workspace = reserve_workspace(run.task_root, run.candidate_id, uuid.uuid4().hex)
    stage = RunStage.BUILD
    progress: CandidateAssemblyProgress | None = None
    try:
        result = build_single_semantic_candidate(run.inputs)
        stage = RunStage.CANDIDATE_ASSEMBLY
        started = time.perf_counter()
        LOGGER.info("Hierarchy stage started stage=%s", stage.value)
        progress = CandidateAssemblyProgress(LOGGER, run.candidate_id)
        seal = _write_staged_candidate(run, workspace, result, progress)
        LOGGER.info(
            "Hierarchy stage completed stage=%s elapsed_seconds=%.3f",
            stage.value,
            time.perf_counter() - started,
        )
        stage = RunStage.AUTHORIZATION
        authorization = _new_authorization(run, workspace, seal)
        stage = RunStage.PUBLICATION
        completion = publish_workspace(workspace, authorization)
        LOGGER.info("Published hierarchy candidate %s", run.candidate_id)
        return completion
    except (Exception, KeyboardInterrupt) as error:
        try:
            _retain_failure(
                run,
                workspace,
                stage,
                error,
                progress.last_snapshot if progress is not None else None,
            )
        except Exception as retention_error:
            error.add_note(f"failed to retain hierarchy attempt: {retention_error}")
            LOGGER.exception(
                "Failed to retain hierarchy attempt for %s after %s",
                run.candidate_id,
                stage.value,
            )
        raise


def _write_staged_candidate(
    run: HierarchyRunContext,
    workspace: CandidateWorkspace,
    result: SingleBuildResult,
    progress: CandidateAssemblyProgress,
) -> CandidateSeal:
    """Assemble active records and write completion last in private staging."""
    producer_wall_seconds, producer_bytes = _producer_measurements(run.inputs)
    measurements = SemanticBuildMeasurements(
        semantic_build_wall_time_seconds=result.wall_seconds,
        semantic_stage_wall_time_seconds=result.stage_wall_time_seconds,
        semantic_build_peak_rss_bytes=result.peak_rss_bytes,
        input_bytes=_input_bytes(run.data_root, run.inputs),
        producer_build_wall_time_seconds=producer_wall_seconds,
        producer_bytes=producer_bytes,
    )
    payload = CandidatePayload(
        identity=run.identity,
        input_inventory=run.inputs.input_inventory,
        environment=build_environment_record(uv_lock_path=run.project_root / "uv.lock"),
        semantic=result.semantic,
    )
    return write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=measurements,
        schema_path=run.schema_path,
        progress=progress.report,
    )


def _new_authorization(
    run: HierarchyRunContext,
    workspace: CandidateWorkspace,
    seal: CandidateSeal,
) -> VerifiedPublicationAuthorization:
    """Apply direct machine policy or Appendix P's source-scoped decision."""
    if run.config.publication_authorization == "machine_validation":
        return seal.machine_authorization
    policy, path = _bounded_controls(run)
    if path.exists():
        return verify_bounded_acceptance(
            path=path,
            policy=policy,
            candidate_root=workspace.staging_root,
            candidate_id=run.candidate_id,
            data_root=run.data_root,
        )
    raise ValueError(
        f"bounded publication requires separately supplied candidate authorization: {path}"
    )


def _existing_authorization(
    run: HierarchyRunContext,
    candidate_root: Path,
) -> VerifiedPublicationAuthorization:
    """Recompute machine authority or verify the source-scoped authorization."""
    if run.config.publication_authorization == "machine_validation":
        return machine_authorization_for_verified_candidate(
            candidate_root,
            run.candidate_id,
            run.schema_path,
        )
    policy, path = _bounded_controls(run)
    if not path.exists():
        raise ValueError("completed candidate has no bounded publication authorization")
    return verify_bounded_acceptance(
        path=path,
        policy=policy,
        candidate_root=candidate_root,
        candidate_id=run.candidate_id,
        data_root=run.data_root,
    )


def _bounded_controls(
    run: HierarchyRunContext,
) -> tuple[VerifiedBoundedAcceptancePolicy, Path]:
    """Return both checked source-scoped controls or fail closed."""
    if run.bounded_acceptance_policy is None or run.bounded_acceptance_path is None:
        raise ValueError("bounded publication selected without verified controls")
    return run.bounded_acceptance_policy, run.bounded_acceptance_path


def _retain_failure(
    run: HierarchyRunContext,
    workspace: CandidateWorkspace,
    stage: RunStage,
    error: BaseException,
    progress_snapshot: ProgressSnapshot | None = None,
) -> None:
    """Persist a stage-qualified disposition without parsing exception prose."""
    failure = disposition_for(error, stage)
    retain_failed_attempt(
        workspace=workspace,
        candidate_id=run.candidate_id,
        fatal_code=failure.fatal_code,
        detail=failure.persisted_detail,
        schema_path=run.schema_path,
        stage=stage,
        progress_snapshot=progress_snapshot,
    )
    preserve_failed_workspace(workspace, run.task_root / "attempts")
    LOGGER.error(
        "Hierarchy candidate %s failed during %s (%s)",
        run.candidate_id,
        failure.stage.value,
        failure.fatal_code,
    )


def _producer_measurements(inputs: HierarchyInferenceInputs) -> tuple[float, int]:
    """Read producer wall time and exact inventoried payload bytes."""
    records_root = inputs.producer_run_root / "records"
    summary = json.loads((records_root / "producer_summary.json").read_text())
    inventory = json.loads((records_root / "artifact_inventory.json").read_text())
    return float(summary["wall_seconds"]), sum(item["byte_size"] for item in inventory["files"])


def _input_bytes(data_root: Path, inputs: HierarchyInferenceInputs) -> int:
    """Count the three verified candidate-producing input files."""
    paths = (
        data_root / inputs.input_inventory["producer_completion_path"],
        data_root / inputs.input_inventory["producer_inventory_path"],
        data_root / inputs.input_inventory["source_path"],
    )
    return sum(path.stat().st_size for path in paths)


def _prepare_run(
    data_root: Path, config_path: Path, config_identity_path: Path | None
) -> HierarchyRunContext:
    """Adapt the optional identity override to the strict preflight API."""
    if config_identity_path is None:
        return prepare_run(data_root, config_path)
    return prepare_run(
        data_root,
        config_path,
        config_identity_path=config_identity_path,
    )


@dataclass(frozen=True)
class HierarchyWorkflowServices:
    """Replaceable workflow edges for public orchestration tests."""

    prepare: Callable[[Path, Path, Path | None], HierarchyRunContext] = _prepare_run
    reuse: Callable[[HierarchyRunContext], Path] = _reuse_candidate
    build_and_publish: Callable[[HierarchyRunContext], Path] = _build_and_publish
