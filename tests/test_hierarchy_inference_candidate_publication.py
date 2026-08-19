"""Focused candidate serialization and publication tests for Task 03E.2."""

from __future__ import annotations

import copy
import hashlib
import json
import tracemalloc
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema.exceptions import ValidationError

import er_commons.hierarchy_inference.candidate_storage as storage
from er_commons.hierarchy_inference.candidate_publication import (
    preserve_failed_workspace,
    publish_workspace,
    reserve_workspace,
    retain_failed_attempt,
    write_validate_and_seal_candidate,
)
from er_commons.hierarchy_inference.candidate_records import (
    CandidatePayload,
    SemanticBuildMeasurements,
    build_attempt_record,
    build_metrics,
    build_summary,
    validate_semantic_payload,
)
from er_commons.hierarchy_inference.candidate_verification import (
    deep_audit_completed_candidate,
    machine_authorization_for_verified_candidate,
    reuse_completed_candidate,
    verify_completed_candidate,
)
from er_commons.hierarchy_inference.constants import (
    FATAL_CODES,
    MANAGED_PAYLOAD_PATHS,
)
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.errors import HierarchyInferenceContractError
from er_commons.hierarchy_inference.failures import RunStage
from er_commons.hierarchy_inference.progress import CandidatePhase, ProgressSnapshot
from er_commons.hierarchy_inference.publication_authorization import (
    SEMANTIC_PATHS,
    VerifiedMachinePublication,
    VerifiedPublicationAuthorization,
    candidate_semantic_sha256,
)
from er_commons.hierarchy_inference.record_schema import HierarchyRecordValidators
from er_commons.hierarchy_inference.semantic_types import SemanticCandidate

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
        semantic=SemanticCandidate(
            features=tuple(source["features"]),
            toc_entries=tuple(source["toc_entries"]),
            reconciliations=tuple(source["reconciliations"]),
            regimes=tuple(source["regimes"]),
            decisions=tuple(source["decisions"]),
            hierarchy=source["hierarchy"],
            ambiguities=tuple(source["ambiguities"]),
            warnings=tuple(source["warnings"]),
        ),
    )


def _measurements() -> SemanticBuildMeasurements:
    fixture = _fixture_bundle()["metrics"]
    return SemanticBuildMeasurements(
        semantic_build_wall_time_seconds=fixture["semantic_build_wall_time_seconds"],
        semantic_stage_wall_time_seconds=fixture["semantic_stage_wall_time_seconds"],
        semantic_build_peak_rss_bytes=fixture["semantic_build_peak_rss_bytes"],
        input_bytes=fixture["input_bytes"],
        producer_build_wall_time_seconds=fixture["producer_build_wall_time_seconds"],
        producer_bytes=fixture["producer_bytes"],
    )


def _gate(workspace: Any) -> VerifiedMachinePublication:
    return machine_authorization_for_verified_candidate(
        workspace.staging_root,
        workspace.final_root.name,
        SCHEMA_PATH,
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
        payload_bytes=10_000,
    )

    assert summary == _fixture_bundle()["summary"]
    assert metrics["semantic_build_wall_time_seconds"] == 1.1
    assert metrics["payload_to_producer_bytes_ratio"] == 0.01
    assert metrics["semantic_build_faster_and_payload_smaller_than_producer"] is True


def test_semantic_validation_does_not_construct_a_publication_tail() -> None:
    records = validate_semantic_payload(
        payload=_payload(),
        validators=HierarchyRecordValidators.load(SCHEMA_PATH),
    )

    assert "metrics" not in records
    assert "artifact_inventory" not in records
    assert "completion" not in records


def test_record_validators_load_and_compile_once_per_unchanged_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema_path = tmp_path / "records.schema.json"
    schema_path.write_bytes(SCHEMA_PATH.read_bytes())
    original_read_text = Path.read_text
    reads = 0

    def counted_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        nonlocal reads
        if path.resolve() == schema_path.resolve():
            reads += 1
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read_text)

    first = HierarchyRecordValidators.load(schema_path)
    second = HierarchyRecordValidators.load(schema_path)

    assert first is second
    assert reads == 1


def test_streamed_publication_is_deterministic_and_counts_payload_bytes(tmp_path: Path) -> None:
    def write(token: str) -> tuple[Path, dict[str, bytes]]:
        payload = _payload()
        workspace = reserve_workspace(tmp_path, payload.identity["candidate_id"], token)
        write_validate_and_seal_candidate(
            workspace=workspace,
            payload=payload,
            measurements=_measurements(),
            schema_path=SCHEMA_PATH,
        )
        return workspace.staging_root, {
            path.relative_to(workspace.staging_root).as_posix(): path.read_bytes()
            for path in workspace.staging_root.rglob("*")
            if path.is_file()
        }

    first_root, first = write("first-stream")
    _second_root, second = write("second-stream")

    assert first == second
    inventory = json.loads(first["records/artifact_inventory.json"])
    metrics = json.loads(first["records/metrics.json"])
    assert [item["path"] for item in inventory["files"]] == list(MANAGED_PAYLOAD_PATHS)
    assert metrics["payload_bytes"] == sum(
        item["byte_size"] for item in inventory["files"] if item["path"] != "records/metrics.json"
    )
    assert b"\n{" in first["artifacts/item_features.jsonl"]
    assert first["artifacts/ambiguities.jsonl"] == b""
    assert (first_root / "records/environment.json").read_bytes().endswith(b"\n")


