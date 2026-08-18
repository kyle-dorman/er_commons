"""Build and serialize deterministic hierarchy candidate records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.hierarchy_inference.bundle import HierarchyBundleView
from er_commons.hierarchy_inference.constants import (
    FATAL_CODES,
    MANAGED_PAYLOAD_PATHS,
    RULE_ORDER,
)
from er_commons.hierarchy_inference.decisions import decisions_cover_features_in_order
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.validation import validate_hierarchy_inference_bundle

JsonRecord = dict[str, Any]

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
    features: tuple[JsonRecord, ...]
    toc_entries: tuple[JsonRecord, ...]
    reconciliations: tuple[JsonRecord, ...]
    regimes: tuple[JsonRecord, ...]
    decisions: tuple[JsonRecord, ...]
    hierarchy: JsonRecord
    ambiguities: tuple[JsonRecord, ...]
    warnings: tuple[JsonRecord, ...]


@dataclass(frozen=True)
class CandidateMeasurements:
    """Resource observations from one production build."""

    build_wall_time_seconds: float
    stage_wall_time_seconds: Mapping[str, float]
    peak_rss_bytes: int
    input_bytes: int
    producer_build_wall_time_seconds: float
    producer_bytes: int


@dataclass(frozen=True)
class PreparedCandidate:
    """A fully validated aggregate and its exact managed file bytes."""

    bundle: JsonRecord
    managed_bytes: Mapping[str, bytes]


def stable_json_bytes(value: Any) -> bytes:
    """Serialize deterministic compact UTF-8 JSON with one terminal newline."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def stable_jsonl_bytes(records: Sequence[JsonRecord]) -> bytes:
    """Serialize ordered records as deterministic newline-delimited JSON."""
    return b"".join(stable_json_bytes(record) for record in records)


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
    measurements: CandidateMeasurements,
    artifact_bytes: int,
) -> JsonRecord:
    """Build exact resource ratios for one prospective managed payload set."""
    if measurements.producer_build_wall_time_seconds <= 0 or measurements.producer_bytes <= 0:
        raise ValueError("producer comparison measurements must be positive")
    if measurements.build_wall_time_seconds < 0:
        raise ValueError("build wall time must be nonnegative")
    return {
        "candidate_id": candidate_id,
        "build_wall_time_seconds": measurements.build_wall_time_seconds,
        "stage_wall_time_seconds": dict(measurements.stage_wall_time_seconds),
        "peak_rss_bytes": measurements.peak_rss_bytes,
        "input_bytes": measurements.input_bytes,
        "artifact_bytes": artifact_bytes,
        "producer_build_wall_time_seconds": measurements.producer_build_wall_time_seconds,
        "producer_bytes": measurements.producer_bytes,
        "wall_time_ratio": (
            measurements.build_wall_time_seconds / measurements.producer_build_wall_time_seconds
        ),
        # Bound this reporting value because its serialized length contributes
        # to artifact_bytes. Exact integer bytes remain the acceptance input.
        "artifact_bytes_ratio": round(artifact_bytes / measurements.producer_bytes, 6),
        "cheap_relative_to_producer": (
            measurements.build_wall_time_seconds < measurements.producer_build_wall_time_seconds
            and artifact_bytes < measurements.producer_bytes
        ),
    }


def build_attempt_record(*, candidate_id: str, fatal_code: str, detail: str) -> JsonRecord:
    """Build one schema-owned failed-attempt record from a frozen fatal code."""
    if fatal_code not in FATAL_CODES:
        raise ValueError(f"unknown hierarchy-inference fatal code: {fatal_code}")
    if not detail:
        raise ValueError("failed-attempt detail must not be empty")
    return {
        "candidate_id": candidate_id,
        "status": "failed",
        "fatal_code": fatal_code,
        "detail": detail,
    }


