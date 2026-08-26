"""Deterministic whole-document assembly and completion-last publication."""

from __future__ import annotations

import gc
import json
import os
import shutil
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import psutil  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    artifact_inventory,
    atomic_text_writer,
    canonical_json_sha256,
    sha256_file,
    write_json_atomic,
    write_json_atomic_streaming,
    write_jsonl,
)
from er_commons.chunked_conversion.page_evidence import assert_exact_page_evidence
from er_commons.chunked_conversion.page_evidence_store import raster_from_evidence
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.aggregate_memory import (
    AggregatePageSource,
    PhaseObserver,
    page_source,
    restore_ordering_page,
    suppress_confirmed_table_regions,
)
from er_commons.chunked_conversion.runtime.contracts import AggregateWorkerSpec
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.docling_adapter import (
    DoclingAdapter,
    GlobalAssembly,
)
from er_commons.chunked_conversion.runtime.inputs import verify_chunk_inputs
from er_commons.chunked_conversion.runtime.range_store import (
    ConvertedRangeStore,
    retain_failure,
)
from er_commons.document_parsing.content_parsing.conversion_seal import (
    ConversionCompletion,
    deep_audit_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingProjectionPage,
    verify_table_stage_reference,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.records import ConversionObservation
from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    BASE_LEVEL,
)
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    SCHEMA_VERSION as HEADING_OVERLAY_SCHEMA_VERSION,
)


@dataclass(frozen=True)
class AggregateRangeSummary:
    """Verified range metadata retained after heavy page evidence is released."""

    range_id: str
    core_pages: tuple[int, ...]
    alignment_pages: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    observation: dict[str, Any]


