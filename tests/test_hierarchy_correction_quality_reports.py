"""Human-readable terminal quality disposition tests."""

from __future__ import annotations

import pytest

from er_commons.hierarchy_correction.failures import QualityGateRejected
from er_commons.hierarchy_correction.quality_reports import QualityReportSet


def _reports(**updates: str) -> QualityReportSet:
    statuses = {
        "development": "pass",
        "outline_numbering_29_21": "pass",
        "controls": "pass",
        "held_out": "pass",
        "review_inventory": "complete",
        "preservation": "pass",
        "repeat_resource": "pass",
        **updates,
    }
    return QualityReportSet(**{name: {"status": status} for name, status in statuses.items()})


def test_accepted_report_set_has_no_rejections() -> None:
    reports = _reports()

    reports.require_acceptance()

    assert reports.rejected_reports() == ()


def test_rejection_names_every_failed_report() -> None:
    reports = _reports(development="reject", held_out="reject")

    with pytest.raises(QualityGateRejected) as error:
        reports.require_acceptance()

    assert error.value.fatal_code == "QUALITY_GATE_REJECTED"
    assert error.value.stage == "quality"
    assert error.value.rejected_reports == ("development", "held_out")
    assert str(error.value) == "quality gate rejected reports: development, held_out"
