"""Public-boundary coverage for the Task 03E.4 orchestration shell."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.document_records.document_structure import workflow
from er_commons.document_records.document_structure.runtime import RuntimeContext

CANDIDATE_ID = "exv1-" + "a" * 64


@pytest.mark.parametrize("existing", [False, True])
def test_public_workflow_selects_fresh_build_or_verified_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    """The public runner exposes the lifecycle decision without private stage replay."""
    context = cast(
        RuntimeContext,
        SimpleNamespace(
            task_root=tmp_path,
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "c" * 64,
            ),
        ),
    )
    candidate_root = tmp_path / CANDIDATE_ID
    if existing:
        candidate_root.mkdir()
    events: list[str] = []
    expected = tmp_path / "completion.json"

    monkeypatch.setattr(workflow, "load_runtime_context", lambda **_: context)
    monkeypatch.setattr(workflow, "_candidate_identity", lambda _: {"extraction_id": CANDIDATE_ID})
    monkeypatch.setattr(
        workflow,
        "reuse_completed_candidate",
        lambda **_: (events.append("reuse"), expected)[1],
    )
    monkeypatch.setattr(
        workflow,
        "build_validate_and_publish",
        lambda **_: (events.append("fresh"), expected)[1],
    )

    result = workflow.map_document_structure(tmp_path, tmp_path / "config.json")

    assert result == expected
    assert events == ["reuse" if existing else "fresh"]
