"""Behavior-oracle tests for the human-owned hierarchy rewrite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.hierarchy_correction.candidate_records import stable_json_bytes
from er_commons.hierarchy_correction.rewrite_equivalence import (
    compare_semantic_payloads,
    load_semantic_reference,
    write_equivalence_evidence,
)


def _reference(tmp_path: Path) -> Path:
    semantic = {
        "features": [{"stable_item_key": "a" * 64}],
        "toc_entries": [],
        "reconciliations": [],
        "regimes": [],
        "decisions": [],
        "hierarchy": {
            "roots": [],
            "edges": [],
            "direct_membership": [],
            "unassigned_content": [],
        },
        "ambiguities": [],
        "warnings": [],
    }
    raw = stable_json_bytes(semantic)
    root = tmp_path / "reference"
    root.mkdir()
    (root / "reference_semantic.json").write_bytes(raw)
    manifest = {
        "reference_id": "mvp-hcorv1-" + "1" * 64,
        "semantic_path": "reference_semantic.json",
        "semantic_sha256": hashlib.sha256(raw).hexdigest(),
        "source_sha256": "2" * 64,
        "config_sha256": "3" * 64,
        "policy_sha256": "4" * 64,
        "schema_sha256": "5" * 64,
    }
    (root / "reference_manifest.json").write_bytes(stable_json_bytes(manifest))
    return root


def test_exact_payload_writes_passing_no_clobber_evidence(tmp_path: Path) -> None:
    reference = load_semantic_reference(_reference(tmp_path))
    report_path = write_equivalence_evidence(
        reference=reference,
        rewritten=reference.semantic,
        rewritten_code_bundle_sha256="6" * 64,
        review_root=tmp_path / "reviews",
    )

    report = json.loads(report_path.read_bytes())
    assert report["status"] == "pass"
    assert report["first_mismatch_path"] is None
    assert report["reference_semantic_sha256"] == report["rewritten_semantic_sha256"]
    comparison_root = report_path.parent
    assert (comparison_root / "reference_semantic.json").read_bytes() == (
        comparison_root / "rewritten_semantic.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        write_equivalence_evidence(
            reference=reference,
            rewritten=reference.semantic,
            rewritten_code_bundle_sha256="6" * 64,
            review_root=tmp_path / "reviews",
        )


def test_mismatch_names_the_first_exact_path(tmp_path: Path) -> None:
    reference = load_semantic_reference(_reference(tmp_path))
    rewritten = json.loads(json.dumps(reference.semantic))
    rewritten["features"][0]["stable_item_key"] = "b" * 64

    comparison = compare_semantic_payloads(reference, rewritten)

    assert comparison.matches is False
    assert comparison.first_mismatch_path == (
        f"$semantic.features[0].stable_item_key ({'a' * 64!r} != {'b' * 64!r})"
    )


def test_reference_checksum_failure_is_actionable(tmp_path: Path) -> None:
    root = _reference(tmp_path)
    (root / "reference_semantic.json").write_text("{}\n")

    with pytest.raises(ValueError, match="rewrite reference checksum differs"):
        load_semantic_reference(root)
