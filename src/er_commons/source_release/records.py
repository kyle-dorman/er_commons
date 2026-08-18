"""Source manifest, inventory, completion, and local verification contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained, read_json_object, sha256_file
from er_commons.source_release.http_discovery import parse_document_links
from er_commons.source_release.integrity_validation import (
    expect_strings,
    required_integer,
    required_object,
    required_string,
    validate_inventory_shape,
)
from er_commons.source_release.models import (
    LandingPageRecord,
    ReleaseSpec,
    SourceManifest,
    SourceRecord,
    SourceRole,
    load_source_spec,
)
from er_commons.source_release.pdf_download import verify_source_record

RELEASE_PARENT = Path("datasets/ceqa/raw/brisbane_baylands")


def aggregate_sources(records: list[SourceRecord]) -> dict[str, Any]:
    """Calculate manifest counts, bytes, and pages by role and in aggregate."""
    roles: dict[str, dict[str, int]] = {}
    for role in SourceRole:
        selected = [item for item in records if item.source_role == role]
        roles[role.value] = {
            "file_count": len(selected),
            "byte_count": sum(item.byte_size for item in selected),
            "page_count": sum(item.pdf_page_count for item in selected),
        }
    return {
        "file_count": len(records),
        "byte_count": sum(item.byte_size for item in records),
        "page_count": sum(item.pdf_page_count for item in records),
        "roles": roles,
    }


def validate_role_contract(spec: ReleaseSpec, records: list[SourceRecord]) -> None:
    """Enforce exact reviewed source membership and role isolation."""
    expected = {item.source_id: item.role for item in spec.sources}
    actual = {item.source_id: item.source_role for item in records}
    if expected != actual:
        raise ValueError("completed source IDs or roles do not match the reviewed specification")
    role_counts = Counter(item.source_role for item in records)
    if role_counts != Counter(item.role for item in spec.sources):
        raise ValueError("source role counts do not match the reviewed specification")
    if role_counts[SourceRole.CURATOR_ONLY_RESPONSE_SOURCE] != 1:
        raise ValueError("exactly one curator-only response source is required")


def terms_note_content(records: list[LandingPageRecord]) -> bytes:
    """Render the release-level visible-terms and access note."""
    copyright_record = next(item for item in records if item.key == "copyright")
    content = f"""# Visible Terms and Access Note

Recorded during acquisition of `brisbane_baylands_2025_deir_sources_v1`.

The City of Brisbane landing pages linked the source files publicly at the
recorded access times. Each saved landing-page snapshot and its checksum are
listed in `source_manifest.json`.

The site's Copyright Notices page was accessed at
`{copyright_record.access_timestamp_utc}` from `{copyright_record.linked_url}`.
The visible page reserved rights in CivicPlus and City of Brisbane content and
did not display an affirmative reuse license.

