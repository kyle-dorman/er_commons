"""Fresh authoring intake obeys a metadata-only predecessor selection boundary."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes, sha256_bytes, sha256_file
from er_commons.synthetic_regeneration import development_slots, prepare_regeneration


def _save(path: Path, value: Any) -> dict[str, Any]:
    """Save and bind an invented fixture object."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))
    return {"path": str(path), "sha256": sha256_file(path), "byte_size": path.stat().st_size}


def _reservation(dev: list[str]) -> dict[str, Any]:
    """Make the real partition sizes without any generated answer content."""
    categories = [
        f"{p}{n:02}"
        for p, count in (("P", 9), ("O", 4), ("F", 10), ("C", 5), ("R", 3))
        for n in range(1, count + 1)
    ]
    selected, other = [], []
    for i, case in enumerate(dev):
        for j, category in enumerate(categories):
            identity = f"{case}-{category}-{j:02}-{i:012x}"
            (selected if j < 22 + (i < 5) else other).append(identity)
    return {
        "development_variant_ids": selected,
        "final_check_variant_ids": other[:118],
        "excluded_variant_ids": other[118:123],
    }


def _fixture(root: Path) -> tuple[Path, dict[str, Any]]:
    """Create sealed original inputs plus inaccessible generated/test payloads."""
    release, batch = root / "release", root / "batch"
    dev = [f"C{i:03}" for i in range(1, 20)]
    split = _save(
        release / "split.json",
        {"status": "approved", "dev": dev, "test": [f"T{i}" for i in range(30)]},
    )
    corpus = _save(release / "corpus/manifest.json", {"documents": []})
    references = {
        case: _save(release / f"curator/cases/{case}.json", {"original_reference": case})
        for case in dev
    }
    released = [
        {**ref, "path": str(Path(ref["path"]).relative_to(release))}
        for ref in [split, corpus, *references.values()]
    ]
    released.append({"path": "target/test.jsonl", "sha256": "forbidden", "byte_size": 0})
    release_completion = _save(
        release / "completion.json", {"status": "complete", "inventory": released}
    )
    release_pointer = _save(
        root / "release_pointer.json",
        {
            "status": "complete",
            "release_id": "frozen",
            "completion": release_completion,
            "approved_split": split,
        },
    )
    packets = [
        {
            "case_id": case,
            "question": "Invented question",
            "release_id": "frozen",
            "reference_binding": references[case],
            "reference_answer": {},
            "sources": [],
            "source_packet_sha256": sha256_bytes(json_bytes([])),
        }
        for case in dev
    ]
    intake = {
        "release_id": "frozen",
        "dev_case_ids": dev,
        "cases": packets,
        "restricted_controls": [],
        "limitations": [],
        "corpus_manifest_binding": corpus,
        "source_bindings": {"pointer": release_pointer, "split": split},
    }
    inventory = [_save(batch / "intake.json", intake)]
    for packet in packets:
        inventory.append(
            _save(
                batch / f"cases/{packet['case_id']}/input.json",
                {**packet, "requested_categories": ["old"]},
            )
        )
    reservation = _save(batch / "published/reservation.json", _reservation(dev))
    inventory.append(reservation)
    inventory = [{**ref, "path": str(Path(ref["path"]).relative_to(batch))} for ref in inventory]
    for forbidden in (
        "published/answers.jsonl",
        "published/expectations.jsonl",
        "cases/C001/attempts/raw_output.json",
    ):
        inventory.append({"path": forbidden, "sha256": "forbidden", "byte_size": 0})
    completion = _save(batch / "completion.json", {"inventory": {"files": inventory}})
    pointer = root / "pointer.json"
    _save(
        pointer,
        {
            "status": "complete_with_limitations",
            "batch_completion": completion,
            "artifacts": {"reservation.json": reservation},
        },
    )
    return pointer, intake


