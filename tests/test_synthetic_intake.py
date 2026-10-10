"""Synthetic checks for development boundaries and frozen byte identities."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes, sha256_file
from er_commons.synthetic_intake import prepare_intake, project_answer, verify_binding, verify_split


def test_projection_preserves_exact_semantics_and_excludes_history() -> None:
    answer: dict[str, Any] = {
        "conclusion": {"text": "Exact text", "point_id": "c", "citation_ids": ["s"]},
        "supporting_points": [],
        "qualifications": [],
        "optional_context": [],
        "citation_locators": [],
        "review_notes": ["SECRET HISTORY"],
    }
    projected = project_answer(answer)
    assert projected["conclusion"] == answer["conclusion"]
    assert "SECRET HISTORY" not in json.dumps(projected)
    projected["conclusion"]["text"] = "changed"
    assert answer["conclusion"]["text"] == "Exact text"


def test_split_rejects_test_overlap() -> None:
    split: dict[str, Any] = {
        "dev": [f"D{i}" for i in range(19)],
        "test": [f"T{i}" for i in range(30)],
        "status": "approved",
    }
    verify_split(split)
    split["test"][0] = split["dev"][0]
    with pytest.raises(ValueError, match="overlap"):
        verify_split(split)


def test_bound_bytes_and_escape(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text("original")
    binding = {"path": str(path), "sha256": sha256_file(path), "byte_size": 8}
    verify_binding(binding, tmp_path)
    path.write_text("modified")
    with pytest.raises(ValueError, match="checksum"):
        verify_binding(binding, tmp_path)
    with pytest.raises(ValueError, match="escaping"):
        verify_binding(binding, tmp_path / "nested")


def _release(root: Path) -> Path:
    """Create a sealed fixture whose test files deliberately are not JSON."""
    root.mkdir(exist_ok=True)

    def save(relative: str, value: Any) -> dict[str, Any]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(value))
        return {"path": str(path), "sha256": sha256_file(path), "byte_size": path.stat().st_size}

    dev = [f"D{i:02d}" for i in range(19)]
    test = [f"T{i:02d}" for i in range(30)]
    split = save("split.json", {"status": "approved", "dev": dev, "test": test})
    target = root / "target/dev.jsonl"
    target.parent.mkdir()
    target.write_bytes(b"".join(json_bytes({"case_id": c, "question": c}) for c in dev))
    target_binding = {"path": str(target), "sha256": sha256_file(target)}
    index = []
    for case_id in dev:
        answer = {
            "conclusion": {},
            "supporting_points": [],
            "qualifications": [],
            "optional_context": [],
            "citation_locators": [],
            "review_notes": ["secret"],
        }
        bound = save(
            f"curator/cases/{case_id}.json",
            {
                "case_id": case_id,
                "question": case_id,
                "answer": answer,
                "citation_occurrences": [],
                "proposal_version": 1,
                "human_answer_approval": {"decision": "approved"},
                "final_disposition": "approved",
            },
        )
        index.append(
            {
                "case_id": case_id,
                "split": "dev",
                "reference_record": f"curator/cases/{case_id}.json",
                "reference_sha256": bound["sha256"],
            }
        )
    for case_id in test:
        path = root / f"curator/cases/{case_id}.json"
        path.write_text("TEST CONTENT MUST NEVER BE PARSED")
        index.append({"case_id": case_id, "split": "test"})
    ip = root / "curator/reference_index.jsonl"
    ip.write_bytes(b"".join(json_bytes(row) for row in index))
    ib = {"path": str(ip), "sha256": sha256_file(ip)}
    corpus = save("corpus/manifest.json", {"documents": []})
    handoff = save(
        "handoff.json",
        {
            "release_id": "fixture",
            "limitations": [],
            "artifacts": {"corpus": corpus, "reference_index": ib},
        },
    )
    inventory = [
        {
            "path": p.relative_to(root).as_posix(),
            "sha256": sha256_file(p),
            "byte_size": p.stat().st_size,
        }
        for p in sorted(root.rglob("*"))
        if p.is_file()
    ]
    completion = save("completion.json", {"status": "complete", "inventory": inventory})
    pointer = root.parent / "pointer.json"
    pointer.write_bytes(
        json_bytes(
            {
                "status": "complete",
                "release_id": "fixture",
                "completion": completion,
                "handoff": handoff,
                "approved_split": split,
                "target_dev": target_binding,
            }
        )
    )
    return pointer


def test_complete_intake_never_parses_test_content(tmp_path: Path) -> None:
    pointer = _release(tmp_path / "release")
    intake = prepare_intake(pointer, tmp_path)
    assert len(intake["cases"]) == 19
    assert "release:curator/cases/T00.json" in intake["source_bindings"]
    assert all(Path(ref["path"]).is_absolute() for ref in intake["source_bindings"].values())
    assert "secret" not in json.dumps(intake["cases"])
    assert "secret" in json.dumps(intake["restricted_controls"])
    assert intake["verification"]["test_content_parsed"] is False
    (tmp_path / "release/unexpected.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        prepare_intake(pointer, tmp_path)