class AggregatePublisher:
    """Verify converted children, interpret globally, and seal one conversion bundle."""

    def __init__(self, adapter: DoclingAdapter | None = None) -> None:
        self.adapter = adapter or DoclingAdapter()

    def run(self, spec: AggregateWorkerSpec) -> Path:
        """Publish or deep-verify the aggregate named by the typed worker spec."""
        if not spec.ordering_projection_path.is_file():
            raise ChunkedConversionError(
                "ordering_projection_missing",
                stage="aggregate",
                path=spec.ordering_projection_path.as_posix(),
            )
        projection_sha256 = sha256_file(spec.ordering_projection_path)
        projection = OrderingProjectionArtifact.model_validate_json(
            spec.ordering_projection_path.read_bytes()
        )
        plan = RangePlan.model_validate_json(spec.plan_path.read_bytes())
        verified = verify_chunk_inputs(spec.config_path, spec.plan_path, spec.data_root)
        aggregate_identity = self._identity(
            verified.prepared.conversion_identity.payload,
            plan,
            projection_sha256=projection_sha256,
        )
        aggregate_id = f"dconv1-{canonical_json_sha256(aggregate_identity)}"
        final = spec.conversion_root / aggregate_id
        if final.exists():
            deep_audit_conversion_bundle(final, aggregate_id)
            return self._publish_reference(spec.run_root, aggregate_id, final)
        attempts = spec.conversion_root / "attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{aggregate_id}.", dir=attempts))
        try:

            def observe(phase: str) -> None:
                _record_phase(spec.run_root, phase)

            children, pages, outline, page_sources = self._verified_global_inputs(
                spec.run_root,
                plan,
                projection,
                observe=observe,
            )
            assembly = self.adapter.assemble_global_memory_bounded(
                verified.prepared,
                pages,
                outline,
                page_sources,
                data_root=spec.data_root,
                observe=observe,
            )
            self._write_bundle(
                staging,
                spec,
                plan,
                children,
                aggregate_id,
                aggregate_identity,
                verified.prepared,
                assembly,
                projection,
                page_sources,
            )
            del assembly, pages, page_sources, children
            gc.collect()
            observe("bundle_written_inputs_released")
            deep_audit_conversion_bundle(staging, aggregate_id)
            final.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(final)
            deep_audit_conversion_bundle(final, aggregate_id)
            return self._publish_reference(spec.run_root, aggregate_id, final)
        except BaseException as error:
            retain_failure(staging, error, stage="aggregate")
            raise

    def _identity(
        self,
        conversion_identity: dict[str, Any],
        plan: RangePlan,
        *,
        projection_sha256: str,
    ) -> dict[str, Any]:
        return {
            **conversion_identity,
            "conversion_invocation": {
                "mode": "restartable_chunked_page_evidence",
                "plan_id": plan.plan_id,
                "ordered_range_ids": [item.range_id for item in plan.ranges],
                "merge_identity": plan.inputs.aggregate_merge_identity,
                "global_interpretation": plan.inputs.global_interpretation_policy_identity,
                "ordering_projection_sha256": projection_sha256,
            },
        }

    def _verified_global_inputs(
        self,
        run_root: Path,
        plan: RangePlan,
        projection: OrderingProjectionArtifact,
        *,
        observe: PhaseObserver = lambda _phase: None,
    ) -> tuple[
        tuple[AggregateRangeSummary, ...],
        list[Any],
        tuple[dict[str, Any], ...],
        tuple[AggregatePageSource, ...],
    ]:
        """Deep-verify and restore each range once, releasing decoded JSON promptly."""
        children: list[AggregateRangeSummary] = []
        pages: list[Any] = []
        sources: list[AggregatePageSource] = []
        by_page = {item.page_no: item for item in projection.pages}
        outline: tuple[dict[str, Any], ...] | None = None
        previous_overlap: dict[int, Any] = {}
        store = ConvertedRangeStore(run_root, plan)
        for position, planned in enumerate(plan.ranges, start=1):
            child = store.verify(planned.range_id)
            current_pages = {page.page_no: page for page in child.pages}
            for page_no in sorted(previous_overlap.keys() & current_pages.keys()):
                assert_exact_page_evidence(
                    previous_overlap[page_no],
                    current_pages[page_no],
                    path=f"aggregate.overlap[{page_no}]",
                )
            child_by_page = current_pages
            for page_no in child.planned.core.pages:
                evidence = child_by_page[page_no]
                pages.append(
                    _ordering_page(
                        restore_ordering_page(evidence),
                        by_page.get(page_no),
                    )
                )
                sources.append(
                    page_source(
                        evidence,
                        child.root / "pages" / f"p{page_no:05d}.json",
                    )
                )
            previous_overlap = {
                page.page_no: page
                for page in child.pages
                if not child.planned.core.contains(page.page_no)
            }
            if outline is None:
                outline = child.outline
            elif child.outline != outline:
                raise ValueError(f"aggregate child outline differs: {child.planned.range_id}")
            children.append(
                AggregateRangeSummary(
                    range_id=child.planned.range_id,
                    core_pages=child.planned.core.pages,
                    alignment_pages=child.alignment_pages,
                    warnings=child.warnings,
                    observation=child.observation,
                )
            )
            del child, child_by_page, current_pages
            gc.collect()
            observe(f"verified_ordering_ranges_{position}_of_{len(plan.ranges)}")
        if outline is None or len(pages) != sum(len(item.core.pages) for item in plan.ranges):
            raise ValueError("aggregate page/outline evidence is incomplete")
        return tuple(children), pages, outline, tuple(sources)

    def _write_bundle(
        self,
        staging: Path,
        spec: AggregateWorkerSpec,
        plan: RangePlan,
        children: tuple[AggregateRangeSummary, ...],
        aggregate_id: str,
        aggregate_identity: dict[str, Any],
        prepared: PreparedContentParsing,
        assembly: GlobalAssembly,
        projection: OrderingProjectionArtifact,
        page_sources: tuple[AggregatePageSource, ...],
    ) -> None:
        """Publish aggregate artifacts in their established completion-last order."""
        source_id = prepared.source.source_id
        page_count = prepared.source.source_page_count
        producer_root = staging / "documents" / source_id / "producer"
        docling_root = producer_root / "docling"
        docling_root.mkdir(parents=True)

        assets = self._write_document_artifacts(
            staging=staging,
            source_id=source_id,
            docling_root=docling_root,
            assembly=assembly,
            page_sources=page_sources,
        )
        self._write_ordering_artifacts(
            staging=staging,
            source_id=source_id,
            docling_root=docling_root,
            plan=plan,
            projection=projection,
            projection_owner=spec.ordering_projection_path.parents[1],
            children=children,
        )
        captured_warnings, warning_evidence = collect_warning_evidence(
            children,
            assembly.warnings,
        )
        self._write_asset_inventory(
            producer_root=producer_root,
            assets=assets,
            page_count=page_count,
            picture_count=len(assembly.document.pictures),
        )
        observation = self._write_conversion_records(
            staging=staging,
            docling_root=docling_root,
            plan=plan,
            children=children,
            aggregate_id=aggregate_id,
            aggregate_identity=aggregate_identity,
            prepared=prepared,
            assembly=assembly,
            assets=assets,
            captured_warnings=captured_warnings,
            warning_evidence=warning_evidence,
        )
        self._seal_bundle(staging, aggregate_id, prepared, observation)

    def _write_document_artifacts(
        self,
        *,
        staging: Path,
        source_id: str,
        docling_root: Path,
        assembly: GlobalAssembly,
        page_sources: tuple[AggregatePageSource, ...],
    ) -> list[dict[str, Any]]:
        """Externalize figure crops and release the exported document payload."""
        assets = _write_streamed_assets(assembly.document, page_sources, staging, source_id)
        document_payload = assembly.document.export_to_dict()
        overlay = _split_heading_overlay_in_place(document_payload)
        write_json_atomic_streaming(docling_root / "document.json", document_payload)
        write_jsonl(docling_root / "heading_overlay.jsonl", overlay)
        del document_payload, overlay
        gc.collect()
        return assets

    def _write_ordering_artifacts(
        self,
        *,
        staging: Path,
        source_id: str,
        docling_root: Path,
        plan: RangePlan,
        projection: OrderingProjectionArtifact,
        projection_owner: Path,
        children: tuple[AggregateRangeSummary, ...],
    ) -> None:
        """Publish ordering metadata, canonical tables, and range alignment."""
        self._write_ordering_publication(
            staging=staging,
            source_id=source_id,
            projection=projection,
            plan=plan,
        )
        table_root = verify_table_stage_reference(projection.table_stage, projection_owner)
        published_tables = staging / "tables"
        shutil.copytree(table_root, published_tables)
        published_projection = projection.relocated_table_stage("tables")
        verify_table_stage_reference(published_projection.table_stage, staging)
        projection_path = staging / "records/ordering_projection.json"
        write_json_atomic(projection_path, published_projection.model_dump(mode="json"))
        alignment = core_alignment_records(children)
        _write_alignment_records(docling_root / "alignment_pages.jsonl", alignment)

    def _write_asset_inventory(
        self,
        *,
        producer_root: Path,
        assets: list[dict[str, Any]],
        page_count: int,
        picture_count: int,
    ) -> None:
        """Describe externalized images after document and table publication."""
        write_json_atomic(
            producer_root / "asset_inventory.json",
            {
                "assets": assets,
                "image_externalization": {
                    "contract_version": "er_commons.docling_image_externalization.v1",
                    "embedded_page_images_removed": page_count,
                    "embedded_picture_images_removed": picture_count,
                    "figure_crops_preserved_as_assets": True,
                    "full_page_renders_preserved": False,
                },
            },
        )

    def _write_conversion_records(
        self,
        *,
        staging: Path,
        docling_root: Path,
        plan: RangePlan,
        children: tuple[AggregateRangeSummary, ...],
        aggregate_id: str,
        aggregate_identity: dict[str, Any],
        prepared: PreparedContentParsing,
        assembly: GlobalAssembly,
        assets: list[dict[str, Any]],
        captured_warnings: tuple[str, ...],
        warning_evidence: dict[str, Any],
    ) -> ConversionObservation:
        """Write conversion, identity, runtime, and aggregate observations."""
        source_id = prepared.source.source_id
        page_count = prepared.source.source_page_count
        observation = ConversionObservation(
            source_id=source_id,
            raw_status="success",
            status=(
                "complete_with_warnings"
                if captured_warnings or prepared.source.warnings
                else "complete"
            ),
            errors=[],
            captured_python_warnings=list(captured_warnings),
            source_manifest_warnings=prepared.source.warnings,
            expected_physical_pages=list(range(1, page_count + 1)),
            converted_physical_pages=list(range(1, page_count + 1)),
            page_coverage_complete=True,
            asset_count=len(assets),
            wall_seconds=assembly.wall_seconds,
            cpu_seconds=assembly.cpu_seconds,
            peak_rss_bytes=assembly.peak_rss_bytes,
        )
        write_json_atomic(
            docling_root / "conversion_observation.json", observation.model_dump(mode="json")
        )
        write_json_atomic(
            staging / "records/conversion_identity.json",
            {"conversion_id": aggregate_id, "identity": aggregate_identity},
        )
        write_json_atomic(staging / "records/runtime_configuration.json", prepared.runtime)
        write_json_atomic(
            staging / "records/aggregate_observation.json",
            {
                "aggregate_id": aggregate_id,
                "plan_id": plan.plan_id,
                "child_observations": [child.observation for child in children],
                "warning_evidence": warning_evidence,
                "raster_memory_evidence": raster_memory_evidence(bool(assets)),
                "wall_seconds": assembly.wall_seconds,
                "cpu_seconds": assembly.cpu_seconds,
                "peak_worker_rss_bytes": assembly.peak_rss_bytes,
            },
        )
        return observation

    def _seal_bundle(
        self,
        staging: Path,
        aggregate_id: str,
        prepared: PreparedContentParsing,
        observation: ConversionObservation,
    ) -> None:
        """Inventory, verify, and write the completion record last."""
        source_id = prepared.source.source_id
        inventory_path = staging / "records/artifact_inventory.json"
        inventory = artifact_inventory(
            staging,
            excluded={"records/artifact_inventory.json", "records/completion_record.json"},
        )
        write_json_atomic(inventory_path, inventory)
        verify_inventory(staging, inventory)
        completion = ConversionCompletion(
            conversion_id=aggregate_id,
            status=cast(Literal["complete", "complete_with_warnings"], observation.status),
            source_id=source_id,
            source_sha256=prepared.source.source_sha256,
            source_manifest_sha256=sha256_file(prepared.source_manifest_path),
            artifact_inventory_sha256=sha256_file(inventory_path),
            completed_at_utc=datetime.now(UTC).isoformat(),
        )
        write_json_atomic(
            staging / "records/completion_record.json", completion.model_dump(mode="json")
        )

    def _write_ordering_publication(
        self,
        *,
        staging: Path,
        source_id: str,
        projection: OrderingProjectionArtifact,
        plan: RangePlan,
    ) -> None:
        """Publish ordered content, canonical tables, fallbacks, and raw references."""
        fallback_pages = [
            decision.physical_pdf_page
            for decision in projection.decisions
            if not decision.may_suppress_table_text
        ]
        write_json_atomic(
            staging / "records/ordering_publication.json",
            {
                "schema_version": "er_commons.ordering_publication.v1",
                "source_id": source_id,
                "plan_id": plan.plan_id,
                "ordered_non_table_content": (
                    f"documents/{source_id}/producer/docling/document.json"
                ),
                "canonical_tables": "tables",
                "fallback_pages": fallback_pages,
                "fallback_policy": "retain_unresolved_page_content",
                "raw_evidence": "ranges/<range_id>/pages",
                "table_evidence_decisions": [
                    decision.as_record() for decision in projection.decisions
                ],
            },
        )

    def _publish_reference(self, run_root: Path, aggregate_id: str, final: Path) -> Path:
        path = run_root / "records/aggregate_reference.json"
        write_json_atomic(path, {"conversion_id": aggregate_id, "path": final.as_posix()})
        return path


