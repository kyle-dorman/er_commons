"""Saved replay rejects mismatched provenance before any production invocation."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.response_inventory import saved_evidence


def test_saved_replay_rejects_unaccepted_candidate(monkeypatch, tmp_path: Path) -> None:
    """An adjacent acceptance must bind the exact validated completion."""
    monkeypatch.setattr(
        saved_evidence, "validate_task05d_candidate", lambda *_: {"completion_id": "new"}
    )
    monkeypatch.setattr(saved_evidence, "read_json_object", lambda *_: {"completion_id": "old"})
    with pytest.raises(ValueError, match="acceptance differs"):
        saved_evidence.replay_saved_source(
            tmp_path / "spec",
            tmp_path,
            tmp_path,
            saved_candidate=tmp_path / "candidate",
            saved_cache=tmp_path / "cache",
        )


def test_saved_replay_rejects_non_source_run(monkeypatch, tmp_path: Path) -> None:
    """A non-source specification cannot reach page reading or qualification."""
    monkeypatch.setattr(
        saved_evidence, "validate_task05d_candidate", lambda *_: {"completion_id": "same"}
    )
    monkeypatch.setattr(saved_evidence, "read_json_object", lambda *_: {"completion_id": "same"})
    monkeypatch.setattr(saved_evidence, "read_jsonl", lambda *_: [{"record_type": "activity"}])
    monkeypatch.setattr(
        saved_evidence, "load_response_inventory_run_spec", lambda *_: (SimpleNamespace(), "digest")
    )
    with pytest.raises(ValueError, match="Task 05D"):
        saved_evidence.replay_saved_source(
            tmp_path / "spec",
            tmp_path,
            tmp_path,
            saved_candidate=tmp_path / "candidate",
            saved_cache=tmp_path / "cache",
        )


def test_replacement_acceptance_keeps_identity_and_path_consistency() -> None:
    """New accepted identities are allowed, but mismatched stage evidence is not."""
    from er_commons.response_inventory.run_spec import AcceptedTask05D

    revision = "revisionv1-" + "a" * 64
    value = {
        "candidate_root": "working/05d/" + revision,
        "acceptance_path": "working/05d/" + revision + ".acceptance.json",
        "revision_id": revision,
        "activity_id": "activityv1-" + "a" * 64,
        "acceptance_id": "acceptancev1-" + "b" * 64,
        "completion_id": "completionv1-" + "c" * 64,
        "inventory_id": "fileinventoryv1-" + "d" * 64,
        "semantic_digest": "e" * 64,
    }
    assert AcceptedTask05D.model_validate(value).revision_id == revision
    with pytest.raises(ValueError, match="activity identities differ"):
        AcceptedTask05D.model_validate({**value, "activity_id": "activityv1-" + "f" * 64})
