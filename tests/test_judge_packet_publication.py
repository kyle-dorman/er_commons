"""Development publication guards and reproducibility, entirely with synthetic files."""

import json
from pathlib import Path

import pytest

from er_commons.artifact_io import file_reference, json_bytes, sha256_bytes
from er_commons.judge_packet_publication import prepare_packets


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Seal a synthetic intake with undecodable reserved and test payload sentinels."""
    root, release = tmp_path / "batch", tmp_path / "release"
    root.mkdir()
    release.mkdir()

    def write(path: Path, value: object) -> dict:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(value))
        return {**file_reference(path, root=path.parent), "path": str(path)}

    dev = [f"C{i:03d}" for i in range(19)]
    split = write(
        release / "split.json",
        {"status": "approved", "dev": dev, "test": [f"T{i}" for i in range(30)]},
    )
    reference = write(release / "reference.json", {"approved": True})
    corpus = write(
        release / "corpus.json",
        {"documents": [{"source_id": "source", "extraction_id": "extract-v1"}]},
    )
    handoff = write(
        release / "handoff.json", {"release_id": "frozen", "artifacts": {"corpus": corpus}}
    )
    (release / "test.json").write_text("INVALID TEST PAYLOAD")
    release_completion = write(
        release / "completion.json",
        {
            "status": "complete",
            "inventory": [
                file_reference(path, root=release) for path in release.iterdir() if path.is_file()
            ],
        },
    )
    release_pointer = tmp_path / "release_pointer.json"
    write(
        release_pointer,
        {
            "status": "complete",
            "release_id": "frozen",
            "completion": release_completion,
            "approved_split": split,
            "handoff": handoff,
        },
    )
    answer = {
        "status": "answered",
        "conclusion": {
            "point_id": "revealing-F01",
            "text": "Exact café claim",
            "citation_ids": ["o1"],
        },
        "supporting_points": [],
        "qualifications": [],
        "optional_context": [],
    }
    sources = [
        {
            "occurrence_id": "o1",
            "source_id": "source",
            "extraction_id": "extract-v1",
            "full_source_text": "Exact source",
            "tables": [],
        }
    ]
    packet = {
        "case_id": dev[0],
        "release_id": "frozen",
        "reference_version": "v1",
        "reference_binding": reference,
        "question": "Question?",
        "reference_answer": answer,
        "sources": sources,
        "source_packet_sha256": sha256_bytes(json_bytes(sources)),
    }
    write(root / "cases" / dev[0] / "input.json", packet)
    write(root / "prepared.json", {"case_ids": dev})
    reservation = {
        "development_variant_ids": [f"v{i}" for i in range(423)],
        "final_check_variant_ids": [f"r{i}" for i in range(118)],
        "excluded_variant_ids": [f"e{i}" for i in range(5)],
    }
    artifacts = {"reservation.json": write(root / "reservation.json", reservation)}
    row = {
        "variant_id": "v0",
        "case_id": dev[0],
        "answer": answer,
        "source_packet_hash": packet["source_packet_sha256"],
        "parent_reference_hash": sha256_bytes(json_bytes(answer)[:-1]),
        "release_id": "frozen",
        "reference_version": "v1",
        "reference_binding": reference,
    }
    for name, value in [
        ("answers.jsonl", row),
        (
            "expectations.jsonl",
            {
                "variant_id": "v0",
                "case_id": dev[0],
                "comparison_eligible": True,
                "synthetic_expectation": "SECRET_LABEL",
            },
        ),
    ]:
        path = root / name
        path.write_bytes(json_bytes(value) + b'{"variant_id":"r0","answer":INVALID}\n')
        artifacts[name] = {**file_reference(path, root=root), "path": str(path)}
    completion = write(
        root / "completion.json",
        {
            "inventory": {
                "files": [
                    file_reference(path, root=root) for path in root.rglob("*") if path.is_file()
                ]
            }
        },
    )
    pointer = tmp_path / "pointer.json"
    write(
        pointer,
        {
            "status": "complete_with_limitations",
            "namespace": str(root),
            "batch_completion": completion,
            "artifacts": artifacts,
        },
    )
    return pointer, release_pointer


def test_selected_publication_repeat_and_boundaries(tmp_path: Path) -> None:
    """Selection never decodes reserved/test sentinels or emits synthetic expectations."""
    pointer, release = fixture(tmp_path)
    output = tmp_path / "output"
    args = dict(variant_ids=["v0"], control_cases=["C000"])
    first = prepare_packets(pointer, release, output, **args)
    assert first == prepare_packets(pointer, release, output, **args)
    assert first["packet_count"] == 4
    for name in ("packets", "provenance"):
        path = output / f"{name}.json"
        assert first[name] == {**file_reference(path, root=output), "path": str(path.resolve())}
    packets = json.loads((output / "packets.json").read_text())
    assert all("SECRET_LABEL" not in json.dumps(p["payload"]) for p in packets)
    assert [p["dimension"] for p in packets] == ["grounding", "adequacy"] * 2
    (output / "packets.json").write_text("changed")
    with pytest.raises(FileExistsError):
        prepare_packets(pointer, release, output, **args)


@pytest.mark.parametrize("variant,control", [("r0", None), ("e0", None), (None, "T0")])
def test_reject_forbidden_selections(
    tmp_path: Path, variant: str | None, control: str | None
) -> None:
    """Held-out identities cannot enter development publication."""
    pointer, release = fixture(tmp_path)
    with pytest.raises(ValueError, match="development"):
        prepare_packets(
            pointer,
            release,
            tmp_path / "output",
            variant_ids=[variant] if variant else [],
            control_cases=[control] if control else [],
        )
    assert not (tmp_path / "output").exists()


def test_explicit_selection_required(tmp_path: Path) -> None:
    """There is no default all-population execution."""
    with pytest.raises(ValueError, match="Select explicit"):
        prepare_packets(
            tmp_path / "absent",
            tmp_path / "absent",
            tmp_path / "out",
            variant_ids=[],
            control_cases=[],
        )


def test_changed_selected_source_rejected(tmp_path: Path) -> None:
    """Missing or changed infrastructure is not an unresolved candidate citation."""
    pointer, release = fixture(tmp_path)
    (tmp_path / "batch/cases/C000/input.json").write_text("changed")
    with pytest.raises(ValueError, match="size changed"):
        prepare_packets(pointer, release, tmp_path / "out", variant_ids=[], control_cases=["C000"])


def reseal(tmp_path: Path, pointer: Path, name: str) -> None:
    """Bind a deliberate synthetic fixture change through both pointer and inventory."""
    root = tmp_path / "batch"
    result = json.loads(pointer.read_text())
    result["artifacts"][name] = {**file_reference(root / name, root=root), "path": str(root / name)}
    completion = root / "completion.json"
    value = json.loads(completion.read_text())
    value["inventory"]["files"] = [
        file_reference(root / row["path"], root=root) for row in value["inventory"]["files"]
    ]
    completion.write_bytes(json_bytes(value))
    result["batch_completion"] = {**file_reference(completion, root=root), "path": str(completion)}
    pointer.write_bytes(json_bytes(result))


def test_ineligible_gate_precedes_answers(tmp_path: Path) -> None:
    """Selected comparison exclusions fail before attempting answer-file access."""
    pointer, release = fixture(tmp_path)
    path = tmp_path / "batch/expectations.jsonl"
    row = json.loads(path.read_text().splitlines()[0])
    row["comparison_eligible"] = False
    path.write_bytes(json_bytes(row))
    reseal(tmp_path, pointer, "expectations.jsonl")
    (tmp_path / "batch/answers.jsonl").unlink()
    with pytest.raises(ValueError, match="comparison exclusion"):
        prepare_packets(pointer, release, tmp_path / "out", variant_ids=["v0"], control_cases=[])


def test_wrong_variant_source_binding_rejected(tmp_path: Path) -> None:
    """Even internally sealed records must match the selected source/reference input."""
    pointer, release = fixture(tmp_path)
    path = tmp_path / "batch/answers.jsonl"
    row = json.loads(path.read_text().splitlines()[0])
    row["source_packet_hash"] = "wrong"
    path.write_bytes(json_bytes(row))
    reseal(tmp_path, pointer, "answers.jsonl")
    with pytest.raises(ValueError, match="source/reference binding"):
        prepare_packets(pointer, release, tmp_path / "out", variant_ids=["v0"], control_cases=[])


@pytest.mark.parametrize(
    "field,value", [("source_id", "official-response"), ("extraction_id", "different-extraction")]
)
def test_source_must_match_frozen_corpus(tmp_path: Path, field: str, value: str) -> None:
    """A sealed case cannot expand the frozen corpus or switch extraction editions."""
    pointer, release = fixture(tmp_path)
    path = tmp_path / "batch/cases/C000/input.json"
    packet = json.loads(path.read_text())
    packet["sources"][0][field] = value
    packet["source_packet_sha256"] = sha256_bytes(json_bytes(packet["sources"]))
    path.write_bytes(json_bytes(packet))
    reseal(tmp_path, pointer, "answers.jsonl")
    with pytest.raises(ValueError, match="outside the frozen allowed corpus"):
        prepare_packets(pointer, release, tmp_path / "out", variant_ids=[], control_cases=["C000"])


def test_output_rejects_unrelated_files_without_writing(tmp_path: Path) -> None:
    """An existing directory must contain only this publication's planned files."""
    pointer, release = fixture(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    (output / "unrelated.txt").write_bytes(b"preserve me")
    with pytest.raises(FileExistsError, match="Unexpected files"):
        prepare_packets(pointer, release, output, variant_ids=[], control_cases=["C000"])
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        "unrelated.txt": b"preserve me"
    }


