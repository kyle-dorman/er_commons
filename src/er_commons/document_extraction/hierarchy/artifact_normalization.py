"""Declared identity and volatility normalization for producer-run comparison."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.hierarchy.document import JsonObject

VOLATILE_KEYS = {
    "completed_at_utc",
    "conversion_cpu_seconds",
    "cpu_seconds",
    "generated_at_utc",
    "output_bytes_before_inventory",
    "page_wall_seconds_sum",
    "peak_rss_bytes",
    "pipeline_wall_seconds",
    "wall_seconds",
}


def load_json_records(path: Path) -> Any:
    """Load one JSON document or ordered JSON Lines collection."""
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line]
    return json.loads(path.read_text())


@dataclass(frozen=True)
class ProducerIdentityValues:
    """Identity strings whose expected changes are normalized across producer runs."""

    run_id: str
    pipeline_id: str
    configuration_id: str

    @classmethod
    def load(cls, root: Path) -> ProducerIdentityValues:
        """Load identity values from one verified producer root."""
        configuration = load_json_records(root / "records/configuration.json")
        identity = load_json_records(root / "records/producer_identity.json")
        if not isinstance(configuration, dict) or not isinstance(identity, dict):
            raise TypeError(f"producer identity records are not objects: {root}")
        return cls(
            run_id=str(identity["producer_run_id"]),
            pipeline_id=str(configuration["pipeline_id"]),
            configuration_id=str(configuration["configuration_id"]),
        )

    def normalize_string(self, value: str) -> str:
        """Replace identity-dependent strings with stable comparison tokens."""
        replacements = (
            (self.run_id, "<PRODUCER_RUN_ID>"),
            (
                f"{self.pipeline_id}_deir_appendix_p_tables",
                "<TABLE_PIPELINE_ID>",
            ),
            (self.pipeline_id, "<PIPELINE_ID>"),
            (self.configuration_id, "<CONFIGURATION_ID>"),
        )
        normalized = value
        for old, new in replacements:
            normalized = normalized.replace(old, new)
        return normalized


def _normalize_generic(value: Any, identity: ProducerIdentityValues) -> Any:
    if isinstance(value, str):
        return identity.normalize_string(value)
    if isinstance(value, list):
        return [_normalize_generic(item, identity) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: _normalize_generic(item, identity)
        for key, item in value.items()
        if key not in VOLATILE_KEYS
    }


def _configuration_projection(value: JsonObject) -> JsonObject:
    projected = dict(value)
    for key in (
        "configuration_id",
        "heading_hierarchy_options",
        "pipeline_id",
        "producer_policy_version",
    ):
        projected.pop(key, None)
    return projected


def _runtime_projection(value: JsonObject) -> JsonObject:
    raw = json.loads(json.dumps(value))
    if not isinstance(raw, dict):
        raise TypeError("runtime projection is not an object")
    projected: JsonObject = raw
    projected.pop("configuration_id", None)
    effective = projected.get("effective_options")
    if isinstance(effective, dict):
        hierarchy = effective.get("heading_hierarchy_options")
        if isinstance(hierarchy, dict):
            hierarchy["enabled"] = "<DECLARED_HIERARCHY_ENABLED>"
    return projected


def _producer_identity_projection(value: JsonObject) -> JsonObject:
    identity = value.get("identity")
    if not isinstance(identity, dict):
        return value
    configuration = identity.get("configuration_policy")
    runtime = identity.get("runtime")
    return {
        "identity_schema_version": identity.get("identity_schema_version"),
        "configuration_policy": (
            _configuration_projection(configuration)
            if isinstance(configuration, dict)
            else configuration
        ),
        "source": identity.get("source"),
        "sealed_release": identity.get("sealed_release"),
        "runtime": _runtime_projection(runtime) if isinstance(runtime, dict) else runtime,
        "model_inventory": identity.get("model_inventory"),
        "routing_sha256": identity.get("routing_sha256"),
        "table_sha256": identity.get("table_sha256"),
        "table_environment": identity.get("table_environment"),
        "package_versions": identity.get("package_versions"),
    }


def normalize_artifact_json(
    relative_path: str,
    value: Any,
    identity: ProducerIdentityValues,
) -> Any:
    """Apply the frozen Task 03E projection for one JSON artifact path."""
    if relative_path == "records/configuration.json" and isinstance(value, dict):
        value = _configuration_projection(value)
    elif relative_path == "records/runtime_configuration.json" and isinstance(value, dict):
        value = _runtime_projection(value)
    elif relative_path == "records/producer_identity.json" and isinstance(value, dict):
        value = _producer_identity_projection(value)
    elif relative_path == "documents/deir_appendix_p/producer/tables/manifest.json" and isinstance(
        value, dict
    ):
        value = dict(value)
        value.pop("configuration_sha256", None)
    elif relative_path in {
        "records/environment.json",
        "documents/deir_appendix_p/producer/tables/environment.json",
    } and isinstance(value, dict):
        value = dict(value)
        value.pop("git_commit", None)
        value.pop("git_dirty", None)
    return _normalize_generic(value, identity)


def normalized_log(path: Path, identity: ProducerIdentityValues) -> list[str]:
    """Remove declared timestamps, timings, and identity values from a producer log."""
    lines = []
    for line in path.read_text().splitlines():
        normalized = re.sub(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} ", "", line)
        normalized = re.sub(
            r"options hash [0-9a-f]+",
            "options hash <CONFIGURATION_ID>",
            normalized,
        )
        normalized = re.sub(
            r"Finished converting (.+) in [0-9.]+ sec\.",
            r"Finished converting \1 in <WALL_SECONDS> sec.",
            normalized,
        )
        lines.append(identity.normalize_string(normalized))
    return lines


def normalized_completion(root: Path) -> JsonObject:
    """Normalize the identity-dependent terminal record for explicit comparison."""
    value = load_json_records(root / "records/completion_record.json")
    if not isinstance(value, dict):
        raise TypeError(f"completion record is not an object: {root}")
    value.pop("artifact_inventory_sha256", None)
    value.pop("completed_at_utc", None)
    value["producer_run_id"] = "<PRODUCER_RUN_ID>"
    return value
