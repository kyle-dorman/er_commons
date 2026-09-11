"""Verify immutable inputs before document-structure construction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import assert_contained, sha256_file
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.records import CompletionRecord
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.document_structure.errors import (
    DocumentStructureInvariantError,
)
from er_commons.document_records.document_structure.handoff import verify_bounded_hierarchy_control
from er_commons.document_records.record_mapping.publication import verify_completed_candidate
from er_commons.hierarchy_inference.candidate_verification import (
    verify_completed_candidate as verify_hierarchy_candidate,
)

JsonObject = dict[str, Any]

if TYPE_CHECKING:
    from er_commons.document_records.document_structure.missing_chapters import (
        MissingChapterDecision,
    )
    from er_commons.document_records.document_structure.repeated_headings import (
        RepeatedHeadingDecision,
    )


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
    repeated_heading_decisions_ref: ArtifactReference | None = None
    repeated_heading_completion_ref: ArtifactReference | None = None
    repeated_heading_inventory_ref: ArtifactReference | None = None
    repeated_heading_qualification_ref: ArtifactReference | None = None
    repeated_heading_decisions: tuple[RepeatedHeadingDecision, ...] = ()
    missing_chapter_decisions_ref: ArtifactReference | None = None
    missing_chapter_completion_ref: ArtifactReference | None = None
    missing_chapter_inventory_ref: ArtifactReference | None = None
    missing_chapter_qualification_ref: ArtifactReference | None = None
    missing_chapter_decisions: tuple[MissingChapterDecision, ...] = ()


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
    repeated_refs, repeated_decisions = _load_repeated_heading_decisions(
        data_root=data_root,
        project_root=project_root,
        config=config,
    )
    missing_refs, missing_decisions = _load_missing_chapter_decisions(
        data_root=data_root, project_root=project_root, config=config
    )
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
        repeated_heading_decisions_ref=repeated_refs.get("decisions"),
        repeated_heading_completion_ref=repeated_refs.get("completion"),
        repeated_heading_inventory_ref=repeated_refs.get("inventory"),
        repeated_heading_qualification_ref=repeated_refs.get("qualification"),
        repeated_heading_decisions=repeated_decisions,
        missing_chapter_decisions_ref=missing_refs.get("decisions"),
        missing_chapter_completion_ref=missing_refs.get("completion"),
        missing_chapter_inventory_ref=missing_refs.get("inventory"),
        missing_chapter_qualification_ref=missing_refs.get("qualification"),
        missing_chapter_decisions=missing_decisions,
    )


def _load_missing_chapter_decisions(
    *, data_root: Path, project_root: Path, config: DocumentStructureConfig
) -> tuple[dict[str, ArtifactReference], tuple[MissingChapterDecision, ...]]:
    """Verify and load the compact v3 missing-chapter decision packet."""
    if config.schema_version != "3.0.0":
        return {}, ()
    assert config.missing_chapter_qualification_relative_root is not None
    assert config.missing_chapter_policy_relative_path is not None
    assert config.missing_chapter_decision_schema_relative_path is not None
    root = assert_contained(
        data_root, config.missing_chapter_qualification_relative_root.as_posix()
    )
    paths = {
        "completion": root / "completion.json",
        "inventory": root / "inventory.json",
        "qualification": root / "qualification.json",
        "decisions": root / "eligible_decisions.jsonl",
    }
    _verify_qualification_file_closure(root, repair_label="missing-chapter")
    completion = _load_json_object(paths["completion"])
    inventory = _load_json_object(paths["inventory"])
    qualification = _load_json_object(paths["qualification"])
    _verify_qualification_packet(
        root,
        paths,
        completion,
        inventory,
        qualification,
        repair_label="missing-chapter",
    )
    schema_path = assert_contained(
        project_root, config.missing_chapter_decision_schema_relative_path.as_posix()
    )
    policy_path = assert_contained(
        project_root, config.missing_chapter_policy_relative_path.as_posix()
    )
    schema = _load_json_object(schema_path)
    for name, expected in (
        (
            "policy_ref",
            (config.missing_chapter_policy_relative_path.as_posix(), sha256_file(policy_path)),
        ),
        (
            "decision_schema_ref",
            (
                config.missing_chapter_decision_schema_relative_path.as_posix(),
                sha256_file(schema_path),
            ),
        ),
    ):
        observed = qualification.get(name) or {}
        _require_input_value(
            invariant=f"missing-chapter qualification binds current {name}",
            expected=expected,
            observed=(observed.get("path"), observed.get("sha256")),
            subject=paths["qualification"].as_posix(),
        )
    records = _read_qualification_records(
        paths["decisions"], schema, repair_label="missing-chapter"
    )
    all_records = _read_qualification_records(
        root / "all_decisions.jsonl", schema, repair_label="missing-chapter"
    )
    decisions = _verify_missing_chapter_records(
        config=config,
        paths=paths,
        records=records,
        all_records=all_records,
        completion=completion,
        qualification=qualification,
    )
    return {role: _data_ref(data_root, path) for role, path in paths.items()}, decisions


def _verify_missing_chapter_records(
    *,
    config: DocumentStructureConfig,
    paths: dict[str, Path],
    records: list[JsonObject],
    all_records: list[JsonObject],
    completion: JsonObject,
    qualification: JsonObject,
) -> tuple[MissingChapterDecision, ...]:
    """Verify source isolation, complete counts, and projection eligibility."""
    counts = {
        status: sum(item["status"] == status for item in all_records)
        for status in ("eligible", "already_present", "rejected", "review_required")
    }
    _require_input_value(
        invariant="missing-chapter qualification counts are exact",
        expected=qualification.get("counts"),
        observed=counts,
        subject=paths["qualification"].as_posix(),
    )
    _require_input_value(
        invariant="missing-chapter qualification has no pending human review",
        expected=0,
        observed=counts["review_required"],
        subject=paths["qualification"].as_posix(),
    )
    eligible = [item for item in all_records if item["status"] == "eligible"]
    _require_input_value(
        invariant="missing-chapter eligible stream is exact subset",
        expected=eligible,
        observed=records,
        subject=paths["decisions"].as_posix(),
    )
    for line_number, record in enumerate(records, start=1):
        _require_input_value(
            invariant="missing-chapter decision stays in configured source",
            expected=config.source.source_id,
            observed=record.get("source_id"),
            subject=f"{paths['decisions'].as_posix()}:{line_number}",
        )
        _require_input_value(
            invariant="missing-chapter decision binds qualification source evidence",
            expected=qualification.get("source_ref"),
            observed=record.get("source_ref"),
            subject=f"{paths['decisions'].as_posix()}:{line_number}",
        )
    _require_input_value(
        invariant="missing-chapter eligible count matches completion",
        expected=completion.get("eligible_decision_count"),
        observed=len(records),
        subject=paths["completion"].as_posix(),
    )
    _require_input_value(
        invariant="missing-chapter total count matches completion",
        expected=completion.get("decision_count"),
        observed=len(all_records),
        subject=paths["completion"].as_posix(),
    )
    _require_input_value(
        invariant="missing-chapter status counts match completion",
        expected=completion.get("decision_counts"),
        observed=counts,
        subject=paths["completion"].as_posix(),
    )
    from er_commons.document_records.document_structure.missing_chapters import (
        MissingChapterDecision,
    )

    decisions = tuple(MissingChapterDecision.from_record(item) for item in records)
    if not decisions or any(item.status != "eligible" for item in decisions):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="v3 missing-chapter inputs are eligible",
            expected="one or more eligible records",
            observed=[item.status for item in decisions],
            subject=paths["decisions"].as_posix(),
        )
    return decisions


def _load_repeated_heading_decisions(
    *,
    data_root: Path,
    project_root: Path,
    config: DocumentStructureConfig,
) -> tuple[dict[str, ArtifactReference], tuple[RepeatedHeadingDecision, ...]]:
    """Validate and load the small v2 decision stream without touching source payloads."""
    if config.schema_version == "1.0.0" or (
        config.schema_version == "3.0.0"
        and config.repeated_heading_qualification_relative_root is None
    ):
        return {}, ()
    assert config.repeated_heading_qualification_relative_root is not None
    assert config.repeated_heading_policy_relative_path is not None
    assert config.repeated_heading_decision_schema_relative_path is not None
    root = assert_contained(
        data_root, config.repeated_heading_qualification_relative_root.as_posix()
    )
    paths = {
        "completion": root / "completion.json",
        "inventory": root / "inventory.json",
        "qualification": root / "qualification.json",
        "decisions": root / "eligible_decisions.jsonl",
    }
    _verify_qualification_file_closure(root, repair_label="repeated-heading")
    completion = _load_json_object(paths["completion"])
    inventory = _load_json_object(paths["inventory"])
    qualification = _load_json_object(paths["qualification"])
    _verify_qualification_packet(
        root,
        paths,
        completion,
        inventory,
        qualification,
        repair_label="repeated-heading",
    )
    schema = _verify_repeated_heading_contract_refs(
        project_root, config, paths["qualification"], qualification
    )
    records = _read_qualification_records(
        paths["decisions"], schema, repair_label="repeated-heading"
    )
    all_records = _read_qualification_records(
        root / "all_decisions.jsonl", schema, repair_label="repeated-heading"
    )
    decisions = _verify_repeated_heading_records(
        paths["decisions"], records, all_records, completion, qualification
    )
    return (
        {role: _data_ref(data_root, path) for role, path in paths.items()},
        decisions,
    )


def _verify_qualification_file_closure(root: Path, *, repair_label: str) -> None:
    """Reject missing, additional, or nested qualification artifacts."""
    expected_files = {
        "all_decisions.jsonl",
        "eligible_decisions.jsonl",
        "qualification.json",
        "inventory.json",
        "completion.json",
    }
    observed_files = {item.name for item in root.iterdir()}
    if observed_files != expected_files:
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant=f"{repair_label} qualification has exact file closure",
            expected=sorted(expected_files),
            observed=sorted(observed_files),
            subject=root.as_posix(),
        )


def _verify_qualification_packet(
    root: Path,
    paths: dict[str, Path],
    completion: JsonObject,
    inventory: JsonObject,
    qualification: JsonObject,
    *,
    repair_label: str,
) -> None:
    """Verify terminal status and the inventory's exact managed-file closure."""
    _require_input_value(
        invariant=f"{repair_label} qualification is terminal without pending review",
        expected="complete",
        observed=completion.get("status"),
        subject=paths["completion"].as_posix(),
    )
    _require_input_value(
        invariant=f"{repair_label} qualification summary is complete",
        expected="complete",
        observed=qualification.get("status"),
        subject=paths["qualification"].as_posix(),
    )
    _require_input_value(
        invariant=f"{repair_label} completion seals its inventory",
        expected=sha256_file(paths["inventory"]),
        observed=completion.get("inventory_sha256"),
        subject=paths["completion"].as_posix(),
    )
    _require_input_value(
        invariant=f"{repair_label} completion declares exact managed file count",
        expected=3,
        observed=completion.get("managed_file_count"),
        subject=paths["completion"].as_posix(),
    )
    files = inventory.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant=f"{repair_label} inventory has file records",
            expected="list of objects",
            observed=files,
            subject=paths["inventory"].as_posix(),
        )
    managed = {item.get("path"): item for item in files}
    expected_managed = {"all_decisions.jsonl", "eligible_decisions.jsonl", "qualification.json"}
    if set(managed) != expected_managed or len(managed) != len(files):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant=f"{repair_label} inventory membership is exact and unique",
            expected=sorted(expected_managed),
            observed=sorted(str(item) for item in managed),
            subject=paths["inventory"].as_posix(),
        )
    for relative, item in managed.items():
        managed_path = root / relative
        _require_input_value(
            invariant=f"{repair_label} managed size matches for {relative}",
            expected=item.get("byte_size"),
            observed=managed_path.stat().st_size,
            subject=managed_path.as_posix(),
        )
        _require_input_value(
            invariant=f"{repair_label} managed digest matches for {relative}",
            expected=item.get("sha256"),
            observed=sha256_file(managed_path),
            subject=managed_path.as_posix(),
        )
    _require_input_value(
        invariant=f"{repair_label} inventory total byte count is exact",
        expected=sum((root / relative).stat().st_size for relative in expected_managed),
        observed=inventory.get("total_bytes"),
        subject=paths["inventory"].as_posix(),
    )


