"""Verify immutable Task 03E.4 inputs before semantic construction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.publication import verify_completed_candidate
from er_commons.document_extraction.producer_artifacts import verify_completed_run
from er_commons.document_extraction.producer_records import CompletionRecord
from er_commons.hierarchy_correction.candidate_publication import (
    verify_completed_candidate as verify_hierarchy_candidate,
)
from er_commons.semantic_materialization.config import SemanticMaterializationConfig
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_structure.constants import EXPECTED_PRODUCER_COMPARISON_SHA256
from er_commons.semantic_structure.handoff import verify_task03e2d_control
from er_commons.source_freeze import assert_contained, sha256_file

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ArtifactReference:
    """One verified input byte string named relative to its owning root."""

    path: str
    sha256: str

    def as_dict(self) -> JsonObject:
        """Return the published artifact-reference shape."""
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class VerifiedProducer:
    """Completion and inventory evidence for one sealed producer run."""

    run_id: str
    completion: CompletionRecord
    completion_ref: ArtifactReference
    inventory_ref: ArtifactReference


@dataclass(frozen=True)
class SemanticMaterializationInputs:
    """All verified external evidence needed to derive the v2 identity."""

    baseline_candidate_root: Path
    baseline_completion: JsonObject
    baseline_completion_ref: ArtifactReference
    baseline_inventory_ref: ArtifactReference
    baseline_producer: VerifiedProducer
    hierarchy_producer: VerifiedProducer
    hierarchy_candidate_root: Path
    hierarchy_completion_ref: ArtifactReference
    hierarchy_inventory_ref: ArtifactReference
    bounded_acceptance_ref: ArtifactReference | None
    producer_comparison_ref: ArtifactReference | None
    control_provenance: JsonObject
    source_manifest_ref: ArtifactReference


def _load_json_object(path: Path) -> JsonObject:
    try:
        value = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise SemanticMaterializationInvariantError(
            stage="input verification",
            invariant="input record contains valid JSON",
            expected="valid JSON",
            observed=f"{error.msg} at line {error.lineno}, column {error.colno}",
            subject=path.as_posix(),
        ) from error
    if not isinstance(value, dict):
        raise SemanticMaterializationInvariantError(
            stage="input verification",
            invariant="input JSON has an object at its root",
            expected="object",
            observed=type(value).__name__,
            subject=path.as_posix(),
        )
    return value


def _require_input_value(
    *,
    invariant: str,
    expected: object,
    observed: object,
    subject: str,
) -> None:
    """Raise one evidence-bearing input-boundary error when values differ."""
    if observed != expected:
        raise SemanticMaterializationInvariantError(
            stage="input verification",
            invariant=invariant,
            expected=expected,
            observed=observed,
            subject=subject,
        )


def _data_ref(data_root: Path, path: Path) -> ArtifactReference:
    return ArtifactReference(path.relative_to(data_root).as_posix(), sha256_file(path))


def _load_producer(
    data_root: Path,
    relative_root: Path,
    run_id: str,
) -> VerifiedProducer:
    run_root = assert_contained(data_root, relative_root.as_posix()) / run_id
    completion_path = verify_completed_run(run_root, run_id)
    inventory_path = run_root / "records" / "artifact_inventory.json"
    completion = CompletionRecord.model_validate_json(completion_path.read_bytes())
    return VerifiedProducer(
        run_id=run_id,
        completion=completion,
        completion_ref=_data_ref(data_root, completion_path),
        inventory_ref=_data_ref(data_root, inventory_path),
    )


def _verify_producer_pair(
    config: SemanticMaterializationConfig,
    baseline: VerifiedProducer,
    hierarchy: VerifiedProducer,
) -> None:
    """Require both sealed producers to describe the same configured source."""
    for label, producer in (("baseline", baseline), ("hierarchy", hierarchy)):
        completion = producer.completion
        expected = (
            (completion.source_id, config.source.source_id, "source ID"),
            (completion.source_sha256, config.source.source_sha256, "source checksum"),
        )
        for actual, frozen, field in expected:
            _require_input_value(
                invariant=f"{label} producer {field} matches Task 03E.4 config",
                expected=frozen,
                observed=actual,
                subject=producer.run_id,
            )
    _require_input_value(
        invariant="producer source-manifest checksums match",
        expected=baseline.completion.source_manifest_sha256,
        observed=hierarchy.completion.source_manifest_sha256,
        subject=f"{baseline.run_id} and {hierarchy.run_id}",
    )


def load_semantic_materialization_inputs(
    *,
    data_root: Path,
    project_root: Path,
    config: SemanticMaterializationConfig,
) -> SemanticMaterializationInputs:
    """Verify every immutable upstream seal and return identity-ready references."""
    baseline_root = assert_contained(data_root, config.baseline_candidate_relative_root.as_posix())
    baseline_completion_path = verify_completed_candidate(
        baseline_root, config.baseline_candidate_id
    )
    baseline_inventory_path = baseline_root / "records" / "artifact_inventory.json"
    baseline_completion = _load_json_object(baseline_completion_path)

    baseline_producer = _load_producer(
        data_root,
        config.baseline_producer_relative_root,
        config.baseline_producer_run_id,
    )
    hierarchy_producer = _load_producer(
        data_root,
        config.hierarchy_producer_relative_root,
        config.hierarchy_producer_run_id,
    )
    _verify_producer_pair(config, baseline_producer, hierarchy_producer)

    source_manifest_path = assert_contained(
        data_root, config.source_manifest_relative_path.as_posix()
    )
    source_manifest_ref = _data_ref(data_root, source_manifest_path)
    _require_input_value(
        invariant="configured source manifest matches the baseline producer seal",
        expected=baseline_producer.completion.source_manifest_sha256,
        observed=source_manifest_ref.sha256,
        subject=source_manifest_ref.path,
    )
    source_manifest = _load_json_object(source_manifest_path)
    source_records = source_manifest.get("sources")
    if not isinstance(source_records, list) or not all(
        isinstance(item, dict) for item in source_records
    ):
        raise SemanticMaterializationInvariantError(
            stage="input verification",
            invariant="source manifest sources are a list of JSON objects",
            expected="list of objects",
            observed=source_records,
            subject=source_manifest_ref.path,
        )
    matching_sources = [
        item for item in source_records if item.get("source_id") == config.source.source_id
    ]
    if len(matching_sources) != 1:
        raise SemanticMaterializationInvariantError(
            stage="input verification",
            invariant="source manifest contains exactly one configured Appendix P record",
            expected=1,
            observed=len(matching_sources),
            subject=source_manifest_ref.path,
        )
    selected_source = matching_sources[0]
    _require_input_value(
        invariant="source manifest Appendix P checksum matches Task 03E.4 config",
        expected=config.source.source_sha256,
        observed=selected_source.get("sha256"),
        subject=config.source.source_id,
    )
    _require_input_value(
        invariant="source manifest Appendix P page count matches Task 03E.4 config",
        expected=config.source.physical_page_count,
        observed=selected_source.get("pdf_page_count"),
        subject=config.source.source_id,
    )

    hierarchy_root = assert_contained(
        data_root, config.hierarchy_candidate_relative_root.as_posix()
    )
    hierarchy_completion_path = hierarchy_root / "records" / "completion_record.json"
    hierarchy_inventory_path = hierarchy_root / "records" / "artifact_inventory.json"
    acceptance_ref = None
    comparison_ref = None
    if config.control_profile == "task03e2d_bounded":
        assert config.bounded_acceptance_relative_path is not None
        assert config.producer_comparison_relative_path is not None
        acceptance_path = assert_contained(
            data_root, config.bounded_acceptance_relative_path.as_posix()
        )
        control = verify_task03e2d_control(hierarchy_root, acceptance_path)
        acceptance_ref = _data_ref(data_root, acceptance_path)
        comparison_path = assert_contained(
            data_root, config.producer_comparison_relative_path.as_posix()
        )
        comparison_ref = _data_ref(data_root, comparison_path)
        _require_input_value(
            invariant="producer comparison checksum matches the bounded control",
            expected=EXPECTED_PRODUCER_COMPARISON_SHA256,
            observed=comparison_ref.sha256,
            subject=comparison_ref.path,
        )
    else:
        verify_hierarchy_candidate(
            hierarchy_root,
            config.hierarchy_candidate_id,
            project_root / config.hierarchy_schema_relative_path,
        )
        completion = _load_json_object(hierarchy_completion_path)
        identity = _load_json_object(hierarchy_root / "records/identity.json")
        identity_source = identity.get("source")
        if not isinstance(identity_source, dict):
            identity_source = identity.get("preimage", {}).get("source", {})
        _require_input_value(
            invariant="strict hierarchy candidate source matches semantic config",
            expected=config.source.source_id,
            observed=identity_source.get("source_id"),
            subject=config.hierarchy_candidate_id,
        )
        control = {
            "control_kind": "strict_quality_gate",
            "candidate_id": config.hierarchy_candidate_id,
            "completion_status": completion["status"],
            "artifact_inventory_sha256": completion["artifact_inventory_sha256"],
            "quality_gate_completion_sha256": sha256_file(hierarchy_completion_path),
            "source_id": config.source.source_id,
            "physical_page_count": config.source.physical_page_count,
            "corpus_wide_acceptance": False,
        }
    return SemanticMaterializationInputs(
        baseline_candidate_root=baseline_root,
        baseline_completion=baseline_completion,
        baseline_completion_ref=_data_ref(data_root, baseline_completion_path),
        baseline_inventory_ref=_data_ref(data_root, baseline_inventory_path),
        baseline_producer=baseline_producer,
        hierarchy_producer=hierarchy_producer,
        hierarchy_candidate_root=hierarchy_root,
        hierarchy_completion_ref=_data_ref(data_root, hierarchy_completion_path),
        hierarchy_inventory_ref=_data_ref(data_root, hierarchy_inventory_path),
        bounded_acceptance_ref=acceptance_ref,
        producer_comparison_ref=comparison_ref,
        control_provenance=control,
        source_manifest_ref=source_manifest_ref,
    )
