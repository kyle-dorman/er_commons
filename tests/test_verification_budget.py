"""Invocation budget rejects prohibited access before touching payload bytes."""

from pathlib import Path

import pytest

from er_commons.artifact_verification import VerificationBudget


def test_hash_limits_roles_and_shared_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Nested readers share a cumulative limit and cannot hash payload roles."""
    path = tmp_path / "record.json"
    path.write_text("{}")
    budget = VerificationBudget(hash_total_limit=3)
    budget.hash_file(path, root=tmp_path, role="completion", source_id="x")
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("opened rejected file"))
    with pytest.raises(ValueError, match="before open"):
        budget.hash_file(path, root=tmp_path, role="completion", source_id="y")
    with pytest.raises(ValueError, match="forbidden"):
        budget.hash_file(path, root=tmp_path, role="canonical_payload", source_id="x")
    with pytest.raises(ValueError, match="before open"):
        VerificationBudget(hash_file_limit=1).hash_file(
            path, root=tmp_path, role="managed_inventory", source_id="x"
        )
    assert budget.hashed_bytes == 2


def test_read_budget_and_metadata_are_separate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Oversized hash records may be read but never called freshly byte verified."""
    path = tmp_path / "manifest.json"
    path.write_text("{}")
    budget = VerificationBudget(hash_file_limit=1, read_total_limit=3)
    assert budget.read_json(path, root=tmp_path, role="source_manifest", source_id="x") == {}
    assert budget.hashed_bytes == 0
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("opened rejected file"))
    with pytest.raises(ValueError, match="before open"):
        budget.read_json(path, root=tmp_path, role="source_manifest", source_id="x")
    budget.check_metadata(path, root=tmp_path, role="payload", source_id="x", byte_size=2)


def test_containment_and_pdf_fail_before_open(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A compact role cannot disguise a PDF or an escaping symlink."""
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    root = tmp_path / "root"
    root.mkdir()
    (root / "escape.json").symlink_to(outside)
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("opened rejected file"))
    budget = VerificationBudget()
    with pytest.raises(ValueError, match="escapes root"):
        budget.hash_file(root / "escape.json", root=root, role="completion", source_id="x")
    with pytest.raises(ValueError, match="forbidden"):
        budget.hash_file(root / "source.pdf", root=root, role="completion", source_id="x")
