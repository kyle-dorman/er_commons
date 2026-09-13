"""Adversarial source-free tests for the frozen v33 retained selection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_collection_imported_selection import _fixture, _json_bytes

from er_commons.collection_processing.selection_generation import (
    generate_imported_selection,
    write_imported_selection,
)


def _retained_spec(tmp_path: Path, fixture: dict[str, object]) -> Path:
    order = fixture["order"]
    assert isinstance(order, tuple)
    path = tmp_path / "retained_collection.json"
    path.write_bytes(
        _json_bytes(
            {
                "source_membership": [
                    {"logical_source_id": source, "physical_source_id": source} for source in order
                ]
            }
        )
    )
    return path


def _generate(tmp_path: Path, fixture: dict[str, object]) -> bytes:
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    return generate_imported_selection(
        data_root=tmp_path,
        document_input_root=document_root,
        retained_collection_spec=_retained_spec(tmp_path, fixture),
    )


def test_exact_35_rows_ignore_three_ordinary_candidates_and_pin_downstream(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path, count=35)
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    for ordinal in range(1, 4):
        ordinary = (
            document_root
            / "document_publications/documents"
            / f"source_{ordinal}"
            / f"docv1-{ordinal + 500:064x}"
            / "records"
        )
        ordinary.mkdir(parents=True)
        (ordinary / "completion_record.json").write_bytes(_json_bytes({"ordinary": True}))

    first = _generate(tmp_path, fixture)
    second = _generate(tmp_path, fixture)
    selection = json.loads(first)

    assert first == second
    assert selection["source_count"] == 35
    assert len(selection["candidates"]) == 35
    assert [row["physical_source_id"] for row in selection["candidates"]] == list(fixture["order"])
    assert all("downstream_replay_ref" in row for row in selection["candidates"])
    assert all(
        row["linked_completion_ref"]["authority"] == "document_input_root"
        and row["linked_completion_ref"]["byte_size"] > 0
        for row in selection["candidates"]
    )


@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_rejects_missing_or_duplicate_downstream_candidate(tmp_path: Path, mutation: str) -> None:
    fixture = _fixture(tmp_path, count=35)
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    source = document_root / "document_publications/documents/source_1"
    downstream = next(source.glob("docv1-*/records/downstream_replay.json"))
    if mutation == "missing":
        downstream.unlink()
    else:
        duplicate = source / ("docv1-" + "f" * 64) / "records/downstream_replay.json"
        duplicate.parent.mkdir(parents=True)
        duplicate.write_bytes(downstream.read_bytes())

    with pytest.raises(ValueError, match="expected one retained downstream candidate"):
        _generate(tmp_path, fixture)


def test_rejects_stale_downstream_linked_completion_binding(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, count=35)
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    downstream = next(
        (document_root / "document_publications/documents/source_1").glob(
            "docv1-*/records/downstream_replay.json"
        )
    )
    value = json.loads(downstream.read_bytes())
    value["replacement_linked_document_completion_ref"]["sha256"] = "f" * 64
    downstream.write_bytes(_json_bytes(value))

    with pytest.raises(ValueError, match="linked completion binding is stale"):
        _generate(tmp_path, fixture)


def test_generation_never_reads_prohibited_payloads_or_legacy_extractors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path, count=35)
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    for suffix in (".pdf", ".png", ".safetensors"):
        (document_root / f"never-read{suffix}").write_bytes(b"sentinel")
    original = Path.read_bytes

    def guarded(path: Path) -> bytes:
        if path.suffix.lower() in {".pdf", ".png", ".safetensors"}:
            pytest.fail(f"prohibited payload read: {path}")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    content = _generate(tmp_path, fixture)
    assert json.loads(content)["source_count"] == 35


def test_selection_publication_is_no_clobber_and_exact_check_is_reusable(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path, count=35)
    document_root = fixture["document_root"]
    assert isinstance(document_root, Path)
    spec = _retained_spec(tmp_path, fixture)
    output = tmp_path / "replay_v33/resolved_specs_v1/00_initial/selection.json"
    kwargs = {
        "data_root": tmp_path,
        "document_input_root": document_root,
        "retained_collection_spec": spec,
        "output": output,
    }

    write_imported_selection(**kwargs, check=False)
    write_imported_selection(**kwargs, check=True)
    with pytest.raises(FileExistsError):
        write_imported_selection(**kwargs, check=False)
