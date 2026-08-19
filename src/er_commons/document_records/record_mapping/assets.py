"""Register canonical producer assets and generated clean-table views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from er_commons.document_records.record_mapping.context import RecordMappingContext
from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.identifiers import make_record_id
from er_commons.document_records.record_mapping.inputs import RecordMappingInputs
from er_commons.document_records.record_mapping.publication import (
    sha256_file,
    write_json,
)
from er_commons.document_records.record_mapping.tables import ProducerTableBundle

CANONICAL_SCHEMA_VERSION = "er_commons.canonical_extraction.v1"
JsonRecord = dict[str, Any]
RawLink = dict[str, Any]


def _readonly_mapping[K, V](values: Mapping[K, V]) -> Mapping[K, V]:
    """Return a read-only copy of one cross-stage lookup."""
    return MappingProxyType(dict(values))


def raw_link(
    producer: str,
    asset_id: str,
    pointer: str,
    provenance_index: int | None = None,
) -> RawLink:
    """Build one canonical raw-object link without retaining mutable state."""
    return {
        "producer": producer,
        "asset_id": asset_id,
        "object_pointer": pointer,
        "provenance_index": provenance_index,
    }


@dataclass(frozen=True)
class AssetCatalog:
    """Immutable asset records and lookup IDs consumed by record builders."""

    records: tuple[JsonRecord, ...]
    raw_docling_asset_id: str
    table_raw_links_by_id: Mapping[str, tuple[RawLink, ...]]
    picture_asset_ids_by_pointer: Mapping[str, str]
    family_assignments_asset_id: str
    table_families_asset_id: str

    def __post_init__(self) -> None:
        """Detach and freeze asset lookup mappings."""
        object.__setattr__(
            self,
            "table_raw_links_by_id",
            _readonly_mapping(self.table_raw_links_by_id),
        )
        object.__setattr__(
            self,
            "picture_asset_ids_by_pointer",
            _readonly_mapping(self.picture_asset_ids_by_pointer),
        )


class _AssetRegistry:
    """Assign deterministic asset IDs in explicit registration order."""

    def __init__(
        self,
        *,
        data_root: Path,
        candidate_root: Path,
        context: RecordMappingContext,
    ) -> None:
        self._data_root = data_root
        self._candidate_root = candidate_root
        self._context = context
        self._records: list[JsonRecord] = []
        self._ids_by_key: dict[str, str] = {}

    @property
    def records(self) -> tuple[JsonRecord, ...]:
        """Return the completed registration sequence without exposing its list."""
        return tuple(self._records)

    def external(
        self,
        *,
        key: str,
        role: str,
        path: Path,
        media_type: str,
        producer: str,
    ) -> str:
        """Register one checksum-pinned file owned outside the candidate."""
        try:
            relative = path.relative_to(self._data_root).as_posix()
        except ValueError as error:
            raise MappingContractError(f"asset escapes ER_COMMONS_DATA_ROOT: {path}") from error
        return self._add(
            key=key,
            role=role,
            path=relative,
            sha256=sha256_file(path),
            byte_size=path.stat().st_size,
            media_type=media_type,
            producer=producer,
        )

    def sealed_external(
        self,
        *,
        key: str,
        role: str,
        path: Path,
        sha256: str,
        byte_size: int,
        media_type: str,
        producer: str,
    ) -> str:
        """Register an immutable owner file using its already sealed digest."""
        try:
            relative = path.relative_to(self._data_root).as_posix()
        except ValueError as error:
            raise MappingContractError(f"asset escapes ER_COMMONS_DATA_ROOT: {path}") from error
        if not path.is_file() or path.stat().st_size != byte_size:
            raise MappingContractError(f"sealed asset path or size differs: {path}")
        return self._add(
            key=key,
            role=role,
            path=relative,
            sha256=sha256,
            byte_size=byte_size,
            media_type=media_type,
            producer=producer,
        )

    def generated(
        self,
        *,
        key: str,
        role: str,
        relative_path: str,
        payload: Any,
        media_type: str,
    ) -> str:
        """Write and register one deterministic candidate-owned JSON asset."""
        path = self._candidate_root / relative_path
        write_json(path, payload)
        return self._add(
            key=key,
            role=role,
            path=relative_path,
            sha256=sha256_file(path),
            byte_size=path.stat().st_size,
            media_type=media_type,
            producer="project",
        )

    def _add(
        self,
        *,
        key: str,
        role: str,
        path: str,
        sha256: str,
        byte_size: int,
        media_type: str,
        producer: str,
    ) -> str:
        if key in self._ids_by_key:
            raise MappingContractError(f"duplicate asset registry key: {key}")
        sequence = len(self._records) + 1
        asset_id = make_record_id(
            self._context.extraction_id,
            "asset",
            self._context.source_id,
            f"{role}/ast{sequence:06d}",
        )
        self._records.append(
            {
                "schema_version": CANONICAL_SCHEMA_VERSION,
                "extraction_id": self._context.extraction_id,
                "id": asset_id,
                "document_id": self._context.document_id,
                "role": role,
                "path": path,
                "sha256": sha256,
                "byte_size": byte_size,
                "media_type": media_type,
                "producer": producer,
            }
        )
        self._ids_by_key[key] = asset_id
        return asset_id


def _register_table_assets(
    *,
    registry: _AssetRegistry,
    candidate_root: Path,
    context: RecordMappingContext,
    tables_root: Path,
    table_bundle: ProducerTableBundle,
) -> dict[str, tuple[RawLink, ...]]:
    links_by_id: dict[str, tuple[RawLink, ...]] = {}
    for table in table_bundle.tables:
        parser_producer = (
            "tableformer_fallback"
            if table.parser == "tableformer_accurate"
            else "camelot_clean_pipeline"
        )
        raw_table_path = tables_root / table.table_record_path
        raw_cells_path = tables_root / table.cells_path
        raw_csv_path = tables_root / table.raw_csv_path
        clean_csv_path = tables_root / table.clean_csv_path
        raw_table_asset = registry.external(
            key=f"{table.table_id}:raw_table",
            role="raw_table_json",
            path=raw_table_path,
            media_type="application/json",
            producer=parser_producer,
        )
        raw_cells_asset = registry.external(
            key=f"{table.table_id}:raw_cells",
            role="raw_table_cells_json",
            path=raw_cells_path,
            media_type="application/json",
            producer=parser_producer,
        )
        raw_csv_asset = registry.external(
            key=f"{table.table_id}:raw_csv",
            role="raw_table_csv",
            path=raw_csv_path,
            media_type="text/csv",
            producer=parser_producer,
        )
        clean_csv_asset = registry.external(
            key=f"{table.table_id}:clean_csv",
            role="clean_table_csv",
            path=clean_csv_path,
            media_type="text/csv",
            producer="camelot_clean_pipeline",
        )
        links_by_id[table.table_id] = (
            raw_link(parser_producer, raw_table_asset, "/"),
            raw_link(parser_producer, raw_cells_asset, "/"),
            raw_link(parser_producer, raw_csv_asset, "/"),
            raw_link("project_cleanup", clean_csv_asset, "/"),
        )
    return links_by_id


def _register_picture_assets(
    *,
    registry: _AssetRegistry,
    inputs: RecordMappingInputs,
) -> dict[str, str]:
    picture_ids: dict[str, str] = {}
    raw_inventory = inputs.asset_inventory.get("assets")
    if not isinstance(raw_inventory, list):
        raise MappingContractError("producer picture asset inventory is invalid")
    for item in raw_inventory:
        if not isinstance(item, dict):
            raise MappingContractError("producer picture asset record is invalid")
        pointer = item.get("raw_object_ref")
        if not isinstance(pointer, str):
            raise MappingContractError("producer picture asset pointer is invalid")
        if pointer in picture_ids:
            raise MappingContractError(f"duplicate picture asset pointer: {pointer}")
        path_value = item.get("path")
        if not isinstance(path_value, str):
            raise MappingContractError(f"picture asset path is invalid: {pointer}")
        path = inputs.conversion_run_root / path_value
        if sha256_file(path) != item.get("sha256") or path.stat().st_size != item.get("byte_size"):
            raise MappingContractError(f"picture asset differs from inventory: {pointer}")
        picture_ids[pointer] = registry.external(
            key=f"picture:{pointer}",
            role="content_image",
            path=path,
            media_type="image/png",
            producer="docling",
        )
    pictures = inputs.document.get("pictures")
    if not isinstance(pictures, list):
        raise MappingContractError("saved Docling picture collection is invalid")
    expected = {f"#/pictures/{index}" for index in range(len(pictures))}
    if set(picture_ids) != expected:
        raise MappingContractError(
            "picture assets do not exactly cover Docling pictures: "
            f"expected={len(expected)} actual={len(picture_ids)}"
        )
    return picture_ids


def materialize_assets(
    *,
    data_root: Path,
    candidate_root: Path,
    context: RecordMappingContext,
    inputs: RecordMappingInputs,
    table_bundle: ProducerTableBundle,
) -> AssetCatalog:
    """Register all producer and generated assets in canonical sequence order."""
    registry = _AssetRegistry(
        data_root=data_root,
        candidate_root=candidate_root,
        context=context,
    )
    producer_root = inputs.document_root / "producer"
    tables_root = producer_root / "tables"
    raw_relative = f"documents/{inputs.selected_source.source_id}/producer/docling/document.json"
    raw_records = inputs.conversion_inventory.get("files")
    if not isinstance(raw_records, list):
        raise MappingContractError("conversion inventory files are invalid")
    raw_matches = [
        record
        for record in raw_records
        if isinstance(record, dict) and record.get("path") == raw_relative
    ]
    if len(raw_matches) != 1:
        raise MappingContractError("raw Docling owner record is missing")
    raw_record = raw_matches[0]
    raw_docling_asset_id = registry.sealed_external(
        key="raw_docling",
        role="raw_docling_json",
        path=inputs.conversion_producer_root / "docling" / "document.json",
        sha256=str(raw_record["sha256"]),
        byte_size=int(raw_record["byte_size"]),
        media_type="application/json",
        producer="docling",
    )
    registry.external(
        key="routing",
        role="routing_jsonl",
        path=producer_root / "routing" / "page_routes.jsonl",
        media_type="application/x-ndjson",
        producer="pdfium_router",
    )
    table_raw_links_by_id = _register_table_assets(
        registry=registry,
        candidate_root=candidate_root,
        context=context,
        tables_root=tables_root,
        table_bundle=table_bundle,
    )
    family_assignments_asset_id = registry.external(
        key="family_assignments",
        role="table_family_assignments_jsonl",
        path=tables_root / "family_assignments.jsonl",
        media_type="application/x-ndjson",
        producer="project",
    )
    table_families_asset_id = registry.external(
        key="table_families",
        role="table_families_json",
        path=tables_root / "table_families.json",
        media_type="application/json",
        producer="project",
    )
    picture_asset_ids_by_pointer = _register_picture_assets(
        registry=registry,
        inputs=inputs,
    )
    return AssetCatalog(
        records=registry.records,
        raw_docling_asset_id=raw_docling_asset_id,
        table_raw_links_by_id=table_raw_links_by_id,
        picture_asset_ids_by_pointer=picture_asset_ids_by_pointer,
        family_assignments_asset_id=family_assignments_asset_id,
        table_families_asset_id=table_families_asset_id,
    )
