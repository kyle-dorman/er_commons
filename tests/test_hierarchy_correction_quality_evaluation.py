"""Focused tests for external Task 03E.2 quality-report producers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.hierarchy_correction.evaluation import load_development_cases
from er_commons.hierarchy_correction.preservation import (
    ManagedArtifactSnapshot,
    ManagedFile,
)
from er_commons.hierarchy_correction.quality_evaluation import (
    ControlProjection,
    EvaluationSurface,
    build_combined_review_inventory,
    build_preservation_report,
    build_repeat_resource_report,
    combine_development_report,
    evaluate_control_cases,
    load_fixed_control_artifacts,
    stable_report_bytes,
    write_named_quality_reports,
)

ROOT = Path(__file__).parents[1]
EVALUATION_CONFIG = (
    ROOT / "configs/brisbane_baylands_2025_deir_task03e_hierarchy_evaluation_v1.json"
)
DEVELOPMENT_CASES = (
    ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1/development_cases.json"
)


def _decision(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "stable_item_key": case["stable_item_key"],
        "raw_role": case["raw_role"],
        "raw_level": case["raw_level"],
        "corrected_role": case["expected_role"],
        "corrected_level": case["expected_level"],
        "selected_rule_id": case["expected_rule_id"],
        "outcome": case["expected_outcome"],
        "evidence": {"source_item_keys": [case["stable_item_key"]]},
    }


def _surface(
    name: str,
    source_id: str,
    decisions: tuple[dict[str, Any], ...],
) -> EvaluationSurface:
    features = tuple(
        {
            "stable_item_key": item["stable_item_key"],
            "reading_order_index": index,
            "physical_page": index + 1,
            "text": f"item {index}",
        }
        for index, item in enumerate(decisions)
    )
    return EvaluationSurface(name, source_id, features, (), decisions)


def test_fixed_control_loader_uses_only_configured_range_names(tmp_path: Path) -> None:
    expected = (
        "deir_main_pages_00044_00046",
        "deir_main_pages_02000_02000",
    )
    for name in expected:
        root = tmp_path / name
        root.mkdir(parents=True)
        (root / "document.json").write_text('{"texts": []}\n')
        (root / "conversion_pages.json").write_text('{"pages": []}\n')
    extra = tmp_path / "undeclared_range"
    extra.mkdir()
    (extra / "document.json").write_text("{}\n")

    specification, artifacts = load_fixed_control_artifacts(
        evaluation_config_path=EVALUATION_CONFIG,
        control_ranges_root=tmp_path,
    )

    assert specification.control_harness.source_id == "deir_main"
    assert tuple(item.range_name for item in artifacts) == expected


def test_control_and_combined_development_reports_require_exact_3_plus_5() -> None:
    cases = load_development_cases(DEVELOPMENT_CASES)
    main_cases = tuple(item for item in cases if item["source_id"] == "deir_main")
    appendix_cases = tuple(item for item in cases if item["source_id"] == "deir_appendix_p")
    controls = ControlProjection(
        (
            _surface("control_a", "deir_main", tuple(_decision(item) for item in main_cases[:2])),
            _surface("control_b", "deir_main", tuple(_decision(item) for item in main_cases[2:])),
        )
    )

    control_report = evaluate_control_cases(development_cases=cases, projection=controls)
    combined = combine_development_report(
        development_cases=cases,
        appendix_decisions=tuple(_decision(item) for item in appendix_cases),
        control_projection=controls,
    )

    assert control_report["status"] == "pass"
    assert control_report["passed_count"] == 3
    assert combined["status"] == "pass"
    assert combined["passed_count"] == 8


def test_combined_review_inventory_retains_surface_and_source_identity() -> None:
    cases = load_development_cases(DEVELOPMENT_CASES)
    applied = tuple(
        _decision(item)
        for item in cases
        if item["expected_outcome"] == "applied"
        and item["expected_rule_id"]
        in {
            "R02_DEMOTE_BULLET_HEADING",
            "R05_APPLY_NUMBERING_REGIME",
            "R07_TRANSFER_LOCAL_HEADING_LEVEL",
        }
    )
    appendix = tuple(
        item for item in applied if item["selected_rule_id"] != "R02_DEMOTE_BULLET_HEADING"
    )
    controls = tuple(
        item for item in applied if item["selected_rule_id"] == "R02_DEMOTE_BULLET_HEADING"
    )

    inventory = build_combined_review_inventory(
        (
            _surface("appendix", "deir_appendix_p", appendix),
            _surface("controls", "deir_main", controls),
        )
    )

    assert inventory["status"] == "complete"
    assert inventory["record_count"] == len(applied)
    assert {item["source_id"] for item in inventory["records"]} == {
        "deir_appendix_p",
        "deir_main",
    }


def test_named_reports_are_deterministic_digest_bound_and_no_clobber(tmp_path: Path) -> None:
    reports = {
        "source_bound_gates": {"status": "pass", "count": 50},
        "review_inventory": {"status": "complete", "records": []},
        "development_cases": {"status": "pass", "passed_count": 8},
    }

    manifest = write_named_quality_reports(tmp_path, reports)

    assert manifest["status"] == "pass"
    assert [item["name"] for item in manifest["reports"]] == sorted(reports)
    for item in manifest["reports"]:
        content = (tmp_path / item["path"]).read_bytes()
        assert content == stable_report_bytes(reports[item["name"]])
        assert hashlib.sha256(content).hexdigest() == item["sha256"]
    persisted_manifest = (tmp_path / manifest["manifest_path"]).read_bytes()
    assert hashlib.sha256(persisted_manifest).hexdigest() == manifest["manifest_sha256"]

    with pytest.raises(FileExistsError):
        write_named_quality_reports(tmp_path, reports)


def test_named_report_manifest_rejects_a_failed_gate(tmp_path: Path) -> None:
    manifest = write_named_quality_reports(
        tmp_path,
        {"development_cases": {"status": "reject", "failed_count": 1}},
    )
    assert manifest["status"] == "reject"
    assert json.loads((tmp_path / "development_cases.json").read_text())["failed_count"] == 1


def _snapshot(kind: str, identity: str, sha256: str = "a" * 64) -> ManagedArtifactSnapshot:
    return ManagedArtifactSnapshot(
        kind=kind,  # type: ignore[arg-type]
        identity=identity,
        completion_sha256=sha256,
        inventory_sha256=sha256,
        files=(ManagedFile("records/value.json", 1, sha256),),
    )


def test_preservation_report_requires_both_immutable_artifacts_and_exact_snapshots() -> None:
    snapshots = (
        _snapshot("producer", "prv1-" + "a" * 64),
        _snapshot("task03d1_reference", "exv1-" + "b" * 64),
    )

    passed = build_preservation_report(before=snapshots, after=snapshots)
    changed = (
        snapshots[0],
        _snapshot("task03d1_reference", "exv1-" + "b" * 64, "c" * 64),
    )
    rejected = build_preservation_report(before=snapshots, after=changed)

    assert passed["status"] == "pass"
    assert passed["artifact_count"] == 2
    assert rejected["status"] == "reject"


def test_repeat_resource_report_requires_three_matches_and_both_resource_gates() -> None:
    candidate_id = "hcorv1-" + "a" * 64
    comparison = {
        "candidate_id": candidate_id,
        "semantic_match": True,
        "builds": [{}, {}, {}],
    }
    metrics = {
        "candidate_id": candidate_id,
        "cheap_relative_to_producer": True,
        "median_fresh_wall_time_seconds": 1.0,
        "wall_time_ratio": 0.1,
        "artifact_bytes": 100,
        "artifact_bytes_ratio": 0.01,
        "peak_rss_bytes": 1000,
    }

    passed = build_repeat_resource_report(
        candidate_id=candidate_id,
        repeat_comparison=comparison,
        metrics=metrics,
    )
    expensive_metrics = {**metrics, "artifact_bytes_ratio": 1.0}
    blocked = build_repeat_resource_report(
        candidate_id=candidate_id,
        repeat_comparison=comparison,
        metrics=expensive_metrics,
    )

    assert passed["status"] == "pass"
    assert passed["repeat_passed"] is True
    assert passed["resource_passed"] is True
    assert blocked["status"] == "reject"
