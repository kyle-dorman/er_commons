"""Thin public application shell for one restartable corpus scope."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction.outcomes import observe_document_outcome
from er_commons.corpus_resolution.domain import ScopeHooks
from er_commons.corpus_resolution.evidence import (
    DocumentRunner,
    OutcomeObserver,
    TerminalEvidenceCollector,
)
from er_commons.corpus_resolution.pipeline import CorpusPipeline
from er_commons.corpus_resolution.preflight import prepare_scope_run


def run_scope(
    data_root: Path,
    run_spec_path: Path,
    *,
    document_runner: DocumentRunner | None = None,
    outcome_observer: OutcomeObserver = observe_document_outcome,
    hooks: ScopeHooks | None = None,
) -> Path:
    """Verify configuration, collect terminal evidence, and publish the join."""
    run = prepare_scope_run(data_root, run_spec_path)
    evidence = TerminalEvidenceCollector(
        document_runner=document_runner,
        outcome_observer=outcome_observer,
    ).collect(run)
    return CorpusPipeline(run, hooks or ScopeHooks()).publish(evidence)
