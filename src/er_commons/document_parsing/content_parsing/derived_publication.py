"""Build and completion-seal routing and table outputs from a sealed conversion."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import directory_bytes, sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.accepted_aggregate import (
    reuse_accepted_aggregate_tables,
)
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
from er_commons.document_parsing.content_parsing.derived_publication_support import (
    DerivedPublicationProgress as DerivedPublicationProgress,
)
from er_commons.document_parsing.content_parsing.derived_publication_support import (
    DerivedStages,
    producer_warnings,
    write_conversion_reference,
)
from er_commons.document_parsing.content_parsing.derived_route_reuse import (
    routes_for_conversion,
)
from er_commons.document_parsing.content_parsing.derived_table_reuse import (
    reuse_aggregate_table_stage,
)
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
)
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_complete_document,
    write_routing_artifacts,
)
from er_commons.document_parsing.content_parsing.services import ContentParsingServices
from er_commons.document_parsing.content_parsing.table_processing import run_complete_table_stage


def build_and_publish_derived(
    *,
    data_root: Path,
    task_root: Path,
    config_path: Path,
    prepared: PreparedContentParsing,
    sealed_conversion: SealedConversion,
    range_run_root: Path | None = None,
    range_plan_path: Path | None = None,
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
        range_run_root=range_run_root,
        range_plan_path=range_plan_path,
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
    range_run_root: Path | None,
    range_plan_path: Path | None,
    workspace: ProducerWorkspace,
    services: ContentParsingServices,
    progress: DerivedPublicationProgress,
) -> DerivedStages:
    """Consume sealed conversion evidence, then route and reconstruct tables."""
    producer_root = workspace.staging_root / "documents" / prepared.source.source_id / "producer"
    producer_root.mkdir(parents=True, exist_ok=False)
    write_conversion_reference(data_root, prepared, sealed_conversion, workspace)
    progress.stage = "route"
    routes, reuse_aggregate_tables, accepted_inventory = routes_for_conversion(
        prepared,
        sealed_conversion,
        range_run_root,
        range_plan_path,
        route_document=route_complete_document,
    )
    routing = write_routing_artifacts(producer_root / "routing", routes)
    progress.stage = "tables"
    inherited_files = None
    if accepted_inventory is not None:
        tables, inherited_files = reuse_accepted_aggregate_tables(
            sealed_conversion,
            prepared,
            routes,
            producer_root / "tables",
            accepted_inventory,
            inherited_files=progress.inherited_files,
        )
    elif reuse_aggregate_tables:
        tables = reuse_aggregate_table_stage(
            sealed_conversion,
            producer_root / "tables",
        )
    else:
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
    return DerivedStages(sealed_conversion.output, routing, tables, inherited_files)


def _seal_and_publish(
    *,
    prepared: PreparedContentParsing,
    workspace: ProducerWorkspace,
    stages: DerivedStages,
    services: ContentParsingServices,
    started: float,
    progress: DerivedPublicationProgress,
) -> Path:
    """Write summary and completion last, then atomically publish the workspace."""
    progress.stage = "reconcile"
    warnings_out = producer_warnings(
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
    inventory_path = (
        write_inventory(workspace.staging_root, inherited_files=stages.inherited_files)
        if stages.inherited_files is not None
        else write_inventory(workspace.staging_root)
    )
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
    return (
        publish_workspace(workspace, inherited_files=set(stages.inherited_files))
        if stages.inherited_files is not None
        else publish_workspace(workspace)
    )
