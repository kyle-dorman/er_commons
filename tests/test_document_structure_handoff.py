"""Offline verification tests for configured bounded hierarchy handoffs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.document_records.document_structure import StructureContractError, handoff

CANDIDATE_ID = "hcorv1-" + "a" * 64
BASELINE_PRODUCER_ID = "prv1-" + "b" * 64
HIERARCHY_PRODUCER_ID = "prv1-" + "c" * 64
SEMANTIC_FILE_DIGEST = "d" * 64
AGGREGATE_DIGEST = "e" * 64
COUNTS = {
    "features": 2,
    "toc_entries": 1,
    "reconciliations": 1,
    "regimes": 1,
    "decisions": 2,
    "roots": 1,
    "edges": 0,
    "direct_membership": 1,
    "unassigned_content": 0,
    "ambiguities": 0,
    "warnings": 1,
}


@dataclass(frozen=True)
class HandoffFixture:
    candidate_root: Path
    acceptance_path: Path
    policy_path: Path
    comparison_path: Path
    schema_path: Path


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> HandoffFixture:
    candidate_root = tmp_path / "data/pipelines/hierarchy" / CANDIDATE_ID
    completion = {
        "artifact_inventory_sha256": "f" * 64,
        "candidate_id": CANDIDATE_ID,
        "status": "complete_with_ambiguities",
    }
    _write_json(candidate_root / handoff.COMPLETION_RELATIVE_PATH, completion)
    acceptance_path = tmp_path / "data/review" / CANDIDATE_ID / "bounded_acceptance.json"
    _write_json(
        acceptance_path,
        {
            "authorization_id": "fixture_authorization",
            "candidate": {"counts": COUNTS},
            "limitations": ["known limitation"],
            "scope": {
                "authorized_uses": ["semantic_input"],
                "corpus_wide_acceptance": False,
                "physical_page_count": 2,
                "source_id": "fixture_source",
            },
            "status": "accepted_with_known_limitations",
        },
    )
    comparison_path = tmp_path / "data/review/comparison.json"
    _write_json(
        comparison_path,
        {
            "machine_status": "pass",
            "proofs": [
                {
                    "role": "baseline",
                    "refreshed_producer_run_id": BASELINE_PRODUCER_ID,
                    "equivalent": True,
                },
                {
                    "role": "hierarchy",
                    "refreshed_producer_run_id": HIERARCHY_PRODUCER_ID,
                    "equivalent": True,
                },
            ],
        },
    )
    policy_path = tmp_path / "project/policy.json"
    schema_path = tmp_path / "project/schema.json"
    monkeypatch.setattr(handoff, "verify_hierarchy_candidate", lambda *_args: Path("completion"))
    monkeypatch.setattr(handoff, "verify_bounded_acceptance_policy", lambda *_args: object())
    monkeypatch.setattr(
        handoff,
        "verify_bounded_acceptance",
        lambda **_kwargs: SimpleNamespace(
            candidate_semantic_sha256=SEMANTIC_FILE_DIGEST,
            frozen_semantic_sha256=AGGREGATE_DIGEST,
        ),
    )
    return HandoffFixture(
        candidate_root=candidate_root,
        acceptance_path=acceptance_path,
        policy_path=policy_path,
        comparison_path=comparison_path,
        schema_path=schema_path,
    )


def _verify(tmp_path: Path, fixture: HandoffFixture) -> dict[str, object]:
    return handoff.verify_bounded_hierarchy_control(
        data_root=tmp_path / "data",
        candidate_root=fixture.candidate_root,
        candidate_id=CANDIDATE_ID,
        hierarchy_schema_path=fixture.schema_path,
        acceptance_path=fixture.acceptance_path,
        acceptance_policy_path=fixture.policy_path,
        producer_comparison_path=fixture.comparison_path,
        baseline_producer_run_id=BASELINE_PRODUCER_ID,
        hierarchy_producer_run_id=HIERARCHY_PRODUCER_ID,
    )


def test_handoff_derives_control_from_verified_configured_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path, monkeypatch)

    control = _verify(tmp_path, fixture)

    assert control["candidate_id"] == CANDIDATE_ID
    assert control["semantic_file_set_sha256"] == SEMANTIC_FILE_DIGEST
    assert control["aggregate_semantic_sha256"] == AGGREGATE_DIGEST
    assert control["semantic_counts"] == COUNTS
    assert (
        control["bounded_acceptance_sha256"]
        == hashlib.sha256(fixture.acceptance_path.read_bytes()).hexdigest()
    )
    assert (
        control["producer_comparison_sha256"]
        == hashlib.sha256(fixture.comparison_path.read_bytes()).hexdigest()
    )


def test_handoff_rejects_comparison_for_different_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path, monkeypatch)
    comparison = json.loads(fixture.comparison_path.read_bytes())
    comparison["proofs"][0]["refreshed_producer_run_id"] = "prv1-" + "0" * 64
    _write_json(fixture.comparison_path, comparison)

    with pytest.raises(StructureContractError, match="configured lineage: baseline"):
        _verify(tmp_path, fixture)


def test_handoff_translates_hierarchy_verifier_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        handoff,
        "verify_hierarchy_candidate",
        lambda *_args: (_ for _ in ()).throw(ValueError("candidate checksum differs")),
    )

    with pytest.raises(StructureContractError, match="candidate checksum differs"):
        _verify(tmp_path, fixture)
