"""Source-free transport, strict PDF, publication, and metadata-reuse tests."""

from __future__ import annotations

import hashlib
import io
import json
import time
from pathlib import Path
from typing import Any

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from er_commons.source_release import qualification_receipts as receipts
from er_commons.source_release import qualified_acquisition as acquisition
from er_commons.source_release.qualification import QualificationPolicy

URL = "https://www.brisbaneca.gov/DocumentCenter/View/2972/Appendix-F1-PDF"


class Response:
    """Minimal streamed Requests response with observable redirect attempts."""

    def __init__(self, payload: bytes, *, status: int = 200, headers: dict[str, str] | None = None):
        self.payload = payload
        self.status_code = status
        self.headers = {"Content-Type": "application/pdf", "Content-Length": str(len(payload))}
        self.headers.update(headers or {})
        self.url = URL

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *_: Any) -> None:
        pass

    def iter_content(self, chunk_size: int):  # type: ignore[no-untyped-def]
        yield from (
            self.payload[index : index + chunk_size]
            for index in range(0, len(self.payload), chunk_size)
        )


class Session:
    """Record request calls without ever using network access."""

    def __init__(self, response: Response, delay: float = 0):
        self.response = response
        self.delay = delay
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: Any) -> Response:
        self.calls.append(url)
        assert kwargs["allow_redirects"] is False
        time.sleep(self.delay)
        return self.response


@pytest.fixture
def policy() -> QualificationPolicy:
    return QualificationPolicy(
        advertised_label="Appendix F1 - Transportation Impact Assessment (PDF)",
        accepted_titles=("Transportation Impact Assessment",),
        required_internal_phrases=("Existing Traffic Conditions Memo",),
        required_project_phrases=("Brisbane Baylands",),
        edition="Final",
        edition_phrases=("Final EIR",),
        expected_document_center_id=2972,
        allowed_hosts=("www.brisbaneca.gov",),
        max_pages=20,
    )


@pytest.fixture
def limits() -> acquisition.AcquisitionLimits:
    return acquisition.AcquisitionLimits(
        connect_timeout_seconds=1,
        read_timeout_seconds=1,
        total_timeout_seconds=20,
        qualification_timeout_seconds=10,
        max_bytes=1024 * 1024,
        minimum_free_bytes=1024,
        max_temporary_plus_final_bytes=2 * 1024 * 1024,
        memory_bytes=2 * 1024**3,
    )