def test_metrics_are_acyclic_over_preterminal_payload_bytes() -> None:
    """Metrics depend only on payload bytes, so inventory can seal them once."""
    measurements = SemanticBuildMeasurements(
        semantic_build_wall_time_seconds=4.3,
        semantic_stage_wall_time_seconds={},
        semantic_build_peak_rss_bytes=1,
        input_bytes=1,
        producer_build_wall_time_seconds=100.0,
        producer_bytes=376_600_000,
    )

    metrics = build_metrics(
        candidate_id="hcorv1-" + "a" * 64,
        measurements=measurements,
        payload_bytes=13_553_439,
    )

    assert metrics["payload_bytes"] == 13_553_439
    assert metrics["payload_to_producer_bytes_ratio"] == round(13_553_439 / 376_600_000, 6)


def test_streaming_encoder_matches_compact_json_bytes() -> None:
    value = {"unicode": "café", "nested": [1, {"line": "a\nb"}], "empty": []}
    expected = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()

    assert b"".join(storage.iter_stable_json_bytes(value)) == expected


def test_jsonl_streaming_memory_does_not_scale_with_serialized_output(tmp_path: Path) -> None:
    records = tuple({"index": index, "text": "x" * 64} for index in range(50_000))
    tracemalloc.start()
    try:
        observed = storage.write_jsonl(tmp_path, "large.jsonl", records)
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert observed.byte_size == (tmp_path / "large.jsonl").stat().st_size
    assert peak < 5_000_000


def test_interrupted_jsonl_stream_has_no_completion(tmp_path: Path) -> None:
    def interrupted_records():
        yield {"index": 1}
        yield {"index": 2}
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        storage.write_jsonl(
            tmp_path,
            "artifacts/item_features.jsonl",
            cast(Any, interrupted_records()),
        )

    assert (tmp_path / "artifacts/item_features.jsonl").is_file()
    assert not (tmp_path / "records/completion_record.json").exists()


def test_completion_is_written_last_and_candidate_supports_fast_reuse_and_deep_audit(
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
    audit = deep_audit_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH)
    assert audit.completion_path == completion
    inventory = json.loads((workspace.final_root / "records/artifact_inventory.json").read_text())
    assert audit.candidate_semantic_sha256 == gate.candidate_semantic_sha256
    assert audit.artifact_inventory_sha256 == canonical_json_sha256(inventory)
    assert (
        reuse_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH, gate)
        == completion
    )


def test_machine_authorization_cannot_be_forged_or_structurally_substituted(
    tmp_path: Path,
) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "authorization-bypass")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )

    with pytest.raises(TypeError):
        VerifiedMachinePublication(candidate_id, candidate_semantic_sha256(workspace.staging_root))
    forged = type(
        "ForgedAuthorization",
        (),
        {
            "candidate_id": candidate_id,
            "candidate_semantic_sha256": candidate_semantic_sha256(workspace.staging_root),
        },
    )()
    with pytest.raises(TypeError, match="verified lifecycle"):
        publish_workspace(workspace, cast(Any, forged))
    with pytest.raises(TypeError, match="verified lifecycle"):
        publish_workspace(workspace, VerifiedPublicationAuthorization())

    assert workspace.staging_root.is_dir()
    assert not workspace.final_root.exists()


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
        expected_error = HierarchyInferenceContractError
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
            cast(Any, object()),
        )


