"""Readable one-build lifecycle for deterministic hierarchy correction."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.bounded_acceptance import (
    VerifiedBoundedAcceptancePolicy,
    verify_bounded_acceptance,
)
from er_commons.hierarchy_correction.candidate_identity import build_environment_record
from er_commons.hierarchy_correction.candidate_publication import (
    CandidateWorkspace,
    VerifiedPublicationAuthorization,
    preserve_failed_workspace,
    publish_workspace,
    reserve_workspace,
    retain_failed_attempt,
    reuse_completed_candidate,
    write_validate_and_seal_candidate,
)
from er_commons.hierarchy_correction.candidate_records import (
    CandidateMeasurements,
    CandidatePayload,
)
from er_commons.hierarchy_correction.failures import RunStage, disposition_for
from er_commons.hierarchy_correction.inputs import HierarchyCorrectionInputs
from er_commons.hierarchy_correction.preflight import CorrectionRunContext, prepare_run
from er_commons.hierarchy_correction.publication_authorization import (
    authorize_validated_candidate,
)
from er_commons.hierarchy_correction.single_build import (
    SingleBuildResult,
    build_single_semantic_candidate,
)

JsonRecord = dict[str, Any]
LOGGER = logging.getLogger(__name__)


def run_hierarchy_correction(data_root: Path, config_path: Path) -> Path:
    """Verify inputs, reuse an authorized candidate, or build and publish once."""
    run = prepare_run(data_root, config_path)
    if run.final_root.exists():
        LOGGER.info("Reusing verified hierarchy candidate %s", run.candidate_id)
        return _reuse_candidate(run)
    LOGGER.info("Building hierarchy candidate %s", run.candidate_id)
    return _build_and_publish(run)


def _reuse_candidate(run: CorrectionRunContext) -> Path:
    """Verify configured authorization and every completed candidate byte."""
    authorization = _existing_authorization(run, run.final_root)
    return reuse_completed_candidate(
        run.final_root,
        run.candidate_id,
        run.schema_path,
        authorization,
    )


def _build_and_publish(run: CorrectionRunContext) -> Path:
    """Build once, validate, authorize, and preserve any failed attempt."""
    workspace = reserve_workspace(run.task_root, run.candidate_id, uuid.uuid4().hex)
    stage = RunStage.BUILD
    try:
        result = build_single_semantic_candidate(run.inputs)
        stage = RunStage.CANDIDATE_ASSEMBLY
        _write_staged_candidate(run, workspace, result)
        stage = RunStage.AUTHORIZATION
        authorization = _new_authorization(run, workspace)
        stage = RunStage.PUBLICATION
        completion = publish_workspace(workspace, authorization)
        LOGGER.info("Published hierarchy candidate %s", run.candidate_id)
        return completion
    except Exception as error:
        try:
            _retain_failure(run, workspace, stage, error)
        except Exception as retention_error:
            error.add_note(f"failed to retain hierarchy attempt: {retention_error}")
            LOGGER.exception(
                "Failed to retain hierarchy attempt for %s after %s",
                run.candidate_id,
                stage.value,
            )
        raise


def _write_staged_candidate(
    run: CorrectionRunContext,
    workspace: CandidateWorkspace,
    result: SingleBuildResult,
) -> None:
    """Assemble active records and write completion last in private staging."""
    producer_wall_seconds, producer_bytes = _producer_measurements(run.inputs)
    measurements = CandidateMeasurements(
        build_wall_time_seconds=result.wall_seconds,
        stage_wall_time_seconds=result.stage_wall_time_seconds,
        peak_rss_bytes=result.peak_rss_bytes,
        input_bytes=_input_bytes(run.data_root, run.inputs),
        producer_build_wall_time_seconds=producer_wall_seconds,
        producer_bytes=producer_bytes,
    )
    payload = _candidate_payload(
        identity=run.identity,
        input_inventory=run.inputs.input_inventory,
        environment=build_environment_record(uv_lock_path=run.project_root / "uv.lock"),
        semantic=result.semantic,
    )
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=measurements,
        schema_path=run.schema_path,
    )


def _new_authorization(
    run: CorrectionRunContext,
    workspace: CandidateWorkspace,
) -> VerifiedPublicationAuthorization:
    """Apply direct machine policy or Appendix P's source-scoped decision."""
    if run.config.publication_authorization == "machine_validation":
        return authorize_validated_candidate(workspace.staging_root, run.candidate_id)
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
    run: CorrectionRunContext,
    candidate_root: Path,
) -> VerifiedPublicationAuthorization:
    """Recompute machine authority or verify the source-scoped authorization."""
    if run.config.publication_authorization == "machine_validation":
        return authorize_validated_candidate(candidate_root, run.candidate_id)
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
    run: CorrectionRunContext,
) -> tuple[VerifiedBoundedAcceptancePolicy, Path]:
    """Return both checked source-scoped controls or fail closed."""
    if run.bounded_acceptance_policy is None or run.bounded_acceptance_path is None:
        raise ValueError("bounded publication selected without verified controls")
    return run.bounded_acceptance_policy, run.bounded_acceptance_path


def _retain_failure(
    run: CorrectionRunContext,
    workspace: CandidateWorkspace,
    stage: RunStage,
    error: Exception,
) -> None:
    """Persist a stage-qualified disposition without parsing exception prose."""
    failure = disposition_for(error, stage)
    retain_failed_attempt(
        workspace=workspace,
        candidate_id=run.candidate_id,
        fatal_code=failure.fatal_code,
        detail=failure.persisted_detail,
        schema_path=run.schema_path,
    )
    preserve_failed_workspace(workspace, run.task_root / "attempts")
    LOGGER.error(
        "Hierarchy candidate %s failed during %s (%s)",
        run.candidate_id,
        failure.stage.value,
        failure.fatal_code,
    )


def _candidate_payload(
    *,
    identity: JsonRecord,
    input_inventory: JsonRecord,
    environment: JsonRecord,
    semantic: JsonRecord,
) -> CandidatePayload:
    """Convert one build's semantic protocol to publication-owned records."""
    return CandidatePayload(
        identity=identity,
        input_inventory=input_inventory,
        environment=environment,
        features=tuple(semantic["features"]),
        toc_entries=tuple(semantic["toc_entries"]),
        reconciliations=tuple(semantic["reconciliations"]),
        regimes=tuple(semantic["regimes"]),
        decisions=tuple(semantic["decisions"]),
        hierarchy=semantic["hierarchy"],
        ambiguities=tuple(semantic["ambiguities"]),
        warnings=tuple(semantic["warnings"]),
    )


def _producer_measurements(inputs: HierarchyCorrectionInputs) -> tuple[float, int]:
    """Read producer wall time and exact inventoried payload bytes."""
    records_root = inputs.producer_run_root / "records"
    summary = json.loads((records_root / "producer_summary.json").read_text())
    inventory = json.loads((records_root / "artifact_inventory.json").read_text())
    return float(summary["wall_seconds"]), sum(item["byte_size"] for item in inventory["files"])


def _input_bytes(data_root: Path, inputs: HierarchyCorrectionInputs) -> int:
    """Count the three verified candidate-producing input files."""
    paths = (
        data_root / inputs.input_inventory["producer_completion_path"],
        data_root / inputs.input_inventory["producer_inventory_path"],
        data_root / inputs.input_inventory["source_path"],
    )
    return sum(path.stat().st_size for path in paths)
