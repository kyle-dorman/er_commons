"""Coordinate one immutable complete-document producer publication."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.artifacts import directory_bytes
from er_commons.document_extraction.producer_artifacts import (
    verify_completed_run,
    write_inventory,
)
from er_commons.document_extraction.producer_config import (
    ProducerConfig,
    load_producer_config,
)
from er_commons.document_extraction.producer_conversion import run_complete_conversion
from er_commons.document_extraction.producer_identity import (
    ProducerIdentity,
    build_producer_identity,
    code_identity,
    producer_code_paths,
    runtime_identity,
)
from er_commons.document_extraction.producer_publication import (
    ProducerWorkspace,
    preserve_failed_attempt,
    publish_workspace,
    reserve_workspace,
    task_artifact_root,
    write_preflight_records,
)
from er_commons.document_extraction.producer_records import (
    CompletionRecord,
    MachineStatus,
    ProducerSummary,
)
from er_commons.document_extraction.producer_routing import (
    route_complete_document,
    write_routing_artifacts,
)
from er_commons.document_extraction.producer_services import ProducerServices
from er_commons.document_extraction.producer_tables import run_complete_table_stage
from er_commons.document_extraction.runtime import verify_model_inventory
from er_commons.document_extraction.sources import (
    CompleteResolvedSource,
    load_sealed_manifest,
    resolve_complete_source,
)
from er_commons.source_freeze import sha256_file, write_json_atomic
from er_commons.table_extraction.pipeline import installed_table_environment

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreparedProducer:
    """Verified inputs and constructed runtime required before staging begins."""

    config: ProducerConfig
    config_sha256: str
    source: CompleteResolvedSource
    source_manifest_path: Path
    converter: Any
    runtime: dict[str, Any]
    identity: ProducerIdentity


def prepare_producer(
    data_root: Path,
    *,
    config: ProducerConfig,
    config_sha256: str,
    services: ProducerServices,
) -> PreparedProducer:
    """Verify source/models/runtime and derive the code-bound producer identity."""
    manifest = load_sealed_manifest(data_root, config)
    source = resolve_complete_source(data_root, config.source, manifest)
    source_manifest_path = (data_root / config.source_manifest_relative_path).resolve()
    source_completion_path = source_manifest_path.parent / "completion_record.json"
    model_inventory_path = (data_root / config.model_inventory_relative_path).resolve()
    model_inventory, models_root = verify_model_inventory(data_root, model_inventory_path)
    converter, options, format_option = services.build_converter(
        models_root,
        thread_count=config.thread_count,
    )
    if options.document_timeout != config.document_timeout_seconds:
        raise ValueError("effective Docling timeout differs from producer config")

    runtime = runtime_identity(config, options, format_option)
    repo_root = Path(__file__).resolve().parents[3]
    project_code = code_identity(
        producer_code_paths(repo_root),
        repo_root=repo_root,
    )
    identity = build_producer_identity(
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
    return PreparedProducer(
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


def run_complete_document_producer(
    data_root: Path,
    config_path: Path,
    *,
    services: ProducerServices | None = None,
) -> Path:
    """Run or checksum-verify one complete immutable producer publication."""
    active_services = services or ProducerServices()
    started_at = active_services.now()
    started = active_services.monotonic()
    config, _digest = load_producer_config(config_path)
    task_root = task_artifact_root(data_root, config.artifact_relative_root)
    producer_run_id: str | None = None
    workspace: ProducerWorkspace | None = None
    stage = "preflight"

    try:
        prepared = prepare_producer(
            data_root,
            config=config,
            config_sha256=_digest,
            services=active_services,
        )
        producer_run_id = prepared.identity.run_id
        final_root = task_root / producer_run_id
        if final_root.exists():
            return verify_completed_run(final_root, producer_run_id)

        stage = "reserve_staging"
        workspace = reserve_workspace(
            task_root,
            producer_run_id,
            token=active_services.new_token(),
        )
        repo_root = Path(__file__).resolve().parents[3]
        write_preflight_records(
            workspace,
            config_path=config_path,
            config_sha256=prepared.config_sha256,
            producer_run_id=producer_run_id,
            identity=prepared.identity.payload,
            runtime=prepared.runtime,
            generated_at=active_services.now(),
            git_state=active_services.read_git_state(repo_root),
        )

        stage = "convert"
        producer_root = (
            workspace.staging_root / "documents" / prepared.source.source_id / "producer"
        )
        conversion = run_complete_conversion(
            converter=prepared.converter,
            source=prepared.source,
            producer_root=producer_root,
            log_path=workspace.staging_root / "logs" / "producer.log",
            services=active_services,
        )

        stage = "route"
        routes = route_complete_document(
            prepared.source,
            conversion.document_payload,
            prepared.config,
        )
        routing = write_routing_artifacts(producer_root / "routing", routes)

        stage = "tables"
        tables = run_complete_table_stage(
            data_root=data_root,
            staging_root=workspace.staging_root,
            config=prepared.config,
            source=prepared.source,
            routes=routes,
            table_runner=active_services.run_tables,
            producer_run_id=producer_run_id,
        )
        write_json_atomic(
            workspace.records_root / "table_stage_observation.json",
            tables.model_dump(mode="json", exclude_none=True),
        )

        stage = "reconcile"
        warnings_out = _producer_warnings(
            prepared.source,
            conversion.observation.captured_python_warnings,
            tables.zero_table_pages,
        )
        producer_status: MachineStatus = "complete_with_warnings" if warnings_out else "complete"
        summary = ProducerSummary(
            producer_run_id=producer_run_id,
            producer_status=producer_status,
            publication_status="complete",
            source_id=prepared.source.source_id,
            physical_page_count=prepared.source.source_page_count,
            routing=routing.route_counts,
            tables=tables,
            asset_count=len(conversion.assets),
            warnings=warnings_out,
            error_count=0,
            wall_seconds=active_services.monotonic() - started,
            conversion_cpu_seconds=conversion.observation.cpu_seconds,
            peak_rss_bytes=conversion.observation.peak_rss_bytes,
            output_bytes_before_inventory=directory_bytes(workspace.staging_root),
        )
        write_json_atomic(
            workspace.records_root / "producer_summary.json",
            summary.model_dump(mode="json", exclude_none=True),
        )
        inventory_path = write_inventory(workspace.staging_root)

        stage = "publish"
        completion = CompletionRecord(
            schema_version="1.0.0",
            producer_run_id=producer_run_id,
            producer_status=producer_status,
            publication_status="complete",
            source_id=prepared.source.source_id,
            source_sha256=prepared.source.source_sha256,
            source_manifest_sha256=sha256_file(prepared.source_manifest_path),
            artifact_inventory="records/artifact_inventory.json",
            artifact_inventory_sha256=sha256_file(inventory_path),
            completed_at_utc=active_services.now().isoformat(),
        )
        write_json_atomic(
            workspace.records_root / "completion_record.json",
            completion.model_dump(mode="json"),
        )
        return publish_workspace(workspace)
    except BaseException as error:
        attempt = preserve_failed_attempt(
            staging_root=workspace.staging_root if workspace is not None else None,
            task_root=task_root,
            producer_run_id=producer_run_id,
            failed_stage=stage,
            started_at=started_at,
            finished_at=active_services.now(),
            wall_seconds=active_services.monotonic() - started,
            error=error,
            token=active_services.new_token(),
        )
        LOGGER.error("Producer attempt failed; evidence=%s", attempt)
        raise
