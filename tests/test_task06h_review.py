"""Source-free policy and restart tests for the Task 06H replacement review."""

from __future__ import annotations

from typing import Any

import pytest

from er_commons.human_review_support.extraction_review.task06h_bindings import figure_controls
from er_commons.human_review_support.extraction_review.task06h_contract import final_f1_warnings
from er_commons.human_review_support.extraction_review.task06h_correspondence import (
    correspondence_result,
    exclusion_correspondence,
)
from er_commons.human_review_support.extraction_review.task06h_records import (
    acceptance_id,
    merge_disposition,
    validate_registry,
    validate_terminal_disposition,
)
from er_commons.human_review_support.extraction_review.task06h_selection import (
    build_selection,
)


def _review_rows() -> list[dict[str, Any]]:
    return [
        {
            "entry_id": f"tocpagev1-{index:03d}",
            "source_id": f"sample_{index:03d}",
            "classification": "unchanged",
            "baseline_evidence": {"disposition": "toc", "physical_page": 1},
        }
        for index in range(31)
    ]


def _figure_decisions() -> list[dict[str, Any]]:
    eligible = [
        {
            "eligibility": "eligible",
            "physical_page_number": 3000 + (index if index <= 170 else index - 170),
            "figure_id": f"figure-{index:03d}",
        }
        for index in range(1, 179)
    ]
    rejected = [
        {"eligibility": "rejected", "figure_id": f"reject-{index:03d}"} for index in range(96)
    ]
    return [*eligible, *rejected]


def test_selection_closure_is_exact_and_deduplicated_by_source_page() -> None:
    selected = build_selection(_review_rows(), _figure_decisions())
    assert len(selected) == 290
    assert sum(row.render_action == "render_new" for row in selected) == 289
    assert sum(row.render_action == "reuse_sealed" for row in selected) == 1
    assert len({(row.source_id, row.physical_page) for row in selected}) == 290
    assert sum(row.source_id == "feir_appendix_f1" for row in selected) == 9
    assert sum(row.source_id == "deir_appendix_a" for row in selected) == 43
    assert sum(row.source_id == "deir_main" for row in selected) == 207


def _substance(*, ids: list[str], text: str = "same") -> dict[str, Any]:
    return {
        "entity_ids": ids,
        "text": text,
        "tables": [],
        "image_attachments": [],
        "placement": {"page": 4},
        "context": {"before": "a", "after": "b"},
    }


def test_correspondence_uses_substance_not_raw_namespaced_ids() -> None:
    assert (
        correspondence_result(
            classification="unchanged",
            source_change_class="preserved_semantic",
            mapping_cardinality="one_to_one",
            old_evidence=_substance(ids=["old/section/1"]),
            new_evidence=_substance(ids=["new/section/1"]),
            policy_compatible=True,
        )
        == "reused_remapped_equivalent"
    )
    assert (
        correspondence_result(
            classification="unchanged",
            source_change_class="preserved_semantic",
            mapping_cardinality="one_to_one",
            old_evidence=_substance(ids=["same"], text="old"),
            new_evidence=_substance(ids=["same"], text="changed"),
            policy_compatible=True,
        )
        == "new_review_required"
    )


@pytest.mark.parametrize(
    ("classification", "change", "cardinality", "policy", "expected"),
    [
        ("unproven", "repaired_structure", "one_to_one", True, "new_review_required"),
        ("unchanged", "substituted_new_source", "one_to_one", True, "new_review_required"),
        ("unchanged", "preserved_semantic", "many_to_one", True, "rejected_ambiguous"),
        ("unchanged", "preserved_semantic", "dangling", True, "rejected_ambiguous"),
        ("unchanged", "preserved_semantic", "one_to_one", False, "new_review_required"),
    ],
)
def test_correspondence_fails_closed(
    classification: str, change: str, cardinality: str, policy: bool, expected: str
) -> None:
    assert (
        correspondence_result(
            classification=classification,
            source_change_class=change,
            mapping_cardinality=cardinality,
            old_evidence=_substance(ids=["old"]),
            new_evidence=_substance(ids=["new"]),
            policy_compatible=policy,
        )
        == expected
    )


