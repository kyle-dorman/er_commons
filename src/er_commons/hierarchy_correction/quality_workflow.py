"""Compose all seven external quality reports against one sealed staging tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.candidate_publication import verify_completed_candidate
from er_commons.hierarchy_correction.configuration import APPENDIX_P_SOURCE_ID
from er_commons.hierarchy_correction.evaluation import (
    evaluate_frozen_outline_numbering_gates,
    load_development_cases,
)
from er_commons.hierarchy_correction.preservation import ManagedArtifactSnapshot
from er_commons.hierarchy_correction.quality_evaluation import (
    EvaluationSurface,
    build_combined_review_inventory,
    build_control_projection,
    build_preservation_report,
    build_repeat_resource_report,
    combine_development_report,
    evaluate_control_cases,
    evaluate_document_development_cases,
    load_fixed_control_artifacts,
    write_named_quality_reports,
)
from er_commons.hierarchy_correction.quality_gate import (
    REPORT_NAMES,
    VerifiedQualityGatePass,
    assemble_quality_gate_pass,
    fixed_control_ranges_root,
    load_quality_gate_config,
)
from er_commons.hierarchy_correction.quality_reports import QualityReportSet
from er_commons.hierarchy_correction.review import (
    HeldOutAnnotationSeal,
    build_held_out_evaluation,
)

JsonRecord = dict[str, Any]


def produce_quality_gate_pass(
    *,
    data_root: Path,
    project_root: Path,
    correction_schema_path: Path,
    quality_config_path: Path,
    candidate_root: Path,
    candidate_id: str,
    source_id: str = APPENDIX_P_SOURCE_ID,
    annotation_seal: HeldOutAnnotationSeal,
    repeat_comparison_path: Path,
    preservation_before: tuple[ManagedArtifactSnapshot, ...],
    preservation_after: tuple[ManagedArtifactSnapshot, ...],
) -> VerifiedQualityGatePass:
    """Produce, bind, and verify all real prepublication quality reports."""
    verify_completed_candidate(candidate_root, candidate_id, correction_schema_path)
    candidate = _load_candidate(candidate_root)
    quality_config, _config_sha256 = load_quality_gate_config(quality_config_path)
    historical_profile = (
        getattr(quality_config, "quality_profile", "appendix_p_task03e2") == "appendix_p_task03e2"
    )
    controls = build_control_projection(())
    development_path = project_root / quality_config.development_cases.path
    development_cases = (
        load_development_cases(development_path)
        if historical_profile
        else load_development_cases(development_path, expected_count=None)
    )
    document_surface = EvaluationSurface(
        name=source_id,
        source_id=source_id,
        features=tuple(candidate["features"]),
        regimes=tuple(candidate["regimes"]),
        decisions=tuple(candidate["decisions"]),
    )
    if historical_profile:
        assert quality_config.task03e_evaluation_config is not None
        specification, control_artifacts = load_fixed_control_artifacts(
            evaluation_config_path=(project_root / quality_config.task03e_evaluation_config.path),
            control_ranges_root=fixed_control_ranges_root(quality_config, data_root),
        )
        controls = build_control_projection(control_artifacts)
        review_pages = frozenset(
            item.physical_page for item in specification.appendix_p_review_pages
        )
        development_report = combine_development_report(
            development_cases=development_cases,
            appendix_decisions=document_surface.decisions,
            control_projection=controls,
        )
        controls_report = evaluate_control_cases(
            development_cases=development_cases,
            projection=controls,
        )
    else:
        review_pages = frozenset(quality_config.document_review_pages)
        development_report = evaluate_document_development_cases(
            source_id=source_id,
            development_cases=development_cases,
            decisions=document_surface.decisions,
        )
        controls_report = {
            "status": "pass",
            "profile": "document_local_only",
            "case_count": 0,
            "detail": "cross-document historical controls are not part of this profile",
        }
    annotations = _load_json_object(annotation_seal.annotations_path)
    report_set = QualityReportSet(
        development=development_report,
        outline_numbering_29_21=evaluate_frozen_outline_numbering_gates(
            review_pages=review_pages,
            features=document_surface.features,
            decisions=document_surface.decisions,
            regimes=document_surface.regimes,
            expected_outline_count=quality_config.expected_exact_outline_anchor_count,
            expected_outline_r03_count=getattr(quality_config, "expected_outline_r03_count", 28),
            expected_outline_toc_override_count=(
                getattr(quality_config, "expected_outline_toc_override_count", 1)
            ),
            expected_numbered_heading_count=(
                getattr(quality_config, "expected_numbered_heading_count", 23)
            ),
            expected_numbering_relation_count=quality_config.expected_numbering_relation_count,
        ),
        controls=controls_report,
        held_out=build_held_out_evaluation(annotations, candidate),
        review_inventory=build_combined_review_inventory((document_surface, *controls.surfaces)),
        preservation=build_preservation_report(
            before=preservation_before,
            after=preservation_after,
        ),
        repeat_resource=build_repeat_resource_report(
            candidate_id=candidate_id,
            repeat_comparison=_load_json_object(repeat_comparison_path),
            metrics=candidate["metrics"],
        ),
    )
    reports = report_set.as_mapping()
    if set(reports) != set(REPORT_NAMES):
        raise ValueError("quality workflow report-name set differs")
    report_root = (
        data_root / quality_config.review_artifact_relative_root / candidate_id / "reports"
    )
    write_named_quality_reports(report_root, reports)
    report_set.require_acceptance()
    return assemble_quality_gate_pass(
        config_path=quality_config_path,
        candidate_root=candidate_root,
        candidate_id=candidate_id,
        project_root=project_root,
        data_root=data_root,
        report_relative_paths={name: Path("reports") / f"{name}.json" for name in REPORT_NAMES},
    )


def _load_candidate(root: Path) -> JsonRecord:
    """Load the schema-verified candidate fields consumed by quality gates."""
    return {
        "identity": _load_json_object(root / "records/identity.json"),
        "features": _load_jsonl(root / "artifacts/item_features.jsonl"),
        "toc_entries": _load_jsonl(root / "artifacts/visible_toc_entries.jsonl"),
        "reconciliations": _load_jsonl(root / "artifacts/toc_reconciliation.jsonl"),
        "regimes": _load_jsonl(root / "artifacts/regimes.jsonl"),
        "decisions": _load_jsonl(root / "artifacts/decisions.jsonl"),
        "hierarchy": _load_json_object(root / "artifacts/hierarchy.json"),
        "ambiguities": _load_jsonl(root / "artifacts/ambiguities.jsonl"),
        "warnings": _load_jsonl(root / "artifacts/warnings.jsonl"),
        "metrics": _load_json_object(root / "records/metrics.json"),
    }


def _load_json_object(path: Path) -> JsonRecord:
    """Load one required JSON object."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"quality workflow expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[JsonRecord]:
    """Load one required JSONL collection in persisted order."""
    records = [json.loads(line) for line in path.read_text().splitlines()]
    if any(not isinstance(record, dict) for record in records):
        raise ValueError(f"quality workflow expected JSON objects: {path}")
    return records
