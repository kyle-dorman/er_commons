"""Reproducible build, comparison, reuse, and atomic-publication lifecycle."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import publish_workspace, reserve_workspace
from er_commons.semantic_materialization.construction import SemanticBuild, build_semantic_records
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.publication import (
    preserve_failed_attempt,
    verify_completed_semantic_candidate,
)
from er_commons.semantic_materialization.reference import (
    compare_reference_candidate,
    write_comparison_report,
)
from er_commons.semantic_materialization.review import build_semantic_review_cache
from er_commons.semantic_materialization.runtime import (
    CandidateLocations,
    RuntimeContext,
    inherited_warnings,
)
from er_commons.semantic_materialization.sealing import (
    SemanticSealingInputs,
    candidate_file_bytes,
    validate_serialize_and_seal,
)
from er_commons.semantic_materialization.support import build_candidate_support


def reuse_completed_candidate(
    *,
    context: RuntimeContext,
    locations: CandidateLocations,
    candidate_id: str,
) -> tuple[Path, Path]:
    """Checksum-verify an existing candidate, review cache, and comparison report."""
    completion = verify_completed_semantic_candidate(locations.candidate_root, candidate_id)
    if getattr(context.config, "reference_profile", "frozen_equivalence") == ("independent_build"):
        return completion, completion
    review = build_semantic_review_cache(
        review_root=locations.candidate_review_root,
        source_pdf=context.source_pdf,
        candidate_root=locations.candidate_root,
        review_pages=context.config.review_pages,
    )
    _compare_and_record(
        context=context,
        locations=locations,
        candidate_root=locations.candidate_root,
        candidate_review_root=locations.candidate_review_root,
        candidate_id=candidate_id,
    )
    return completion, review


def build_compare_and_publish(
    *,
    context: RuntimeContext,
    locations: CandidateLocations,
    identity: dict[str, Any],
    candidate_id: str,
) -> tuple[Path, Path]:
    """Build twice, compare with the frozen MVP, then atomically publish one copy."""
    reserved_workspaces = []
    try:
        first = reserve_workspace(context.task_root, candidate_id, uuid.uuid4().hex)
        reserved_workspaces.append(first)
        second = reserve_workspace(context.task_root, candidate_id, uuid.uuid4().hex)
        reserved_workspaces.append(second)
        for workspace in (first, second):
            _write_candidate_workspace(
                context=context,
                identity=identity,
                candidate_id=candidate_id,
                root=workspace.staging_root,
            )
        _require_byte_identical(first.staging_root, second.staging_root, candidate_id)
        if getattr(context.config, "reference_profile", "frozen_equivalence") == (
            "frozen_equivalence"
        ):
            review = build_semantic_review_cache(
                review_root=locations.candidate_review_root,
                source_pdf=context.source_pdf,
                candidate_root=first.staging_root,
                review_pages=context.config.review_pages,
            )
            _compare_and_record(
                context=context,
                locations=locations,
                candidate_root=first.staging_root,
                candidate_review_root=locations.candidate_review_root,
                candidate_id=candidate_id,
            )
        else:
            review = first.staging_root / "records/completion_record.json"
        shutil.rmtree(second.staging_root)
        completion = publish_workspace(first)
        verify_completed_semantic_candidate(locations.candidate_root, candidate_id)
        if getattr(context.config, "reference_profile", "frozen_equivalence") == (
            "independent_build"
        ):
            review = completion
        return completion, review
    except Exception:
        for workspace in reserved_workspaces:
            if workspace.staging_root.exists():
                preserve_failed_attempt(context.task_root, workspace.staging_root)
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
        expectations=context.config.expectations,
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
            expectations=context.config.expectations,
            source_semantic_disposition=(
                "strict_quality_gate"
                if context.config.control_profile == "strict_quality_gate"
                else "accepted_with_known_limitations"
            ),
        ),
    )
    return build


def _require_byte_identical(first: Path, second: Path, candidate_id: str) -> None:
    if candidate_file_bytes(first) != candidate_file_bytes(second):
        raise SemanticMaterializationInvariantError(
            stage="reproducibility",
            invariant="fresh candidate workspaces are byte-identical",
            expected="identical file map",
            observed="different file bytes",
            subject=candidate_id,
        )


def _compare_and_record(
    *,
    context: RuntimeContext,
    locations: CandidateLocations,
    candidate_root: Path,
    candidate_review_root: Path,
    candidate_id: str,
) -> Path:
    """Write no-clobber comparison evidence and stop on any semantic mismatch."""
    if context.config.mvp_reference_candidate_id is None:
        raise ValueError("frozen equivalence lacks a reference candidate")
    comparison = compare_reference_candidate(
        reference_root=locations.reference_root,
        candidate_root=candidate_root,
        reference_review_root=locations.reference_review_root,
        candidate_review_root=candidate_review_root,
        reference_candidate_id=context.config.mvp_reference_candidate_id,
        candidate_id=candidate_id,
    )
    report = write_comparison_report(locations.comparison_root, comparison)
    if comparison.status != "equivalent":
        raise SemanticMaterializationInvariantError(
            stage="rewrite comparison",
            invariant="rewritten candidate matches the frozen MVP under declared normalization",
            expected="equivalent",
            observed=comparison.status,
            subject=report.as_posix(),
        )
    return report
