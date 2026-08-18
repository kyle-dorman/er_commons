"""Republish document evidence after replacing only its downstream owner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.candidates import (
    CandidateIdentity,
    build_candidate_identity,
    verify_identity_and_upstreams,
    write_candidate_identity,
)
from er_commons.corpus_extraction.downstream_replay_validation import (
    artifact_ref,
    verify_cross_reference_completion,
    verify_downstream_replay,
)
from er_commons.corpus_extraction.identity import canonical_digest
from er_commons.corpus_extraction.preflight import DocumentRun, prepare_document_run
from er_commons.corpus_extraction.records import (
    STAGE_COMPLETION_ROLES,
    ArtifactRef,
    DocumentIdentityRecord,
    DownstreamReplayRecord,
    PipelineResult,
)
from er_commons.corpus_extraction.storage import (
    import_content,
    publish_candidate,
    reserve_candidate_workspace,
    verify_candidate,
)
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class ReplayInputs:
    """Verified source lineage and replacement owner for one republication."""

    source_root: Path
    source_identity: DocumentIdentityRecord
    source_completion: Path
    source_inventory: Path
    cross_reference_root: Path
    stage_completions: dict[str, ArtifactRef]


def publish_downstream_replay(
    *,
    data_root: Path,
    document_run_spec: Path,
    source_id: str,
    source_candidate_root: Path,
    cross_reference_completion: Path,
) -> Path:
    """Publish a new document descendant without allocating a document attempt."""
    run = prepare_document_run(data_root, document_run_spec, source_id)
    inputs = _load_inputs(
        run,
        source_candidate_root=source_candidate_root,
        cross_reference_completion=cross_reference_completion,
    )
    result = _build_pipeline_result(run, inputs)
    identity = build_candidate_identity(
        run, content_root=inputs.cross_reference_root, result=result
    )

    existing = run.final_parent / identity.candidate_id
    if existing.is_dir():
        verify_candidate(existing, identity.candidate_id, run.source)
        verify_downstream_replay(existing, data_root=data_root)
        return existing / "records/completion_record.json"
    return _publish_new_candidate(run, inputs, result, identity)


def _load_inputs(
    run: DocumentRun,
    *,
    source_candidate_root: Path,
    cross_reference_completion: Path,
) -> ReplayInputs:
    source_completion = source_candidate_root / "records/completion_record.json"
    source_inventory = source_candidate_root / "records/artifact_inventory.json"
    identity_path = source_candidate_root / "records/document_identity.json"
    identity = DocumentIdentityRecord.model_validate_json(identity_path.read_bytes())
    verify_candidate(source_candidate_root, source_candidate_root.name, run.source)
    verify_identity_and_upstreams(
        source_candidate_root,
        identity=identity.model_dump(mode="json"),
        data_root=run.data_root,
    )
    cross_root = cross_reference_completion.parents[1]
    verify_cross_reference_completion(cross_root, cross_reference_completion)
    stages = {
        role: reference
        for role, reference in identity.stage_completions.items()
        if role != "cross_references"
    }
    stages["cross_references"] = artifact_ref(cross_reference_completion, run.data_root)
    return ReplayInputs(
        source_root=source_candidate_root,
        source_identity=identity,
        source_completion=source_completion,
        source_inventory=source_inventory,
        cross_reference_root=cross_root,
        stage_completions=stages,
    )


def _build_pipeline_result(run: DocumentRun, inputs: ReplayInputs) -> PipelineResult:
    """Adapt verified replay inputs to the existing candidate identity builder."""
    warnings = (
        ["reused upstream warning disposition"]
        if inputs.source_identity.terminal_state == "complete_with_warnings"
        else []
    )
    return PipelineResult(
        source_id=run.source.source_id,
        raw_docling_status="SUCCESS",
        processed_pages=list(range(1, run.source.pdf_page_count + 1)),
        structured_errors=[],
        warnings=warnings,
        final_candidate_root=str(inputs.cross_reference_root),
        stage_completions=inputs.stage_completions,
        stage_timings={role: 0.0 for role in STAGE_COMPLETION_ROLES},
        resource_enforcement="validated_before_content_owners",
    )


def _publish_new_candidate(
    run: DocumentRun,
    inputs: ReplayInputs,
    result: PipelineResult,
    identity: CandidateIdentity,
) -> Path:
    """Import the replacement content and atomically publish its sealed lineage."""
    staging_parent = run.extraction_root / "downstream_replays" / run.source.source_id
    workspace = reserve_candidate_workspace(staging_parent, run.final_parent)
    import_content(inputs.cross_reference_root, workspace.staging_root)
    write_candidate_identity(workspace.staging_root / "records", identity, run)
    replay = _build_replay_record(run, inputs, identity)
    write_json_atomic(
        workspace.staging_root / "records/downstream_replay.json",
        replay.model_dump(mode="json"),
    )
    completion = publish_candidate(
        workspace,
        transaction_id=replay.replay_id,
        candidate_id=identity.candidate_id,
        source=run.source,
        processed_pages=result.processed_pages,
    )
    verify_candidate(completion.parents[1], identity.candidate_id, run.source)
    verify_downstream_replay(completion.parents[1], data_root=run.data_root)
    return completion


def _build_replay_record(
    run: DocumentRun,
    inputs: ReplayInputs,
    identity: CandidateIdentity,
) -> DownstreamReplayRecord:
    replay_id = f"replayv1-{canonical_digest(_replay_preimage(inputs, identity))}"
    return DownstreamReplayRecord(
        replay_id=replay_id,
        source=run.source,
        source_candidate_id=inputs.source_root.name,
        source_completion_ref=artifact_ref(inputs.source_completion, run.data_root),
        source_inventory_ref=artifact_ref(inputs.source_inventory, run.data_root),
        reused_stage_completions={
            role: reference
            for role, reference in inputs.stage_completions.items()
            if role != "cross_references"
        },
        replacement_cross_reference_completion_ref=inputs.stage_completions["cross_references"],
        candidate_id=identity.candidate_id,
    )


def _replay_preimage(inputs: ReplayInputs, identity: CandidateIdentity) -> dict[str, object]:
    return {
        "schema_version": "er_commons.downstream_document_replay_identity.v1",
        "source_candidate_id": inputs.source_identity.candidate_id,
        "source_control_digest": inputs.source_identity.control_digest,
        "candidate_id": identity.candidate_id,
        "candidate_control_digest": identity.control_digest,
    }


__all__ = ["publish_downstream_replay", "verify_downstream_replay"]