def _write_streamed_assets(
    document: Any,
    page_sources: tuple[AggregatePageSource, ...],
    conversion_root: Path,
    source_id: str,
) -> list[dict[str, Any]]:
    from docling_core.types.doc.items.picture.picture import PictureItem

    indexed: dict[int, list[tuple[int, Any]]] = {}
    for index, (item, _level) in enumerate(document.iterate_items(), start=1):
        if isinstance(item, PictureItem) and item.prov:
            indexed.setdefault(int(item.prov[0].page_no), []).append((index, item))
    assets_root = conversion_root / "documents" / source_id / "assets" / "figures"
    assets_root.mkdir(parents=True)
    assets: list[dict[str, Any]] = []
    for evidence in page_sources:
        pictures = indexed.get(evidence.page_no)
        if not pictures:
            continue
        image = raster_from_evidence(evidence)  # type: ignore[arg-type]
        for iteration_index, picture in pictures:
            crop_bbox = (
                picture.prov[0]
                .bbox.scaled(scale=evidence.image_scale)
                .to_top_left_origin(page_height=evidence.page_height * evidence.image_scale)
            )
            crop = image.crop(crop_bbox.as_tuple())
            relative = figure_asset_relative_path(source_id, iteration_index)
            output = conversion_root / relative
            crop.save(output, format="PNG")
            picture.image = None
            assets.append(
                {
                    "artifact_id": f"figure-{iteration_index:04d}",
                    "artifact_kind": "figure_crop",
                    "physical_pdf_page": evidence.page_no,
                    "raw_object_ref": str(picture.self_ref),
                    "path": relative.as_posix(),
                    "sha256": sha256_file(output),
                    "byte_size": output.stat().st_size,
                }
            )
    return assets