This note records visible access and copyright evidence only. Public
availability does not establish a license, and this release makes no legal,
licensing, reuse, redistribution, or publication conclusion. The acquired
files are retained locally for the learning pilot.
"""
    return content.encode()


def software_versions() -> dict[str, str]:
    """Return relevant project and dependency versions for the acquisition record."""
    return {
        name: version(name)
        for name in (
            "er-commons",
            "requests",
            "urllib3",
            "beautifulsoup4",
            "pikepdf",
            "pypdf",
            "pydantic",
        )
    }


def acquisition_record_payload(
    spec_path: Path,
    spec_sha256: str,
    manifest: SourceManifest,
    *,
    clock: Callable[[], str],
) -> dict[str, Any]:
    """Build the command, software, aggregate, and warning record."""
    return {
        "schema_version": "er_commons.acquisition_record.v1",
        "source_release_version": manifest.source_release_version,
        "completed_at_utc": clock(),
        "command": "make freeze-brisbane-sources",
        "verification_command": "make verify-brisbane-sources",
        "source_spec_path": spec_path.as_posix(),
        "source_spec_sha256": spec_sha256,
        "software_versions": software_versions(),
        "aggregates": manifest.aggregates,
        "landing_page_provenance": [
            {
                "key": page.key,
                "url": page.linked_url,
                "access_timestamp_utc": page.access_timestamp_utc,
                "sha256": page.sha256,
            }
            for page in manifest.landing_pages
        ],
        "warnings": manifest.warnings,
    }


def validate_acquisition_record(
    path: Path,
    spec_sha256: str,
    manifest: SourceManifest,
) -> None:
    """Require the acquisition record to agree with the frozen release."""
    record = read_json_object(path)
    expect_strings(
        record,
        path,
        (
            ("schema_version", "er_commons.acquisition_record.v1", "acquisition-record schema"),
            ("source_release_version", manifest.source_release_version, "acquisition release ID"),
            ("source_spec_sha256", spec_sha256, "acquisition source-spec checksum"),
        ),
    )
    if required_object(record, "aggregates", path) != manifest.aggregates:
        raise ValueError(f"acquisition-record aggregates mismatch in {path}: key=aggregates")


def completion_record_payload(
    data_root: Path,
    release_root: Path,
    manifest_path: Path,
    acquisition_path: Path,
    terms_path: Path,
    inventory_path: Path,
    source_spec_sha256: str,
    *,
    clock: Callable[[], str],
) -> dict[str, Any]:
    """Build the final transactional marker over required release records."""

    def file_entry(path: Path) -> dict[str, Any]:
        return {
            "local_path": path.relative_to(data_root).as_posix(),
            "sha256": sha256_file(path),
            "byte_size": path.stat().st_size,
        }

    return {
        "schema_version": "er_commons.source_release_completion.v1",
        "source_release_version": release_root.name,
        "completed_at_utc": clock(),
        "source_spec_sha256": source_spec_sha256,
        "manifest": file_entry(manifest_path),
        "acquisition_record": file_entry(acquisition_path),
        "visible_terms_note": file_entry(terms_path),
        "landing_page_inventory": file_entry(inventory_path),
    }


def verify_completion_record(
    data_root: Path,
    path: Path,
    spec_sha256: str,
    manifest: SourceManifest,
) -> None:
    """Verify the final marker and every required record it seals."""
    record = read_json_object(path)
    expect_strings(
        record,
        path,
        (
            (
                "schema_version",
                "er_commons.source_release_completion.v1",
                "completion-record schema",
            ),
            ("source_release_version", manifest.source_release_version, "completion release ID"),
            ("source_spec_sha256", spec_sha256, "completion source-spec checksum"),
        ),
    )
    for key in ("manifest", "acquisition_record", "visible_terms_note", "landing_page_inventory"):
        item = required_object(record, key, path)
        local_path = required_string(item, "local_path", path, parent=key)
        expected_size = required_integer(item, "byte_size", path, parent=key)
        expected_sha256 = required_string(item, "sha256", path, parent=key)
        if len(expected_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in expected_sha256
        ):
            raise ValueError(
                f"invalid integrity record {path}: {key}.sha256 must be lowercase SHA-256"
            )
        try:
            sealed_path = assert_contained(data_root, local_path)
        except ValueError as error:
            raise ValueError(
                f"invalid integrity record {path}: {key}.local_path: {error}"
            ) from error
        if not sealed_path.is_file():
            raise ValueError(f"completion-record sealed file is absent: {path}: key={key}")
        if sealed_path.stat().st_size != expected_size:
            raise ValueError(f"completion-record byte-size mismatch: {key}")
        if sha256_file(sealed_path) != expected_sha256:
            raise ValueError(f"completion-record checksum mismatch: {key}")


def landing_page_inventory_payload(spec: ReleaseSpec, release_root: Path) -> dict[str, Any]:
    """Materialize ordered labels and dispositions from frozen snapshots."""
    selected = {
        (source.landing_page_key, source.document_center_id): source for source in spec.sources
    }
    pages: list[dict[str, Any]] = []
    for page in spec.landing_pages:
        links = parse_document_links(
            (release_root / "landing_pages" / page.snapshot_filename).read_bytes(),
            page.url,
        )
        expected = {
            source.document_center_id
            for source in spec.sources
            if source.landing_page_key == page.key
        } | set(page.expected_excluded_document_ids)
        if {link.document_center_id for link in links} != expected:
            raise ValueError(f"frozen landing-page inventory mismatch: {page.key}")
        rows = []
        for link in links:
            source = selected.get((page.key, link.document_center_id))
            rows.append(
                {
                    "position": link.position,
                    "document_center_id": link.document_center_id,
                    "label": link.label,
                    "linked_url": link.linked_url,
                    "disposition": "selected" if source else "excluded",
                    "source_id": source.source_id if source else None,
                    "source_role": source.role.value if source else None,
                }
            )
        pages.append({"key": page.key, "url": page.url, "links": rows})
    return {
        "schema_version": "er_commons.landing_page_inventory.v1",
        "source_release_version": spec.release_id,
        "pages": pages,
    }


def validate_landing_page_inventory(path: Path, spec: ReleaseSpec, release_root: Path) -> None:
    """Require the ordered inventory to reproduce from saved snapshots."""
    observed = read_json_object(path)
    expect_strings(
        observed,
        path,
        (
            (
                "schema_version",
                "er_commons.landing_page_inventory.v1",
                "landing-page inventory schema",
            ),
            ("source_release_version", spec.release_id, "landing-page inventory release ID"),
        ),
    )
    validate_inventory_shape(observed, path)
    if observed != landing_page_inventory_payload(spec, release_root):
        raise ValueError(f"landing-page inventory mismatch in {path}")


def verify_release_contents(data_root: Path, spec_path: Path) -> SourceManifest:
    """Verify release contents before or after the final completion marker."""
    spec, spec_sha256 = load_source_spec(spec_path)
    release_root = data_root / RELEASE_PARENT / spec.release_id
    manifest = SourceManifest.model_validate_json(
        (release_root / "records" / "source_manifest.json").read_bytes()
    )
    if manifest.source_spec_sha256 != spec_sha256:
        raise ValueError("manifest source-spec checksum mismatch")
    if manifest.source_release_version != spec.release_id:
        raise ValueError("manifest release ID mismatch")
    source_ids = [item.source_id for item in manifest.sources]
    local_paths = [item.local_path for item in manifest.sources]
    if len(source_ids) != len(set(source_ids)) or len(local_paths) != len(set(local_paths)):
        raise ValueError("manifest contains duplicate source IDs or local paths")
    validate_role_contract(spec, manifest.sources)
    for record in manifest.sources:
        verify_source_record(data_root, record)
    for page in manifest.landing_pages:
        path = assert_contained(data_root, page.local_path)
        if path.stat().st_size != page.byte_size or sha256_file(path) != page.sha256:
            raise ValueError(f"landing-page snapshot mismatch: {page.key}")
    if not assert_contained(data_root, manifest.visible_terms_note).is_file():
        raise FileNotFoundError(manifest.visible_terms_note)
    if aggregate_sources(manifest.sources) != manifest.aggregates:
        raise ValueError("manifest aggregates do not match source records")
    partials = list(release_root.rglob("*.part"))
    if partials:
        raise ValueError(f"partial files remain in completed release: {partials}")
    return manifest


__all__ = [
    "RELEASE_PARENT",
    "acquisition_record_payload",
    "aggregate_sources",
    "completion_record_payload",
    "landing_page_inventory_payload",
    "terms_note_content",
    "validate_acquisition_record",
    "validate_landing_page_inventory",
    "validate_role_contract",
    "verify_completion_record",
    "verify_release_contents",
]
