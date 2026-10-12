"""Invented combined publications exercise selection, origin binding and frozen nesting."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from test_judge_qualification_packets import packet

from er_commons import grounding_dataset_panel as panel
from er_commons.artifact_io import json_bytes


def put(path: Path, value: Any) -> dict:
    """Save an invented object with the normal immutable file binding shape."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))
    return panel._binding(path)


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    """Build 442 invented metadata rows; only 136 eligible six-case answers have payloads."""
    root, base = tmp_path / "combined", tmp_path / "base"
    pub = root / "published"
    pub.mkdir(parents=True)
    base.mkdir()
    source = packet()
    source["reference_answer"]["conclusion"].pop("expected_score")
    source["reference_answer"].pop("synthetic_expectation")
    for case in panel.DEV6:
        put(base / "cases" / case / "input.json", {"case_id": case})
    put(base / "raw.json", {"do_not_decode": "invented provenance"})
    files = [p for p in base.rglob("*.json")]
    inv = [{**panel._binding(p), "path": p.relative_to(base).as_posix()} for p in files]
    base_binding = put(base / "completion.json", {"inventory": {"files": inv}})
    predecessor = put(tmp_path / "predecessor.json", {"batch_completion": base_binding})
    identities = {
        "source_packet_hash": "source",
        "parent_reference_hash": "parent",
        "reference_binding": {},
        "reference_version": 1,
        "release_id": "release",
        "annotation_version": "task09a2.stage_expectations.v1",
    }
    answers, expectations, origins = [], [], []
    for case, count in panel.CASE_COUNTS.items():
        for i in range(count):
            key = f"task09a2-{case}-F01-{i}"
            common = {
                "variant_id": key,
                "case_id": case,
                **identities,
                "provenance": {
                    "raw_output": {**panel._binding(base / "raw.json"), "path": "raw.json"}
                },
            }
            answers.append({**common, "answer": copy.deepcopy(source["reference_answer"])})
            expectations.append(
                {
                    **common,
                    "comparison_eligible": True,
                    "perturbation_id": "F01",
                    "grounding": {
                        "score": 1,
                        "point_expectations": [{"point_id": "O02-omission", "supported": False}],
                        "unsupported_premise_point_ids": ["O02-omission"],
                    },
                }
            )
            origins.append({"variant_id": key, "root": str(base)})
    for i in range(306):
        expectations.append(
            {"variant_id": f"other-{i}", "case_id": "C006", "comparison_eligible": i < 294}
        )
    for name, rows in [
        ("answers", answers),
        ("expectations", expectations),
        ("record_origins", origins),
    ]:
        (pub / f"{name}.jsonl").write_bytes(b"".join(json_bytes(r) for r in rows))
    put(
        pub / "reservation.json",
        {
            "development_variant_ids": [
                r["variant_id"] for r in expectations if r["comparison_eligible"]
            ],
            "excluded_variant_ids": [
                r["variant_id"] for r in expectations if not r["comparison_eligible"]
            ],
            "final_check_variant_ids": [],
        },
    )
    put(pub / "manifest.json", {"base_completion": base_binding})
    files = list(pub.iterdir())
    artifacts = {p.name: panel._binding(p) for p in files}
    inventory = [{**panel._binding(p), "path": p.relative_to(root).as_posix()} for p in files]
    completion = put(root / "completion.json", {"inventory": {"files": inventory}})
    result = tmp_path / "result.json"
    put(
        result,
        {
            "schema_version": "task09a3.final_result.v1",
            "status": "complete_with_limitations",
            "annotation_version": "task09a2.stage_expectations.v1",
            "namespace": str(root),
            "namespace_completion": completion,
            "predecessor_result": predecessor,
            "artifacts": artifacts,
        },
    )
    release = tmp_path / "release.json"
    put(release, {"status": "complete", "release_id": "release"})
    monkeypatch.setattr(
        panel, "_verify_release", lambda value: (tmp_path, {}, list(panel.DEV6), {}, release)
    )
    monkeypatch.setattr(panel, "_load_case_input", lambda *args, **kwargs: copy.deepcopy(source))
    return result, release, tmp_path / "frozen"


def test_freeze_load_nested_combined_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load all eligible variants, preserve the prefix panel and remap restricted point IDs."""
    result, release, output = fixture(tmp_path, monkeypatch)
    manifest = panel.freeze_dataset_panel(result, release, output)
    assert len(manifest["samples"]) == 136
    dev3 = panel.load_dataset_panel_samples(output / "manifest.json", "dev3")
    dev6 = panel.load_dataset_panel_samples(output / "manifest.json", "dev6")
    extra = panel.load_dataset_panel_samples(output / "manifest.json", "dev6_additions")
    assert len(dev3) == 69 and len(dev6) == 136 and len(extra) == 67
    assert dev6 == dev3 + extra and all(not s["control"] for s in dev6)
    assert dev3[0]["stage_expectations"]["point_expectations"][0]["point_id"] == "P2"
    assert dev3[0]["stage_expectations"]["unsupported_premise_point_ids"] == ["P2"]
    assert "point_expectations" not in json.dumps(dev3[0]["packet"]["payload"])
    assert panel.freeze_dataset_panel(result, release, output) == manifest


def test_combined_artifact_tampering_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Input bytes must match both the publication pointer and sealed inventory."""
    result, release, output = fixture(tmp_path, monkeypatch)
    (tmp_path / "combined/published/answers.jsonl").write_text("{}\n")
    with pytest.raises(ValueError):
        panel.freeze_dataset_panel(result, release, output)
    assert not output.exists()


def test_origin_relative_provenance_tampering_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Relative provenance resolves against its original root and verifies exact bytes."""
    result, release, output = fixture(tmp_path, monkeypatch)
    (tmp_path / "base/raw.json").write_text("{}")
    with pytest.raises(ValueError):
        panel.freeze_dataset_panel(result, release, output)
    assert not output.exists()


def test_frozen_panel_rejects_wrong_nesting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Panel lists cannot drop an old Dev3 answer from the Dev6 continuation."""
    result, release, output = fixture(tmp_path, monkeypatch)
    manifest = panel.freeze_dataset_panel(result, release, output)
    manifest["panels"]["dev6"].pop(0)
    put(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match="nesting"):
        panel.load_dataset_panel_samples(output / "manifest.json", "dev6")


def test_eligibility_requires_reservation_membership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A proposal's eligible flag cannot bypass the sealed development membership gate."""
    fixture(tmp_path, monkeypatch)
    root = tmp_path / "combined/published"
    reservation = json.loads((root / "reservation.json").read_text())
    allowed = set(reservation["development_variant_ids"])
    allowed.pop()
    with pytest.raises(ValueError, match="reservation"):
        panel._eligible_metadata(root / "expectations.jsonl", allowed)


def test_restricted_stage_ids_remain_original_on_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Remapping is a load-time copy; original expectation provenance stays untouched."""
    result, release, output = fixture(tmp_path, monkeypatch)
    panel.freeze_dataset_panel(result, release, output)
    original = (output / "restricted_expectations.json").read_bytes()
    panel.load_dataset_panel_samples(output / "manifest.json", "dev3")
    assert original == (output / "restricted_expectations.json").read_bytes()
    expected = json.loads(original)[0]["expectation"]
    assert expected["grounding"]["point_expectations"][0]["point_id"] == "O02-omission"
