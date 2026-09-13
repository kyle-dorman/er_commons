"""Source-free preparation helpers for imported collection evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.authority_refs import CollectionArtifactResolver
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.collection_processing.imported_selection import (
    ImportedDocumentSelection,
    load_imported_document_selection,
)
from er_commons.collection_processing.production_identity import (
    validate_collection_production_identity,
)
from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec
from er_commons.document_publication.identity import build_scope_id
from er_commons.source_family_catalog import SourceFamilyCatalog


@dataclass(frozen=True)
class ImportedCollectionContext:
    """Verified values required by the shared collection pipeline."""

    data_root: Path
    document_spec_path: Path
    document_spec: DocumentRunSpec
    scope_id: str
    output_root: Path
    production_id: str
    document_root: Path
    selection: ImportedDocumentSelection
    resolver: CollectionArtifactResolver


def prepare_imported_collection(
    *,
    data_root: Path,
    collection_spec: CollectionRunSpec,
    collection_spec_sha256: str,
    budget: VerificationBudget,
) -> ImportedCollectionContext:
    """Verify v4 only from compact selected evidence and frozen controls."""
    artifact_root = data_root.resolve()
    output_relative = collection_spec.collection_output_relative_root
    imported_relative = collection_spec.imported_document_root_relative_path
    identity_ref = collection_spec.collection_production_identity_ref
    selection_ref = collection_spec.imported_selection_ref
    imported_spec_ref = collection_spec.imported_document_run_spec_ref
    imported_identity_ref = collection_spec.imported_document_production_identity_ref
    production_id = collection_spec.collection_production_id
    assert (
        output_relative is not None
        and imported_relative is not None
        and identity_ref is not None
        and selection_ref is not None
        and imported_spec_ref is not None
        and imported_identity_ref is not None
        and production_id is not None
    )
    output_root = assert_contained(artifact_root, output_relative.as_posix())
    document_root = assert_contained(artifact_root, imported_relative.as_posix())
    _validate_roots(output_root, document_root)
    resolver, selection = _validate_identity_and_selection(
        artifact_root=artifact_root,
        document_root=document_root,
        output_root=output_root,
        output_namespace=output_relative.as_posix(),
        production_id=production_id,
        identity_ref=identity_ref,
        selection_ref=selection_ref,
        source_ids=collection_spec.source_ids,
        budget=budget,
    )
    if (
        selection.document_run_spec_ref != imported_spec_ref
        or selection.document_production_identity_ref != imported_identity_ref
        or selection.document_input_root_relative_path != imported_relative.as_posix()
    ):
        raise ValueError("collection v4 imported controls differ from frozen selection")
    document_spec_path = resolver.resolve(
        imported_spec_ref, expected_authority="document_input_root"
    )
    document_spec, document_spec_sha256 = load_document_run_spec(document_spec_path)
    imported_identity = resolver.read_json(
        imported_identity_ref, expected_authority="document_input_root"
    )
    document_artifact_root = assert_contained(
        artifact_root, document_spec.artifact_relative_root.as_posix()
    )
    if (
        document_spec_sha256 != imported_spec_ref.sha256
        or imported_identity.get("extraction_id") != document_spec.production_extraction_id
        or not document_artifact_root.is_relative_to(document_root)
    ):
        raise ValueError("collection v4 imported document production differs")
    _validate_catalog(artifact_root, collection_spec, selection)
    return ImportedCollectionContext(
        data_root=artifact_root,
        document_spec_path=document_spec_path,
        document_spec=document_spec,
        scope_id=build_scope_id(
            run_spec_sha256=collection_spec_sha256,
            production_extraction_id=production_id,
        ),
        output_root=output_root,
        production_id=production_id,
        document_root=document_root,
        selection=selection,
        resolver=resolver,
    )


def _validate_identity_and_selection(
    *,
    artifact_root: Path,
    document_root: Path,
    output_root: Path,
    output_namespace: str,
    production_id: str,
    identity_ref: object,
    selection_ref: object,
    source_ids: tuple[str, ...],
    budget: VerificationBudget,
) -> tuple[CollectionArtifactResolver, ImportedDocumentSelection]:
    """Validate collection identity and load its exact imported selection."""
    from er_commons.authority_reference import AuthorityReference

    checked_identity_ref = AuthorityReference.model_validate(identity_ref)
    checked_selection_ref = AuthorityReference.model_validate(selection_ref)
    repository_root = Path(__file__).resolve().parents[3]
    identity_path = checked_identity_ref.resolve(
        repository_root=repository_root,
        artifact_root=artifact_root,
        budget=budget,
        role="identity_preimage",
        source_id="collection",
    )
    identity_record = budget.read_json(
        identity_path,
        role="identity_preimage",
        source_id="collection",
        root=artifact_root,
    )
    if not isinstance(identity_record, dict):
        raise ValueError("collection v4 production identity must be an object")
    identity = validate_collection_production_identity(
        identity_record,
        repository_root=repository_root,
        artifact_root=artifact_root,
        expected_imported_selection_ref=checked_selection_ref,
        expected_output_namespace=output_namespace,
    )
    if identity.collection_production_id != production_id:
        raise ValueError("collection v4 production identity differs")
    resolver = CollectionArtifactResolver(
        document_input_root=document_root,
        collection_output_root=output_root,
    )
    selection_path = checked_selection_ref.resolve(
        repository_root=repository_root,
        artifact_root=artifact_root,
        budget=budget,
        role="input_binding",
        source_id="collection",
    )
    return resolver, load_imported_document_selection(
        selection_path,
        expected_source_order=source_ids,
        expected_sha256=checked_selection_ref.sha256,
        expected_byte_size=checked_selection_ref.byte_size,
        resolver=resolver,
    )


def _validate_roots(output_root: Path, document_root: Path) -> None:
    if (
        output_root == document_root
        or output_root.is_relative_to(document_root)
        or document_root.is_relative_to(output_root)
    ):
        raise ValueError("collection v4 resolved roots are not distinct")
    if output_root.exists() and (not output_root.is_dir() or output_root.is_symlink()):
        raise ValueError("collection v4 output root must be absent or a real directory")
    if not document_root.is_dir() or document_root.is_symlink():
        raise ValueError("collection v4 imported root must be a real retained directory")


def _validate_catalog(
    artifact_root: Path,
    spec: CollectionRunSpec,
    selection: ImportedDocumentSelection,
) -> None:
    catalog = SourceFamilyCatalog.load(
        assert_contained(artifact_root, spec.source_family_catalog_relative_path.as_posix())
    )
    if [source.source_id for source in catalog.sources] != list(spec.source_ids):
        raise ValueError("source-family catalog differs from the exact imported collection")
    selected = {item.physical_source_id: item.source_identity for item in selection.candidates}
    for source in catalog.sources:
        observed = {
            key: source.source.get(key) for key in ("source_id", "sha256", "pdf_page_count")
        }
        if observed != selected[source.source_id].model_dump(mode="json"):
            raise ValueError("source-family catalog differs from imported candidate identity")


__all__ = ["ImportedCollectionContext", "prepare_imported_collection"]
