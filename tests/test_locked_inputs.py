"""Invented offline split routing, projection and identity checks for Task 13."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_target_generation import packet

from er_commons import locked_inputs as inputs
from er_commons.artifact_io import sha256_bytes, stable_json_sha256
from er_commons.reporting_inputs import SealedInputs


def split() -> dict[str, Any]:
    """Build an invented disjoint 19/30 roster."""
    return {
        "status": "approved",
        "dev": [f"C{i:03}" for i in range(1, 20)],
        "test": [f"C{i:03}" for i in range(20, 50)],
    }


def test_full_roster_preserves_180_slots() -> None:
    cases = inputs.validate_roster(split(), "test")
    slots = inputs.planned_slots(cases)
    assert len(slots) == 180
    assert len({(r["model"], r["case_id"], r["repeat"]) for r in slots}) == 180
    assert {r["repeat"] for r in slots} == {1, 2, 3}
    assert all(
        r["condition"] == ("openai_generation" if r["model"] == "luna" else "anthropic_generation")
        for r in slots
    )
    assert inputs.planned_slots(cases) == slots


@pytest.mark.parametrize("failure", ["overlap", "missing", "duplicate", "unapproved"])
def test_invalid_roster_fails_before_content(failure: str) -> None:
    value = split()
    if failure == "overlap":
        value["test"][0] = value["dev"][0]
    elif failure == "missing":
        value["test"].pop()
    elif failure == "duplicate":
        value["test"][0] = value["test"][1]
    else:
        value["status"] = "draft"
    with pytest.raises(ValueError):
        inputs.validate_roster(value, "test")


def test_duplicate_missing_and_reordered_rows_rejected() -> None:
    cases = split()["test"]
    rows = [{"case_id": case} for case in cases]
    for bad in (rows[:-1], rows + rows[:1], list(reversed(rows))):
        with pytest.raises(ValueError, match="roster"):
            inputs._rows(b"\n".join(json.dumps(row).encode() for row in bad), cases)
    with pytest.raises(ValueError, match="Duplicate"):
        inputs._json(b'{"case_id":"C001","case_id":"C002"}')


def test_projection_preserves_verbatim_evidence_and_excludes_references() -> None:
    record = packet()
    record["payload"]["question"] = "What does the 2025 Draft EIR say?"
    passage = record["payload"]["passages"][0]
    passage["source_id"] = "feir_appendix_f1"
    passage["full_source_text"] = "The 2025 Draft EIR describes 2100 conditions."
    original = copy.deepcopy(record)
    mapping = {
        "case_id": record["case_id"],
        "payload_sha256": stable_json_sha256(record["payload"]),
        "private_reference_role": "must never reach the target",
    }
    projected, projected_mapping = inputs.project_record(record, mapping)
    assert projected["payload"]["question"] == "What does the EIR say?"
    assert projected["payload"]["passages"][0]["full_source_text"] == passage["full_source_text"]
    assert projected["payload"]["passages"][0]["title"].startswith("EIR Appendix F.1: ")
    assert "must never reach" not in json.dumps(projected)
    assert record == original
    assert projected_mapping["payload_sha256"] == stable_json_sha256(projected["payload"])
    assert mapping["payload_sha256"] == stable_json_sha256(original["payload"])
    projected["reference"] = "secret"
    with pytest.raises(ValueError, match="fields"):
        inputs.project_record(projected, projected_mapping)


def test_projection_rejects_unbound_mapping() -> None:
    record = packet()
    with pytest.raises(ValueError, match="mapping"):
        inputs.project_record(record, {"case_id": "other", "payload_sha256": "wrong"})


def test_sealed_reader_does_not_open_unselected_siblings(tmp_path: Path) -> None:
    raw = b'{"case_id":"C020"}\n'
    (tmp_path / "test.jsonl").write_bytes(raw)
    reader = SealedInputs(
        tmp_path,
        {
            "files": [
                {"path": "test.jsonl", "sha256": sha256_bytes(raw), "byte_size": len(raw)},
                {"path": "reserved.jsonl", "sha256": "not available", "byte_size": 123},
            ]
        },
    )
    sources = inputs._Sources(tmp_path, tmp_path)
    assert sources.sealed(reader, "test.jsonl") == raw
    assert list(reader.consumed) == ["test.jsonl"]
    (tmp_path / "test.jsonl").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="mismatch"):
        sources.sealed(reader, "test.jsonl")


def test_explicit_development_entry_cannot_select_test(monkeypatch: pytest.MonkeyPatch) -> None:
    observed = []

    def load(repo: Path, root: Path, mode: str) -> dict[str, Any]:
        """Capture selection without loading any real source content."""
        observed.append(mode)
        return {"split": mode}

    monkeypatch.setattr(inputs, "_load", load)
    assert inputs.load_development_replay(Path("."), Path("."))["split"] == "dev"
    assert inputs.load_locked(Path("."), Path("."))["split"] == "test"
    assert observed == ["dev", "test"]


def test_complete_adapter_opens_only_selected_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise all loader joins with invented sealed publications and forbidden siblings."""
    repo, data = tmp_path / "repo", tmp_path / "data"
    specs = repo / "docs/specs"
    specs.mkdir(parents=True)
    data.mkdir()

    def write(path: Path, value: Any, *, raw: bool = False) -> dict[str, Any]:
        """Create an invented artifact and return its byte identity."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = value if raw else json.dumps(value).encode()
        path.write_bytes(content)
        return {"path": str(path), "byte_size": len(content), "sha256": sha256_bytes(content)}

    def seal(root: Path, files: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Bind explicit metadata, including deliberately unreadable other splits."""
        return write(
            root / "completion.json", {"inventory": [{**v, "path": k} for k, v in files.items()]}
        )

    frozen = {}
    for key in ("prompt", "context"):
        binding = write(repo / f"{key}.md", b"Frozen instructions", raw=True)
        frozen[f"{key}_path"] = f"{key}.md"
        frozen[f"{key}_sha256"] = binding["sha256"]
    binding = write(specs / "frozen.json", frozen)
    binding["path"] = "docs/specs/frozen.json"
    write(specs / "task11e_result.json", {"frozen_configuration": binding})
    source, refs, d6 = data / "task10", data / "refs", data / "d6"
    files = {"split.json": write(source / "split.json", split())}
    records, mappings, ref_files, d6_files = [], [], {}, {}
    for case in split()["test"]:
        record = packet()
        record["case_id"] = case
        record["payload"]["passages"][0]["source_id"] = "deir_main"
        records.append(record)
        mappings.append({"case_id": case, "payload_sha256": stable_json_sha256(record["payload"])})
        reference = {
            "case_id": case,
            "answer": {
                "question": record["payload"]["question"],
                "conclusion": {"text": "Private gold"},
            },
        }
        name = f"curator/cases/{case}.json"
        ref_files[name] = write(refs / name, reference)
        name = f"labels/publication_v5/private/{case}.json"
        private = {
            "payload": reference["answer"],
            "labels": {"approval_status": "inherited_approved_reference"},
            "source": reference,
        }
        d6_files[name] = write(d6 / name, private)
    for name, values in (
        ("target/test.jsonl", records),
        ("evaluator/test_mappings.jsonl", mappings),
    ):
        files[name] = write(
            source / name, b"\n".join(json.dumps(row).encode() for row in values), raw=True
        )
    files["target/dev.jsonl"] = {"byte_size": 100, "sha256": "deliberately absent"}
    write(specs / "task10_final_result.json", {"completion": seal(source, files)})
    write(
        specs / "task09f_question_publication_v2_result.json", {"completion": seal(refs, ref_files)}
    )
    script = b"""RECORDS = []
def add(collection, old_id, case, payload, labels, source, heldout):
    assert heldout
    RECORDS.append({"eligible": True, "retirement_reasons": [], "payload": payload,
                    "new_id": case, "private_original": {"payload": payload,
                    "labels": labels, "source": source}})
"""
    name = "labels/publish_labels_v5.py"
    d6_files[name] = write(d6 / name, script, raw=True)
    d6_files["labels/publication_v5/records.jsonl"] = {
        "byte_size": 100,
        "sha256": "reserved never opened",
    }
    write(specs / "task11d6_result.json", {"completion": seal(d6, d6_files)})
    opened = []
    original = Path.read_bytes

    def read(path: Path) -> bytes:
        """Record actual file reads to check the split boundary."""
        opened.append(str(path))
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    result = inputs.load_locked(repo, data)
    assert len(result["inputs"]) == 30
    assert len(result["slots"]) == 180
    assert all("Private gold" not in json.dumps(row["record"]) for row in result["inputs"].values())
    assert not any("dev.jsonl" in path or "records.jsonl" in path for path in opened)
    assert result["inputs_sha256"] == stable_json_sha256(result["inputs"])


