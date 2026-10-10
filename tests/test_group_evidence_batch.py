"""Reject incomplete or changed upstream closure before batch research."""

from pathlib import Path

import pytest

from er_commons.group_claims_batch import reference, write_new
from er_commons.group_evidence_batch import _verify_bindings, _verify_preparation


def test_nested_binding_rejects_changed_bytes(tmp_path: Path) -> None:
    """A nested supplemental reference cannot survive mutation."""
    path = tmp_path / "record.json"
    write_new(path, {"context": "original"})
    binding = {"required": [{"source": reference(path)}]}
    _verify_bindings(binding)
    path.write_text("changed")
    with pytest.raises(ValueError, match="binding changed"):
        _verify_bindings(binding)


def test_nested_binding_rejects_wrong_size(tmp_path: Path) -> None:
    """The inventory size remains part of closure even when its hash is correct."""
    path = tmp_path / "record.json"
    write_new(path, {})
    with pytest.raises(ValueError, match="byte size"):
        _verify_bindings({**reference(path), "bytes": 0})


def test_preparation_verifies_manifest_members_and_queue(tmp_path: Path) -> None:
    """A valid manifest seal cannot mask changed members or a substituted queue."""
    queue = tmp_path / "queue.json"
    member = tmp_path / "context.json"
    manifest = tmp_path / "manifest.json"
    write_new(queue, {"cases": []})
    write_new(member, {"context": "frozen"})
    write_new(manifest, {"files": [reference(member)]})
    preparation = {"queue": reference(queue), "manifest": reference(manifest)}
    _verify_preparation(preparation, reference(queue))
    with pytest.raises(ValueError, match="queue bindings differ"):
        _verify_preparation(preparation, reference(member))
    member.write_text("changed")
    with pytest.raises(ValueError, match="binding changed"):
        _verify_preparation(preparation, reference(queue))
