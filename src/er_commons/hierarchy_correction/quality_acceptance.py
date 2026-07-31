"""Candidate-bound quality pass assembly and verification."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from er_commons.hierarchy_correction.candidate_records import stable_json_bytes
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.quality_config import (
    StrictModel,
    load_quality_gate_config,
)
from er_commons.hierarchy_correction.quality_evidence import verify_config_evidence

REPORT_NAMES = (
    "development",
    "outline_numbering_29_21",
    "controls",
    "held_out",
    "review_inventory",
    "preservation",
    "repeat_resource",
)
SEMANTIC_PATHS = (
    "artifacts/item_features.jsonl",
    "artifacts/visible_toc_entries.jsonl",
    "artifacts/toc_reconciliation.jsonl",
    "artifacts/regimes.jsonl",
    "artifacts/decisions.jsonl",
    "artifacts/hierarchy.json",
    "artifacts/ambiguities.jsonl",
    "artifacts/warnings.jsonl",
)


class ReportEvidence(StrictModel):
    """One named candidate-bound external report."""

    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["pass", "complete"]


class QualityGateReports(StrictModel):
    """Complete report set required for a terminal pass."""

    development: ReportEvidence
    outline_numbering_29_21: ReportEvidence
    controls: ReportEvidence
    held_out: ReportEvidence
    review_inventory: ReportEvidence
    preservation: ReportEvidence
    repeat_resource: ReportEvidence

    @model_validator(mode="after")
    def require_distinct_paths(self) -> QualityGateReports:
        """Prevent report aliasing and require each gate's terminal status."""
        paths = [getattr(self, name).path for name in REPORT_NAMES]
        if len(set(paths)) != len(paths):
            raise ValueError("quality-gate report paths must be distinct")
        expected = {
            "development": "pass",
            "outline_numbering_29_21": "pass",
            "controls": "pass",
            "held_out": "pass",
            "review_inventory": "complete",
            "preservation": "pass",
            "repeat_resource": "pass",
        }
        for name, expected_status in expected.items():
            if getattr(self, name).status != expected_status:
                raise ValueError(f"quality-gate report terminal status differs: {name}")
        return self


class QualityGatePass(StrictModel):
    """Terminal external acceptance record bound to one candidate semantic."""

    record_type: Literal["hierarchy_quality_gate_pass"]
    schema_version: Literal["1.0.0"]
    quality_gate_id: Literal["brisbane_baylands_2025_deir_task03e2_quality_gate_v1"]
    quality_gate_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_id: str = Field(pattern=r"^hcorv1-[0-9a-f]{64}$")
    candidate_semantic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reports: QualityGateReports
    status: Literal["pass"]


@dataclass(frozen=True)
class VerifiedQualityGatePass:
    """Opaque proof returned only after all external evidence verifies."""

    path: Path
    candidate_id: str
    candidate_semantic_sha256: str


def candidate_semantic_sha256(candidate_root: Path) -> str:
    """Hash exact semantic artifact checksums in their frozen path order."""
    records = []
    for relative in SEMANTIC_PATHS:
        path = candidate_root / relative
        if not path.is_file():
            raise ValueError(f"quality-gate candidate semantic is missing: {relative}")
        records.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return canonical_json_sha256({"semantic_files": records})


