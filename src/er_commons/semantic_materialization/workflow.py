"""Public orchestration shell for the human-owned Task 03E.4 materializer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from er_commons.semantic_materialization.construction import build_semantic_records
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.identity import build_semantic_candidate_identity
from er_commons.semantic_materialization.lifecycle import (
    build_validate_and_publish,
    reuse_completed_candidate,
)
from er_commons.semantic_materialization.runtime import (
    PLACEHOLDER_ID,
    RuntimeContext,
    load_runtime_context,
    owned_runtime_paths,
)
from er_commons.semantic_materialization.support import build_candidate_support


def run_semantic_materialization(
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
    identity = _candidate_identity(context)
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


def _candidate_identity(context: RuntimeContext) -> dict[str, Any]:
    """Derive identity from the candidate-ID-independent placeholder projection."""
    build = build_semantic_records(context.construction_inputs)
    support = build_candidate_support(
        baseline_root=context.inputs.baseline_candidate_root,
        build=build,
        baseline_candidate_id=context.config.baseline_candidate_id,
        candidate_id=PLACEHOLDER_ID,
        control=context.inputs.control_provenance,
        expectations=context.construction_inputs.expectations,
    )
    return build_semantic_candidate_identity(
        project_root=context.project_root,
        config_path=context.config_identity_path,
        config=context.config,
        inputs=context.inputs,
        bridge_entries=build.bridge_entries,
        support_preimages=support.payloads,
        owned_paths=owned_runtime_paths(context.config_identity_path),
    )


def _require_new_candidate_id(context: RuntimeContext, candidate_id: str) -> None:
    if candidate_id == context.config.baseline_candidate_id:
        raise SemanticMaterializationInvariantError(
            stage="candidate identity",
            invariant="semantic candidate differs from the Task 03D.1 baseline",
            expected="new extraction ID",
            observed=candidate_id,
            subject="Appendix P candidate",
        )
