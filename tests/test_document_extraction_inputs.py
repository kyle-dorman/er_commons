"""Tests for sealed-source reconciliation and runtime guardrails."""

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.document_extraction.config import SelectionSpec
from er_commons.document_extraction.runtime import assert_native_only
from er_commons.document_extraction.sources import resolve_sources
from er_commons.source_freeze import SourceManifest


def test_resolve_sources_checks_role_identity_and_bytes(tmp_path: Path) -> None:
    """A selected source must agree with both the manifest and local bytes."""
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-test")
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    selection = SelectionSpec.model_validate(
        {
            "pilot_spec_schema_version": "1",
            "pilot_id": "pilot",
            "source_release_version": "release",
            "source_manifest_path": "records/source_manifest.json",
            "page_number_basis": "one_based_physical_pdf_page",
            "expected_selected_page_count": 1,
            "sources": [
                {
                    "source_id": "document",
                    "expected_sha256": digest,
                    "expected_pdf_page_count": 1,
                    "page_ranges": [
                        {
                            "first_page": 1,
                            "last_page": 1,
                            "expected_printed_labels": [],
                            "stressors": ["control"],
                        }
                    ],
                }
            ],
        }
    )
    manifest = SourceManifest.model_validate(
        {
            "manifest_schema_version": "1",
            "source_release_version": "release",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "source_spec_schema_version": "1",
            "source_spec_sha256": "a" * 64,
            "visible_terms_note": "",
            "landing_pages": [],
            "sources": [
                {
                    "source_id": "document",
                    "official_title": "Document",
                    "document_type": "appendix",
                    "source_role": "model_corpus",
                    "landing_page_key": "page",
                    "landing_page_url": "https://example.test",
                    "linked_file_url": "https://example.test/source.pdf",
                    "final_resolved_url": "https://example.test/source.pdf",
                    "access_timestamp_utc": "2026-01-01T00:00:00Z",
                    "http_status": 200,
                    "response_headers": {},
                    "redirect_history": [],
                    "local_path": "source.pdf",
                    "original_filename": "source.pdf",
                    "sha256": digest,
                    "byte_size": source_path.stat().st_size,
                    "delivered_mime_type": "application/pdf",
                    "detected_file_type": "pdf",
                    "pdf_signature_valid": True,
                    "pdf_page_count": 1,
                    "retrieval_status": "complete",
                    "validation_status": "accepted",
                    "warnings": [],
                    "visible_terms_note": "",
                }
            ],
            "aggregates": {},
            "warnings": [],
        }
    )

    resolved = resolve_sources(tmp_path, selection, manifest)

    assert len(resolved) == 1
    assert resolved[0].source_path == source_path.resolve()
    assert resolved[0].source_sha256 == digest


def _accepted_options(models_root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        do_ocr=False,
        enable_remote_services=False,
        allow_external_plugins=False,
        do_picture_classification=False,
        do_picture_description=False,
        do_chart_extraction=False,
        do_code_enrichment=False,
        do_formula_enrichment=False,
        do_table_structure=False,
        artifacts_path=models_root,
    )


def test_native_only_guard_accepts_exact_backend_and_rejects_ocr(tmp_path: Path) -> None:
    """The runtime fails closed if a forbidden parser path becomes active."""
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    options = _accepted_options(tmp_path)
    format_option = SimpleNamespace(
        pipeline_cls=StandardPdfPipeline,
        backend=PyPdfiumDocumentBackend,
    )
    assert_native_only(options, format_option, tmp_path)

    options.do_ocr = True
    with pytest.raises(ValueError, match="forbidden"):
        assert_native_only(options, format_option, tmp_path)
