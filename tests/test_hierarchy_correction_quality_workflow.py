"""Synthetic composition tests for all seven prepublication quality reports."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import er_commons.hierarchy_correction.quality_workflow as workflow
from er_commons.hierarchy_correction.failures import QualityGateRejected
from er_commons.hierarchy_correction.quality_gate import (
    REPORT_NAMES,
    VerifiedQualityGatePass,
)
from er_commons.hierarchy_correction.review import HeldOutAnnotationSeal


@pytest.mark.parametrize("held_out_status", ["pass", "reject"])
def test_quality_workflow_composes_exact_required_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    held_out_status: str,
) -> None:
    candidate_id = "hcorv1-" + "a" * 64
    candidate_root = tmp_path / "candidate"
    annotations_path = tmp_path / "held_out_annotations.json"
    annotations_path.write_text("{}\n")
    repeat_path = tmp_path / "repeat_comparison.json"
    repeat_path.write_text(json.dumps({"semantic_match": True}) + "\n")
    candidate = {
        "identity": {"candidate_id": candidate_id},
        "features": [],
        "regimes": [],
        "decisions": [],
        "metrics": {"candidate_id": candidate_id},
    }
    quality_config = SimpleNamespace(
        task03e_evaluation_config=SimpleNamespace(path=Path("evaluation.json")),
        development_cases=SimpleNamespace(path=Path("development.json")),
        expected_exact_outline_anchor_count=29,
        expected_numbering_relation_count=21,
        review_artifact_relative_root=Path("review"),
    )
    specification = SimpleNamespace(appendix_p_review_pages=(SimpleNamespace(physical_page=4),))
    controls = SimpleNamespace(surfaces=(), decisions=())
    captured: dict[str, Any] = {}
    verified = VerifiedQualityGatePass(
        tmp_path / "quality_gate_pass.json",
        candidate_id,
        "b" * 64,
    )

    monkeypatch.setattr(workflow, "verify_completed_candidate", lambda *_args: None)
    monkeypatch.setattr(workflow, "_load_candidate", lambda _root: candidate)
    monkeypatch.setattr(
        workflow,
        "load_quality_gate_config",
        lambda _path: (quality_config, "c" * 64),
    )
    monkeypatch.setattr(workflow, "fixed_control_ranges_root", lambda *_args: tmp_path)
    monkeypatch.setattr(
        workflow,
        "load_fixed_control_artifacts",
        lambda **_kwargs: (specification, ()),
    )
    monkeypatch.setattr(workflow, "build_control_projection", lambda _items: controls)
    monkeypatch.setattr(workflow, "load_development_cases", lambda _path: ())
    monkeypatch.setattr(
        workflow,
        "combine_development_report",
        lambda **_kwargs: {"status": "pass"},
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_frozen_outline_numbering_gates",
        lambda **_kwargs: {"status": "pass"},
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_control_cases",
        lambda **_kwargs: {"status": "pass"},
    )
    monkeypatch.setattr(
        workflow,
        "build_held_out_evaluation",
        lambda *_args: {"status": held_out_status},
    )
    monkeypatch.setattr(
        workflow,
        "build_combined_review_inventory",
        lambda _surfaces: {"status": "complete"},
    )
    monkeypatch.setattr(
        workflow,
        "build_preservation_report",
        lambda **_kwargs: {"status": "pass"},
    )
    monkeypatch.setattr(
        workflow,
        "build_repeat_resource_report",
        lambda **_kwargs: {"status": "pass"},
    )

    def write_reports(_root: Path, reports: dict[str, Any]) -> dict[str, Any]:
        captured["reports"] = reports
        return {"status": "pass"}

    monkeypatch.setattr(workflow, "write_named_quality_reports", write_reports)
    monkeypatch.setattr(
        workflow,
        "assemble_quality_gate_pass",
        lambda **kwargs: captured.setdefault("assembly", kwargs) and verified,
    )

    def produce() -> VerifiedQualityGatePass:
        return workflow.produce_quality_gate_pass(
            data_root=tmp_path,
            project_root=tmp_path,
            correction_schema_path=tmp_path / "schema.json",
            quality_config_path=tmp_path / "quality.json",
            candidate_root=candidate_root,
            candidate_id=candidate_id,
            annotation_seal=HeldOutAnnotationSeal(
                annotations_path,
                tmp_path / "held_out_annotations.seal.json",
                candidate_id,
                "d" * 64,
            ),
            repeat_comparison_path=repeat_path,
            preservation_before=(),
            preservation_after=(),
        )

    if held_out_status == "reject":
        with pytest.raises(QualityGateRejected) as error:
            produce()
        assert error.value.rejected_reports == ("held_out",)
        assert "assembly" not in captured
    else:
        result = produce()
        assert result == verified
        assert set(captured["assembly"]["report_relative_paths"]) == set(REPORT_NAMES)
    assert set(captured["reports"]) == set(REPORT_NAMES)
    assert captured["reports"]["review_inventory"]["status"] == "complete"


def test_generic_quality_workflow_uses_only_document_local_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate_id = "hcorv1-" + "a" * 64
    annotations_path = tmp_path / "held_out_annotations.json"
    annotations_path.write_text("{}\n")
    repeat_path = tmp_path / "repeat_comparison.json"
    repeat_path.write_text("{}\n")
    quality_config = SimpleNamespace(
        quality_profile="generic_document",
        development_cases=SimpleNamespace(path=Path("alternate_cases.json")),
        document_review_pages=(1,),
        expected_exact_outline_anchor_count=0,
        expected_outline_r03_count=0,
        expected_outline_toc_override_count=0,
        expected_numbered_heading_count=0,
        expected_numbering_relation_count=0,
        review_artifact_relative_root=Path("review"),
    )
    controls = SimpleNamespace(surfaces=(), decisions=())
    captured: dict[str, Any] = {}
    monkeypatch.setattr(workflow, "verify_completed_candidate", lambda *_args: None)
    monkeypatch.setattr(
        workflow,
        "_load_candidate",
        lambda _root: {"features": [], "regimes": [], "decisions": [], "metrics": {}},
    )
    monkeypatch.setattr(
        workflow, "load_quality_gate_config", lambda _path: (quality_config, "c" * 64)
    )
    monkeypatch.setattr(workflow, "build_control_projection", lambda _items: controls)
    monkeypatch.setattr(
        workflow,
        "load_development_cases",
        lambda _path, **_kwargs: ({"source_id": "alternate"},),
    )
    monkeypatch.setattr(
        workflow,
        "evaluate_document_development_cases",
        lambda **kwargs: (
            {"status": "pass"}
            if kwargs["source_id"] == "alternate"
            else pytest.fail("selected source was not propagated")
        ),
    )
    monkeypatch.setattr(
        workflow,
        "load_fixed_control_artifacts",
        lambda **_kwargs: pytest.fail("generic workflow used Appendix P evaluation"),
    )
    monkeypatch.setattr(
        workflow, "evaluate_frozen_outline_numbering_gates", lambda **_kwargs: {"status": "pass"}
    )
    monkeypatch.setattr(workflow, "build_held_out_evaluation", lambda *_args: {"status": "pass"})
    monkeypatch.setattr(
        workflow, "build_combined_review_inventory", lambda _items: {"status": "complete"}
    )
    monkeypatch.setattr(workflow, "build_preservation_report", lambda **_kwargs: {"status": "pass"})
    monkeypatch.setattr(
        workflow, "build_repeat_resource_report", lambda **_kwargs: {"status": "pass"}
    )
    monkeypatch.setattr(
        workflow,
        "write_named_quality_reports",
        lambda _root, reports: captured.setdefault("reports", reports),
    )
    verified = VerifiedQualityGatePass(tmp_path / "quality_gate_pass.json", candidate_id, "b" * 64)
    monkeypatch.setattr(workflow, "assemble_quality_gate_pass", lambda **_kwargs: verified)

    result = workflow.produce_quality_gate_pass(
        data_root=tmp_path,
        project_root=tmp_path,
        correction_schema_path=tmp_path / "schema.json",
        quality_config_path=tmp_path / "quality.json",
        candidate_root=tmp_path / "candidate",
        candidate_id=candidate_id,
        source_id="alternate",
        annotation_seal=HeldOutAnnotationSeal(
            annotations_path,
            tmp_path / "held_out_annotations.seal.json",
            candidate_id,
            "d" * 64,
        ),
        repeat_comparison_path=repeat_path,
        preservation_before=(),
        preservation_after=(),
    )

    assert result == verified
    assert captured["reports"]["controls"]["profile"] == "document_local_only"
