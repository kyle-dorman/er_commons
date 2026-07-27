"""Restartable acquisition and verification for frozen public source releases."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import warnings as warnings_module
from collections import Counter
from datetime import UTC, datetime
from enum import StrEnum
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import pikepdf
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pypdf import PdfReader
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

LOGGER = logging.getLogger(__name__)
ALLOWED_SOURCE_HOSTS = {"brisbaneca.gov", "www.brisbaneca.gov"}
RELEASE_PARENT = Path("datasets/ceqa/raw/brisbane_baylands")
HEADER_NAMES = (
    "Content-Type",
    "Content-Length",
    "Content-Encoding",
    "Content-Disposition",
    "ETag",
    "Last-Modified",
    "Date",
)


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
        """Reject ambiguous IDs, paths, landing-page references, and exclusions."""
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


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).isoformat()


def sha256_bytes(content: bytes) -> str:
    """Calculate SHA-256 for bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 for an existing file without loading it into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_source_spec(path: Path) -> tuple[ReleaseSpec, str]:
    """Load and validate the reviewed JSON source specification."""
    raw = path.read_bytes()
    return ReleaseSpec.model_validate_json(raw), sha256_bytes(raw)


def build_http_session() -> requests.Session:
    """Create the bounded, GET-only retrying HTTP session."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=(429, 500, 502, 503, 504),
        backoff_factor=1.0,
        backoff_jitter=0.25,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers["User-Agent"] = "er-commons-source-freeze/0.1"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def selected_headers(response: requests.Response) -> dict[str, str]:
    """Preserve useful delivered HTTP response metadata."""
    return {name: response.headers[name] for name in HEADER_NAMES if name in response.headers}


def redirect_history(response: requests.Response) -> list[RedirectRecord]:
    """Preserve ordered HTTP redirect provenance."""
    return [
        RedirectRecord(
            status_code=item.status_code,
            url=item.url,
            location=item.headers.get("Location"),
        )
        for item in response.history
    ]


def ensure_allowed_url(url: str) -> None:
    """Reject unexpected schemes or redirect hosts."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
        raise ValueError(f"unexpected source URL: {url}")


def parse_document_links(content: bytes, page_url: str) -> list[DiscoveredLink]:
    """Parse ordered City Document Center links with Beautiful Soup."""
    links: list[DiscoveredLink] = []
    seen_ids: set[int] = set()
    soup = BeautifulSoup(content, "html.parser")
    for position, anchor in enumerate(
        soup.select('a[href*="/DocumentCenter/View/"]'),
        start=1,
    ):
        href = str(anchor.get("href", ""))
        match = re.search(r"/DocumentCenter/View/(\d+)", href)
        if not match:
            continue
        document_id = int(match.group(1))
        if document_id in seen_ids:
            raise ValueError(f"duplicate Document Center ID {document_id} on {page_url}")
        seen_ids.add(document_id)
        links.append(
            DiscoveredLink(
                document_center_id=document_id,
                label=" ".join(anchor.get_text(" ", strip=True).split()),
                linked_url=urljoin(page_url, href),
                position=position,
            )
        )
    return links


