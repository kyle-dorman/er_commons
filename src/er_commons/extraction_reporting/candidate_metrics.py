"""Per-document metrics and anomaly evidence for extraction reports."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from er_commons.extraction_reporting.anomalies import (
    build_anomaly,
    build_resolution_anomaly,
    record_class,
)
from er_commons.extraction_reporting.inputs import (
    JsonObject,
    product_completion,
    read_json_object,
    read_jsonl_objects,
    verified_inventory,
    verified_inventory_path,
    verified_reference,
)


@dataclass(frozen=True)
class CandidateEvidence:
    """Verified records needed to report one published document."""

    source_id: str
    collections: dict[str, list[JsonObject]]
    content_root: Path
    content_inventory: JsonObject
    conversion: JsonObject
    hierarchy_summary: JsonObject
    hierarchy_warnings: list[JsonObject]
    hierarchy_ambiguities: list[JsonObject]
    observability: JsonObject


def summarize_candidate(
    *,
    data_root: Path,
    extraction_root: Path,
    candidate_root: Path,
    completion: JsonObject,
    accounting_row: JsonObject,
) -> tuple[JsonObject, list[JsonObject]]:
    """Summarize one verified document candidate and its diagnostic evidence."""
    evidence = _load_candidate_evidence(
        data_root=data_root,
        extraction_root=extraction_root,
        candidate_root=candidate_root,
        completion=completion,
        accounting_row=accounting_row,
    )
    local_statuses = Counter(
        str(row["resolution_status"]) for row in evidence.collections["cross_references"]
    )
    anomalies = _candidate_anomalies(evidence)
    metrics = {
        name: len(evidence.collections[name])
        for name in (
            "pages",
            "tables",
            "table_families",
            "sections",
            "page_labels",
            "target_aliases",
            "cross_references",
        )
    }
    metrics.update(
        {
            "hierarchy_ambiguities": int(evidence.hierarchy_summary["ambiguity_count"]),
            "hierarchy_warnings": int(evidence.hierarchy_summary["warning_count"]),
            "terminal_warning": int(accounting_row["terminal_state"] == "complete_with_warnings"),
        }
    )
    return (
        {
            "source_id": evidence.source_id,
            "candidate_id": completion["candidate_id"],
            "terminal_state": accounting_row["terminal_state"],
            "metrics": metrics,
            "local_mention_status_counts": dict(sorted(local_statuses.items())),
            "resources": {
                "wall_seconds": evidence.observability["wall_seconds"],
                "peak_rss_bytes": evidence.observability["peak_rss_bytes"],
                "output_bytes": evidence.observability["output_bytes"],
                "stage_timings": evidence.observability["stage_timings"],
            },
        },
        anomalies,
    )


def _load_candidate_evidence(
    *,
    data_root: Path,
    extraction_root: Path,
    candidate_root: Path,
    completion: JsonObject,
    accounting_row: JsonObject,
) -> CandidateEvidence:
    """Load and verify the product inputs required for one source report."""
    source_id = str(completion["source"]["source_id"])
    canonical = candidate_root / "content" / "canonical"
    collection_paths = {
        "pages": canonical / "pages.jsonl",
        "tables": canonical / "tables.jsonl",
        "table_families": canonical / "table_families.jsonl",
        "sections": canonical / "sections.jsonl",
        "page_labels": candidate_root / "content/observations/page_labels.jsonl",
        "target_aliases": canonical / "target_aliases.jsonl",
        "cross_references": canonical / "cross_references.jsonl",
    }
    collections = {name: read_jsonl_objects(path) for name, path in collection_paths.items()}
    identity = read_json_object(candidate_root / "records" / "document_identity.json")

    content_completion = verified_reference(
        data_root,
        product_completion(identity, "stable_content_evidence"),
        role=f"{source_id} stable content completion",
    )
    content_root = content_completion.parents[1]
    content_inventory = verified_inventory(
        content_root,
        completion=content_completion,
        role=f"{source_id} stable content",
    )
    conversion_relative = f"documents/{source_id}/producer/docling/conversion_observation.json"
    conversion = read_json_object(
        verified_inventory_path(
            content_root,
            content_inventory,
            conversion_relative,
            role=f"{source_id} stable content",
        )
    )

    hierarchy_completion = verified_reference(
        data_root,
        product_completion(identity, "hierarchy_decisions"),
        role=f"{source_id} hierarchy completion",
    )
    hierarchy_root = hierarchy_completion.parents[1]
    hierarchy_inventory = verified_inventory(
        hierarchy_root,
        completion=hierarchy_completion,
        role=f"{source_id} hierarchy",
    )
    hierarchy_files = {
        relative: verified_inventory_path(
            hierarchy_root,
            hierarchy_inventory,
            relative,
            role=f"{source_id} hierarchy",
        )
        for relative in (
            "records/summary.json",
            "artifacts/warnings.jsonl",
            "artifacts/ambiguities.jsonl",
        )
    }
    return CandidateEvidence(
        source_id=source_id,
        collections=collections,
        content_root=content_root,
        content_inventory=content_inventory,
        conversion=conversion,
        hierarchy_summary=read_json_object(hierarchy_files["records/summary.json"]),
        hierarchy_warnings=read_jsonl_objects(hierarchy_files["artifacts/warnings.jsonl"]),
        hierarchy_ambiguities=read_jsonl_objects(hierarchy_files["artifacts/ambiguities.jsonl"]),
        observability=candidate_observability(
            extraction_root,
            candidate_root,
            accounting_row,
            source_id=source_id,
        ),
    )


def _candidate_anomalies(evidence: CandidateEvidence) -> list[JsonObject]:
    """Combine content, hierarchy, and document-reference anomaly evidence."""
    return [
        *content_anomalies(
            source_id=evidence.source_id,
            content_root=evidence.content_root,
            inventory=evidence.content_inventory,
            conversion=evidence.conversion,
        ),
        *(
            build_anomaly(
                evidence.source_id,
                f"hierarchy_warning:{record_class(row)}",
                row,
                "stable_item_key",
            )
            for row in evidence.hierarchy_warnings
        ),
        *(
            build_anomaly(
                evidence.source_id,
                f"hierarchy_ambiguity:{record_class(row)}",
                row,
                "stable_item_key",
            )
            for row in evidence.hierarchy_ambiguities
        ),
        *(
            build_resolution_anomaly(evidence.source_id, "document", row)
            for row in evidence.collections["cross_references"]
            if row["resolution_status"] in {"ambiguous", "unresolved"}
        ),
    ]


def candidate_observability(
    extraction_root: Path,
    candidate_root: Path,
    accounting_row: JsonObject,
    *,
    source_id: str,
) -> JsonObject:
    """Read metrics from the direct attempt or the one replay origin."""
    attempt_ref = accounting_row.get("attempt_record_ref")
    if isinstance(attempt_ref, dict):
        attempt_record = extraction_root / str(attempt_ref["path"])
        return read_json_object(attempt_record.parent / "observability.json")
    replay = read_json_object(candidate_root / "records/downstream_replay.json")
    source_completion = read_json_object(
        extraction_root.parents[2] / str(replay["source_completion_ref"]["path"])
    )
    transaction_id = str(source_completion["transaction_id"])
    matches = sorted((extraction_root / "attempts").glob(f"{transaction_id}.*"))
    if len(matches) != 1:
        raise ValueError(
            "downstream replay lacks one originating attempt: "
            f"source={source_id}, transaction={transaction_id}, matches={len(matches)}"
        )
    return read_json_object(matches[0] / "observability.json")


def content_anomalies(
    *,
    source_id: str,
    content_root: Path,
    inventory: JsonObject,
    conversion: JsonObject,
) -> list[JsonObject]:
    """Collect parser errors, warnings, and learned-fallback abstentions."""
    anomalies: list[JsonObject] = []
    for error in conversion.get("errors", []):
        if isinstance(error, dict):
            anomalies.append(
                build_anomaly(
                    source_id,
                    f"producer_error:{record_class(error)}",
                    error,
                    "message",
                )
            )
    for field, warning_class in (
        ("captured_python_warnings", "captured_python"),
        ("source_manifest_warnings", "source_manifest"),
    ):
        for index, warning in enumerate(conversion.get(field, []), start=1):
            anomalies.append(
                build_anomaly(
                    source_id,
                    f"producer_warning:{warning_class}",
                    {"sequence": index, "warning": str(warning)},
                    "sequence",
                )
            )
    result_paths = sorted(
        str(item["path"])
        for item in inventory.get("files", [])
        if str(item.get("path", "")).endswith("/result.json")
        and "/tables/pages/page_" in str(item.get("path", ""))
    )
    for relative in result_paths:
        result = read_json_object(
            verified_inventory_path(
                content_root,
                inventory,
                relative,
                role=f"{source_id} stable content",
            )
        )
        evidence = result.get("parser_evidence", {})
        attempts = (
            evidence.get("learned_fallback_attempts", []) if isinstance(evidence, dict) else []
        )
        for attempt in attempts:
            if not isinstance(attempt, dict) or attempt.get("status") != "abstained":
                continue
            record = {"physical_pdf_page": result.get("physical_pdf_page"), **attempt}
            anomalies.append(
                build_anomaly(
                    source_id,
                    f"producer_abstention:{attempt.get('reason', 'unknown')}",
                    record,
                    "region_id",
                )
            )
    return anomalies


__all__ = ["summarize_candidate"]
