"""Explicit chunked alternative to the maintained monolithic conversion entrypoint."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object, sha256_file, write_json_atomic
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime import (
    ChunkedConversionRequest,
    ensure_chunked_conversion_bundle,
)
from er_commons.chunked_conversion.runtime.contracts import PreAggregateContext
from er_commons.chunked_conversion.runtime.range_store import (
    ConvertedRangeStore,
)
from er_commons.document_parsing.content_parsing.config import (
    ContentParsingConfig,
    load_content_parsing_config,
)
from er_commons.document_parsing.content_parsing.conversion_seal import SealedConversion
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
    OrderingTableStageObservation,
    TableEvidenceDecision,
    TableEvidenceOutcome,
    build_ordering_projection,
    capture_table_stage_reference,
    classify_table_evidence,
    verify_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.preparation import (
    PreparedContentParsing,
    prepare_content_parsing,
)
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    task_artifact_root,
)
from er_commons.document_parsing.content_parsing.range_projection_reuse import (
    verified_core_page_projections,
)
from er_commons.document_parsing.content_parsing.records import (
    PageRouteRecord,
    TableStageObservation,
)
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
    validate_table_artifacts,
)
from er_commons.document_parsing.table_reconstruction.pipeline import (
    artifact_inventory as table_artifact_inventory,
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
        output = context.child_root / "records" / "ordering_projection.json"
        if output.is_file():
            _verify_reusable_projection(output, self.source)
            return output
        store = ConvertedRangeStore(context.child_root, plan)
        projections = verified_core_page_projections(store, plan, self.source.source_page_count)
        routes = route_page_projections(projections, self.config)
        root = context.child_root / "pre_aggregate"
        root.mkdir(parents=True, exist_ok=True)
        write_routing_artifacts(root / "routing", routes)
        table_root = root / "documents" / self.source.source_id / "producer" / "tables"
        if _table_stage_claims_completion(table_root, routes):
            table_observation = _reuse_validated_table_stage(table_root, routes)
        else:
            table_observation = run_complete_table_stage(
                data_root=self.data_root,
                staging_root=root,
                config=self.config,
                source=self.source,
                routes=routes,
                table_runner=self.table_runner,
                producer_run_id=context.run_id,
            )
        page_rows, table_rows = _table_evidence_rows(table_root, table_observation.status)
        decisions = _table_evidence_decisions(routes, page_rows, table_rows)
        _validate_table_suppression_coverage(decisions, table_rows)
        ordering = build_ordering_projection(projections, decisions)
        artifact = OrderingProjectionArtifact(
            table_stage_observation=OrderingTableStageObservation.model_validate(
                table_observation.model_dump(mode="python")
            ),
            table_stage=capture_table_stage_reference(
                context.child_root,
                table_root,
                table_observation,
            ),
            pages=ordering.pages,
            decisions=ordering.decisions,
        )
        write_json_atomic(output, artifact.model_dump(mode="json"))
        return output


@dataclass(frozen=True)
class PreparedChunkedRun:
    """Verified conversion and rebound producer inputs ready for derived publication."""

    config: ContentParsingConfig
    prepared: PreparedContentParsing
    producer_identity: ContentParsingIdentity
    sealed_conversion: SealedConversion
    task_root: Path


def _prepare_chunked_run(
    *,
    data_root: Path,
    config_path: Path,
    request: ChunkedConversionRequest,
    services: ContentParsingServices,
) -> PreparedChunkedRun:
    """Resolve config, seal chunked conversion, and bind the derived producer identity."""
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
            services=services,
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
    rebound = replace(
        prepared,
        conversion_identity=conversion_identity,
        identity=producer_identity,
    )
    return PreparedChunkedRun(
        config=config,
        prepared=rebound,
        producer_identity=producer_identity,
        sealed_conversion=sealed,
        task_root=task_artifact_root(data_root, config.artifact_relative_root),
    )


def _verify_reusable_projection(
    path: Path,
    source: CompleteResolvedSource,
) -> None:
    """Deep-verify plan-scoped table and ordering evidence before aggregate reuse."""
    artifact = OrderingProjectionArtifact.model_validate_json(path.read_bytes())
    expected_pages = list(range(1, source.source_page_count + 1))
    actual_pages = [page.page_no for page in artifact.pages]
    if actual_pages != expected_pages:
        raise ValueError("reused ordering projection does not cover the complete source")
    expected_table_root = (
        path.parents[1] / "pre_aggregate" / "documents" / source.source_id / "producer" / "tables"
    )
    table_root = verify_table_stage_reference(artifact.table_stage, path.parents[1])
    if table_root.resolve() != expected_table_root.resolve():
        raise ValueError("reused ordering projection table root differs")
    observation = artifact.table_stage_observation.as_producer_record()
    if observation.status == "not_applicable":
        no_table = read_json_object(table_root / "no_table_stage.json")
        if no_table != observation.model_dump(mode="json", exclude_none=True):
            raise ValueError("reused no-table observation differs")
        return
    manifest = read_json_object(table_root / "manifest.json")
    configuration_path = table_root / str(manifest.get("configuration"))
    if sha256_file(configuration_path) != manifest.get("configuration_sha256"):
        raise ValueError("reused table configuration seal differs")
    validated = validate_table_artifacts(table_root, observation.routed_pages)
    if validated != observation:
        raise ValueError("reused table-stage observation differs")
    stage = PersistedTableStage.load(table_root)
    _validate_table_suppression_coverage(list(artifact.decisions), stage.tables)


def _reuse_validated_table_stage(
    table_root: Path, routes: list[PageRouteRecord]
) -> TableStageObservation:
    """Reuse a sealed table stage when only the ordering projection changed."""
    positive_pages = [
        route.physical_pdf_page for route in routes if route.route != "no_table_route"
    ]
    if not positive_pages:
        observation = TableStageObservation.model_validate(
            read_json_object(table_root / "no_table_stage.json")
        )
        if observation.status != "not_applicable":
            raise ValueError("reused no-table stage has an invalid status")
        return observation
    manifest = read_json_object(table_root / "manifest.json")
    configuration_path = table_root / str(manifest.get("configuration"))
    if sha256_file(configuration_path) != manifest.get("configuration_sha256"):
        raise ValueError("reused table configuration seal differs")
    inventory_path = table_root / str(manifest.get("artifact_inventory"))
    expected_inventory = read_json_object(inventory_path)
    actual_inventory = table_artifact_inventory(
        table_root,
        {"artifact_inventory.json", "manifest.json"},
    )
    if actual_inventory != expected_inventory:
        raise ValueError("reused table artifact inventory differs")
    return validate_table_artifacts(table_root, positive_pages)


def _table_stage_claims_completion(table_root: Path, routes: list[PageRouteRecord]) -> bool:
    """Recognize only completion-last table markers, not a partial directory."""
    has_positive_route = any(route.route != "no_table_route" for route in routes)
    terminal = table_root / ("manifest.json" if has_positive_route else "no_table_stage.json")
    return terminal.is_file()


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


def _validate_table_suppression_coverage(
    decisions: list[TableEvidenceDecision], table_rows: list[dict[str, Any]]
) -> None:
    """Require suppression refs to be exact while allowing explicit partial evidence."""
    expected = {(int(row["physical_pdf_page"]), str(row["table_id"])) for row in table_rows}
    actual = {
        (decision.physical_pdf_page, table_ref)
        for decision in decisions
        for table_ref in decision.confirmed_table_refs
    }
    unexpected = sorted(actual - expected)
    decisions_by_page = {decision.physical_pdf_page: decision for decision in decisions}
    unexplained_missing = sorted(
        item
        for item in expected - actual
        if (
            item[0] not in decisions_by_page
            or decisions_by_page[item[0]].outcome is not TableEvidenceOutcome.PARTIAL
        )
    )
    if unexpected or unexplained_missing:
        raise ValueError(
            "validated table artifacts and ordering suppression decisions are inconsistent: "
            f"unexplained_missing={unexplained_missing[:10]!r}, "
            f"unexpected={unexpected[:10]!r}, "
            f"unexplained_missing_count={len(unexplained_missing)}, "
            f"unexpected_count={len(unexpected)}"
        )


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
    run = _prepare_chunked_run(
        data_root=data_root,
        config_path=config_path,
        request=request,
        services=active_services,
    )
    producer_identity = run.producer_identity
    final_root = run.task_root / producer_identity.run_id
    progress = DerivedPublicationProgress()
    try:
        if final_root.exists():
            completion = verify_completed_run(final_root, producer_identity.run_id)
            resolve_conversion_input(data_root, final_root / "records/conversion_input.json")
            return completion
        return build_and_publish_derived(
            data_root=data_root,
            task_root=run.task_root,
            config_path=config_path,
            prepared=run.prepared,
            sealed_conversion=run.sealed_conversion,
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
            task_root=run.task_root,
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