def publish_bytes_no_clobber(path: Path, content: bytes) -> None:
    """Publish bytes atomically without overwriting a conflicting final file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == content:
            return
        raise FileExistsError(f"refusing to overwrite changed file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_json_atomic(path: Path, payload: BaseModel | dict[str, Any]) -> None:
    """Write a small generated JSON record through an atomic rename."""
    if isinstance(payload, BaseModel):
        content = payload.model_dump_json(indent=2).encode() + b"\n"
    else:
        content = json.dumps(payload, indent=2).encode() + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def fetch_and_reconcile_pages(
    session: requests.Session,
    spec: ReleaseSpec,
    data_root: Path,
    release_root: Path,
) -> tuple[list[LandingPageRecord], dict[str, dict[int, DiscoveredLink]], dict[str, bytes]]:
    """Fetch landing pages and stop unless every live document link is accounted for."""
    records: list[LandingPageRecord] = []
    discoveries: dict[str, dict[int, DiscoveredLink]] = {}
    contents: dict[str, bytes] = {}
    selected_by_page: dict[str, set[int]] = {
        page.key: {
            source.document_center_id
            for source in spec.sources
            if source.landing_page_key == page.key
        }
        for page in spec.landing_pages
    }
    for page in spec.landing_pages:
        ensure_allowed_url(page.url)
        response = session.get(page.url, timeout=(10, 60))
        response.raise_for_status()
        ensure_allowed_url(response.url)
        content = response.content
        links = parse_document_links(content, page.url)
        discovered_ids = {link.document_center_id for link in links}
        expected_ids = selected_by_page[page.key] | set(page.expected_excluded_document_ids)
        if discovered_ids != expected_ids:
            missing = sorted(expected_ids - discovered_ids)
            unexpected = sorted(discovered_ids - expected_ids)
            raise ValueError(
                f"landing-page inventory changed for {page.key}: "
                f"missing={missing}, unexpected={unexpected}"
            )
        local_path = release_root / "landing_pages" / page.snapshot_filename
        records.append(
            LandingPageRecord(
                key=page.key,
                linked_url=page.url,
                final_resolved_url=response.url,
                access_timestamp_utc=utc_now(),
                http_status=response.status_code,
                response_headers=selected_headers(response),
                redirect_history=redirect_history(response),
                local_path=local_path.relative_to(data_root).as_posix(),
                sha256=sha256_bytes(content),
                byte_size=len(content),
                discovered_document_ids=sorted(discovered_ids),
                excluded_document_ids=page.expected_excluded_document_ids,
            )
        )
        discoveries[page.key] = {link.document_center_id: link for link in links}
        contents[page.key] = content
    for source in spec.sources:
        discovered = discoveries[source.landing_page_key][source.document_center_id]
        if discovered.label != source.expected_label:
            raise ValueError(
                f"link label changed for {source.source_id}: "
                f"expected={source.expected_label!r}, found={discovered.label!r}"
            )
    return records, discoveries, contents


def original_filename(response: requests.Response, fallback: str) -> str:
    """Extract the delivered filename without trusting it as a local path."""
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"filename=(?:\"([^\"]+)\"|([^;]+))", disposition, flags=re.IGNORECASE)
    if not match:
        return fallback
    return Path(unquote((match.group(1) or match.group(2)).strip())).name


def inspect_pdf(path: Path) -> tuple[int, list[str]]:
    """Validate a PDF with pikepdf and a recorded strict pypdf fallback."""
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError(f"missing PDF signature: {path}")
    validation_warnings: list[str] = []
    try:
        with pikepdf.open(path) as document:
            page_count = len(document.pages)
            with warnings_module.catch_warnings(record=True) as caught:
                warnings_module.simplefilter("always")
                validation_warnings.extend(str(item) for item in document.check_pdf_syntax())
            validation_warnings.extend(str(item.message) for item in caught)
    except pikepdf.PdfError as error:
        reader = PdfReader(path, strict=True)
        page_count = len(reader.pages)
        validation_warnings.append(
            f"pikepdf structural validation failed; strict pypdf fallback opened the file: {error}"
        )
    if page_count <= 0:
        raise ValueError(f"PDF has no pages: {path}")
    return page_count, validation_warnings


def download_source(
    session: requests.Session,
    source: SourceSpecEntry,
    discovered: DiscoveredLink,
    page_url: str,
    data_root: Path,
    release_root: Path,
    terms_note_path: Path,
) -> SourceRecord:
    """Stream, validate, and atomically publish one source PDF."""
    ensure_allowed_url(discovered.linked_url)
    destination = release_root / "sources" / source.role.value / source.local_filename
    destination_existed = destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=destination.parent, suffix=".part")
    temporary_path = Path(temporary_name)
    os.close(descriptor)
    digest = hashlib.sha256()
    byte_size = 0
    try:
        with session.get(
            discovered.linked_url,
            stream=True,
            timeout=(10, 120),
        ) as response:
            response.raise_for_status()
            ensure_allowed_url(response.url)
            with temporary_path.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    stream.write(chunk)
                    digest.update(chunk)
                    byte_size += len(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            delivered_length = response.headers.get("Content-Length")
            if (
                delivered_length is not None
                and response.headers.get("Content-Encoding") is None
                and int(delivered_length) != byte_size
            ):
                raise ValueError(
                    f"incomplete response for {source.source_id}: "
                    f"expected {delivered_length}, received {byte_size}"
                )
            page_count, pdf_warnings = inspect_pdf(temporary_path)
            retrieval_status = "downloaded"
            if destination_existed:
                if (
                    destination.stat().st_size != byte_size
                    or sha256_file(destination) != digest.hexdigest()
                ):
                    raise FileExistsError(
                        f"unrecorded existing source does not match live bytes: {destination}"
                    )
                existing_page_count, _ = inspect_pdf(destination)
                if existing_page_count != page_count:
                    raise ValueError(f"unrecorded existing page-count mismatch: {destination}")
                retrieval_status = "verified_existing"
            else:
                try:
                    os.link(temporary_path, destination)
                except FileExistsError as error:
                    raise FileExistsError(f"refusing to overwrite {destination}") from error
            return SourceRecord(
                source_id=source.source_id,
                official_title=discovered.label,
                document_type="pdf",
                source_role=source.role,
                landing_page_key=source.landing_page_key,
                landing_page_url=page_url,
                linked_file_url=discovered.linked_url,
                final_resolved_url=response.url,
                access_timestamp_utc=utc_now(),
                http_status=response.status_code,
                response_headers=selected_headers(response),
                redirect_history=redirect_history(response),
                local_path=destination.relative_to(data_root).as_posix(),
                original_filename=original_filename(response, source.local_filename),
                sha256=digest.hexdigest(),
                byte_size=byte_size,
                delivered_mime_type=response.headers.get("Content-Type", "").split(";")[0],
                detected_file_type="application/pdf",
                pdf_signature_valid=True,
                pdf_page_count=page_count,
                retrieval_status=retrieval_status,
                validation_status="valid_with_warnings" if pdf_warnings else "valid",
                warnings=[*source.warnings, *pdf_warnings],
                visible_terms_note=terms_note_path.relative_to(data_root).as_posix(),
            )
    finally:
        temporary_path.unlink(missing_ok=True)


def assert_contained(data_root: Path, relative_path: str) -> Path:
    """Resolve a manifest path and reject traversal outside the configured root."""
    candidate = (data_root / relative_path).resolve()
    root = data_root.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f"manifest path escapes ER_COMMONS_DATA_ROOT: {relative_path}")
    return candidate


def verify_source_record(data_root: Path, record: SourceRecord) -> None:
    """Verify one manifest source against immutable bytes on disk."""
    path = assert_contained(data_root, record.local_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size != record.byte_size:
        raise ValueError(f"byte-size mismatch: {record.source_id}")
    if sha256_file(path) != record.sha256:
        raise ValueError(f"checksum mismatch: {record.source_id}")
    page_count, _ = inspect_pdf(path)
    if page_count != record.pdf_page_count:
        raise ValueError(f"page-count mismatch: {record.source_id}")


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
    expected_counts = Counter(item.role for item in spec.sources)
    if role_counts != expected_counts:
        raise ValueError("source role counts do not match the reviewed specification")
    if role_counts[SourceRole.CURATOR_ONLY_RESPONSE_SOURCE] != 1:
        raise ValueError("exactly one curator-only response source is required")


def terms_note_content(records: list[LandingPageRecord]) -> bytes:
    """Render the corpus-level visible-terms and access note."""
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
) -> dict[str, Any]:
    """Build the corpus-level command, software, aggregate, and warning record."""
    return {
        "schema_version": "er_commons.acquisition_record.v1",
        "source_release_version": manifest.source_release_version,
        "completed_at_utc": utc_now(),
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
    record = json.loads(path.read_text())
    if record.get("schema_version") != "er_commons.acquisition_record.v1":
        raise ValueError("unexpected acquisition-record schema")
    if record.get("source_release_version") != manifest.source_release_version:
        raise ValueError("acquisition-record release ID mismatch")
    if record.get("source_spec_sha256") != spec_sha256:
        raise ValueError("acquisition-record source-spec checksum mismatch")
    if record.get("aggregates") != manifest.aggregates:
        raise ValueError("acquisition-record aggregates mismatch")


def completion_record_payload(
    data_root: Path,
    release_root: Path,
    manifest_path: Path,
    acquisition_path: Path,
    terms_path: Path,
    inventory_path: Path,
    source_spec_sha256: str,
) -> dict[str, Any]:
    """Build the final transactional marker over all required release records."""

    def file_entry(path: Path) -> dict[str, Any]:
        return {
            "local_path": path.relative_to(data_root).as_posix(),
            "sha256": sha256_file(path),
            "byte_size": path.stat().st_size,
        }

    return {
        "schema_version": "er_commons.source_release_completion.v1",
        "source_release_version": release_root.name,
        "completed_at_utc": utc_now(),
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
    record = json.loads(path.read_text())
    if record.get("schema_version") != "er_commons.source_release_completion.v1":
        raise ValueError("unexpected completion-record schema")
    if record.get("source_release_version") != manifest.source_release_version:
        raise ValueError("completion-record release ID mismatch")
    if record.get("source_spec_sha256") != spec_sha256:
        raise ValueError("completion-record source-spec checksum mismatch")
    for key in (
        "manifest",
        "acquisition_record",
        "visible_terms_note",
        "landing_page_inventory",
    ):
        item = record[key]
        sealed_path = assert_contained(data_root, item["local_path"])
        if sealed_path.stat().st_size != item["byte_size"]:
            raise ValueError(f"completion-record byte-size mismatch: {key}")
        if sha256_file(sealed_path) != item["sha256"]:
            raise ValueError(f"completion-record checksum mismatch: {key}")


def landing_page_inventory_payload(
    spec: ReleaseSpec,
    release_root: Path,
) -> dict[str, Any]:
    """Materialize ordered labels and dispositions from frozen page snapshots."""
    selected = {
        (source.landing_page_key, source.document_center_id): source for source in spec.sources
    }
    pages: list[dict[str, Any]] = []
    for page in spec.landing_pages:
        snapshot = release_root / "landing_pages" / page.snapshot_filename
        links = parse_document_links(snapshot.read_bytes(), page.url)
        expected = {
            source.document_center_id
            for source in spec.sources
            if source.landing_page_key == page.key
        } | set(page.expected_excluded_document_ids)
        if {link.document_center_id for link in links} != expected:
            raise ValueError(f"frozen landing-page inventory mismatch: {page.key}")
        rows: list[dict[str, Any]] = []
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


def validate_landing_page_inventory(
    path: Path,
    spec: ReleaseSpec,
    release_root: Path,
) -> None:
    """Require the ordered inventory to reproduce from saved page snapshots."""
    actual = json.loads(path.read_text())
    expected = landing_page_inventory_payload(spec, release_root)
    if actual != expected:
        raise ValueError("landing-page inventory does not match frozen snapshots and spec")


def freeze_release(data_root: Path, spec_path: Path) -> SourceManifest:
    """Acquire a complete source release or safely resume an interrupted run."""
    spec, spec_sha256 = load_source_spec(spec_path)
    release_root = data_root / RELEASE_PARENT / spec.release_id
    records_root = release_root / "records"
    manifest_path = records_root / "source_manifest.json"
    acquisition_path = records_root / "acquisition_record.json"
    completion_path = records_root / "completion_record.json"
    inventory_path = records_root / "landing_page_inventory.json"
    state_path = records_root / "acquisition_state.json"
    terms_path = records_root / spec.terms_note_filename
    if manifest_path.exists():
        LOGGER.info("release manifest already exists; completing and verifying records")
        manifest = verify_release_contents(data_root, spec_path)
        if not acquisition_path.exists():
            publish_bytes_no_clobber(
                acquisition_path,
                json.dumps(
                    acquisition_record_payload(spec_path, spec_sha256, manifest),
                    indent=2,
                ).encode()
                + b"\n",
            )
        validate_acquisition_record(acquisition_path, spec_sha256, manifest)
        if not inventory_path.exists():
            publish_bytes_no_clobber(
                inventory_path,
                json.dumps(
                    landing_page_inventory_payload(spec, release_root),
                    indent=2,
                ).encode()
                + b"\n",
            )
        validate_landing_page_inventory(inventory_path, spec, release_root)
        if not completion_path.exists():
            publish_bytes_no_clobber(
                completion_path,
                json.dumps(
                    completion_record_payload(
                        data_root,
                        release_root,
                        manifest_path,
                        acquisition_path,
                        terms_path,
                        inventory_path,
                        spec_sha256,
                    ),
                    indent=2,
                ).encode()
                + b"\n",
            )
        verify_completion_record(
            data_root,
            completion_path,
            spec_sha256,
            manifest,
        )
        return manifest

    session = build_http_session()
    try:
        page_records, discoveries, contents = fetch_and_reconcile_pages(
            session,
            spec,
            data_root,
            release_root,
        )
        completed: list[SourceRecord] = []
        if state_path.exists():
            state = AcquisitionState.model_validate_json(state_path.read_bytes())
            if state.source_spec_sha256 != spec_sha256:
                raise ValueError("restart state belongs to a different source specification")
            if [item.sha256 for item in state.landing_pages] != [
                item.sha256 for item in page_records
            ]:
                raise ValueError("live landing pages changed since the interrupted acquisition")
            page_records = state.landing_pages
            for record in state.sources:
                verify_source_record(data_root, record)
            completed = state.sources

        for page, content in zip(spec.landing_pages, contents.values(), strict=True):
            publish_bytes_no_clobber(
                release_root / "landing_pages" / page.snapshot_filename,
                content,
            )
        publish_bytes_no_clobber(terms_path, terms_note_content(page_records))
        if not state_path.exists():
            write_json_atomic(
                state_path,
                AcquisitionState(
                    source_spec_sha256=spec_sha256,
                    landing_pages=page_records,
                    sources=[],
                ),
            )

        completed_ids = {item.source_id for item in completed}
        page_urls = {page.key: page.url for page in spec.landing_pages}
        for index, source in enumerate(spec.sources, start=1):
            if source.source_id in completed_ids:
                LOGGER.info("reused verified source %s", source.source_id)
                continue
            LOGGER.info("downloading %s (%s/%s)", source.source_id, index, len(spec.sources))
            record = download_source(
                session,
                source,
                discoveries[source.landing_page_key][source.document_center_id],
                page_urls[source.landing_page_key],
                data_root,
                release_root,
                terms_path,
            )
            completed.append(record)
            write_json_atomic(
                state_path,
                AcquisitionState(
                    source_spec_sha256=spec_sha256,
                    landing_pages=page_records,
                    sources=completed,
                ),
            )

        validate_role_contract(spec, completed)
        warnings = sorted({warning for item in completed for warning in item.warnings})
        manifest = SourceManifest(
            manifest_schema_version=spec.manifest_schema_version,
            source_release_version=spec.release_id,
            generated_at_utc=utc_now(),
            source_spec_schema_version=spec.schema_version,
            source_spec_sha256=spec_sha256,
            visible_terms_note=terms_path.relative_to(data_root).as_posix(),
            landing_pages=page_records,
            sources=completed,
            aggregates=aggregate_sources(completed),
            warnings=warnings,
        )
        publish_bytes_no_clobber(
            manifest_path,
            manifest.model_dump_json(indent=2).encode() + b"\n",
        )
        publish_bytes_no_clobber(
            acquisition_path,
            json.dumps(
                acquisition_record_payload(spec_path, spec_sha256, manifest),
                indent=2,
            ).encode()
            + b"\n",
        )
        publish_bytes_no_clobber(
            inventory_path,
            json.dumps(
                landing_page_inventory_payload(spec, release_root),
                indent=2,
            ).encode()
            + b"\n",
        )
        publish_bytes_no_clobber(
            completion_path,
            json.dumps(
                completion_record_payload(
                    data_root,
                    release_root,
                    manifest_path,
                    acquisition_path,
                    terms_path,
                    inventory_path,
                    spec_sha256,
                ),
                indent=2,
            ).encode()
            + b"\n",
        )
        state_path.unlink(missing_ok=True)
        return verify_release(data_root, spec_path)
    finally:
        session.close()


def verify_release(data_root: Path, spec_path: Path) -> SourceManifest:
    """Verify a completed release locally without network access."""
    spec, spec_sha256 = load_source_spec(spec_path)
    release_root = data_root / RELEASE_PARENT / spec.release_id
    records_root = release_root / "records"
    manifest = verify_release_contents(data_root, spec_path)
    acquisition_path = records_root / "acquisition_record.json"
    completion_path = records_root / "completion_record.json"
    inventory_path = records_root / "landing_page_inventory.json"
    validate_acquisition_record(acquisition_path, spec_sha256, manifest)
    validate_landing_page_inventory(inventory_path, spec, release_root)
    verify_completion_record(
        data_root,
        completion_path,
        spec_sha256,
        manifest,
    )
    return manifest


def verify_release_contents(data_root: Path, spec_path: Path) -> SourceManifest:
    """Verify release contents before or after the final completion marker."""
    spec, spec_sha256 = load_source_spec(spec_path)
    release_root = data_root / RELEASE_PARENT / spec.release_id
    manifest_path = release_root / "records" / "source_manifest.json"
    manifest = SourceManifest.model_validate_json(manifest_path.read_bytes())
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
    terms_path = assert_contained(data_root, manifest.visible_terms_note)
    if not terms_path.is_file():
        raise FileNotFoundError(terms_path)
    if aggregate_sources(manifest.sources) != manifest.aggregates:
        raise ValueError("manifest aggregates do not match source records")
    partials = list(release_root.rglob("*.part"))
    if partials:
        raise ValueError(f"partial files remain in completed release: {partials}")
    return manifest
