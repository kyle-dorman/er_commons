"""Offline calibration integrity checks using invented source text only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons import point_grounding_panel as panel


def _digest(data: bytes) -> str:
    """Match the published SHA-256 convention."""
    return hashlib.sha256(data).hexdigest()


def _build_panel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build an invented panel with the production shape and isolated trust anchors."""
    root = tmp_path / "panel"
    (root / "payloads").mkdir(parents=True)
    files: dict[str, Any] = {}
    selected, inputs, labels = [], [], []
    cases = sorted(panel.DEVELOPMENT_CASES)
    for index in range(36):
        case = cases[index % len(cases)]
        candidate = f"G-{case}-{index:03d}"
        packet = {
            "question": "How many homes?",
            "point_text": "There are three homes.",
            "evidence": [
                {
                    "occurrence_id": f"{case}-S001",
                    "source_id": "invented",
                    "full_source_text": "Homes: 3.\nFootnote: estimated.",
                    "tables": [{"headers": ["Homes"], "rows": [["3"]]}],
                }
            ],
        }
        data = json.dumps(packet).encode()
        relative = f"payloads/{candidate}.json"
        (root / relative).write_bytes(data)
        files[relative] = {"sha256": _digest(data), "byte_size": len(data)}
        entry = {
            "candidate_id": candidate,
            "payload_path": str(root / relative),
            "payload_sha256": _digest(data),
        }
        inputs.append(entry)
        selected.append(
            {
                **entry,
                "case_id": case,
                "point_text_sha256": _digest(packet["point_text"].encode()),
                "evidence_sha256": _digest(
                    json.dumps(
                        packet["evidence"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ),
            }
        )
        labels.append({"candidate_id": candidate, "expected_supported": index < 19})
    for name, rows in [("inputs.jsonl", inputs), ("labels.jsonl", labels)]:
        data = "\n".join(json.dumps(row) for row in rows).encode()
        (root / name).write_bytes(data)
        files[name] = {"sha256": _digest(data), "byte_size": len(data)}
    selection = json.dumps({"selection": selected}).encode()
    completion = json.dumps({"files": files}).encode()
    (root / "selection.json").write_bytes(selection)
    (root / "completion.json").write_bytes(completion)
    monkeypatch.setattr(panel, "LOCKED_SELECTION_SHA256", _digest(selection))
    monkeypatch.setattr(panel, "LOCKED_COMPLETION_SHA256", _digest(completion))
    pointer = tmp_path / "pointer.json"
    pointer.write_text(
        json.dumps(
            {
                "status": "accepted_and_locked_for_development_calibration",
                "release_id": "task09f_20261014_v2",
                "panels": {"g": {"artifact_root": str(root)}},
            }
        )
    )
    return pointer


def test_panel_preserves_owned_sources_and_separates_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Model packets retain table/text bytes but cannot contain scorer labels."""
    pointer = _build_panel(tmp_path, monkeypatch)
    samples, labels, provenance = panel.load_panel(pointer)
    assert len(samples) == 36
    assert sum(labels.values()) == 19
    assert {s["case_id"] for s in samples} == panel.DEVELOPMENT_CASES
    for sample in samples:
        packet = sample["packet"]
        assert set(packet) == {"question", "point_text", "evidence"}
        original = json.loads(
            (tmp_path / "panel/payloads" / f"{sample['sample_id']}.json").read_text()
        )
        assert packet == original
        assert "expected_supported" not in json.dumps(sample)
    assert provenance["scope"] == "locked_36_point_development_calibration"


@pytest.mark.parametrize(
    "artifact",
    [
        "selection.json",
        "completion.json",
        "labels.jsonl",
        "inputs.jsonl",
        "payloads/G-C001-000.json",
    ],
)
def test_artifact_mutation_fails_before_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact: str,
) -> None:
    """Any change to a locked payload or sidecar fails closed."""
    pointer = _build_panel(tmp_path, monkeypatch)
    path = tmp_path / "panel" / artifact
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="integrity mismatch"):
        panel.load_panel(pointer)


def test_missing_valid_payload_is_evaluator_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing selected source is never mislabeled unsupported."""
    pointer = _build_panel(tmp_path, monkeypatch)
    (tmp_path / "panel/payloads/G-C001-000.json").unlink()
    with pytest.raises(ValueError, match="evaluator artifact loading error"):
        panel.load_panel(pointer)


def test_payload_symlink_cannot_escape_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not follow manifest payloads outside the accepted selected directory."""
    pointer = _build_panel(tmp_path, monkeypatch)
    path = tmp_path / "panel/payloads/G-C001-000.json"
    outside = tmp_path / "outside.json"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes selected panel"):
        panel.load_panel(pointer)
