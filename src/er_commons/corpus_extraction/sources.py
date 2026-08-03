"""Manifest-driven complete-source selection for stage one."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction.config import RunSpec
from er_commons.corpus_extraction.records import SourceIdentity
from er_commons.document_extraction.sources import load_sealed_manifest
from er_commons.source_freeze import SourceRole, assert_contained, sha256_file


def resolve_manifest_source(data_root: Path, run_spec: RunSpec, source_id: str) -> SourceIdentity:
    """Select and byte-verify exactly one complete model-corpus source."""
    manifest = load_sealed_manifest(data_root, run_spec)
    matches = [item for item in manifest.sources if item.source_id == source_id]
    if len(matches) != 1:
        raise ValueError(f"sealed manifest must contain exactly one source: {source_id}")
    record = matches[0]
    if record.source_role != SourceRole.MODEL_CORPUS:
        raise ValueError(f"source is not model_corpus: {source_id}")
    source_path = assert_contained(data_root, record.local_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if source_path.stat().st_size != record.byte_size:
        raise ValueError(f"source byte size changed: {source_id}")
    if sha256_file(source_path) != record.sha256:
        raise ValueError(f"source checksum changed: {source_id}")
    return SourceIdentity(
        source_id=source_id,
        sha256=record.sha256,
        pdf_page_count=record.pdf_page_count,
    )
