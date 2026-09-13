"""Run-or-reuse document candidates and observe verified terminal evidence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from er_commons.collection_processing.imported_evidence import (
    build_imported_terminal_evidence,
)
from er_commons.collection_processing.preflight import CollectionRun
from er_commons.document_publication.outcomes import (
    observe_document_outcome,
    observe_downstream_replay_outcome,
)
from er_commons.document_publication.published_document import DocumentTerminalEvidence
from er_commons.document_publication.workflow import publish_document

LOGGER = logging.getLogger(__name__)


class DocumentRunner(Protocol):
    """Execute one document candidate through the publication boundary."""

    def __call__(self, data_root: Path, run_spec: Path, source_id: str, /) -> Path: ...


class OutcomeObserver(Protocol):
    """Observe one source's retained terminal evidence in collection order."""

    def __call__(
        self,
        data_root: Path,
        document_run_spec: Path,
        source_id: str,
        *,
        source_ordinal: int,
    ) -> DocumentTerminalEvidence: ...


class TerminalEvidenceCollector:
    """Own the continuation boundary between document execution and accounting."""

    def __init__(
        self,
        *,
        document_runner: DocumentRunner | None = None,
        outcome_observer: OutcomeObserver | None = None,
    ) -> None:
        self._runner = document_runner or _run_document
        self._observer = outcome_observer

    def collect(self, run: CollectionRun) -> tuple[DocumentTerminalEvidence, ...]:
        """Return one verified terminal outcome per declared source in order."""
        if run.collection_spec.document_evidence_mode == "imported_downstream_selection":
            if (
                run.imported_selection is None
                or run.artifact_resolver is None
                or run.collection_spec.imported_selection_ref is None
            ):
                raise ValueError("imported selection mode lacks verified preflight evidence")
            return build_imported_terminal_evidence(
                run.imported_selection,
                selection_ref=run.collection_spec.imported_selection_ref.model_dump(mode="json"),
                resolver=run.artifact_resolver,
            )
        evidence = [
            self._run_and_observe(run, source_id, ordinal)
            for ordinal, source_id in enumerate(run.collection_spec.source_ids, start=1)
        ]
        return tuple(evidence)

    def _run_and_observe(
        self,
        run: CollectionRun,
        source_id: str,
        ordinal: int,
    ) -> DocumentTerminalEvidence:
        execution_error: Exception | None = None
        if run.collection_spec.document_evidence_mode == "document_attempt":
            try:
                self._runner(run.data_root, run.document_spec_path, source_id)
            except Exception as error:
                execution_error = error
                LOGGER.warning(
                    "Document execution failed before terminal observation "
                    "source=%s error_class=%s detail=%s",
                    source_id,
                    type(error).__name__,
                    error,
                    exc_info=True,
                )
        try:
            observer = self._observer or (
                observe_downstream_replay_outcome
                if run.collection_spec.document_evidence_mode == "downstream_replay_only"
                else observe_document_outcome
            )
            terminal = observer(
                run.data_root,
                run.document_spec_path,
                source_id,
                source_ordinal=ordinal,
            )
        except Exception as observation_error:
            if execution_error is not None:
                raise execution_error from observation_error
            raise
        if execution_error is not None:
            LOGGER.info(
                "Retained terminal evidence allowed collection continuation "
                "source=%s disposition=%s execution_error_class=%s",
                source_id,
                terminal.disposition,
                type(execution_error).__name__,
            )
        LOGGER.info("Observed terminal source=%s disposition=%s", source_id, terminal.disposition)
        return terminal


def _run_document(data_root: Path, run_spec: Path, source_id: str) -> Path:
    """Adapt the public document workflow to the collector's typed seam."""
    return publish_document(data_root, run_spec, source_id)
