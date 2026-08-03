"""Readable application lifecycle for deterministic hierarchy correction."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.bounded_acceptance import (
    VerifiedBoundedAcceptance,
    VerifiedBoundedAcceptancePolicy,
    assemble_bounded_acceptance,
    verify_bounded_acceptance,
)
from er_commons.hierarchy_correction.candidate_identity import build_environment_record
from er_commons.hierarchy_correction.candidate_publication import (
    CandidateWorkspace,
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
from er_commons.hierarchy_correction.preflight import (
    CorrectionRunContext,
    NewCandidateContext,
    prepare_new_candidate,
    prepare_run,
)
from er_commons.hierarchy_correction.preservation import (
    ManagedArtifactSnapshot,
    assert_artifacts_preserved,
    snapshot_verified_producer,
    snapshot_verified_task03d1_reference,
)
from er_commons.hierarchy_correction.quality_gate import (
    VerifiedQualityGatePass,
    verify_quality_gate_pass,
)
from er_commons.hierarchy_correction.quality_workflow import produce_quality_gate_pass
from er_commons.hierarchy_correction.repeat_builds import (
    RepeatBuildResult,
    run_fresh_builds,
)

JsonRecord = dict[str, Any]
LOGGER = logging.getLogger(__name__)


def run_hierarchy_correction(data_root: Path, config_path: Path) -> Path:
    """Verify inputs, reuse an accepted candidate, or build and publish one."""
    run = prepare_run(data_root, config_path)
    if run.final_root.exists():
        LOGGER.info("Reusing verified hierarchy candidate %s", run.candidate_id)
        return _reuse_candidate(run)

    # Held-out annotations and the canonical reference must verify before any
    # corrected output or private staging workspace exists.
    new_candidate = prepare_new_candidate(run)
    LOGGER.info("Building hierarchy candidate %s", run.candidate_id)
    return _build_evaluate_and_publish(new_candidate)


def _reuse_candidate(run: CorrectionRunContext) -> Path:
    """Verify one external authorization and every completed candidate byte."""
    authorization = _existing_authorization(run, run.final_root)
    return reuse_completed_candidate(
        run.final_root,
        run.candidate_id,
        run.schema_path,
        authorization,
    )


def _build_evaluate_and_publish(new: NewCandidateContext) -> Path:
    """Own the unpublished lifecycle and preserve any failed attempt."""
    run = new.run
    token = uuid.uuid4().hex
    workspace = reserve_workspace(run.task_root, run.candidate_id, token)
    repeat_root = (
        run.data_root
        / run.config.review_artifact_relative_root
        / run.candidate_id
        / "repeat_builds"
        / token
    )
    stage = RunStage.FRESH_BUILDS
    try:
        repeats = run_fresh_builds(
            run.data_root,
            run.config_path,
            repeat_root,
            run.candidate_id,
        )

        stage = RunStage.PRESERVATION
        preservation_after = _snapshot_preserved_inputs(new)
        assert_artifacts_preserved(new.preservation_before, preservation_after)

        stage = RunStage.CANDIDATE_ASSEMBLY
        _write_staged_candidate(run, workspace, repeats)

        stage = RunStage.QUALITY_GATE
        authorization = _publication_authorization(
            new,
            workspace,
            repeats,
            preservation_after,
        )

        stage = RunStage.PUBLICATION
        completion = publish_workspace(workspace, authorization)
        LOGGER.info("Published hierarchy candidate %s", run.candidate_id)
        return completion
    except Exception as error:
        _retain_failure(run, workspace, stage, error)
        raise


def _snapshot_preserved_inputs(
    new: NewCandidateContext,
) -> tuple[ManagedArtifactSnapshot, ManagedArtifactSnapshot]:
    """Reverify both immutable inputs after the independent builds finish."""
    run = new.run
    reference = run.quality_gate_config.task03d1_reference
    return (
        snapshot_verified_producer(run.inputs.producer_run_root, run.config.producer_run_id),
        snapshot_verified_task03d1_reference(new.task03d1_root, reference.extraction_id),
    )


def _write_staged_candidate(
    run: CorrectionRunContext,
    workspace: CandidateWorkspace,
    repeats: RepeatBuildResult,
) -> None:
    """Assemble validated records and write completion last in private staging."""
    producer_wall_seconds, producer_bytes = _producer_measurements(run.inputs)
    measurements = CandidateMeasurements(
        fresh_wall_time_seconds=repeats.wall_times,
        stage_wall_time_seconds=repeats.median_stage_times(),
        peak_rss_bytes=repeats.peak_rss_bytes,
        input_bytes=_input_bytes(run.data_root, run.inputs),
        producer_build_wall_time_seconds=producer_wall_seconds,
        producer_bytes=producer_bytes,
    )
    payload = _candidate_payload(
        identity=run.identity,
        input_inventory=run.inputs.input_inventory,
        environment=build_environment_record(uv_lock_path=run.project_root / "uv.lock"),
        semantic=repeats.semantic,
    )
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=measurements,
        schema_path=run.schema_path,
    )


def _quality_pass(
    new: NewCandidateContext,
    workspace: CandidateWorkspace,
    repeats: RepeatBuildResult,
    preservation_after: tuple[ManagedArtifactSnapshot, ManagedArtifactSnapshot],
) -> VerifiedQualityGatePass:
    """Reuse a matching pass or produce all reports before publication."""
    run = new.run
    if run.quality_gate_pass_path.exists():
        return verify_quality_gate_pass(
            pass_path=run.quality_gate_pass_path,
            config_path=run.quality_gate_config_path,
            candidate_root=workspace.staging_root,
            candidate_id=run.candidate_id,
            project_root=run.project_root,
            data_root=run.data_root,
        )
    if new.annotation_seal is None:
        raise ValueError("strict quality evaluation requires candidate-local annotations")
    return produce_quality_gate_pass(
        data_root=run.data_root,
        project_root=run.project_root,
        correction_schema_path=run.schema_path,
        quality_config_path=run.quality_gate_config_path,
        candidate_root=workspace.staging_root,
        candidate_id=run.candidate_id,
        source_id=run.config.source.source_id,
        annotation_seal=new.annotation_seal,
        repeat_comparison_path=repeats.comparison_path,
        preservation_before=new.preservation_before,
        preservation_after=preservation_after,
    )


def _publication_authorization(
    new: NewCandidateContext,
    workspace: CandidateWorkspace,
    repeats: RepeatBuildResult,
    preservation_after: tuple[ManagedArtifactSnapshot, ManagedArtifactSnapshot],
) -> VerifiedQualityGatePass | VerifiedBoundedAcceptance:
    """Prefer an existing strict pass; otherwise issue the bounded decision."""
    run = new.run
    if run.config.publication_authorization == "strict_quality_gate":
        return _quality_pass(new, workspace, repeats, preservation_after)
    policy = _bounded_policy(run)
    if run.bounded_acceptance_path.exists():
        return verify_bounded_acceptance(
            path=run.bounded_acceptance_path,
            policy=policy,
            candidate_root=workspace.staging_root,
            candidate_id=run.candidate_id,
            data_root=run.data_root,
        )
    return assemble_bounded_acceptance(
        path=run.bounded_acceptance_path,
        policy=policy,
        candidate_root=workspace.staging_root,
        candidate_id=run.candidate_id,
        data_root=run.data_root,
    )


def _existing_authorization(
    run: CorrectionRunContext,
    candidate_root: Path,
) -> VerifiedQualityGatePass | VerifiedBoundedAcceptance:
    """Verify exactly one already-issued strict or bounded authorization."""
    if run.config.publication_authorization == "strict_quality_gate":
        return verify_quality_gate_pass(
            pass_path=run.quality_gate_pass_path,
            config_path=run.quality_gate_config_path,
            candidate_root=candidate_root,
            candidate_id=run.candidate_id,
            project_root=run.project_root,
            data_root=run.data_root,
        )
    policy = _bounded_policy(run)
    if run.bounded_acceptance_path.exists():
        return verify_bounded_acceptance(
            path=run.bounded_acceptance_path,
            policy=policy,
            candidate_root=candidate_root,
            candidate_id=run.candidate_id,
            data_root=run.data_root,
        )
    raise ValueError("completed candidate has no verified publication authorization")


def _bounded_policy(run: CorrectionRunContext) -> VerifiedBoundedAcceptancePolicy:
    """Return the verified bounded policy selected by checked configuration."""
    if run.bounded_acceptance_policy is None:
        raise ValueError("bounded publication selected without a verified policy")
    return run.bounded_acceptance_policy


def _retain_failure(
    run: CorrectionRunContext,
    workspace: CandidateWorkspace,
    stage: RunStage,
    error: Exception,
) -> None:
    """Persist a stage-qualified disposition without deriving codes from prose."""
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
    """Convert the subprocess semantic protocol to publication-owned records."""
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
    """Read frozen producer wall time and exact inventoried payload bytes."""
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
