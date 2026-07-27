"""Fast contract tests for source acquisition and verification glue."""

import json
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import pikepdf
import pytest
import requests
from pydantic import ValidationError

from er_commons.source_freeze import (
    DiscoveredLink,
    LandingPageSpec,
    ReleaseSpec,
    SourceManifest,
    SourceRecord,
    SourceRole,
    SourceSpecEntry,
    assert_contained,
    completion_record_payload,
    download_source,
    load_source_spec,
    publish_bytes_no_clobber,
    verify_completion_record,
    verify_source_record,
)


def source_entry(**overrides: object) -> SourceSpecEntry:
    """Return one valid tiny source entry with optional field overrides."""
    values: dict[str, object] = {
        "source_id": "deir_main",
        "document_center_id": 1,
        "landing_page_key": "draft",
        "role": SourceRole.MODEL_CORPUS,
        "expected_label": "Main",
        "local_filename": "deir_main.pdf",
        "warnings": [],
    }
    values.update(overrides)
    return SourceSpecEntry.model_validate(values)


def release_spec(sources: list[SourceSpecEntry]) -> ReleaseSpec:
    """Return a valid tiny release specification."""
    return ReleaseSpec(
        schema_version="test.source_spec.v1",
        release_id="test_release_v1",
        manifest_schema_version="test.manifest.v1",
        landing_pages=[
            LandingPageSpec(
                key="draft",
                url="https://www.brisbaneca.gov/draft",
                snapshot_filename="draft.html",
                expected_excluded_document_ids=[],
            )
        ],
        terms_note_filename="terms.md",
        sources=sources,
    )


def test_real_spec_has_stable_unique_ids_and_expected_roles() -> None:
    """The reviewed source specification freezes exact role membership."""
    spec, checksum = load_source_spec(Path("configs/brisbane_baylands_2025_deir_sources_v1.json"))

    assert len(checksum) == 64
    assert len(spec.sources) == 96
    assert len({item.source_id for item in spec.sources}) == 96
    assert sum(item.role == SourceRole.MODEL_CORPUS for item in spec.sources) == 35
    assert sum(item.role == SourceRole.CURATOR_ONLY_RESPONSE_SOURCE for item in spec.sources) == 1
    repaired = next(item for item in spec.sources if item.source_id.endswith("k2_part_2_of_5"))
    assert repaired.document_center_id == 2965
    assert repaired.warnings[0].startswith("source_edition_override:")


@pytest.mark.parametrize(
    "sources",
    [
        [
            source_entry(),
            source_entry(source_id="deir_main", document_center_id=2),
        ],
        [
            source_entry(),
            source_entry(
                source_id="deir_other",
                document_center_id=2,
                local_filename="deir_main.pdf",
            ),
        ],
        [
            source_entry(),
            source_entry(
                source_id="deir_other",
                document_center_id=1,
                local_filename="deir_other.pdf",
            ),
        ],
    ],
)
def test_spec_rejects_duplicate_ids_paths_and_urls(sources: list[SourceSpecEntry]) -> None:
    """Ambiguous source identities cannot enter a reviewed specification."""
    with pytest.raises(ValidationError):
        release_spec(sources)


def test_publish_bytes_is_idempotent_but_never_clobbers(tmp_path: Path) -> None:
    """No-clobber publication accepts identical bytes and rejects changed bytes."""
    target = tmp_path / "snapshot.html"

    publish_bytes_no_clobber(target, b"first")
    publish_bytes_no_clobber(target, b"first")

    with pytest.raises(FileExistsError):
        publish_bytes_no_clobber(target, b"changed")
    assert target.read_bytes() == b"first"


def test_containment_rejects_parent_traversal(tmp_path: Path) -> None:
    """Manifest paths cannot escape the configured artifact root."""
    with pytest.raises(ValueError, match="escapes"):
        assert_contained(tmp_path, "../outside.pdf")


def test_verify_source_detects_checksum_mismatch(tmp_path: Path) -> None:
    """Changed local bytes fail verification before PDF parsing."""
    relative = "release/source.pdf"
    path = tmp_path / relative
    path.parent.mkdir()
    path.write_bytes(b"%PDF-broken")
    record = SourceRecord(
        source_id="deir_main",
        official_title="Main",
        document_type="pdf",
        source_role=SourceRole.MODEL_CORPUS,
        landing_page_key="draft",
        landing_page_url="https://www.brisbaneca.gov/draft",
        linked_file_url="https://www.brisbaneca.gov/DocumentCenter/View/1",
        final_resolved_url="https://www.brisbaneca.gov/DocumentCenter/View/1",
        access_timestamp_utc="2026-07-24T00:00:00+00:00",
        http_status=200,
        response_headers={},
        redirect_history=[],
        local_path=relative,
        original_filename="source.pdf",
        sha256="0" * 64,
        byte_size=len(b"%PDF-broken"),
        delivered_mime_type="application/pdf",
        detected_file_type="application/pdf",
        pdf_signature_valid=True,
        pdf_page_count=1,
        retrieval_status="downloaded",
        validation_status="valid",
        warnings=[],
        visible_terms_note="release/terms.md",
    )

    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_source_record(tmp_path, record)


