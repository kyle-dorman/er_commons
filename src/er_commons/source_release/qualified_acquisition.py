"""Bounded, no-clobber acquisition and compact reuse of qualified sources.

The caller separately authorizes network access. Completed directories are immutable;
failed attempts remain evidence and retries require a fresh directory.
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import resource
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import psutil  # type: ignore[import-untyped]

from er_commons.source_release.acquisition_limits import AcquisitionLimits
from er_commons.source_release.pdf_download import original_filename
from er_commons.source_release.qualification import (
    PageText,
    QualificationPolicy,
    qualify_pages,
    validate_document_url,
)
from er_commons.source_release.qualification_receipts import (
    _binding,
    _canonical,
    _destination,
    _publish_qualified,
    _retain_failure,
)
from er_commons.source_release.qualification_receipts import (
    reuse_qualified_source as reuse_qualified_source,
)


def _inspect_pdf(
    path: Path, policy: QualificationPolicy, limits: AcquisitionLimits
) -> dict[str, Any]:
    """Require strict structure and inspect only the frozen physical page window."""
    import pikepdf
    from pypdf import PdfReader

    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError("missing PDF signature")
    with pikepdf.open(path, attempt_recovery=False) as pdf:
        problems = pdf.check_pdf_syntax()
        if problems:
            raise ValueError(f"PDF structural warnings: {str(problems)[:1000]}")
        count = len(pdf.pages)
        if not 0 < count <= limits.max_pdf_pages:
            raise ValueError("PDF page count outside reviewed ceiling")
    reader = PdfReader(path, strict=True)
    pages = []
    for index in range(min(count, policy.max_pages)):
        content = reader.pages[index].extract_text() or ""
        if len(content) > 200_000:
            raise ValueError(f"qualification text ceiling exceeded on physical page {index + 1}")
        pages.append(PageText(physical_page=index + 1, text=content))
    evidence = qualify_pages(policy, pages)
    return {
        "pdf_signature_valid": True,
        "pdf_page_count": count,
        "qualification": evidence.model_dump(mode="json"),
    }


def _worker(
    connection: Any,
    session: Any,
    directory: Path,
    source_url: str,
    policy: QualificationPolicy,
    limits: AcquisitionLimits,
    access_timestamp: str,
    inspect: Callable[[Path, QualificationPolicy, AcquisitionLimits], dict[str, Any]],
) -> None:
    """Constrain the complete transport/parser process; return only compact metadata."""
    try:
        if sys.platform != "darwin":
            resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.max_bytes, limits.max_bytes))
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = str(limits.threads)
        started = time.monotonic()
        metadata = _stream(
            session, directory, source_url, policy, limits, lambda: access_timestamp, started
        )
        # The parent additionally enforces the qualification-specific deadline.
        connection.send({"phase": "qualification", "observed": metadata})
        metadata.update(inspect(directory / "source.part", policy, limits))
        metadata["elapsed_seconds"] = time.monotonic() - started
        connection.send({"result": metadata})
    except BaseException as error:
        connection.send({"error": f"{type(error).__name__}: {str(error)[:2000]}"})
    finally:
        connection.close()


def _validate_response_headers(response: Any, limits: AcquisitionLimits) -> int | None:
    """Require an unencoded PDF response and bound its optional declared length."""
    if response.status_code != 200:
        raise ValueError(f"expected HTTP 200, observed {response.status_code}")
    mime = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if mime != "application/pdf":
        raise ValueError("required response Content-Type is not application/pdf")
    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
        raise ValueError("encoded response prevents exact wire-size qualification")
    declared = response.headers.get("Content-Length")
    expected = None if declared is None else int(declared)
    if expected is not None and (expected <= 0 or expected > limits.max_bytes):
        raise ValueError("Content-Length exceeds reviewed byte ceiling or is empty")
    return expected


def _stream(
    session: Any,
    directory: Path,
    source_url: str,
    policy: QualificationPolicy,
    limits: AcquisitionLimits,
    clock: Callable[[], str],
    started: float,
) -> dict[str, Any]:
    """Hash exactly once while streaming, validating each redirect before following it."""
    url = source_url
    redirects: list[dict[str, Any]] = []
    while True:
        validate_document_url(url, policy)
        remaining = limits.total_timeout_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("acquisition total elapsed ceiling exceeded")
        with session.get(
            url,
            stream=True,
            allow_redirects=False,
            headers={"Accept-Encoding": "identity"},
            timeout=(
                min(remaining, limits.connect_timeout_seconds),
                min(remaining, limits.read_timeout_seconds),
            ),
        ) as response:
            if response.url != url:
                raise ValueError("transport followed an unreviewed redirect")
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location or len(redirects) >= limits.max_redirects:
                    raise ValueError("missing redirect location or redirect ceiling exceeded")
                target = urljoin(url, location)
                validate_document_url(target, policy)
                redirects.append(
                    {"url": url, "status_code": response.status_code, "location": location}
                )
                url = target
                continue
            expected = _validate_response_headers(response, limits)
            digest = hashlib.sha256()
            size = 0
            with (directory / "source.part").open("xb") as output:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if time.monotonic() - started > limits.total_timeout_seconds:
                        raise TimeoutError("acquisition total elapsed ceiling exceeded")
                    if not chunk:
                        continue
                    if size + len(chunk) > limits.max_bytes:
                        raise ValueError("stream byte ceiling exceeded")
                    if shutil.disk_usage(directory).free < limits.minimum_free_bytes + len(chunk):
                        raise ValueError("disk free-space floor reached")
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                output.flush()
                os.fsync(output.fileno())
            if size == 0 or (expected is not None and size != expected):
                raise ValueError(f"truncated/empty transfer: expected {expected}, observed {size}")
            return {
                "original_url": source_url,
                "final_url": url,
                "access_timestamp_utc": clock(),
                "http_status": 200,
                "response_headers": {
                    key: response.headers[key]
                    for key in (
                        "Date",
                        "Content-Type",
                        "Content-Length",
                        "Content-Disposition",
                        "ETag",
                        "Last-Modified",
                        "Content-Encoding",
                    )
                    if key in response.headers
                },
                "redirects": redirects,
                "original_filename": (original_filename(response, "") or None),
                "byte_size": size,
                "sha256": digest.hexdigest(),
            }


def acquire_qualified_source(
    *,
    session: Any,
    data_root: Path,
    destination: Path,
    source_url: str,
    policy: QualificationPolicy,
    limits: AcquisitionLimits,
    clock: Callable[[], str],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Acquire after separate authorization, retaining bounded failure evidence.

    A fresh spawned subprocess bounds blocking network and parser operations, avoiding
    inherited parser or HTTP thread state. Session state is transferred only in memory.
    """
    validate_document_url(source_url, policy)
    directory = _destination(data_root, destination)
    if directory.exists():
        raise FileExistsError(f"acquisition requires a fresh namespace: {directory}")
    if (
        shutil.disk_usage(data_root).free
        < limits.minimum_free_bytes + limits.max_temporary_plus_final_bytes
    ):
        raise ValueError("insufficient free space for reviewed acquisition budget")
    binding = _binding(source_url, destination, policy, limits, provenance)
    if len(_canonical(binding)) > 64 * 1024:
        raise ValueError("reviewed acquisition binding exceeds 64 KiB metadata ceiling")
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(exist_ok=False)
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_worker,
        args=(child, session, directory, source_url, policy, limits, clock(), _inspect_pdf),
    )
    started = time.monotonic()
    peak_rss_bytes = 0
    observed: dict[str, Any] = {}
    deadline = started + limits.total_timeout_seconds
    try:
        process.start()
        child.close()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("acquisition or qualification elapsed ceiling exceeded")
            try:
                rss = psutil.Process(process.pid).memory_info().rss
            except psutil.NoSuchProcess:
                rss = 0
            peak_rss_bytes = max(peak_rss_bytes, rss)
            if rss > limits.memory_bytes:
                raise MemoryError("acquisition worker RSS ceiling exceeded")
            if not parent.poll(min(remaining, 0.05)):
                continue
            message = parent.recv()
            if "error" in message:
                raise ValueError(message["error"])
            if message.get("phase") == "qualification":
                observed = message["observed"]
                deadline = min(deadline, time.monotonic() + limits.qualification_timeout_seconds)
                continue
            observed = message["result"]
            observed["peak_observed_rss_bytes"] = peak_rss_bytes
            observed["memory_monitor_interval_seconds"] = 0.05
            break
        process.join(timeout=max(0, deadline - time.monotonic()))
        if process.is_alive() or process.exitcode != 0:
            raise ValueError("acquisition worker did not finish cleanly")
        return _publish_qualified(directory, binding, observed)
    except BaseException as error:
        if process.pid is not None and process.is_alive():
            process.kill()
            process.join(timeout=5)
        _retain_failure(directory, binding, observed, error, started, peak_rss_bytes)
        raise
    finally:
        parent.close()
        child.close()
