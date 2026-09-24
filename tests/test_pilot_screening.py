"""Check the single-case preparation boundary independently of Label Studio."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.pilot_screening import _paragraphs, build_trial_task, main


def _seal(root: Path, name: str, rows: list[dict[str, Any]]) -> str:
    """Write a small fixture and return its byte seal."""
    content = "".join(json.dumps(row) + "\n" for row in rows).encode()
    (root / name).write_bytes(content)
    return hashlib.sha256(content).hexdigest()


@pytest.fixture
def sample(tmp_path: Path) -> Path:
    """Provide two selectable comments with one shared response and linked context."""
    units = [
        {
            "unit_id": key,
            "unit_kind": kind,
            "official_label": key,
            "text": f"{key}\nA <script>alert('x')</script> & a wrapped \nline.\nNext paragraph.",
            "source_pages": [1],
            "span_ids": [f"span-{key}"],
        }
        for key, kind in [
            ("c1", "comment"),
            ("c2", "comment"),
            ("r", "response"),
            ("g", "general_response"),
        ]
    ]
    cases = [
        {
            "comment_id": key,
            "comment_label": key,
            "accepted_view_id": f"view-{key}",
            "context_unit_ids": [key, "r", "g"],
            "direct_response_ids": ["r"],
            "general_response_ids": ["g"],
            "relationship_ids": ["edge1"],
            "reference_outcome_ids": ["o1"],
        }
        for key in ["c1", "c2"]
    ]
    outcomes = [
        {
            "outcome_id": "o1",
            "source_unit_id": "g",
            "outcome": "unresolved",
            "raw_target_label": "Figure <2>",
            "terminal_reason": "visual evidence",
        }
    ]
    manifest = {
        "inventory_id": "inventory-1",
        "files": {
            "sample.jsonl": _seal(tmp_path, "sample.jsonl", cases),
            "review_context.jsonl": _seal(tmp_path, "review_context.jsonl", units),
        },
        "source_components": {
            "outcomes": {
                "path": "outcomes.jsonl",
                "sha256": _seal(tmp_path, "outcomes.jsonl", outcomes),
            }
        },
    }
    (tmp_path / "selection_manifest.json").write_text(json.dumps(manifest))
    return tmp_path


def test_one_unrated_case_preserves_context_and_escapes_source(sample: Path) -> None:
    """A shared response does not cause other comments or executable markup to leak in."""
    task = build_trial_task(
        sample, "c1", data_root=sample, source_base_url="http://127.0.0.1:8098/source.pdf"
    )
    assert list(task) == ["data"]
    data = task["data"]
    assert data["comment_id"] == "c1"
    assert data["context_unit_ids"] == ["c1", "r", "g"]
    assert "<script>" not in data["comment_html"]
    assert "&lt;script&gt;" in data["comment_html"]
    assert "wrapped line." in data["comment_html"]
    assert "#page=1" in data["comment_html"]
    assert "c2" not in json.dumps(task)
    assert "Figure &lt;2&gt;" in data["reference_html"]
    assert "visual evidence" in data["reference_html"]
    assert "fit" not in data and "predictions" not in task and "annotations" not in task


def test_rejects_changed_source_or_unknown_case(sample: Path) -> None:
    """Selection and checksum errors fail before creating an import."""
    with pytest.raises(ValueError, match="not in the selected"):
        build_trial_task(sample, "unknown", data_root=sample)
    with (sample / "review_context.jsonl").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        build_trial_task(sample, "c1", data_root=sample)


def test_rejects_duplicate_selection(sample: Path) -> None:
    """Even correctly sealed duplicate identities must not silently collapse."""
    rows = [json.loads(line) for line in (sample / "sample.jsonl").read_text().splitlines()]
    manifest = json.loads((sample / "selection_manifest.json").read_text())
    manifest["files"]["sample.jsonl"] = _seal(sample, "sample.jsonl", rows + [rows[0]])
    (sample / "selection_manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Duplicate comment_id"):
        build_trial_task(sample, "c1", data_root=sample)


def test_cli_writes_exactly_one_and_does_not_clobber(
    sample: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command has no bulk mode and cannot overwrite a previous review packet."""
    output = sample / "trial.json"
    monkeypatch.setenv("ER_COMMONS_DATA_ROOT", str(sample))
    monkeypatch.setattr(
        "sys.argv",
        [
            "pilot_screening",
            "--sample-root",
            str(sample),
            "--comment-id",
            "c1",
            "--output",
            str(output),
        ],
    )
    main()
    assert len(json.loads(output.read_text())) == 1
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        main()
    assert output.read_bytes() == before


def test_figure_labels_are_separate_and_original_survives(sample: Path) -> None:
    """Figure OCR remains available without appearing as ordinary response prose."""
    path = sample / "review_context.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    original = (
        "Introductory prose.\nDraft EIR Figure 2-11: Agency responsibilities\n"
        "OCRLABEL\nChapter 13. Responses to Comments\n"
        "13.2. General Responses\n13-18 Baylands Specific Plan Final EIR\n"
        "Volume 4. Responses to Comments on the Draft EIR\nCity of Brisbane\nMay 2026\n"
        "Continuing prose.\n"
    )
    rows[-1]["text"] = original
    manifest_path = sample / "selection_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["review_context.jsonl"] = _seal(sample, path.name, rows)
    manifest_path.write_text(json.dumps(manifest))
    data = build_trial_task(sample, "c1", data_root=sample)["data"]
    assert "<p>OCRLABEL" not in data["context_html"]
    assert "Figure caption and extracted labels" in data["context_html"]
    assert "<p>Continuing prose.</p>" in data["context_html"]
    assert original in data["context_html"]


def test_paragraph_reflow_respects_extraction_boundaries() -> None:
    """Only trailing-whitespace continuations join; completed lines stay separate."""
    assert _paragraphs("Wrapped \ncontinuation\nNext paragraph.\n\nLast\t\nline.") == (
        "<p>Wrapped continuation</p><p>Next paragraph.</p><p>Last line.</p>"
    )
