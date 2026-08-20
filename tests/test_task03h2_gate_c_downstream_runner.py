"""Offline behavior tests for the human-owned Gate C downstream workflow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.artifact_io import artifact_inventory, sha256_file
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.downstream_application import (
    DownstreamActions,
    run_downstream,
)
from er_commons.chunked_conversion.qualification.downstream_audit import (
    validate_downstream_completion,
)
from er_commons.chunked_conversion.qualification.downstream_configuration import (
    transplant_process_config,
)
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    AGGREGATE_ID,
    GATE_C_RUN_ID,
    QUALIFICATION_PRODUCER_ID,
    QUALIFICATION_STAGE_IDS,
    DownstreamCompletion,
    DownstreamPaths,
    DownstreamRequest,
    DownstreamStage,
)
from er_commons.chunked_conversion.qualification.downstream_difference_policy import (
    build_difference_policy,
)
from er_commons.chunked_conversion.qualification.downstream_stages import (
    validate_expected_stage_completions,
)
from er_commons.chunked_conversion.qualification.semantic_comparison import compare_trees
from er_commons.document_publication.process_validation import ProcessCompletions


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _completion(root: Path, candidate_id: str) -> Path:
    path = root / candidate_id / "records/completion_record.json"
    _write(path, {"status": "complete"})
    return path


def _process_completions(root: Path) -> ProcessCompletions:
    producer = _completion(root / "producer", QUALIFICATION_PRODUCER_ID)
    return ProcessCompletions(
        content_parsing=producer,
        heading_evidence_parsing=producer,
        record_mapping=_completion(root / "records", QUALIFICATION_STAGE_IDS["mapped_records"]),
        hierarchy_inference=_completion(
            root / "hierarchy", QUALIFICATION_STAGE_IDS["hierarchy_decisions"]
        ),
        document_structure=_completion(
            root / "records", QUALIFICATION_STAGE_IDS["structured_document"]
        ),
        document_reference_linking=_completion(
            root / "records", QUALIFICATION_STAGE_IDS["linked_document"]
        ),
    )


def _sealed_downstream(paths: DownstreamPaths) -> Path:
    report = paths.downstream / "records/gate_c_downstream_report.json"
    _write(
        report,
        {
            "status": "complete",
            "aggregate_conversion_id": AGGREGATE_ID,
            "g2_inspected": False,
        },
    )
    inventory_path = paths.downstream / "records/artifact_inventory.json"
    inventory = artifact_inventory(
        paths.downstream,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    _write(inventory_path, inventory)
    completion = DownstreamCompletion(
        schema_version="er_commons.task03h2_gate_c_downstream_completion.v1",
        status="complete",
        gate_c_run_id=GATE_C_RUN_ID,
        aggregate_conversion_id=AGGREGATE_ID,
        report="records/gate_c_downstream_report.json",
        artifact_inventory="records/artifact_inventory.json",
        artifact_inventory_sha256=sha256_file(inventory_path),
        completion_last=True,
    )
    completion_path = paths.downstream / "records/completion_record.json"
    _write(completion_path, completion.model_dump(mode="json"))
    return completion_path


def test_config_transplant_moves_output_and_producer_lineage_together() -> None:
    payload = {
        "artifact_relative_root": "accepted/records",
        "producer_artifact_relative_root": "accepted/producer",
        "policy": "unchanged",
    }
    transplanted = transplant_process_config("record_mapping", payload, Path("qualification/run"))

    assert transplanted == {
        "artifact_relative_root": "qualification/run/document_records",
        "producer_artifact_relative_root": "qualification/run/document_parse_evidence",
        "policy": "unchanged",
    }
    assert payload["producer_artifact_relative_root"] == "accepted/producer"


def test_unknown_config_role_has_structured_failure() -> None:
    with pytest.raises(QualificationError) as caught:
        transplant_process_config("mystery", {}, Path("qualification"))
    assert caught.value.code == "known_process_role"
    assert caught.value.stage == "downstream_configuration"


def test_expected_stage_completions_reject_lineage_transplant(tmp_path: Path) -> None:
    completions = _process_completions(tmp_path)
    validate_expected_stage_completions(completions)
    foreign = _completion(tmp_path / "records", "exv1-" + "f" * 64)
    corrupted = ProcessCompletions(**{**completions.__dict__, "record_mapping": foreign})

    with pytest.raises(QualificationError) as caught:
        validate_expected_stage_completions(corrupted)
    assert caught.value.code == "completion_identity"
    assert caught.value.context["role"] == "mapped_records"
    assert caught.value.path == foreign.as_posix()


def test_completed_run_reuse_requires_exact_typed_identity_and_seal(tmp_path: Path) -> None:
    paths = DownstreamPaths(tmp_path, project_root=tmp_path)
    completion_path = _sealed_downstream(paths)
    assert validate_downstream_completion(paths).evidence_id == GATE_C_RUN_ID

    payload = json.loads(completion_path.read_text())
    payload["aggregate_conversion_id"] = "dconv1-" + "f" * 64
    _write(completion_path, payload)
    with pytest.raises(QualificationError) as caught:
        validate_downstream_completion(paths)
    assert caught.value.code == "aggregate_identity"


def test_completed_run_reuse_rejects_managed_file_corruption(tmp_path: Path) -> None:
    paths = DownstreamPaths(tmp_path, project_root=tmp_path)
    _sealed_downstream(paths)
    report = paths.downstream / "records/gate_c_downstream_report.json"
    report.write_text("{}\n")

    with pytest.raises(QualificationError) as caught:
        validate_downstream_completion(paths)
    assert caught.value.code in {"artifact_size", "artifact_checksum"}
    assert caught.value.path == report.as_posix()


def test_difference_policy_does_not_waive_semantic_timing_named_field(
    tmp_path: Path,
) -> None:
    expected, actual = tmp_path / "expected", tmp_path / "actual"
    _write(expected / "completion.json", {"wall_seconds": 1.0})
    _write(actual / "completion.json", {"wall_seconds": 2.0})
    _write(expected / "semantic.json", {"wall_seconds": 1.0})
    _write(actual / "semantic.json", {"wall_seconds": 2.0})
    policy, summary = build_difference_policy(
        expected,
        actual,
        artifact_marker="/documents/source/",
    )
    assert summary.ignored_observations == 1
    with pytest.raises(QualificationError) as caught:
        compare_trees(expected, actual, policy)
    assert caught.value.path == "semantic.json#/wall_seconds"


def test_application_dispatches_public_stage_actions_without_script_import(
    tmp_path: Path,
) -> None:
    completion = tmp_path / "completion.json"
    request = DownstreamRequest(data_root=tmp_path, stage=DownstreamStage.REPORT)
    clock = iter((10.0, 12.5))
    actions = DownstreamActions(
        producer=lambda _paths: completion,
        records=lambda _paths: _process_completions(tmp_path),
        publication=lambda _paths: completion,
        report=lambda _paths: completion,
    )

    progress = run_downstream(request, actions=actions, monotonic=lambda: next(clock))

    assert progress.stage == DownstreamStage.REPORT
    assert progress.result == str(completion)
    assert progress.wall_seconds == 2.5


def test_request_rejects_relative_root() -> None:
    with pytest.raises(ValidationError, match="must be absolute"):
        DownstreamRequest(data_root=Path("relative"), stage=DownstreamStage.PRODUCER)
