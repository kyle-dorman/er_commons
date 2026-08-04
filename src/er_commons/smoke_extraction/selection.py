"""Manifest reconciliation and identity for Task 03G.1."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import rfc8785

from er_commons.document_extraction.sources import CompleteResolvedSource, load_sealed_manifest
from er_commons.smoke_extraction.config import SmokeSpec, selected_pages
from er_commons.source_freeze import SourceRole, assert_contained, sha256_file


def validate_manifest_metadata(data_root: Path, spec: SmokeSpec) -> None:
    """Match the frozen selection to sealed metadata without opening source PDFs."""
    manifest = load_sealed_manifest(data_root, spec)
    records = [
        record for record in manifest.sources if record.source_role == SourceRole.MODEL_CORPUS
    ]
    if [record.source_id for record in records] != [source.source_id for source in spec.sources]:
        raise ValueError("smoke source order differs from sealed model_corpus order")
    for record, selected in zip(records, spec.sources, strict=True):
        expected = (
            (record.sha256, selected.expected_sha256, "checksum"),
            (record.byte_size, selected.expected_byte_size, "byte size"),
            (record.pdf_page_count, selected.expected_pdf_page_count, "page count"),
            (selected_pages(record.pdf_page_count), selected.selected_physical_pages, "selection"),
        )
        for observed, frozen, label in expected:
            if observed != frozen:
                raise ValueError(f"smoke source {label} differs: {selected.source_id}")


def resolve_source_bytes(
    data_root: Path,
    spec: SmokeSpec,
    source_id: str,
) -> CompleteResolvedSource:
    """Verify one selected source byte-for-byte after PDF execution is approved."""
    manifest = load_sealed_manifest(data_root, spec)
    records = {record.source_id: record for record in manifest.sources}
    selected_by_id = {source.source_id: source for source in spec.sources}
    selected = selected_by_id.get(source_id)
    if selected is None:
        raise ValueError(f"source is outside smoke selection: {source_id}")
    record = records[selected.source_id]
    source_path = assert_contained(data_root, record.local_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.stat().st_size != selected.expected_byte_size:
        raise ValueError(f"source byte size changed: {selected.source_id}")
    if sha256_file(source_path) != selected.expected_sha256:
        raise ValueError(f"source bytes changed: {selected.source_id}")
    return CompleteResolvedSource(
        source_id=selected.source_id,
        source_path=source_path,
        source_sha256=selected.expected_sha256,
        source_byte_size=selected.expected_byte_size,
        source_page_count=selected.expected_pdf_page_count,
        warnings=record.warnings,
    )


def smoke_id(repo_root: Path, spec: SmokeSpec, spec_sha256: str) -> str:
    """Bind the diagnostic identity to its spec, production recipe, and wrapper code."""
    owned_code = []
    for relative in spec.owned_code_paths:
        path = (repo_root / relative).resolve()
        if not path.is_relative_to(repo_root.resolve()) or not path.is_file():
            raise FileNotFoundError(path)
        owned_code.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    payload: Any = {
        "schema_version": "er_commons.task03g1_smoke_identity.v1",
        "spec_sha256": spec_sha256,
        "production_extraction_id": spec.production_extraction_id,
        "owned_code": owned_code,
    }
    return spec.smoke_identity_prefix + hashlib.sha256(rfc8785.dumps(payload)).hexdigest()
