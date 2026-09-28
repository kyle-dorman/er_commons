"""Source access must not admit stale bytes, escaped paths, or ambiguous identities."""

import hashlib
from pathlib import Path

import pytest

from er_commons.pilot_citation_records import bound_bytes, index_records, source_path


def test_bound_source_rejects_changed_bytes(tmp_path: Path) -> None:
    """A previously bound file must be verified again when it is read."""
    path = tmp_path / "blocks.jsonl"
    original = b'{"id":"b1"}\n'
    path.write_bytes(original)
    binding = {"path": path.name, "sha256": hashlib.sha256(original).hexdigest()}
    assert bound_bytes(binding, tmp_path) == original
    path.write_bytes(b'{"id":"b2"}\n')
    with pytest.raises(ValueError, match="hash mismatch"):
        bound_bytes(binding, tmp_path)


def test_source_path_rejects_symlink_escape(tmp_path: Path) -> None:
    """A relative-looking reference cannot cross the configured artifact root."""
    root = tmp_path / "artifacts"
    root.mkdir()
    external = tmp_path / "outside.jsonl"
    external.write_text('{"id":"b1"}\n')
    (root / "blocks.jsonl").symlink_to(external)
    with pytest.raises(ValueError, match="escapes data root"):
        source_path(root, "blocks.jsonl")


def test_index_records_rejects_duplicates_instead_of_overwriting() -> None:
    """Duplicate canonical IDs cannot resolve to an arbitrary last record."""
    with pytest.raises(ValueError, match="Duplicate citation source ID: b1"):
        index_records(b'{"id":"b1","text":"first"}\n{"id":"b1","text":"last"}')
