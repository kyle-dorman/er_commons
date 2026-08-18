"""Thin public workflow for the human-owned Task 03E.5 implementation."""

from __future__ import annotations

import uuid
from pathlib import Path

from er_commons.canonical_extraction.publication import publish_workspace, reserve_workspace
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
    write_failed_build_snapshot,
)
from er_commons.cross_reference_enrichment.types import JsonObject
from er_commons.cross_reference_enrichment.validation import (
    validate_candidate_build,
    validate_serialized_terminal_records,
)
from er_commons.source_family_catalog import SourceFamilyCatalog


def run_cross_reference_enrichment(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
) -> Path:
    """Verify inputs, reuse, or build, validate, and publish once."""
    context = RuntimeContext.load(
        data_root,
        config_path,
        config_identity_path=config_identity_path,
    )
    identity = build_candidate_identity(context)
    candidate_id = identity["extraction_id"]
    candidate_root = context.task_root / candidate_id
    if candidate_root.exists():
        return verify_completed_candidate(candidate_root, candidate_id)
    return _build_validate_and_publish(context, identity)


def _build_validate_and_publish(context: RuntimeContext, identity: JsonObject) -> Path:
    candidate_id = str(identity["extraction_id"])
    upstream = CandidateSource.load(context.upstream_root)
    catalog = SourceFamilyCatalog.load(context.source_family_catalog_path)
    policy = default_mention_policy()
    workspace = None
    build = None
    try:
        workspace = reserve_workspace(context.task_root, candidate_id, uuid.uuid4().hex)
        build = CrossReferenceCandidateBuilder(
            source=upstream,
            upstream_candidate_id=context.config.upstream_candidate_id,
            candidate_id=candidate_id,
            policy=policy,
            source_family_catalog=catalog,
            source_family_catalog_sha256=context.source_family_catalog_sha256,
            source_id=context.config.source_id,
        ).build()
        validate_candidate_build(
            build=build,
            upstream_root=context.upstream_root,
            upstream_candidate_id=context.config.upstream_candidate_id,
            candidate_id=candidate_id,
            schema_path=context.project_root / context.config.schema_relative_path,
            identity_extension=identity["cross_reference_contract"],
            source_family_catalog=catalog,
            source_id=context.config.source_id,
            source_family_catalog_sha256=context.source_family_catalog_sha256,
        )
        CandidateWriter(upstream).write(workspace.staging_root, build, identity)
        validate_serialized_terminal_records(
            workspace.staging_root,
            context.project_root / context.config.schema_relative_path,
        )
        completion = publish_workspace(workspace)
        verify_completed_candidate(context.task_root / candidate_id, candidate_id)
        return completion
    except Exception as error:
        if workspace is not None and workspace.staging_root.exists():
            if build is not None:
                write_failed_build_snapshot(
                    workspace.staging_root,
                    build=build,
                    identity=identity,
                    error=error,
                )
            preserve_failed_attempt(context.task_root, workspace.staging_root)
        raise