def _verify_repeated_heading_contract_refs(
    project_root: Path,
    config: DocumentStructureConfig,
    qualification_path: Path,
    qualification: JsonObject,
) -> JsonObject:
    """Verify the packet's checked-in policy and schema bindings."""
    assert config.repeated_heading_decision_schema_relative_path is not None
    assert config.repeated_heading_policy_relative_path is not None
    schema_path = assert_contained(
        project_root, config.repeated_heading_decision_schema_relative_path.as_posix()
    )
    schema = _load_json_object(schema_path)
    policy_path = assert_contained(
        project_root,
        config.repeated_heading_policy_relative_path.as_posix(),
    )
    _require_input_value(
        invariant="repeated-heading qualification binds the current policy",
        expected=sha256_file(policy_path),
        observed=(qualification.get("policy_ref") or {}).get("sha256"),
        subject=qualification_path.as_posix(),
    )
    _require_input_value(
        invariant="repeated-heading qualification names the configured policy path",
        expected=config.repeated_heading_policy_relative_path.as_posix(),
        observed=(qualification.get("policy_ref") or {}).get("path"),
        subject=qualification_path.as_posix(),
    )
    _require_input_value(
        invariant="repeated-heading qualification binds the current schema",
        expected=sha256_file(schema_path),
        observed=(qualification.get("decision_schema_ref") or {}).get("sha256"),
        subject=qualification_path.as_posix(),
    )
    _require_input_value(
        invariant="repeated-heading qualification names the configured schema path",
        expected=config.repeated_heading_decision_schema_relative_path.as_posix(),
        observed=(qualification.get("decision_schema_ref") or {}).get("path"),
        subject=qualification_path.as_posix(),
    )
    return schema


