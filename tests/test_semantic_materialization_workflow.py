"""Public-boundary coverage for the Task 03E.4 orchestration shell."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.semantic_materialization import workflow
from er_commons.semantic_materialization.runtime import CandidateLocations, RuntimeContext

CANDIDATE_ID = "exv1-" + "a" * 64
REFERENCE_ID = "exv1-" + "b" * 64


@pytest.mark.parametrize("existing", [False, True])
def test_public_workflow_selects_fresh_build_or_verified_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    """The public runner exposes the lifecycle decision without private stage replay."""
    context = cast(
        RuntimeContext,
        SimpleNamespace(
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "c" * 64,
                mvp_reference_candidate_id=REFERENCE_ID,
            )
        ),
    )
    locations = CandidateLocations(
        candidate_root=tmp_path / "candidate",
        candidate_review_root=tmp_path / "candidate-review",
        reference_root=tmp_path / "reference",
        reference_review_root=tmp_path / "reference-review",
        comparison_root=tmp_path / "comparisons",
    )
    locations.reference_root.mkdir()
    if existing:
        locations.candidate_root.mkdir()
    events: list[str] = []
    expected = (tmp_path / "completion.json", tmp_path / "review.json")

    monkeypatch.setattr(workflow, "load_runtime_context", lambda **_: context)
    monkeypatch.setattr(workflow, "_candidate_identity", lambda _: {"extraction_id": CANDIDATE_ID})
    monkeypatch.setattr(workflow, "candidate_locations", lambda *_: locations)
    monkeypatch.setattr(
        workflow,
        "verify_completed_semantic_candidate",
        lambda *_: events.append("reference_verified"),
    )
    monkeypatch.setattr(
        workflow,
        "reuse_completed_candidate",
        lambda **_: (events.append("reuse"), expected)[1],
    )
    monkeypatch.setattr(
        workflow,
        "build_compare_and_publish",
        lambda **_: (events.append("fresh"), expected)[1],
    )

    result = workflow.run_semantic_materialization(tmp_path, tmp_path / "config.json")

    assert result == expected
    assert events == ["reference_verified", "reuse" if existing else "fresh"]
