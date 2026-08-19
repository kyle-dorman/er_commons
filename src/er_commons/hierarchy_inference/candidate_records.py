"""Build and serialize deterministic hierarchy candidate records."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_inference.candidate_storage import ManagedFile
from er_commons.hierarchy_inference.constants import (
    FATAL_CODES,
    MANAGED_PAYLOAD_PATHS,
    RULE_ORDER,
)
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.progress import (
    PHASE_UNITS,
    CandidatePhase,
    ProgressSnapshot,
)
from er_commons.hierarchy_inference.record_schema import HierarchyRecordValidators
from er_commons.hierarchy_inference.semantic_types import SemanticCandidate
from er_commons.hierarchy_inference.validation import (
    validate_publication_tail,
    validate_semantic_candidate,
)

JsonRecord = dict[str, Any]
ProgressCallback = Callable[[ProgressSnapshot], None]

JSONL_PATHS = frozenset(
    {
        "artifacts/item_features.jsonl",
        "artifacts/visible_toc_entries.jsonl",
        "artifacts/toc_reconciliation.jsonl",
        "artifacts/regimes.jsonl",
        "artifacts/decisions.jsonl",
        "artifacts/ambiguities.jsonl",
        "artifacts/warnings.jsonl",
    }
)


@dataclass(frozen=True)
class CandidatePayload:
    """Validated-stage records needed to assemble one correction candidate."""

    identity: JsonRecord
    input_inventory: JsonRecord
    environment: JsonRecord
    semantic: SemanticCandidate

    @property
    def features(self) -> tuple[JsonRecord, ...]:
        """Expose features for summary derivation."""
        return self.semantic.features

    @property
    def decisions(self) -> tuple[JsonRecord, ...]:
        """Expose decisions for summary derivation."""
        return self.semantic.decisions

    @property
    def ambiguities(self) -> tuple[JsonRecord, ...]:
        """Expose ambiguities for status derivation."""
        return self.semantic.ambiguities

    @property
    def warnings(self) -> tuple[JsonRecord, ...]:
        """Expose warnings for status derivation."""
        return self.semantic.warnings


@dataclass(frozen=True)
class SemanticBuildMeasurements:
    """Resource observations limited to semantic construction, before publication."""

    semantic_build_wall_time_seconds: float
    semantic_stage_wall_time_seconds: Mapping[str, float]
    semantic_build_peak_rss_bytes: int
    input_bytes: int
    producer_build_wall_time_seconds: float
    producer_bytes: int


def build_summary(payload: CandidatePayload) -> JsonRecord:
    """Derive candidate status and complete decision counts from stage records."""
    status = "complete_with_ambiguities" if payload.ambiguities else "complete"
    selected_counts = {rule_id: 0 for rule_id in RULE_ORDER}
    eligible_not_selected_counts = {rule_id: 0 for rule_id in RULE_ORDER}
    for decision in payload.decisions:
        selected = decision["selected_rule_id"]
        selected_counts[selected] += 1
        for eligible in decision["eligible_rule_ids"]:
            if eligible != selected:
                eligible_not_selected_counts[eligible] += 1
    return {
        "candidate_id": payload.identity["candidate_id"],
        "status": status,
        "feature_count": len(payload.features),
        "decision_count": len(payload.decisions),
        "heading_count": sum(item["corrected_role"] == "heading" for item in payload.decisions),
        "content_count": sum(item["corrected_role"] == "content" for item in payload.decisions),
        "excluded_count": sum(item["corrected_role"] == "excluded" for item in payload.decisions),
        "ambiguity_count": len(payload.ambiguities),
        "warning_count": len(payload.warnings),
        "selected_rule_counts": selected_counts,
        "eligible_not_selected_rule_counts": eligible_not_selected_counts,
    }


def build_metrics(
    *,
    candidate_id: str,
    measurements: SemanticBuildMeasurements,
    payload_bytes: int,
) -> JsonRecord:
    """Build exact resource ratios for one prospective managed payload set."""
    if measurements.producer_build_wall_time_seconds <= 0 or measurements.producer_bytes <= 0:
        raise ValueError("producer comparison measurements must be positive")
    if measurements.semantic_build_wall_time_seconds < 0:
        raise ValueError("semantic-build wall time must be nonnegative")
    return {
        "candidate_id": candidate_id,
        "semantic_build_wall_time_seconds": measurements.semantic_build_wall_time_seconds,
        "semantic_stage_wall_time_seconds": dict(measurements.semantic_stage_wall_time_seconds),
        "semantic_build_peak_rss_bytes": measurements.semantic_build_peak_rss_bytes,
        "input_bytes": measurements.input_bytes,
        "payload_bytes": payload_bytes,
        "producer_build_wall_time_seconds": measurements.producer_build_wall_time_seconds,
        "producer_bytes": measurements.producer_bytes,
        "semantic_build_to_producer_wall_time_ratio": (
            measurements.semantic_build_wall_time_seconds
            / measurements.producer_build_wall_time_seconds
        ),
        # The ratio is diagnostic; exact integer payload bytes remain authoritative.
        "payload_to_producer_bytes_ratio": round(payload_bytes / measurements.producer_bytes, 6),
        "semantic_build_faster_and_payload_smaller_than_producer": (
            measurements.semantic_build_wall_time_seconds
            < measurements.producer_build_wall_time_seconds
            and payload_bytes < measurements.producer_bytes
        ),
    }


def build_attempt_record(
    *,
    candidate_id: str,
    fatal_code: str,
    detail: str,
    stage: str | None = None,
    progress_snapshot: ProgressSnapshot | None = None,
) -> JsonRecord:
    """Build one schema-owned failed-attempt record from a frozen fatal code."""
    if fatal_code not in FATAL_CODES:
        raise ValueError(f"unknown hierarchy-inference fatal code: {fatal_code}")
    if not detail:
        raise ValueError("failed-attempt detail must not be empty")
    record: JsonRecord = {
        "candidate_id": candidate_id,
        "status": "failed",
        "fatal_code": fatal_code,
        "detail": detail,
    }
    if stage is not None:
        record["stage"] = stage
    if progress_snapshot is not None:
        record["phase"] = progress_snapshot.phase.value
        record["processed_units"] = progress_snapshot.processed_units
        record["total_units"] = progress_snapshot.total_units
        record["unit"] = progress_snapshot.unit
    return record


def validate_semantic_payload(
    *,
    payload: CandidatePayload,
    validators: HierarchyRecordValidators,
    progress: ProgressCallback | None = None,
) -> JsonRecord:
    """Validate resident semantic records without copying or serializing their arrays."""
    summary = build_summary(payload)
    records: JsonRecord = {
        "identity": payload.identity,
        "input_inventory": payload.input_inventory,
        "environment": payload.environment,
        **payload.semantic.as_mapping(),
        "summary": summary,
    }
    validators.validate_semantic_schema(records, progress)
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.SEMANTIC_CROSS_RECORD_VALIDATION, 0, 1, "checks"))
    validate_semantic_candidate(records)
    if progress is not None:
        progress(ProgressSnapshot(CandidatePhase.SEMANTIC_CROSS_RECORD_VALIDATION, 1, 1, "checks"))
    return records


def validate_attempt_record(
    record: JsonRecord,
    validators: HierarchyRecordValidators,
) -> None:
    """Validate a failed-attempt record against its schema definition."""
    validators.validate_definition("attempt_record", record)
    progress_fields = {"phase", "processed_units", "total_units", "unit"}
    present_progress_fields = progress_fields.intersection(record)
    if present_progress_fields and present_progress_fields != progress_fields:
        raise ValueError("failed-attempt progress snapshot is incomplete")
    if present_progress_fields and record["processed_units"] > record["total_units"]:
        raise ValueError("failed-attempt progress counts are invalid")
    if present_progress_fields:
        phase = CandidatePhase(record["phase"])
        if record["unit"] != PHASE_UNITS[phase]:
            raise ValueError("failed-attempt progress unit differs from its phase")


def validate_candidate_bundle(bundle: JsonRecord, schema_path: Path) -> None:
    """Apply aggregate JSON Schema and human-owned cross-record validation."""
    HierarchyRecordValidators.load(schema_path).validate_bundle_schema(bundle)
    validate_semantic_candidate(bundle)
    validate_publication_tail(bundle)


def validate_terminal_records(
    *,
    identity: JsonRecord,
    summary: JsonRecord,
    metrics: JsonRecord,
    inventory: JsonRecord,
    completion: JsonRecord,
    managed_files: Sequence[ManagedFile],
    validators: HierarchyRecordValidators,
) -> None:
    """Validate the acyclic metrics, inventory, and completion tail."""
    for definition, record in (
        ("metrics", metrics),
        ("artifact_inventory", inventory),
        ("completion", completion),
    ):
        validators.validate_definition(definition, record)
    expected_inventory = [item.as_record() for item in managed_files]
    if inventory["files"] != expected_inventory:
        raise ValueError("artifact inventory files differ")
    if [item.path for item in managed_files] != list(MANAGED_PAYLOAD_PATHS):
        raise ValueError("artifact inventory paths differ")
    payload_bytes = sum(
        item.byte_size for item in managed_files if item.path != "records/metrics.json"
    )
    if metrics["payload_bytes"] != payload_bytes:
        raise ValueError("metrics payload bytes differ")
    validate_publication_tail(
        {
            "identity": identity,
            "summary": summary,
            "metrics": metrics,
            "artifact_inventory": inventory,
            "completion": completion,
        }
    )


def validate_reuse_metadata(
    *,
    identity: JsonRecord,
    input_inventory: JsonRecord,
    environment: object,
    summary: JsonRecord,
    metrics: JsonRecord,
    inventory: JsonRecord,
    completion: JsonRecord,
    managed_files: Sequence[ManagedFile],
    validators: HierarchyRecordValidators,
) -> None:
    """Revalidate every small record while trusting sealed semantic payload bytes."""
    for definition, record in (
        ("identity", identity),
        ("input_inventory", input_inventory),
        ("summary", summary),
    ):
        validators.validate_definition(definition, record)
    if not isinstance(environment, dict):
        raise ValueError("environment record is not an object")
    identity_payload = {key: value for key, value in identity.items() if key != "candidate_id"}
    if identity["candidate_id"] != f"hcorv1-{canonical_json_sha256(identity_payload)}":
        raise ValueError("candidate identity digest differs")
    for field_name in (
        "source_sha256",
        "producer_completion_sha256",
        "producer_inventory_sha256",
        "conversion_completion_sha256",
        "conversion_inventory_sha256",
    ):
        if input_inventory[field_name] != identity[field_name]:
            raise ValueError(f"input inventory {field_name} differs")
    validate_terminal_records(
        identity=identity,
        summary=summary,
        metrics=metrics,
        inventory=inventory,
        completion=completion,
        managed_files=managed_files,
        validators=validators,
    )
