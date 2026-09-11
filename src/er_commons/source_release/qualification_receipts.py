"""Compact qualification publication and metadata-only receipt verification."""

from __future__ import annotations

import hashlib
import json
import os
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from er_commons.source_release.acquisition_limits import AcquisitionLimits
from er_commons.source_release.qualification import QualificationPolicy, policy_sha256


def _canonical(value: Any) -> bytes:
    """Serialize compact records deterministically for small-record seals."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _write(path: Path, value: Any) -> None:
    """Write a new compact record with exclusive creation and durability."""
    payload = _canonical(value)
    if len(payload) > 256 * 1024:
        raise ValueError("compact acquisition record exceeds 256 KiB")
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _destination(data_root: Path, destination: Path) -> Path:
    """Resolve a relative directory strictly inside the configured artifact root."""
    root = data_root.resolve(strict=True)
    if destination.is_absolute() or ".." in destination.parts or not destination.parts:
        raise ValueError("destination must be a contained relative directory")
    path = root / destination
    if not path.resolve().is_relative_to(root) or path.resolve() == root:
        raise ValueError("destination escapes artifact root")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError("destination cannot traverse symlinks")
        current = current.parent
    return path


def _binding(
    source_url: str,
    destination: Path,
    policy: QualificationPolicy,
    limits: AcquisitionLimits,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Bind every reviewed input to the compact completion receipt."""
    return {
        "schema_version": "er_commons.recovery.qualified_acquisition.v1",
        "source_url": source_url,
        "destination": destination.as_posix(),
        "policy_sha256": policy_sha256(policy),
        "limits": limits.model_dump(mode="json"),
        "provenance": provenance,
        "qualification_implementation": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in (
                "qualified_acquisition.py",
                "qualification.py",
                "pdf_download.py",
                "acquisition_limits.py",
                "qualification_receipts.py",
            )
        },
        "software_versions": {
            name: version(name) for name in ("requests", "pikepdf", "pypdf", "psutil")
        },
    }


def _publish_qualified(
    directory: Path, binding: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    """Publish the small source record and write its completion last."""
    os.link(directory / "source.part", directory / "source.pdf")
    (directory / "source.part").unlink()
    stat = (directory / "source.pdf").stat()
    record = {
        "binding": binding,
        "observed": observed,
        "payload_stat": {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "inode": stat.st_ino,
        },
        "status": "qualified",
        "verification_scope": "stream_digest_then_metadata_only",
    }
    _write(directory / "source_record.json", record)
    _write(
        directory / "completion.json",
        {
            "schema_version": "er_commons.recovery.qualified_completion.v1",
            "record_sha256": hashlib.sha256(_canonical(record)).hexdigest(),
            "members": ["completion.json", "source.pdf", "source_record.json"],
        },
    )
    return dict(record)


def _retain_failure(
    directory: Path,
    binding: dict[str, Any],
    observed: dict[str, Any],
    error: BaseException,
    started: float,
    peak_rss_bytes: int,
) -> None:
    """Retain bounded nonterminal evidence even when semantic observations exceed limits."""
    next_step = (
        "retain delivered bytes; separately propose local requalification under revised policy"
        if observed.get("sha256")
        else "retain incomplete attempt; separately authorize acquisition in a fresh namespace"
    )
    if len(_canonical(observed)) > 128 * 1024:
        compact_transport = {
            key: observed[key]
            for key in (
                "sha256",
                "byte_size",
                "original_url",
                "final_url",
                "access_timestamp_utc",
                "http_status",
                "response_headers",
                "redirects",
                "original_filename",
            )
            if key in observed and len(_canonical(observed[key])) <= 8 * 1024
        }
        observed = {
            **compact_transport,
            "omitted_oversized_evidence_sha256": hashlib.sha256(_canonical(observed)).hexdigest(),
            "omitted_oversized_evidence_bytes": len(_canonical(observed)),
        }
    _write(
        directory / "failure.json",
        {
            "status": "incomplete",
            "binding": binding,
            "error": f"{type(error).__name__}: {str(error)[:2000]}",
            "elapsed_seconds": time.monotonic() - started,
            "peak_observed_rss_bytes": peak_rss_bytes,
            "observed": observed,
            "retained_payload_bytes": sum(
                (directory / name).stat().st_size
                for name in ("source.part", "source.pdf")
                if (directory / name).exists()
            ),
            "next_step": next_step,
        },
    )


def reuse_qualified_source(
    *,
    data_root: Path,
    destination: Path,
    source_url: str,
    policy: QualificationPolicy,
    limits: AcquisitionLimits,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Verify completion and payload metadata without opening or hashing the PDF."""
    directory = _destination(data_root, destination)
    expected = ["completion.json", "source.pdf", "source_record.json"]
    if sorted(item.name for item in directory.iterdir()) != expected:
        raise ValueError("qualified receipt has incomplete or unexpected membership")
    for name in expected:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"qualified receipt member is not a regular file: {name}")
        if name != "source.pdf" and path.stat().st_size > 256 * 1024:
            raise ValueError("compact receipt exceeds metadata budget")
    record_bytes = (directory / "source_record.json").read_bytes()
    record = json.loads(record_bytes)
    completion = json.loads((directory / "completion.json").read_bytes())
    if completion != {
        "schema_version": "er_commons.recovery.qualified_completion.v1",
        "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
        "members": expected,
    }:
        raise ValueError("qualified receipt seal mismatch")
    if record.get("binding") != _binding(source_url, destination, policy, limits, provenance):
        raise ValueError("stale source, policy, resource, or destination binding")
    stat = (directory / "source.pdf").stat()
    if record.get("payload_stat") != {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "inode": stat.st_ino,
    }:
        raise ValueError("qualified payload metadata changed; bounded audit required")
    if record.get("status") != "qualified":
        raise ValueError("source qualification is incomplete")
    return dict(record)
