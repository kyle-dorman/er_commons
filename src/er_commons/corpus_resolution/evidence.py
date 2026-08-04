"""Run-or-reuse document candidates and observe verified terminal evidence."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from er_commons.corpus_extraction.outcomes import (
    DocumentTerminalEvidence,
    observe_document_outcome,
)
from er_commons.corpus_extraction.workflow import run_document
from er_commons.corpus_resolution.preflight import ScopeRun

LOGGER = logging.getLogger(__name__)
DocumentRunner = Callable[[Path, Path, str], Path]
OutcomeObserver = Callable[..., DocumentTerminalEvidence]


class TerminalEvidenceCollector:
    """Own the continuation boundary between document execution and accounting."""

    def __init__(
        self,
        *,
        document_runner: DocumentRunner | None = None,
        outcome_observer: OutcomeObserver = observe_document_outcome,
    ) -> None:
        self._runner = document_runner or _run_document
        self._observer = outcome_observer

    def collect(self, run: ScopeRun) -> tuple[DocumentTerminalEvidence, ...]:
        """Return one verified terminal outcome per declared source in order."""
        evidence = [
            self._run_and_observe(run, source_id, ordinal)
            for ordinal, source_id in enumerate(run.scope_spec.source_ids, start=1)
        ]
        return tuple(evidence)

    def _run_and_observe(
        self,
        run: ScopeRun,
        source_id: str,
        ordinal: int,
    ) -> DocumentTerminalEvidence:
        execution_error: Exception | None = None
        try:
            self._runner(run.data_root, run.document_spec_path, source_id)
        except Exception as error:
            execution_error = error
        try:
            terminal = self._observer(
                run.data_root,
                run.document_spec_path,
                source_id,
                source_ordinal=ordinal,
            )
        except Exception as observation_error:
            if execution_error is not None:
                raise execution_error from observation_error
            raise
        LOGGER.info("Observed terminal source=%s disposition=%s", source_id, terminal.disposition)
        return terminal


def _run_document(data_root: Path, run_spec: Path, source_id: str) -> Path:
    """Adapt the public document workflow to the collector's typed seam."""
    return run_document(data_root, run_spec, source_id)
