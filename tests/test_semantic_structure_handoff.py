"""Offline verification tests for the immutable Task 03E.2d handoff."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import rfc8785

from er_commons.semantic_structure import SemanticContractError, verify_task03e2d_control
from er_commons.semantic_structure import handoff as handoff_module
from er_commons.semantic_structure.constants import (
    EXPECTED_AGGREGATE_DIGEST,
    EXPECTED_AUTHORIZATION_ID,
    EXPECTED_AUTHORIZED_USES,
    EXPECTED_CANDIDATE_ID,
    EXPECTED_LIMITATIONS,
    EXPECTED_SEMANTIC_COUNTS,
    EXPECTED_SEMANTIC_FILE_SET_DIGEST,
)
from er_commons.semantic_structure.policies import control as control_policy


@dataclass(frozen=True)
class HandoffFixture:
    """Paths and bytes needed to mutate one synthetic sealed handoff."""

    candidate_root: Path
    acceptance_path: Path
    managed_path: Path
    inventory_path: Path
    completion_path: Path
    comparison_path: Path


def _stable_json_bytes(value: object) -> bytes:
    """Serialize test evidence in the project's stable file representation."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _build_handoff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> HandoffFixture:
    """Create a tiny sealed tree and bind the verifier to its exact digests."""
    data_root = tmp_path / "data"
    candidate_root = (
        data_root
        / "pipelines/brisbane_baylands/task_03e2_hierarchy_correction"
        / EXPECTED_CANDIDATE_ID
    )
    records_root = candidate_root / "records"
    managed_path = candidate_root / "artifacts/example.json"
    records_root.mkdir(parents=True)
    managed_path.parent.mkdir(parents=True)
    managed_bytes = b'{"example":true}\n'
    managed_path.write_bytes(managed_bytes)

    inventory = {
        "files": [
            {
                "path": "artifacts/example.json",
                "byte_size": len(managed_bytes),
                "sha256": hashlib.sha256(managed_bytes).hexdigest(),
            }
        ]
    }
    inventory_digest = hashlib.sha256(rfc8785.dumps(inventory)).hexdigest()
    inventory_path = records_root / "artifact_inventory.json"
    inventory_path.write_bytes(_stable_json_bytes(inventory))

    completion = {
        "artifact_inventory_sha256": inventory_digest,
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "status": "complete_with_ambiguities",
    }
    completion_path = records_root / "completion_record.json"
    completion_path.write_bytes(_stable_json_bytes(completion))

    acceptance = {
        "authorization_id": EXPECTED_AUTHORIZATION_ID,
        "candidate": {
            "candidate_semantic_sha256": EXPECTED_SEMANTIC_FILE_SET_DIGEST,
            "frozen_semantic_sha256": EXPECTED_AGGREGATE_DIGEST,
            "counts": EXPECTED_SEMANTIC_COUNTS,
        },
        "limitations": list(EXPECTED_LIMITATIONS),
        "scope": {
            "authorized_uses": list(EXPECTED_AUTHORIZED_USES),
            "corpus_wide_acceptance": False,
            "physical_page_count": 222,
            "source_id": "deir_appendix_p",
        },
        "status": "accepted_with_known_limitations",
    }
    acceptance_path = tmp_path / "bounded_acceptance.json"
    acceptance_bytes = _stable_json_bytes(acceptance)
    acceptance_path.write_bytes(acceptance_bytes)
    acceptance_digest = hashlib.sha256(acceptance_bytes).hexdigest()

    comparison_path = data_root / handoff_module.PRODUCER_COMPARISON_RELATIVE_PATH
    comparison_path.parent.mkdir(parents=True)
    comparison_bytes = b'{"status":"pass"}\n'
    comparison_path.write_bytes(comparison_bytes)
    comparison_digest = hashlib.sha256(comparison_bytes).hexdigest()

    monkeypatch.setattr(handoff_module, "EXPECTED_INVENTORY_DIGEST", inventory_digest)
    monkeypatch.setattr(handoff_module, "EXPECTED_ACCEPTANCE_SHA256", acceptance_digest)
    monkeypatch.setattr(
        handoff_module,
        "EXPECTED_PRODUCER_COMPARISON_SHA256",
        comparison_digest,
    )
    expected_control = copy.deepcopy(control_policy.EXPECTED_CONTROL_FIELDS)
    expected_control["artifact_inventory_sha256"] = inventory_digest
    expected_control["bounded_acceptance_sha256"] = acceptance_digest
    expected_control["producer_comparison_sha256"] = comparison_digest
    monkeypatch.setattr(control_policy, "EXPECTED_CONTROL_FIELDS", expected_control)

    return HandoffFixture(
        candidate_root=candidate_root,
        acceptance_path=acceptance_path,
        managed_path=managed_path,
        inventory_path=inventory_path,
        completion_path=completion_path,
        comparison_path=comparison_path,
    )


def test_verified_handoff_returns_compact_control_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    control = verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)
    assert control["candidate_id"] == EXPECTED_CANDIDATE_ID
    assert control["acceptance_status"] == "accepted_with_known_limitations"
    assert control["physical_page_count"] == 222


def test_handoff_rejects_changed_managed_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    fixture.managed_path.write_bytes(b'{"example":null}\n')
    with pytest.raises(SemanticContractError, match="byte size differs|checksum differs"):
        verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)


def test_handoff_rejects_unrecorded_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    (fixture.candidate_root / ".DS_Store").write_bytes(b"unexpected")
    with pytest.raises(SemanticContractError, match="managed file set differs"):
        verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)


def test_handoff_rejects_changed_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    completion = json.loads(fixture.completion_path.read_bytes())
    completion["unexpected"] = True
    fixture.completion_path.write_bytes(_stable_json_bytes(completion))
    with pytest.raises(SemanticContractError, match="completion differs"):
        verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)


def test_handoff_rejects_changed_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    fixture.acceptance_path.write_bytes(b'{"status":"changed"}\n')
    with pytest.raises(SemanticContractError, match="bounded-acceptance bytes differ"):
        verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)


def test_handoff_rejects_changed_producer_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_handoff(tmp_path, monkeypatch)
    fixture.comparison_path.write_bytes(b'{"status":"changed"}\n')
    with pytest.raises(SemanticContractError, match="producer comparison bytes differ"):
        verify_task03e2d_control(fixture.candidate_root, fixture.acceptance_path)
