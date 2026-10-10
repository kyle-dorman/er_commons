"""Qualification of scoped intake without external documents or model execution."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.group_answer_intake import (
    _original_scope,
    file_binding,
    normalize_case,
    read_bound,
)


def _fixture(tmp_path: Path) -> dict[str, Any]:
    """Build one source and a hidden source under a synthetic overlay."""

    def source(identity: str) -> dict[str, Any]:
        """Return a compact synthetic canonical-source snapshot."""
        return {
            "occurrence_id": identity,
            "candidate_id": identity + "-candidate",
            "extraction_id": "ex1",
            "source_id": "doc",
            "edition": "draft",
            "quote": "Complete source text.",
            "physical_pages": [1],
            "anchors": [],
            "citation_unit": {"kind": "section", "section_id": "sec1"},
        }

    packet = {
        "sources": [source("C001-S001"), source("C001-S999")],
        "claim_findings": [],
        "beyond_claim_findings": [],
        "frozen_input": {},
    }
    base = tmp_path / "base.json"
    base.write_text(json.dumps({"state": {"packet": packet}}))
    side = tmp_path / "scope.json"
    side.write_text("{}")
    return {
        "case_id": "C001",
        "question": "Exact amended question?",
        "base_review": file_binding(base),
        "review_mode": "approved_display_scope_overlay",
        "approval_scope_binding": file_binding(side),
        "approved_proposal_binding": file_binding(side),
        "revised_checkpoint": file_binding(base),
        "approval_scope": {},
        "citation_roles": {"required": ["C001-S001"], "preserved_background": ["C001-S999"]},
        "approved_occurrence_sources": packet["sources"],
        "exact_approved_display": "Earlier displayed question and framing.",
        "exact_display_amendments": {"question": "Exact amended question?"},
        "eligibility": {"eligible": True},
    }


def test_hash_change_fails_closed(tmp_path: Path) -> None:
    """Historical tampering must fail before source normalization."""
    path = tmp_path / "record.json"
    path.write_text("{}")
    ref = file_binding(path)
    path.write_text('{"changed": true}')
    with pytest.raises(ValueError, match="Changed upstream"):
        read_bound(ref)


def test_overlay_excludes_hidden_background_and_keeps_amendment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Source availability cannot promote a background occurrence to answer evidence."""
    monkeypatch.setattr("er_commons.group_answer_intake.validate_units", lambda *_: None)
    result = normalize_case(_fixture(tmp_path), tmp_path)
    assert [source["occurrence_id"] for source in result["citations"]] == ["C001-S001"]
    assert result["question"] == result["exact_display_amendments"]["question"]
    assert result["answer_approval"] is result["final_disposition"] is None
    assert result["citations"][0]["canonical_target"]["unit_id"] == "sec1"


def test_cross_case_source_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Even a present occurrence cannot cross the case boundary."""
    monkeypatch.setattr("er_commons.group_answer_intake.validate_units", lambda *_: None)
    case = _fixture(tmp_path)
    case["citation_roles"] = {"required": ["C002-S001"]}
    with pytest.raises(ValueError, match="Cross-case"):
        normalize_case(case, tmp_path)


def test_later_rejection_overrides_relationship_scope() -> None:
    """A broad saved scope cannot revive a subsequently rejected finding."""
    rows = [
        {"finding_id": "F1", "occurrence_id": "C001-S001", "metric_role": "required"},
        {"finding_id": "F2", "occurrence_id": "C001-S002", "metric_role": "required"},
    ]
    checkpoint = {
        "state": {
            "decisions": {
                "F1": {"decision": "accept", "decision_scope": {"accepted_relationships": rows}},
                "F2": {"decision": "reject"},
            }
        },
        "journal": {"events": [{"kind": "display", "chat_text": "Approved framing."}]},
    }
    selected, _, _ = _original_scope({"case_id": "C001"}, checkpoint)
    assert [row["finding_id"] for row in selected] == ["F1"]


def test_no_implicit_acceptance_from_finding() -> None:
    """Accepted findings lacking explicit citation scope must not unlock all links."""
    checkpoint = {
        "state": {"decisions": {"F1": {"decision": "accept"}}},
        "journal": {"events": [{"kind": "display", "chat_text": "Framing."}]},
    }
    with pytest.raises(ValueError, match="Missing explicit"):
        _original_scope({"case_id": "C001"}, checkpoint)


def test_table_grid_and_notes_survive_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One grid per table retains row/column meaning without per-cell duplication."""
    monkeypatch.setattr("er_commons.group_answer_intake.validate_units", lambda *_: None)
    case = _fixture(tmp_path)
    table = {
        "id": "ex/table/doc/t1",
        "shape": {"rows": 1, "columns": 2},
        "cells": [
            {"row_index": 0, "column_index": 0, "text": "Label"},
            {"row_index": 0, "column_index": 1, "text": "42"},
        ],
    }
    source = case["approved_occurrence_sources"][0]
    source["anchors"] = [
        {"record_id": table["id"], "record": table, "quote": "Label"},
        {"record_id": table["id"], "record": table, "quote": "42"},
    ]
    source["quote"] = "Label\n\n42\n\nNote: modeled value."
    result = normalize_case(case, tmp_path)
    citation = result["citations"][0]
    assert citation["tables"] == [table]
    assert "Note: modeled value." in citation["full_source_text"]


def test_c002_acceptance_does_not_unlock_undisplayed_extra() -> None:
    """C002's accepted A005 cannot promote its undisplayed extra S011 citation."""
    checkpoint = {
        "state": {
            "decisions": {"C002-A005": {"decision": "accept", "decision_scope": "Displayed only"}},
            "packet": {
                "claim_findings": [
                    {
                        "finding_id": "C002-A005",
                        "citations": [
                            {"occurrence_id": "C002-S010"},
                            {"occurrence_id": "C002-S011"},
                        ],
                    }
                ],
                "beyond_claim_findings": [],
            },
        },
        "journal": {"events": [{"kind": "display", "chat_text": "Displayed S010 only."}]},
    }
    relationships, _, _ = _original_scope({"case_id": "C002"}, checkpoint)
    assert [row["occurrence_id"] for row in relationships] == ["C002-S010"]