def _record_phase(run_root: Path, phase: str) -> None:
    """Append one durable aggregate resource checkpoint for failed-run diagnosis."""
    process = psutil.Process(os.getpid())
    record = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "phase": phase,
        "rss_bytes": process.memory_info().rss,
        "system_available_bytes": psutil.virtual_memory().available,
        "swap_used_bytes": psutil.swap_memory().used,
    }
    path = run_root / "records/aggregate_phase_observations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
        stream.write("\n")
        stream.flush()


def _split_heading_overlay_in_place(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize an already-detached Docling export without a second full copy."""
    overlay: list[dict[str, Any]] = []
    for item in _json_objects(document):
        level = item.get("level")
        pointer = item.get("self_ref")
        if not isinstance(level, int):
            continue
        if not isinstance(pointer, str):
            raise HierarchyInferenceContractError("leveled Docling object lacks self_ref")
        item["level"] = BASE_LEVEL
        if level != BASE_LEVEL:
            overlay.append(
                {
                    "schema_version": HEADING_OVERLAY_SCHEMA_VERSION,
                    "raw_self_ref": pointer,
                    "level": level,
                }
            )
    overlay.sort(key=lambda record: str(record["raw_self_ref"]))
    return overlay


def _json_objects(value: Any) -> Iterator[dict[str, Any]]:
    """Yield nested JSON objects without allocating a second document graph."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _json_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_objects(child)


def figure_asset_relative_path(source_id: str, iteration_index: int) -> Path:
    """Return the conversion-root-relative path consumed by downstream mapping."""
    return (
        Path("documents") / source_id / "assets" / "figures" / f"figure-{iteration_index:04d}.png"
    )


def core_alignment_records(
    children: tuple[AggregateRangeSummary, ...],
) -> tuple[dict[str, Any], ...]:
    """Verify duplicate overlap rows and emit every core-owned page exactly once."""
    seen: dict[int, tuple[str, dict[str, Any]]] = {}
    output: list[dict[str, Any]] = []
    for child in children:
        range_id = child.range_id
        by_page = {int(record["page_no"]): record for record in child.alignment_pages}
        for page_no, record in by_page.items():
            previous = seen.get(page_no)
            if previous is not None and previous[1] != record:
                raise ChunkedConversionError(
                    "alignment_overlap",
                    stage="aggregate",
                    path=f"alignment_pages[{page_no}]",
                    expected={"range_id": previous[0], "record": previous[1]},
                    actual={"range_id": range_id, "record": record},
                )
            seen[page_no] = (range_id, record)
        try:
            output.extend(by_page[page_no] for page_no in child.core_pages)
        except KeyError as error:
            raise ChunkedConversionError(
                "alignment_core_missing",
                stage="aggregate",
                path=f"ranges[{range_id}].alignment_pages",
                actual=int(error.args[0]),
            ) from error
    return tuple(output)


def collect_warning_evidence(
    children: tuple[AggregateRangeSummary, ...],
    global_warnings: tuple[str, ...],
) -> tuple[tuple[str, ...], dict[str, Any]]:
    """Preserve child-order warning text and record its exact source range."""
    child_rows = tuple(
        {"range_id": child.range_id, "warnings": list(child.warnings)} for child in children
    )
    child_warnings = tuple(warning for child in children for warning in child.warnings)
    combined = (*child_warnings, *global_warnings)
    return combined, {
        "child_ranges": list(child_rows),
        "global": list(global_warnings),
        "child_warning_count": len(child_warnings),
        "global_warning_count": len(global_warnings),
        "combined_warning_count": len(combined),
        "combined_order": "range-plan order, then global interpretation",
    }


def raster_memory_evidence(has_assets: bool) -> dict[str, Any]:
    """Describe the enforced path-backed raster ownership during aggregation."""
    return {
        "range_page_rasters": "verified_path_backed_png",
        "all_page_png_bytes_materialized": False,
        "global_interpretation_decoded_page_rasters": 0,
        "asset_crop_peak_decoded_page_rasters": 1 if has_assets else 0,
    }


def _write_alignment_records(path: Path, records: tuple[dict[str, Any], ...]) -> None:
    with atomic_text_writer(path) as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            stream.write("\n")


def _ordering_page(page: Any, projection: OrderingProjectionPage | None) -> Any:
    """Suppress confirmed tables, then normalize temporary ordering geometry."""
    if projection is None:
        raise ChunkedConversionError(
            "ordering_projection_page_missing",
            stage="aggregate",
            path=f"ordering_projection.pages[{page.page_no}]",
        )
    if projection.ordering_suppressed_table_refs:
        suppress_confirmed_table_regions(page, projection)
    return page


__all__ = [
    "AggregateRangeSummary",
    "AggregatePublisher",
    "collect_warning_evidence",
    "core_alignment_records",
    "figure_asset_relative_path",
    "raster_memory_evidence",
]
