"""Resolve and validate one versioned collection scope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.authority_refs import CollectionArtifactResolver
from er_commons.collection_processing.config import CollectionRunSpec, load_collection_run_spec
from er_commons.collection_processing.imported_preflight import prepare_imported_collection
from er_commons.collection_processing.imported_selection import ImportedDocumentSelection
from er_commons.collection_processing.legacy_preflight import prepare_legacy_collection
from er_commons.document_publication.config import DocumentRunSpec


@dataclass(frozen=True)
class CollectionRun:
    """Verified document and collection context for one declared source set."""

    data_root: Path
    collection_spec: CollectionRunSpec
    document_spec_path: Path
    document_spec: DocumentRunSpec
    scope_id: str
    extraction_root: Path
    collection_spec_sha256: str | None = None
    collection_production_id: str | None = None
    imported_document_root: Path | None = None
    imported_selection: ImportedDocumentSelection | None = None
    artifact_resolver: CollectionArtifactResolver | None = None


def prepare_collection_run(
    data_root: Path,
    run_spec_path: Path,
    *,
    budget: VerificationBudget | None = None,
) -> CollectionRun:
    """Dispatch to source-free v4 or the preserved historical preparation path."""
    checked_budget = budget or VerificationBudget()
    spec, spec_sha256 = load_collection_run_spec(run_spec_path)
    if spec.schema_version.endswith(".v4"):
        imported_context = prepare_imported_collection(
            data_root=data_root,
            collection_spec=spec,
            collection_spec_sha256=spec_sha256,
            budget=checked_budget,
        )
        return CollectionRun(
            data_root=imported_context.data_root,
            collection_spec=spec,
            document_spec_path=imported_context.document_spec_path,
            document_spec=imported_context.document_spec,
            scope_id=imported_context.scope_id,
            extraction_root=imported_context.output_root,
            collection_spec_sha256=spec_sha256,
            collection_production_id=imported_context.production_id,
            imported_document_root=imported_context.document_root,
            imported_selection=imported_context.selection,
            artifact_resolver=imported_context.resolver,
        )
    legacy_context = prepare_legacy_collection(
        data_root=data_root,
        run_spec_path=run_spec_path,
        collection_spec=spec,
        budget=checked_budget,
    )
    return CollectionRun(
        data_root=data_root.resolve(),
        collection_spec=spec,
        document_spec_path=legacy_context.document_spec_path,
        document_spec=legacy_context.document_spec,
        scope_id=legacy_context.scope_id,
        extraction_root=legacy_context.extraction_root,
        collection_spec_sha256=spec_sha256,
    )


__all__ = ["CollectionRun", "prepare_collection_run"]
