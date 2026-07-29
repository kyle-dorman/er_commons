"""Offline application-level tests for the complete producer runner."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import er_commons.document_extraction.complete_document as application
from er_commons.document_extraction.complete_document import PreparedProducer
from er_commons.document_extraction.producer_artifacts import verify_completed_run
from er_commons.document_extraction.producer_config import load_producer_config
from er_commons.document_extraction.producer_conversion import (
    ConversionOutput,
)
from er_commons.document_extraction.producer_identity import (
    ProducerIdentity,
    canonical_json_sha256,
)
from er_commons.document_extraction.producer_records import (
    ConversionObservation,
    PageRouteRecord,
)
from er_commons.document_extraction.producer_services import (
    GitState,
    ProducerServices,
)
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.source_freeze import sha256_file, write_json_atomic


def _route_record() -> PageRouteRecord:
    return PageRouteRecord(
        physical_pdf_page=1,
        page_size_pdf_points=[612.0, 792.0],
        native_character_count=4,
        nonspace_character_count=4,
        native_text_rectangle_count=1,
        nonempty_line_count=1,
        text_width_fraction=0.1,
        text_height_fraction=0.1,
        nonspace_characters_per_square_point=0.0001,
        digit_fraction=0,
        coordinate_key_count=0,
        strict_table_dominant=False,
        strict_checks={
            "width": False,
            "height": False,
            "lines": False,
            "density": False,
            "digits": False,
        },
        numeric_table_bearing=False,
        numeric_checks={
            "width": False,
            "lines": False,
            "density": False,
            "digits": False,
        },
        layout_table_region_count=0,
        layout_table_regions_pdf_points_bottom_left=[],
        route="no_table_route",
        source_id="document",
        layout_table_observations=[],
        status="complete",
    )


def _services() -> ProducerServices:
    def unused_converter(
        _models_root: Path,
        *,
        thread_count: int,
    ) -> tuple[Any, Any, Any]:
        raise AssertionError(f"unexpected converter construction: {thread_count}")

    def unused_tables(
        _data_root: Path,
        _config_path: Path,
        _artifact_root: Path | None = None,
    ) -> Path:
        raise AssertionError("no-table fake run must not invoke the table runner")

    ticks = iter(float(value) for value in range(1, 100))
    return ProducerServices(
        build_converter=unused_converter,
        run_tables=unused_tables,
        memory_observation=lambda: pytest.fail("memory sampler should be faked"),
        monotonic=lambda: next(ticks),
        process_time=lambda: 1.0,
        now=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        new_token=lambda: "12345678abcdef",
        read_git_state=lambda _root: GitState(commit="abc123", dirty=False),
    )


def _prepared(tmp_path: Path) -> PreparedProducer:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-test")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    source_manifest_path = tmp_path / "source_manifest.json"
    source_manifest_path.write_text('{"sealed": true}\n')
    config, config_sha256 = load_producer_config(
        Path("configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json")
    )
    config = config.model_copy(
        update={
            "source": config.source.model_copy(
                update={
                    "source_id": "document",
                    "official_title": "Document",
                    "expected_sha256": source_sha256,
                    "expected_byte_size": source_path.stat().st_size,
                    "expected_pdf_page_count": 1,
                }
            ),
            "artifact_relative_root": Path("pipelines/test_complete_document"),
        }
    )
    source = CompleteResolvedSource(
        source_id="document",
        source_path=source_path,
        source_sha256=source_sha256,
        source_byte_size=source_path.stat().st_size,
        source_page_count=1,
        warnings=[],
    )
    identity_payload = {
        "source": {"source_id": "document", "sha256": source_sha256},
        "sealed_release": {"manifest_sha256": sha256_file(source_manifest_path)},
        "policy": "offline-test",
    }
    identity = ProducerIdentity(
        run_id=f"prv1-{canonical_json_sha256(identity_payload)}",
        payload=identity_payload,
    )
    return PreparedProducer(
        config=config,
        config_sha256=config_sha256,
        source=source,
        source_manifest_path=source_manifest_path,
        converter=object(),
        runtime={"configuration_id": "fake"},
        identity=identity,
    )


def _successful_conversion(producer_root: Path) -> ConversionOutput:
    document_payload = {"pages": {"1": {"page_no": 1}}, "tables": []}
    write_json_atomic(producer_root / "docling" / "document.json", document_payload)
    write_json_atomic(
        producer_root / "docling" / "conversion_pages.json",
        {"pages": [{"page_no": 1}], "assembled": {}, "confidence": {}},
    )
    write_json_atomic(producer_root / "asset_inventory.json", {"assets": []})
    observation = ConversionObservation(
        source_id="document",
        raw_status="success",
        status="complete",
        errors=[],
        captured_python_warnings=[],
        source_manifest_warnings=[],
        expected_physical_pages=[1],
        converted_physical_pages=[1],
        page_coverage_complete=True,
        asset_count=0,
        wall_seconds=1,
        cpu_seconds=1,
        peak_rss_bytes=100,
    )
    write_json_atomic(
        producer_root / "docling" / "conversion_observation.json",
        observation.model_dump(mode="json"),
    )
    return ConversionOutput(
        document_payload=document_payload,
        assets=[],
        observation=observation,
    )


def test_fake_run_publishes_atomically_then_reuses_verified_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    conversions = 0

    def fake_prepare(
        _data_root: Path,
        *,
        config: Any,
        config_sha256: str,
        services: ProducerServices,
    ) -> PreparedProducer:
        del config, config_sha256, services
        return prepared

    def fake_convert(**arguments: Any) -> ConversionOutput:
        nonlocal conversions
        conversions += 1
        return _successful_conversion(arguments["producer_root"])

    monkeypatch.setattr(application, "prepare_producer", fake_prepare)
    monkeypatch.setattr(application, "run_complete_conversion", fake_convert)
    monkeypatch.setattr(
        application,
        "route_complete_document",
        lambda _source, _payload, _config: [_route_record()],
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    completion = application.run_complete_document_producer(
        tmp_path,
        config_path,
        services=_services(),
    )

    run_root = completion.parents[1]
    assert completion.is_file()
    assert not (run_root.parent / ".tmp" / run_root.name).exists()
    assert verify_completed_run(run_root, prepared.identity.run_id) == completion
    summary = json.loads((run_root / "records" / "producer_summary.json").read_text())
    assert summary["routing"] == {
        "no_table_route": 1,
        "layout_regions": 0,
        "full_page_numeric": 0,
    }
    assert summary["tables"]["status"] == "not_applicable"
    assert conversions == 1

    reused = application.run_complete_document_producer(
        tmp_path,
        config_path,
        services=_services(),
    )

    assert reused == completion
    assert conversions == 1


def test_fake_conversion_failure_is_preserved_as_attempt_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)

    monkeypatch.setattr(
        application,
        "prepare_producer",
        lambda *_args, **_kwargs: prepared,
    )

    def fail_conversion(**arguments: Any) -> ConversionOutput:
        producer_root = arguments["producer_root"]
        write_json_atomic(producer_root / "docling" / "partial.json", {"page": 1})
        raise RuntimeError("simulated conversion failure")

    monkeypatch.setattr(application, "run_complete_conversion", fail_conversion)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    with pytest.raises(RuntimeError, match="simulated conversion failure"):
        application.run_complete_document_producer(
            tmp_path,
            config_path,
            services=_services(),
        )

    task_root = tmp_path / prepared.config.artifact_relative_root
    attempts = list((task_root / "attempts").iterdir())
    assert len(attempts) == 1
    assert (attempts[0] / "documents/document/producer/docling/partial.json").is_file()
    assert not (attempts[0] / "records/completion_record.json").exists()
    assert not (task_root / prepared.identity.run_id).exists()
