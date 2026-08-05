"""Resolve and verify one hierarchy-correction run before mutable work."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.bounded_acceptance import (
    VerifiedBoundedAcceptancePolicy,
    verify_bounded_acceptance_policy,
)
from er_commons.hierarchy_correction.candidate_identity import build_candidate_identity
from er_commons.hierarchy_correction.code_inventory import owned_code_paths
from er_commons.hierarchy_correction.configuration import (
    HierarchyCorrectionConfig,
    load_hierarchy_correction_config,
)
from er_commons.hierarchy_correction.inputs import (
    HierarchyCorrectionInputs,
    load_hierarchy_correction_inputs,
)

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class CorrectionRunContext:
    """Verified immutable inputs, identity, and publication-policy paths."""

    data_root: Path
    project_root: Path
    config_path: Path
    config: HierarchyCorrectionConfig
    inputs: HierarchyCorrectionInputs
    schema_path: Path
    identity: JsonRecord
    candidate_id: str
    task_root: Path
    final_root: Path
    bounded_acceptance_policy: VerifiedBoundedAcceptancePolicy | None
    bounded_acceptance_path: Path | None


def prepare_run(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
) -> CorrectionRunContext:
    """Verify candidate-producing inputs and derive all stable run paths."""
    project_root = Path(__file__).resolve().parents[3]
    config, effective_config_sha256 = load_hierarchy_correction_config(config_path)
    config_sha256 = (
        load_hierarchy_correction_config(config_identity_path)[1]
        if config_identity_path is not None
        else effective_config_sha256
    )
    inputs = load_hierarchy_correction_inputs(data_root, config)
    schema_path = project_root / config.schema_relative_path
    identity = build_candidate_identity(
        config=config,
        config_sha256=config_sha256,
        inputs=inputs,
        policy_path=project_root / config.policy_relative_path,
        schema_path=schema_path,
        project_root=project_root,
        owned_code_paths=owned_code_paths(project_root),
    )
    candidate_id = identity["candidate_id"]
    task_root = data_root / config.artifact_relative_root
    bounded_policy = None
    bounded_path = None
    if config.publication_authorization == "bounded_acceptance":
        assert config.bounded_acceptance_config_relative_path is not None
        assert config.bounded_acceptance_artifact_relative_root is not None
        bounded_policy = verify_bounded_acceptance_policy(
            project_root / config.bounded_acceptance_config_relative_path,
            data_root,
        )
        bounded_path = (
            data_root
            / config.bounded_acceptance_artifact_relative_root
            / candidate_id
            / "bounded_acceptance.json"
        )
    return CorrectionRunContext(
        data_root=data_root,
        project_root=project_root,
        config_path=config_path,
        config=config,
        inputs=inputs,
        schema_path=schema_path,
        identity=identity,
        candidate_id=candidate_id,
        task_root=task_root,
        final_root=task_root / candidate_id,
        bounded_acceptance_policy=bounded_policy,
        bounded_acceptance_path=bounded_path,
    )
