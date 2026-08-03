"""Thin public workflow for the human-owned Task 03E.5 implementation."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from er_commons.canonical_extraction.publication import publish_workspace, reserve_workspace
from er_commons.cross_reference_enrichment.catalog import CorpusDocumentCatalog
from er_commons.cross_reference_enrichment.comparison import (
    compare_policy_correction,
    write_comparison_report,
)
from er_commons.cross_reference_enrichment.config import RuntimeContext
from er_commons.cross_reference_enrichment.construction import (
    CandidateSource,
    CrossReferenceCandidateBuilder,
)
from er_commons.cross_reference_enrichment.identity import build_candidate_identity
from er_commons.cross_reference_enrichment.policy import default_mention_policy
from er_commons.cross_reference_enrichment.publication import (
    CandidateWriter,
    preserve_failed_attempt,
    verify_completed_candidate,
)
from er_commons.cross_reference_enrichment.types import JsonObject
from er_commons.cross_reference_enrichment.validation import (
    validate_candidate_build,
    validate_serialized_terminal_records,
)


def run_cross_reference_enrichment(data_root: Path, config_path: Path) -> tuple[Path, Path]:
    """Verify → identify/reuse → build twice → compare → publish atomically."""
    context = RuntimeContext.load(data_root, config_path)
    identity = build_candidate_identity(context)
    candidate_id = identity["extraction_id"]
    candidate_root = context.task_root / candidate_id
    if candidate_root.exists():
        completion = verify_completed_candidate(candidate_root, candidate_id)
        comparison = _compare_and_record(context, candidate_root, candidate_id)
        return completion, comparison
    return _build_compare_and_publish(context, identity)


def _build_compare_and_publish(context: RuntimeContext, identity: JsonObject) -> tuple[Path, Path]:
    candidate_id = str(identity["extraction_id"])
    upstream = CandidateSource.load(context.upstream_root)
    catalog = CorpusDocumentCatalog.from_source_manifest(context.source_manifest_path)
    policy = default_mention_policy()
    workspaces = []
    try:
        for _ in range(2):
            workspace = reserve_workspace(context.task_root, candidate_id, uuid.uuid4().hex)
            workspaces.append(workspace)
            build = CrossReferenceCandidateBuilder(
                source=upstream,
                upstream_candidate_id=context.config.upstream_candidate_id,
                candidate_id=candidate_id,
                policy=policy,
                corpus_catalog=catalog,
            ).build()
            validate_candidate_build(
                build=build,
                upstream_root=context.upstream_root,
                upstream_candidate_id=context.config.upstream_candidate_id,
                candidate_id=candidate_id,
                schema_path=context.project_root / context.config.schema_relative_path,
                identity_extension=identity["cross_reference_contract"],
            )
            CandidateWriter(upstream).write(workspace.staging_root, build, identity)
            validate_serialized_terminal_records(
                workspace.staging_root,
                context.project_root / context.config.schema_relative_path,
            )
        if _file_bytes(workspaces[0].staging_root) != _file_bytes(workspaces[1].staging_root):
            raise ValueError("fresh human-owned candidate builds differ")
        comparison = _compare_and_record(context, workspaces[0].staging_root, candidate_id)
        shutil.rmtree(workspaces[1].staging_root)
        completion = publish_workspace(workspaces[0])
        verify_completed_candidate(context.task_root / candidate_id, candidate_id)
        return completion, comparison
    except Exception:
        for workspace in workspaces:
            if workspace.staging_root.exists():
                preserve_failed_attempt(context.task_root, workspace.staging_root)
        raise


def _compare_and_record(context: RuntimeContext, candidate_root: Path, candidate_id: str) -> Path:
    result = compare_policy_correction(
        reference_root=context.reference_root,
        candidate_root=candidate_root,
        reference_id=context.config.reference_candidate_id,
        candidate_id=candidate_id,
        policy=default_mention_policy(),
    )
    report = write_comparison_report(context.comparison_root, result)
    if result.status != "policy_corrected":
        raise ValueError(f"cross-reference correction audit failed: {report}")
    return report


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