def test_exclusion_correspondence_never_promotes_links() -> None:
    exclusions = [
        {
            "reference_id": f"old/cross-reference/source/xref{index:06d}",
            "source_id": "source",
            "machine_evidence": {"candidate_target_ids": ["old/page/source/p000004"]},
        }
        for index in range(725)
    ]
    comparisons = [
        {
            "mention_key": f"cross-reference/source/xref{index:06d}",
            "classification": "unchanged",
            "baseline": {"candidates": [{"target_record_id": "page/source/p000004"}]},
            "replacement": {"candidates": [{"target_record_id": "page/source/p000004"}]},
        }
        for index in range(725)
    ]
    rows = exclusion_correspondence(exclusions, comparisons)
    assert {row["result"] for row in rows} == {"excluded_rebound"}
    assert all(row["link_promoted"] is False for row in rows)


def _disposition() -> dict[str, Any]:
    return {
        "mechanical_readiness": "ready_for_review",
        "exact_target_identity": "confirmed",
        "human_usability": "usable",
        "visual_evidence_quality": "legible",
        "text_only_model_eligibility": "unavailable_to_text_only_model",
        "overall_review": "accepted",
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-13T00:00:00Z",
        "question_version": "v1",
        "source_id": "source",
        "document_id": "document",
        "stable_correspondence_key": "key",
        "evidence_refs": ["evidence"],
        "rationale": "visual identity does not imply text-only eligibility",
        "limitations": [],
    }


def test_dimensions_are_independent_and_conflicts_fail() -> None:
    row = _disposition()
    validate_terminal_disposition(row)
    journal = merge_disposition({}, row)
    assert merge_disposition(journal, row) == journal
    changed = {**row, "human_usability": "unusable"}
    with pytest.raises(ValueError, match="conflicting"):
        merge_disposition(journal, changed)
    for field in ("reviewer", "exact_target_identity"):
        incomplete = dict(row)
        del incomplete[field]
        with pytest.raises(ValueError, match="incomplete"):
            validate_terminal_disposition(incomplete)


def test_final_f1_warning_scope_and_figure_controls_are_frozen() -> None:
    limits = final_f1_warnings()
    assert limits["mention_count"] == 66
    assert len(limits["response_specific"]) == 2
    assert sum(len(row["mention_ids"]) for row in limits["response_specific"]) == 3
    assert limits["other_mentions_not_proven_draft_final_equivalent"] == 64
    mapped = tuple(
        {"physical_page_number": 3000 + (index if index <= 170 else index - 170)}
        for index in range(1, 179)
    )
    controls = figure_controls({"decisions": _figure_decisions()}, mapped)
    assert controls["eligible_target_count"] == 178
    assert controls["eligible_page_count"] == 170
    assert controls["rejected_negative_control_count"] == 96
    assert len(controls["negative_controls"]) == 96
    assert controls["figure_4_8_exact_target_count"] == 0
    assert controls["marker_truncation_allowed"] is False
    assert controls["text_only_status"] == "pending_independent_human_disposition"


def test_registry_and_acceptance_bindings_fail_closed() -> None:
    sources = [{"source_id": f"s{index}"} for index in range(35)]
    targets = [{"target_id": f"t{index}"} for index in range(185)]
    exclusions = [
        {
            "historical_reference_id": f"x{index}",
            "result": "excluded_rebound",
            "link_promoted": False,
        }
        for index in range(725)
    ]
    recheck = {
        "source_id": "deir_appendix_k2_part_5_of_5",
        "physical_pages": list(range(974, 984)),
    }
    validate_registry(
        source_rows=sources,
        expected_source_ids={row["source_id"] for row in sources},
        target_rows=targets,
        expected_target_ids={row["target_id"] for row in targets},
        exclusions=exclusions,
        task03i=recheck,
    )
    bindings = {
        "mechanical_handoff_id": "handoff",
        "readiness_sha256": "a" * 64,
        "review_completion_sha256": "b" * 64,
        "correspondence_completion_sha256": "c" * 64,
        "registry_id": "registry",
        "source_substitution": "final_f1",
        "limitations_sha256": "d" * 64,
        "task05g_handoff_sha256": "e" * 64,
        "mechanical_status": "ready_for_review",
        "human_review_status": "accepted_with_limitation",
    }
    accepted = acceptance_id(bindings)
    assert acceptance_id(dict(bindings)) == accepted
    assert acceptance_id({**bindings, "limitations_sha256": "f" * 64}) != accepted
    with pytest.raises(ValueError, match="human gate"):
        acceptance_id({**bindings, "human_review_status": "incomplete"})
