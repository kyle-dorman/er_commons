"""Offline orchestration tests for fresh, resumed, and recovered source releases."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pikepdf
import pytest
import requests

from er_commons.source_release import (
    LandingPageSpec,
    ReleaseSpec,
    SourceRole,
    SourceSpecEntry,
    freeze_release,
)
from er_commons.source_release.application import SourceReleaseServices
from er_commons.source_release.pdf_download import download_source
from er_commons.source_release.publication import ReleasePaths

NOW = "2026-08-18T12:00:00+00:00"


class RouterSession:
    """In-memory URL router implementing the acquisition session boundary."""

    def __init__(self, content: dict[str, bytes]) -> None:
        self.content = content
        self.calls: list[str] = []
        self.closed = False

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        del kwargs
        self.calls.append(url)
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response._content = self.content[url]
        response._content_consumed = True
        if url.endswith("/draft") or url.endswith("/copyright"):
            response.headers["Content-Type"] = "text/html"
        else:
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Length"] = str(len(self.content[url]))
        return response

    def close(self) -> None:
        self.closed = True


def _pdf_bytes() -> bytes:
    output = BytesIO()
    with pikepdf.new() as document:
        document.add_blank_page()
        document.save(output)
    return output.getvalue()


def _spec(path: Path, *, schema_version: str = "test.source_spec.v1") -> ReleaseSpec:
    spec = ReleaseSpec(
        schema_version=schema_version,
        release_id="test_release_v1",
        manifest_schema_version="test.manifest.v1",
        landing_pages=[
            LandingPageSpec(
                key="draft",
                url="https://www.brisbaneca.gov/draft",
                snapshot_filename="draft.html",
                expected_excluded_document_ids=[],
            ),
            LandingPageSpec(
                key="copyright",
                url="https://www.brisbaneca.gov/copyright",
                snapshot_filename="copyright.html",
                expected_excluded_document_ids=[],
            ),
        ],
        terms_note_filename="terms.md",
        sources=[
            SourceSpecEntry(
                source_id="main",
                document_center_id=1,
                landing_page_key="draft",
                role=SourceRole.MODEL_CORPUS,
                expected_label="Main",
                local_filename="main.pdf",
            ),
            SourceSpecEntry(
                source_id="response",
                document_center_id=2,
                landing_page_key="draft",
                role=SourceRole.CURATOR_ONLY_RESPONSE_SOURCE,
                expected_label="Response",
                local_filename="response.pdf",
            ),
        ],
    )
    path.write_text(spec.model_dump_json(indent=2) + "\n")
    return spec


def _content() -> dict[str, bytes]:
    pdf = _pdf_bytes()
    return {
        "https://www.brisbaneca.gov/draft": (
            b'<a href="/DocumentCenter/View/1">Main</a>'
            b'<a href="/DocumentCenter/View/2">Response</a>'
        ),
        "https://www.brisbaneca.gov/copyright": b"<html>copyright</html>",
        "https://www.brisbaneca.gov/DocumentCenter/View/1": pdf,
        "https://www.brisbaneca.gov/DocumentCenter/View/2": pdf,
    }


def _services(session: RouterSession, *, downloader=download_source) -> SourceReleaseServices:
    return SourceReleaseServices(
        session_factory=lambda: session,
        clock=lambda: NOW,
        downloader=downloader,
    )


def test_fresh_release_publishes_completion_and_removes_restart_state(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    spec = _spec(spec_path)
    session = RouterSession(_content())

    manifest = freeze_release(tmp_path, spec_path, services=_services(session))
    paths = ReleasePaths.from_spec(tmp_path, spec)

    assert manifest.aggregates["file_count"] == 2
    assert paths.completion.is_file()
    assert not paths.state.exists()
    assert not list(paths.release_root.rglob("*.part"))
    assert session.closed


def test_interrupted_release_resumes_without_redownloading_completed_source(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.json"
    spec = _spec(spec_path)
    first_session = RouterSession(_content())

    def interrupt_second(*args: Any, **kwargs: Any):
        source = args[1]
        if source.source_id == "response":
            raise RuntimeError("synthetic interruption")
        return download_source(*args, **kwargs)

    with pytest.raises(RuntimeError, match="synthetic interruption"):
        freeze_release(
            tmp_path,
            spec_path,
            services=_services(first_session, downloader=interrupt_second),
        )
    paths = ReleasePaths.from_spec(tmp_path, spec)
    assert paths.state.is_file()

    second_session = RouterSession(_content())
    manifest = freeze_release(tmp_path, spec_path, services=_services(second_session))

    assert manifest.aggregates["file_count"] == 2
    assert "https://www.brisbaneca.gov/DocumentCenter/View/1" not in second_session.calls
    assert "https://www.brisbaneca.gov/DocumentCenter/View/2" in second_session.calls
    assert not paths.state.exists()


def test_changed_spec_rejects_existing_restart_state(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    _spec(spec_path)
    session = RouterSession(_content())

    def stop(*args: Any, **kwargs: Any):
        raise RuntimeError("stop after page evidence")

    with pytest.raises(RuntimeError):
        freeze_release(tmp_path, spec_path, services=_services(session, downloader=stop))
    _spec(spec_path, schema_version="test.source_spec.changed")

    with pytest.raises(ValueError, match="different source specification"):
        freeze_release(
            tmp_path,
            spec_path,
            services=_services(RouterSession(_content())),
        )


def test_existing_manifest_recovers_missing_records_without_session(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    spec = _spec(spec_path)
    freeze_release(tmp_path, spec_path, services=_services(RouterSession(_content())))
    paths = ReleasePaths.from_spec(tmp_path, spec)
    paths.acquisition.unlink()
    paths.inventory.unlink()
    paths.completion.unlink()

    def fail_session() -> RouterSession:
        raise AssertionError("completed-manifest recovery must not create an HTTP session")

    recovered = freeze_release(
        tmp_path,
        spec_path,
        services=SourceReleaseServices(session_factory=fail_session, clock=lambda: NOW),
    )

    assert recovered.source_release_version == spec.release_id
    assert paths.acquisition.is_file()
    assert paths.inventory.is_file()
    assert paths.completion.is_file()
