"""Sequence the six accepted document-content owners."""

from __future__ import annotations

import logging
from pathlib import Path

from er_commons.canonical_extraction import run_document_canonicalization
from er_commons.corpus_extraction.config import HierarchyDisposition, RunSpec
from er_commons.corpus_extraction.owner_diagnostics import run_owner_stage
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs, prepare_owner_configs
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
    *,
    data_root: Path,
    project_root: Path,
    run_spec: RunSpec,
    source_id: str,
    configs: OwnerConfigs | None = None,
    diagnostics_root: Path | None = None,
) -> PipelineResult:
    """Run content owners in order and return one verified worker handoff."""
    disposition = run_spec.hierarchy_disposition(source_id)
    _require_bounded_authorization_input(data_root, disposition)
    active_configs = configs or prepare_owner_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    timings: dict[str, float] = {}
    baseline = run_owner_stage(
        "baseline_producer",
        timings,
        lambda: run_complete_document_producer(data_root, active_configs.baseline_producer),
        diagnostics_root=diagnostics_root,
        ordinal=1,
        data_root=data_root,
    )
    hierarchy = run_owner_stage(
        "hierarchy_producer",
        timings,
        lambda: run_complete_document_producer(data_root, active_configs.hierarchy_producer),
        diagnostics_root=diagnostics_root,
        ordinal=2,
        data_root=data_root,
    )
    canonical = run_owner_stage(
        "canonical",
        timings,
        lambda: run_document_canonicalization(data_root, active_configs.canonical),
        diagnostics_root=diagnostics_root,
        ordinal=3,
        data_root=data_root,
    )
    correction = run_owner_stage(
        "hierarchy_correction",
        timings,
        lambda: run_hierarchy_correction(data_root, active_configs.hierarchy_correction),
        diagnostics_root=diagnostics_root,
        ordinal=4,
        data_root=data_root,
    )
    semantic = run_owner_stage(
        "semantic",
        timings,
        lambda: run_semantic_materialization(data_root, active_configs.semantic),
        diagnostics_root=diagnostics_root,
        ordinal=5,
        data_root=data_root,
    )
    cross_references = run_owner_stage(
        "cross_references",
        timings,
        lambda: run_cross_reference_enrichment(data_root, active_configs.cross_references),
        diagnostics_root=diagnostics_root,
        ordinal=6,
        data_root=data_root,
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
        configs=active_configs,
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


_timed = run_owner_stage


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
