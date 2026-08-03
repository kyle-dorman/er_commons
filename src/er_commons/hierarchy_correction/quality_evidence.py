"""Checksum and identity verification for frozen quality-gate evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from er_commons.hierarchy_correction.quality_config import QualityGateConfig


def verify_config_evidence(
    config: QualityGateConfig,
    project_root: Path,
    data_root: Path,
) -> None:
    """Verify tracked inputs and accepted Task 03E and 03D.1 terminal records."""
    tracked = [
        config.development_cases,
        config.fixture_manifest,
        config.held_out_manifest,
        config.review_schema,
    ]
    if config.task03e_evaluation_config is not None:
        tracked.append(config.task03e_evaluation_config)
    for evidence in tracked:
        path = project_root / evidence.path
        if hashlib.sha256(path.read_bytes()).hexdigest() != evidence.sha256:
            raise ValueError(f"quality-gate tracked checksum differs: {evidence.path}")

    fixture_manifest = json.loads((project_root / config.fixture_manifest.path).read_bytes())
    development_evidence = fixture_manifest.get("development_evidence", {})
    if (
        development_evidence.get("reviewed_exact_outline_anchor_count")
        != config.expected_exact_outline_anchor_count
        or development_evidence.get("reviewed_numbering_relation_count")
        != config.expected_numbering_relation_count
    ):
        raise ValueError("quality-gate fixture-manifest 29/21 counts differ")
    if config.quality_profile == "appendix_p_task03e2":
        _verify_control_scope(config, project_root)
        _verify_task03e_evidence(config, data_root, development_evidence)
    _verify_task03d1_evidence(config, data_root)


def _verify_control_scope(config: QualityGateConfig, project_root: Path) -> None:
    assert config.task03e_evaluation_config is not None
    evaluation = json.loads((project_root / config.task03e_evaluation_config.path).read_bytes())
    actual_controls = tuple(
        (item["first_page"], item["last_page"], item["purpose"])
        for item in evaluation["main_report_controls"]
    )
    configured_controls = tuple(
        (item.first_page, item.last_page, item.purpose)
        for item in config.main_report_control_ranges
    )
    expected_names = [item.range_name for item in config.main_report_control_ranges]
    if (
        actual_controls != configured_controls
        or evaluation["control_harness"]["expected_range_names"] != expected_names
    ):
        raise ValueError("quality-gate evaluation control ranges differ")


def _verify_task03e_evidence(
    config: QualityGateConfig,
    data_root: Path,
    development_evidence: dict[str, object],
) -> None:
    reference = config.task03e_review_reference
    assert reference is not None
    root = data_root / reference.artifact_relative_root / reference.comparison_id
    reports = (
        ("producer_comparison_report.json", reference.producer_comparison_report_sha256),
        ("bounded_review_report.json", reference.bounded_review_report_sha256),
        ("controls/control_report.json", reference.control_report_sha256),
    )
    for relative, expected_sha256 in reports:
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected_sha256:
            raise ValueError(f"Task 03E review checksum differs: {relative}")

    control_root = root / reference.control_ranges_relative_root
    for control in config.main_report_control_ranges:
        for filename, expected_sha256 in (
            ("document.json", control.document_sha256),
            ("conversion_pages.json", control.conversion_pages_sha256),
        ):
            if (
                hashlib.sha256(
                    (control_root / control.range_name / filename).read_bytes()
                ).hexdigest()
                != expected_sha256
            ):
                raise ValueError(
                    f"Task 03E control checksum differs: {control.range_name}/{filename}"
                )
    if (
        development_evidence.get("task_03e_comparison_report_sha256")
        != reference.producer_comparison_report_sha256
        or development_evidence.get("task_03e_bounded_review_sha256")
        != reference.bounded_review_report_sha256
    ):
        raise ValueError("quality-gate fixture-manifest Task 03E seals differ")


def _verify_task03d1_evidence(config: QualityGateConfig, data_root: Path) -> None:
    reference = config.task03d1_reference
    root = data_root / reference.artifact_relative_root / reference.extraction_id
    for relative, expected_sha256 in (
        ("records/completion_record.json", reference.completion_sha256),
        ("records/artifact_inventory.json", reference.artifact_inventory_sha256),
    ):
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected_sha256:
            raise ValueError(f"Task 03D.1 terminal checksum differs: {relative}")
    completion = json.loads((root / "records/completion_record.json").read_bytes())
    if (
        completion.get("candidate_id") != reference.extraction_id
        or completion.get("artifact_inventory_sha256") != reference.artifact_inventory_sha256
    ):
        raise ValueError("Task 03D.1 completion seal differs")
