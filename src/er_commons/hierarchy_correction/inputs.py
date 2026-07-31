"""Verify and load immutable Task 03E producer inputs without reconstruction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.producer_artifacts import verify_completed_run
from er_commons.document_extraction.producer_config import CompleteSource
from er_commons.document_extraction.producer_records import CompletionRecord
from er_commons.document_extraction.sources import (
    CompleteResolvedSource,
    load_sealed_manifest,
    resolve_complete_source,
)
from er_commons.hierarchy_correction.configuration import HierarchyCorrectionConfig
from er_commons.source_freeze import SourceManifest, assert_contained, sha256_file

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class HierarchyCorrectionInputs:
    """Verified plain-data view of the candidate-producing correction inputs."""

    producer_run_root: Path
    sealed_manifest: SourceManifest
    selected_source: CompleteResolvedSource
    producer_completion: CompletionRecord
    producer_identity: JsonObject
    document: JsonObject
    conversion_pages: JsonObject
    input_inventory: JsonObject


@dataclass
class _ReleaseSelection:
    """Adapt strict correction config to the shared source-seal verifier."""

    source_release_version: str
    source_manifest_path: Path


def _load_json_object(path: Path) -> JsonObject:
    """Load one persisted JSON object and reject other top-level shapes."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _verify_producer_identity(
    config: HierarchyCorrectionConfig,
    completion: CompletionRecord,
    producer_identity: JsonObject,
) -> None:
    """Require completion and identity to name the configured producer source."""
    identity = producer_identity.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("producer identity payload is missing")
    source = identity.get("source")
    if not isinstance(source, dict):
        raise ValueError("producer source identity is missing")
    expected = (
        (producer_identity.get("producer_run_id"), config.producer_run_id, "identity run ID"),
        (completion.producer_run_id, config.producer_run_id, "completion run ID"),
        (completion.source_id, config.source.source_id, "completion source ID"),
        (completion.source_sha256, config.source.expected_sha256, "completion source checksum"),
        (source.get("source_id"), config.source.source_id, "identity source ID"),
        (source.get("sha256"), config.source.expected_sha256, "identity source checksum"),
    )
    for actual, frozen, label in expected:
        if actual != frozen:
            raise ValueError(f"producer {label} differs from Task 03E.2 config")


def load_hierarchy_correction_inputs(
    data_root: Path,
    config: HierarchyCorrectionConfig,
) -> HierarchyCorrectionInputs:
    """Verify exact producer inventory and sealed source before semantic reads."""
    producer_task_root = assert_contained(
        data_root,
        config.producer_artifact_relative_root.as_posix(),
    )
    producer_run_root = producer_task_root / config.producer_run_id
    completion_path = verify_completed_run(producer_run_root, config.producer_run_id)

    manifest = load_sealed_manifest(
        data_root,
        _ReleaseSelection(
            source_release_version=config.source_release_version,
            source_manifest_path=config.source_manifest_relative_path,
        ),
    )
    selected_source = resolve_complete_source(
        data_root,
        CompleteSource.model_validate(config.source.model_dump()),
        manifest,
    )
    records_root = producer_run_root / "records"
    inventory_path = records_root / "artifact_inventory.json"
    completion = CompletionRecord.model_validate_json(completion_path.read_bytes())
    producer_identity = _load_json_object(records_root / "producer_identity.json")
    _verify_producer_identity(config, completion, producer_identity)

    manifest_path = assert_contained(
        data_root,
        config.source_manifest_relative_path.as_posix(),
    )
    if completion.source_manifest_sha256 != sha256_file(manifest_path):
        raise ValueError("producer source-manifest checksum differs from sealed manifest")

    document_root = producer_run_root / "documents" / config.source.source_id / "producer"
    document_path = document_root / "docling" / "document.json"
    conversion_pages_path = document_root / "docling" / "conversion_pages.json"
    input_inventory: JsonObject = {
        "producer_completion_path": completion_path.relative_to(data_root).as_posix(),
        "producer_completion_sha256": sha256_file(completion_path),
        "producer_inventory_path": inventory_path.relative_to(data_root).as_posix(),
        "producer_inventory_sha256": sha256_file(inventory_path),
        "source_path": selected_source.source_path.relative_to(data_root).as_posix(),
        "source_sha256": selected_source.source_sha256,
        "verified_file_count": 3,
    }
    return HierarchyCorrectionInputs(
        producer_run_root=producer_run_root,
        sealed_manifest=manifest,
        selected_source=selected_source,
        producer_completion=completion,
        producer_identity=producer_identity,
        document=_load_json_object(document_path),
        conversion_pages=_load_json_object(conversion_pages_path),
        input_inventory=input_inventory,
    )
