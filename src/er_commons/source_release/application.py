"""Short application shell for source-release acquisition and verification."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from er_commons.source_release.http_discovery import build_http_session
from er_commons.source_release.models import SourceManifest, load_source_spec
from er_commons.source_release.pdf_download import download_source
from er_commons.source_release.publication import (
    Download,
    ReleasePaths,
    freeze_with_session,
    recover_final_records,
    verify_release,
)


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class SourceReleaseServices:
    """Injected network, clock, and download seams for one acquisition."""

    session_factory: Callable[[], Any] = build_http_session
    clock: Callable[[], str] = utc_now
    downloader: Download = download_source


def freeze_release(
    data_root: Path,
    spec_path: Path,
    *,
    services: SourceReleaseServices | None = None,
) -> SourceManifest:
    """Acquire a complete source release or safely resume an interrupted run."""
    active = services or SourceReleaseServices()
    spec, _ = load_source_spec(spec_path)
    if ReleasePaths.from_spec(data_root, spec).manifest.exists():
        return recover_final_records(data_root, spec_path, clock=active.clock)
    session = active.session_factory()
    try:
        return freeze_with_session(
            data_root,
            spec_path,
            session=session,
            clock=active.clock,
            downloader=active.downloader,
        )
    finally:
        session.close()


__all__ = ["SourceReleaseServices", "freeze_release", "utc_now", "verify_release"]
