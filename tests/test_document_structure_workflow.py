"""Public-boundary coverage for the Task 03E.4 orchestration shell."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.document_records.document_structure import lifecycle, workflow
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
            project_root=tmp_path,
            config_identity_path=tmp_path / "config.json",
            inputs=object(),
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "c" * 64,
                source=SimpleNamespace(source_id="source"),
            ),
        ),
    )
    candidate_root = tmp_path / CANDIDATE_ID
    if existing:
        candidate_root.mkdir()
    events: list[str] = []
    expected = tmp_path / "completion.json"

    monkeypatch.setattr(workflow, "load_runtime_context", lambda **_: context)
    monkeypatch.setattr(
        workflow,
        "build_document_structure_identity",
        lambda **_: {"extraction_id": CANDIDATE_ID},
    )
    monkeypatch.setattr(workflow, "owned_runtime_paths", lambda _path: ())
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


def test_fresh_workspace_loads_and_builds_semantics_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cache miss extends verified metadata once and performs one semantic build."""
    events: list[str] = []
    construction_inputs = SimpleNamespace(expectations=object())
    build = object()
    context = cast(
        RuntimeContext,
        SimpleNamespace(
            project_root=tmp_path,
            inputs=SimpleNamespace(
                baseline_candidate_root=tmp_path / "baseline",
                control_provenance=object(),
            ),
            config=SimpleNamespace(
                baseline_candidate_id="exv1-" + "b" * 64,
                baseline_producer_run_id="prv1-" + "c" * 64,
                hierarchy_producer_run_id="prv1-" + "d" * 64,
                control_profile="strict_quality_gate",
            ),
            semantic_schema_path=tmp_path / "schema.json",
        ),
    )

    monkeypatch.setattr(
        lifecycle,
        "load_construction_inputs",
        lambda *_args, **_kwargs: (events.append("load"), construction_inputs)[1],
    )
    monkeypatch.setattr(
        lifecycle,
        "build_document_structure_records",
        lambda _inputs: (events.append("build"), build)[1],
    )
    monkeypatch.setattr(
        lifecycle,
        "build_candidate_support",
        lambda **_kwargs: (events.append("support"), object())[1],
    )
    monkeypatch.setattr(
        lifecycle,
        "validate_serialize_and_seal",
        lambda **_kwargs: events.append("seal"),
    )
    monkeypatch.setattr(lifecycle, "inherited_warnings", lambda _inputs: ())

    result = lifecycle._write_candidate_workspace(
        context=context,
        identity={"extraction_id": CANDIDATE_ID},
        candidate_id=CANDIDATE_ID,
        root=tmp_path / "workspace",
    )

    assert result is build
    assert events == ["load", "build", "support", "seal"]
