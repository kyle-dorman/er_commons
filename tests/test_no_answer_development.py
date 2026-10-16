"""Offline integrity, projection and uncertainty checks for the A310 development suite."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from er_commons import no_answer_development as development
from er_commons import no_answer_inspect as native


def _fixture(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Create one invented development-shaped record with sealed payload bytes."""
    packet = {"candidate_conclusion": "I cannot answer."}
    raw = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    path = root / "payloads/A-C001-A01.json"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    index = [
        {
            "candidate_id": "A-C001-A01",
            "case_id": "C001",
            "payload_path": "payloads/A-C001-A01.json",
            "payload_sha256": digest,
            "conclusion_sha256": hashlib.sha256(
                packet["candidate_conclusion"].encode()
            ).hexdigest(),
        }
    ]
    labels = [
        {
            "candidate_id": "A-C001-A01",
            "proposed_label": "clean_abstention",
            "author_uncertainty": "Review wording",
            "reviewer_uncertainty": None,
        }
    ]
    inventory = {
        "payloads/A-C001-A01.json": {
            "path": "payloads/A-C001-A01.json",
            "sha256": digest,
            "byte_size": len(raw),
        }
    }
    return index, labels, inventory


def test_fixture_preserves_uncertainty_outside_payload(tmp_path: Path) -> None:
    """Proposal and uncertainty annotations survive solely in sample metadata."""
    index, label_rows, inventory = _fixture(tmp_path)
    samples, labels = development._assemble(index, label_rows, inventory, tmp_path)
    assert labels == {"A-C001-A01": "clean_abstention"}
    assert samples[0]["label_record"] == label_rows[0]
    assert samples[0]["label_uncertain"] is True
    assert samples[0]["candidate_record"] == index[0]
    assert samples[0]["packet"] == {"candidate_conclusion": "I cannot answer."}


@pytest.mark.parametrize(
    "change",
    [
        "file",
        "canonical",
        "conclusion",
        "label",
        "missing",
        "duplicate",
        "extra",
        "heldout",
        "projection",
        "path",
    ],
)
def test_fixture_rejects_integrity_and_scope_errors(tmp_path: Path, change: str) -> None:
    """Every boundary fails before a malformed or out-of-scope sample can run."""
    index, labels, inventory = _fixture(tmp_path)
    path = tmp_path / "payloads/A-C001-A01.json"
    if change == "file":
        path.write_text("{}")
    elif change == "canonical":
        index[0]["payload_sha256"] = "0" * 64
    elif change == "conclusion":
        index[0]["conclusion_sha256"] = "0" * 64
    elif change == "label":
        labels[0]["proposed_label"] = "invalid_output"
    elif change == "missing":
        labels.clear()
    elif change == "duplicate":
        labels.append(dict(labels[0]))
    elif change == "extra":
        labels.append({**labels[0], "candidate_id": "extra"})
    elif change == "heldout":
        index[0]["case_id"] = "C002"
    elif change == "path":
        index[0]["payload_path"] = "../payloads/A-C001-A01.json"
    else:
        raw = b'{"candidate_conclusion":"I cannot answer.","expected_label":"ambiguous"}'
        path.write_bytes(raw)
        inventory["payloads/A-C001-A01.json"].update(
            sha256=hashlib.sha256(raw).hexdigest(), byte_size=len(raw)
        )
    with pytest.raises(ValueError):
        development._assemble(index, labels, inventory, tmp_path)


def test_changed_completion_pointer_rejected(tmp_path: Path) -> None:
    """Replacing the sealed publication requires an explicit implementation revision."""
    pointer = tmp_path / "pointer.json"
    pointer.write_text(json.dumps({"completion": {"sha256": "changed"}}))
    with pytest.raises(ValueError, match="pinned publication"):
        development.load_full_development(pointer)


def test_actual_full_publication_and_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """All published proposals, including uncertain cases, become exact v2 samples."""
    pointer = json.loads(
        (
            development.core.REPO / "docs/specs/task09f1_no_answer_candidates_v1_result.json"
        ).read_text()
    )
    if not Path(pointer["completion"]["path"]).exists():
        pytest.skip("External A development publication unavailable")
    samples, labels, provenance = development.load_full_development()
    assert len(samples) == len(labels) == 310
    assert Counter(labels.values()) == development.EXPECTED_COUNTS
    assert len({sample["case_id"] for sample in samples}) == 19
    assert sum(sample["label_uncertain"] for sample in samples) == 33
    assert provenance["exclusions"] == []
    assert provenance["label_status"] == "agent_reviewed_proposals_not_human_gold"
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: None)
    task = native.no_answer_full()
    assert len(task.dataset) == 310
    assert task.metadata["prompt_version"] == "task09f1.no_answer.conclusion.v2"
    for source, sample in zip(samples, task.dataset, strict=True):
        assert sample.id == source["sample_id"]
        assert sample.target == labels[sample.id]
        assert sample.metadata["label_record"] == source["label_record"]
        assert json.loads(sample.input[1].text) == source["packet"]
        assert set(json.loads(sample.input[1].text)) == {"candidate_conclusion"}
