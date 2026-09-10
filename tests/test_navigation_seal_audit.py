"""Explicit deep audits reject altered bytes and incomplete navigation closure."""

import json
from pathlib import Path

import pytest

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    file_reference,
    sha256_file,
    write_json_atomic,
)
from er_commons.navigation_overlay.seal_audit import deep_audit_navigation_root


def _seal(tmp_path: Path) -> Path:
    """Create an entire tiny historical navigation seal for byte-audit tests."""
    preimage = {"synthetic": "historical-navigation"}
    root = tmp_path / f"navlinkv1-{canonical_json_sha256(preimage)}"
    (root / "records").mkdir(parents=True)
    write_json_atomic(root / "records/identity_preimage.json", preimage)
    for name in (
        "toc_text_pages.jsonl",
        "toc_text_entries.jsonl",
        "toc_entry_reconciliations.jsonl",
        "link_overlay.jsonl",
    ):
        (root / name).write_text("{}\n")
    inventory = root / "records/artifact_inventory.json"
    write_json_atomic(inventory, artifact_inventory(root, {"records/artifact_inventory.json"}))
    completion = {
        "status": "complete",
        "link_view_id": root.name,
        "artifact_inventory_sha256": sha256_file(inventory),
        "managed_files": [
            file_reference(p, root=root) for p in sorted(root.rglob("*")) if p.is_file()
        ],
    }
    write_json_atomic(root / "records/completion_record.json", completion)
    return root


def test_deep_audit_checks_complete_inventory_and_same_size_bytes(tmp_path: Path) -> None:
    root = _seal(tmp_path)
    assert deep_audit_navigation_root(root) == sha256_file(root / "records/completion_record.json")
    (root / "toc_text_pages.jsonl").write_text("[]\n")
    with pytest.raises(ValueError, match="exact inventory differs"):
        deep_audit_navigation_root(root)


@pytest.mark.parametrize("mutation", ["extra", "missing", "omitted_completion", "symlink"])
def test_deep_audit_rejects_incomplete_managed_closure(tmp_path: Path, mutation: str) -> None:
    root = _seal(tmp_path)
    if mutation == "extra":
        (root / "unlisted.json").write_text("{}")
    elif mutation == "missing":
        (root / "toc_text_pages.jsonl").unlink()
    elif mutation == "symlink":
        (root / "linked.json").symlink_to(root / "toc_text_pages.jsonl")
    else:
        path = root / "records/completion_record.json"
        completion = json.loads(path.read_text())
        completion["managed_files"] = completion["managed_files"][1:]
        write_json_atomic(path, completion)
    with pytest.raises(ValueError, match="inventory differs|managed closure differs|symlink"):
        deep_audit_navigation_root(root)


def test_review_input_preparation_verifies_seal_before_reading_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejected seal cannot leave newly prepared review inputs behind."""
    from er_commons.navigation_overlay import relink_run_validation as validation

    root = _seal(tmp_path)
    (root / "extra.json").write_text("{}")
    output = tmp_path / "prepared"

    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("unverified navigation rows were consumed")

    monkeypatch.setattr(validation, "_navigation_inputs", unexpected)
    with pytest.raises(ValueError, match="exact inventory differs"):
        validation.prepare_reviewed_navigation_inputs(
            navigation_root=root,
            semantic_dispositions_path=tmp_path / "not-read",
            output_root=output,
            validation={},
        )
    assert not output.exists()


def test_review_input_publication_is_no_clobber(tmp_path: Path) -> None:
    """Explicit diagnostic output roots still cannot replace existing review bytes."""
    from er_commons.document_records.document_references.relinking import NavigationInputs
    from er_commons.navigation_overlay.relink_run_validation import _write_reviewed_inputs

    dispositions = tmp_path / "selected.jsonl"
    dispositions.write_text("")
    output = tmp_path / "review"
    output.mkdir()
    protected = output / "dispositions.jsonl"
    protected.write_text("protected\n")
    with pytest.raises(ValueError, match="refusing to replace"):
        _write_reviewed_inputs(
            NavigationInputs((), ()),
            semantic_dispositions_path=dispositions,
            output_root=output,
            validation={"reviewed_source_ids": []},
        )
    assert protected.read_text() == "protected\n"
    assert not (output / "text_entries.jsonl").exists()
