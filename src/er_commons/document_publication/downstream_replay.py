"""Republish document evidence after replacing only its final linked product."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.accepted_inputs import verify_prepared_document_run
from er_commons.document_publication.candidate_identity_validation import (
    verify_identity_and_upstreams,
)
from er_commons.document_publication.candidates import (
    CandidateIdentity,
    build_candidate_identity,
    write_candidate_identity,
)
from er_commons.document_publication.downstream_replay_validation import (
    artifact_ref,
    build_replay_record,
    verify_cross_reference_completion,
    verify_downstream_replay,
)
from er_commons.document_publication.preflight import DocumentRun, prepare_accepted_document_run
from er_commons.document_publication.records import (
    DOCUMENT_PROCESS_NAMES,
    ArtifactRef,
    DocumentCompletion,
    DocumentIdentityRecord,
    PipelineResult,
)
from er_commons.document_publication.storage import (
    import_content,
    publish_candidate,
    reserve_candidate_workspace,
    sealed_content_inventory,
    verify_candidate_metadata,
)


@dataclass(frozen=True)
class ReplayInputs:
    """Verified source lineage and replacement linked product for republication."""

    source_root: Path
    source_identity: DocumentIdentityRecord
    source_completion: Path
    source_inventory: Path
    source_inventory_sha256: str
    cross_reference_root: Path
    stage_completions: dict[str, ArtifactRef]
    content_inventory: dict[str, Any]


def publish_downstream_replay(
    *,
    data_root: Path,
    document_run_spec: Path,
    source_id: str,
    source_candidate_root: Path,
    cross_reference_completion: Path,
    budget: VerificationBudget | None = None,
    prepared_run: DocumentRun | None = None,
) -> Path:
    """Publish a new document descendant without allocating a document attempt."""
    budget = budget or VerificationBudget()
    run = prepared_run or prepare_accepted_document_run(
        data_root, document_run_spec, source_id, budget=budget
    )
    verify_prepared_document_run(run, data_root, document_run_spec, source_id, budget)
    inputs = _load_inputs(
        run,
        source_candidate_root=source_candidate_root,
        cross_reference_completion=cross_reference_completion,
        budget=budget,
    )
    result = _build_pipeline_result(run, inputs)
    identity = build_candidate_identity(
        run,
        content_root=inputs.cross_reference_root,
        result=result,
        recorded_content_inventory=inputs.content_inventory,
    )

    existing = run.final_parent / identity.candidate_id
    if existing.is_dir():
        verify_candidate_metadata(existing, identity.candidate_id, run.source, budget=budget)
        verify_downstream_replay(existing, data_root=data_root, budget=budget)
        return existing / "records/completion_record.json"
    return _publish_new_candidate(run, inputs, result, identity, budget=budget)


def _load_inputs(
    run: DocumentRun,
    *,
    source_candidate_root: Path,
    cross_reference_completion: Path,
    budget: VerificationBudget,
) -> ReplayInputs:
    source_completion = source_candidate_root / "records/completion_record.json"
    source_inventory = source_candidate_root / "records/artifact_inventory.json"
    identity_path = source_candidate_root / "records/document_identity.json"
    identity = DocumentIdentityRecord.model_validate(
        budget.read_json(
            identity_path,
            role="identity_preimage",
            source_id=run.source.source_id,
            root=source_candidate_root,
        )
    )
    verify_candidate_metadata(
        source_candidate_root, source_candidate_root.name, run.source, budget=budget
    )
    verify_identity_and_upstreams(
        source_candidate_root,
        identity=identity.model_dump(mode="json"),
        data_root=run.data_root,
        budget=budget,
    )
    cross_root = cross_reference_completion.parents[1]
    verify_cross_reference_completion(cross_root, cross_reference_completion)
    stages = {
        role: reference
        for role, reference in identity.stage_completions.items()
        if role != "linked_document"
    }
    stages["linked_document"] = artifact_ref(
        cross_reference_completion, run.data_root, budget=budget
    )
    return ReplayInputs(
        source_root=source_candidate_root,
        source_identity=identity,
        source_completion=source_completion,
        source_inventory=source_inventory,
        source_inventory_sha256=DocumentCompletion.model_validate(
            budget.read_json(
                source_completion,
                role="completion",
                source_id=run.source.source_id,
                root=source_candidate_root,
            )
        ).candidate_inventory.sha256,
        cross_reference_root=cross_root,
        stage_completions=stages,
        content_inventory=sealed_content_inventory(
            cross_root, budget=budget, source_id=run.source.source_id
        ),
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
        stage_timings={name: 0.0 for name in DOCUMENT_PROCESS_NAMES},
        resource_enforcement="validated_before_document_processes",
    )


def _publish_new_candidate(
    run: DocumentRun,
    inputs: ReplayInputs,
    result: PipelineResult,
    identity: CandidateIdentity,
    *,
    budget: VerificationBudget,
) -> Path:
    """Import the replacement content and atomically publish its sealed lineage."""
    staging_parent = run.extraction_root / "downstream_replays" / run.source.source_id
    workspace = reserve_candidate_workspace(staging_parent, run.final_parent)
    import_content(inputs.cross_reference_root, workspace.staging_root)
    write_candidate_identity(workspace.staging_root / "records", identity, run)
    replay = build_replay_record(run, inputs, identity, budget=budget)
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
        recorded_files={
            "content/" + row["path"]: {**row, "path": "content/" + row["path"]}
            for row in inputs.content_inventory["files"]
        },
    )
    verify_candidate_metadata(
        completion.parents[1], identity.candidate_id, run.source, budget=budget
    )
    verify_downstream_replay(completion.parents[1], data_root=run.data_root, budget=budget)
    return completion


__all__ = ["publish_downstream_replay", "verify_downstream_replay"]
