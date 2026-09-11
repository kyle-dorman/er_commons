"""Manifest-driven complete-source selection for stage one."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import assert_contained, sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing.sources import (
    SealedReleaseSelection,
    load_sealed_manifest,
    load_sealed_manifest_metadata,
)
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.records import SourceIdentity
from er_commons.source_release.models import SourceManifest
from er_commons.source_release.retained_processing import validate_processing_source


def resolve_manifest_source(
    data_root: Path, run_spec: DocumentRunSpec, source_id: str
) -> SourceIdentity:
    """Select and byte-verify exactly one complete model-corpus source."""
    manifest = load_sealed_manifest(data_root, run_spec)
    matches = [item for item in manifest.sources if item.source_id == source_id]
    if len(matches) != 1:
        raise ValueError(f"sealed manifest must contain exactly one source: {source_id}")
    record = matches[0]
    retained = validate_processing_source(data_root, manifest, record)
    source_path = assert_contained(data_root, record.local_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.stat().st_size != record.byte_size:
        raise ValueError(f"source byte size changed: {source_id}")
    if not retained and sha256_file(source_path) != record.sha256:
        raise ValueError(f"source checksum changed: {source_id}")
    return SourceIdentity(
        source_id=source_id,
        sha256=record.sha256,
        pdf_page_count=record.pdf_page_count,
    )


def resolve_manifest_source_metadata(
    data_root: Path,
    run_spec: DocumentRunSpec,
    source_id: str,
    budget: VerificationBudget,
    *,
    manifest: SourceManifest | None = None,
) -> SourceIdentity:
    """Select one original per-source release without opening its PDF."""
    if manifest is None:
        selection = manifest_selection_for(run_spec, source_id)
        manifest = load_sealed_manifest_metadata(data_root, selection, budget)
    matches = [item for item in manifest.sources if item.source_id == source_id]
    if len(matches) != 1:
        raise ValueError(f"sealed manifest must contain exactly one source: {source_id}")
    record = matches[0]
    validate_processing_source(data_root, manifest, record)
    budget.check_metadata(
        data_root / record.local_path,
        root=data_root,
        role="source_pdf",
        source_id=source_id,
        byte_size=record.byte_size,
    )
    return SourceIdentity(
        source_id=source_id, sha256=record.sha256, pdf_page_count=record.pdf_page_count
    )


def manifest_selection_for(
    run_spec: DocumentRunSpec,
    source_id: str,
) -> SealedReleaseSelection:
    """Keep each selected document bound to its declared original release."""
    matches = [item for item in run_spec.document_processes if item.source_id == source_id]
    if len(matches) != 1:
        raise ValueError(f"run spec lacks one document process: {source_id}")
    process = matches[0]
    if process.source_manifest_relative_path is None:
        return run_spec
    assert process.source_release_version is not None
    return ManifestSelection(process.source_release_version, process.source_manifest_relative_path)


@dataclass(frozen=True)
class ManifestSelection:
    """One immutable per-source release selection for shared manifest loading."""

    source_release_version: str
    source_manifest_path: Path
