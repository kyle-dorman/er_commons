"""Focused source-free tests for the frozen Task 06H contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.human_review_support.extraction_review.task06h_contract import (
    PAGE28_SHA256,
    SEALS,
    _validate_page28_records,
    exact_questions,
    final_f1_warnings,
    task05g_handoff,
    verify_accepted_input_closure,
)


def test_seals_cover_every_frozen_input_family() -> None:
    names = {seal.name for seal in SEALS}
    assert len(SEALS) == 39
    assert len(names) == len(SEALS)
    assert {
        "readiness",
        "handoff_completion",
        "review_correspondence",
        "source_correspondence",
        "target_correspondence",
        "comparison_completion",
        "06d_completion",
        "06d_qualification",
        "06d_decisions",
        "06e_completion",
        "06e_qualification",
        "06e_decisions",
        "06f_completion",
        "06f_qualification",
        "06f_aliases",
        "06f_targets",
        "task04_gate_d_completion",
        "task04_registry",
        "task04_exclusions",
        "task04_task03i",
        "task04_risk",
        "task04_freeze",
        "task02_manifest",
        "task02_completion",
        "final_f1_manifest",
        "final_f1_completion",
        "page28_inventory",
        "page28_review",
    } <= names
    assert all(len(seal.sha256) == 64 for seal in SEALS)


def test_page28_validation_uses_recorded_digest_only() -> None:
    inventory = {"files": [{"name": "page-028.png", "sha256": PAGE28_SHA256}]}
    review = {"physical_page": 28, "render_sha256": PAGE28_SHA256}
    _validate_page28_records(inventory, review)
    review["physical_page"] = 29
    with pytest.raises(ValueError, match="review reference"):
        _validate_page28_records(inventory, review)


def test_closure_fails_before_reads_when_a_root_is_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing Task 06H accepted roots"):
        verify_accepted_input_closure({"candidate": tmp_path})


def test_closure_detects_metadata_digest_drift(tmp_path: Path) -> None:
    roots = {name: tmp_path / name for name in {seal.root for seal in SEALS}}
    for root in roots.values():
        root.mkdir()
    candidate_completion = roots["candidate"] / "completion.json"
    candidate_completion.write_text(json.dumps({}), encoding="utf-8")
    first = next(seal for seal in SEALS if seal.verification == "hash")
    path = roots[first.root] / first.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("drift", encoding="utf-8")
    with pytest.raises(ValueError, match=first.name):
        verify_accepted_input_closure(roots)


def test_exact_questions_keep_figures_and_text_only_support_independent() -> None:
    questions = exact_questions()
    assert set(questions) == {
        "final_f1",
        "appendix_a_each_group",
        "chapters_8_9_each",
        "fresh_navigation",
        "sampled_reuse",
        "caption_backed_figure",
    }
    assert len(questions["caption_backed_figure"]) == 3
    assert "caption/text alone" in questions["caption_backed_figure"][2]
    assert "Draft/Final equivalence" in questions["final_f1"][3]


def test_final_f1_warning_bindings_do_not_turn_three_ids_into_three_locations() -> None:
    warnings = final_f1_warnings()
    locations = warnings["response_specific"]
    assert warnings["mention_count"] == 66
    assert warnings["named_response_location_count"] == 2
    assert warnings["named_mention_id_count"] == 3
    assert warnings["other_mentions_not_proven_draft_final_equivalent"] == 64
    assert {row["material"] for row in locations} == {
        "Muni section revision",
        "Table 6 revision",
    }
    assert sum(len(row["mention_ids"]) for row in locations) == 3
    assert warnings["caption_alias_implies_text_only_support"] is False


def test_task05g_handoff_is_complete_but_not_authorized() -> None:
    handoff = task05g_handoff()
    assert handoff["outcomes"] == {"total": 511, "links": 295, "explicit_nonlinks": 216}
    assert sum((509, 2)) == handoff["outcomes"]["total"]
    assert handoff["only_source_free_invalidated_resolver_descendants"] is True
    assert handoff["specific_target_downgrade_allowed"] is False
    assert handoff["image_dependent_figure_is_text_only_evidence"] is False
    assert handoff["execution_authorized"] is False
