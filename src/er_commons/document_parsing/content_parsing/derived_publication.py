"""Build and completion-seal routing and table outputs from a sealed conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import directory_bytes, sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.conversion import ConversionOutput
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.evidence import (
    verify_completed_run,
    write_inventory,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.publication import (
    ProducerWorkspace,
    publish_workspace,
    reserve_workspace,
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
from er_commons.document_parsing.content_parsing.services import ContentParsingServices
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_processing import run_complete_table_stage


@dataclass
class DerivedPublicationProgress:
    """Failure stage and workspace retained by the application shell."""

    stage: str = "preflight"
    workspace: ProducerWorkspace | None = None


@dataclass(frozen=True)
class _DerivedStages:
    """Completed conversion, routing, and table-stage outputs."""

    conversion: ConversionOutput
    routing: RoutingSummary
    tables: TableStageObservation


def build_and_publish_derived(
    *,
    data_root: Path,
    task_root: Path,
    config_path: Path,
    prepared: PreparedContentParsing,
    sealed_conversion: SealedConversion,
    services: ContentParsingServices,
    started: float,
    progress: DerivedPublicationProgress,
) -> Path:
    """Reserve, build, seal, and atomically publish all conversion consumers."""
    workspace = _reserve_and_record_preflight(
        task_root=task_root,
        config_path=config_path,
        prepared=prepared,
        services=services,
        progress=progress,
    )
    stages = _run_derived_stages(
        data_root=data_root,
        prepared=prepared,
        sealed_conversion=sealed_conversion,
        workspace=workspace,
        services=services,
        progress=progress,
    )
    return _seal_and_publish(
        prepared=prepared,
        workspace=workspace,
        stages=stages,
        services=services,
        started=started,
        progress=progress,
    )


def _reserve_and_record_preflight(
    *,
    task_root: Path,
    config_path: Path,
    prepared: PreparedContentParsing,
    services: ContentParsingServices,
    progress: DerivedPublicationProgress,
) -> ProducerWorkspace:
    """Reserve an isolated workspace and persist verified preflight evidence."""
    progress.stage = "reserve_staging"
    workspace = reserve_workspace(
        task_root,
        prepared.identity.run_id,
        token=services.new_token(),
    )
    progress.workspace = workspace
    write_preflight_records(
        workspace,
        config_path=config_path,
        config_sha256=prepared.config_sha256,
        producer_run_id=prepared.identity.run_id,
        identity=prepared.identity.payload,
        runtime=prepared.runtime,
        generated_at=services.now(),
        git_state=services.read_git_state(Path(__file__).resolve().parents[4]),
    )
    return workspace


def _run_derived_stages(
    *,
    data_root: Path,
    prepared: PreparedContentParsing,
    sealed_conversion: SealedConversion,
    workspace: ProducerWorkspace,
    services: ContentParsingServices,
    progress: DerivedPublicationProgress,
) -> _DerivedStages:
    """Consume sealed conversion evidence, then route and reconstruct tables."""
    producer_root = workspace.staging_root / "documents" / prepared.source.source_id / "producer"
    producer_root.mkdir(parents=True, exist_ok=False)
    _write_conversion_reference(data_root, prepared, sealed_conversion, workspace)
    progress.stage = "route"
    routes = route_complete_document(
        prepared.source,
        sealed_conversion.output.document_payload,
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
    return _DerivedStages(sealed_conversion.output, routing, tables)


def _write_conversion_reference(
    data_root: Path,
    prepared: PreparedContentParsing,
    sealed: SealedConversion,
    workspace: ProducerWorkspace,
) -> None:
    """Persist the exact immutable conversion seal consumed by derived stages."""
    write_json_atomic(
        workspace.records_root / "conversion_input.json",
        {
            "schema_version": "er_commons.conversion_input_reference.v1",
            **sealed.reference,
            "document_view": (
                "heading" if prepared.config.heading_hierarchy_options is not None else "base"
            ),
            "path": sealed.root.relative_to(data_root.resolve()).as_posix(),
            "completion_path": sealed.completion_path.relative_to(data_root.resolve()).as_posix(),
            "inventory_path": sealed.inventory_path.relative_to(data_root.resolve()).as_posix(),
        },
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


def _seal_and_publish(
    *,
    prepared: PreparedContentParsing,
    workspace: ProducerWorkspace,
    stages: _DerivedStages,
    services: ContentParsingServices,
    started: float,
    progress: DerivedPublicationProgress,
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
    verify_completed_run(workspace.staging_root, prepared.identity.run_id)
    return publish_workspace(workspace)
