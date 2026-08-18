"""Lightweight source-release specifications and persisted records."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import sha256_bytes


class SourceRole(StrEnum):
    """Mechanically isolated roles in the Brisbane source release."""

    MODEL_CORPUS = "model_corpus"
    CURATOR_ONLY_RESPONSE_SOURCE = "curator_only_response_source"
    CURATOR_QA_ORIGINAL_SUBMISSION = "curator_qa_original_submission"
    RECOVERY_QA_DUPLICATE = "recovery_qa_duplicate"


class LandingPageSpec(BaseModel):
    """Reviewed landing-page identity and accounted exclusions."""

    key: str
    url: str
    snapshot_filename: str
    expected_excluded_document_ids: list[int]


class SourceSpecEntry(BaseModel):
    """Reviewed expected source linked from an authoritative landing page."""

    source_id: str = Field(pattern=r"^[a-z0-9_]+$")
    document_center_id: int = Field(gt=0)
    landing_page_key: str
    role: SourceRole
    expected_label: str
    local_filename: str = Field(pattern=r"^[a-z0-9_]+\.pdf$")
    warnings: list[str] = Field(default_factory=list)


class ReleaseSpec(BaseModel):
    """Complete reviewed specification for one immutable release."""

    schema_version: str
    release_id: str = Field(pattern=r"^[a-z0-9_]+$")
    manifest_schema_version: str
    landing_pages: list[LandingPageSpec]
    terms_note_filename: str
    sources: list[SourceSpecEntry]

    @model_validator(mode="after")
    def validate_uniqueness_and_references(self) -> ReleaseSpec:
        """Reject ambiguous IDs, paths, references, and exclusions."""
        page_keys = [page.key for page in self.landing_pages]
        if len(page_keys) != len(set(page_keys)):
            raise ValueError("landing page keys must be unique")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source IDs must be unique")
        local_paths = [(source.role.value, source.local_filename) for source in self.sources]
        if len(local_paths) != len(set(local_paths)):
            raise ValueError("source local paths must be unique")
        page_key_set = set(page_keys)
        if any(source.landing_page_key not in page_key_set for source in self.sources):
            raise ValueError("every source must reference a configured landing page")
        selected = {(source.landing_page_key, source.document_center_id) for source in self.sources}
        if len(selected) != len(self.sources):
            raise ValueError("document IDs may appear only once per landing page")
        for page in self.landing_pages:
            if len(page.expected_excluded_document_ids) != len(
                set(page.expected_excluded_document_ids)
            ):
                raise ValueError(f"duplicate exclusions for landing page {page.key}")
            if any((page.key, item) in selected for item in page.expected_excluded_document_ids):
                raise ValueError(f"selected source also excluded on landing page {page.key}")
        return self


class RedirectRecord(BaseModel):
    """One HTTP redirect hop preserved as retrieval provenance."""

    status_code: int
    url: str
    location: str | None


class LandingPageRecord(BaseModel):
    """Frozen landing-page snapshot metadata."""

    key: str
    linked_url: str
    final_resolved_url: str
    access_timestamp_utc: str
    http_status: int
    response_headers: dict[str, str]
    redirect_history: list[RedirectRecord]
    local_path: str
    sha256: str
    byte_size: int
    discovered_document_ids: list[int]
    excluded_document_ids: list[int]


class SourceRecord(BaseModel):
    """Validated provenance and integrity record for one acquired PDF."""

    source_id: str
    official_title: str
    document_type: str
    source_role: SourceRole
    landing_page_key: str
    landing_page_url: str
    linked_file_url: str
    final_resolved_url: str
    access_timestamp_utc: str
    http_status: int
    response_headers: dict[str, str]
    redirect_history: list[RedirectRecord]
    local_path: str
    original_filename: str
    sha256: str
    byte_size: int
    delivered_mime_type: str
    detected_file_type: str
    pdf_signature_valid: bool
    pdf_page_count: int
    retrieval_status: str
    validation_status: str
    warnings: list[str]
    visible_terms_note: str


class SourceManifest(BaseModel):
    """Authoritative completed source-release manifest."""

    model_config = ConfigDict(use_enum_values=True)

    manifest_schema_version: str
    source_release_version: str
    generated_at_utc: str
    source_spec_schema_version: str
    source_spec_sha256: str
    visible_terms_note: str
    landing_pages: list[LandingPageRecord]
    sources: list[SourceRecord]
    aggregates: dict[str, Any]
    warnings: list[str]


class AcquisitionState(BaseModel):
    """Restart state written after each successfully published source."""

    source_spec_sha256: str
    landing_pages: list[LandingPageRecord]
    sources: list[SourceRecord]


class DiscoveredLink(BaseModel):
    """Document link parsed from a live authoritative landing page."""

    document_center_id: int
    label: str
    linked_url: str
    position: int


def load_source_spec(path: Path) -> tuple[ReleaseSpec, str]:
    """Load and validate the reviewed JSON source specification."""
    raw = path.read_bytes()
    return ReleaseSpec.model_validate_json(raw), sha256_bytes(raw)


__all__ = [
    "AcquisitionState",
    "DiscoveredLink",
    "LandingPageRecord",
    "LandingPageSpec",
    "RedirectRecord",
    "ReleaseSpec",
    "SourceManifest",
    "SourceRecord",
    "SourceRole",
    "SourceSpecEntry",
    "load_source_spec",
]
