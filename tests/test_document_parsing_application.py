"""Offline application-level tests for the complete producer runner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import er_commons.document_parsing.content_parsing.application as application
import er_commons.document_parsing.content_parsing.conversion_execution as conversion_execution
import er_commons.document_parsing.content_parsing.derived_publication as derived_publication
from er_commons.artifact_io import sha256_file, write_json_atomic, write_jsonl
from er_commons.document_parsing.content_parsing.application import PreparedContentParsing
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.conversion import (
    ConversionOutput,
)
from er_commons.document_parsing.content_parsing.conversion_identity import (
    COMMON_HEADING_HIERARCHY,
    effective_runtime_identity,
)
from er_commons.document_parsing.content_parsing.evidence import (
    verify_completed_run,
    write_inventory,
)
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    canonical_json_sha256,
)
from er_commons.document_parsing.content_parsing.records import (
    ConversionObservation,
    PageRouteRecord,
)
from er_commons.document_parsing.content_parsing.runtime import ModelInventory
from er_commons.document_parsing.content_parsing.services import (
    ContentParsingServices,
    GitState,
)
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource


def _route_record() -> PageRouteRecord:
    return PageRouteRecord(
        physical_pdf_page=1,
        page_size_pdf_points=[612.0, 792.0],
        displayed_page_size_pdf_points=[612.0, 792.0],
        source_page_bbox_pdf_points_bottom_left=[0.0, 0.0, 612.0, 792.0],
        routing_page_bbox_pdf_points_bottom_left=[0.0, 0.0, 612.0, 792.0],
        routing_coordinate_system="displayed_pdf_points_bottom_left",
        page_rotation_degrees=0,
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
        boundary_markers_before_first_table=[],
        status="complete",
    )


def _services(builds: list[Path] | None = None) -> ContentParsingServices:
    def fake_converter(
        models_root: Path,
        *,
        thread_count: int,
        heading_hierarchy_options: Any = None,
    ) -> tuple[Any, Any, Any]:
        assert thread_count == 4
        if builds is not None:
            builds.append(models_root)
        hierarchy_payload = (
            heading_hierarchy_options.model_dump(mode="json")
            if heading_hierarchy_options is not None
            else {
                "enabled": False,
                "use_bookmarks": True,
                "use_numbering": True,
                "use_style": True,
                "numbering_schemes": None,
                "max_level": 6,
                "bookmark_match_threshold": 0.8,
            }
        )
        hierarchy = SimpleNamespace(model_dump=lambda **_kwargs: hierarchy_payload)
        options = SimpleNamespace(
            document_timeout=None,
            heading_hierarchy_options=hierarchy,
            model_dump=lambda **_kwargs: {"artifacts_path": str(models_root)},
        )
        format_option = SimpleNamespace(
            pipeline_cls=type("FakePipeline", (), {}),
            backend=type("FakeBackend", (), {}),
        )
        return object(), options, format_option

    def unused_tables(
        _data_root: Path,
        _config_path: Path,
        _artifact_root: Path | None = None,
    ) -> Path:
        raise AssertionError("no-table fake run must not invoke the table runner")

    ticks = iter(float(value) for value in range(1, 100))
    return ContentParsingServices(
        build_converter=fake_converter,
        run_tables=unused_tables,
        memory_observation=lambda: pytest.fail("memory sampler should be faked"),
        monotonic=lambda: next(ticks),
        process_time=lambda: 1.0,
        now=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        new_token=lambda: "12345678abcdef",
        read_git_state=lambda _root: GitState(commit="abc123", dirty=False),
    )


def _prepared(tmp_path: Path) -> PreparedContentParsing:
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-test")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    source_manifest_path = tmp_path / "source_manifest.json"
    source_manifest_path.write_text('{"sealed": true}\n')
    config, config_sha256 = load_content_parsing_config(
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
        "source": {
            "source_id": "document",
            "sha256": source_sha256,
            "pdf_page_count": 1,
        },
        "sealed_release": {"manifest_sha256": sha256_file(source_manifest_path)},
        "policy": "offline-test",
    }
    conversion_payload = {
        "conversion_policy": {
            "heading_hierarchy_options": COMMON_HEADING_HIERARCHY.model_dump(mode="json"),
        },
        "source": {
            "source_id": "document",
            "sha256": source_sha256,
            "pdf_page_count": 1,
        },
        "sealed_release": {"manifest_sha256": sha256_file(source_manifest_path)},
    }
    conversion_identity = ContentParsingIdentity(
        run_id=f"dconv1-{canonical_json_sha256(conversion_payload)}",
        payload=conversion_payload,
    )
    models_root = tmp_path / "models"
    models_root.mkdir()
    model_inventory_path = tmp_path / "model_inventory.json"
    write_json_atomic(
        model_inventory_path,
        {
            "schema_version": "offline-test",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "models": [],
            "packages": {},
        },
    )
    model_inventory = ModelInventory.model_validate_json(model_inventory_path.read_bytes())
    _converter, options, format_option = _services().build_converter(
        models_root,
        thread_count=config.thread_count,
        heading_hierarchy_options=COMMON_HEADING_HIERARCHY,
    )
    runtime = effective_runtime_identity(config, options, format_option)
    identity_payload["runtime"] = runtime
    identity = ContentParsingIdentity(
        run_id=f"prv1-{canonical_json_sha256(identity_payload)}",
        payload=identity_payload,
    )
    return PreparedContentParsing(
        config=config,
        config_sha256=config_sha256,
        source=source,
        source_manifest_path=source_manifest_path,
        models_root=models_root,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
        model_inventory_sha256=sha256_file(model_inventory_path),
        runtime=runtime,
        conversion_identity=conversion_identity,
        identity=identity,
    )


def _successful_conversion(producer_root: Path) -> ConversionOutput:
    document_payload = {"pages": {"1": {"page_no": 1}}, "tables": []}
    write_json_atomic(producer_root / "docling" / "document.json", document_payload)
    write_jsonl(
        producer_root / "docling" / "alignment_pages.jsonl",
        [
            {
                "schema_version": "er_commons.hierarchy_alignment_page.v1",
                "page_no": 1,
                "width": 612.0,
                "height": 792.0,
                "alignment_index": [],
            }
        ],
    )
    write_jsonl(producer_root / "docling" / "heading_overlay.jsonl", [])
    write_json_atomic(
        producer_root / "asset_inventory.json",
        {
            "assets": [],
            "image_externalization": {
                "contract_version": "er_commons.docling_image_externalization.v1",
                "embedded_page_images_removed": 0,
                "embedded_picture_images_removed": 0,
                "figure_crops_preserved_as_assets": True,
                "full_page_renders_preserved": False,
            },
        },
    )
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
    converter_builds: list[Path] = []
    conversion_events: list[str] = []

    def fake_prepare(
        _data_root: Path,
        *,
        config: Any,
        config_sha256: str,
    ) -> PreparedContentParsing:
        del config, config_sha256
        return prepared

    def fake_convert(**arguments: Any) -> ConversionOutput:
        nonlocal conversions
        conversions += 1
        conversion_events.append("convert")
        return _successful_conversion(arguments["producer_root"])

    def verify_models(*_args: Any, **_kwargs: Any) -> None:
        conversion_events.append("verify_models")

    monkeypatch.setattr(application, "prepare_content_parsing", fake_prepare)
    monkeypatch.setattr(conversion_execution, "run_complete_conversion", fake_convert)
    monkeypatch.setattr(conversion_execution, "verify_model_files", verify_models)
    monkeypatch.setattr(
        derived_publication,
        "route_complete_document",
        lambda _source, _payload, _config: [_route_record()],
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    base_services = _services(converter_builds)
    build_converter = base_services.build_converter

    def build_after_verification(*args: Any, **kwargs: Any) -> tuple[Any, Any, Any]:
        conversion_events.append("build_converter")
        return build_converter(*args, **kwargs)

    services = replace(base_services, build_converter=build_after_verification)
    completion = application.run_document_parsing(
        tmp_path,
        config_path,
        services=services,
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
    producer_identity = json.loads((run_root / "records" / "producer_identity.json").read_text())
    assert set(producer_identity["identity"]["runtime"]) >= {
        "configuration_id",
        "pipeline_class",
        "backend_class",
        "effective_options",
    }
    assert conversions == 1
    assert prepared.model_inventory_path.is_file()
    assert conversion_events == ["verify_models", "build_converter", "convert"]

    reused = application.run_document_parsing(
        tmp_path,
        config_path,
        services=services,
    )

    assert reused == completion
    assert conversions == 1
    assert converter_builds == [prepared.models_root]
    assert conversion_events == ["verify_models", "build_converter", "convert"]


def test_routing_change_reuses_conversion_and_rebuilds_derived_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    conversions = 0
    model_verifications = 0
    converter_builds: list[Path] = []

    def fake_convert(**arguments: Any) -> ConversionOutput:
        nonlocal conversions
        conversions += 1
        return _successful_conversion(arguments["producer_root"])

    def verify_models(*_args: Any, **_kwargs: Any) -> None:
        nonlocal model_verifications
        model_verifications += 1

    current = prepared
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: current)
    monkeypatch.setattr(conversion_execution, "run_complete_conversion", fake_convert)
    monkeypatch.setattr(conversion_execution, "verify_model_files", verify_models)
    monkeypatch.setattr(
        derived_publication,
        "route_complete_document",
        lambda _source, _payload, _config: [_route_record()],
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    services = _services(converter_builds)
    first = application.run_document_parsing(tmp_path, config_path, services=services)
    changed_payload = {**prepared.identity.payload, "routing_policy": "changed"}
    current = replace(
        prepared,
        identity=ContentParsingIdentity(
            run_id=f"prv1-{canonical_json_sha256(changed_payload)}",
            payload=changed_payload,
        ),
    )
    second = application.run_document_parsing(tmp_path, config_path, services=services)

    assert first != second
    assert conversions == 1
    assert model_verifications == 1
    assert converter_builds == [prepared.models_root]
    second_input = json.loads((second.parents[1] / "records/conversion_input.json").read_text())
    assert second_input["conversion_id"] == prepared.conversion_identity.run_id


def test_interruption_after_conversion_publish_reuses_raw_seal_on_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    conversions = 0
    routes = 0

    def fake_convert(**arguments: Any) -> ConversionOutput:
        nonlocal conversions
        conversions += 1
        return _successful_conversion(arguments["producer_root"])

    def route_once(*_args: Any) -> list[PageRouteRecord]:
        nonlocal routes
        routes += 1
        if routes == 1:
            raise KeyboardInterrupt()
        return [_route_record()]

    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(conversion_execution, "run_complete_conversion", fake_convert)
    monkeypatch.setattr(derived_publication, "route_complete_document", route_once)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    with pytest.raises(KeyboardInterrupt):
        application.run_document_parsing(tmp_path, config_path, services=_services())
    task_root = tmp_path / prepared.config.artifact_relative_root
    [attempt] = list((task_root / "attempts").iterdir())
    attempt_record = json.loads((attempt / "attempt_record.json").read_text())
    assert attempt_record["exception_type"] == "KeyboardInterrupt"
    assert attempt_record["failed_stage"] == "route"
    assert not (attempt / "records/completion_record.json").exists()
    completion = application.run_document_parsing(tmp_path, config_path, services=_services())

    assert completion.is_file()
    assert conversions == 1
    assert routes == 2


def test_corrupt_conversion_seal_blocks_derived_reuse_before_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    routes = 0

    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(
        conversion_execution,
        "run_complete_conversion",
        lambda **arguments: _successful_conversion(arguments["producer_root"]),
    )

    def route(*_args: Any) -> list[PageRouteRecord]:
        nonlocal routes
        routes += 1
        return [_route_record()]

    monkeypatch.setattr(derived_publication, "route_complete_document", route)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")
    application.run_document_parsing(tmp_path, config_path, services=_services())
    raw_root = (
        tmp_path
        / prepared.config.artifact_relative_root
        / "docling_conversions"
        / prepared.conversion_identity.run_id
    )
    (raw_root / "documents/document/producer/docling/document.json").write_text("{}\n")

    with pytest.raises(ValueError, match="inventory_file"):
        application.run_document_parsing(tmp_path, config_path, services=_services())
    assert routes == 1


def test_resealed_incomplete_page_accounting_is_rejected_before_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    routes = 0
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(
        conversion_execution,
        "run_complete_conversion",
        lambda **arguments: _successful_conversion(arguments["producer_root"]),
    )

    def route(*_args: Any) -> list[PageRouteRecord]:
        nonlocal routes
        routes += 1
        return [_route_record()]

    monkeypatch.setattr(derived_publication, "route_complete_document", route)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")
    application.run_document_parsing(tmp_path, config_path, services=_services())
    raw_root = (
        tmp_path
        / prepared.config.artifact_relative_root
        / "docling_conversions"
        / prepared.conversion_identity.run_id
    )
    observation_path = raw_root / "documents/document/producer/docling/conversion_observation.json"
    observation = json.loads(observation_path.read_text())
    observation["converted_physical_pages"] = []
    write_json_atomic(observation_path, observation)
    inventory_path = write_inventory(raw_root)
    completion_path = raw_root / "records/completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json_atomic(completion_path, completion)

    with pytest.raises(ValueError, match="conversion_reference"):
        application.run_document_parsing(tmp_path, config_path, services=_services())
    assert routes == 1


def test_resealed_embedded_image_contract_violation_is_rejected_before_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    routes = 0
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(
        conversion_execution,
        "run_complete_conversion",
        lambda **arguments: _successful_conversion(arguments["producer_root"]),
    )

    def route(*_args: Any) -> list[PageRouteRecord]:
        nonlocal routes
        routes += 1
        return [_route_record()]

    monkeypatch.setattr(derived_publication, "route_complete_document", route)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")
    application.run_document_parsing(tmp_path, config_path, services=_services())
    raw_root = (
        tmp_path
        / prepared.config.artifact_relative_root
        / "docling_conversions"
        / prepared.conversion_identity.run_id
    )
    document_path = raw_root / "documents/document/producer/docling/document.json"
    document = json.loads(document_path.read_text())
    document["pages"]["1"]["image"] = {"uri": "data:image/png;base64,AAAA"}
    write_json_atomic(document_path, document)
    inventory_path = write_inventory(raw_root)
    completion_path = raw_root / "records/completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = sha256_file(inventory_path)
    write_json_atomic(completion_path, completion)

    with pytest.raises(ValueError, match="conversion_reference"):
        application.run_document_parsing(tmp_path, config_path, services=_services())
    assert routes == 1


def test_fake_conversion_failure_is_preserved_as_attempt_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)

    monkeypatch.setattr(
        application,
        "prepare_content_parsing",
        lambda *_args, **_kwargs: prepared,
    )

    def fail_conversion(**arguments: Any) -> ConversionOutput:
        producer_root = arguments["producer_root"]
        write_json_atomic(producer_root / "docling" / "partial.json", {"page": 1})
        raise RuntimeError("simulated conversion failure")

    monkeypatch.setattr(conversion_execution, "run_complete_conversion", fail_conversion)
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    with pytest.raises(RuntimeError, match="simulated conversion failure"):
        application.run_document_parsing(
            tmp_path,
            config_path,
            services=_services(),
        )

    task_root = tmp_path / prepared.config.artifact_relative_root
    attempts = list((task_root / "docling_conversions" / "attempts").iterdir())
    assert len(attempts) == 1
    assert not (task_root / "attempts").exists()
    attempt = json.loads((attempts[0] / "attempt_record.json").read_text())
    assert attempt["failed_stage"] == "docling_conversion"
    assert (attempts[0] / "documents/document/producer/docling/partial.json").is_file()
    assert not (attempts[0] / "records/completion_record.json").exists()
    assert not (task_root / prepared.identity.run_id).exists()


def test_model_inventory_change_after_preflight_blocks_converter_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    write_json_atomic(
        prepared.model_inventory_path,
        {
            "schema_version": "changed-after-preflight",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "models": [],
            "packages": {},
        },
    )
    converter_builds: list[Path] = []
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(
        conversion_execution,
        "run_complete_conversion",
        lambda **_kwargs: pytest.fail("conversion must not start after inventory mutation"),
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")

    with pytest.raises(ValueError, match="model inventory changed after conversion preflight"):
        application.run_document_parsing(
            tmp_path,
            config_path,
            services=_services(converter_builds),
        )

    assert converter_builds == []
    conversion_root = tmp_path / prepared.config.artifact_relative_root / "docling_conversions"
    assert not (conversion_root / prepared.conversion_identity.run_id).exists()
    [attempt] = list((conversion_root / "attempts").iterdir())
    assert not (attempt / "records/completion_record.json").exists()


def test_invalid_staged_conversion_is_retained_before_publish_and_retry_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    calls = 0

    def convert(**arguments: Any) -> ConversionOutput:
        nonlocal calls
        calls += 1
        output = _successful_conversion(arguments["producer_root"])
        if calls == 1:
            write_json_atomic(
                arguments["producer_root"] / "docling/document.json",
                {"pages": {}, "tables": []},
            )
        return output

    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(conversion_execution, "run_complete_conversion", convert)
    monkeypatch.setattr(
        derived_publication,
        "route_complete_document",
        lambda _source, _payload, _config: [_route_record()],
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")
    conversion_root = tmp_path / prepared.config.artifact_relative_root / "docling_conversions"
    final_conversion = conversion_root / prepared.conversion_identity.run_id

    with pytest.raises(ValueError, match="document_page_accounting"):
        application.run_document_parsing(tmp_path, config_path, services=_services())

    assert not final_conversion.exists()
    [attempt] = list((conversion_root / "attempts").iterdir())
    assert not (attempt / "records/completion_record.json").exists()

    completion = application.run_document_parsing(tmp_path, config_path, services=_services())

    assert completion.is_file()
    assert final_conversion.is_dir()
    assert calls == 2


def test_invalid_staged_derived_candidate_is_retained_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *_args, **_kwargs: prepared)
    monkeypatch.setattr(
        conversion_execution,
        "run_complete_conversion",
        lambda **arguments: _successful_conversion(arguments["producer_root"]),
    )
    monkeypatch.setattr(
        derived_publication,
        "route_complete_document",
        lambda _source, _payload, _config: [_route_record()],
    )
    monkeypatch.setattr(
        derived_publication,
        "verify_completed_run",
        lambda *_args: (_ for _ in ()).throw(ValueError("invalid staged derived candidate")),
    )
    config_path = tmp_path / "producer_config.json"
    config_path.write_text(prepared.config.model_dump_json(indent=2) + "\n")
    task_root = tmp_path / prepared.config.artifact_relative_root

    with pytest.raises(ValueError, match="invalid staged derived candidate"):
        application.run_document_parsing(tmp_path, config_path, services=_services())

    assert not (task_root / prepared.identity.run_id).exists()
    [attempt] = list((task_root / "attempts").iterdir())
    assert not (attempt / "records/completion_record.json").exists()
