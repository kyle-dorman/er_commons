"""Focused ownership tests for the in-process semantic stage runner."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import er_commons.hierarchy_inference.single_build as single_build


def test_single_build_runs_each_semantic_stage_once_in_fixed_order(monkeypatch: Any) -> None:
    events: list[str] = []
    feature = {"stable_item_key": "a" * 64}
    inputs = SimpleNamespace(
        alignment_pages={1: object(), 2: object()},
        document={},
        selected_source=SimpleNamespace(source_path=Path("source.pdf")),
    )

    def operation(name: str, result: object) -> Any:
        def run(*_args: object, **_kwargs: object) -> object:
            events.append(name)
            return result

        return run

    monkeypatch.setattr(
        single_build,
        "start_stage",
        lambda stage, _units: events.append(f"start:{stage}") or 0.0,
    )
    monkeypatch.setattr(
        single_build,
        "complete_stage",
        lambda stage, _started, _units: events.append(f"complete:{stage}") or 1.0,
    )
    monkeypatch.setattr(single_build, "_peak_rss_bytes", lambda: 123)
    monkeypatch.setattr(
        single_build,
        "build_feature_seeds",
        operation("feature_indexing", [feature]),
    )
    pdf_observations = SimpleNamespace(outline_observations=(), diagnostics=())
    monkeypatch.setattr(
        single_build,
        "read_pdf_observations",
        operation("outline_observations", pdf_observations),
    )
    monkeypatch.setattr(
        single_build,
        "apply_outline_observations",
        operation("outline_overlay", [feature]),
    )
    monkeypatch.setattr(
        single_build,
        "read_native_heading_observations",
        operation("native_headings", {}),
    )
    monkeypatch.setattr(
        single_build,
        "document_index_text_pointers",
        operation("document_index_pointers", frozenset()),
    )
    toc = SimpleNamespace(
        features=(feature,),
        entries=(),
        reconciliations=(),
        diagnostics=(),
    )
    monkeypatch.setattr(single_build, "build_visible_toc", operation("visible_toc", toc))
    scopes = SimpleNamespace(features=(feature,), regimes=())
    monkeypatch.setattr(
        single_build,
        "build_numbering_regimes",
        operation("numbering_scopes", scopes),
    )
    decisions = SimpleNamespace(decisions=(), ambiguities=())
    monkeypatch.setattr(
        single_build,
        "build_rule_decisions",
        operation("rule_decisions", decisions),
    )
    hierarchy = SimpleNamespace(hierarchy={}, warnings=())
    monkeypatch.setattr(
        single_build,
        "build_corrected_hierarchy",
        operation("hierarchy_projection", hierarchy),
    )

    result = single_build.build_single_semantic_candidate(inputs)

    assert events == [
        "start:feature_indexing",
        "feature_indexing",
        "complete:feature_indexing",
        "start:outline_observations",
        "outline_observations",
        "complete:outline_observations",
        "start:outline_overlay",
        "outline_overlay",
        "native_headings",
        "complete:outline_overlay",
        "start:visible_toc",
        "document_index_pointers",
        "visible_toc",
        "complete:visible_toc",
        "start:numbering_scopes",
        "numbering_scopes",
        "complete:numbering_scopes",
        "start:rule_decisions",
        "rule_decisions",
        "complete:rule_decisions",
        "start:hierarchy_projection",
        "hierarchy_projection",
        "complete:hierarchy_projection",
    ]
    assert result.stage_wall_time_seconds == {
        "feature_indexing": 1.0,
        "outline_observations": 1.0,
        "outline_overlay": 1.0,
        "visible_toc": 1.0,
        "numbering_scopes": 1.0,
        "rule_decisions": 1.0,
        "hierarchy_projection": 1.0,
    }
    assert result.semantic.features == (feature,)
    assert result.peak_rss_bytes == 123
