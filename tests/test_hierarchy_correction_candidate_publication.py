"""Focused candidate serialization and publication tests for Task 03E.2."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema.exceptions import ValidationError

from er_commons.hierarchy_correction.candidate_publication import (
    publish_workspace,
    reserve_workspace,
    retain_failed_attempt,
    reuse_completed_candidate,
    verify_completed_candidate,
    write_validate_and_seal_candidate,
)
from er_commons.hierarchy_correction.candidate_records import (
    CandidateMeasurements,
    CandidatePayload,
    _stabilize_terminal_records,
    build_attempt_record,
    build_metrics,
    build_summary,
    prepare_candidate,
    stable_json_bytes,
)
from er_commons.hierarchy_correction.constants import (
    FATAL_CODES,
    MANAGED_PAYLOAD_PATHS,
)
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.errors import HierarchyCorrectionContractError
from er_commons.hierarchy_correction.publication_authorization import (
    SEMANTIC_PATHS,
    VerifiedMachinePublication,
    candidate_semantic_sha256,
)

ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json"
FIXTURE_PATH = ROOT / "benchmarks/er_bench/fixtures/hierarchy_correction/v1/valid_bundle.json"


def _fixture_bundle() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text())


def _payload(bundle: dict[str, Any] | None = None) -> CandidatePayload:
    source = copy.deepcopy(bundle or _fixture_bundle())
    return CandidatePayload(
        identity=source["identity"],
        input_inventory=source["input_inventory"],
        environment={"python_version": "3.13.5", "platform": "fixture"},
        features=tuple(source["features"]),
        toc_entries=tuple(source["toc_entries"]),
        reconciliations=tuple(source["reconciliations"]),
        regimes=tuple(source["regimes"]),
        decisions=tuple(source["decisions"]),
        hierarchy=source["hierarchy"],
        ambiguities=tuple(source["ambiguities"]),
        warnings=tuple(source["warnings"]),
    )


def _measurements() -> CandidateMeasurements:
    fixture = _fixture_bundle()["metrics"]
    return CandidateMeasurements(
        build_wall_time_seconds=fixture["build_wall_time_seconds"],
        stage_wall_time_seconds=fixture["stage_wall_time_seconds"],
        peak_rss_bytes=fixture["peak_rss_bytes"],
        input_bytes=fixture["input_bytes"],
        producer_build_wall_time_seconds=fixture["producer_build_wall_time_seconds"],
        producer_bytes=fixture["producer_bytes"],
    )


def _gate(workspace: Any) -> VerifiedMachinePublication:
    return VerifiedMachinePublication(
        candidate_id=workspace.final_root.name,
        candidate_semantic_sha256=candidate_semantic_sha256(workspace.staging_root),
    )


def test_candidate_semantic_digest_preserves_accepted_checksum_contract(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    records = []
    for index, relative in enumerate(SEMANTIC_PATHS, start=1):
        path = candidate / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"semantic-{index}\n".encode())
        records.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )

    assert candidate_semantic_sha256(candidate) == canonical_json_sha256(
        {"semantic_files": records}
    )


def test_summary_and_metrics_are_derived_from_owned_records() -> None:
    payload = _payload()
    summary = build_summary(payload)
    metrics = build_metrics(
        candidate_id=payload.identity["candidate_id"],
        measurements=_measurements(),
        artifact_bytes=10_000,
    )

    assert summary == _fixture_bundle()["summary"]
    assert metrics["build_wall_time_seconds"] == 1.1
    assert metrics["artifact_bytes_ratio"] == 0.01
    assert metrics["cheap_relative_to_producer"] is True


def test_preparation_is_deterministic_and_counts_all_15_final_files() -> None:
    first = prepare_candidate(
        payload=_payload(),
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    second = prepare_candidate(
        payload=_payload(),
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )

    assert first.managed_bytes == second.managed_bytes
    inventory = first.bundle["artifact_inventory"]
    assert [item["path"] for item in inventory["files"]] == list(MANAGED_PAYLOAD_PATHS)
    assert first.bundle["metrics"]["artifact_bytes"] == (
        sum(item["byte_size"] for item in inventory["files"])
        + len(stable_json_bytes(inventory))
        + len(stable_json_bytes(first.bundle["completion"]))
    )
    assert b"\n{" in first.managed_bytes["artifacts/item_features.jsonl"]
    assert first.managed_bytes["artifacts/ambiguities.jsonl"] == b""
    assert first.managed_bytes["records/environment.json"].endswith(b"\n")


def test_terminal_records_do_not_oscillate_on_ratio_serialization() -> None:
    """A one-byte ratio-rendering change must not prevent the exact fixed point."""
    other_managed_bytes = {
        path: (b"x" * 13_553_439 if index == 0 else b"")
        for index, path in enumerate(MANAGED_PAYLOAD_PATHS)
        if path != "records/metrics.json"
    }
    measurements = CandidateMeasurements(
        build_wall_time_seconds=4.3,
        stage_wall_time_seconds={},
        peak_rss_bytes=1,
        input_bytes=1,
        producer_build_wall_time_seconds=100.0,
        producer_bytes=376_600_000,
    )

    metrics, inventory, completion = _stabilize_terminal_records(
        candidate_id="hcorv1-" + "a" * 64,
        completion_status="complete",
        measurements=measurements,
        other_managed_bytes=other_managed_bytes,
    )

    total = (
        sum(len(value) for value in other_managed_bytes.values())
        + len(stable_json_bytes(metrics))
        + len(stable_json_bytes(inventory))
        + len(stable_json_bytes(completion))
    )
    assert metrics["artifact_bytes"] == total
    assert metrics["artifact_bytes_ratio"] == round(total / 376_600_000, 6)


def test_completion_is_written_last_and_candidate_reuses_by_exact_checksum(
    tmp_path: Path,
) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "first")

    seal = write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )

    assert workspace.staging_root.parent == tmp_path / ".tmp"
    assert seal.written_paths[:-2] == MANAGED_PAYLOAD_PATHS
    assert seal.written_paths[-2:] == (
        "records/artifact_inventory.json",
        "records/completion_record.json",
    )
    gate = _gate(workspace)
    completion = publish_workspace(workspace, gate)
    assert verify_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH) == completion
    assert (
        reuse_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH, gate)
        == completion
    )


def test_workspace_and_final_publication_never_clobber(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    reserve_workspace(tmp_path, candidate_id, "same")
    with pytest.raises(FileExistsError):
        reserve_workspace(tmp_path, candidate_id, "same")
    with pytest.raises(ValueError, match="contained names"):
        reserve_workspace(tmp_path, candidate_id, "../escape")

    workspace = reserve_workspace(tmp_path, candidate_id, "other")
    workspace.final_root.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        write_validate_and_seal_candidate(
            workspace=workspace,
            payload=payload,
            measurements=_measurements(),
            schema_path=SCHEMA_PATH,
        )


@pytest.mark.parametrize("failure_kind", ["schema", "cross_record"])
def test_aggregate_validation_fails_before_completion(
    tmp_path: Path,
    failure_kind: str,
) -> None:
    bundle = _fixture_bundle()
    if failure_kind == "schema":
        bundle["identity"]["candidate_id"] = "invalid"
        expected_error = ValidationError
    else:
        bundle["decisions"] = bundle["decisions"][:-1]
        expected_error = HierarchyCorrectionContractError
    payload = _payload(bundle)
    workspace = reserve_workspace(
        tmp_path,
        _fixture_bundle()["identity"]["candidate_id"],
        failure_kind,
    )

    with pytest.raises(expected_error):
        write_validate_and_seal_candidate(
            workspace=workspace,
            payload=payload,
            measurements=_measurements(),
            schema_path=SCHEMA_PATH,
        )

    assert not (workspace.staging_root / "records/completion_record.json").exists()
    assert list(workspace.staging_root.rglob("*")) == []


def test_failed_attempt_is_retained_without_completion(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "failed")

    attempt_path = retain_failed_attempt(
        workspace=workspace,
        candidate_id=candidate_id,
        fatal_code="HIERARCHY_CYCLE",
        detail="fixture cycle",
        schema_path=SCHEMA_PATH,
    )

    assert json.loads(attempt_path.read_text()) == {
        "candidate_id": candidate_id,
        "status": "failed",
        "fatal_code": "HIERARCHY_CYCLE",
        "detail": "fixture cycle",
    }
    assert not (workspace.staging_root / "records/completion_record.json").exists()
    with pytest.raises(ValueError, match="no completion"):
        publish_workspace(
            workspace,
            VerifiedMachinePublication(candidate_id, "a" * 64),
        )


def test_failed_attempt_retracts_completion_after_post_seal_failure(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "post-seal")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )

    attempt_path = retain_failed_attempt(
        workspace=workspace,
        candidate_id=candidate_id,
        fatal_code="PUBLICATION_COLLISION",
        detail="fixture failure before rename",
        schema_path=SCHEMA_PATH,
    )

    assert attempt_path.is_file()
    assert not (workspace.staging_root / "records/completion_record.json").exists()


def test_attempt_builder_accepts_only_frozen_fatal_codes() -> None:
    schema_codes = set(
        json.loads(SCHEMA_PATH.read_text())["$defs"]["attempt_record"]["properties"]["fatal_code"][
            "enum"
        ]
    )
    assert schema_codes == FATAL_CODES
    with pytest.raises(ValueError, match="unknown hierarchy-correction fatal code"):
        build_attempt_record(candidate_id="hcorv1-" + "a" * 64, fatal_code="UNKNOWN", detail="x")


def test_reuse_rejects_changed_or_unmanaged_bytes(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "published")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    gate = _gate(workspace)
    publish_workspace(workspace, gate)
    feature_path = workspace.final_root / "artifacts/item_features.jsonl"
    feature_path.write_bytes(feature_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="authorization semantic differs"):
        reuse_completed_candidate(
            workspace.final_root,
            candidate_id,
            SCHEMA_PATH,
            gate,
        )


def test_reuse_rejects_an_unmanaged_file(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "unmanaged")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    gate = _gate(workspace)
    publish_workspace(workspace, gate)
    (workspace.final_root / "unmanaged.txt").write_text("not sealed")

    with pytest.raises(ValueError, match="managed file set differs"):
        reuse_completed_candidate(
            workspace.final_root,
            candidate_id,
            SCHEMA_PATH,
            gate,
        )
