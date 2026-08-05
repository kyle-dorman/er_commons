"""Behavior-focused tests for the Task 03G.1 diagnostic boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.smoke_extraction.config import (
    load_smoke_spec,
    selected_pages,
    selection_sha256,
)
from er_commons.smoke_extraction.conversion import RangeDiagnostic
from er_commons.smoke_extraction.reporting import build_source_summary, validate_terminal_run
from er_commons.smoke_extraction.selection import smoke_id, validate_manifest_metadata
from er_commons.smoke_extraction.services import SmokeServices
from er_commons.smoke_extraction.source_processing import contiguous_ranges, process_source
from er_commons.smoke_extraction.table_stage import run_smoke_tables
from er_commons.smoke_extraction.workflow import run_smoke
from er_commons.source_freeze import sha256_file, write_json_atomic

SPEC_PATH = Path("configs/brisbane_baylands_2025_deir_task03g1_smoke_v1.json")


def _source_record(source: Any) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "official_title": source.source_id,
        "document_type": "appendix",
        "source_role": "model_corpus",
        "landing_page_key": "draft",
        "landing_page_url": "https://example.test",
        "linked_file_url": "https://example.test/source.pdf",
        "final_resolved_url": "https://example.test/source.pdf",
        "access_timestamp_utc": "2026-01-01T00:00:00Z",
        "http_status": 200,
        "response_headers": {},
        "redirect_history": [],
        "local_path": f"sources/{source.source_id}.pdf",
        "original_filename": f"{source.source_id}.pdf",
        "sha256": source.expected_sha256,
        "byte_size": source.expected_byte_size,
        "delivered_mime_type": "application/pdf",
        "detected_file_type": "pdf",
        "pdf_signature_valid": True,
        "pdf_page_count": source.expected_pdf_page_count,
        "retrieval_status": "complete",
        "validation_status": "accepted",
        "warnings": [],
        "visible_terms_note": "",
    }


def _write_sealed_manifest(data_root: Path) -> None:
    spec, _digest = load_smoke_spec(SPEC_PATH)
    path = data_root / spec.source_manifest_relative_path
    path.parent.mkdir(parents=True)
    write_json_atomic(
        path,
        {
            "manifest_schema_version": "1",
            "source_release_version": spec.source_release_version,
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "source_spec_schema_version": "1",
            "source_spec_sha256": "a" * 64,
            "visible_terms_note": "",
            "landing_pages": [],
            "sources": [_source_record(source) for source in spec.sources],
            "aggregates": {},
            "warnings": [],
        },
    )
    write_json_atomic(
        path.parent / "completion_record.json",
        {
            "source_release_version": spec.source_release_version,
            "manifest": {
                "local_path": spec.source_manifest_relative_path.as_posix(),
                "byte_size": path.stat().st_size,
                "sha256": sha256_file(path),
            },
        },
    )


def test_selection_rule_and_checked_in_seal_are_exact() -> None:
    """The frozen 35-source selection is formula-derived and checksum-closed."""
    spec, _digest = load_smoke_spec(SPEC_PATH)

    assert selected_pages(4) == [1, 2, 3, 4]
    assert selected_pages(11) == [1, 2, 3, 4, 5, 6, 7, 9, 10, 11]
    assert contiguous_ranges(selected_pages(222)) == [(1, 3), (110, 113), (220, 222)]
    pairs: list[list[str | int]] = [
        [source.source_id, page]
        for source in spec.sources
        for page in source.selected_physical_pages
    ]
    assert len(spec.sources) == 35
    assert len(pairs) == 342
    assert selection_sha256(pairs) == spec.selection_sha256


def test_manifest_reconciliation_uses_metadata_only(tmp_path: Path) -> None:
    """Pre-run validation needs a sealed manifest but no source PDF bytes."""
    _write_sealed_manifest(tmp_path)
    spec, _digest = load_smoke_spec(SPEC_PATH)

    validate_manifest_metadata(tmp_path, spec)

    assert not (tmp_path / "sources").exists()


class _FakeOptions:
    def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
        return {"diagnostic": True}


def test_smoke_retains_one_terminal_outcome_without_completion_artifacts(
    tmp_path: Path,
) -> None:
    """A mixed diagnostic result stays page-complete but never becomes a document candidate."""
    _write_sealed_manifest(tmp_path)
    spec, _digest = load_smoke_spec(SPEC_PATH)
    sources = [
        CompleteResolvedSource(
            source_id=source.source_id,
            source_path=tmp_path / "unused" / f"{source.source_id}.pdf",
            source_sha256=source.expected_sha256,
            source_byte_size=source.expected_byte_size,
            source_page_count=source.expected_pdf_page_count,
            warnings=[],
        )
        for source in spec.sources
    ]

    def fake_convert(
        _converter: Any,
        source: CompleteResolvedSource,
        first: int,
        last: int,
        output_root: Path,
        _services: Any,
    ) -> RangeDiagnostic:
        if source.source_id == "deir_main" and first == 1:
            raise RuntimeError("synthetic source-local failure")
        output_root.mkdir(parents=True)
        write_json_atomic(
            output_root / "observation.json",
            {"wall_seconds": 1.0, "peak_rss_bytes": 1234},
        )
        return RangeDiagnostic(
            document_payload={"pages": {str(page): {} for page in range(first, last + 1)}},
            converted_pages=list(range(first, last + 1)),
            raw_status="success",
            status="complete",
            errors=[],
            source_manifest_warnings=source.warnings,
            conversion_warnings=[],
            wall_seconds=1.0,
            cpu_seconds=1.0,
            peak_rss_bytes=1234,
        )

    services = SmokeServices(
        resolve_source=lambda _root, _spec, source_id: next(
            source for source in sources if source.source_id == source_id
        ),
        verify_models=lambda _root, _path: (None, tmp_path),
        build_converter=lambda *_args, **_kwargs: (
            object(),
            _FakeOptions(),
            SimpleNamespace(
                pipeline_cls=type("Pipeline", (), {}),
                backend=type("Backend", (), {}),
            ),
        ),
        convert=fake_convert,
        route=lambda _path, _document, page, _spec: {
            "physical_pdf_page": page,
            "route": "no_table_route",
        },
        run_tables=lambda *_args, **_kwargs: {},
        disk_usage=lambda _path: SimpleNamespace(free=100 * 1024**3),
        new_token=lambda: "fresh",
    )

    run_id = smoke_id(Path.cwd(), spec, _digest)
    stale = tmp_path / spec.artifact_relative_root / run_id / "attempts" / "attempt-stale"
    stale.mkdir(parents=True)
    (stale / "partial.txt").write_text("interrupted\n")
    summary_path = run_smoke(tmp_path, SPEC_PATH, services=services)
    summary = json.loads(summary_path.read_text())
    run_root = summary_path.parent

    assert summary["scope_status"] == "diagnostic_complete"
    assert summary["complete_document_semantics"] is False
    assert summary["requested_page_count"] == 342
    assert summary["status_counts"] == {"complete": 339, "conversion_failed": 3}
    assert summary["conversion_status_counts"] == {
        "complete": 339,
        "conversion_failed": 3,
    }
    assert summary["table_stage_status_counts"] == {
        "not_applicable": 339,
        "not_run": 3,
    }
    assert summary["error_count"] == 3
    assert summary["observed_peak_rss_bytes"] == 1234
    assert summary["attempt_id"] == "attempt-fresh"
    assert (stale / "partial.txt").is_file()
    assert (run_root / "attempts" / "attempt-fresh" / "diagnostic_summary.json").is_file()
    assert not list(run_root.rglob("completion_record.json"))
    assert not list(run_root.rglob("handoff.json"))
    assert hashlib.sha256((run_root / "smoke_spec.json").read_bytes()).hexdigest() == _digest


def test_low_disk_stops_every_source_without_source_resolution(tmp_path: Path) -> None:
    """The first low-disk decision terminally accounts for the remaining scope."""
    _write_sealed_manifest(tmp_path)
    calls: list[str] = []

    def unexpected_resolution(_root: Path, _spec: Any, source_id: str) -> Any:
        calls.append(source_id)
        raise AssertionError("source resolution must not run after the disk stop")

    services = SmokeServices(
        resolve_source=unexpected_resolution,
        verify_models=lambda _root, _path: (None, tmp_path),
        build_converter=lambda *_args, **_kwargs: (
            object(),
            _FakeOptions(),
            SimpleNamespace(
                pipeline_cls=type("Pipeline", (), {}),
                backend=type("Backend", (), {}),
            ),
        ),
        disk_usage=lambda _path: SimpleNamespace(free=0),
        new_token=lambda: "low-disk",
    )

    summary = json.loads(run_smoke(tmp_path, SPEC_PATH, services=services).read_text())

    assert calls == []
    assert summary["status_counts"] == {"not_run_resource_stop": 342}
    assert summary["conversion_status_counts"] == {"not_run": 342}
    assert summary["table_stage_status_counts"] == {"not_run": 342}


def test_terminal_validation_rejects_production_publication_names(tmp_path: Path) -> None:
    """A diagnostic tree cannot contain an artifact that resembles production completion."""
    forbidden = tmp_path / "nested" / "completion_record.json"
    forbidden.parent.mkdir()
    forbidden.write_text("{}\n")
    outcome = {
        "source_id": "source",
        "physical_pdf_page": 1,
        "status": "complete",
        "conversion": "complete",
        "routing": "complete",
        "route": "no_table_route",
        "table_stage": "not_applicable",
        "warnings": [],
        "errors": [],
    }

    with pytest.raises(RuntimeError, match="forbidden publication artifacts"):
        validate_terminal_run([outcome], 1, tmp_path)


def test_warning_summary_counts_each_scope_once(tmp_path: Path) -> None:
    """Source warnings deduplicate once while conversion and page evidence stays scoped."""
    source_root = tmp_path / "source"
    write_json_atomic(
        source_root / "source_warnings.json",
        {
            "scope": "source_manifest",
            "source_id": "source",
            "raw_warnings": ["source a", "source a", "source b"],
            "raw_count": 3,
            "exact_unique_count": 2,
        },
    )
    for index, conversion_warnings in enumerate((["range a", "range a"], ["range b"]), start=1):
        write_json_atomic(
            source_root / "conversion" / f"range_{index}" / "observation.json",
            {
                "source_warning_evidence": "../../source_warnings.json",
                "captured_python_warnings": conversion_warnings,
                "wall_seconds": 1.0,
                "peak_rss_bytes": 10,
            },
        )
    outcomes = [
        {
            "source_id": "source",
            "physical_pdf_page": 1,
            "status": "complete_with_warnings",
            "conversion": "complete",
            "routing": "complete",
            "route": "no_table_route",
            "table_stage": "not_applicable",
            "warnings": ["page warning"],
            "errors": [],
        }
    ]

    summary = build_source_summary("source", outcomes, source_root, 2.0)

    assert summary["warning_scope_counts"] == {
        "source_manifest_raw": 3,
        "source_manifest_unique": 2,
        "conversion": 3,
        "page": 1,
        "aggregate": 6,
    }
    assert summary["warning_count"] == 6
    assert summary["warning_evidence"] == [
        "source_warnings.json",
        "conversion/range_1/observation.json",
        "conversion/range_2/observation.json",
    ]


def test_source_warnings_survive_when_every_conversion_fails(tmp_path: Path) -> None:
    """Source-owned warning evidence does not depend on a successful conversion."""
    spec, _digest = load_smoke_spec(SPEC_PATH)
    source = CompleteResolvedSource(
        source_id="deir_main",
        source_path=tmp_path / "unused.pdf",
        source_sha256="a" * 64,
        source_byte_size=1,
        source_page_count=2092,
        warnings=["source a", "source a", "source b"],
    )
    services = SmokeServices(
        convert=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("failed")),
        route=lambda *_args, **_kwargs: {},
        run_tables=lambda *_args, **_kwargs: {},
    )
    source_root = tmp_path / "source"

    outcomes = process_source(
        tmp_path,
        "smoke-test",
        source,
        [1, 2, 3],
        source_root,
        object(),
        spec,
        services,
    )
    summary = build_source_summary("deir_main", outcomes, source_root, 1.0)

    assert summary["warning_scope_counts"]["source_manifest_raw"] == 3
    assert summary["warning_scope_counts"]["source_manifest_unique"] == 2
    assert summary["warning_count"] == 2
    assert summary["warning_evidence"] == ["source_warnings.json"]


def _diagnostic(first: int, last: int, *, extra_page: int | None = None) -> RangeDiagnostic:
    pages = list(range(first, last + 1))
    if extra_page is not None:
        pages.append(extra_page)
    return RangeDiagnostic(
        document_payload={"pages": {str(page): {} for page in pages}},
        converted_pages=pages,
        raw_status="success",
        status="complete",
        errors=[],
        source_manifest_warnings=[],
        conversion_warnings=[],
        wall_seconds=1.0,
        cpu_seconds=1.0,
        peak_rss_bytes=1234,
    )


def test_extra_converted_page_rejects_the_entire_requested_range(tmp_path: Path) -> None:
    """Docling cannot silently expand the exact frozen page authorization."""
    spec, _digest = load_smoke_spec(SPEC_PATH)
    source = CompleteResolvedSource(
        source_id="deir_main",
        source_path=tmp_path / "unused.pdf",
        source_sha256="a" * 64,
        source_byte_size=1,
        source_page_count=2092,
        warnings=[],
    )
    services = SmokeServices(
        convert=lambda _converter, _source, first, last, _root, _services: _diagnostic(
            first, last, extra_page=last + 1
        ),
        route=lambda *_args: (_ for _ in ()).throw(AssertionError("routing must not run")),
    )

    outcomes = process_source(
        tmp_path, "smokev1-test", source, [1, 2, 3], tmp_path / "source", object(), spec, services
    )

    assert [outcome["status"] for outcome in outcomes] == ["conversion_failed"] * 3
    assert all("outside requested range" in outcome["errors"][0] for outcome in outcomes)


def test_missing_routed_table_outcome_is_terminal_failure(tmp_path: Path) -> None:
    """Every routed page needs an explicit table-stage outcome."""
    spec, _digest = load_smoke_spec(SPEC_PATH)
    source = CompleteResolvedSource(
        source_id="deir_main",
        source_path=tmp_path / "unused.pdf",
        source_sha256="a" * 64,
        source_byte_size=1,
        source_page_count=2092,
        warnings=[],
    )
    services = SmokeServices(
        convert=lambda _converter, _source, first, last, _root, _services: _diagnostic(first, last),
        route=lambda _path, _document, page, _spec: {
            "physical_pdf_page": page,
            "route": "full_page_numeric",
        },
        run_tables=lambda *_args, **_kwargs: {
            1: {"status": "complete", "table_count": 1},
            2: {"status": "complete", "table_count": 0},
        },
    )

    outcomes = process_source(
        tmp_path, "smokev1-test", source, [1, 2, 3], tmp_path / "source", object(), spec, services
    )

    assert [outcome["status"] for outcome in outcomes] == ["complete", "complete", "table_failed"]
    assert outcomes[2]["table_stage"] == "table_failed"


def test_table_request_names_actual_attempt_artifact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The copied table request remains truthful despite use of an explicit override."""
    spec, _digest = load_smoke_spec(SPEC_PATH)
    source = CompleteResolvedSource(
        source_id="deir_main",
        source_path=tmp_path / "unused.pdf",
        source_sha256="a" * 64,
        source_byte_size=1,
        source_page_count=2092,
        warnings=[],
    )
    source_root = (
        tmp_path
        / spec.artifact_relative_root
        / "smokev1-test"
        / "attempts"
        / "attempt-test"
        / "sources"
        / source.source_id
    )
    source_root.mkdir(parents=True)

    def fake_table_pipeline(
        data_root: Path,
        request_path: Path,
        table_root: Path,
    ) -> Path:
        request = json.loads(request_path.read_text())
        assert request["artifact_relative_root"] == table_root.relative_to(data_root).as_posix()
        page_root = table_root / "pages" / "page_00001"
        page_root.mkdir(parents=True)
        write_json_atomic(page_root / "result.json", {"artifacts": {}, "tables": []})
        (table_root / "pages.jsonl").write_text(
            json.dumps(
                {
                    "physical_pdf_page": 1,
                    "route": "full_page_numeric",
                    "table_count": 0,
                    "result": "pages/page_00001/result.json",
                }
            )
            + "\n"
        )
        write_json_atomic(table_root / "manifest.json", {})
        return table_root / "manifest.json"

    monkeypatch.setattr(
        "er_commons.smoke_extraction.table_stage.run_table_extraction",
        fake_table_pipeline,
    )

    outcomes = run_smoke_tables(
        tmp_path,
        "smokev1-test",
        source,
        [{"physical_pdf_page": 1, "route": "full_page_numeric"}],
        source_root,
        spec,
    )

    assert outcomes[1]["status"] == "complete"
    assert outcomes[1]["table_count"] == 0
    assert not list(source_root.rglob("*.png"))
