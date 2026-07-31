"""Named quality-report set and explicit terminal disposition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from er_commons.hierarchy_correction.failures import QualityGateRejected

JsonRecord = dict[str, Any]
EXPECTED_REPORT_STATUS = {
    "development": "pass",
    "outline_numbering_29_21": "pass",
    "controls": "pass",
    "held_out": "pass",
    "review_inventory": "complete",
    "preservation": "pass",
    "repeat_resource": "pass",
}


@dataclass(frozen=True)
class QualityReportSet:
    """The seven named reports required before publication can be considered."""

    development: JsonRecord
    outline_numbering_29_21: JsonRecord
    controls: JsonRecord
    held_out: JsonRecord
    review_inventory: JsonRecord
    preservation: JsonRecord
    repeat_resource: JsonRecord

    def as_mapping(self) -> dict[str, JsonRecord]:
        """Return reports in the durable gate order."""
        return {name: getattr(self, name) for name in EXPECTED_REPORT_STATUS}

    def rejected_reports(self) -> tuple[str, ...]:
        """Name every report whose terminal status blocks publication."""
        return tuple(
            name
            for name, expected_status in EXPECTED_REPORT_STATUS.items()
            if self.as_mapping()[name].get("status") != expected_status
        )

    def require_acceptance(self) -> None:
        """Raise a typed rejection instead of constructing a pass-only model."""
        rejected = self.rejected_reports()
        if rejected:
            raise QualityGateRejected(rejected)


def require_report_names(reports: Mapping[str, JsonRecord]) -> None:
    """Fail with explicit missing and unexpected report names."""
    expected = set(EXPECTED_REPORT_STATUS)
    actual = set(reports)
    if actual != expected:
        raise ValueError(
            "quality report names differ: "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )
