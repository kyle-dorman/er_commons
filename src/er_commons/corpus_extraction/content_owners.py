"""Sequence the six accepted document-content owners."""

from __future__ import annotations

import logging
from pathlib import Path

from er_commons.corpus_extraction.config import HierarchyDisposition, RunSpec
from er_commons.corpus_extraction.owner_diagnostics import run_owner_stage
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs, prepare_owner_configs
from er_commons.corpus_extraction.owner_observations import (
    collect_owner_warnings,
    producer_observations,
    producer_page_count,
)
from er_commons.corpus_extraction.owner_sequence import OwnerSequence
from er_commons.corpus_extraction.owner_validation import validate_owner_lineage
from er_commons.corpus_extraction.records import ArtifactRef, PipelineResult
from er_commons.source_freeze import sha256_file

LOGGER = logging.getLogger(__name__)
_timed = run_owner_stage


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
    sequence = OwnerSequence(
        data_root=data_root,
        project_root=project_root,
        source_id=source_id,
        configs=active_configs,
        diagnostics_root=diagnostics_root,
        fresh=run_spec.lineage_mode(source_id) == "fresh_build",
    ).run()
    completions = sequence.completions
    active_configs = sequence.configs
    validate_owner_lineage(
        data_root=data_root,
        source_id=source_id,
        hierarchy_disposition=disposition.model_dump(mode="json"),
        configs=active_configs,
        completions=completions,
    )
    raw_status, structured_errors = producer_observations(completions.baseline_producer)
    return PipelineResult(
        source_id=source_id,
        raw_docling_status=raw_status,
        processed_pages=list(range(1, producer_page_count(completions.baseline_producer) + 1)),
        structured_errors=structured_errors,
        warnings=collect_owner_warnings(completions),
        final_candidate_root=str(completions.cross_references.parents[1]),
        stage_completions={
            role: ArtifactRef(
                path=path.relative_to(data_root).as_posix(),
                sha256=sha256_file(path),
            )
            for role, path in completions.as_dict().items()
        },
        stage_timings=sequence.timings,
        resource_enforcement="validated_before_content_owners",
    )


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