def test_failed_attempt_retains_exact_progress_snapshot(tmp_path: Path) -> None:
    payload = _payload()
    workspace = reserve_workspace(tmp_path, payload.identity["candidate_id"], "progress-failure")
    snapshot = ProgressSnapshot(CandidatePhase.STREAMING_PUBLICATION, 20_000, 50_000, "records")

    attempt_path = retain_failed_attempt(
        workspace=workspace,
        candidate_id=payload.identity["candidate_id"],
        fatal_code="RUN_INTERRUPTED",
        detail="candidate_assembly: KeyboardInterrupt",
        schema_path=SCHEMA_PATH,
        stage=RunStage.CANDIDATE_ASSEMBLY,
        progress_snapshot=snapshot,
    )

    attempt = json.loads(attempt_path.read_text())
    assert attempt["stage"] == "candidate_assembly"
    assert attempt["phase"] == "streaming_publication"
    assert (attempt["processed_units"], attempt["total_units"], attempt["unit"]) == (
        20_000,
        50_000,
        "records",
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


def test_publication_and_failure_renames_fsync_both_parents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    published = reserve_workspace(tmp_path / "published", candidate_id, "candidate")
    write_validate_and_seal_candidate(
        workspace=published,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    gate = _gate(published)
    observed: list[Path] = []
    monkeypatch.setattr(storage, "fsync_directory", observed.append)

    publish_workspace(published, gate)

    assert published.staging_root.parent in observed
    assert published.final_root.parent in observed

    failed = reserve_workspace(tmp_path / "failed", candidate_id, "candidate")
    retain_failed_attempt(
        workspace=failed,
        candidate_id=candidate_id,
        fatal_code="RUN_INTERRUPTED",
        detail="candidate_assembly: KeyboardInterrupt",
        schema_path=SCHEMA_PATH,
    )
    attempts_root = failed.final_root.parent / "attempts"
    preserve_failed_workspace(failed, attempts_root)

    assert failed.staging_root.parent in observed
    assert attempts_root in observed
    assert attempts_root.parent in observed


def test_attempt_builder_accepts_only_frozen_fatal_codes() -> None:
    schema_codes = set(
        json.loads(SCHEMA_PATH.read_text())["$defs"]["attempt_record"]["properties"]["fatal_code"][
            "enum"
        ]
    )
    assert schema_codes == FATAL_CODES
    with pytest.raises(ValueError, match="unknown hierarchy-inference fatal code"):
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

    with pytest.raises(
        ValueError,
        match="candidate inventory size differs: artifacts/item_features.jsonl",
    ):
        reuse_completed_candidate(
            workspace.final_root,
            candidate_id,
            SCHEMA_PATH,
            gate,
        )


def test_fast_reuse_does_not_open_semantic_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "fast-reuse")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    gate = _gate(workspace)
    completion = publish_workspace(workspace, gate)
    original = Path.open

    def guarded_open(path: Path, *args: Any, **kwargs: Any):
        if path.is_relative_to(workspace.final_root):
            relative = path.relative_to(workspace.final_root).as_posix()
            if relative in SEMANTIC_PATHS:
                pytest.fail(f"fast reuse opened semantic payload: {relative}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    assert (
        reuse_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH, gate)
        == completion
    )


def test_same_size_semantic_corruption_requires_explicit_deep_audit(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "deep-audit")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    gate = _gate(workspace)
    completion = publish_workspace(workspace, gate)
    feature_path = workspace.final_root / "artifacts/item_features.jsonl"
    original = feature_path.read_bytes()
    feature_path.write_bytes(bytes([original[0] ^ 1]) + original[1:])

    assert (
        reuse_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH, gate)
        == completion
    )
    with pytest.raises(
        ValueError,
        match="candidate inventory checksum differs: artifacts/item_features.jsonl",
    ):
        deep_audit_completed_candidate(workspace.final_root, candidate_id, SCHEMA_PATH)


def test_candidate_assembly_reports_validation_and_streaming_progress(tmp_path: Path) -> None:
    payload = _payload()
    workspace = reserve_workspace(tmp_path, payload.identity["candidate_id"], "progress")
    reports: list[ProgressSnapshot] = []

    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
        progress=reports.append,
    )

    by_phase: dict[str, list[tuple[int, int]]] = {}
    for report in reports:
        by_phase.setdefault(report.phase.value, []).append(
            (report.processed_units, report.total_units)
        )
    assert set(by_phase) == {
        "semantic_schema_validation",
        "semantic_cross_record_validation",
        "streaming_publication",
        "terminal_validation",
        "inventory_seal",
        "completion_seal",
    }
    for observations in by_phase.values():
        assert observations[0][0] == 0
        assert observations[-1][0] == observations[-1][1]


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


def test_reuse_rejects_consistently_resealed_wrong_identity(tmp_path: Path) -> None:
    payload = _payload()
    candidate_id = payload.identity["candidate_id"]
    workspace = reserve_workspace(tmp_path, candidate_id, "resealed-identity")
    write_validate_and_seal_candidate(
        workspace=workspace,
        payload=payload,
        measurements=_measurements(),
        schema_path=SCHEMA_PATH,
    )
    identity_path = workspace.staging_root / "records/identity.json"
    identity = json.loads(identity_path.read_text())
    identity["source_sha256"] = "f" * 64
    identity_bytes = storage.stable_json_bytes(identity)
    identity_path.write_bytes(identity_bytes)

    inventory_path = workspace.staging_root / "records/artifact_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    identity_record = next(
        item for item in inventory["files"] if item["path"] == "records/identity.json"
    )
    identity_record["byte_size"] = len(identity_bytes)
    identity_record["sha256"] = hashlib.sha256(identity_bytes).hexdigest()
    inventory_path.write_bytes(storage.stable_json_bytes(inventory))
    completion_path = workspace.staging_root / "records/completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = canonical_json_sha256(inventory)
    completion_path.write_bytes(storage.stable_json_bytes(completion))

    with pytest.raises(ValueError, match="candidate identity digest differs"):
        verify_completed_candidate(workspace.staging_root, candidate_id, SCHEMA_PATH)
