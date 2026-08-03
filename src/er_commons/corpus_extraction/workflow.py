"""Readable application shell for one restartable document transaction."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from er_commons.corpus_extraction.attempts import AttemptSession, next_attempt_number
from er_commons.corpus_extraction.candidates import find_reusable_candidate
from er_commons.corpus_extraction.config import RunSpec
from er_commons.corpus_extraction.hooks import WorkflowHooks
from er_commons.corpus_extraction.observability import record_resource_enforcement
from er_commons.corpus_extraction.preflight import DocumentRun, prepare_document_run
from er_commons.corpus_extraction.process import ProcessOutcome, run_isolated_document
from er_commons.corpus_extraction.publication import (
    complete_attempt,
    retain_unexpected_failure,
)

LOGGER = logging.getLogger(__name__)
Executor = Callable[[Path, Path, Path, str, Path, RunSpec], ProcessOutcome]


def run_document(
    data_root: Path,
    run_spec_path: Path,
    source_id: str,
    *,
    executor: Executor | None = None,
    hooks: WorkflowHooks | None = None,
) -> Path:
    """Reuse or run one complete document until success or terminal failure."""
    run = prepare_document_run(data_root, run_spec_path, source_id)
    LOGGER.info(
        "Prepared document run source=%s scope=%s",
        run.source.source_id,
        run.scope_id,
    )
    reusable = find_reusable_candidate(run)
    if reusable is not None:
        return reusable

    execute = executor or _execute_in_child_process
    active_hooks = hooks or WorkflowHooks()
    first_attempt = next_attempt_number(run)
    for number in range(first_attempt, run.maximum_attempts + 1):
        completion = _run_attempt(run, number, execute, active_hooks)
        if completion is not None:
            return completion
    raise RuntimeError("document retry loop ended without a terminal result")


def _run_attempt(
    run: DocumentRun, number: int, executor: Executor, hooks: WorkflowHooks
) -> Path | None:
    """Execute and finalize one retained attempt."""
    attempt = AttemptSession.start(run, number)
    LOGGER.info(
        "Starting document attempt source=%s attempt=%s transaction=%s",
        run.source.source_id,
        number,
        attempt.transaction_id,
    )
    try:
        outcome = executor(
            run.data_root,
            run.project_root,
            run.run_spec_path,
            run.source.source_id,
            attempt.root,
            run.spec,
        )
        if outcome.result is not None:
            record_resource_enforcement(
                attempt.root,
                transaction_id=attempt.transaction_id,
                enforcement=outcome.result.resource_enforcement,
            )
        return complete_attempt(run, attempt, outcome, hooks=hooks)
    except Exception as error:
        disposition = retain_unexpected_failure(run, attempt, error, hooks=hooks)
        if disposition == "failed_terminal":
            raise
        return None


def _execute_in_child_process(
    data_root: Path,
    project_root: Path,
    run_spec_path: Path,
    source_id: str,
    attempt_root: Path,
    spec: RunSpec,
) -> ProcessOutcome:
    """Run content owners behind the hard per-document process boundary."""
    return run_isolated_document(
        data_root=data_root,
        project_root=project_root,
        run_spec_path=run_spec_path,
        source_id=source_id,
        attempt_root=attempt_root,
        resources=spec.resource_policy,
    )