def verify_quality_gate_pass(
    *,
    pass_path: Path,
    config_path: Path,
    candidate_root: Path,
    candidate_id: str,
    project_root: Path,
    data_root: Path,
) -> VerifiedQualityGatePass:
    """Verify config, canonical seals, reports, and candidate semantic binding."""
    config, config_sha256 = load_quality_gate_config(config_path)
    verify_config_evidence(config, project_root, data_root)
    expected_root = data_root / config.review_artifact_relative_root / candidate_id
    if pass_path != expected_root / "quality_gate_pass.json":
        raise ValueError("quality-gate pass path differs from configured candidate root")
    record = QualityGatePass.model_validate_json(pass_path.read_bytes())
    if record.quality_gate_config_sha256 != config_sha256:
        raise ValueError("quality-gate config checksum differs")
    if record.quality_gate_id != config.quality_gate_id or record.candidate_id != candidate_id:
        raise ValueError("quality-gate candidate or gate identity differs")
    semantic_sha256 = candidate_semantic_sha256(candidate_root)
    if record.candidate_semantic_sha256 != semantic_sha256:
        raise ValueError("quality-gate candidate semantic checksum differs")
    for name in REPORT_NAMES:
        evidence = getattr(record.reports, name)
        _require_contained(evidence.path)
        raw = (expected_root / evidence.path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != evidence.sha256:
            raise ValueError(f"quality-gate report checksum differs: {name}")
        report = json.loads(raw)
        if not isinstance(report, dict) or report.get("status") != evidence.status:
            raise ValueError(f"quality-gate report status differs: {name}")
        if name == "repeat_resource":
            _verify_repeat_resource_binding(report, candidate_root, candidate_id)
    return VerifiedQualityGatePass(pass_path, candidate_id, semantic_sha256)


def write_quality_gate_pass(path: Path, record: QualityGatePass) -> None:
    """Write a terminal pass once; report producers must construct its evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(stable_json_bytes(record.model_dump(mode="json")))


def assemble_quality_gate_pass(
    *,
    config_path: Path,
    candidate_root: Path,
    candidate_id: str,
    project_root: Path,
    data_root: Path,
    report_relative_paths: Mapping[str, Path],
) -> VerifiedQualityGatePass:
    """Bind a complete existing report set and write the terminal pass once."""
    config, config_sha256 = load_quality_gate_config(config_path)
    verify_config_evidence(config, project_root, data_root)
    if set(report_relative_paths) != set(REPORT_NAMES):
        raise ValueError("quality-gate report-name set differs")
    review_root = data_root / config.review_artifact_relative_root / candidate_id
    report_evidence = {}
    for name in REPORT_NAMES:
        relative = report_relative_paths[name]
        _require_contained(relative)
        raw = (review_root / relative).read_bytes()
        report = json.loads(raw)
        if not isinstance(report, dict) or not isinstance(report.get("status"), str):
            raise ValueError(f"quality-gate report has no terminal status: {name}")
        report_evidence[name] = {
            "path": relative,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "status": report["status"],
        }
    record = QualityGatePass.model_validate(
        {
            "record_type": "hierarchy_quality_gate_pass",
            "schema_version": "1.0.0",
            "quality_gate_id": config.quality_gate_id,
            "quality_gate_config_sha256": config_sha256,
            "candidate_id": candidate_id,
            "candidate_semantic_sha256": candidate_semantic_sha256(candidate_root),
            "reports": report_evidence,
            "status": "pass",
        }
    )
    pass_path = review_root / "quality_gate_pass.json"
    write_quality_gate_pass(pass_path, record)
    return verify_quality_gate_pass(
        pass_path=pass_path,
        config_path=config_path,
        candidate_root=candidate_root,
        candidate_id=candidate_id,
        project_root=project_root,
        data_root=data_root,
    )


def _require_contained(path: Path) -> None:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("quality-gate report paths must be contained relative paths")


def _verify_repeat_resource_binding(
    report: dict[str, object], candidate_root: Path, candidate_id: str
) -> None:
    metrics = json.loads((candidate_root / "records/metrics.json").read_bytes())
    fields = (
        "median_fresh_wall_time_seconds",
        "wall_time_ratio",
        "artifact_bytes",
        "artifact_bytes_ratio",
        "peak_rss_bytes",
    )
    if report.get("candidate_id") != candidate_id or any(
        report.get(field) != metrics.get(field) for field in fields
    ):
        raise ValueError("quality-gate repeat/resource metrics differ from candidate")
