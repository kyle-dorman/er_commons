"""Candidate-neutral aggregate and anomaly reporting for a verified pilot scope."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256
from er_commons.corpus_resolution.handoff_validation import validate_handoff
from er_commons.corpus_resolution.storage import json_bytes, jsonl_bytes
from er_commons.source_freeze import sha256_file, write_json_atomic

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class AnomalyPolicy:
    """One corpus-wide deterministic cap for source-qualified anomaly samples."""

    max_examples_per_class: int = 5

    def __post_init__(self) -> None:
        if self.max_examples_per_class < 1:
            raise ValueError("anomaly sample cap must be positive")


@dataclass(frozen=True)
class PilotReportArtifacts:
    """Paths for one completion-last candidate-neutral report bundle."""

    report: Path
    anomalies: Path
    inventory: Path
    completion: Path


def build_pilot_report(
    *,
    data_root: Path,
    extraction_root: Path,
    scope_id: str,
    schema_path: Path,
    anomaly_policy: AnomalyPolicy,
) -> tuple[JsonObject, list[JsonObject]]:
    """Validate the handoff, then aggregate immutable pilot evidence read-only."""
    verified = validate_handoff(
        extraction_root=extraction_root,
        scope_id=scope_id,
        schema_path=schema_path,
        data_root=data_root,
    )
    bundle = _json(extraction_root / "scopes" / scope_id / "contract_bundle.json")
    report, anomalies = summarize_verified_pilot(
        data_root=data_root,
        extraction_root=extraction_root,
        bundle=bundle,
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


def summarize_verified_pilot(
    *,
    data_root: Path,
    extraction_root: Path,
    bundle: JsonObject,
    anomaly_policy: AnomalyPolicy,
) -> tuple[JsonObject, list[JsonObject]]:
    """Summarize a caller-verified bundle without changing candidate bytes."""
    completion_by_source = {
        str(item["source"]["source_id"]): item for item in bundle["document_completions"]
    }
    accounting = bundle["accounting"]
    rows = accounting["rows"]
    sources: list[JsonObject] = []
    anomaly_candidates: list[JsonObject] = []
    candidate_source: dict[str, str] = {}
    for row in rows:
        source_id = str(row["source_id"])
        if row["terminal_state"] == "failed_terminal":
            sources.append(
                {
                    "source_id": source_id,
                    "terminal_state": "failed_terminal",
                    "failure_class": row.get("failure_class"),
                }
            )
            anomaly_candidates.append(
                _anomaly(source_id, "terminal_failure", row, "transaction_id")
            )
            continue
        completion = completion_by_source[source_id]
        candidate_id = str(completion["candidate_id"])
        candidate_source[candidate_id] = source_id
        candidate_root = extraction_root / "documents" / source_id / candidate_id
        source_report, source_anomalies = _summarize_candidate(
            data_root=data_root,
            extraction_root=extraction_root,
            candidate_root=candidate_root,
            completion=completion,
            accounting_row=row,
        )
        sources.append(source_report)
        anomaly_candidates.extend(source_anomalies)

    resolution = bundle["resolution_completion"]
    for record in resolution["resolutions"]:
        if record["status"] not in {"ambiguous", "unresolved"}:
            continue
        source_id = candidate_source.get(str(record["source_candidate_id"]), "unknown")
        anomaly_candidates.append(_resolution_anomaly(source_id, "corpus", record))

    totals = _sum_source_metrics(sources)
    extrema = _resource_extrema(sources)
    ordinary_anomalies = _bounded_anomalies(anomaly_candidates, anomaly_policy)
    extrema_anomalies = [
        _anomaly(
            str(record["source_id"]),
            f"deterministic_extremum:{metric}:{bound}",
            record,
            "source_id",
        )
        for metric, bounds in extrema.items()
        for bound, record in bounds.items()
    ]
    anomalies = [*ordinary_anomalies, *extrema_anomalies]
    report: JsonObject = {
        "schema_version": "er_commons.representative_pilot_report.v1",
        "scope_id": accounting["scope_id"],
        "production_extraction_id": bundle["production_extraction_id"],
        "task04_status": "not_evaluated",
        "publication_authority": False,
        "sources": sources,
        "totals": totals,
        "stage_two": {
            "accounting_counts": accounting["counts"],
            "target_index_entry_count": bundle["target_index"]["entry_count"],
            "eligible_mention_count": resolution["mention_input_manifest"][
                "eligible_mention_count"
            ],
            "resolution_counts": resolution["counts"],
            "handoff_status": bundle["handoff"]["status"],
        },
        "deterministic_extrema": extrema,
        "anomaly_summary": {
            "candidate_counts": dict(
                sorted(Counter(item["category"] for item in anomaly_candidates).items())
            ),
            "sample_counts": dict(sorted(Counter(item["category"] for item in anomalies).items())),
            "sample_count": len(anomalies),
            "ordinary_sample_count": len(ordinary_anomalies),
            "extrema_count": len(extrema_anomalies),
            "max_examples_per_class": anomaly_policy.max_examples_per_class,
        },
        "scope_artifact_bytes": _directory_bytes(
            extraction_root / "scopes" / str(accounting["scope_id"])
        ),
    }
    return report, anomalies


def write_pilot_report(
    root: Path,
    *,
    report: JsonObject,
    anomalies: list[JsonObject],
) -> PilotReportArtifacts:
    """Write review evidence with an inventory and non-authoritative completion last."""
    root.mkdir(parents=True, exist_ok=False)
    report_path = root / "pilot_report.json"
    anomaly_path = root / "anomalies.jsonl"
    report_path.write_bytes(json_bytes(report))
    anomaly_path.write_bytes(jsonl_bytes(anomalies))
    inventory_path = root / "artifact_inventory.json"
    inventory = {
        "files": [
            _file_record(report_path, root),
            _file_record(anomaly_path, root),
        ]
    }
    write_json_atomic(inventory_path, inventory)
    completion_path = root / "completion.json"
    write_json_atomic(
        completion_path,
        {
            "schema_version": "er_commons.representative_pilot_report_completion.v1",
            "scope_id": report["scope_id"],
            "status": "review_evidence_complete",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "publication_authority": False,
            "task04_status": "not_evaluated",
            "completion_last": True,
        },
    )
    return PilotReportArtifacts(report_path, anomaly_path, inventory_path, completion_path)


def _summarize_candidate(
    *,
    data_root: Path,
    extraction_root: Path,
    candidate_root: Path,
    completion: JsonObject,
    accounting_row: JsonObject,
) -> tuple[JsonObject, list[JsonObject]]:
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
    collections = {name: _jsonl(path) for name, path in collection_paths.items()}
    identity = _json(candidate_root / "records" / "document_identity.json")
    producer_completion = _verified_reference(
        data_root, identity["stage_completions"]["baseline_producer"]
    )
    producer_root = producer_completion.parents[1]
    producer_inventory = _verified_owner_inventory(producer_root, completion=producer_completion)
    conversion_path = f"documents/{source_id}/producer/docling/conversion_observation.json"
    conversion = _json(_verified_inventory_path(producer_root, producer_inventory, conversion_path))
    producer_anomalies = _producer_anomalies(
        source_id=source_id,
        producer_root=producer_root,
        inventory=producer_inventory,
        conversion=conversion,
    )
    correction_completion = _verified_reference(
        data_root, identity["stage_completions"]["hierarchy_correction"]
    )
    correction_root = correction_completion.parents[1]
    correction_files = _verified_owner_files(
        correction_root,
        completion=correction_completion,
        relatives=(
            "records/summary.json",
            "artifacts/warnings.jsonl",
            "artifacts/ambiguities.jsonl",
        ),
    )
    hierarchy_summary = _json(correction_files["records/summary.json"])
    hierarchy_warnings = _jsonl(correction_files["artifacts/warnings.jsonl"])
    hierarchy_ambiguities = _jsonl(correction_files["artifacts/ambiguities.jsonl"])
    local_statuses = Counter(
        str(row["resolution_status"]) for row in collections["cross_references"]
    )

    observability = _candidate_observability(extraction_root, candidate_root, accounting_row)
    anomalies = [
        *producer_anomalies,
        *(
            _anomaly(
                source_id,
                f"hierarchy_warning:{_record_class(row)}",
                row,
                "stable_item_key",
            )
            for row in hierarchy_warnings
        ),
        *(
            _anomaly(
                source_id,
                f"hierarchy_ambiguity:{_record_class(row)}",
                row,
                "stable_item_key",
            )
            for row in hierarchy_ambiguities
        ),
        *(
            _resolution_anomaly(source_id, "document", row)
            for row in collections["cross_references"]
            if row["resolution_status"] in {"ambiguous", "unresolved"}
        ),
    ]
    return (
        {
            "source_id": source_id,
            "candidate_id": completion["candidate_id"],
            "terminal_state": accounting_row["terminal_state"],
            "metrics": {
                "pages": len(collections["pages"]),
                "tables": len(collections["tables"]),
                "table_families": len(collections["table_families"]),
                "sections": len(collections["sections"]),
                "page_labels": len(collections["page_labels"]),
                "target_aliases": len(collections["target_aliases"]),
                "cross_references": len(collections["cross_references"]),
                "hierarchy_ambiguities": int(hierarchy_summary["ambiguity_count"]),
                "hierarchy_warnings": int(hierarchy_summary["warning_count"]),
                "terminal_warning": int(
                    accounting_row["terminal_state"] == "complete_with_warnings"
                ),
            },
            "local_mention_status_counts": dict(sorted(local_statuses.items())),
            "resources": {
                "wall_seconds": observability["wall_seconds"],
                "peak_rss_bytes": observability["peak_rss_bytes"],
                "output_bytes": observability["output_bytes"],
                "stage_timings": observability["stage_timings"],
            },
        },
        anomalies,
    )


def _candidate_observability(
    extraction_root: Path, candidate_root: Path, accounting_row: JsonObject
) -> JsonObject:
    """Reuse the originating attempt metrics for a downstream-only replay."""
    attempt_ref = accounting_row.get("attempt_record_ref")
    if isinstance(attempt_ref, dict):
        attempt_record = extraction_root / str(attempt_ref["path"])
        return _json(attempt_record.parent / "observability.json")
    replay = _json(candidate_root / "records/downstream_replay.json")
    source_completion = _json(
        extraction_root.parents[2] / str(replay["source_completion_ref"]["path"])
    )
    transaction_id = str(source_completion["transaction_id"])
    matches = sorted((extraction_root / "attempts").glob(f"{transaction_id}.*"))
    if len(matches) != 1:
        raise ValueError("downstream replay lacks one originating attempt")
    return _json(matches[0] / "observability.json")


def _bounded_anomalies(candidates: list[JsonObject], policy: AnomalyPolicy) -> list[JsonObject]:
    selected: list[JsonObject] = []
    categories = sorted({str(row["category"]) for row in candidates})
    for category in categories:
        rows = sorted(
            (row for row in candidates if row["category"] == category),
            key=_anomaly_order,
        )
        first_by_source: dict[str, JsonObject] = {}
        for row in rows:
            first_by_source.setdefault(str(row["source_id"]), row)
        class_sample = [first_by_source[source] for source in sorted(first_by_source)]
        class_sample = class_sample[: policy.max_examples_per_class]
        selected_keys = {
            (row["source_id"], row["record_id"], row["sha256"]) for row in class_sample
        }
        class_sample.extend(
            row
            for row in rows
            if (row["source_id"], row["record_id"], row["sha256"]) not in selected_keys
        )
        selected.extend(class_sample[: policy.max_examples_per_class])
    return selected


def _anomaly_order(row: JsonObject) -> tuple[str, str, str]:
    return (str(row["source_id"]), str(row["record_id"]), str(row["sha256"]))


def _producer_anomalies(
    *,
    source_id: str,
    producer_root: Path,
    inventory: JsonObject,
    conversion: JsonObject,
) -> list[JsonObject]:
    anomalies: list[JsonObject] = []
    for error in conversion.get("errors", []):
        if isinstance(error, dict):
            anomalies.append(
                _anomaly(
                    source_id,
                    f"producer_error:{_record_class(error)}",
                    error,
                    "message",
                )
            )
    for field, warning_class in (
        ("captured_python_warnings", "captured_python"),
        ("source_manifest_warnings", "source_manifest"),
    ):
        for index, warning in enumerate(conversion.get(field, []), start=1):
            record = {"sequence": index, "warning": str(warning)}
            anomalies.append(
                _anomaly(
                    source_id,
                    f"producer_warning:{warning_class}",
                    record,
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
        result = _json(_verified_inventory_path(producer_root, inventory, relative))
        page = result.get("physical_pdf_page")
        evidence = result.get("parser_evidence", {})
        attempts = (
            evidence.get("learned_fallback_attempts", []) if isinstance(evidence, dict) else []
        )
        for attempt in attempts:
            if not isinstance(attempt, dict) or attempt.get("status") != "abstained":
                continue
            record = {"physical_pdf_page": page, **attempt}
            anomalies.append(
                _anomaly(
                    source_id,
                    f"producer_abstention:{attempt.get('reason', 'unknown')}",
                    record,
                    "region_id",
                )
            )
    return anomalies


def _resolution_anomaly(source_id: str, stage: str, record: JsonObject) -> JsonObject:
    status = str(record["status"] if stage == "corpus" else record["resolution_status"])
    detail = record.get("unresolved_reason") or record.get("mention_class") or "unspecified"
    id_field = "mention_id" if stage == "corpus" else "id"
    return _anomaly(
        source_id,
        f"{stage}_cross_reference:{status}:{detail}",
        record,
        id_field,
    )


def _record_class(record: JsonObject) -> str:
    for field in (
        "code",
        "error_code",
        "component_type",
        "module_name",
        "type",
        "kind",
        "exception_type",
    ):
        value = record.get(field)
        if isinstance(value, str) and value:
            return value
    return "unspecified"


def _anomaly(source_id: str, category: str, record: JsonObject, id_field: str) -> JsonObject:
    value = json_bytes(record)
    return {
        "source_id": source_id,
        "category": category,
        "record_id": str(record.get(id_field) or "unknown"),
        "sha256": hashlib.sha256(value).hexdigest(),
        "record": record,
    }


def _sum_source_metrics(sources: list[JsonObject]) -> JsonObject:
    totals: Counter[str] = Counter()
    wall_seconds = 0.0
    output_bytes = 0
    peak_rss_bytes = 0
    for source in sources:
        for name, value in source.get("metrics", {}).items():
            totals[name] += value
        resources = source.get("resources", {})
        wall_seconds += float(resources.get("wall_seconds", 0))
        output_bytes += int(resources.get("output_bytes", 0))
        peak_rss_bytes = max(peak_rss_bytes, int(resources.get("peak_rss_bytes") or 0))
    return {
        **dict(sorted(totals.items())),
        "wall_seconds": wall_seconds,
        "output_bytes": output_bytes,
        "peak_rss_bytes_max": peak_rss_bytes,
    }


def _resource_extrema(sources: list[JsonObject]) -> JsonObject:
    successful = [source for source in sources if "metrics" in source]
    definitions = {
        "tables": ("metrics", "tables"),
        "table_families": ("metrics", "table_families"),
        "wall_seconds": ("resources", "wall_seconds"),
        "peak_rss_bytes": ("resources", "peak_rss_bytes"),
        "output_bytes": ("resources", "output_bytes"),
    }
    extrema: JsonObject = {}
    for metric, (group, field) in definitions.items():
        values = [
            {
                "source_id": source["source_id"],
                "candidate_id": source["candidate_id"],
                "metric": metric,
                "value": source[group][field],
            }
            for source in successful
        ]
        if not values:
            continue
        ordered = sorted(values, key=lambda row: (row["value"], row["source_id"]))
        extrema[metric] = {"minimum": ordered[0], "maximum": ordered[-1]}
    return extrema


def _verified_reference(data_root: Path, reference: JsonObject) -> Path:
    root = data_root.resolve()
    path = (root / str(reference["path"])).resolve()
    if (
        not path.is_relative_to(root)
        or not path.is_file()
        or sha256_file(path) != reference["sha256"]
    ):
        raise ValueError(f"pilot report input reference differs: {reference.get('path')}")
    return path


def _verified_owner_files(
    root: Path,
    *,
    completion: Path,
    relatives: tuple[str, ...],
) -> dict[str, Path]:
    inventory = _verified_owner_inventory(root, completion=completion)
    return {relative: _verified_inventory_path(root, inventory, relative) for relative in relatives}


def _verified_owner_inventory(root: Path, *, completion: Path) -> JsonObject:
    completion_record = _json(completion)
    inventory_path = root / "records" / "artifact_inventory.json"
    if not inventory_path.is_file():
        raise ValueError(f"pilot report owner inventory differs: {root}")
    inventory = _json(inventory_path)
    accepted_seals = {sha256_file(inventory_path), canonical_sha256(inventory)}
    if completion_record.get("artifact_inventory_sha256") not in accepted_seals:
        raise ValueError(f"pilot report owner inventory differs: {root}")
    return inventory


def _verified_inventory_path(root: Path, inventory: JsonObject, relative: str) -> Path:
    entries = {str(item["path"]): item for item in inventory.get("files", [])}
    item = entries.get(relative)
    path = (root / relative).resolve()
    if (
        item is None
        or not path.is_relative_to(root.resolve())
        or not path.is_file()
        or path.stat().st_size != item.get("byte_size")
        or sha256_file(path) != item.get("sha256")
    ):
        raise ValueError(f"pilot report owner artifact differs: {relative}")
    return path


def _json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _jsonl(path: Path) -> list[JsonObject]:
    rows: list[JsonObject] = []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object: {path}:{number}")
        rows.append(value)
    return rows


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _file_record(path: Path, root: Path) -> JsonObject:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }
