"""Resolve and validate a manifest-ordered stage-two scope."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.config import RunSpec, load_run_spec
from er_commons.corpus_extraction.identity import build_scope_id
from er_commons.corpus_resolution.config import ScopeRunSpec, load_scope_run_spec
from er_commons.document_extraction.sources import load_sealed_manifest
from er_commons.source_family_catalog import SourceFamilyCatalog
from er_commons.source_freeze import SourceRole, assert_contained


@dataclass(frozen=True)
class ScopeRun:
    """Verified stage-one and stage-two context for one declared source scope."""

    data_root: Path
    scope_spec: ScopeRunSpec
    document_spec_path: Path
    document_spec: RunSpec
    scope_id: str
    extraction_root: Path


def prepare_scope_run(data_root: Path, run_spec_path: Path) -> ScopeRun:
    """Verify scope configuration and exact manifest-subset order."""
    scope_spec, _ = load_scope_run_spec(run_spec_path)
    document_spec_path = (run_spec_path.resolve().parent / scope_spec.document_run_spec).resolve()
    if not document_spec_path.is_file():
        raise FileNotFoundError(document_spec_path)
    document_spec, document_spec_sha256 = load_run_spec(document_spec_path)
    manifest = load_sealed_manifest(data_root, document_spec)
    model_sources = [
        record.source_id
        for record in manifest.sources
        if record.source_role == SourceRole.MODEL_CORPUS
    ]
    positions = [model_sources.index(source_id) for source_id in scope_spec.source_ids]
    if positions != sorted(positions):
        raise ValueError("scope sources are not in sealed manifest order")
    owner_ids = [owner.source_id for owner in document_spec.document_owners]
    if list(scope_spec.source_ids) != owner_ids:
        raise ValueError("scope source IDs differ from the document run specification")
    catalog_path = assert_contained(data_root, scope_spec.corpus_catalog_relative_path.as_posix())
    catalog = SourceFamilyCatalog.load(catalog_path)
    manifest_by_id = {record.source_id: record for record in manifest.sources}
    for family_source in catalog.sources:
        record = manifest_by_id.get(family_source.source_id)
        if record is None:
            raise ValueError("source-family catalog names an unsealed source")
        expected = {
            "source_id": record.source_id,
            "sha256": record.sha256,
            "pdf_page_count": record.pdf_page_count,
        }
        observed = {
            key: family_source.source.get(key) for key in ("source_id", "sha256", "pdf_page_count")
        }
        if observed != expected:
            raise ValueError("source-family catalog source identity differs from manifest")
    scope_id = build_scope_id(
        run_spec_sha256=document_spec_sha256,
        production_extraction_id=document_spec.production_extraction_id,
    )
    extraction_root = assert_contained(data_root, document_spec.artifact_relative_root.as_posix())
    return ScopeRun(
        data_root=data_root.resolve(),
        scope_spec=scope_spec,
        document_spec_path=document_spec_path,
        document_spec=document_spec,
        scope_id=scope_id,
        extraction_root=extraction_root,
    )
