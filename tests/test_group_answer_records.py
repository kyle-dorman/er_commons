"""Source-free qualification of Task 08F structured answer boundaries."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from er_commons.group_answer_records import (
    render_answer,
    validate_answer,
    validate_blocked,
)


def fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """Invent one isolated case with required and optional-context source roles."""
    citation = {
        "occurrence_id": "C001-S001",
        "role": "required",
        "canonical_target": {
            "document_id": "invented-document",
            "edition": "Invented edition",
            "unit_id": "section-1",
            "unit_type": "section",
            "label": "Section 1",
            "pages": [2],
        },
        "source_label": "Invented source",
        "excerpt": "The limit is five units, under the stated conditions.",
        "full_source_ref": {"path": "/invented/complete.txt", "sha256": "synthetic"},
    }
    citations = [citation]
    for cid, role in (("C001-S002", "required"), ("C001-S003", "optional_context")):
        other = deepcopy(citation)
        other.update(occurrence_id=cid, role=role)
        citations.append(other)
    case_input = {"case_id": "C001", "question": "What is the limit?", "citations": citations}
    answer = {
        "case_id": "C001",
        "question": case_input["question"],
        "conclusion": {
            "point_id": "conclusion",
            "text": "The limit is five units.",
            "citation_ids": ["C001-S001", "C001-S002"],
        },
        "supporting_points": [
            {
                "point_id": "support1",
                "text": "The document states this limit.",
                "citation_ids": ["C001-S001"],
            }
        ],
        "qualifications": [
            {
                "point_id": "qualification1",
                "text": "The stated conditions apply.",
                "citation_ids": ["C001-S002"],
                "applies_to": ["conclusion", "support1"],
            }
        ],
        "optional_context": [
            {
                "point_id": "context1",
                "text": "Additional context is available.",
                "citation_ids": ["C001-S003"],
            }
        ],
        "citation_locators": [
            {"occurrence_id": cid, "excerpt": "The limit is five units"}
            for cid in ("C001-S001", "C001-S002", "C001-S003")
        ],
        "review_notes": ["Synthetic model note; no semantic verification."],
        "substantive_changes": [],
    }
    return case_input, answer


def test_multicitation_qualifications_and_context_render() -> None:
    """A valid proposal keeps multiple citations and attached limits without approval."""
    case_input, answer = fixture()
    result = validate_answer(answer, case_input)
    assert result["valid"]
    assert result["check_type"] == "mechanical"
    assert result["semantic_support_verified"] is False
    assert result["human_approval"] is False
    display = render_answer(answer, case_input)
    assert "five units. [^1] [^2]" in display
    assert display.count("**Qualification:**") == 2
    assert "## Optional context" in display
    assert "Excerpt: The limit is five units" in display
    assert "[Complete source](/invented/complete.txt)" in display
    assert "approval: blank" in display


@pytest.mark.parametrize(
    "field,value",
    [
        ("question", "Silently rewritten question"),
        ("case_id", "C002"),
        ("approval", True),
        ("final_disposition", "approved"),
        ("prose_answer", "duplicate"),
    ],
)
def test_wrong_binding_and_extra_outputs_rejected(field: str, value: Any) -> None:
    """Case drift, invented approvals and a second answer cannot enter preparation."""
    case_input, answer = fixture()
    answer[field] = value
    assert not validate_answer(answer, case_input)["valid"]


@pytest.mark.parametrize("change", ["uncited", "unknown", "duplicate", "context", "target"])
def test_point_failures_rejected(change: str) -> None:
    """Fail closed on malformed points, invented sources and context promotion."""
    case_input, answer = fixture()
    if change == "uncited":
        answer["conclusion"]["citation_ids"] = []
    elif change == "unknown":
        answer["conclusion"]["citation_ids"] = ["C002-S001"]
    elif change == "duplicate":
        answer["supporting_points"][0]["point_id"] = "conclusion"
    elif change == "context":
        answer["conclusion"]["citation_ids"] = ["C001-S003"]
    else:
        answer["qualifications"][0]["applies_to"] = ["context1"]
    assert not validate_answer(answer, case_input)["valid"]
    with pytest.raises(ValueError, match="invalid answer"):
        render_answer(answer, case_input)


@pytest.mark.parametrize("field", ["excerpt", "full_source_ref", "canonical_target"])
def test_missing_source_locator_rejected(field: str) -> None:
    """An occurrence ID alone does not establish an inspectable canonical citation."""
    case_input, answer = fixture()
    del case_input["citations"][0][field]
    assert not validate_answer(answer, case_input)["valid"]


def test_optional_context_can_be_empty_and_notes_are_separate() -> None:
    """Optional background is not mandatory answer content or semantic validation."""
    case_input, answer = fixture()
    answer["optional_context"] = []
    answer["citation_locators"].pop()
    assert validate_answer(answer, case_input)["valid"]
    display = render_answer(answer, case_input)
    assert "## Optional context" not in display
    assert "## Advisory preparation notes" in display


def test_blocked_record_is_not_an_answer_or_human_disposition() -> None:
    """A specific obstacle can account for a case while its answer remains unapproved."""
    case_input, _ = fixture()
    blocked = {
        "case_id": "C001",
        "question": case_input["question"],
        "blocked_reason": "The supplied sources omit the necessary threshold.",
        "review_notes": [],
    }
    assert validate_blocked(blocked, case_input)["valid"]
    assert not validate_answer(blocked, case_input)["valid"]
    blocked["final_disposition"] = "stop"
    assert not validate_blocked(blocked, case_input)["valid"]


@pytest.mark.parametrize(
    "status,has_answer,has_reason,valid",
    [
        ("proposed", True, False, True),
        ("blocked", False, True, True),
        ("proposed", True, True, False),
        ("proposed", False, False, False),
        ("blocked", True, True, False),
        ("blocked", False, False, False),
    ],
)
def test_preparation_discriminator(
    status: str, has_answer: bool, has_reason: bool, valid: bool
) -> None:
    """Only exactly one proposal or obstacle can be retained as a valid outcome."""
    from er_commons.group_answer_records import validate_preparation

    case_input, answer = fixture()
    output = {
        "status": status,
        "answer": answer if has_answer else None,
        "blocked_reason": "Missing necessary source premise." if has_reason else None,
    }
    assert validate_preparation(output, case_input)["valid"] is valid


@pytest.mark.parametrize("change", ["invented", "missing", "unknown"])
def test_model_locator_must_match_used_source_text(change: str) -> None:
    """Short excerpts locate actual source text without inventing supporting words."""
    case_input, answer = fixture()
    if change == "invented":
        answer["citation_locators"][0]["excerpt"] = "An invented source assertion."
    elif change == "missing":
        answer["citation_locators"].pop(0)
    else:
        answer["citation_locators"][0]["occurrence_id"] = "C002-S001"
    assert not validate_answer(answer, case_input)["valid"]


def test_multiple_locators_and_complete_source_link() -> None:
    """One citation may locate multiple relevant passages within its canonical unit."""
    case_input, answer = fixture()
    answer["citation_locators"].append(
        {"occurrence_id": "C001-S001", "excerpt": "under the stated conditions."}
    )
    case_input["citations"][0]["full_source_ref"] = {
        "binding": {"path": "/invented/upstream.json", "sha256": "synthetic"}
    }
    case_input["citations"][0]["pdf_url"] = "https://example.org/source.pdf#page=2"
    assert validate_answer(answer, case_input)["valid"]
    display = render_answer(answer, case_input)
    assert "Excerpt: under the stated conditions." in display
    assert "[Complete source](/invented/upstream.json)" in display
    assert "[Source PDF, cited page](https://example.org/source.pdf#page=2)" in display


def test_transport_omits_unique_items_but_local_validation_enforces_it() -> None:
    """Provider schema limits do not weaken the local citation uniqueness rule."""
    import json

    from er_commons.group_answer_records import preparation_output_schema, validate_preparation

    assert "uniqueItems" not in json.dumps(preparation_output_schema())
    case_input, answer = fixture()
    answer["conclusion"]["citation_ids"] = ["C001-S001", "C001-S001"]
    output = {"status": "proposed", "answer": answer, "blocked_reason": None}
    assert not validate_preparation(output, case_input)["valid"]


@pytest.mark.parametrize(
    "source_id,label",
    [
        ("deir_main", "DEIR main report"),
        ("deir_appendix_a", "DEIR Appendix A"),
        ("deir_appendix_g2", "DEIR Appendix G.2"),
        ("deir_appendix_k1_part_1_of_4", "DEIR Appendix K.1 part 1 of 4"),
        ("feir_appendix_f1", "Final EIR Appendix F.1"),
    ],
)
def test_missing_document_title_uses_readable_source_identity(source_id: str, label: str) -> None:
    """A missing descriptive title must not hide the cited document identity."""
    case_input, answer = fixture()
    source = case_input["citations"][0]
    del source["source_label"]
    source["source_id"] = source_id
    assert f"[^1]: {label};" in render_answer(answer, case_input)
    source["document_title"] = "Supplied document title"
    assert "[^1]: Supplied document title;" in render_answer(answer, case_input)
    source["source_label"] = "Supplied source label"
    assert "[^1]: Supplied source label;" in render_answer(answer, case_input)
