"""Offline full-development loading checks with invented evidence and sealed fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons import point_grounding_development as development
from er_commons import point_grounding_inspect as native
from er_commons import point_grounding_panel as panel


def _seal(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reseal synthetic publications so structural checks are tested beyond checksums."""
    inventory = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "completion.json":
            data = path.read_bytes()
            inventory.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "byte_size": len(data),
                }
            )
    data = json.dumps(
        {
            "status": "complete",
            "release_id": "task09f_20261014_v2",
            "development_ids": sorted(panel.DEVELOPMENT_CASES),
            "inventory": inventory,
        }
    ).encode()
    (root / "completion.json").write_bytes(data)
    monkeypatch.setattr(development, "LOCKED_COMPLETION_SHA256", hashlib.sha256(data).hexdigest())


@pytest.fixture
def pool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Build production-sized invented inputs with separate reviews and four nulls."""
    root = tmp_path / "pool"
    (root / "payloads").mkdir(parents=True)
    cases = sorted(panel.DEVELOPMENT_CASES)
    rows: list[dict[str, Any]] = []
    reviews = []
    selected = []
    labels = {}
    ids = [f"G-{cases[i % 19]}-{i + 100:03d}" for i in range(611)] + sorted(
        development.UNRESOLVED_IDS
    )
    for i, sid in enumerate(ids):
        case = sid.split("-")[1]
        expected = i < 247 if i < 611 else None
        packet = {
            "question": "How many trees?",
            "point_text": f"There are {i} trees.",
            "evidence": [
                {
                    "occurrence_id": f"{case}-S001",
                    "source_id": "invented",
                    "canonical_target": {"section_id": "s1"},
                    "title": "Trees",
                    "full_source_text": "Invented tree inventory.\nFootnote: estimate.",
                    "physical_pages": [1],
                    "tables": [{"header": ["Trees"], "rows": [[str(i)]]}],
                }
            ],
        }
        data = json.dumps(packet).encode()
        relative = f"payloads/{sid}.json"
        (root / relative).write_bytes(data)
        rows.append(
            {
                "candidate_id": sid,
                "case_id": case,
                "eligible_for_future_calibration": i < 611,
                "payload_path": relative,
                "payload_sha256": hashlib.sha256(data).hexdigest(),
                "point_text_sha256": hashlib.sha256(packet["point_text"].encode()).hexdigest(),
                "evidence_sha256": development._digest(packet["evidence"]),
                "citation_ids": [f"{case}-S001"],
                "mechanisms": ["number"],
                "role": "supporting_point",
            }
        )
        reviews.append(
            {
                "candidate_id": sid,
                "proposed_supported": expected,
                "author_proposed_supported": expected,
                "human_approved": False,
                "review": {
                    "candidate_id": sid,
                    "author": "author_a",
                    "reviewer": "reviewer_b",
                    "reviewed_supported": expected,
                    "disposition": "agree" if i < 611 else "unresolved",
                    "rationale": "Invented review.",
                },
            }
        )
        if i < 36:
            selected.append({"sample_id": sid, "packet": packet})
            labels[sid] = expected
    for name, content in [("candidates.jsonl", rows), ("labels_reviews.jsonl", reviews)]:
        (root / name).write_text("\n".join(json.dumps(r) for r in content))
    (root / "validation.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "errors": [],
                **dict.fromkeys(
                    [
                        "development_only",
                        "source_fidelity_and_ownership",
                        "label_separation",
                        "original_reference_hashes_verified",
                        "no_test_or_reserved_case_content_loaded",
                    ],
                    True,
                ),
            }
        )
    )
    _seal(root, monkeypatch)
    monkeypatch.setattr(panel, "load_panel", lambda: (selected, labels, {"scope": "invented"}))
    pointer = tmp_path / "pointer.json"
    pointer.write_text(
        json.dumps(
            {"status": "complete", "release_id": "task09f_20261014_v2", "artifact_root": str(root)}
        )
    )
    return pointer, root


def test_full_pool_keeps_payloads_and_excludes_only_unresolved(pool: tuple[Path, Path]) -> None:
    """All611 including overlap reach scoring; only four frozen null labels are excluded."""
    pointer, root = pool
    samples, labels, provenance = development.load_development(pointer)
    assert len(samples) == 611 and sum(labels.values()) == 247
    assert sum(s["metadata"]["calibration_overlap"] for s in samples) == 36
    assert {r["sample_id"] for r in provenance["excluded_unresolved"]} == development.UNRESOLVED_IDS
    assert provenance["label_status"] == "independently_reviewed_agent_proposals_not_human_gold"
    for sample in samples:
        assert sample["packet"] == json.loads(
            (root / f"payloads/{sample['sample_id']}.json").read_text()
        )
        assert set(sample["packet"]) == {"question", "point_text", "evidence"}
        assert "proposed_supported" not in json.dumps(sample)


@pytest.mark.parametrize(
    "name",
    ["completion.json", "candidates.jsonl", "labels_reviews.jsonl", "payloads/G-C001-100.json"],
)
def test_mutation_fails_before_generation(pool: tuple[Path, Path], name: str) -> None:
    """Sealed inputs, labels and completion cannot be silently changed."""
    pointer, root = pool
    path = root / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="integrity mismatch"):
        development.load_development(pointer)


@pytest.mark.parametrize(
    "attack", ["review", "eligibility", "label", "ownership", "scope", "leak", "duplicate"]
)
def test_invalid_publication_fails_closed(
    pool: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    """Publication validity and semantic label boundaries are checked independently of hashes."""
    pointer, root = pool
    name = "labels_reviews.jsonl" if attack in {"review", "label"} else "candidates.jsonl"
    rows = [json.loads(line) for line in (root / name).read_text().splitlines()]
    if attack == "review":
        rows[0]["review"]["reviewer"] = "author_a"
    elif attack == "label":
        rows[0]["proposed_supported"] = 1
    elif attack == "eligibility":
        rows[0]["eligible_for_future_calibration"] = False
    elif attack == "ownership":
        rows[0]["citation_ids"] = ["other"]
    elif attack == "scope":
        rows[0]["case_id"] = "C002"
    elif attack == "duplicate":
        rows.append(rows[0])
    else:
        path = root / rows[0]["payload_path"]
        packet = json.loads(path.read_text())
        packet["expected_supported"] = True
        data = json.dumps(packet).encode()
        path.write_bytes(data)
        rows[0]["payload_sha256"] = hashlib.sha256(data).hexdigest()
    (root / name).write_text("\n".join(json.dumps(r) for r in rows))
    _seal(root, monkeypatch)
    with pytest.raises(ValueError):
        development.load_development(pointer)


def test_full_task_uses_v3_without_label_leakage(
    pool: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Native full entry preserves separate targets and the selected v3 prompt."""
    from inspect_ai.model import get_model

    pointer, _ = pool
    frozen = development.load_development(pointer)
    monkeypatch.setattr(development, "load_development", lambda: frozen)
    monkeypatch.setattr(native, "native_model", lambda *a, **k: get_model("mockllm/model"))
    task = native.point_grounding_full()
    assert len(task.dataset) == 611
    assert task.metadata["prompt_version"] == "task09f1.grounding.point.v3"
    for sample in task.dataset:
        packet = json.loads(sample.input[1].text)
        assert set(packet) == {"question", "point_text", "evidence"}
        assert sample.target in {"yes", "no"}
