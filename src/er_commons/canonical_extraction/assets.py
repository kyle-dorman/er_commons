"""Register canonical producer assets and generated clean-table views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from er_commons.canonical_extraction.context import MaterializationContext
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.identifiers import make_record_id
from er_commons.canonical_extraction.inputs import CanonicalizationInputs
from er_commons.canonical_extraction.publication import (
    sha256_file,
    write_json,
)
from er_commons.canonical_extraction.tables import ProducerTableBundle

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
        context: MaterializationContext,
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
            raise ContractError(f"asset escapes ER_COMMONS_DATA_ROOT: {path}") from error
        return self._add(
            key=key,
            role=role,
            path=relative,
            sha256=sha256_file(path),
            byte_size=path.stat().st_size,
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
            raise ContractError(f"duplicate asset registry key: {key}")
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
    context: MaterializationContext,
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
        clean_cells_payload = [
            {
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                **(cell.span_fields() if table.parser == "tableformer_accurate" else {}),
                "text": cell.text,
                "bbox_pdf_points_bottom_left": list(cell.bbox_pdf_points_bottom_left),
            }
            for cell in table.cells
        ]
        clean_relative_root = f"documents/{context.source_id}/assets/tables/{table.table_id}"
        clean_table_asset = registry.generated(
            key=f"{table.table_id}:clean_table",
            role="clean_table_json",
            relative_path=f"{clean_relative_root}/table.json",
            payload={
                "schema_version": "er_commons.clean_table.v1",
                "producer_table_id": table.table_id,
                "shape": list(table.shape_clean),
                "cleanup": table.cleanup.as_json(),
                "clean_csv_sha256": table.clean_csv_sha256,
            },
            media_type="application/json",
        )
        clean_cells_asset = registry.generated(
            key=f"{table.table_id}:clean_cells",
            role="clean_table_cells_json",
            relative_path=f"{clean_relative_root}/cells.json",
            payload=clean_cells_payload,
            media_type="application/json",
        )
        links_by_id[table.table_id] = (
            raw_link(parser_producer, raw_table_asset, "/"),
            raw_link(parser_producer, raw_cells_asset, "/"),
            raw_link(parser_producer, raw_csv_asset, "/"),
            raw_link("project_cleanup", clean_csv_asset, "/"),
            raw_link("project_cleanup", clean_table_asset, "/"),
            raw_link("project_cleanup", clean_cells_asset, "/"),
        )
    return links_by_id


def _register_picture_assets(
    *,
    registry: _AssetRegistry,
    inputs: CanonicalizationInputs,
) -> dict[str, str]:
    picture_ids: dict[str, str] = {}
    raw_inventory = inputs.asset_inventory.get("assets")
    if not isinstance(raw_inventory, list):
        raise ContractError("producer picture asset inventory is invalid")
    for item in raw_inventory:
        if not isinstance(item, dict):
            raise ContractError("producer picture asset record is invalid")
        pointer = item.get("raw_object_ref")
        if not isinstance(pointer, str):
            raise ContractError("producer picture asset pointer is invalid")
        if pointer in picture_ids:
            raise ContractError(f"duplicate picture asset pointer: {pointer}")
        path_value = item.get("path")
        if not isinstance(path_value, str):
            raise ContractError(f"picture asset path is invalid: {pointer}")
        path = inputs.producer_run_root / path_value
        if sha256_file(path) != item.get("sha256") or path.stat().st_size != item.get("byte_size"):
            raise ContractError(f"picture asset differs from inventory: {pointer}")
        picture_ids[pointer] = registry.external(
            key=f"picture:{pointer}",
            role="content_image",
            path=path,
            media_type="image/png",
            producer="docling",
        )
    pictures = inputs.document.get("pictures")
    if not isinstance(pictures, list):
        raise ContractError("saved Docling picture collection is invalid")
    expected = {f"#/pictures/{index}" for index in range(len(pictures))}
    if set(picture_ids) != expected:
        raise ContractError(
            "picture assets do not exactly cover Docling pictures: "
            f"expected={len(expected)} actual={len(picture_ids)}"
        )
    return picture_ids


def materialize_assets(
    *,
    data_root: Path,
    candidate_root: Path,
    context: MaterializationContext,
    inputs: CanonicalizationInputs,
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
    raw_docling_asset_id = registry.external(
        key="raw_docling",
        role="raw_docling_json",
        path=producer_root / "docling" / "document.json",
        media_type="application/json",
        producer="docling",
    )
    registry.external(
        key="conversion_pages",
        role="conversion_pages_json",
        path=producer_root / "docling" / "conversion_pages.json",
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
