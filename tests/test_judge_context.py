"""Check frozen context identity and one-copy composition without provider calls."""

import json
from pathlib import Path

import pytest

from er_commons import judge_context as context


def test_context_matches_frozen_real_evaluation_identity():
    """The synthetic/runtime context is exactly the accepted real overview bytes."""
    root = Path(__file__).resolve().parents[1]
    freeze = json.loads((root / "docs/specs/task11e_frozen_generation_v1.json").read_text())
    assert context.OVERVIEW_SHA256 == freeze["context_sha256"]
    assert context.OVERVIEW_PATH == root / freeze["context_path"]
    summary = context.baylands_overview()
    expected = freeze["context_delivery"]["template"].replace("{overview_file_text}", summary)
    expected = expected.replace("{unchanged_base_or_judge_core}", "Judge instructions.")
    assert context.structured_conclusion_prompt("Judge instructions.") == expected
    assert context.compose_project_context(expected, summary) == expected
    assert expected.count("<project_context>") == 1
    with pytest.raises(ValueError, match="context differ"):
        context.compose_project_context(expected, "A different overview.")


def test_context_rejects_unversioned_file_change(tmp_path, monkeypatch):
    """Context drift must fail before provider dispatch rather than silently prefixing it."""
    changed = tmp_path / "overview.md"
    changed.write_text("Changed context.")
    monkeypatch.setattr(context, "OVERVIEW_PATH", changed)
    with pytest.raises(ValueError, match="overview changed"):
        context.structured_conclusion_prompt("Judge instructions.")
