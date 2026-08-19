"""Verify and load sealed producer artifacts without parser reconstruction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained, read_json_object
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.records import (
    CompletionRecord,
    ConversionObservation,
    PageRouteRecord,
    ProducerSummary,
)
from er_commons.document_parsing.content_parsing.references import (
    ResolvedConversionInput,
    inventory_file_record,
    load_conversion_document,
    resolve_conversion_input,
)
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest
from er_commons.document_records.record_mapping.config import RecordMappingConfig
from er_commons.source_release.models import SourceManifest, SourceRecord, SourceRole

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class RecordMappingIdentityInputs:
    """Small verified records needed to derive an extraction identity."""

    conversion_identity: JsonObject
    conversion_runtime: JsonObject
    sealed_manifest: SourceManifest
    selected_source: SourceRecord
    producer_identity: JsonObject
    producer_completion_record: CompletionRecord


@dataclass(frozen=True)
class RecordMappingInputs:
    """Verified plain-data view of one complete-document producer handoff."""

    producer_run_root: Path
    document_root: Path
    conversion_run_root: Path
    conversion_producer_root: Path
    conversion_inventory: JsonObject
    conversion_identity: JsonObject
    conversion_runtime: JsonObject
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


@dataclass(frozen=True)
class PreparedRecordMappingInputs:
    """Verified seal metadata reusable for identity and semantic input loads."""

    producer_run_root: Path
    document_root: Path
    producer_root: Path
    conversion: ResolvedConversionInput
    conversion_producer_root: Path
    sealed_manifest: SourceManifest
    selected_source: SourceRecord
    producer_identity: JsonObject
    producer_completion: CompletionRecord
    conversion_identity: JsonObject
    conversion_runtime: JsonObject

    def identity_inputs(self) -> RecordMappingIdentityInputs:
        """Project the small identity-bearing records used for reuse lookup."""
        return RecordMappingIdentityInputs(
            conversion_identity=self.conversion_identity,
            conversion_runtime=self.conversion_runtime,
            sealed_manifest=self.sealed_manifest,
            selected_source=self.selected_source,
            producer_identity=self.producer_identity,
            producer_completion_record=self.producer_completion,
        )

    def semantic_inputs(self) -> RecordMappingInputs:
        """Extend this verified metadata with large semantic producer payloads."""
        conversion_prefix = f"documents/{self.selected_source.source_id}/producer"
        for relative in (
            f"{conversion_prefix}/docling/document.json",
            f"{conversion_prefix}/docling/conversion_observation.json",
            f"{conversion_prefix}/asset_inventory.json",
        ):
            inventory_file_record(self.conversion, relative)
        records_root = self.producer_run_root / "records"
        return RecordMappingInputs(
            producer_run_root=self.producer_run_root,
            document_root=self.document_root,
            conversion_run_root=self.conversion.root,
            conversion_producer_root=self.conversion_producer_root,
            conversion_inventory=self.conversion.inventory,
            conversion_identity=self.conversion_identity,
            conversion_runtime=self.conversion_runtime,
            sealed_manifest=self.sealed_manifest,
            selected_source=self.selected_source,
            producer_identity=self.producer_identity,
            producer_summary_record=ProducerSummary.model_validate_json(
                (records_root / "producer_summary.json").read_bytes()
            ),
            producer_completion_record=self.producer_completion,
            document=load_conversion_document(
                self.conversion, source_id=self.selected_source.source_id
            ),
            conversion_observation_record=ConversionObservation.model_validate_json(
                (self.conversion_producer_root / "docling/conversion_observation.json").read_bytes()
            ),
            page_route_records=tuple(
                PageRouteRecord.model_validate(record)
                for record in _load_jsonl_objects(self.producer_root / "routing/page_routes.jsonl")
            ),
            asset_inventory=_load_json_object(
                self.conversion_producer_root / "asset_inventory.json"
            ),
        )


def _load_json_object(path: Path) -> JsonObject:
    """Load one preserved JSON object without parser-model revalidation."""
    return read_json_object(path)


def _load_jsonl_objects(path: Path) -> tuple[JsonObject, ...]:
    """Load preserved JSONL objects in their serialized producer order."""
    records: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL artifact {path}:{line_number}: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object in artifact {path}:{line_number}")
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
            raise ValueError(f"selected source {label} differs from record-mapping config")
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
            raise ValueError(f"producer {label} differs from record-mapping config")


def prepare_record_mapping_inputs(
    data_root: Path,
    config: RecordMappingConfig,
) -> PreparedRecordMappingInputs:
    """Verify immutable seals and load only small identity records."""
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
        raise ValueError("sealed source release differs from record-mapping config")
    selected_source = _verify_selected_source(config, manifest_model)

    records_root = producer_run_root / "records"
    document_root = (
        producer_run_root / "documents" / config.ordered_materialization_scope[0].source_id
    )
    producer_root = document_root / "producer"
    conversion = resolve_conversion_input(data_root, records_root / "conversion_input.json")
    conversion_prefix = f"documents/{selected_source.source_id}/producer"
    for relative in ("records/conversion_identity.json", "records/runtime_configuration.json"):
        inventory_file_record(conversion, relative)
    conversion_producer_root = conversion.root / conversion_prefix

    producer_identity = _load_json_object(records_root / "producer_identity.json")
    producer_completion = CompletionRecord.model_validate_json(
        (records_root / "completion_record.json").read_bytes()
    )
    _verify_producer_selection(config, producer_identity, producer_completion)

    return PreparedRecordMappingInputs(
        producer_run_root=producer_run_root,
        document_root=document_root,
        producer_root=producer_root,
        conversion=conversion,
        conversion_producer_root=conversion_producer_root,
        conversion_identity=_load_json_object(conversion.root / "records/conversion_identity.json"),
        conversion_runtime=_load_json_object(
            conversion.root / "records/runtime_configuration.json"
        ),
        sealed_manifest=manifest_model,
        selected_source=selected_source,
        producer_identity=producer_identity,
        producer_completion=producer_completion,
    )


def load_record_mapping_identity_inputs(
    data_root: Path,
    config: RecordMappingConfig,
) -> RecordMappingIdentityInputs:
    """Load only small verified records needed for candidate reuse lookup."""
    return prepare_record_mapping_inputs(data_root, config).identity_inputs()


def load_record_mapping_inputs(
    data_root: Path,
    config: RecordMappingConfig,
) -> RecordMappingInputs:
    """Verify immutable seals, then load the semantic producer payloads."""
    return prepare_record_mapping_inputs(data_root, config).semantic_inputs()
