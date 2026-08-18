"""Thin public application shell for one restartable collection."""

from __future__ import annotations

from pathlib import Path

from er_commons.collection_processing.document_evidence import (
    DocumentRunner,
    OutcomeObserver,
    TerminalEvidenceCollector,
)
from er_commons.collection_processing.domain import CollectionHooks
from er_commons.collection_processing.pipeline import CollectionPipeline
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.document_publication.outcomes import observe_document_outcome


def assemble_collection_handoff(
    data_root: Path,
    run_spec_path: Path,
    *,
    document_runner: DocumentRunner | None = None,
    outcome_observer: OutcomeObserver = observe_document_outcome,
    hooks: CollectionHooks | None = None,
) -> Path:
    """Verify configuration, collect terminal evidence, and publish the join."""
    run = prepare_collection_run(data_root, run_spec_path)
    evidence = TerminalEvidenceCollector(
        document_runner=document_runner,
        outcome_observer=outcome_observer,
    ).collect(run)
    return CollectionPipeline(run, hooks or CollectionHooks()).publish(evidence)
