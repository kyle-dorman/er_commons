"""Single-build validation, reuse, and atomic-publication lifecycle."""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import publish_workspace, reserve_workspace
from er_commons.semantic_materialization.construction import SemanticBuild, build_semantic_records
from er_commons.semantic_materialization.publication import (
    preserve_failed_attempt,
    verify_completed_semantic_candidate,
)
from er_commons.semantic_materialization.runtime import (
    RuntimeContext,
    inherited_warnings,
)
from er_commons.semantic_materialization.sealing import (
    SemanticSealingInputs,
    validate_serialize_and_seal,
)
from er_commons.semantic_materialization.support import build_candidate_support


def reuse_completed_candidate(
    *,
    context: RuntimeContext,
    candidate_id: str,
) -> Path:
    """Checksum-verify and reuse one completed semantic candidate."""
    return verify_completed_semantic_candidate(context.task_root / candidate_id, candidate_id)


def build_validate_and_publish(
    *,
    context: RuntimeContext,
    identity: dict[str, Any],
    candidate_id: str,
) -> Path:
    """Build and validate one fresh candidate, then publish it atomically."""
    workspace = None
    try:
        workspace = reserve_workspace(context.task_root, candidate_id, uuid.uuid4().hex)
        _write_candidate_workspace(
            context=context,
            identity=identity,
            candidate_id=candidate_id,
            root=workspace.staging_root,
        )
        completion = publish_workspace(workspace)
        verify_completed_semantic_candidate(context.task_root / candidate_id, candidate_id)
        return completion
    except Exception as error:
        if workspace is not None and workspace.staging_root.exists():
            try:
                preserve_failed_attempt(
                    context.task_root,
                    workspace.staging_root,
                    candidate_id=candidate_id,
                    error=error,
                )
            except Exception as retention_error:
                error.add_note(f"failed to retain semantic attempt: {retention_error}")
        raise


def _write_candidate_workspace(
    *,
    context: RuntimeContext,
    identity: dict[str, Any],
    candidate_id: str,
    root: Path,
) -> SemanticBuild:
    """Construct support records and seal one fresh workspace completion-last."""
    build = build_semantic_records(replace(context.construction_inputs, candidate_id=candidate_id))
    support = build_candidate_support(
        baseline_root=context.inputs.baseline_candidate_root,
        build=build,
        baseline_candidate_id=context.config.baseline_candidate_id,
        candidate_id=candidate_id,
        control=context.inputs.control_provenance,
        expectations=context.construction_inputs.expectations,
    )
    validate_serialize_and_seal(
        root=root,
        build=build,
        support=support,
        inputs=SemanticSealingInputs(
            project_root=context.project_root,
            identity=identity,
            baseline_root=context.inputs.baseline_candidate_root,
            baseline_candidate_id=context.config.baseline_candidate_id,
            baseline_producer_run_id=context.config.baseline_producer_run_id,
            hierarchy_producer_run_id=context.config.hierarchy_producer_run_id,
            control=context.inputs.control_provenance,
            inherited_warnings=inherited_warnings(context.inputs),
            expectations=context.construction_inputs.expectations,
            source_semantic_disposition=(
                "strict_quality_gate"
                if context.config.control_profile == "strict_quality_gate"
                else "accepted_with_known_limitations"
            ),
            semantic_schema_path=context.semantic_schema_path,
        ),
    )
    return build
