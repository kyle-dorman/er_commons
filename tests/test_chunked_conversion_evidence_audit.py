"""Focused tests for read-only Task 03H.2 sealed-evidence auditing."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.evidence_audit import (
    EvidenceRootSpec,
    RecordedClaim,
    Task03H2EvidenceSet,
    audit_evidence_root,
    audit_evidence_roots,
    audit_task03h2_evidence,
)
from er_commons.chunked_conversion.qualification.semantic_comparison import (
    QualificationDiagnosticError,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _sealed_root(root: Path, evidence_id: str = "gatec1-test") -> EvidenceRootSpec:
    report = root / "records/report.json"
    _write(report, {"checks": {"preserved": True}})
    inventory_path = root / "records/artifact_inventory.json"
    inventory = {
        "files": [
            {
                "path": "records/report.json",
                "byte_size": report.stat().st_size,
                "sha256": sha256_file(report),
            }
        ],
        "file_count": 1,
        "byte_count": report.stat().st_size,
    }
    _write(inventory_path, inventory)
    _write(
        root / "records/completion_record.json",
        {
            "run_id": evidence_id,
            "status": "complete",
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
        },
    )
    return EvidenceRootSpec(
        role="gate_c",
        root=root,
        expected_id=evidence_id,
        completion_id_field="run_id",
        claims=(RecordedClaim("records/report.json", "/checks/preserved", True),),
    )


def test_audit_validates_explicit_identity_seal_files_and_claims(tmp_path: Path) -> None:
    spec = _sealed_root(tmp_path / "gate-c")

    audit = audit_evidence_root(spec)

    assert audit.role == "gate_c"
    assert audit.evidence_id == "gatec1-test"
    assert audit.file_count == 1
    assert audit.byte_count > 0


def test_audit_rejects_corruption_with_exact_artifact_path(tmp_path: Path) -> None:
    spec = _sealed_root(tmp_path / "gate-c")
    report = spec.root / "records/report.json"
    report.write_text("{}\n")

    with pytest.raises(QualificationDiagnosticError) as caught:
        audit_evidence_root(spec)
    assert caught.value.code in {"artifact_size", "artifact_checksum"}
    assert caught.value.path == str(report.resolve())


def test_audit_rejects_extra_file_and_false_recorded_claim(tmp_path: Path) -> None:
    extra_spec = _sealed_root(tmp_path / "extra")
    (extra_spec.root / "unmanaged.txt").write_text("unexpected")
    with pytest.raises(QualificationDiagnosticError, match="managed_file_set"):
        audit_evidence_root(extra_spec)

    claim_spec = _sealed_root(tmp_path / "claim")
    report = claim_spec.root / "records/report.json"
    _write(report, {"checks": {"preserved": False}})
    inventory_path = claim_spec.root / "records/artifact_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    inventory["files"][0].update(byte_size=report.stat().st_size, sha256=sha256_file(report))
    inventory["byte_count"] = report.stat().st_size
    _write(inventory_path, inventory)
    completion_path = claim_spec.root / "records/completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    _write(completion_path, completion)
    with pytest.raises(QualificationDiagnosticError, match="recorded_pass_claim"):
        audit_evidence_root(claim_spec)


def test_audit_rejects_wrong_identity_and_duplicate_root(tmp_path: Path) -> None:
    spec = _sealed_root(tmp_path / "gate-c")
    wrong = EvidenceRootSpec("gate_c", spec.root, "other", "run_id")
    with pytest.raises(QualificationDiagnosticError, match="completion_identity"):
        audit_evidence_root(wrong)
    with pytest.raises(QualificationDiagnosticError, match="unique_evidence_root"):
        audit_evidence_roots((spec, spec))


def test_task_oracle_requires_all_five_named_roots(tmp_path: Path) -> None:
    roles = ("gate_a", "gate_b", "gate_c", "aggregate", "downstream")
    specs = tuple(
        replace(_sealed_root(tmp_path / role, evidence_id=role), role=role) for role in roles
    )
    evidence = Task03H2EvidenceSet(*specs)

    assert [item.role for item in audit_task03h2_evidence(evidence)] == list(roles)


def test_qualification_modules_remain_human_sized() -> None:
    root = Path("src/er_commons/chunked_conversion/qualification")
    for name in ("semantic_comparison.py", "evidence_audit.py"):
        path = root / name
        source = path.read_text()
        assert len(source.splitlines()) <= 270, f"split responsibilities in {name}"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 80, f"split {name}:{node.name} ({length} lines)"
