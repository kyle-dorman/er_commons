"""Resolve fixed selections against the immutable source release."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from er_commons.document_extraction.config import PageRange, SelectionSpec
from er_commons.source_freeze import (
    SourceManifest,
    SourceRole,
    assert_contained,
    sha256_file,
)


class ResolvedSource(BaseModel):
    """A selected source whose manifest identity and bytes are verified."""

    source_id: str
    source_path: Path
    source_sha256: str
    source_page_count: int
    warnings: list[str]
    page_ranges: list[PageRange]


def load_sealed_manifest(data_root: Path, selection: SelectionSpec) -> SourceManifest:
    """Verify the completion seal before reading the source manifest."""
    manifest_path = assert_contained(data_root, selection.source_manifest_path.as_posix())
    completion_path = manifest_path.parent / "completion_record.json"
    if not completion_path.is_file():
        raise FileNotFoundError("sealed source completion record is missing")
    completion = json.loads(completion_path.read_text())
    if completion.get("source_release_version") != selection.source_release_version:
        raise ValueError("completion record release differs from selection")
    sealed = completion.get("manifest", {})
    if sealed.get("local_path") != selection.source_manifest_path.as_posix():
        raise ValueError("completion record does not seal the selected manifest")
    if manifest_path.stat().st_size != sealed.get("byte_size"):
        raise ValueError("sealed source manifest byte size changed")
    if sha256_file(manifest_path) != sealed.get("sha256"):
        raise ValueError("sealed source manifest checksum changed")
    manifest = SourceManifest.model_validate_json(manifest_path.read_bytes())
    if manifest.source_release_version != selection.source_release_version:
        raise ValueError("source manifest release differs from selection")
    return manifest


def resolve_sources(
    data_root: Path,
    selection: SelectionSpec,
    manifest: SourceManifest,
) -> list[ResolvedSource]:
    """Reconcile selected model-corpus sources and verify their bytes."""
    records = {record.source_id: record for record in manifest.sources}
    resolved: list[ResolvedSource] = []
    for selected in selection.sources:
        record = records.get(selected.source_id)
        if record is None:
            raise ValueError(f"source absent from sealed manifest: {selected.source_id}")
        if record.source_role != SourceRole.MODEL_CORPUS:
            raise ValueError(f"source is not model_corpus: {selected.source_id}")
        if record.sha256 != selected.expected_sha256:
            raise ValueError(f"source checksum differs from selection: {selected.source_id}")
        if record.pdf_page_count != selected.expected_pdf_page_count:
            raise ValueError(f"source page count differs from selection: {selected.source_id}")
        if max(page.last_page for page in selected.page_ranges) > record.pdf_page_count:
            raise ValueError(f"selected page is outside source bounds: {selected.source_id}")
        source_path = assert_contained(data_root, record.local_path)
        if sha256_file(source_path) != selected.expected_sha256:
            raise ValueError(f"source bytes changed: {selected.source_id}")
        resolved.append(
            ResolvedSource(
                source_id=selected.source_id,
                source_path=source_path,
                source_sha256=record.sha256,
                source_page_count=record.pdf_page_count,
                warnings=record.warnings,
                page_ranges=selected.page_ranges,
            )
        )
    return resolved