class InterruptedResponse(requests.Response):
    """Response fixture that fails after yielding one partial chunk."""

    def __init__(self) -> None:
        super().__init__()
        self.status_code = 200
        self.url = "https://www.brisbaneca.gov/DocumentCenter/View/1"
        self.headers["Content-Type"] = "application/pdf"

    def iter_content(
        self,
        chunk_size: int = 1,
        decode_unicode: bool = False,
    ) -> Iterator[bytes]:
        """Yield one chunk and simulate a broken network stream."""
        del chunk_size, decode_unicode
        yield b"%PDF-"
        raise requests.ConnectionError("interrupted fixture")

    def close(self) -> None:
        """Close the synthetic response without an underlying socket."""


class InterruptedSession:
    """Minimal session fixture returning the interrupted response."""

    def get(self, url: str, **kwargs: object) -> InterruptedResponse:
        """Return a context-managed response without external network access."""
        del url, kwargs
        return InterruptedResponse()


class StaticSession:
    """Minimal session fixture returning one complete in-memory PDF."""

    def __init__(self, content: bytes) -> None:
        self.content = content

    def get(self, url: str, **kwargs: object) -> requests.Response:
        """Return the same complete response without external network access."""
        del kwargs
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Length"] = str(len(self.content))
        response._content = self.content
        response._content_consumed = True
        return response


def test_partial_download_is_cleaned_up(tmp_path: Path) -> None:
    """An interrupted transfer leaves neither a final PDF nor a partial file."""
    release_root = tmp_path / "release"
    terms_path = release_root / "records" / "terms.md"
    terms_path.parent.mkdir(parents=True)
    terms_path.write_text("terms")

    with pytest.raises(requests.ConnectionError):
        download_source(
            InterruptedSession(),  # type: ignore[arg-type]
            source_entry(),
            DiscoveredLink(
                document_center_id=1,
                label="Main",
                linked_url="https://www.brisbaneca.gov/DocumentCenter/View/1",
                position=1,
            ),
            "https://www.brisbaneca.gov/draft",
            tmp_path,
            release_root,
            terms_path,
        )

    assert not list(release_root.rglob("*.part"))
    assert not list(release_root.rglob("*.pdf"))


def test_unrecorded_matching_source_is_verified_and_reused(tmp_path: Path) -> None:
    """A crash after publication can resume only when live bytes match exactly."""
    buffer = BytesIO()
    with pikepdf.new() as document:
        document.add_blank_page()
        document.save(buffer)
    content = buffer.getvalue()
    release_root = tmp_path / "release"
    destination = release_root / "sources" / "model_corpus" / "deir_main.pdf"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(content)
    terms_path = release_root / "records" / "terms.md"
    terms_path.parent.mkdir(parents=True)
    terms_path.write_text("terms")

    record = download_source(
        StaticSession(content),  # type: ignore[arg-type]
        source_entry(),
        DiscoveredLink(
            document_center_id=1,
            label="Main",
            linked_url="https://www.brisbaneca.gov/DocumentCenter/View/1",
            position=1,
        ),
        "https://www.brisbaneca.gov/draft",
        tmp_path,
        release_root,
        terms_path,
    )

    assert record.retrieval_status == "verified_existing"
    assert destination.read_bytes() == content
    assert not list(release_root.rglob("*.part"))

    destination.write_bytes(b"changed")
    with pytest.raises(FileExistsError, match="does not match"):
        download_source(
            StaticSession(content),  # type: ignore[arg-type]
            source_entry(),
            DiscoveredLink(
                document_center_id=1,
                label="Main",
                linked_url="https://www.brisbaneca.gov/DocumentCenter/View/1",
                position=1,
            ),
            "https://www.brisbaneca.gov/draft",
            tmp_path,
            release_root,
            terms_path,
        )
    assert destination.read_bytes() == b"changed"


def test_completion_record_seals_required_release_records(tmp_path: Path) -> None:
    """The final marker detects a changed terms note after completion."""
    release_root = tmp_path / "release_v1"
    records_root = release_root / "records"
    records_root.mkdir(parents=True)
    manifest_path = records_root / "source_manifest.json"
    acquisition_path = records_root / "acquisition_record.json"
    terms_path = records_root / "terms.md"
    inventory_path = records_root / "landing_page_inventory.json"
    manifest_path.write_text("{}")
    acquisition_path.write_text("{}")
    terms_path.write_text("visible terms")
    inventory_path.write_text("{}")
    spec_checksum = "a" * 64
    manifest = SourceManifest(
        manifest_schema_version="test.manifest.v1",
        source_release_version="release_v1",
        generated_at_utc="2026-07-24T00:00:00+00:00",
        source_spec_schema_version="test.spec.v1",
        source_spec_sha256=spec_checksum,
        visible_terms_note="release_v1/records/terms.md",
        landing_pages=[],
        sources=[],
        aggregates={},
        warnings=[],
    )
    completion = completion_record_payload(
        tmp_path,
        release_root,
        manifest_path,
        acquisition_path,
        terms_path,
        inventory_path,
        spec_checksum,
    )
    completion_path = records_root / "completion_record.json"
    completion_path.write_text(json.dumps(completion))

    verify_completion_record(tmp_path, completion_path, spec_checksum, manifest)
    terms_path.write_text("changed")

    with pytest.raises(ValueError, match="visible_terms_note"):
        verify_completion_record(tmp_path, completion_path, spec_checksum, manifest)