def pdf_bytes(title: str = "Transportation Impact Assessment") -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    lines = [title, "Brisbane Baylands", "Final EIR", "Existing Traffic Conditions Memo"]
    stream.set_data(
        (
            "BT /F1 12 Tf 50 700 Td " + " 0 -20 Td ".join(f"({line}) Tj" for line in lines) + " ET"
        ).encode()
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def acquire(
    tmp_path: Path,
    policy: QualificationPolicy,
    limits: acquisition.AcquisitionLimits,
    response: Response,
    **extra: Any,
) -> dict[str, Any]:
    return acquisition.acquire_qualified_source(
        session=Session(response, **extra),
        data_root=tmp_path,
        destination=Path("new"),
        source_url=URL,
        policy=policy,
        limits=limits,
        clock=lambda: "2026-09-10T00:00:00Z",
        provenance={"edition": "Final", "logical_source_id": "deir_appendix_f1"},
    )


def reuse(
    tmp_path: Path, policy: QualificationPolicy, limits: acquisition.AcquisitionLimits
) -> dict[str, Any]:
    return acquisition.reuse_qualified_source(
        data_root=tmp_path,
        destination=Path("new"),
        source_url=URL,
        policy=policy,
        limits=limits,
        provenance={"edition": "Final", "logical_source_id": "deir_appendix_f1"},
    )


def test_publish_digest_and_metadata_only_reuse(tmp_path, policy, limits, monkeypatch):
    payload = pdf_bytes()
    result = acquire(tmp_path, policy, limits, Response(payload))
    assert result["observed"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["observed"]["pdf_page_count"] == 1
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.suffix != ".pdf", "receipt reuse opened the PDF"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(acquisition, "_inspect_pdf", lambda *_: pytest.fail("reuse parsed PDF"))
    assert reuse(tmp_path, policy, limits) == result
    with pytest.raises(FileExistsError):
        acquire(tmp_path, policy, limits, Response(payload))


@pytest.mark.parametrize("case", ["title", "malformed", "truncated", "oversized", "mime", "status"])
def test_rejected_sources_retain_failure(tmp_path, policy, limits, case):
    response = Response(pdf_bytes())
    if case == "title":
        response = Response(pdf_bytes("Bayshore Mobility Study"))
    elif case == "malformed":
        response = Response(b"%PDF-1.7 invalid data")
    elif case == "truncated":
        response.headers["Content-Length"] = str(len(response.payload) + 1)
    elif case == "oversized":
        response.headers.pop("Content-Length")
        response.payload = b"x" * (limits.max_bytes + 1)
    elif case == "mime":
        response.headers["Content-Type"] = "text/html"
    elif case == "status":
        response.status_code = 206
    with pytest.raises(ValueError):
        acquire(tmp_path, policy, limits, response)
    assert not (tmp_path / "new/completion.json").exists()
    assert json.loads((tmp_path / "new/failure.json").read_text())["status"] == "incomplete"
    assert (
        sum(p.stat().st_size for p in (tmp_path / "new").iterdir())
        < limits.max_temporary_plus_final_bytes
    )


def test_redirect_rejected_before_following(tmp_path, policy, limits):
    session = Session(
        Response(
            b"",
            status=302,
            headers={"Location": "https://www.brisbaneca.gov/DocumentCenter/View/553/Wrong"},
        )
    )
    with pytest.raises(ValueError):
        acquisition._stream(session, tmp_path, URL, policy, limits, lambda: "now", time.monotonic())
    assert session.calls == [URL]


def test_hard_timeout_covers_blocking_request(tmp_path, policy, limits):
    limits = limits.model_copy(
        update={"total_timeout_seconds": 0.1, "qualification_timeout_seconds": 0.1}
    )
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        acquire(tmp_path, policy, limits, Response(pdf_bytes()), delay=5)
    assert time.monotonic() - started < 2
    assert (tmp_path / "new/failure.json").is_file()


def test_stale_receipt_and_unexpected_members(tmp_path, policy, limits):
    acquire(tmp_path, policy, limits, Response(pdf_bytes()))
    changed = policy.model_copy(update={"max_pages": 19})
    with pytest.raises(ValueError, match="stale"):
        reuse(tmp_path, changed, limits)
    (tmp_path / "new/unexpected").touch()
    with pytest.raises(ValueError, match="membership"):
        reuse(tmp_path, policy, limits)
    (tmp_path / "new/unexpected").unlink()
    with (tmp_path / "new/source.pdf").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="metadata"):
        reuse(tmp_path, policy, limits)


def test_wrong_destination_no_request(tmp_path, policy, limits):
    session = Session(Response(pdf_bytes()))
    with pytest.raises(ValueError, match="contained"):
        acquisition.acquire_qualified_source(
            session=session,
            data_root=tmp_path,
            destination=Path("../escape"),
            source_url=URL,
            policy=policy,
            limits=limits,
            clock=lambda: "now",
            provenance={},
        )
    assert session.calls == []


def test_changed_tool_identity_invalidates_receipt(tmp_path, policy, limits, monkeypatch):
    acquire(tmp_path, policy, limits, Response(pdf_bytes()))
    monkeypatch.setattr(receipts, "version", lambda _: "changed")
    with pytest.raises(ValueError, match="stale"):
        reuse(tmp_path, policy, limits)


def test_qualification_timeout_retains_transport_metadata(tmp_path, policy, limits, monkeypatch):
    monkeypatch.setattr(acquisition, "_inspect_pdf", slow_inspection)
    limits = limits.model_copy(update={"qualification_timeout_seconds": 0.1})
    with pytest.raises(TimeoutError):
        acquire(tmp_path, policy, limits, Response(pdf_bytes()))
    failure = json.loads((tmp_path / "new/failure.json").read_text())
    assert failure["observed"]["http_status"] == 200
    assert failure["retained_payload_bytes"] == len(pdf_bytes())


def test_oversized_semantic_record_still_retains_failure(tmp_path, policy, limits, monkeypatch):
    monkeypatch.setattr(acquisition, "_inspect_pdf", oversized_inspection)
    with pytest.raises(ValueError, match="record exceeds"):
        acquire(tmp_path, policy, limits, Response(pdf_bytes()))
    failure = json.loads((tmp_path / "new/failure.json").read_text())
    assert failure["observed"]["omitted_oversized_evidence_bytes"] > 256 * 1024
    assert failure["observed"]["sha256"] == hashlib.sha256(pdf_bytes()).hexdigest()
    assert failure["observed"]["http_status"] == 200
    assert failure["observed"]["byte_size"] == len(pdf_bytes())
    assert "local requalification" in failure["next_step"]
    assert not (tmp_path / "new/completion.json").exists()


def test_parent_enforces_observed_rss_ceiling(tmp_path, policy, limits, monkeypatch):
    class OverBudgetProcess:
        def __init__(self, _pid):
            pass

        def memory_info(self):
            from types import SimpleNamespace

            return SimpleNamespace(rss=limits.memory_bytes + 1)

    monkeypatch.setattr(acquisition.psutil, "Process", OverBudgetProcess)
    with pytest.raises(MemoryError, match="RSS"):
        acquire(tmp_path, policy, limits, Response(pdf_bytes()), delay=1)
    failure = json.loads((tmp_path / "new/failure.json").read_text())
    assert failure["peak_observed_rss_bytes"] > limits.memory_bytes


def test_disk_and_symlink_destinations_fail_before_request(tmp_path, policy, limits, monkeypatch):
    from types import SimpleNamespace

    (tmp_path / "link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinks"):
        acquisition._destination(tmp_path, Path("link/new"))
    session = Session(Response(pdf_bytes()))
    monkeypatch.setattr(acquisition.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(ValueError, match="free space"):
        acquisition.acquire_qualified_source(
            session=session,
            data_root=tmp_path,
            destination=Path("new"),
            source_url=URL,
            policy=policy,
            limits=limits,
            clock=lambda: "now",
            provenance={},
        )
    assert session.calls == []


def test_stream_digest_updates_exactly_once_per_delivered_byte(
    tmp_path, policy, limits, monkeypatch
):
    payload = pdf_bytes()
    original_sha256 = hashlib.sha256
    updated = bytearray()

    class ObservedDigest:
        def __init__(self):
            self.digest = original_sha256()

        def update(self, chunk):
            updated.extend(chunk)
            self.digest.update(chunk)

        def hexdigest(self):
            return self.digest.hexdigest()

    monkeypatch.setattr(acquisition.hashlib, "sha256", ObservedDigest)
    result = acquisition._stream(
        Session(Response(payload)), tmp_path, URL, policy, limits, lambda: "now", time.monotonic()
    )
    assert bytes(updated) == payload
    assert result["sha256"] == original_sha256(payload).hexdigest()


def slow_inspection(*_):
    """Picklable subprocess test double for qualification timeout."""
    time.sleep(5)


def oversized_inspection(*_):
    """Picklable subprocess test double for bounded failure persistence."""
    return {"text": "x" * (300 * 1024)}
