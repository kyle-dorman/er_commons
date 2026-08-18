"""Sequence the six accepted document-content owners."""

from __future__ import annotations

import logging
from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.config import DocumentRunSpec, HierarchyDisposition
from er_commons.document_publication.process_inputs import ProcessConfigs, prepare_process_configs
from er_commons.document_publication.process_observations import (
    collect_process_warnings,
    content_parse_observations,
    content_parse_page_count,
)
from er_commons.document_publication.process_sequence import DocumentProcessSequence
from er_commons.document_publication.process_validation import validate_process_lineage
from er_commons.document_publication.records import ArtifactRef, PipelineResult

LOGGER = logging.getLogger(__name__)


def run_document_processes(
    *,
    data_root: Path,
    project_root: Path,
    run_spec: DocumentRunSpec,
    source_id: str,
    configs: ProcessConfigs | None = None,
    diagnostics_root: Path | None = None,
) -> PipelineResult:
    """Run document transformations and return one verified worker handoff."""
    disposition = run_spec.hierarchy_disposition(source_id)
    _require_bounded_authorization_input(data_root, disposition)
    active_configs = configs or prepare_process_configs(
        project_root=project_root,
        data_root=data_root,
        run_spec=run_spec,
        source_id=source_id,
    )
    sequence = DocumentProcessSequence(
        data_root=data_root,
        project_root=project_root,
        source_id=source_id,
        configs=active_configs,
        diagnostics_root=diagnostics_root,
        fresh=run_spec.lineage_mode(source_id) == "fresh_build",
    ).run()
    completions = sequence.completions
    active_configs = sequence.configs
    validate_process_lineage(
        data_root=data_root,
        source_id=source_id,
        hierarchy_disposition=disposition.model_dump(mode="json"),
        configs=active_configs,
        completions=completions,
    )
    raw_status, structured_errors = content_parse_observations(completions.content_parsing)
    return PipelineResult(
        source_id=source_id,
        raw_docling_status=raw_status,
        processed_pages=list(range(1, content_parse_page_count(completions.content_parsing) + 1)),
        structured_errors=structured_errors,
        warnings=collect_process_warnings(completions),
        final_candidate_root=str(completions.document_reference_linking.parents[1]),
        stage_completions={
            role: ArtifactRef(
                path=path.relative_to(data_root).as_posix(),
                sha256=sha256_file(path),
            )
            for role, path in completions.as_dict().items()
        },
        stage_timings=sequence.timings,
        resource_enforcement="validated_before_document_processes",
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
