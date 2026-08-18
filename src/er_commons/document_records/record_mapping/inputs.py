"""Verify and load preserved Task 03C.1 artifacts without parser reconstruction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.records import (
    CompletionRecord,
    ConversionObservation,
    PageRouteRecord,
    ProducerSummary,
)
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest
from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.source_release.models import SourceManifest, SourceRecord, SourceRole

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class RecordMappingInputs:
    """Verified plain-data view of the complete Appendix P producer handoff."""

    producer_run_root: Path
    document_root: Path
    sealed_manifest: SourceManifest
    selected_source: SourceRecord
    producer_identity: JsonObject
    producer_summary_record: ProducerSummary
    producer_completion_record: CompletionRecord
    document: JsonObject
    conversion_observation_record: ConversionObservation
    page_route_records: tuple[PageRouteRecord, ...]
    asset_inventory: JsonObject


@dataclass
class _ReleaseSelection:
    """Adapt the frozen pilot config to the shared source-seal verifier."""

    source_release_version: str
    source_manifest_path: Path


def _load_json_object(path: Path) -> JsonObject:
    """Load one preserved JSON object without parser-model revalidation."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _load_jsonl_objects(path: Path) -> tuple[JsonObject, ...]:
    """Load preserved JSONL objects in their serialized producer order."""
    records: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected a JSON object at {path}:{line_number}")
        records.append(value)
    return tuple(records)


def _verify_selected_source(
    config: RecordMappingConfig,
    source_manifest: SourceManifest,
) -> SourceRecord:
    """Match the one-document scope to exactly one sealed model-corpus record."""
    selected = config.ordered_materialization_scope[0]
    matches = [
        record for record in source_manifest.sources if record.source_id == selected.source_id
    ]
    if len(matches) != 1:
        raise ValueError("sealed manifest must contain exactly one selected source record")
    record = matches[0]
    if record.source_role != SourceRole.MODEL_CORPUS:
        raise ValueError("selected record-mapping source is not model_corpus")
    expected = (
        (record.sha256, selected.source_sha256, "checksum"),
        (record.pdf_page_count, selected.pdf_page_count, "page count"),
    )
    for actual, configured, label in expected:
        if actual != configured:
            raise ValueError(f"selected source {label} differs from Task 03D config")
    return record


def _verify_producer_selection(
    config: RecordMappingConfig,
    producer_identity: JsonObject,
    producer_completion: CompletionRecord,
) -> None:
    """Require the verified run to describe the exact configured source and run."""
    selected = config.ordered_materialization_scope[0]
    identity = producer_identity.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("producer identity payload is missing")
    source = identity.get("source")
    if not isinstance(source, dict):
        raise ValueError("producer source identity is missing")
    expected = (
        (producer_identity.get("producer_run_id"), config.producer_run_id, "identity run ID"),
        (producer_completion.producer_run_id, config.producer_run_id, "completion run ID"),
        (source.get("source_id"), selected.source_id, "source ID"),
        (source.get("sha256"), selected.source_sha256, "source checksum"),
        (source.get("pdf_page_count"), selected.pdf_page_count, "source page count"),
    )
    for actual, configured, label in expected:
        if actual != configured:
            raise ValueError(f"producer {label} differs from Task 03D config")


def load_record_mapping_inputs(
    data_root: Path,
    config: RecordMappingConfig,
) -> RecordMappingInputs:
    """Verify immutable seals, then load the saved producer dictionaries directly."""
    producer_task_root = assert_contained(
        data_root,
        config.producer_artifact_relative_root.as_posix(),
    )
    producer_run_root = producer_task_root / config.producer_run_id
    verify_completed_run(producer_run_root, config.producer_run_id)

    manifest_model = load_sealed_manifest(
        data_root,
        _ReleaseSelection(
            source_release_version=config.source_release_version,
            source_manifest_path=config.source_manifest_relative_path,
        ),
    )
    if manifest_model.source_release_version != config.source_release_version:
        raise ValueError("sealed source release differs from Task 03D config")
    selected_source = _verify_selected_source(config, manifest_model)

    records_root = producer_run_root / "records"
    document_root = (
        producer_run_root / "documents" / config.ordered_materialization_scope[0].source_id
    )
    producer_root = document_root / "producer"

    producer_identity = _load_json_object(records_root / "producer_identity.json")
    producer_completion = CompletionRecord.model_validate_json(
        (records_root / "completion_record.json").read_bytes()
    )
    _verify_producer_selection(config, producer_identity, producer_completion)

    return RecordMappingInputs(
        producer_run_root=producer_run_root,
        document_root=document_root,
        sealed_manifest=manifest_model,
        selected_source=selected_source,
        producer_identity=producer_identity,
        producer_summary_record=ProducerSummary.model_validate_json(
            (records_root / "producer_summary.json").read_bytes()
        ),
        producer_completion_record=producer_completion,
        document=_load_json_object(producer_root / "docling" / "document.json"),
        conversion_observation_record=ConversionObservation.model_validate_json(
            (producer_root / "docling" / "conversion_observation.json").read_bytes()
        ),
        page_route_records=tuple(
            PageRouteRecord.model_validate(record)
            for record in _load_jsonl_objects(producer_root / "routing" / "page_routes.jsonl")
        ),
        asset_inventory=_load_json_object(producer_root / "asset_inventory.json"),
    )
