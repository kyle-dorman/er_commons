"""Explicit chunked alternative to the maintained monolithic conversion entrypoint."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object, write_json_atomic
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime import (
    ChunkedConversionRequest,
    ensure_chunked_conversion_bundle,
)
from er_commons.chunked_conversion.runtime.contracts import PreAggregateContext
from er_commons.chunked_conversion.runtime.range_store import (
    ConvertedRangeStore,
    VerifiedConvertedRange,
)
from er_commons.document_parsing.content_parsing.config import (
    ContentParsingConfig,
    load_content_parsing_config,
)
from er_commons.document_parsing.content_parsing.derived_publication import (
    DerivedPublicationProgress,
    build_and_publish_derived,
)
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
)
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    TableEvidenceDecision,
    build_ordering_projection,
    classify_table_evidence,
)
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection
from er_commons.document_parsing.content_parsing.preparation import (
    PreparedContentParsing,
    prepare_content_parsing,
)
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    task_artifact_root,
)
from er_commons.document_parsing.content_parsing.records import PageRouteRecord
from er_commons.document_parsing.content_parsing.references import resolve_conversion_input
from er_commons.document_parsing.content_parsing.routing_execution import (
    route_page_projections,
    write_routing_artifacts,
)
from er_commons.document_parsing.content_parsing.services import (
    ContentParsingServices,
    TableRunner,
)
from er_commons.document_parsing.content_parsing.sources import CompleteResolvedSource
from er_commons.document_parsing.content_parsing.table_processing import (
    PersistedTableStage,
    run_complete_table_stage,
)
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreAggregateOrchestrator:
    """Route sealed page evidence, run tables, and publish one strict projection."""

    data_root: Path
    config: ContentParsingConfig
    source: CompleteResolvedSource
    table_runner: TableRunner

    def __call__(self, context: PreAggregateContext) -> Path:
        plan = RangePlan.model_validate_json(context.plan_path.read_bytes())
        if context.plan_id != plan.plan_id:
            raise ValueError("pre-aggregate context plan differs from the selected plan")
        store = ConvertedRangeStore(context.child_root, plan)
        verified = tuple(store.verify(item.range_id) for item in plan.ranges)
        projections = _core_page_projections(verified, self.source.source_page_count)
        routes = route_page_projections(projections, self.config)
        root = context.child_root / "pre_aggregate"
        root.mkdir(parents=True, exist_ok=True)
        write_routing_artifacts(root / "routing", routes)
        table_observation = run_complete_table_stage(
            data_root=self.data_root,
            staging_root=root,
            config=self.config,
            source=self.source,
            routes=routes,
            table_runner=self.table_runner,
            producer_run_id=context.run_id,
        )
        table_root = root / "documents" / self.source.source_id / "producer" / "tables"
        page_rows, table_rows = _table_evidence_rows(table_root, table_observation.status)
        decisions = _table_evidence_decisions(routes, page_rows, table_rows)
        ordering = build_ordering_projection(
            [{"page_no": item.physical_pdf_page, **item.as_record()} for item in projections],
            decisions,
        )
        artifact = OrderingProjectionArtifact(
            table_stage_observation=table_observation.model_dump(mode="json"),
            table_stage_root=table_root.as_posix(),
            pages=ordering.pages,
            decisions=ordering.decisions,
        )
        output = context.child_root / "records" / "ordering_projection.json"
        write_json_atomic(output, artifact.model_dump(mode="json"))
        return output


def _core_page_projections(
    ranges: tuple[VerifiedConvertedRange, ...], source_page_count: int
) -> list[PageEvidenceProjection]:
    """Select core-owned page evidence and require complete source coverage."""
    projections = [
        projection
        for item in ranges
        for projection in item.projections
        if item.planned.core.contains(projection.physical_pdf_page)
    ]
    expected_pages = list(range(1, source_page_count + 1))
    actual_pages = [item.physical_pdf_page for item in projections]
    if actual_pages != expected_pages:
        raise ValueError("page projections do not cover the complete source")
    return projections


def _table_evidence_rows(
    table_root: Path, status: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load required table-stage rows, allowing only the explicit no-table result."""
    if status == "not_applicable":
        return [], []
    table_stage = PersistedTableStage.load(table_root)
    return table_stage.pages, table_stage.tables


