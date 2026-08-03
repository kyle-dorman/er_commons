"""Sequence the six accepted document-content owners."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from er_commons.canonical_extraction import run_document_canonicalization
from er_commons.corpus_extraction.config import HierarchyDisposition, RunSpec
from er_commons.corpus_extraction.owner_inputs import prepare_owner_configs
from er_commons.corpus_extraction.owner_observations import (
    collect_owner_warnings,
    producer_observations,
    producer_page_count,
)
from er_commons.corpus_extraction.owner_validation import (
    OwnerCompletions,
    validate_owner_lineage,
)
from er_commons.corpus_extraction.records import ArtifactRef, PipelineResult
from er_commons.cross_reference_enrichment import run_cross_reference_enrichment
from er_commons.document_extraction import run_complete_document_producer
from er_commons.hierarchy_correction import run_hierarchy_correction
from er_commons.semantic_materialization import run_semantic_materialization
from er_commons.source_freeze import sha256_file

LOGGER = logging.getLogger(__name__)


def run_content_owners(
    *, data_root: Path, project_root: Path, run_spec: RunSpec, source_id: str
) -> PipelineResult:
    """Run content owners in order and return one verified worker handoff."""
    disposition = run_spec.hierarchy_disposition(source_id)
    _require_bounded_authorization_input(data_root, disposition)
    configs = prepare_owner_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )

    timings: dict[str, float] = {}
    baseline = _timed(
        "baseline_producer",
        timings,
        lambda: run_complete_document_producer(data_root, configs.baseline_producer),
    )
    hierarchy = _timed(
        "hierarchy_producer",
        timings,
        lambda: run_complete_document_producer(data_root, configs.hierarchy_producer),
    )
    canonical = _timed(
        "canonical",
        timings,
        lambda: run_document_canonicalization(data_root, configs.canonical),
    )
    correction = _timed(
        "hierarchy_correction",
        timings,
        lambda: run_hierarchy_correction(data_root, configs.hierarchy_correction),
    )
    semantic = _timed(
        "semantic",
        timings,
        lambda: run_semantic_materialization(data_root, configs.semantic)[0],
    )
    cross_references = _timed(
        "cross_references",
        timings,
        lambda: run_cross_reference_enrichment(data_root, configs.cross_references)[0],
    )
    completions = OwnerCompletions(
        baseline_producer=baseline,
        hierarchy_producer=hierarchy,
        canonical=canonical,
        hierarchy_correction=correction,
        semantic=semantic,
        cross_references=cross_references,
    )
    validate_owner_lineage(
        data_root=data_root,
        source_id=source_id,
        hierarchy_disposition=disposition.model_dump(mode="json"),
        configs=configs,
        completions=completions,
    )
    raw_status, structured_errors = producer_observations(baseline)
    return PipelineResult(
        source_id=source_id,
        raw_docling_status=raw_status,
        processed_pages=list(range(1, producer_page_count(baseline) + 1)),
        structured_errors=structured_errors,
        warnings=collect_owner_warnings(completions),
        final_candidate_root=str(cross_references.parents[1]),
        stage_completions={
            role: ArtifactRef(
                path=path.relative_to(data_root).as_posix(),
                sha256=sha256_file(path),
            )
            for role, path in completions.as_dict().items()
        },
        stage_timings=timings,
        resource_enforcement="validated_before_content_owners",
    )


def _timed[T](name: str, timings: dict[str, float], operation: Callable[[], T]) -> T:
    """Measure and log one plainly named owner stage."""
    LOGGER.info("Starting content owner %s", name)
    started = time.monotonic()
    result = operation()
    timings[name] = time.monotonic() - started
    LOGGER.info("Completed content owner %s in %.3fs", name, timings[name])
    return result


def _require_bounded_authorization_input(
    data_root: Path, disposition: HierarchyDisposition
) -> None:
    if disposition.authority != "bounded_acceptance":
        return
    relative_path = disposition.authorization_relative_path
    if relative_path is None:
        raise ValueError("bounded hierarchy disposition lacks authorization path")
    path = data_root / relative_path
    if not path.is_file():
        raise FileNotFoundError(path)
