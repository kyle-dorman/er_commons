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
from er_commons.hierarchy_correction.preservation import (
    ManagedArtifactSnapshot,
    snapshot_verified_producer,
    snapshot_verified_task03d1_reference,
)
from er_commons.hierarchy_correction.quality_gate import (
    QualityGateConfig,
    load_quality_gate_config,
)
from er_commons.hierarchy_correction.review import (
    HeldOutAnnotationSeal,
    verify_sealed_held_out_annotations,
)

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class CorrectionRunContext:
    """Verified immutable paths and records shared by reuse and fresh builds."""

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
    quality_gate_config_path: Path
    quality_gate_config: QualityGateConfig
    quality_gate_pass_path: Path
    bounded_acceptance_policy: VerifiedBoundedAcceptancePolicy | None
    bounded_acceptance_path: Path
    producer_before: ManagedArtifactSnapshot


@dataclass(frozen=True)
class NewCandidateContext:
    """Source-only review and preservation evidence required before building."""

    run: CorrectionRunContext
    annotation_seal: HeldOutAnnotationSeal | None
    task03d1_root: Path
    preservation_before: tuple[ManagedArtifactSnapshot, ManagedArtifactSnapshot]


def prepare_run(data_root: Path, config_path: Path) -> CorrectionRunContext:
    """Verify candidate-producing inputs and derive all stable run paths."""
    project_root = Path(__file__).resolve().parents[3]
    config, config_sha256 = load_hierarchy_correction_config(config_path)
    inputs = load_hierarchy_correction_inputs(data_root, config)
    producer_before = snapshot_verified_producer(inputs.producer_run_root, config.producer_run_id)
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
    quality_gate_config_path = project_root / config.quality_gate_config_relative_path
    quality_gate_config, _digest = load_quality_gate_config(quality_gate_config_path)
    if (
        config.publication_authorization == "strict_quality_gate"
        and config.source.source_id != "deir_appendix_p"
        and quality_gate_config.quality_profile != "generic_document"
    ):
        raise ValueError("non-Appendix strict correction requires generic quality evidence")
    review_root = data_root / config.review_artifact_relative_root / candidate_id
    bounded_policy = None
    if config.publication_authorization == "bounded_acceptance":
        assert config.bounded_acceptance_config_relative_path is not None
        bounded_policy = verify_bounded_acceptance_policy(
            project_root / config.bounded_acceptance_config_relative_path,
            data_root,
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
        quality_gate_config_path=quality_gate_config_path,
        quality_gate_config=quality_gate_config,
        quality_gate_pass_path=review_root / "quality_gate_pass.json",
        bounded_acceptance_policy=bounded_policy,
        bounded_acceptance_path=review_root / "bounded_acceptance.json",
        producer_before=producer_before,
    )


def prepare_new_candidate(run: CorrectionRunContext) -> NewCandidateContext:
    """Verify review and canonical-reference evidence before corrected output."""
    # Task 03E.2d binds the frozen historical annotation and rejection through
    # the bounded policy. A strict pass, if one already exists, retains the
    # original candidate-local annotation verification path.
    annotation_seal = None
    if run.config.publication_authorization == "strict_quality_gate":
        annotation_seal = verify_sealed_held_out_annotations(
            data_root=run.data_root,
            config_path=run.config_path,
            candidate_id=run.candidate_id,
        )
    reference = run.quality_gate_config.task03d1_reference
    task03d1_root = run.data_root / reference.artifact_relative_root / reference.extraction_id
    task03d1_before = snapshot_verified_task03d1_reference(
        task03d1_root,
        reference.extraction_id,
    )
    return NewCandidateContext(
        run=run,
        annotation_seal=annotation_seal,
        task03d1_root=task03d1_root,
        preservation_before=(run.producer_before, task03d1_before),
    )
