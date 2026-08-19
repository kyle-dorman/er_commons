"""Resolve and validate a manifest-ordered stage-two scope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.collection_processing.config import CollectionRunSpec, load_collection_run_spec
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest
from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec
from er_commons.document_publication.identity import build_scope_id
from er_commons.source_family_catalog import SourceFamilyCatalog
from er_commons.source_release.models import SourceRole


@dataclass(frozen=True)
class CollectionRun:
    """Verified document and collection context for one declared source set."""

    data_root: Path
    collection_spec: CollectionRunSpec
    document_spec_path: Path
    document_spec: DocumentRunSpec
    scope_id: str
    extraction_root: Path


def prepare_collection_run(data_root: Path, run_spec_path: Path) -> CollectionRun:
    """Verify collection configuration and exact manifest-subset order."""
    collection_spec, _ = load_collection_run_spec(run_spec_path)
    document_spec_path = (
        run_spec_path.resolve().parent / collection_spec.document_run_spec
    ).resolve()
    if not document_spec_path.is_file():
        raise FileNotFoundError(document_spec_path)
    document_spec, document_spec_sha256 = load_document_run_spec(document_spec_path)
    manifest = load_sealed_manifest(data_root, document_spec)
    model_sources = [
        record.source_id
        for record in manifest.sources
        if record.source_role == SourceRole.MODEL_CORPUS
    ]
    positions = [model_sources.index(source_id) for source_id in collection_spec.source_ids]
    if positions != sorted(positions):
        raise ValueError("collection sources are not in sealed manifest order")
    process_ids = [process.source_id for process in document_spec.document_processes]
    if list(collection_spec.source_ids) != process_ids:
        raise ValueError("collection source IDs differ from the document run specification")
    catalog_path = assert_contained(
        data_root, collection_spec.source_family_catalog_relative_path.as_posix()
    )
    catalog = SourceFamilyCatalog.load(catalog_path)
    manifest_by_id = {record.source_id: record for record in manifest.sources}
    catalog_source_ids = [source.source_id for source in catalog.sources]
    if catalog_source_ids != list(collection_spec.source_ids):
        raise ValueError("source-family catalog differs from the exact collection scope")
    for family_source in catalog.sources:
        record = manifest_by_id.get(family_source.source_id)
        if record is None:
            raise ValueError("source-family catalog names an unsealed source")
        expected = {
            "source_id": record.source_id,
            "sha256": record.sha256,
            "byte_size": record.byte_size,
            "pdf_page_count": record.pdf_page_count,
        }
        observed = {
            key: family_source.source.get(key)
            for key in ("source_id", "sha256", "byte_size", "pdf_page_count")
        }
        if observed != expected:
            raise ValueError("source-family catalog source identity differs from manifest")
    scope_id = build_scope_id(
        run_spec_sha256=document_spec_sha256,
        production_extraction_id=document_spec.production_extraction_id,
    )
    extraction_root = assert_contained(data_root, document_spec.artifact_relative_root.as_posix())
    return CollectionRun(
        data_root=data_root.resolve(),
        collection_spec=collection_spec,
        document_spec_path=document_spec_path,
        document_spec=document_spec,
        scope_id=scope_id,
        extraction_root=extraction_root,
    )
