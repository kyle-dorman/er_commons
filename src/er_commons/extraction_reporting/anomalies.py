"""Deterministic anomaly records and bounded collection-wide sampling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.artifact_io import json_bytes, sha256_bytes

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class AnomalyPolicy:
    """One collection-wide cap for source-qualified anomaly samples."""

    max_examples_per_class: int = 5

    def __post_init__(self) -> None:
        if self.max_examples_per_class < 1:
            raise ValueError("anomaly sample cap must be positive")


def build_anomaly(
    source_id: str,
    category: str,
    record: JsonObject,
    id_field: str,
) -> JsonObject:
    """Build one stable source-qualified anomaly record."""
    return {
        "source_id": source_id,
        "category": category,
        "record_id": str(record.get(id_field) or "unknown"),
        "sha256": sha256_bytes(json_bytes(record)),
        "record": record,
    }


def build_resolution_anomaly(
    source_id: str,
    stage: str,
    record: JsonObject,
) -> JsonObject:
    """Describe one unresolved or ambiguous document/collection reference."""
    status_field = "status" if stage == "collection" else "resolution_status"
    status = str(record[status_field])
    detail = record.get("unresolved_reason") or record.get("mention_class") or "unspecified"
    id_field = "mention_id" if stage == "collection" else "id"
    return build_anomaly(
        source_id,
        f"{stage}_cross_reference:{status}:{detail}",
        record,
        id_field,
    )


def select_bounded_anomalies(
    candidates: list[JsonObject],
    policy: AnomalyPolicy,
) -> list[JsonObject]:
    """Select deterministic samples while representing sources before repeats."""
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


def record_class(record: JsonObject) -> str:
    """Return the first stable classifier present on an evidence record."""
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


def _anomaly_order(row: JsonObject) -> tuple[str, str, str]:
    return (str(row["source_id"]), str(row["record_id"]), str(row["sha256"]))


__all__ = [
    "AnomalyPolicy",
    "build_anomaly",
    "build_resolution_anomaly",
    "record_class",
    "select_bounded_anomalies",
]
