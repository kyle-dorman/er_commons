"""Readable application shell for candidate-neutral collection reporting."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from er_commons.artifact_io import directory_bytes
from er_commons.collection_processing.handoff_validation import validate_collection_handoff
from er_commons.extraction_reporting.anomalies import (
    AnomalyPolicy,
    build_anomaly,
    build_resolution_anomaly,
    select_bounded_anomalies,
)
from er_commons.extraction_reporting.candidate_metrics import summarize_candidate
from er_commons.extraction_reporting.collection_metrics import (
    resource_extrema,
    sum_source_metrics,
)
from er_commons.extraction_reporting.inputs import (
    JsonObject,
    VerifiedCollectionEvidence,
    read_json_object,
)


def build_extraction_report(
    *,
    data_root: Path,
    extraction_root: Path,
    scope_id: str,
    schema_path: Path,
    anomaly_policy: AnomalyPolicy,
) -> tuple[JsonObject, list[JsonObject]]:
    """Validate the handoff, then aggregate immutable collection evidence read-only."""
    verified = validate_collection_handoff(
        extraction_root=extraction_root,
        scope_id=scope_id,
        schema_path=schema_path,
        data_root=data_root,
    )
    bundle_path = extraction_root / "scopes" / scope_id / "contract_bundle.json"
    report, anomalies = summarize_verified_collection(
        data_root=data_root,
        extraction_root=extraction_root,
        bundle=read_json_object(bundle_path),
        anomaly_policy=anomaly_policy,
    )
    report["handoff_validation"] = {
        "handoff_id": verified.handoff_id,
        "status": verified.status,
        "verified_document_count": verified.verified_document_count,
        "unavailable_source_count": verified.unavailable_source_count,
        "task04_status": verified.task04_status,
    }
    return report, anomalies


def summarize_verified_collection(
    *,
    data_root: Path,
    extraction_root: Path,
    bundle: JsonObject,
    anomaly_policy: AnomalyPolicy,
) -> tuple[JsonObject, list[JsonObject]]:
    """Summarize a caller-verified bundle without changing candidate bytes."""
    evidence = VerifiedCollectionEvidence.from_bundle(bundle)
    completion_by_source = {
        str(item["source"]["source_id"]): item for item in evidence.document_completions
    }
    sources: list[JsonObject] = []
    anomaly_candidates: list[JsonObject] = []
    candidate_source: dict[str, str] = {}

    for row in evidence.accounting_rows:
        source_id = str(row["source_id"])
        if row["terminal_state"] == "failed_terminal":
            sources.append(_failed_source(source_id, row))
            anomaly_candidates.append(
                build_anomaly(source_id, "terminal_failure", row, "transaction_id")
            )
            continue
        completion = completion_by_source.get(source_id)
        if completion is None:
            raise ValueError(f"successful accounting row lacks document completion: {source_id}")
        candidate_id = str(completion["candidate_id"])
        candidate_source[candidate_id] = source_id
        source_report, source_anomalies = summarize_candidate(
            data_root=data_root,
            extraction_root=extraction_root,
            candidate_root=extraction_root / "documents" / source_id / candidate_id,
            completion=completion,
            accounting_row=row,
        )
        sources.append(source_report)
        anomaly_candidates.extend(source_anomalies)

    for record in evidence.resolution["resolutions"]:
        if record["status"] in {"ambiguous", "unresolved"}:
            source_id = candidate_source.get(str(record["source_candidate_id"]), "unknown")
            anomaly_candidates.append(build_resolution_anomaly(source_id, "collection", record))

    extrema = resource_extrema(sources)
    ordinary_anomalies = select_bounded_anomalies(anomaly_candidates, anomaly_policy)
    extrema_anomalies = _extrema_anomalies(extrema)
    anomalies = [*ordinary_anomalies, *extrema_anomalies]
    report = _collection_report(
        evidence=evidence,
        sources=sources,
        anomalies=anomalies,
        anomaly_candidates=anomaly_candidates,
        ordinary_anomalies=ordinary_anomalies,
        extrema=extrema,
        anomaly_policy=anomaly_policy,
        extraction_root=extraction_root,
    )
    return report, anomalies


def _failed_source(source_id: str, row: JsonObject) -> JsonObject:
    return {
        "source_id": source_id,
        "terminal_state": "failed_terminal",
        "failure_class": row.get("failure_class"),
    }


def _extrema_anomalies(extrema: JsonObject) -> list[JsonObject]:
    return [
        build_anomaly(
            str(record["source_id"]),
            f"deterministic_extremum:{metric}:{bound}",
            record,
            "source_id",
        )
        for metric, bounds in extrema.items()
        for bound, record in bounds.items()
    ]


def _collection_report(
    *,
    evidence: VerifiedCollectionEvidence,
    sources: list[JsonObject],
    anomalies: list[JsonObject],
    anomaly_candidates: list[JsonObject],
    ordinary_anomalies: list[JsonObject],
    extrema: JsonObject,
    anomaly_policy: AnomalyPolicy,
    extraction_root: Path,
) -> JsonObject:
    accounting = evidence.accounting
    resolution = evidence.resolution
    scope_id = str(accounting["scope_id"])
    return {
        "schema_version": "er_commons.extraction_report.v2",
        "scope_id": scope_id,
        "production_extraction_id": evidence.production_extraction_id,
        "task04_status": "not_evaluated",
        "publication_authority": False,
        "sources": sources,
        "totals": sum_source_metrics(sources),
        "collection_processing": {
            "accounting_counts": accounting["counts"],
            "target_index_entry_count": evidence.target_index["entry_count"],
            "eligible_mention_count": resolution["mention_input_manifest"][
                "eligible_mention_count"
            ],
            "resolution_counts": resolution["counts"],
            "handoff_status": evidence.handoff["status"],
        },
        "deterministic_extrema": extrema,
        "anomaly_summary": {
            "candidate_counts": dict(
                sorted(Counter(item["category"] for item in anomaly_candidates).items())
            ),
            "sample_counts": dict(sorted(Counter(item["category"] for item in anomalies).items())),
            "sample_count": len(anomalies),
            "ordinary_sample_count": len(ordinary_anomalies),
            "extrema_count": len(anomalies) - len(ordinary_anomalies),
            "max_examples_per_class": anomaly_policy.max_examples_per_class,
        },
        "scope_artifact_bytes": directory_bytes(extraction_root / "scopes" / scope_id),
    }


__all__ = ["build_extraction_report", "summarize_verified_collection"]
