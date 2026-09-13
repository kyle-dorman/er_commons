"""Historical v2/v3 collection preparation kept separate from v4 recovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.collection_processing.source_membership import select_collection_sources
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest_metadata
from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec
from er_commons.document_publication.identity import build_scope_id
from er_commons.source_family_catalog import SourceFamilyCatalog
from er_commons.source_release.models import SourceRole


@dataclass(frozen=True)
class LegacyCollectionContext:
    """Verified context for the unchanged historical collection contract."""

    document_spec_path: Path
    document_spec: DocumentRunSpec
    scope_id: str
    extraction_root: Path


def prepare_legacy_collection(
    *,
    data_root: Path,
    run_spec_path: Path,
    collection_spec: CollectionRunSpec,
    budget: VerificationBudget,
) -> LegacyCollectionContext:
    """Execute the original manifest-backed v2/v3 preparation path."""
    assert collection_spec.document_run_spec is not None
    document_spec_path = (
        run_spec_path.resolve().parent / collection_spec.document_run_spec
    ).resolve()
    if not document_spec_path.is_file():
        raise FileNotFoundError(document_spec_path)
    document_spec, document_spec_sha256 = load_document_run_spec(document_spec_path)
    manifest = load_sealed_manifest_metadata(data_root, document_spec, budget)
    model_sources = [
        record.source_id
        for record in manifest.sources
        if record.source_role == SourceRole.MODEL_CORPUS
    ]
    logical_ids = (
        [item.logical_source_id for item in collection_spec.source_membership]
        if collection_spec.source_membership
        else list(collection_spec.source_ids)
    )
    _validate_scope_membership(document_spec, collection_spec, logical_ids, model_sources)
    if list(collection_spec.source_ids) != [
        process.source_id for process in document_spec.document_processes
    ]:
        raise ValueError("collection source IDs differ from the document run specification")
    catalog = SourceFamilyCatalog.load(
        assert_contained(data_root, collection_spec.source_family_catalog_relative_path.as_posix())
    )
    manifest_by_id = select_collection_sources(
        data_root, collection_spec, document_spec, manifest, budget
    )
    if [source.source_id for source in catalog.sources] != list(collection_spec.source_ids):
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
    return LegacyCollectionContext(
        document_spec_path=document_spec_path,
        document_spec=document_spec,
        scope_id=build_scope_id(
            run_spec_sha256=document_spec_sha256,
            production_extraction_id=document_spec.production_extraction_id,
        ),
        extraction_root=assert_contained(
            data_root, document_spec.artifact_relative_root.as_posix()
        ),
    )


def _validate_scope_membership(
    document_spec: DocumentRunSpec,
    collection_spec: CollectionRunSpec,
    logical_ids: list[str],
    model_sources: list[str],
) -> None:
    """Validate pilot order or exact production replacement composition."""
    if document_spec.scope_kind == "representative_pilot":
        positions = [model_sources.index(source_id) for source_id in logical_ids]
        if positions != sorted(positions):
            raise ValueError("collection sources are not in sealed manifest order")
    elif collection_spec.source_membership and (
        len(logical_ids) != len(model_sources) or set(logical_ids) != set(model_sources)
    ):
        raise ValueError(
            "production-full replacement membership must contain every model source once"
        )
    elif not collection_spec.source_membership and logical_ids != model_sources:
        raise ValueError(
            "production-full collection must contain every model source once in manifest order"
        )


__all__ = ["LegacyCollectionContext", "prepare_legacy_collection"]