@pytest.mark.parametrize("conflicting_file", ["provenance.json", "completion.json"])
def test_output_conflict_does_not_publish_other_files(
    tmp_path: Path, conflicting_file: str
) -> None:
    """A conflict in a later planned file must fail before publishing earlier files."""
    pointer, release = fixture(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    (output / conflicting_file).write_bytes(b"conflicting content")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        prepare_packets(pointer, release, output, variant_ids=[], control_cases=["C000"])
    assert {path.name: path.read_bytes() for path in output.iterdir()} == {
        conflicting_file: b"conflicting content"
    }


@pytest.mark.parametrize("retained_file", ["packets.json", "provenance.json", "completion.json"])
def test_output_resumes_exact_partial_publication(tmp_path: Path, retained_file: str) -> None:
    """Any identical partial output resumes to the same complete publication bytes."""
    pointer, release = fixture(tmp_path)
    output = tmp_path / "output"
    args = dict(variant_ids=["v0"], control_cases=["C000"])
    manifest = prepare_packets(pointer, release, output, **args)
    expected = {path.name: path.read_bytes() for path in output.iterdir()}
    for path in output.iterdir():
        if path.name != retained_file:
            path.unlink()
    assert prepare_packets(pointer, release, output, **args) == manifest
    assert {path.name: path.read_bytes() for path in output.iterdir()} == expected
