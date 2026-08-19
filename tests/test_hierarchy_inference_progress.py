"""Progress-reporting tests for long hierarchy candidate assembly phases."""

from __future__ import annotations

import logging

import pytest

from er_commons.hierarchy_inference import single_build
from er_commons.hierarchy_inference.progress import (
    CandidateAssemblyProgress,
    CandidatePhase,
    ProgressSnapshot,
)


def test_progress_logs_throughput_and_eta(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("test.hierarchy.progress")
    progress = CandidateAssemblyProgress(
        logger,
        "hcorv1-" + "a" * 64,
        report_interval_seconds=0,
    )

    with caplog.at_level(logging.INFO, logger=logger.name):
        progress.report(
            ProgressSnapshot(CandidatePhase.SEMANTIC_SCHEMA_VALIDATION, 0, 100, "records")
        )
        progress.report(
            ProgressSnapshot(CandidatePhase.SEMANTIC_SCHEMA_VALIDATION, 50, 100, "records")
        )
        progress.report(
            ProgressSnapshot(CandidatePhase.SEMANTIC_SCHEMA_VALIDATION, 100, 100, "records")
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any("state=start" in message and "total_units=100" in message for message in messages)
    assert any(
        "state=progress" in message
        and "throughput_units_per_second=" in message
        and "eta_seconds=" in message
        for message in messages
    )
    assert any(
        "state=complete" in message and "eta_seconds=0.000" in message for message in messages
    )


@pytest.mark.parametrize(
    ("processed", "total"),
    [(-1, 1), (2, 1), (0, -1)],
)
def test_progress_rejects_invalid_counts(processed: int, total: int) -> None:
    with pytest.raises(ValueError, match="counts are invalid"):
        ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, processed, total, "records")


def test_progress_rejects_a_phase_that_changes_its_total() -> None:
    progress = CandidateAssemblyProgress(logging.getLogger(__name__), "candidate")
    progress.report(ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, 0, 10, "records"))

    with pytest.raises(ValueError, match="changed its total or unit"):
        progress.report(ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, 1, 11, "records"))


def test_progress_rejects_regression_without_replacing_failure_evidence() -> None:
    progress = CandidateAssemblyProgress(logging.getLogger(__name__), "candidate")
    accepted = ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, 7, 10, "records")
    progress.report(accepted)

    with pytest.raises(ValueError, match="progress regressed"):
        progress.report(ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, 6, 10, "records"))

    assert progress.last_snapshot == accepted


def test_semantic_stage_boundaries_use_one_consistent_unit(
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected_units = {
        "feature_indexing": "pages",
        "outline_observations": "features",
        "outline_overlay": "features",
        "visible_toc": "features",
        "numbering_scopes": "features",
        "rule_decisions": "features",
        "hierarchy_projection": "features",
    }

    with caplog.at_level(logging.INFO, logger=single_build.LOGGER.name):
        for stage in expected_units:
            started = single_build.start_stage(stage, 1)
            single_build.complete_stage(stage, started, 1)

    messages = [record.getMessage() for record in caplog.records]
    for stage, unit in expected_units.items():
        assert any(
            f"started stage={stage}" in message and f"unit={unit}" in message
            for message in messages
        )
        assert any(
            f"completed stage={stage}" in message and f"unit={unit}" in message
            for message in messages
        )
