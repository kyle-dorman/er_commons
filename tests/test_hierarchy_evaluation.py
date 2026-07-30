"""Behavior and frozen-evidence tests for the human-owned hierarchy evaluator."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from er_commons.document_extraction.hierarchy.process import completed_run_root
from er_commons.document_extraction.hierarchy.report import (
    HierarchyEvaluationReport,
    machine_gate_status,
)
from er_commons.document_extraction.hierarchy.run_comparison import (
    compare_producer_runs,
)
from er_commons.document_extraction.hierarchy.specification import (
    load_hierarchy_evaluation_spec,
)

BASELINE_ID = "prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0"
CANDIDATE_ID = "prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1"
COMPARISON_ID = "cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0"


def test_machine_gate_requires_each_independent_surface() -> None:
    passing = {"status": "pass"}
    rejected = {"status": "reject"}

    assert machine_gate_status(passing, passing, passing) == "pass"
    assert machine_gate_status(rejected, passing, passing) == "reject"
    assert machine_gate_status(passing, rejected, passing) == "reject"
    assert machine_gate_status(passing, passing, rejected) == "reject"


def test_report_serialization_keeps_stable_contract() -> None:
    comparison = {"status": "pass"}
    report = HierarchyEvaluationReport(
        comparison_id="comparison",
        evaluation_path=Path("evaluation.json"),
        evaluation_sha256="evaluation-sha",
        candidate_config_path=Path("candidate.json"),
        candidate_config_sha256="candidate-sha",
        baseline_run_id="baseline",
        candidate_run_id="candidate",
        publication_status="already_published",
        baseline_comparison=comparison,
        repeat_comparison=comparison,
        control_report=comparison,
        timings_seconds={"repeat": 1.5},
    )

    serialized = report.to_json()

    assert serialized["machine_status"] == "pass"
    assert serialized["human_review_status"] == "pending"
    assert serialized["evaluation"] == {
        "path": "evaluation.json",
        "sha256": "evaluation-sha",
    }
    assert "published_completion" not in serialized


def test_completion_path_failure_names_expected_and_actual() -> None:
    with pytest.raises(
        ValueError,
        match="expected=completion_record.json actual=manifest.json",
    ):
        completed_run_root(Path("/tmp/run/records/manifest.json"))


def test_frozen_task03e_comparisons_are_exactly_reproduced() -> None:
    """Recompute both 159-artifact comparisons against immutable Task 03E evidence."""
    data_root_value = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not data_root_value:
        pytest.skip("ER_COMMONS_DATA_ROOT is not configured")
    data_root = Path(data_root_value)
    comparison_root = (
        data_root / "pipelines/brisbane_baylands/task_03e_hierarchy_review" / COMPARISON_ID
    )
    report_path = comparison_root / "producer_comparison_report.json"
    producer_root = data_root / "pipelines/brisbane_baylands/task_03c_single_document"
    if not report_path.is_file() or not producer_root.is_dir():
        pytest.skip("frozen Task 03E evidence is not present")

    frozen = json.loads(report_path.read_text())
    spec, _sha256 = load_hierarchy_evaluation_spec(
        Path("configs/brisbane_baylands_2025_deir_task03e_hierarchy_evaluation_v1.json")
    )
    review_pages = {item.physical_page for item in spec.appendix_p_review_pages}
    baseline = producer_root / BASELINE_ID
    candidate = producer_root / CANDIDATE_ID
    repeat = comparison_root / "scratch_build_b" / CANDIDATE_ID

    assert (
        compare_producer_runs(
            baseline,
            candidate,
            review_pages=review_pages,
        )
        == frozen["baseline_comparison"]
    )
    assert (
        compare_producer_runs(
            candidate,
            repeat,
            review_pages=review_pages,
        )
        == frozen["repeat_comparison"]
    )