@pytest.mark.parametrize("source", ["deir_appendix_k1_part_1_of_4", "deir_appendix_k1_part_4_of_4"])
def test_multipart_appendix_preserves_source_identity(source: str) -> None:
    """Multipart PDFs share an appendix label without merging canonical evidence."""
    record = packet()
    record["payload"]["passages"][0]["source_id"] = source
    original = copy.deepcopy(record)
    mapping = {
        "case_id": record["case_id"],
        "payload_sha256": stable_json_sha256(record["payload"]),
    }
    projected, _ = inputs.project_record(record, mapping)
    passage = projected["payload"]["passages"][0]
    assert passage["source_id"] == source
    assert passage["title"].startswith("EIR Appendix K.1: ")
    assert {k: v for k, v in passage.items() if k not in {"title", "edition"}} == {
        k: v for k, v in original["payload"]["passages"][0].items() if k not in {"title", "edition"}
    }
    assert record == original


@pytest.mark.parametrize(
    "suffix",
    [
        "_part_0_of_4",
        "_part_5_of_4",
        "_part_1_of_0",
        "_part_01_of_4",
        "_part_1",
        "_part_1_of_4_extra",
    ],
)
def test_multipart_appendix_rejects_malformed_suffix(suffix: str) -> None:
    """Only positive in-range part numbers qualify for the mechanical label rule."""
    with pytest.raises(ValueError, match="source label"):
        inputs._document("deir_appendix_k1" + suffix)
