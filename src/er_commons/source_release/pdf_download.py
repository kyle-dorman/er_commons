"""Streaming PDF acquisition, structural validation, and source verification."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import warnings as warnings_module
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote

import pikepdf
import requests
from pypdf import PdfReader

from er_commons.artifact_io import assert_contained, sha256_file
from er_commons.source_release.http_discovery import (
    HttpSession,
    ensure_allowed_url,
    redirect_history,
    selected_headers,
)
from er_commons.source_release.models import DiscoveredLink, SourceRecord, SourceSpecEntry


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
    session: HttpSession,
    source: SourceSpecEntry,
    discovered: DiscoveredLink,
    page_url: str,
    data_root: Path,
    release_root: Path,
    terms_note_path: Path,
    *,
    clock: Callable[[], str],
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
        with session.get(discovered.linked_url, stream=True, timeout=(10, 120)) as response:
            response.raise_for_status()
            ensure_allowed_url(response.url)
            with temporary_path.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        stream.write(chunk)
                        digest.update(chunk)
                        byte_size += len(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            _validate_content_length(response, source.source_id, byte_size)
            page_count, pdf_warnings = inspect_pdf(temporary_path)
            retrieval_status = _publish_or_verify_existing(
                destination,
                temporary_path,
                destination_existed=destination_existed,
                byte_size=byte_size,
                digest=digest.hexdigest(),
                page_count=page_count,
            )
            return SourceRecord(
                source_id=source.source_id,
                official_title=discovered.label,
                document_type="pdf",
                source_role=source.role,
                landing_page_key=source.landing_page_key,
                landing_page_url=page_url,
                linked_file_url=discovered.linked_url,
                final_resolved_url=response.url,
                access_timestamp_utc=clock(),
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


def _validate_content_length(
    response: requests.Response,
    source_id: str,
    byte_size: int,
) -> None:
    delivered = response.headers.get("Content-Length")
    if (
        delivered is not None
        and response.headers.get("Content-Encoding") is None
        and int(delivered) != byte_size
    ):
        raise ValueError(
            f"incomplete response for {source_id}: expected {delivered}, received {byte_size}"
        )


def _publish_or_verify_existing(
    destination: Path,
    temporary_path: Path,
    *,
    destination_existed: bool,
    byte_size: int,
    digest: str,
    page_count: int,
) -> str:
    if destination_existed:
        if destination.stat().st_size != byte_size or sha256_file(destination) != digest:
            raise FileExistsError(
                f"unrecorded existing source does not match live bytes: {destination}"
            )
        existing_page_count, _ = inspect_pdf(destination)
        if existing_page_count != page_count:
            raise ValueError(f"unrecorded existing page-count mismatch: {destination}")
        return "verified_existing"
    try:
        os.link(temporary_path, destination)
    except FileExistsError as error:
        raise FileExistsError(f"refusing to overwrite {destination}") from error
    return "downloaded"


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


__all__ = ["download_source", "inspect_pdf", "original_filename", "verify_source_record"]
