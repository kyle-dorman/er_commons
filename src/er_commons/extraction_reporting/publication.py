"""Completion-last publication for machine extraction reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import json_bytes, jsonl_bytes, sha256_file, write_json_atomic
from er_commons.extraction_reporting.inputs import JsonObject


@dataclass(frozen=True)
class ExtractionReportArtifacts:
    """Paths for one candidate-neutral report bundle."""

    report: Path
    anomalies: Path
    inventory: Path
    completion: Path


def write_extraction_report(
    root: Path,
    *,
    report: JsonObject,
    anomalies: list[JsonObject],
) -> ExtractionReportArtifacts:
    """Write machine evidence with an inventory and completion marker last."""
    root.mkdir(parents=True, exist_ok=False)
    report_path = root / "extraction_report.json"
    anomaly_path = root / "anomalies.jsonl"
    report_path.write_bytes(json_bytes(report))
    anomaly_path.write_bytes(jsonl_bytes(anomalies))
    inventory_path = root / "artifact_inventory.json"
    inventory = {
        "files": [
            _file_record(report_path, root),
            _file_record(anomaly_path, root),
        ]
    }
    write_json_atomic(inventory_path, inventory)
    completion_path = root / "completion.json"
    write_json_atomic(
        completion_path,
        {
            "schema_version": "er_commons.extraction_report_completion.v2",
            "scope_id": report["scope_id"],
            "status": "machine_report_complete",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "publication_authority": False,
            "task04_status": "not_evaluated",
            "completion_last": True,
        },
    )
    return ExtractionReportArtifacts(report_path, anomaly_path, inventory_path, completion_path)


def _file_record(path: Path, root: Path) -> JsonObject:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


__all__ = ["ExtractionReportArtifacts", "write_extraction_report"]
