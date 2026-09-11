"""Resolve fixed selections against the immutable source release."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from er_commons.artifact_io import assert_contained, sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing.config import CompleteSource
from er_commons.source_release.models import SourceManifest
from er_commons.source_release.retained_processing import validate_processing_source


class SealedReleaseSelection(Protocol):
    """Minimal release identity required to verify a sealed manifest."""

    @property
    def source_release_version(self) -> str:
        """Return the original sealed release version."""

    @property
    def source_manifest_path(self) -> Path:
        """Return the manifest path relative to the data root."""


def load_sealed_manifest(
    data_root: Path,
    selection: SealedReleaseSelection,
) -> SourceManifest:
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


def load_sealed_manifest_metadata(
    data_root: Path,
    selection: SealedReleaseSelection,
    budget: VerificationBudget,
) -> SourceManifest:
    """Consume a historical release seal without hashing or opening source PDFs."""
    path = assert_contained(data_root, selection.source_manifest_path.as_posix())
    completion_path = path.parent / "completion_record.json"
    context = selection.source_release_version
    budget.hash_file(completion_path, root=data_root, role="completion", source_id=context)
    completion = budget.read_json(
        completion_path,
        root=data_root,
        role="completion",
        source_id=context,
    )
    if not isinstance(completion, dict) or completion.get("schema_version") != (
        "er_commons.source_release_completion.v1"
    ):
        raise ValueError(f"unsupported source completion schema: {completion_path}")
    if completion.get("source_release_version") != selection.source_release_version:
        raise ValueError("completion record release differs from selection")
    sealed = completion.get("manifest")
    if not isinstance(sealed, dict) or sealed.get("local_path") != (
        selection.source_manifest_path.as_posix()
    ):
        raise ValueError("completion record does not seal the selected manifest")
    size, digest = sealed.get("byte_size"), sealed.get("sha256")
    if not isinstance(size, int) or not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"source manifest seal lacks size/digest: {path}")
    budget.check_metadata(
        path, root=data_root, role="source_manifest", source_id=context, byte_size=size
    )
    if size <= budget.hash_file_limit:
        if (
            budget.hash_file(path, root=data_root, role="source_manifest", source_id=context)
            != digest
        ):
            raise ValueError(f"sealed source manifest checksum changed: {path}")
    else:
        budget.observations.append(
            {
                "source_id": context,
                "role": "source_manifest",
                "path": str(path),
                "byte_size": size,
                "recorded_digest": digest,
                "verification_mode": "metadata_checked",
                "limitation": "oversized manifest digest retained; bytes not freshly hashed",
            }
        )
    raw = budget.read_json(path, root=data_root, role="source_manifest", source_id=context)
    manifest = SourceManifest.model_validate(raw)
    if manifest.source_release_version != selection.source_release_version:
        raise ValueError("source manifest release differs from selection")
    if manifest.source_spec_sha256 != completion.get("source_spec_sha256"):
        raise ValueError("source specification binding differs from completion")
    ids = [record.source_id for record in manifest.sources]
    if len(ids) != len(set(ids)):
        raise ValueError("sealed source manifest contains duplicate source IDs")
    return manifest


class CompleteResolvedSource(BaseModel):
    """One complete source verified against exactly one sealed manifest record."""

    source_id: str
    source_path: Path
    source_sha256: str
    source_byte_size: int
    source_page_count: int
    warnings: list[str]


def resolve_complete_source(
    data_root: Path,
    selected: CompleteSource,
    manifest: SourceManifest,
) -> CompleteResolvedSource:
    """Resolve exactly one complete model-corpus source without range selection."""
    matches = [record for record in manifest.sources if record.source_id == selected.source_id]
    if len(matches) != 1:
        raise ValueError(
            f"sealed manifest must contain exactly one source record: {selected.source_id}"
        )
    record = matches[0]
    retained = validate_processing_source(data_root, manifest, record)
    expected = (
        (record.sha256, selected.expected_sha256, "checksum"),
        (record.byte_size, selected.expected_byte_size, "byte size"),
        (record.pdf_page_count, selected.expected_pdf_page_count, "page count"),
        (record.official_title, selected.official_title, "official title"),
    )
    for actual, frozen, label in expected:
        if actual != frozen:
            raise ValueError(f"source {label} differs from producer config: {selected.source_id}")
    source_path = assert_contained(data_root, record.local_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.stat().st_size != selected.expected_byte_size:
        raise ValueError(f"source byte size changed: {selected.source_id}")
    if not retained and sha256_file(source_path) != selected.expected_sha256:
        raise ValueError(f"source bytes changed: {selected.source_id}")
    return CompleteResolvedSource(
        source_id=selected.source_id,
        source_path=source_path,
        source_sha256=record.sha256,
        source_byte_size=record.byte_size,
        source_page_count=record.pdf_page_count,
        warnings=record.warnings,
    )
