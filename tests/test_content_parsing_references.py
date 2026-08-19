"""Human-owned tests for closed conversion references and document views."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from er_commons.document_parsing.content_parsing import references
from er_commons.document_parsing.content_parsing.evidence import CompletedRunInvariantError
from er_commons.document_parsing.content_parsing.references import (
    ConversionInputReference,
    ResolvedConversionInput,
    load_document_views,
)


def _resolved(root: Path, view: str) -> ResolvedConversionInput:
    prefix = "documents/source/producer/docling"
    files = []
    for relative in (f"{prefix}/document.json", f"{prefix}/heading_overlay.jsonl"):
        path = root / relative
        files.append({"path": relative, "byte_size": path.stat().st_size, "sha256": "a" * 64})
    return ResolvedConversionInput(
        reference=ConversionInputReference.model_validate(
            {
                "schema_version": "er_commons.conversion_input_reference.v1",
                "conversion_id": "dconv1-" + "a" * 64,
                "path": root.as_posix(),
                "completion_path": (root / "records/completion_record.json").as_posix(),
                "inventory_path": (root / "records/artifact_inventory.json").as_posix(),
                "completion_sha256": "b" * 64,
                "inventory_sha256": "c" * 64,
                "document_view": view,
            }
        ),
        root=root,
        inventory={"files": files},
    )


def test_common_document_views_load_base_once_and_detach_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prefix = tmp_path / "documents/source/producer/docling"
    prefix.mkdir(parents=True)
    document_path = prefix / "document.json"
    document_path.write_text(json.dumps({"texts": [{"self_ref": "#/texts/0", "level": 1}]}))
    (prefix / "heading_overlay.jsonl").write_text(
        json.dumps(
            {
                "schema_version": "er_commons.heading_level_overlay.v1",
                "raw_self_ref": "#/texts/0",
                "level": 3,
            }
        )
        + "\n"
    )
    reads: list[Path] = []
    original = references.read_json_object

    def observe(path: Path) -> dict[str, object]:
        reads.append(path)
        return original(path)

    monkeypatch.setattr(references, "read_json_object", observe)
    base, heading = load_document_views(
        _resolved(tmp_path, "base"), _resolved(tmp_path, "heading"), source_id="source"
    )

    assert reads.count(document_path) == 1
    assert base["texts"][0]["level"] == 1
    assert heading["texts"][0]["level"] == 3
    assert base is not heading


def test_document_views_reject_different_conversion_owners(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    for root in (first_root, second_root):
        prefix = root / "documents/source/producer/docling"
        prefix.mkdir(parents=True)
        (prefix / "document.json").write_text("{}")
        (prefix / "heading_overlay.jsonl").write_text("")

    with pytest.raises(CompletedRunInvariantError, match="one sealed conversion owner"):
        load_document_views(
            _resolved(first_root, "base"),
            _resolved(second_root, "heading"),
            source_id="source",
        )
