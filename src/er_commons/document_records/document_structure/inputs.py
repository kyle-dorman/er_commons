"""Verify immutable inputs before document-structure construction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained, sha256_file
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.records import CompletionRecord
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.document_structure.handoff import verify_bounded_hierarchy_control
from er_commons.document_records.record_mapping.publication import verify_completed_candidate
from er_commons.hierarchy_inference.candidate_publication import (
    verify_completed_candidate as verify_hierarchy_candidate,
)

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
class DocumentStructureInputs:
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


@dataclass(frozen=True)
class _BaselineEvidence:
    root: Path
    completion: JsonObject
    completion_ref: ArtifactReference
    inventory_ref: ArtifactReference


@dataclass(frozen=True)
class _HierarchyEvidence:
    root: Path
    completion_ref: ArtifactReference
    inventory_ref: ArtifactReference
    acceptance_ref: ArtifactReference | None
    comparison_ref: ArtifactReference | None
    control: JsonObject


def _load_json_object(path: Path) -> JsonObject:
    try:
        value = json.loads(path.read_bytes())
    except json.JSONDecodeError as error:
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="input record contains valid JSON",
            expected="valid JSON",
            observed=f"{error.msg} at line {error.lineno}, column {error.colno}",
            subject=path.as_posix(),
        ) from error
    if not isinstance(value, dict):
        raise DocumentStructureInvariantError(
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
        raise DocumentStructureInvariantError(
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
    config: DocumentStructureConfig,
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


def _load_baseline_evidence(data_root: Path, config: DocumentStructureConfig) -> _BaselineEvidence:
    """Verify the baseline candidate seal and retain its published references."""
    root = assert_contained(data_root, config.baseline_candidate_relative_root.as_posix())
    completion_path = verify_completed_candidate(root, config.baseline_candidate_id)
    return _BaselineEvidence(
        root=root,
        completion=_load_json_object(completion_path),
        completion_ref=_data_ref(data_root, completion_path),
        inventory_ref=_data_ref(data_root, root / "records" / "artifact_inventory.json"),
    )


def _verify_source_manifest(
    data_root: Path,
    config: DocumentStructureConfig,
    baseline_producer: VerifiedProducer,
) -> ArtifactReference:
    """Verify that the configured manifest identifies the sealed source bytes."""
    path = assert_contained(data_root, config.source_manifest_relative_path.as_posix())
    reference = _data_ref(data_root, path)
    _require_input_value(
        invariant="configured source manifest matches the baseline producer seal",
        expected=baseline_producer.completion.source_manifest_sha256,
        observed=reference.sha256,
        subject=reference.path,
    )
    source_records = _load_json_object(path).get("sources")
    if not isinstance(source_records, list) or not all(
        isinstance(item, dict) for item in source_records
    ):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="source manifest sources are a list of JSON objects",
            expected="list of objects",
            observed=source_records,
            subject=reference.path,
        )
    matches = [item for item in source_records if item.get("source_id") == config.source.source_id]
    if len(matches) != 1:
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="source manifest contains exactly one configured Appendix P record",
            expected=1,
            observed=len(matches),
            subject=reference.path,
        )
    selected = matches[0]
    for invariant, expected, observed in (
        (
            "source manifest Appendix P checksum matches Task 03E.4 config",
            config.source.source_sha256,
            selected.get("sha256"),
        ),
        (
            "source manifest Appendix P page count matches Task 03E.4 config",
            config.source.physical_page_count,
            selected.get("pdf_page_count"),
        ),
    ):
        _require_input_value(
            invariant=invariant,
            expected=expected,
            observed=observed,
            subject=config.source.source_id,
        )
    return reference


def _verify_bounded_control(
    data_root: Path,
    project_root: Path,
    config: DocumentStructureConfig,
    hierarchy_root: Path,
) -> tuple[JsonObject, ArtifactReference, ArtifactReference]:
    """Verify the bounded acceptance evidence for one hierarchy candidate."""
    assert config.bounded_acceptance_relative_path is not None
    assert config.bounded_acceptance_policy_relative_path is not None
    assert config.producer_comparison_relative_path is not None
    acceptance_path = assert_contained(
        data_root, config.bounded_acceptance_relative_path.as_posix()
    )
    _require_input_value(
        invariant="bounded-acceptance root matches the configured hierarchy candidate",
        expected=config.hierarchy_candidate_id,
        observed=acceptance_path.parent.name,
        subject=config.bounded_acceptance_relative_path.as_posix(),
    )
    comparison_path = assert_contained(
        data_root, config.producer_comparison_relative_path.as_posix()
    )
    control = verify_bounded_hierarchy_control(
        data_root=data_root,
        candidate_root=hierarchy_root,
        candidate_id=config.hierarchy_candidate_id,
        hierarchy_schema_path=project_root / config.hierarchy_schema_relative_path,
        acceptance_path=acceptance_path,
        acceptance_policy_path=assert_contained(
            project_root, config.bounded_acceptance_policy_relative_path.as_posix()
        ),
        producer_comparison_path=comparison_path,
        baseline_producer_run_id=config.baseline_producer_run_id,
        hierarchy_producer_run_id=config.hierarchy_producer_run_id,
    )
    _require_input_value(
        invariant="bounded control names the configured hierarchy candidate",
        expected=config.hierarchy_candidate_id,
        observed=control.get("candidate_id"),
        subject=config.hierarchy_candidate_id,
    )
    acceptance_ref = _data_ref(data_root, acceptance_path)
    comparison_ref = _data_ref(data_root, comparison_path)
    _require_input_value(
        invariant="producer comparison checksum matches the bounded control",
        expected=control["producer_comparison_sha256"],
        observed=comparison_ref.sha256,
        subject=comparison_ref.path,
    )
    return control, acceptance_ref, comparison_ref


def _verify_hierarchy_evidence(
    data_root: Path, project_root: Path, config: DocumentStructureConfig
) -> _HierarchyEvidence:
    """Verify the selected hierarchy candidate through its configured control."""
    root = assert_contained(data_root, config.hierarchy_candidate_relative_root.as_posix())
    _require_input_value(
        invariant="hierarchy candidate root matches the configured candidate ID",
        expected=config.hierarchy_candidate_id,
        observed=root.name,
        subject=config.hierarchy_candidate_relative_root.as_posix(),
    )
    completion_path = root / "records" / "completion_record.json"
    acceptance_ref: ArtifactReference | None
    comparison_ref: ArtifactReference | None
    if config.control_profile == "task03e2d_bounded":
        control, acceptance_ref, comparison_ref = _verify_bounded_control(
            data_root, project_root, config, root
        )
    else:
        verify_hierarchy_candidate(
            root,
            config.hierarchy_candidate_id,
            project_root / config.hierarchy_schema_relative_path,
        )
        completion = _load_json_object(completion_path)
        identity = _load_json_object(root / "records/identity.json")
        identity_source = identity.get("source")
        if not isinstance(identity_source, dict):
            preimage = identity.get("preimage", {})
            identity_source = preimage.get("source", {}) if isinstance(preimage, dict) else {}
        observed_source_id = (
            identity_source.get("source_id")
            if isinstance(identity_source, dict) and identity_source
            else identity.get("source_id")
        )
        _require_input_value(
            invariant="strict hierarchy candidate source matches semantic config",
            expected=config.source.source_id,
            observed=observed_source_id,
            subject=config.hierarchy_candidate_id,
        )
        control = {
            "control_kind": "strict_quality_gate",
            "candidate_id": config.hierarchy_candidate_id,
            "completion_status": completion["status"],
            "artifact_inventory_sha256": completion["artifact_inventory_sha256"],
            "quality_gate_completion_sha256": sha256_file(completion_path),
            "source_id": config.source.source_id,
            "physical_page_count": config.source.physical_page_count,
            "corpus_wide_acceptance": False,
        }
        acceptance_ref = comparison_ref = None
    return _HierarchyEvidence(
        root=root,
        completion_ref=_data_ref(data_root, completion_path),
        inventory_ref=_data_ref(data_root, root / "records" / "artifact_inventory.json"),
        acceptance_ref=acceptance_ref,
        comparison_ref=comparison_ref,
        control=control,
    )


def load_document_structure_inputs(
    *,
    data_root: Path,
    project_root: Path,
    config: DocumentStructureConfig,
) -> DocumentStructureInputs:
    """Verify every immutable upstream seal and return identity-ready references."""
    baseline = _load_baseline_evidence(data_root, config)
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
    source_manifest_ref = _verify_source_manifest(data_root, config, baseline_producer)
    hierarchy = _verify_hierarchy_evidence(data_root, project_root, config)
    return DocumentStructureInputs(
        baseline_candidate_root=baseline.root,
        baseline_completion=baseline.completion,
        baseline_completion_ref=baseline.completion_ref,
        baseline_inventory_ref=baseline.inventory_ref,
        baseline_producer=baseline_producer,
        hierarchy_producer=hierarchy_producer,
        hierarchy_candidate_root=hierarchy.root,
        hierarchy_completion_ref=hierarchy.completion_ref,
        hierarchy_inventory_ref=hierarchy.inventory_ref,
        bounded_acceptance_ref=hierarchy.acceptance_ref,
        producer_comparison_ref=hierarchy.comparison_ref,
        control_provenance=hierarchy.control,
        source_manifest_ref=source_manifest_ref,
    )