def _read_qualification_records(
    path: Path, schema: JsonObject, *, repair_label: str
) -> list[JsonObject]:
    """Parse and schema-validate the eligible JSONL stream."""
    validator = Draft202012Validator(schema)
    records: list[JsonObject] = []
    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            raise DocumentStructureInvariantError(
                stage="input verification",
                invariant=f"{repair_label} decision line contains valid JSON",
                expected="valid JSON object",
                observed=f"{error.msg} at line {line_number}",
                subject=path.as_posix(),
            ) from error
        if not isinstance(record, dict):
            raise DocumentStructureInvariantError(
                stage="input verification",
                invariant=f"{repair_label} decision line is an object",
                expected="object",
                observed=type(record).__name__,
                subject=f"{path.as_posix()}:{line_number}",
            )
        errors = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
        if errors:
            raise DocumentStructureInvariantError(
                stage="input verification",
                invariant=f"{repair_label} decision matches its schema",
                expected="valid decision record",
                observed=errors[0].message,
                subject=f"{path.as_posix()}:{line_number}",
            )
        records.append(record)
    return records


def _verify_repeated_heading_records(
    path: Path,
    records: list[JsonObject],
    all_records: list[JsonObject],
    completion: JsonObject,
    qualification: JsonObject,
) -> tuple[RepeatedHeadingDecision, ...]:
    """Verify counts, source bindings, ordering, and projection eligibility."""
    from er_commons.document_records.document_structure.repeated_headings import (
        RepeatedHeadingDecision,
    )

    _require_input_value(
        invariant="repeated-heading eligible count matches completion",
        expected=completion.get("eligible_decision_count"),
        observed=len(records),
        subject=path.as_posix(),
    )
    qualification_counts = qualification.get("counts")
    observed_counts = {
        status: sum(record["status"] == status for record in all_records)
        for status in ("eligible", "rejected", "review_required")
    }
    _require_input_value(
        invariant="repeated-heading all-decision counts match qualification",
        expected=qualification_counts,
        observed=observed_counts,
        subject=path.as_posix(),
    )
    _require_input_value(
        invariant="repeated-heading qualification has no pending human review",
        expected=0,
        observed=observed_counts["review_required"],
        subject=path.as_posix(),
    )
    eligible_records = [record for record in all_records if record["status"] == "eligible"]
    _require_input_value(
        invariant="repeated-heading eligible stream is exact subset of all decisions",
        expected=eligible_records,
        observed=records,
        subject=path.as_posix(),
    )
    expected_source_ref = qualification.get("source_ref")
    for line_number, record in enumerate(records, start=1):
        _require_input_value(
            invariant="repeated-heading decision binds qualification source evidence",
            expected=expected_source_ref,
            observed=record.get("source_ref"),
            subject=f"{path.as_posix()}:{line_number}",
        )
    stable_groups = [tuple(record["heading_stable_keys"]) for record in records]
    if len(set(stable_groups)) != len(stable_groups) or stable_groups != sorted(stable_groups):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="repeated-heading decisions are unique and canonically ordered",
            expected="unique groups in ascending stable-key order",
            observed=stable_groups,
            subject=path.as_posix(),
        )
    decisions = tuple(RepeatedHeadingDecision.from_record(record) for record in records)
    if not decisions or any(item.status != "eligible" for item in decisions):
        raise DocumentStructureInvariantError(
            stage="input verification",
            invariant="production repeated-heading inputs are nonempty eligible decisions",
            expected="one or more eligible records",
            observed=[item.status for item in decisions],
            subject=path.as_posix(),
        )
    return decisions
