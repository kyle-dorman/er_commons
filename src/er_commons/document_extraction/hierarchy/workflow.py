"""Application shell for the Task 03E repeated producer gate."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_extraction.complete_document import prepare_producer
from er_commons.document_extraction.hierarchy.controls import run_hierarchy_controls
from er_commons.document_extraction.hierarchy.document import JsonObject
from er_commons.document_extraction.hierarchy.process import (
    completed_run_root,
    run_producer_subprocess,
)
from er_commons.document_extraction.hierarchy.report import HierarchyEvaluationReport
from er_commons.document_extraction.hierarchy.run_comparison import compare_producer_runs
from er_commons.document_extraction.hierarchy.specification import (
    HierarchyEvaluationSpec,
    load_hierarchy_evaluation_spec,
)
from er_commons.document_extraction.producer_artifacts import verify_completed_run
from er_commons.document_extraction.producer_config import load_producer_config
from er_commons.document_extraction.producer_identity import canonical_json_sha256
from er_commons.document_extraction.producer_publication import task_artifact_root
from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.source_freeze import write_json_atomic


@dataclass(frozen=True)
class EvaluationContext:
    """Verified configuration, identity, and artifact paths for one evaluation."""

    spec: HierarchyEvaluationSpec
    evaluation_path: Path
    evaluation_sha256: str
    candidate_config_path: Path
    candidate_config_sha256: str
    candidate_run_id: str
    comparison_id: str
    baseline_root: Path
    final_root: Path
    comparison_root: Path
    scratch_a_relative: Path
    scratch_b_relative: Path

    @property
    def review_pages(self) -> set[int]:
        """Return the fixed Appendix P page set for human-review rows."""
        return {item.physical_page for item in self.spec.appendix_p_review_pages}


def _comparison_id(
    *,
    evaluation_sha256: str,
    candidate_config_sha256: str,
    baseline_run_id: str,
    candidate_run_id: str,
) -> str:
    """Build the frozen Task 03E comparison identity."""
    payload = {
        "schema_version": "task03e-hierarchy-comparison-v2",
        "evaluation_sha256": evaluation_sha256,
        "candidate_config_sha256": candidate_config_sha256,
        "baseline_run_id": baseline_run_id,
        "candidate_run_id": candidate_run_id,
    }
    return f"cmpv2-{canonical_json_sha256(payload)}"


def _prepare_evaluation(
    data_root: Path,
    evaluation_path: Path,
) -> EvaluationContext:
    """Validate configuration and resolve all immutable run locations."""
    spec, evaluation_sha256 = load_hierarchy_evaluation_spec(evaluation_path)
    candidate_config_path = spec.candidate_config_path
    config, candidate_config_sha256 = load_producer_config(candidate_config_path)
    if config.heading_hierarchy_options != spec.heading_hierarchy_options:
        raise ValueError("candidate and evaluation hierarchy options differ")

    baseline_root = (
        data_root / config.artifact_relative_root / spec.baseline_producer_run_id
    ).resolve()
    verify_completed_run(baseline_root, spec.baseline_producer_run_id)

    prepared = prepare_producer(
        data_root,
        config=config,
        config_sha256=candidate_config_sha256,
        services=ProducerServices(),
    )
    candidate_run_id = prepared.identity.run_id
    comparison_id = _comparison_id(
        evaluation_sha256=evaluation_sha256,
        candidate_config_sha256=candidate_config_sha256,
        baseline_run_id=spec.baseline_producer_run_id,
        candidate_run_id=candidate_run_id,
    )
    review_task_root = task_artifact_root(
        data_root,
        spec.control_harness.artifact_relative_root,
    )
    comparison_root = review_task_root / comparison_id
    comparison_root.mkdir(parents=True, exist_ok=True)
    final_task_root = task_artifact_root(data_root, config.artifact_relative_root)
    return EvaluationContext(
        spec=spec,
        evaluation_path=evaluation_path,
        evaluation_sha256=evaluation_sha256,
        candidate_config_path=candidate_config_path,
        candidate_config_sha256=candidate_config_sha256,
        candidate_run_id=candidate_run_id,
        comparison_id=comparison_id,
        baseline_root=baseline_root,
        final_root=final_task_root / candidate_run_id,
        comparison_root=comparison_root,
        scratch_a_relative=(
            spec.control_harness.artifact_relative_root / comparison_id / "scratch_build_a"
        ),
        scratch_b_relative=(
            spec.control_harness.artifact_relative_root / comparison_id / "scratch_build_b"
        ),
    )


def _primary_candidate(
    data_root: Path,
    context: EvaluationContext,
    timings: dict[str, float],
) -> tuple[Path, str]:
    """Verify the published candidate or build the first independent scratch run."""
    if context.final_root.exists():
        verify_completed_run(context.final_root, context.candidate_run_id)
        return context.final_root, "already_published"

    started = time.perf_counter()
    completion = run_producer_subprocess(
        data_root,
        context.candidate_config_path,
        artifact_root_override=context.scratch_a_relative,
    )
    timings["fresh_build_a"] = time.perf_counter() - started
    primary_root = completed_run_root(completion)
    if primary_root.name != context.candidate_run_id:
        raise ValueError(
            "fresh build A derived an unexpected producer run ID: "
            f"expected={context.candidate_run_id} actual={primary_root.name}"
        )
    return primary_root, "pending_machine_gate"


def _repeat_candidate(
    data_root: Path,
    context: EvaluationContext,
    timings: dict[str, float],
) -> Path:
    """Build or checksum-reuse the second isolated scratch candidate."""
    started = time.perf_counter()
    completion = run_producer_subprocess(
        data_root,
        context.candidate_config_path,
        artifact_root_override=context.scratch_b_relative,
    )
    timings["fresh_build_b_or_reuse"] = time.perf_counter() - started
    repeat_root = completed_run_root(completion)
    if repeat_root.name != context.candidate_run_id:
        raise ValueError(
            "fresh build B derived an unexpected producer run ID: "
            f"expected={context.candidate_run_id} actual={repeat_root.name}"
        )
    return repeat_root


def _machine_evidence(
    data_root: Path,
    context: EvaluationContext,
    primary_root: Path,
    repeat_root: Path,
) -> tuple[JsonObject, JsonObject, JsonObject]:
    """Build the preservation, repeatability, and control evidence independently."""
    baseline_comparison = compare_producer_runs(
        context.baseline_root,
        primary_root,
        review_pages=context.review_pages,
    )
    repeat_comparison = compare_producer_runs(
        primary_root,
        repeat_root,
        review_pages=context.review_pages,
    )
    controls = run_hierarchy_controls(
        data_root=data_root,
        spec=context.spec,
        comparison_root=context.comparison_root,
    )
    return baseline_comparison, repeat_comparison, controls


def run_hierarchy_producer_evaluation(
    data_root: Path,
    evaluation_path: Path,
) -> Path:
    """Run independent builds, compare all gates, and publish only on success."""
    context = _prepare_evaluation(data_root, evaluation_path)
    timings: dict[str, float] = {}
    primary_root, publication_status = _primary_candidate(data_root, context, timings)
    repeat_root = _repeat_candidate(data_root, context, timings)
    baseline, repeat, controls = _machine_evidence(
        data_root,
        context,
        primary_root,
        repeat_root,
    )
    report = HierarchyEvaluationReport(
        comparison_id=context.comparison_id,
        evaluation_path=evaluation_path,
        evaluation_sha256=context.evaluation_sha256,
        candidate_config_path=context.candidate_config_path,
        candidate_config_sha256=context.candidate_config_sha256,
        baseline_run_id=context.spec.baseline_producer_run_id,
        candidate_run_id=context.candidate_run_id,
        publication_status=publication_status,
        baseline_comparison=baseline,
        repeat_comparison=repeat,
        control_report=controls,
        timings_seconds=timings,
    )
    report_path = context.comparison_root / "producer_comparison_report.json"
    write_json_atomic(report_path, report.to_json())
    if report.to_json()["machine_status"] != "pass":
        return report_path

    if not context.final_root.exists():
        primary_root.rename(context.final_root)
        primary_root = context.final_root
        report.publication_status = "published_after_machine_gate"
    verify_completed_run(primary_root, context.candidate_run_id)

    started = time.perf_counter()
    reuse_completion = run_producer_subprocess(
        data_root,
        context.candidate_config_path,
    )
    timings["checksum_verified_reuse"] = time.perf_counter() - started
    if completed_run_root(reuse_completion) != context.final_root:
        raise ValueError(
            "normal producer command did not reuse the published candidate: "
            f"expected={context.final_root} actual={completed_run_root(reuse_completion)}"
        )
    report.published_completion = reuse_completion
    write_json_atomic(report_path, report.to_json())
    return report_path
