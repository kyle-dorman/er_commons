"""Translate worker outcomes into retained failures or published candidates."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.attempts import AttemptSession
from er_commons.document_publication.candidates import (
    build_candidate_identity,
    write_candidate_identity,
)
from er_commons.document_publication.hooks import WorkflowHooks
from er_commons.document_publication.lifecycle import Disposition, classify_failure
from er_commons.document_publication.observability import record_observability
from er_commons.document_publication.preflight import DocumentRun
from er_commons.document_publication.process import ProcessOutcome
from er_commons.document_publication.process_diagnostics import retained_stage_timings
from er_commons.document_publication.records import DOCUMENT_PRODUCT_ROLE_SET, PipelineResult
from er_commons.document_publication.storage import (
    candidate_output_bytes,
    import_content,
    publish_candidate,
    reserve_candidate_workspace,
    verify_candidate,
)

LOGGER = logging.getLogger(__name__)
PUBLICATION_GATE_MESSAGE = (
    "Docling SUCCESS, zero structured errors, and full-page accounting required"
)


def complete_attempt(
    run: DocumentRun,
    attempt: AttemptSession,
    outcome: ProcessOutcome,
    *,
    hooks: WorkflowHooks,
) -> Path | None:
    """Retain a rejected outcome or atomically publish one accepted candidate."""
    exhausted = attempt.number >= run.maximum_attempts
    if outcome.timed_out or outcome.result is None:
        _retain_child_failure(run, attempt, outcome, exhausted=exhausted, hooks=hooks)
        return None
    if not _passes_publication_gate(outcome.result, run):
        _retain_gate_failure(run, attempt, outcome.result, exhausted=exhausted, hooks=hooks)
        return None
    return _publish_success(run, attempt, outcome.result, hooks=hooks)


def retain_unexpected_failure(
    run: DocumentRun,
    attempt: AttemptSession,
    error: Exception,
    *,
    hooks: WorkflowHooks,
) -> Disposition:
    """Persist diagnostics for an exception raised outside a typed worker outcome."""
    record_observability(
        attempt.root,
        transaction_id=attempt.transaction_id,
        wall_seconds=attempt.wall_seconds(),
        output_bytes=candidate_output_bytes(attempt.root),
        stage_timings=retained_stage_timings(attempt.root),
    )
    disposition: Disposition = (
        "failed_terminal"
        if attempt.number >= run.maximum_attempts
        else classify_failure(type(error).__name__)
    )
    attempt.events.transition(disposition, "FAILURE")
    hooks.before_attempt_record(disposition)
    attempt.record(
        source_id=run.source.source_id,
        disposition=disposition,
        failure_class=type(error).__name__,
        message=str(error),
    )
    LOGGER.warning(
        "Retained %s attempt %s for %s after %s: %s",
        disposition,
        attempt.number,
        run.source.source_id,
        type(error).__name__,
        error,
    )
    return disposition


def _retain_child_failure(
    run: DocumentRun,
    attempt: AttemptSession,
    outcome: ProcessOutcome,
    *,
    exhausted: bool,
    hooks: WorkflowHooks,
) -> None:
    record_observability(
        attempt.root,
        transaction_id=attempt.transaction_id,
        wall_seconds=attempt.wall_seconds(),
        output_bytes=candidate_output_bytes(attempt.root),
        stage_timings=retained_stage_timings(attempt.root),
    )
    disposition: Disposition = (
        "failed_terminal"
        if exhausted
        else classify_failure("ChildProcessError", timed_out=outcome.timed_out)
    )
    attempt.events.transition(disposition, "FAILURE" if not outcome.timed_out else None)
    hooks.before_attempt_record(disposition)
    attempt.record(
        source_id=run.source.source_id,
        disposition=disposition,
        failure_class=("OuterProcessDeadline" if outcome.timed_out else "ChildProcessError"),
        message=outcome.diagnostic_text,
    )
    LOGGER.warning(
        "Retained %s child outcome for %s attempt %s",
        disposition,
        run.source.source_id,
        attempt.number,
    )


def _retain_gate_failure(
    run: DocumentRun,
    attempt: AttemptSession,
    result: PipelineResult,
    *,
    exhausted: bool,
    hooks: WorkflowHooks,
) -> None:
    record_observability(
        attempt.root,
        transaction_id=attempt.transaction_id,
        wall_seconds=attempt.wall_seconds(),
        output_bytes=candidate_output_bytes(attempt.root),
        stage_timings=result.stage_timings,
    )
    disposition: Disposition = "failed_terminal" if exhausted else "failed_retryable"
    attempt.events.transition(disposition, result.raw_docling_status)
    hooks.before_attempt_record(disposition)
    attempt.record(
        source_id=run.source.source_id,
        disposition=disposition,
        failure_class="ProjectPublicationGate",
        message=PUBLICATION_GATE_MESSAGE,
    )
    LOGGER.warning(
        "Rejected %s attempt %s at publication gate: status=%s errors=%s pages=%s/%s",
        run.source.source_id,
        attempt.number,
        result.raw_docling_status,
        len(result.structured_errors),
        len(result.processed_pages),
        run.source.pdf_page_count,
    )


def _publish_success(
    run: DocumentRun,
    attempt: AttemptSession,
    result: PipelineResult,
    *,
    hooks: WorkflowHooks,
) -> Path:
    _verify_pipeline_handoff(run.data_root, result, run)
    workspace = reserve_candidate_workspace(attempt.root, run.final_parent)
    content_root = import_content(Path(result.final_candidate_root), workspace.staging_root)
    identity = build_candidate_identity(
        run,
        content_root=content_root,
        result=result,
    )
    write_candidate_identity(workspace.staging_root / "records", identity, run)
    record_observability(
        attempt.root,
        transaction_id=attempt.transaction_id,
        wall_seconds=attempt.wall_seconds(),
        output_bytes=candidate_output_bytes(workspace.staging_root),
        stage_timings=result.stage_timings,
    )
    completion = publish_candidate(
        workspace,
        transaction_id=attempt.transaction_id,
        candidate_id=identity.candidate_id,
        source=run.source,
        processed_pages=result.processed_pages,
    )
    hooks.after_candidate_publish(completion)
    attempt.events.transition(identity.terminal_state, "SUCCESS")
    hooks.before_attempt_record(identity.terminal_state)
    attempt.record(
        source_id=run.source.source_id,
        disposition=identity.terminal_state,
        failure_class=None,
        message=None,
        completion_path=str(completion),
    )
    verify_candidate(completion.parents[1], identity.candidate_id, run.source)
    LOGGER.info(
        "Published document candidate %s for %s",
        identity.candidate_id,
        run.source.source_id,
    )
    return completion


def _passes_publication_gate(result: PipelineResult, run: DocumentRun) -> bool:
    expected_pages = list(range(1, run.source.pdf_page_count + 1))
    return bool(
        result.source_id == run.source.source_id
        and result.raw_docling_status == "SUCCESS"
        and not result.structured_errors
        and result.processed_pages == expected_pages
    )


def _verify_pipeline_handoff(data_root: Path, result: PipelineResult, run: DocumentRun) -> None:
    """Verify product completion seals and final canonical source identity."""
    if set(result.stage_completions) != DOCUMENT_PRODUCT_ROLE_SET:
        raise ValueError("document-process handoff lacks the exact six product completions")
    resolved_completions: dict[str, Path] = {}
    for role, reference in result.stage_completions.items():
        path = (data_root / reference.path).resolve()
        if (
            not path.is_relative_to(data_root.resolve())
            or not path.is_file()
            or sha256_file(path) != reference.sha256
        ):
            raise ValueError(f"document-product completion seal differs: {role}")
        resolved_completions[role] = path
    final_root = Path(result.final_candidate_root).resolve()
    linked_document_root = resolved_completions["linked_document"].parents[1]
    allowed_relative = (
        run.execution_preflight.final_artifact_relative_root
        if run.execution_preflight is not None
        else Path(".")
    )
    allowed_root = (data_root / allowed_relative).resolve()
    if (
        not final_root.is_relative_to(data_root.resolve())
        or not final_root.is_relative_to(allowed_root)
        or final_root != linked_document_root
    ):
        raise ValueError(
            "final content candidate does not match the linked-document completion: "
            f"final={final_root}, linked_document={linked_document_root}, allowed={allowed_root}"
        )
    document_path = final_root / "canonical" / "documents.jsonl"
    if not document_path.is_file():
        raise FileNotFoundError(document_path)
    document = json.loads(document_path.read_text().splitlines()[0])
    observed = (
        document.get("source_id"),
        document.get("source_sha256"),
        document.get("page_count"),
    )
    expected = (
        run.source.source_id,
        run.source.sha256,
        run.source.pdf_page_count,
    )
    if observed != expected:
        raise ValueError(
            "final content candidate differs from selected source identity: "
            f"expected={expected}, observed={observed}, path={document_path}"
        )
