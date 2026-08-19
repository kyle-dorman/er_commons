"""Audit-only command tests for sealed hierarchy candidates."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

import er_commons.hierarchy_inference as hierarchy
from er_commons.hierarchy_inference.candidate_verification import HierarchyAuditResult


def test_deep_audit_command_refuses_a_missing_candidate_before_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate_id = "hcorv1-" + "a" * 64
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_hierarchy_candidate.py",
            "--candidate-root",
            str(tmp_path / candidate_id),
            "--candidate-id",
            candidate_id,
        ],
    )
    with pytest.raises(SystemExit) as captured:
        runpy.run_path(
            Path(__file__).parents[1] / "scripts/audit_hierarchy_candidate.py",
            run_name="__main__",
        )
    assert captured.value.code == 2
    assert "deep audit requires the exact existing candidate root and ID" in capsys.readouterr().err


def test_deep_audit_command_reports_human_usable_totals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate_id = "hcorv1-" + "a" * 64
    candidate_root = tmp_path / candidate_id
    candidate_root.mkdir()
    completion = candidate_root / "records/completion_record.json"
    monkeypatch.setattr(
        hierarchy,
        "deep_audit_completed_candidate",
        lambda *_args, **_kwargs: HierarchyAuditResult(
            candidate_id,
            completion,
            13,
            4_096,
            1.25,
            "b" * 64,
            "c" * 64,
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "audit_hierarchy_candidate.py",
            "--candidate-root",
            str(candidate_root),
            "--candidate-id",
            candidate_id,
        ],
    )

    runpy.run_path(
        Path(__file__).parents[1] / "scripts/audit_hierarchy_candidate.py",
        run_name="__main__",
    )

    output = capsys.readouterr().out
    assert f"candidate_id={candidate_id}" in output
    assert "verified_files=13" in output
    assert "verified_bytes=4096" in output
    assert f"candidate_semantic_sha256={'b' * 64}" in output
    assert f"artifact_inventory_sha256={'c' * 64}" in output
    assert "elapsed_seconds=1.250" in output
