"""Lightweight public facade for immutable source-release workflows."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from er_commons.source_release.models import (
    AcquisitionState,
    DiscoveredLink,
    LandingPageRecord,
    LandingPageSpec,
    RedirectRecord,
    ReleaseSpec,
    SourceManifest,
    SourceRecord,
    SourceRole,
    SourceSpecEntry,
    load_source_spec,
)

if TYPE_CHECKING:
    from er_commons.source_release.application import SourceReleaseServices
    from er_commons.source_release.http_discovery import HttpSession


def freeze_release(
    data_root: Path,
    spec_path: Path,
    *,
    services: SourceReleaseServices | None = None,
) -> SourceManifest:
    """Lazily load acquisition dependencies and freeze one source release."""
    from er_commons.source_release.application import freeze_release as execute

    return execute(data_root, spec_path, services=services)


def verify_release(data_root: Path, spec_path: Path) -> SourceManifest:
    """Lazily load PDF verification dependencies and verify one release."""
    from er_commons.source_release.publication import verify_release as execute

    return execute(data_root, spec_path)


def verify_release_contents(data_root: Path, spec_path: Path) -> SourceManifest:
    """Lazily verify release contents without requiring a completion marker."""
    from er_commons.source_release.records import verify_release_contents as execute

    return execute(data_root, spec_path)


def download_source(
    session: HttpSession,
    source: SourceSpecEntry,
    discovered: DiscoveredLink,
    page_url: str,
    data_root: Path,
    release_root: Path,
    terms_note_path: Path,
) -> SourceRecord:
    """Lazily stream one source using the default clock unless one is supplied."""
    from er_commons.source_release.application import utc_now
    from er_commons.source_release.pdf_download import download_source as execute

    return execute(
        session,
        source,
        discovered,
        page_url,
        data_root,
        release_root,
        terms_note_path,
        clock=utc_now,
    )


def verify_source_record(data_root: Path, record: SourceRecord) -> None:
    """Lazily verify one source record and its local PDF."""
    from er_commons.source_release.pdf_download import verify_source_record as execute

    execute(data_root, record)


def aggregate_sources(records: list[SourceRecord]) -> dict[str, Any]:
    """Lazily aggregate source counts, bytes, and pages."""
    from er_commons.source_release.records import aggregate_sources as execute

    return execute(records)


def validate_role_contract(spec: ReleaseSpec, records: list[SourceRecord]) -> None:
    """Lazily enforce exact source membership and role isolation."""
    from er_commons.source_release.records import validate_role_contract as execute

    execute(spec, records)


def completion_record_payload(
    data_root: Path,
    release_root: Path,
    manifest_path: Path,
    acquisition_path: Path,
    terms_path: Path,
    inventory_path: Path,
    source_spec_sha256: str,
) -> dict[str, Any]:
    """Build a completion marker using the default clock unless supplied."""
    from er_commons.source_release.application import utc_now
    from er_commons.source_release.records import completion_record_payload as execute

    return execute(
        data_root,
        release_root,
        manifest_path,
        acquisition_path,
        terms_path,
        inventory_path,
        source_spec_sha256,
        clock=utc_now,
    )


def verify_completion_record(
    data_root: Path,
    path: Path,
    spec_sha256: str,
    manifest: SourceManifest,
) -> None:
    """Lazily verify a completion marker and its sealed records."""
    from er_commons.source_release.records import verify_completion_record as execute

    execute(data_root, path, spec_sha256, manifest)


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
    "aggregate_sources",
    "completion_record_payload",
    "download_source",
    "freeze_release",
    "load_source_spec",
    "validate_role_contract",
    "verify_completion_record",
    "verify_release",
    "verify_release_contents",
    "verify_source_record",
]
