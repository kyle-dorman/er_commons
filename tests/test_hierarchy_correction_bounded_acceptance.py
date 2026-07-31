"""Focused tests for candidate-bound Appendix P acceptance evidence."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import er_commons.hierarchy_correction.bounded_acceptance as acceptance
from er_commons.hierarchy_correction.bounded_acceptance import (
    AcceptanceEvidence,
    BoundedAcceptanceConfig,
    SemanticCounts,
    VerifiedBoundedAcceptancePolicy,
    assemble_bounded_acceptance,
    load_bounded_acceptance_config,
    semantic_counts,
    verify_bounded_acceptance,
)
from er_commons.hierarchy_correction.candidate_records import (
    JSONL_PATHS,
    stable_json_bytes,
    stable_jsonl_bytes,
)
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.quality_gate import SEMANTIC_PATHS

ROOT = Path(__file__).parents[1]
CONFIG_PATH = ROOT / "configs/brisbane_baylands_2025_deir_task03e2d_bounded_acceptance_v1.json"
FIXTURE_PATH = ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1/valid_bundle.json"


def test_checked_in_policy_freezes_status_scope_limitations_and_counts() -> None:
    config, digest = load_bounded_acceptance_config(CONFIG_PATH)

    assert config.status == "accepted_with_known_limitations"
    assert config.scope.corpus_wide_acceptance is False
    assert config.limitations == acceptance.LIMITATIONS
    assert config.expected_counts.model_dump() == acceptance.EXPECTED_COUNTS
    assert len(digest) == 64

    raw = json.loads(CONFIG_PATH.read_bytes())
    for field, changed in (
        ("status", "pass"),
        ("limitations", raw["limitations"][:-1]),
    ):
        tampered = copy.deepcopy(raw)
        tampered[field] = changed
        with pytest.raises(ValidationError):
            BoundedAcceptanceConfig.model_validate(tampered)
    tampered = copy.deepcopy(raw)
    tampered["scope"]["corpus_wide_acceptance"] = True
    with pytest.raises(ValidationError):
        BoundedAcceptanceConfig.model_validate(tampered)


def test_policy_evidence_verifier_rejects_changed_report_bytes(tmp_path: Path) -> None:
    def write(relative: str, value: object) -> tuple[str, str]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = stable_json_bytes(value)
        path.write_bytes(raw)
        return relative, hashlib.sha256(raw).hexdigest()

    annotations = {"annotations": "frozen"}
    annotation_path, annotation_sha = write("review/held_out_annotations.json", annotations)
    render_path, render_sha = write("review/preparation/render_manifest.json", {"pages": []})
    seal = {
        "candidate_id": acceptance.HISTORICAL_CANDIDATE_ID,
        "status": "sealed",
        "annotations_path": Path(annotation_path).name,
        "annotations_file_sha256": annotation_sha,
        "annotation_bundle_sha256": canonical_json_sha256(annotations),
        "render_manifest_path": Path(render_path).relative_to("review").as_posix(),
        "render_manifest_sha256": render_sha,
    }
    seal_path, seal_sha = write("review/held_out_annotations.seal.json", seal)
    report_items = []
    for name, status in (
        ("development", "reject"),
        ("held_out", "reject"),
        ("controls", "pass"),
    ):
        relative, digest = write(f"review/reports/{name}.json", {"status": status})
        report_items.append(
            {
                "name": name,
                "path": Path(relative).name,
                "sha256": digest,
                "status": status,
            }
        )
    manifest_path, manifest_sha = write(
        "review/reports/quality_report_manifest.json",
        {"status": "reject", "reports": report_items},
    )
    attempt_path, attempt_sha = write(
        "attempt/attempt_record.json",
        {"candidate_id": acceptance.HISTORICAL_CANDIDATE_ID, "status": "failed"},
    )
    semantic_raw = stable_json_bytes({"semantic": "fixture"})
    semantic_sha = hashlib.sha256(semantic_raw).hexdigest()
    semantic_paths = (
        "mvp/reference_semantic.json",
        "comparison/reference_semantic.json",
        "comparison/rewritten_semantic.json",
    )
    semantic_bindings = []
    for relative in semantic_paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(semantic_raw)
        semantic_bindings.append((relative, semantic_sha))
    counts = acceptance.EXPECTED_COUNTS
    reference_path, reference_sha = write(
        "mvp/reference_manifest.json",
        {"semantic_sha256": semantic_sha, "counts": counts},
    )
    equivalence_path, equivalence_sha = write(
        "comparison/equivalence_report.json",
        {
            "status": "pass",
            "reference_semantic_sha256": semantic_sha,
            "rewritten_semantic_sha256": semantic_sha,
            "counts": counts,
        },
    )
    offline_path, offline_sha = write("comparison/offline.json", {"status": "pass"})
    evidence = AcceptanceEvidence.model_validate(
        {
            "historical_held_out_seal": {"path": seal_path, "sha256": seal_sha},
            "historical_quality_report_manifest": {
                "path": manifest_path,
                "sha256": manifest_sha,
            },
            "historical_failed_attempt": {"path": attempt_path, "sha256": attempt_sha},
            "post_03e2a_reference_manifest": {
                "path": reference_path,
                "sha256": reference_sha,
            },
            "post_03e2a_reference_semantic": {
                "path": semantic_bindings[0][0],
                "sha256": semantic_bindings[0][1],
            },
            "task_03e2b_equivalence_report": {
                "path": equivalence_path,
                "sha256": equivalence_sha,
            },
            "task_03e2b_reference_semantic": {
                "path": semantic_bindings[1][0],
                "sha256": semantic_bindings[1][1],
            },
            "task_03e2b_rewritten_semantic": {
                "path": semantic_bindings[2][0],
                "sha256": semantic_bindings[2][1],
            },
            "task_03e2b_offline_candidate_report": {
                "path": offline_path,
                "sha256": offline_sha,
            },
        }
    )
    checked, _digest = load_bounded_acceptance_config(CONFIG_PATH)
    synthetic = checked.model_copy(
        update={"expected_semantic_sha256": semantic_sha, "evidence": evidence}
    )

    acceptance._verify_bounded_acceptance_evidence(synthetic, tmp_path)
    (tmp_path / "review/reports/development.json").write_bytes(
        stable_json_bytes({"status": "pass"})
    )

    with pytest.raises(ValueError, match="historical quality report differs"):
        acceptance._verify_bounded_acceptance_evidence(synthetic, tmp_path)


def _write_candidate(root: Path) -> tuple[str, dict[str, object]]:
    fixture = json.loads(FIXTURE_PATH.read_bytes())
    identity = fixture["identity"]
    (root / "records").mkdir(parents=True)
    (root / "records/identity.json").write_bytes(stable_json_bytes(identity))
    values = {
        "artifacts/item_features.jsonl": fixture["features"],
        "artifacts/visible_toc_entries.jsonl": fixture["toc_entries"],
        "artifacts/toc_reconciliation.jsonl": fixture["reconciliations"],
        "artifacts/regimes.jsonl": fixture["regimes"],
        "artifacts/decisions.jsonl": fixture["decisions"],
        "artifacts/hierarchy.json": fixture["hierarchy"],
        "artifacts/ambiguities.jsonl": fixture["ambiguities"],
        "artifacts/warnings.jsonl": fixture["warnings"],
    }
    for relative in SEMANTIC_PATHS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        value = values[relative]
        path.write_bytes(
            stable_jsonl_bytes(value) if relative in JSONL_PATHS else stable_json_bytes(value)
        )
    return identity["candidate_id"], fixture


def test_authorization_is_no_clobber_and_fails_for_semantic_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_root = tmp_path / "candidate"
    candidate_id, _fixture = _write_candidate(candidate_root)
    payload = acceptance.semantic_payload(candidate_root)
    frozen_digest = hashlib.sha256(stable_json_bytes(payload)).hexdigest()
    checked_config, _digest = load_bounded_acceptance_config(CONFIG_PATH)
    synthetic_config = checked_config.model_copy(
        update={
            "expected_semantic_sha256": frozen_digest,
            "expected_counts": SemanticCounts.model_validate(semantic_counts(payload)),
        }
    )
    policy = VerifiedBoundedAcceptancePolicy(CONFIG_PATH, synthetic_config, "a" * 64)
    monkeypatch.setattr(acceptance, "verify_bounded_acceptance_policy", lambda *_args: policy)
    path = tmp_path / "review" / candidate_id / "bounded_acceptance.json"

    verified = assemble_bounded_acceptance(
        path=path,
        policy=policy,
        candidate_root=candidate_root,
        candidate_id=candidate_id,
        data_root=tmp_path,
    )

    assert verified.frozen_semantic_sha256 == frozen_digest
    assert json.loads(path.read_bytes())["status"] == "accepted_with_known_limitations"
    with pytest.raises(FileExistsError):
        assemble_bounded_acceptance(
            path=path,
            policy=policy,
            candidate_root=candidate_root,
            candidate_id=candidate_id,
            data_root=tmp_path,
        )

    feature_path = candidate_root / SEMANTIC_PATHS[0]
    original = feature_path.read_bytes()
    feature_path.write_bytes(original + original.splitlines(keepends=True)[0])
    with pytest.raises(ValueError, match="candidate binding differs"):
        verify_bounded_acceptance(
            path=path,
            policy=policy,
            candidate_root=candidate_root,
            candidate_id=candidate_id,
            data_root=tmp_path,
        )
    feature_path.write_bytes(original)

    original_record = json.loads(path.read_bytes())
    mutations = []
    wrong_candidate = copy.deepcopy(original_record)
    wrong_candidate["candidate"]["identity"]["candidate_id"] = "hcorv1-" + "f" * 64
    mutations.append(wrong_candidate)
    missing_limitation = copy.deepcopy(original_record)
    missing_limitation["limitations"] = missing_limitation["limitations"][:-1]
    mutations.append(missing_limitation)
    wrong_status = copy.deepcopy(original_record)
    wrong_status["status"] = "pass"
    mutations.append(wrong_status)
    wrong_scope = copy.deepcopy(original_record)
    wrong_scope["scope"]["corpus_wide_acceptance"] = True
    mutations.append(wrong_scope)
    wrong_evidence = copy.deepcopy(original_record)
    wrong_evidence["evidence"]["historical_held_out_seal"]["sha256"] = "f" * 64
    mutations.append(wrong_evidence)
    for mutation in mutations:
        path.write_bytes(stable_json_bytes(mutation))
        with pytest.raises((ValueError, ValidationError)):
            verify_bounded_acceptance(
                path=path,
                policy=policy,
                candidate_root=candidate_root,
                candidate_id=candidate_id,
                data_root=tmp_path,
            )
