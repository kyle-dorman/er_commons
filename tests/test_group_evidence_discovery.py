"""Saved query plans must precede retrieval and survive interruption safely."""

import json
from pathlib import Path

import pytest

from er_commons import group_evidence_discovery as discovery


def test_query_resume_budget_and_changed_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One execution is reused exactly; changed intent and overspend fail closed."""
    case = tmp_path / "case"
    case.mkdir()
    plan = {"tracks": {"direct_claims": {"queries": 1, "follow_up_queries": 1}}}
    (case / "plan.json").write_text(json.dumps(plan))
    calls = []

    def fake_search(index: Path, **query: object) -> dict:
        """Assert intent exists before simulated retrieval starts."""
        assert list((case / "queries/direct_claims").glob("*.plan.json"))
        calls.append(query)
        return {"status": "completed", "hits": [], **query}

    monkeypatch.setattr(discovery, "search", fake_search)
    query = {"query_id": "q1", "expression": "test"}
    first = discovery.run_query(case, tmp_path / "index", "direct_claims", query)
    assert discovery.run_query(case, tmp_path / "index", "direct_claims", query) == first
    assert len(calls) == 1
    with pytest.raises(ValueError, match="overwrite"):
        discovery.run_query(
            case, tmp_path / "index", "direct_claims", {**query, "expression": "changed"}
        )
    discovery.run_query(case, tmp_path / "index", "direct_claims", {**query, "query_id": "q2"})
    with pytest.raises(ValueError, match="budget"):
        discovery.run_query(case, tmp_path / "index", "direct_claims", {**query, "query_id": "q3"})


def test_requires_saved_plan(tmp_path: Path) -> None:
    """No search can occur without a durable per-case effort plan."""
    with pytest.raises(ValueError, match="Save the case plan"):
        discovery.run_query(tmp_path, tmp_path / "index", "direct_claims", {"query_id": "q"})


def test_invalid_filter_rejected_before_intent(tmp_path: Path) -> None:
    """Reject a list filter before creating an intent that cannot yield a receipt."""
    (tmp_path / "plan.json").write_text(json.dumps({"tracks": {"direct_claims": {}}}))
    with pytest.raises(ValueError, match="source_filter"):
        discovery.run_query(
            tmp_path,
            tmp_path / "index",
            "direct_claims",
            {"query_id": "q", "source_filter": ["source"]},
        )
    assert not (tmp_path / "queries").exists()


def test_native_labels_are_not_guessed() -> None:
    """Unique source furniture labels pass; conflicting or absent labels remain unknown."""
    assert (
        discovery.native_printed_label("Body\nBaylands Specific Plan\n4.9-65\nApril 2025")
        == "4.9-65"
    )
    assert discovery.native_printed_label("Table 4.9-2\n4.9-65\nApril 2025") is None
    assert discovery.native_printed_label("No label here\nApril 2025") is None