def prepare_candidate(
    *,
    payload: CandidatePayload,
    measurements: CandidateMeasurements,
    schema_path: Path,
) -> PreparedCandidate:
    """Serialize and validate the complete aggregate before completion exists."""
    summary = build_summary(payload)
    records: JsonRecord = {
        "identity": payload.identity,
        "input_inventory": payload.input_inventory,
        "environment": payload.environment,
        "features": list(payload.features),
        "toc_entries": list(payload.toc_entries),
        "reconciliations": list(payload.reconciliations),
        "regimes": list(payload.regimes),
        "decisions": list(payload.decisions),
        "hierarchy": payload.hierarchy,
        "ambiguities": list(payload.ambiguities),
        "warnings": list(payload.warnings),
        "summary": summary,
    }
    path_values: dict[str, Any] = {
        "records/identity.json": records["identity"],
        "records/input_inventory.json": records["input_inventory"],
        "records/environment.json": records["environment"],
        "artifacts/item_features.jsonl": records["features"],
        "artifacts/visible_toc_entries.jsonl": records["toc_entries"],
        "artifacts/toc_reconciliation.jsonl": records["reconciliations"],
        "artifacts/regimes.jsonl": records["regimes"],
        "artifacts/decisions.jsonl": records["decisions"],
        "artifacts/hierarchy.json": records["hierarchy"],
        "artifacts/ambiguities.jsonl": records["ambiguities"],
        "artifacts/warnings.jsonl": records["warnings"],
        "records/summary.json": records["summary"],
    }
    managed_bytes = {
        path: stable_jsonl_bytes(value) if path in JSONL_PATHS else stable_json_bytes(value)
        for path, value in path_values.items()
    }
    # Fail malformed semantic aggregates before deriving their self-referential
    # terminal byte-count records.
    decisions_cover_features_in_order(HierarchyBundleView(records))
    metrics, inventory, completion = _stabilize_terminal_records(
        candidate_id=payload.identity["candidate_id"],
        completion_status=summary["status"],
        measurements=measurements,
        other_managed_bytes=managed_bytes,
    )
    records["metrics"] = metrics
    managed_bytes["records/metrics.json"] = stable_json_bytes(metrics)
    aggregate_records = {key: value for key, value in records.items() if key != "environment"}
    bundle = {**aggregate_records, "artifact_inventory": inventory, "completion": completion}
    validate_candidate_bundle(bundle, schema_path)
    return PreparedCandidate(bundle=bundle, managed_bytes=managed_bytes)


def validate_attempt_record(record: JsonRecord, schema_path: Path) -> None:
    """Validate a failed-attempt record against its schema definition."""
    schema = json.loads(schema_path.read_text())
    Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$ref": "#/$defs/attempt_record",
            "$defs": schema["$defs"],
        }
    ).validate(record)


def validate_candidate_bundle(bundle: JsonRecord, schema_path: Path) -> None:
    """Apply aggregate JSON Schema and human-owned cross-record validation."""
    schema = json.loads(schema_path.read_text())
    Draft202012Validator(schema).validate(bundle)
    validate_hierarchy_inference_bundle(bundle)


def _stabilize_terminal_records(
    *,
    candidate_id: str,
    completion_status: str,
    measurements: CandidateMeasurements,
    other_managed_bytes: Mapping[str, bytes],
) -> tuple[JsonRecord, JsonRecord, JsonRecord]:
    """Set artifact_bytes to all 15 final candidate files by size fixed point."""
    artifact_bytes = sum(len(value) for value in other_managed_bytes.values())
    for _ in range(20):
        metrics = build_metrics(
            candidate_id=candidate_id,
            measurements=measurements,
            artifact_bytes=artifact_bytes,
        )
        metrics_bytes = stable_json_bytes(metrics)
        all_managed_bytes = {
            **other_managed_bytes,
            "records/metrics.json": metrics_bytes,
        }
        inventory: JsonRecord = {
            "files": [
                {
                    "path": path,
                    "byte_size": len(all_managed_bytes[path]),
                    "sha256": _sha256_bytes(all_managed_bytes[path]),
                }
                for path in MANAGED_PAYLOAD_PATHS
            ]
        }
        completion: JsonRecord = {
            "candidate_id": candidate_id,
            "status": completion_status,
            "artifact_inventory_sha256": canonical_json_sha256(inventory),
        }
        next_value = (
            sum(len(value) for value in all_managed_bytes.values())
            + len(stable_json_bytes(inventory))
            + len(stable_json_bytes(completion))
        )
        if next_value == artifact_bytes:
            return metrics, inventory, completion
        artifact_bytes = next_value
    raise ValueError("candidate artifact-byte size did not stabilize")


def _sha256_bytes(value: bytes) -> str:
    """Return one complete in-memory SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()