def test_exact_slots_without_opening_generated_or_test_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pointer, original = _fixture(tmp_path)
    open_path = Path.open
    seen: list[Path] = []

    def guarded(path: Path, *args: Any, **kwargs: Any) -> Any:
        """Fail even checksum access to forbidden payloads, not just JSON reads."""
        assert not any(
            word in str(path)
            for word in (
                "answers.jsonl",
                "expectations.jsonl",
                "raw_output",
                "test.jsonl",
                "attempts/",
            )
        )
        seen.append(path)
        return open_path(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    result = prepare_regeneration(pointer, tmp_path)
    assert sum(len(row["regeneration_slots"]) for row in result["cases"]) == 423
    assert len(result["cases"]) == 19
    assert result["annotation_version"] == "task09a2.stage_expectations.v1"
    assert len(result["regeneration"]["preserved_final_check_variant_ids"]) == 118
    assert len(result["regeneration"]["preserved_excluded_variant_ids"]) == 5
    assert result["source_bindings"] and seen
    assert all(
        row["requested_categories"] == sorted(row["regeneration_slots"]) for row in result["cases"]
    )
    assert "annotation_version" not in original["cases"][0]


def test_changed_original_input_fails_closed(tmp_path: Path) -> None:
    pointer, _ = _fixture(tmp_path)
    (tmp_path / "batch/cases/C001/input.json").write_text("changed")
    with pytest.raises(ValueError, match="Bound size changed"):
        prepare_regeneration(pointer, tmp_path)


def test_changed_frozen_reference_fails_closed(tmp_path: Path) -> None:
    pointer, _ = _fixture(tmp_path)
    (tmp_path / "release/curator/cases/C001.json").write_text("changed")
    with pytest.raises(ValueError, match="Bound size changed"):
        prepare_regeneration(pointer, tmp_path)


@pytest.mark.parametrize("mutation", ["overlap", "duplicate_category", "test_case", "missing_slot"])
def test_rejects_invalid_slot_boundaries(mutation: str) -> None:
    dev = [f"C{i:03}" for i in range(1, 20)]
    reservation = _reservation(dev)
    ids = reservation["development_variant_ids"]
    if mutation == "overlap":
        reservation["final_check_variant_ids"][0] = ids[0]
    elif mutation == "duplicate_category":
        ids[1] = ids[0][:-12] + "ffffffffffff"
    elif mutation == "test_case":
        ids[0] = ids[0].replace("C001", "C999")
    else:
        ids.pop()
    with pytest.raises(ValueError):
        development_slots(reservation, dev)


def test_resigned_input_cannot_diverge_from_original_intake(tmp_path: Path) -> None:
    pointer, _ = _fixture(tmp_path)
    path = tmp_path / "batch/cases/C001/input.json"
    value = json.loads(path.read_text())
    value["question"] = "Injected changed question"
    changed = _save(path, value)
    completion_path = tmp_path / "batch/completion.json"
    completion = json.loads(completion_path.read_text())
    for row in completion["inventory"]["files"]:
        if row["path"] == "cases/C001/input.json":
            row.update({**changed, "path": row["path"]})
    completion_binding = _save(completion_path, completion)
    result = json.loads(pointer.read_text())
    result["batch_completion"] = completion_binding
    _save(pointer, result)
    with pytest.raises(ValueError, match="differs from source-only intake"):
        prepare_regeneration(pointer, tmp_path)


def test_authoritative_category_edges() -> None:
    dev = [f"C{i:03}" for i in range(1, 20)]
    reservation = _reservation(dev)
    ids = reservation["development_variant_ids"]
    # Replace existing first-case categories, retaining exact population counts.
    ids[0] = "C001-F10-00-fffffffffff0"
    ids[1] = "C001-R03-01-fffffffffff1"
    # F10 was already in the 23-category first-case selection.
    ids[22] = "C001-C01-22-fffffffffff2"
    slots = development_slots(reservation, dev)
    assert {"F10", "R03"} <= slots["C001"].keys()
    ids[1] = "C001-R04-01-fffffffffff1"
    with pytest.raises(ValueError, match="Invalid development slot identity"):
        development_slots(reservation, dev)
