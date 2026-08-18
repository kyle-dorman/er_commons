"""Restart-state handling and completion-last source-release publication."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from er_commons.artifact_io import publish_bytes_no_clobber, write_json_atomic
from er_commons.source_release.http_discovery import HttpSession, fetch_and_reconcile_pages
from er_commons.source_release.models import (
    AcquisitionState,
    DiscoveredLink,
    LandingPageRecord,
    ReleaseSpec,
    SourceManifest,
    SourceRecord,
    SourceSpecEntry,
    load_source_spec,
)
from er_commons.source_release.pdf_download import download_source, verify_source_record
from er_commons.source_release.records import (
    RELEASE_PARENT,
    acquisition_record_payload,
    aggregate_sources,
    completion_record_payload,
    landing_page_inventory_payload,
    terms_note_content,
    validate_acquisition_record,
    validate_landing_page_inventory,
    validate_role_contract,
    verify_completion_record,
    verify_release_contents,
)

LOGGER = logging.getLogger(__name__)


class Download(Protocol):
    """Injected single-source download boundary."""

    def __call__(
        self,
        session: HttpSession,
        source: SourceSpecEntry,
        discovered: DiscoveredLink,
        page_url: str,
        data_root: Path,
        release_root: Path,
        terms_note_path: Path,
        *,
        clock: Callable[[], str],
    ) -> SourceRecord: ...


@dataclass(frozen=True)
class ReleasePaths:
    """Named paths for one release transaction."""

    release_root: Path
    manifest: Path
    acquisition: Path
    completion: Path
    inventory: Path
    state: Path
    terms: Path

    @classmethod
    def from_spec(cls, data_root: Path, spec: ReleaseSpec) -> ReleasePaths:
        release_root = data_root / RELEASE_PARENT / spec.release_id
        records = release_root / "records"
        return cls(
            release_root=release_root,
            manifest=records / "source_manifest.json",
            acquisition=records / "acquisition_record.json",
            completion=records / "completion_record.json",
            inventory=records / "landing_page_inventory.json",
            state=records / "acquisition_state.json",
            terms=records / spec.terms_note_filename,
        )


def freeze_with_session(
    data_root: Path,
    spec_path: Path,
    *,
    session: HttpSession,
    clock: Callable[[], str],
    downloader: Download = download_source,
) -> SourceManifest:
    """Acquire or resume one release using explicit side-effect services."""
    spec, spec_sha256 = load_source_spec(spec_path)
    paths = ReleasePaths.from_spec(data_root, spec)
    if paths.manifest.exists():
        return recover_final_records(data_root, spec_path, clock=clock)
    page_records, discoveries, contents = fetch_and_reconcile_pages(
        session,
        spec,
        data_root,
        paths.release_root,
        clock=clock,
    )
    completed = _resume_state(data_root, paths, spec_sha256, page_records)
    _publish_page_evidence(spec, paths, page_records, contents)
    if not paths.state.exists():
        _write_state(paths, spec_sha256, page_records, [])
    completed_ids = {item.source_id for item in completed}
    page_urls = {page.key: page.url for page in spec.landing_pages}
    for index, source in enumerate(spec.sources, start=1):
        if source.source_id in completed_ids:
            LOGGER.info("reused verified source %s", source.source_id)
            continue
        LOGGER.info("downloading %s (%s/%s)", source.source_id, index, len(spec.sources))
        completed.append(
            downloader(
                session,
                source,
                discoveries[source.landing_page_key][source.document_center_id],
                page_urls[source.landing_page_key],
                data_root,
                paths.release_root,
                paths.terms,
                clock=clock,
            )
        )
        _write_state(paths, spec_sha256, page_records, completed)
    return _publish_final_records(
        data_root,
        spec_path,
        spec,
        spec_sha256,
        paths,
        page_records,
        completed,
        clock=clock,
    )


def recover_final_records(
    data_root: Path,
    spec_path: Path,
    *,
    clock: Callable[[], str],
) -> SourceManifest:
    """Complete missing metadata records around an existing valid manifest."""
    spec, spec_sha256 = load_source_spec(spec_path)
    paths = ReleasePaths.from_spec(data_root, spec)
    LOGGER.info("release manifest already exists; completing and verifying records")
    manifest = verify_release_contents(data_root, spec_path)
    if not paths.acquisition.exists():
        _publish_json(
            paths.acquisition,
            acquisition_record_payload(spec_path, spec_sha256, manifest, clock=clock),
        )
    validate_acquisition_record(paths.acquisition, spec_sha256, manifest)
    if not paths.inventory.exists():
        _publish_json(paths.inventory, landing_page_inventory_payload(spec, paths.release_root))
    validate_landing_page_inventory(paths.inventory, spec, paths.release_root)
    if not paths.completion.exists():
        _publish_json(
            paths.completion,
            completion_record_payload(
                data_root,
                paths.release_root,
                paths.manifest,
                paths.acquisition,
                paths.terms,
                paths.inventory,
                spec_sha256,
                clock=clock,
            ),
        )
    verify_completion_record(data_root, paths.completion, spec_sha256, manifest)
    return manifest


def verify_release(data_root: Path, spec_path: Path) -> SourceManifest:
    """Verify a completed release locally without network access."""
    spec, spec_sha256 = load_source_spec(spec_path)
    paths = ReleasePaths.from_spec(data_root, spec)
    manifest = verify_release_contents(data_root, spec_path)
    validate_acquisition_record(paths.acquisition, spec_sha256, manifest)
    validate_landing_page_inventory(paths.inventory, spec, paths.release_root)
    verify_completion_record(data_root, paths.completion, spec_sha256, manifest)
    return manifest


def _resume_state(
    data_root: Path,
    paths: ReleasePaths,
    spec_sha256: str,
    page_records: list[LandingPageRecord],
) -> list[SourceRecord]:
    if not paths.state.exists():
        return []
    state = AcquisitionState.model_validate_json(paths.state.read_bytes())
    if state.source_spec_sha256 != spec_sha256:
        raise ValueError("restart state belongs to a different source specification")
    if [item.sha256 for item in state.landing_pages] != [item.sha256 for item in page_records]:
        raise ValueError("live landing pages changed since the interrupted acquisition")
    for record in state.sources:
        verify_source_record(data_root, record)
    page_records[:] = state.landing_pages
    return list(state.sources)


def _publish_page_evidence(
    spec: ReleaseSpec,
    paths: ReleasePaths,
    page_records: list[LandingPageRecord],
    contents: dict[str, bytes],
) -> None:
    for page, content in zip(spec.landing_pages, contents.values(), strict=True):
        publish_bytes_no_clobber(
            paths.release_root / "landing_pages" / page.snapshot_filename,
            content,
        )
    publish_bytes_no_clobber(paths.terms, terms_note_content(page_records))


def _write_state(
    paths: ReleasePaths,
    spec_sha256: str,
    page_records: list[LandingPageRecord],
    completed: list[SourceRecord],
) -> None:
    write_json_atomic(
        paths.state,
        AcquisitionState(
            source_spec_sha256=spec_sha256,
            landing_pages=page_records,
            sources=completed,
        ),
    )


def _publish_final_records(
    data_root: Path,
    spec_path: Path,
    spec: ReleaseSpec,
    spec_sha256: str,
    paths: ReleasePaths,
    page_records: list[LandingPageRecord],
    completed: list[SourceRecord],
    *,
    clock: Callable[[], str],
) -> SourceManifest:
    validate_role_contract(spec, completed)
    manifest = SourceManifest(
        manifest_schema_version=spec.manifest_schema_version,
        source_release_version=spec.release_id,
        generated_at_utc=clock(),
        source_spec_schema_version=spec.schema_version,
        source_spec_sha256=spec_sha256,
        visible_terms_note=paths.terms.relative_to(data_root).as_posix(),
        landing_pages=page_records,
        sources=completed,
        aggregates=aggregate_sources(completed),
        warnings=sorted({warning for item in completed for warning in item.warnings}),
    )
    publish_bytes_no_clobber(paths.manifest, manifest.model_dump_json(indent=2).encode() + b"\n")
    _publish_json(
        paths.acquisition,
        acquisition_record_payload(spec_path, spec_sha256, manifest, clock=clock),
    )
    _publish_json(paths.inventory, landing_page_inventory_payload(spec, paths.release_root))
    _publish_json(
        paths.completion,
        completion_record_payload(
            data_root,
            paths.release_root,
            paths.manifest,
            paths.acquisition,
            paths.terms,
            paths.inventory,
            spec_sha256,
            clock=clock,
        ),
    )
    paths.state.unlink(missing_ok=True)
    return verify_release(data_root, spec_path)


def _publish_json(path: Path, payload: dict[str, Any]) -> None:
    publish_bytes_no_clobber(path, json.dumps(payload, indent=2).encode() + b"\n")


__all__ = [
    "Download",
    "ReleasePaths",
    "freeze_with_session",
    "recover_final_records",
    "verify_release",
]
