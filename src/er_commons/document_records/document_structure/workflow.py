"""Public orchestration for mapping and publishing document structure."""

from __future__ import annotations

from pathlib import Path

from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.document_structure.identity import (
    build_document_structure_identity,
)
from er_commons.document_records.document_structure.lifecycle import (
    build_validate_and_publish,
    reuse_completed_candidate,
)
from er_commons.document_records.document_structure.runtime import (
    RuntimeContext,
    load_runtime_context,
    owned_runtime_paths,
)


def map_document_structure(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
) -> Path:
    """Verify inputs, identify/reuse, or build, validate, and publish once."""
    context = load_runtime_context(
        data_root=data_root,
        config_path=config_path,
        config_identity_path=config_identity_path,
    )
    identity = build_document_structure_identity(
        project_root=context.project_root,
        config_path=context.config_identity_path,
        config=context.config,
        inputs=context.inputs,
        owned_paths=owned_runtime_paths(context.config_identity_path),
    )
    candidate_id = identity["extraction_id"]
    _require_new_candidate_id(context, candidate_id)
    candidate_root = context.task_root / candidate_id
    if candidate_root.exists():
        return reuse_completed_candidate(context=context, candidate_id=candidate_id)
    return build_validate_and_publish(
        context=context,
        identity=identity,
        candidate_id=candidate_id,
    )


def _require_new_candidate_id(context: RuntimeContext, candidate_id: str) -> None:
    if candidate_id == context.config.baseline_candidate_id:
        raise DocumentStructureInvariantError(
            stage="candidate identity",
            invariant="semantic candidate differs from the Task 03D.1 baseline",
            expected="new extraction ID",
            observed=candidate_id,
            subject=f"{context.config.source.source_id} candidate",
        )