def _table_evidence_decisions(
    routes: list[PageRouteRecord],
    page_rows: list[dict[str, Any]],
    table_rows: list[dict[str, Any]],
) -> list[TableEvidenceDecision]:
    """Join persisted table outcomes to routes without treating routes as success."""
    page_rows_by_page = {int(row["physical_pdf_page"]): row for row in page_rows}
    table_rows_by_page: dict[int, list[dict[str, Any]]] = {}
    for row in table_rows:
        table_rows_by_page.setdefault(int(row["physical_pdf_page"]), []).append(row)
    return [
        classify_table_evidence(
            physical_pdf_page=route.physical_pdf_page,
            route=route.route,
            page_record=page_rows_by_page.get(route.physical_pdf_page),
            table_records=table_rows_by_page.get(route.physical_pdf_page, []),
        )
        for route in routes
    ]


def _build_pre_aggregate_projection(
    *,
    data_root: Path,
    config: ContentParsingConfig,
    prepared: PreparedContentParsing,
    services: ContentParsingServices,
) -> PreAggregateOrchestrator:
    """Bind production dependencies to the pre-aggregate orchestration seam."""
    return PreAggregateOrchestrator(
        data_root=data_root,
        config=config,
        source=prepared.source,
        table_runner=services.run_tables,
    )


def run_chunked_document_parsing(
    data_root: Path,
    config_path: Path,
    plan_path: Path,
    *,
    request: ChunkedConversionRequest,
    services: ContentParsingServices | None = None,
) -> Path:
    """Publish the normal producer bundle using an explicitly selected chunk plan."""
    active_services = services or ContentParsingServices()
    started_at = active_services.now()
    started = active_services.monotonic()
    if request.plan_path.resolve() != plan_path.resolve():
        raise ValueError("chunk request plan differs from the selected production plan")
    config, config_sha256 = load_content_parsing_config(config_path)
    prepared = prepare_content_parsing(data_root, config=config, config_sha256=config_sha256)
    project_root = Path(__file__).resolve().parents[4]
    sealed = ensure_chunked_conversion_bundle(
        request,
        project_root=project_root,
        pre_aggregate=_build_pre_aggregate_projection(
            data_root=data_root,
            config=config,
            prepared=prepared,
            services=active_services,
        ),
    )
    producer_identity = build_content_parsing_identity(
        config=config,
        source=prepared.source,
        source_manifest_path=prepared.source_manifest_path,
        source_completion_path=prepared.source_manifest_path.parent / "completion_record.json",
        table_environment=installed_table_environment(),
        project_code=code_identity(parsing_code_paths(project_root), repo_root=project_root),
        conversion_id=sealed.conversion_id,
    )
    conversion_record = read_json_object(sealed.root / "records/conversion_identity.json")
    conversion_identity = ContentParsingIdentity(
        run_id=sealed.conversion_id,
        payload=cast(dict[str, Any], conversion_record["identity"]),
    )
    prepared = replace(
        prepared,
        conversion_identity=conversion_identity,
        identity=producer_identity,
    )
    task_root = task_artifact_root(data_root, config.artifact_relative_root)
    final_root = task_root / producer_identity.run_id
    progress = DerivedPublicationProgress()
    try:
        if final_root.exists():
            completion = verify_completed_run(final_root, producer_identity.run_id)
            resolve_conversion_input(data_root, final_root / "records/conversion_input.json")
            return completion
        return build_and_publish_derived(
            data_root=data_root,
            task_root=task_root,
            config_path=config_path,
            prepared=prepared,
            sealed_conversion=sealed,
            range_run_root=request.output_root / "plans",
            range_plan_path=plan_path,
            services=active_services,
            started=started,
            progress=progress,
        )
    except BaseException as error:
        attempt = preserve_failed_attempt(
            staging_root=(
                progress.workspace.staging_root if progress.workspace is not None else None
            ),
            task_root=task_root,
            producer_run_id=producer_identity.run_id,
            failed_stage=progress.stage,
            started_at=started_at,
            finished_at=active_services.now(),
            wall_seconds=active_services.monotonic() - started,
            error=error,
            token=active_services.new_token(),
        )
        LOGGER.error("Producer attempt failed; evidence=%s", attempt)
        raise


__all__ = ["run_chunked_document_parsing"]
