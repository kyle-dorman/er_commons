"""Offline lifecycle coverage for the human-owned semantic materializer."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.canonical_extraction.publication import write_json
from er_commons.semantic_materialization import lifecycle
from er_commons.semantic_materialization.runtime import CandidateLocations, RuntimeContext

CANDIDATE_ID = "exv1-" + "a" * 64


def test_fake_lifecycle_publishes_then_checksum_reuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The full lifecycle reaches publication and reuse without document tooling."""
    context, locations = _context_and_locations(tmp_path)
    _patch_lifecycle_edges(monkeypatch)

    completion, review = lifecycle.build_compare_and_publish(
        context=context,
        locations=locations,
        identity={"extraction_id": CANDIDATE_ID},
        candidate_id=CANDIDATE_ID,
    )

    assert completion == locations.candidate_root / "records" / "completion_record.json"
    assert review == locations.candidate_review_root / "review_manifest.json"
    assert locations.candidate_root.is_dir()

    reused_completion, reused_review = lifecycle.reuse_completed_candidate(
        context=context, locations=locations, candidate_id=CANDIDATE_ID
    )
    assert reused_completion == completion
    assert reused_review == review


def test_fake_lifecycle_retains_failed_workspace_without_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure after partial sealing cannot leave a misleading completed candidate."""
    context, locations = _context_and_locations(tmp_path)

    def fail_after_partial(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "records" / "partial.json", {"stage": "sealing"})
        write_json(root / "records" / "completion_record.json", {"status": "complete"})
        raise RuntimeError("simulated sealing failure")

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", fail_after_partial)

    with pytest.raises(RuntimeError, match="simulated sealing failure"):
        lifecycle.build_compare_and_publish(
            context=context,
            locations=locations,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    attempts = sorted((context.task_root / "attempts").iterdir())
    partial = next(
        attempt for attempt in attempts if (attempt / "records" / "partial.json").is_file()
    )
    assert not (partial / "records" / "completion_record.json").exists()
    assert not locations.candidate_root.exists()


def test_second_reservation_failure_retains_first_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second reservation failure cannot strand the first workspace in .tmp."""
    context, locations = _context_and_locations(tmp_path)
    real_reserve = lifecycle.reserve_workspace
    reservation_count = 0

    def fail_second_reservation(task_root: Path, candidate_id: str, token: str) -> Any:
        nonlocal reservation_count
        reservation_count += 1
        if reservation_count == 2:
            raise RuntimeError("simulated second reservation failure")
        return real_reserve(task_root, candidate_id, token)

    monkeypatch.setattr(lifecycle, "reserve_workspace", fail_second_reservation)

    with pytest.raises(RuntimeError, match="simulated second reservation failure"):
        lifecycle.build_compare_and_publish(
            context=context,
            locations=locations,
            identity={"extraction_id": CANDIDATE_ID},
            candidate_id=CANDIDATE_ID,
        )

    attempts = list((context.task_root / "attempts").iterdir())
    assert len(attempts) == 1
    assert not (context.task_root / ".tmp" / attempts[0].name).exists()
    assert not locations.candidate_root.exists()


def _context_and_locations(tmp_path: Path) -> tuple[RuntimeContext, CandidateLocations]:
    task_root = tmp_path / "task"
    review_root = tmp_path / "review"
    context = cast(
        RuntimeContext,
        SimpleNamespace(
            task_root=task_root,
            source_pdf=tmp_path / "source.pdf",
            construction_inputs=None,
            inputs=None,
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "b" * 64,
                baseline_producer_run_id="prv1-baseline",
                hierarchy_producer_run_id="prv1-hierarchy",
                mvp_reference_candidate_id="exv1-" + "c" * 64,
                review_pages=(1, 11, 44),
            ),
            project_root=tmp_path,
        ),
    )
    return context, CandidateLocations(
        candidate_root=task_root / CANDIDATE_ID,
        candidate_review_root=review_root / CANDIDATE_ID,
        reference_root=task_root / ("exv1-" + "c" * 64),
        reference_review_root=review_root / ("exv1-" + "c" * 64),
        comparison_root=tmp_path / "comparisons",
    )


def _patch_lifecycle_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    def write_complete_workspace(**kwargs: Any) -> None:
        root = cast(Path, kwargs["root"])
        write_json(root / "canonical" / "payload.json", {"status": "built"})
        write_json(root / "records" / "completion_record.json", {"status": "complete"})

    def write_review(**kwargs: Any) -> Path:
        review_root = cast(Path, kwargs["review_root"])
        review_root.mkdir(parents=True, exist_ok=True)
        manifest = review_root / "review_manifest.json"
        write_json(manifest, {"status": "reviewed"})
        return manifest

    monkeypatch.setattr(lifecycle, "_write_candidate_workspace", write_complete_workspace)
    monkeypatch.setattr(lifecycle, "build_semantic_review_cache", write_review)
    monkeypatch.setattr(
        lifecycle,
        "verify_completed_semantic_candidate",
        lambda root, candidate_id: root / "records" / "completion_record.json",
    )
    monkeypatch.setattr(
        lifecycle,
        "_compare_and_record",
        lambda **kwargs: cast(CandidateLocations, kwargs["locations"]).comparison_root.joinpath(
            "comparison_report.json"
        ),
    )
