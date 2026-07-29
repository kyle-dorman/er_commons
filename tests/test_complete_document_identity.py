"""Configuration, source, status, and identity tests for the complete producer."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from er_commons.document_extraction.producer_config import (
    CompleteSource,
    ProducerConfig,
    load_producer_config,
)
from er_commons.document_extraction.producer_conversion import map_conversion_status
from er_commons.document_extraction.producer_identity import canonical_json_sha256
from er_commons.document_extraction.routing import layout_table_observations
from er_commons.document_extraction.sources import resolve_complete_source
from er_commons.source_freeze import SourceManifest


def _manifest_record(
    source_path: Path,
    *,
    source_id: str = "document",
    role: str = "model_corpus",
) -> dict[str, object]:
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    return {
        "source_id": source_id,
        "official_title": "Document",
        "document_type": "appendix",
        "source_role": role,
        "landing_page_key": "page",
        "landing_page_url": "https://example.test",
        "linked_file_url": "https://example.test/source.pdf",
        "final_resolved_url": "https://example.test/source.pdf",
        "access_timestamp_utc": "2026-01-01T00:00:00Z",
        "http_status": 200,
        "response_headers": {},
        "redirect_history": [],
        "local_path": source_path.name,
        "original_filename": source_path.name,
        "sha256": digest,
        "byte_size": source_path.stat().st_size,
        "delivered_mime_type": "application/pdf",
        "detected_file_type": "pdf",
        "pdf_signature_valid": True,
        "pdf_page_count": 2,
        "retrieval_status": "complete",
        "validation_status": "accepted",
        "warnings": [],
        "visible_terms_note": "",
    }


def _manifest(records: list[dict[str, object]]) -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "manifest_schema_version": "1",
            "source_release_version": "release",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "source_spec_schema_version": "1",
            "source_spec_sha256": "a" * 64,
            "visible_terms_note": "",
            "landing_pages": [],
            "sources": records,
            "aggregates": {},
            "warnings": [],
        }
    )


def _selected(source_path: Path) -> CompleteSource:
    return CompleteSource(
        source_id="document",
        official_title="Document",
        expected_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        expected_byte_size=source_path.stat().st_size,
        expected_pdf_page_count=2,
    )


def test_tracked_configs_preserve_v1_and_select_human_owned_v2() -> None:
    """The rewrite gets a new policy identity without mutating the v1 config."""
    v1, _ = load_producer_config(
        Path("configs/brisbane_baylands_2025_deir_task03c_appendix_p_v1.json")
    )
    v2, _ = load_producer_config(
        Path("configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json")
    )

    assert v1.producer_policy_version == "task03c-v1"
    assert v2.producer_policy_version == "task03c-v2"
    assert v1.source == v2.source
    assert v2.source.source_id == "deir_appendix_p"
    assert v2.source.expected_pdf_page_count == 222
    assert v2.document_timeout_seconds is None

    payload = v2.model_dump(mode="json")
    payload["artifact_relative_root"] = "../escape"
    with pytest.raises(ValueError, match="contained relative"):
        ProducerConfig.model_validate(payload)


def test_complete_source_rejects_ambiguous_or_wrong_role(tmp_path: Path) -> None:
    """Manifest selection never guesses between duplicates or curator-only files."""
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-test")
    selected = _selected(source_path)
    record = _manifest_record(source_path)

    with pytest.raises(ValueError, match="exactly one"):
        resolve_complete_source(tmp_path, selected, _manifest([record, record]))

    curator_record = _manifest_record(
        source_path,
        role="curator_qa_original_submission",
    )
    with pytest.raises(ValueError, match="not model_corpus"):
        resolve_complete_source(tmp_path, selected, _manifest([curator_record]))


def test_complete_source_verifies_manifest_identity_and_local_bytes(
    tmp_path: Path,
) -> None:
    """The selected manifest record and local file must both match the config."""
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-test")
    selected = _selected(source_path)
    manifest = _manifest([_manifest_record(source_path)])

    resolved = resolve_complete_source(tmp_path, selected, manifest)

    assert resolved.source_page_count == 2
    assert resolved.source_path == source_path.resolve()

    source_path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        resolve_complete_source(tmp_path, selected, manifest)


@pytest.mark.parametrize(
    ("raw", "errors", "warnings_out", "expected"),
    [
        ("success", [], [], "complete"),
        ("success", [], ["warning"], "complete_with_warnings"),
        ("success", [{"message": "bad"}], [], "failed"),
        ("partial_success", [], [], "partial"),
        ("failure", [], [], "failed"),
        ("pending", [], [], "failed"),
        ("started", [], [], "failed"),
        ("skipped", [], [], "failed"),
    ],
)
def test_conversion_status_mapping_is_total_and_fail_closed(
    raw: str,
    errors: list[dict[str, str]],
    warnings_out: list[str],
    expected: str,
) -> None:
    assert map_conversion_status(raw, errors=errors, warnings_out=warnings_out) == expected

    with pytest.raises(ValueError, match="unknown"):
        map_conversion_status("new_status", errors=[], warnings_out=[])


def test_identity_hash_is_order_independent_and_content_bound() -> None:
    """Mapping order is formatting; source content remains identity-bearing."""
    first = {"source": {"sha256": "a" * 64}, "threads": 4}
    reordered = {"threads": 4, "source": {"sha256": "a" * 64}}
    changed = {"source": {"sha256": "b" * 64}, "threads": 4}

    assert canonical_json_sha256(first) == canonical_json_sha256(reordered)
    assert canonical_json_sha256(first) != canonical_json_sha256(changed)


def test_layout_observations_retain_raw_lineage_pointers() -> None:
    """Routing retains Docling references without consuming Docling table cells."""
    payload = {
        "tables": [
            {
                "prov": [
                    {
                        "page_no": 2,
                        "bbox": {"l": 1, "b": 2, "r": 3, "t": 4},
                    }
                ]
            }
        ]
    }

    assert layout_table_observations(payload, 2) == [
        {
            "raw_object_ref": "#/tables/0",
            "provenance_index": 0,
            "bbox_pdf_points_bottom_left": [1.0, 2.0, 3.0, 4.0],
        }
    ]
