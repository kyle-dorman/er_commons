"""Independent equivalence checks for the Task 03E.4 human-owned rewrite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from er_commons.semantic_materialization.comparison import compare_baseline_collections
from er_commons.semantic_materialization.reference import (
    compare_reference_candidate,
    write_comparison_report,
)

CONFIG_PATH = "configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json"
MVP_CONFIG_SHA256 = "cf2bcd52da018581c92af059191229ff3602a920d64cba3fa7ee4cbf743871d6"
REWRITE_CONFIG_SHA256 = "fb26c518ae817814608897d34fd65489777c5db553fdc6e871a10196842607bc"


def test_reference_comparison_ignores_only_declared_identity_derivatives(tmp_path: Path) -> None:
    """Candidate IDs and derived terminal digests do not hide semantic changes."""
    reference_id = "exv1-" + "a" * 64
    candidate_id = "exv1-" + "b" * 64
    reference_root = tmp_path / "reference"
    candidate_root = tmp_path / "candidate"
    reference_review = tmp_path / "reference-review"
    candidate_review = tmp_path / "candidate-review"
    _write_candidate(
        reference_root, reference_id, text="unchanged", config_sha256=MVP_CONFIG_SHA256
    )
    _write_candidate(
        candidate_root, candidate_id, text="unchanged", config_sha256=REWRITE_CONFIG_SHA256
    )
    _write_review(reference_review, reference_id)
    _write_review(candidate_review, candidate_id)

    comparison = compare_reference_candidate(
        reference_root=reference_root,
        candidate_root=candidate_root,
        reference_review_root=reference_review,
        candidate_review_root=candidate_review,
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
    )

    assert comparison.status == "equivalent"

    _write_jsonl(
        candidate_root / "canonical" / "blocks.jsonl",
        [{"id": f"{candidate_id}/block/source/blk000001", "text": "changed"}],
    )
    changed = compare_reference_candidate(
        reference_root=reference_root,
        candidate_root=candidate_root,
        reference_review_root=reference_review,
        candidate_review_root=candidate_review,
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
    )

    assert changed.status == "different"
    assert changed.mismatches[0]["path"] == "canonical/blocks.jsonl"


def test_reference_comparison_rejects_undeclared_configuration(tmp_path: Path) -> None:
    """Only the frozen lifecycle-only configuration transition is normalized."""
    reference_id = "exv1-" + "a" * 64
    candidate_id = "exv1-" + "b" * 64
    _write_candidate(
        tmp_path / "reference",
        reference_id,
        text="unchanged",
        config_sha256=MVP_CONFIG_SHA256,
    )
    _write_candidate(
        tmp_path / "candidate",
        candidate_id,
        text="unchanged",
        config_sha256="9" * 64,
    )
    _write_review(tmp_path / "reference-review", reference_id)
    _write_review(tmp_path / "candidate-review", candidate_id)

    with pytest.raises(ValueError, match="undeclared configuration"):
        compare_reference_candidate(
            reference_root=tmp_path / "reference",
            candidate_root=tmp_path / "candidate",
            reference_review_root=tmp_path / "reference-review",
            candidate_review_root=tmp_path / "candidate-review",
            reference_candidate_id=reference_id,
            candidate_id=candidate_id,
        )


def test_reference_comparison_keeps_unaffected_support_preimages_bound(tmp_path: Path) -> None:
    """Only the two scalar-ID correction roles are normalized from identity."""
    reference_id = "exv1-" + "a" * 64
    candidate_id = "exv1-" + "b" * 64
    _write_candidate(
        tmp_path / "reference",
        reference_id,
        text="unchanged",
        config_sha256=MVP_CONFIG_SHA256,
    )
    _write_candidate(
        tmp_path / "candidate",
        candidate_id,
        text="unchanged",
        config_sha256=REWRITE_CONFIG_SHA256,
    )
    _write_review(tmp_path / "reference-review", reference_id)
    _write_review(tmp_path / "candidate-review", candidate_id)
    identity_path = tmp_path / "candidate" / "records" / "extraction_identity.json"
    identity = json.loads(identity_path.read_bytes())
    identity["semantic_contract"]["support_preimage_sha256s"]["cross_producer_bridge"] = "9" * 64
    _write_json(identity_path, identity)

    comparison = compare_reference_candidate(
        reference_root=tmp_path / "reference",
        candidate_root=tmp_path / "candidate",
        reference_review_root=tmp_path / "reference-review",
        candidate_review_root=tmp_path / "candidate-review",
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
    )

    assert comparison.status == "different"
    assert comparison.mismatches[0]["path"] == "records/extraction_identity.json"


def test_comparison_report_records_all_hashes_counts_and_stable_identity(tmp_path: Path) -> None:
    """Successful comparisons remain auditable without timing-based report churn."""
    reference_id = "exv1-" + "a" * 64
    candidate_id = "exv1-" + "b" * 64
    _write_candidate(
        tmp_path / "reference",
        reference_id,
        text="unchanged",
        config_sha256=MVP_CONFIG_SHA256,
    )
    _write_candidate(
        tmp_path / "candidate",
        candidate_id,
        text="unchanged",
        config_sha256=REWRITE_CONFIG_SHA256,
    )
    _write_review(tmp_path / "reference-review", reference_id)
    _write_review(tmp_path / "candidate-review", candidate_id)
    comparison = compare_reference_candidate(
        reference_root=tmp_path / "reference",
        candidate_root=tmp_path / "candidate",
        reference_review_root=tmp_path / "reference-review",
        candidate_review_root=tmp_path / "candidate-review",
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
    )

    report_path = write_comparison_report(tmp_path / "reports", comparison)
    report = json.loads(report_path.read_bytes())
    repeated = write_comparison_report(
        tmp_path / "reports",
        type(comparison)(
            **{
                **comparison.__dict__,
                "elapsed_seconds": comparison.elapsed_seconds + 1.0,
            }
        ),
    )

    assert repeated == report_path
    assert report["counts"] == {
        "candidate_files": 5,
        "review_files": 3,
        "candidate_mismatches": 0,
        "review_mismatches": 0,
    }
    assert all(item["reference_sha256"] for item in report["candidate_files"])
    assert all(item["candidate_sha256"] for item in report["review_files"])
    assert report["timings_seconds"]["comparison"] >= 0


def test_baseline_normalization_ignores_declared_fields_only_at_record_root() -> None:
    """Nested provenance fields cannot disappear under top-level extension policy."""
    candidate_id = "exv1-" + "a" * 64
    baseline = {
        "blocks": [
            {
                "id": f"{candidate_id}/block/source/blk000001",
                "section_id": "old-top-level-section",
                "raw_links": [{"section_id": "preserved-provenance"}],
            }
        ]
    }
    candidate = {
        "blocks": [
            {
                "id": f"{candidate_id}/block/source/blk000001",
                "section_id": "new-top-level-section",
                "raw_links": [{"section_id": "changed-provenance"}],
            }
        ]
    }

    result = compare_baseline_collections(
        baseline,
        candidate,
        baseline_candidate_id=candidate_id,
        new_candidate_id=candidate_id,
    )

    assert result["undeclared_difference_count"] == 1


def _write_candidate(root: Path, candidate_id: str, *, text: str, config_sha256: str) -> None:
    _write_json(
        root / "records" / "extraction_identity.json",
        {
            "extraction_id": candidate_id,
            "identity_sha256": candidate_id.removeprefix("exv1-"),
            "semantic_contract": {
                "owned_code_bundle_sha256": "c" * 64,
                "configuration": {"path": CONFIG_PATH, "sha256": config_sha256},
                "support_preimage_sha256s": {
                    "cross_producer_bridge": "1" * 64,
                    "candidate_correspondence": candidate_id.removeprefix("exv1-"),
                    "baseline_preservation": candidate_id.removeprefix("exv1-"),
                    "bounded_control_verification": "2" * 64,
                },
            },
        },
    )
    _write_jsonl(
        root / "canonical" / "blocks.jsonl",
        [{"id": f"{candidate_id}/block/source/blk000001", "text": text}],
    )
    _write_json(
        root / "records" / "manifest.json",
        {
            "extraction_id": candidate_id,
            "identity_sha256": candidate_id.removeprefix("exv1-"),
            "record_files": [{"path": "canonical/blocks.jsonl", "sha256": "e" * 64}],
        },
    )
    _write_json(
        root / "records" / "artifact_inventory.json",
        {"files": [{"path": "canonical/blocks.jsonl", "sha256": "f" * 64}]},
    )
    _write_json(
        root / "records" / "completion_record.json",
        {"extraction_id": candidate_id, "artifact_inventory_sha256": "0" * 64},
    )


def _write_review(root: Path, candidate_id: str) -> None:
    overlay = root / "semantic-overlay-p00002.png"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_bytes(b"same overlay pixels")
    _write_json(
        root / "diagnostic-p00002.json",
        {"record_id": f"{candidate_id}/block/source/blk000001"},
    )
    _write_json(
        root / "review_manifest.json",
        {
            "candidate_id": candidate_id,
            "pages": [
                {
                    "overlay": {
                        "path": overlay.name,
                        "sha256": hashlib.sha256(overlay.read_bytes()).hexdigest(),
                    },
                    "diagnostic": {"path": "diagnostic-p00002.json", "sha256": candidate_id},
                }
            ],
        },
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values))
