"""Load, namespace, and order immutable Task 03D.1 canonical records."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError

JsonObject = dict[str, Any]

BASELINE_COLLECTION_PATHS = {
    "documents": "canonical/documents.jsonl",
    "pages": "canonical/pages.jsonl",
    "sections": "canonical/sections.jsonl",
    "blocks": "canonical/blocks.jsonl",
    "tables": "canonical/tables.jsonl",
    "table_families": "canonical/table_families.jsonl",
    "figures": "canonical/figures.jsonl",
    "images": "canonical/images.jsonl",
    "assets": "canonical/assets.jsonl",
    "cross_references": "canonical/cross_references.jsonl",
    "routing_observations": "observations/routing.jsonl",
    "table_stage_observations": "observations/table_stage.jsonl",
    "conversion_observations": "observations/conversion.jsonl",
    "raw_mappings": "mappings/raw_to_canonical.jsonl",
}


@dataclass(frozen=True)
class BaselineCandidate:
    """Immutable Task 03D.1 collections in their persisted family order."""

    collections: dict[str, list[JsonObject]]


def load_baseline_candidate(root: Path) -> BaselineCandidate:
    """Load every v1 family named by the sealed baseline layout."""
    return BaselineCandidate(
        {
            family: _load_jsonl(root / relative)
            for family, relative in BASELINE_COLLECTION_PATHS.items()
        }
    )


def remap_candidate_namespace(
    baseline: BaselineCandidate,
    *,
    old_extraction_id: str,
    new_extraction_id: str,
) -> dict[str, list[JsonObject]]:
    """Copy unchanged baseline records into the v2 candidate namespace."""
    remapped = _replace_extraction_id(
        copy.deepcopy(baseline.collections), old_extraction_id, new_extraction_id
    )
    collections = cast(dict[str, list[JsonObject]], remapped)
    for records in collections.values():
        for record in records:
            record["schema_version"] = "er_commons.canonical_extraction.v2"
    return collections


def prepare_semantic_content_in_place(
    collections: dict[str, list[JsonObject]],
) -> list[JsonObject]:
    """Add transient placement fields and return content in retained mixed order."""
    content_by_id: dict[str, JsonObject] = {}
    for record_type, family in (("block", "blocks"), ("table", "tables"), ("figure", "figures")):
        for record in collections[family]:
            record["record_type"] = record_type
            record.setdefault("content_layer", "body")
            content_by_id[record["id"]] = record
    ordered_ids = list(
        dict.fromkeys(
            record_id for page in collections["pages"] for record_id in page["ordered_content_ids"]
        )
    )
    if set(ordered_ids) != set(content_by_id):
        raise SemanticMaterializationInvariantError(
            stage="baseline ordering",
            invariant="page mixed order covers canonical content exactly",
            expected=len(content_by_id),
            observed=len(ordered_ids),
            subject="Task 03D.1 candidate",
        )
    return [content_by_id[record_id] for record_id in ordered_ids]


def restore_placed_content_families_in_place(
    collections: dict[str, list[JsonObject]], placed_content: list[JsonObject]
) -> None:
    """Remove transient fields and restore persisted record-family order."""
    placed_by_id = {record["id"]: record for record in placed_content}
    for family, expected_type in (("blocks", "block"), ("tables", "table"), ("figures", "figure")):
        records = [placed_by_id[record["id"]] for record in collections[family]]
        for record in records:
            actual_type = record.pop("record_type", None)
            if actual_type != expected_type:
                raise SemanticMaterializationInvariantError(
                    stage="semantic placement",
                    invariant="placed content retains its source record family",
                    expected=expected_type,
                    observed=actual_type,
                    subject=record["id"],
                )
        collections[family] = records


def _load_jsonl(path: Path) -> list[JsonObject]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _replace_extraction_id(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [_replace_extraction_id(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: _replace_extraction_id(item, old, new) for key, item in value.items()}
    return value
