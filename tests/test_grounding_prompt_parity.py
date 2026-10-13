"""Byte parity protects live cloud instructions from historical prompt cleanup."""

import hashlib
import json
from pathlib import Path

from er_commons import grounding_comparison_semantics as semantics
from er_commons import grounding_stages as legacy


def test_cloud_prompts_match_precleanup_hashes(monkeypatch):
    """Legacy wording can change independently without silently rewriting cloud requests."""
    expected = json.loads(Path("tests/fixtures/task09e1_prompt_hashes.json").read_text())
    monkeypatch.setattr(legacy, "POINT_PROMPT", "Deliberately changed historical instructions")
    monkeypatch.setattr(legacy, "CONCLUSION_PROMPT", "Deliberately changed historical instructions")
    actual = {
        f"{mode}_{kind}": hashlib.sha256(function(kind).encode()).hexdigest()
        for mode, function in [
            ("generation", semantics.stage_prompt),
            ("decision", semantics.native_stage_prompt),
        ]
        for kind in ("abstention", "point", "conclusion")
    }
    actual["conclusion_only"] = hashlib.sha256(
        semantics.conclusion_only_prompt().encode()
    ).hexdigest()
    assert actual == expected


def test_selected_glm_prompt_only_adds_accepted_empty_review_clarification():
    """The maintained explicit override excludes the rejected semantic appendix."""
    selected = json.loads(Path("configs/grounding_glm_prompts_v1.json").read_text())
    base = semantics.stage_prompt("conclusion")
    assert set(selected) == {"conclusion"}
    assert selected["conclusion"].startswith(base)
    assert selected["conclusion"][len(base) :] == (
        "\n\nReview only the individual claims supplied in the claim list. "
        "When the supplied claim list is empty, return an empty point_reviews list. "
        "Do not invent a claim ID or add the conclusion itself as a claim review; "
        "assess the conclusion only in the conclusion fields."
    )
