"""Focused validation of collection-only v3 handoff closure."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from test_collection_imported_selection import _fixture

from er_commons.collection_processing import handoff_validation, handoff_validation_v3
from er_commons.collection_processing.production_identity import (
    V33_COLLECTION_OUTPUT_NAMESPACE,
)

SCOPE = "scopev1-" + "1" * 64
COLLECTION = "cprodv1-" + "2" * 64


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write(root: Path, relative: str, value: object) -> dict[str, object]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _json_bytes(value)
    path.write_bytes(content)
    return {
        "path": relative,
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _artifact_ref(data_root: Path, path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "authority": "artifact_root",
        "path": path.relative_to(data_root).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }


def _handoff_fixture(tmp_path: Path) -> dict[str, Any]:
    imported = _fixture(tmp_path, count=35)
    root = tmp_path / V33_COLLECTION_OUTPUT_NAMESPACE
    root.mkdir(parents=True)
    control_root = root.parent / "resolved_specs_v1/00_initial"
    selection_path = control_root / "imported_document_selection.json"
    selection_path.parent.mkdir(parents=True)
    selection_path.write_bytes(imported["path"].read_bytes())
    selection_ref = _artifact_ref(tmp_path, selection_path)
    identity_path = control_root / "collection_production_identity.json"
    identity_path.write_bytes(_json_bytes({"collection_production_id": COLLECTION}))
    identity_ref = _artifact_ref(tmp_path, identity_path)
    accounting = {"scope_id": SCOPE}
    target = {"index_id": "idxv1-" + "3" * 64, "unavailable_sources": []}
    resolution = {"resolution_id": "resv1-" + "4" * 64}
    handoff = {
        "handoff_id": "handoffv1-" + "5" * 64,
        "status": "ready",
        "task04_status": "not_evaluated",
    }
    attempts = []
    for stage, stage_id, directory, record in (
        ("accounting", SCOPE, "accounting", accounting),
        ("target_index", target["index_id"], "target_indexes", target),
        ("resolution", resolution["resolution_id"], "resolutions", resolution),
        ("handoff", handoff["handoff_id"], "handoffs", handoff),
    ):
        completion = _write(
            root,
            f"scopes/{SCOPE}/{directory}/{stage_id}/records/completion_record.json",
            record,
        )
        event = _write(root, f"attempts/{stage}/attempt_0001/0001.json", {"ok": True})
        attempts.append(
            {
                "schema_version": "er_commons.collection_stage_attempt.v2",
                "stage_type": stage,
                "stage_id": stage_id,
                "attempt": 1,
                "disposition": "complete",
                "failure_class": None,
                "state_event_refs": [event],
                "completion_ref": completion,
            }
        )
    bundle = {
        "schema_version": "er_commons.collection_workflow_contract.v3",
        "collection_production_id": COLLECTION,
        "imported_selection_sha256": selection_ref["sha256"],
        "collection_production_identity_ref": identity_ref,
        "imported_selection_ref": selection_ref,
        "imported_document_evidence": {
            "selection_ref": selection_ref,
            "selection_sha256": selection_ref["sha256"],
            "document_production_identity_ref": imported["manifest"][
                "document_production_identity_ref"
            ],
            "document_run_spec_ref": imported["manifest"]["document_run_spec_ref"],
            "selections": imported["manifest"]["candidates"],
        },
        "accounting": accounting,
        "target_index": target,
        "resolution_completion": resolution,
        "handoff": handoff,
        "collection_stage_attempts": attempts,
    }
    bundle_path = root / "scopes" / SCOPE / "contract_bundle.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(_json_bytes(bundle))
    schema_path = tmp_path / "schema.json"
    schema_path.write_bytes(_json_bytes({"type": "object"}))
    return {
        "root": root,
        "document_root": imported["document_root"],
        "bundle": bundle,
        "bundle_path": bundle_path,
        "schema_path": schema_path,
        "selection_path": selection_path,
    }


def _install_isolated_validators(
    monkeypatch: pytest.MonkeyPatch, fixture: dict[str, Any]
) -> list[dict[str, object]]:
    monkeypatch.setattr(handoff_validation_v3, "validate_collection_bundle", lambda *_: None)
    monkeypatch.setattr(
        handoff_validation,
        "_verify_document_candidate",
        lambda *_: pytest.fail("v3 must not invoke legacy candidate verification"),
    )
    calls: list[dict[str, object]] = []

    def validate_identity(record: dict[str, object], **kwargs: object) -> SimpleNamespace:
        calls.append({"record": record, **kwargs})
        return SimpleNamespace(collection_production_id=COLLECTION)

    monkeypatch.setattr(
        handoff_validation_v3, "validate_collection_production_identity", validate_identity
    )
    return calls


def test_v3_validates_frozen_35_candidate_selection_without_legacy_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _handoff_fixture(tmp_path)
    calls = _install_isolated_validators(monkeypatch, fixture)

    result = handoff_validation.validate_collection_handoff(
        extraction_root=fixture["root"],
        scope_id=SCOPE,
        schema_path=fixture["schema_path"],
        data_root=tmp_path,
        document_input_root=fixture["document_root"],
    )

    assert result.status == "ready"
    assert result.verified_document_count == 35
    assert result.unavailable_source_count == 0
    assert len(calls) == 1
    assert calls[0]["expected_output_namespace"] == V33_COLLECTION_OUTPUT_NAMESPACE
    expected = calls[0]["expected_imported_selection_ref"]
    assert expected.path == fixture["selection_path"].relative_to(tmp_path).as_posix()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("selection", "frozen selection"),
        ("legacy", "legacy document execution"),
        ("attempt", "did not finish successfully"),
        ("stage_id", "another stage identity"),
        ("outer_authority", "artifact-root authority"),
        ("envelope_ref", "another selection reference"),
    ],
)
def test_v3_rejects_imported_or_fresh_collection_evidence_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    fixture = _handoff_fixture(tmp_path)
    _install_isolated_validators(monkeypatch, fixture)
    bundle = deepcopy(fixture["bundle"])
    if mutation == "selection":
        bundle["imported_document_evidence"]["selections"][0]["logical_source_id"] = "drift"
    elif mutation == "legacy":
        bundle["document_attempts"] = []
    elif mutation == "attempt":
        bundle["collection_stage_attempts"][-1].update(
            disposition="cancelled", failure_class="Interrupted", completion_ref=None
        )
    elif mutation == "stage_id":
        bundle["collection_stage_attempts"][-1]["stage_id"] = "handoffv1-" + "9" * 64
    elif mutation == "outer_authority":
        bundle["imported_selection_ref"]["authority"] = "repository"
    else:
        bundle["imported_document_evidence"]["selection_ref"] = {
            **bundle["imported_document_evidence"]["selection_ref"],
            "path": "different.json",
        }
    fixture["bundle_path"].write_bytes(_json_bytes(bundle))

    with pytest.raises(ValueError, match=message):
        handoff_validation.validate_collection_handoff(
            extraction_root=fixture["root"],
            scope_id=SCOPE,
            schema_path=fixture["schema_path"],
            data_root=tmp_path,
            document_input_root=fixture["document_root"],
        )


def test_v3_requires_both_authority_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = _handoff_fixture(tmp_path)
    _install_isolated_validators(monkeypatch, fixture)

    with pytest.raises(ValueError, match="explicit data and document input roots"):
        handoff_validation.validate_collection_handoff(
            extraction_root=fixture["root"],
            scope_id=SCOPE,
            schema_path=fixture["schema_path"],
            data_root=tmp_path,
        )


def test_v3_requires_bundle_to_name_validated_collection_production_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _handoff_fixture(tmp_path)
    monkeypatch.setattr(handoff_validation_v3, "validate_collection_bundle", lambda *_: None)
    monkeypatch.setattr(
        handoff_validation_v3,
        "validate_collection_production_identity",
        lambda *_args, **_kwargs: SimpleNamespace(collection_production_id="cprodv1-" + "9" * 64),
    )

    with pytest.raises(ValueError, match="production identity differs"):
        handoff_validation.validate_collection_handoff(
            extraction_root=fixture["root"],
            scope_id=SCOPE,
            schema_path=fixture["schema_path"],
            data_root=tmp_path,
            document_input_root=fixture["document_root"],
        )
