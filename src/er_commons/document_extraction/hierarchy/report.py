"""Stable report construction for the Task 03E machine gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from er_commons.document_extraction.hierarchy.document import JsonObject


def machine_gate_status(
    baseline_comparison: JsonObject,
    repeat_comparison: JsonObject,
    control_report: JsonObject,
) -> str:
    """Require all three independent evidence surfaces to pass."""
    statuses = (
        baseline_comparison.get("status"),
        repeat_comparison.get("status"),
        control_report.get("status"),
    )
    return "pass" if statuses == ("pass", "pass", "pass") else "reject"


@dataclass
class HierarchyEvaluationReport:
    """Named state for the persisted producer-comparison report."""

    comparison_id: str
    evaluation_path: Path
    evaluation_sha256: str
    candidate_config_path: Path
    candidate_config_sha256: str
    baseline_run_id: str
    candidate_run_id: str
    publication_status: str
    baseline_comparison: JsonObject
    repeat_comparison: JsonObject
    control_report: JsonObject
    timings_seconds: dict[str, float] = field(default_factory=dict)
    published_completion: Path | None = None

    def to_json(self) -> JsonObject:
        """Serialize the exact Task 03E report contract."""
        report: JsonObject = {
            "schema_version": "1.0.0",
            "comparison_id": self.comparison_id,
            "evaluation": {
                "path": self.evaluation_path.as_posix(),
                "sha256": self.evaluation_sha256,
            },
            "candidate_configuration": {
                "path": self.candidate_config_path.as_posix(),
                "sha256": self.candidate_config_sha256,
            },
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "machine_status": machine_gate_status(
                self.baseline_comparison,
                self.repeat_comparison,
                self.control_report,
            ),
            "human_review_status": "pending",
            "publication_status": self.publication_status,
            "timings_seconds": self.timings_seconds,
            "baseline_comparison": self.baseline_comparison,
            "repeat_comparison": self.repeat_comparison,
            "control_report": self.control_report,
        }
        if self.published_completion is not None:
            report["published_completion"] = self.published_completion.as_posix()
        return report
