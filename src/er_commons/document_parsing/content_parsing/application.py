"""Coordinate one immutable complete-document producer publication."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import directory_bytes, sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.config import (
    ContentParsingConfig,
    load_content_parsing_config,
)
from er_commons.document_parsing.content_parsing.conversion import (
    ConversionOutput,
    run_complete_conversion,
)
from er_commons.document_parsing.content_parsing.evidence import (
    verify_completed_run,
    write_inventory,
)
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
    runtime_identity,
)
from er_commons.document_parsing.content_parsing.publication import (
    ProducerWorkspace,
    preserve_failed_attempt,
    publish_workspace,
    reserve_workspace,
    task_artifact_root,
    write_preflight_records,
)
from er_commons.document_parsing.content_parsing.records import (
    CompletionRecord,
    MachineStatus,
    ProducerSummary,
    RoutingSummary,
    TableStageObservation,
)
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_complete_document,
    write_routing_artifacts,
)
from er_commons.document_parsing.content_parsing.runtime import verify_model_inventory
from er_commons.document_parsing.content_parsing.services import ContentParsingServices
from er_commons.document_parsing.content_parsing.sources import (
    CompleteResolvedSource,
    load_sealed_manifest,
    resolve_complete_source,
)
from er_commons.document_parsing.content_parsing.table_processing import run_complete_table_stage
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedContentParsing:
    """Verified inputs and constructed runtime required before staging begins."""

    config: ContentParsingConfig
    config_sha256: str
    source: CompleteResolvedSource
    source_manifest_path: Path
    converter: Any
    runtime: dict[str, Any]
    identity: ContentParsingIdentity


@dataclass
class _RunProgress:
    """Mutable failure context for the current publication attempt."""

    stage: str = "preflight"


@dataclass(frozen=True)
class _ContentStages:
    """Completed conversion, routing, and table-stage outputs."""

    conversion: ConversionOutput
    routing: RoutingSummary
    tables: TableStageObservation


def prepare_content_parsing(
    data_root: Path,
    *,
    config: ContentParsingConfig,
    config_sha256: str,
    services: ContentParsingServices,
) -> PreparedContentParsing:
    """Verify source/models/runtime and derive the code-bound producer identity."""
    manifest = load_sealed_manifest(data_root, config)
    source = resolve_complete_source(data_root, config.source, manifest)
    source_manifest_path = (data_root / config.source_manifest_relative_path).resolve()
    source_completion_path = source_manifest_path.parent / "completion_record.json"
    model_inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    model_inventory, models_root = verify_model_inventory(data_root, model_inventory_path)
    converter_kwargs: dict[str, Any] = {"thread_count": config.thread_count}
    if config.heading_hierarchy_options is not None:
        converter_kwargs["heading_hierarchy_options"] = config.heading_hierarchy_options
    converter, options, format_option = services.build_converter(models_root, **converter_kwargs)
    if options.document_timeout != config.document_timeout_seconds:
        raise ValueError("effective Docling timeout differs from producer config")
    effective_hierarchy = options.heading_hierarchy_options.model_dump(mode="json")
    expected_hierarchy = (
        config.heading_hierarchy_options.model_dump(mode="json")
        if config.heading_hierarchy_options is not None
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
    if effective_hierarchy != expected_hierarchy:
        raise ValueError("effective Docling hierarchy options differ from producer config")

    runtime = runtime_identity(config, options, format_option)
    repo_root = Path(__file__).resolve().parents[4]
    project_code = code_identity(
        parsing_code_paths(repo_root),
        repo_root=repo_root,
    )
    identity = build_content_parsing_identity(
        config=config,
        source=source,
        source_manifest_path=source_manifest_path,
        source_completion_path=source_completion_path,
        model_inventory_path=model_inventory_path,
        model_inventory=model_inventory,
        runtime=runtime,
        table_environment=installed_table_environment(),
        project_code=project_code,
    )
    return PreparedContentParsing(
        config=config,
        config_sha256=config_sha256,
        source=source,
        source_manifest_path=source_manifest_path,
        converter=converter,
        runtime=runtime,
        identity=identity,
    )


def _producer_warnings(
    source: CompleteResolvedSource,
    python_warnings: list[str],
    zero_table_pages: list[int],
) -> list[str]:
    warnings_out = [*source.warnings, *python_warnings]
    if zero_table_pages:
        warnings_out.append(f"routed pages with zero reconstructed tables: {zero_table_pages}")
    return warnings_out


def _reserve_and_record_preflight(
    task_root: Path,
    config_path: Path,
    prepared: PreparedContentParsing,
    services: ContentParsingServices,
    progress: _RunProgress,
) -> ProducerWorkspace:
    """Reserve an isolated workspace and persist verified preflight evidence."""
    progress.stage = "reserve_staging"
    workspace = reserve_workspace(
        task_root,
        prepared.identity.run_id,
        token=services.new_token(),
    )
    repo_root = Path(__file__).resolve().parents[4]
    write_preflight_records(
        workspace,
        config_path=config_path,
        config_sha256=prepared.config_sha256,
        producer_run_id=prepared.identity.run_id,
        identity=prepared.identity.payload,
        runtime=prepared.runtime,
        generated_at=services.now(),
        git_state=services.read_git_state(repo_root),
    )
    return workspace


def _run_content_stages(
    data_root: Path,
    prepared: PreparedContentParsing,
    workspace: ProducerWorkspace,
    services: ContentParsingServices,
    progress: _RunProgress,
) -> _ContentStages:
    """Convert, route, and reconstruct tables in their persisted order."""
    producer_root = workspace.staging_root / "documents" / prepared.source.source_id / "producer"
    progress.stage = "convert"
    conversion = run_complete_conversion(
        converter=prepared.converter,
        source=prepared.source,
        producer_root=producer_root,
        log_path=workspace.staging_root / "logs" / "producer.log",
        services=services,
    )
    progress.stage = "route"
    routes = route_complete_document(
        prepared.source,
        conversion.document_payload,
        prepared.config,
    )
    routing = write_routing_artifacts(producer_root / "routing", routes)
    progress.stage = "tables"
    tables = run_complete_table_stage(
        data_root=data_root,
        staging_root=workspace.staging_root,
        config=prepared.config,
        source=prepared.source,
        routes=routes,
        table_runner=services.run_tables,
        producer_run_id=prepared.identity.run_id,
    )
    write_json_atomic(
        workspace.records_root / "table_stage_observation.json",
        tables.model_dump(mode="json", exclude_none=True),
    )
    return _ContentStages(conversion=conversion, routing=routing, tables=tables)


def _seal_and_publish(
    prepared: PreparedContentParsing,
    workspace: ProducerWorkspace,
    stages: _ContentStages,
    services: ContentParsingServices,
    started: float,
    progress: _RunProgress,
) -> Path:
    """Write summary and completion last, then atomically publish the workspace."""
    progress.stage = "reconcile"
    warnings_out = _producer_warnings(
        prepared.source,
        stages.conversion.observation.captured_python_warnings,
        stages.tables.zero_table_pages,
    )
    producer_status: MachineStatus = "complete_with_warnings" if warnings_out else "complete"
    summary = ProducerSummary(
        producer_run_id=prepared.identity.run_id,
        producer_status=producer_status,
        publication_status="complete",
        source_id=prepared.source.source_id,
        physical_page_count=prepared.source.source_page_count,
        routing=stages.routing.route_counts,
        tables=stages.tables,
        asset_count=len(stages.conversion.assets),
        warnings=warnings_out,
        error_count=0,
        wall_seconds=services.monotonic() - started,
        conversion_cpu_seconds=stages.conversion.observation.cpu_seconds,
        peak_rss_bytes=stages.conversion.observation.peak_rss_bytes,
        output_bytes_before_inventory=directory_bytes(workspace.staging_root),
    )
    write_json_atomic(
        workspace.records_root / "producer_summary.json",
        summary.model_dump(mode="json", exclude_none=True),
    )
    inventory_path = write_inventory(workspace.staging_root)
    progress.stage = "publish"
    completion = CompletionRecord(
        schema_version="1.0.0",
        producer_run_id=prepared.identity.run_id,
        producer_status=producer_status,
        publication_status="complete",
        source_id=prepared.source.source_id,
        source_sha256=prepared.source.source_sha256,
        source_manifest_sha256=sha256_file(prepared.source_manifest_path),
        artifact_inventory="records/artifact_inventory.json",
        artifact_inventory_sha256=sha256_file(inventory_path),
        completed_at_utc=services.now().isoformat(),
    )
    write_json_atomic(
        workspace.records_root / "completion_record.json",
        completion.model_dump(mode="json"),
    )
    return publish_workspace(workspace)


def run_document_parsing(
    data_root: Path,
    config_path: Path,
    *,
    services: ContentParsingServices | None = None,
    artifact_root_override: Path | None = None,
) -> Path:
    """Run or checksum-verify one complete immutable producer publication."""
    active_services = services or ContentParsingServices()
    started_at = active_services.now()
    started = active_services.monotonic()
    config, _digest = load_content_parsing_config(config_path)
    task_root = task_artifact_root(
        data_root,
        artifact_root_override
        if artifact_root_override is not None
        else config.artifact_relative_root,
    )
    producer_run_id: str | None = None
    workspace: ProducerWorkspace | None = None
    progress = _RunProgress()

    try:
        prepared = prepare_content_parsing(
            data_root,
            config=config,
            config_sha256=_digest,
            services=active_services,
        )
        producer_run_id = prepared.identity.run_id
        final_root = task_root / producer_run_id
        if final_root.exists():
            return verify_completed_run(final_root, producer_run_id)

        workspace = _reserve_and_record_preflight(
            task_root, config_path, prepared, active_services, progress
        )
        stages = _run_content_stages(data_root, prepared, workspace, active_services, progress)
        return _seal_and_publish(prepared, workspace, stages, active_services, started, progress)
    except BaseException as error:
        attempt = preserve_failed_attempt(
            staging_root=workspace.staging_root if workspace is not None else None,
            task_root=task_root,
            producer_run_id=producer_run_id,
            failed_stage=progress.stage,
            started_at=started_at,
            finished_at=active_services.now(),
            wall_seconds=active_services.monotonic() - started,
            error=error,
            token=active_services.new_token(),
        )
        LOGGER.error("Producer attempt failed; evidence=%s", attempt)
        raise
