"""Deterministic whole-document assembly and completion-last publication."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

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
from er_commons.chunked_conversion.page_evidence_store import (
    raster_from_evidence,
    restore_global_page,
)
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.contracts import AggregateWorkerSpec
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.docling_adapter import (
    DoclingAdapter,
    GlobalAssembly,
)
from er_commons.chunked_conversion.runtime.inputs import verify_chunk_inputs
from er_commons.chunked_conversion.runtime.range_store import (
    ConvertedRangeStore,
    VerifiedConvertedRange,
    retain_failure,
)
from er_commons.document_parsing.content_parsing.conversion_seal import (
    ConversionCompletion,
    deep_audit_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.records import ConversionObservation
from er_commons.document_parsing.heading_evidence_parsing.heading_overlay import (
    split_heading_overlay,
)


class AggregatePublisher:
    """Verify converted children, interpret globally, and seal one conversion bundle."""

    def __init__(self, adapter: DoclingAdapter | None = None) -> None:
        self.adapter = adapter or DoclingAdapter()

    def run(self, spec: AggregateWorkerSpec) -> Path:
        """Publish or deep-verify the aggregate named by the typed worker spec."""
        plan = RangePlan.model_validate_json(spec.plan_path.read_bytes())
        verified = verify_chunk_inputs(spec.config_path, spec.plan_path, spec.data_root)
        aggregate_identity = self._identity(verified.prepared.conversion_identity.payload, plan)
        aggregate_id = f"dconv1-{canonical_json_sha256(aggregate_identity)}"
        final = spec.conversion_root / aggregate_id
        if final.exists():
            deep_audit_conversion_bundle(final, aggregate_id)
            return self._publish_reference(spec.run_root, aggregate_id, final)
        attempts = spec.conversion_root / "attempts"
        attempts.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{aggregate_id}.", dir=attempts))
        try:
            children = self._verified_children(spec.run_root, plan)
            pages, outline = self._global_inputs(children)
            assembly = self.adapter.assemble_global(
                verified.prepared,
                pages,
                outline,
                data_root=spec.data_root,
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
            )
            deep_audit_conversion_bundle(staging, aggregate_id)
            final.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(final)
            deep_audit_conversion_bundle(final, aggregate_id)
            return self._publish_reference(spec.run_root, aggregate_id, final)
        except BaseException as error:
            retain_failure(staging, error, stage="aggregate")
            raise

    def _identity(self, conversion_identity: dict[str, Any], plan: RangePlan) -> dict[str, Any]:
        return {
            **conversion_identity,
            "conversion_invocation": {
                "mode": "restartable_chunked_page_evidence",
                "plan_id": plan.plan_id,
                "ordered_range_ids": [item.range_id for item in plan.ranges],
                "merge_identity": plan.inputs.aggregate_merge_identity,
                "global_interpretation": plan.inputs.global_interpretation_policy_identity,
            },
        }

    def _verified_children(
        self, run_root: Path, plan: RangePlan
    ) -> tuple[VerifiedConvertedRange, ...]:
        store = ConvertedRangeStore(run_root, plan)
        return tuple(store.verify(planned.range_id) for planned in plan.ranges)

    def _global_inputs(
        self, children: tuple[VerifiedConvertedRange, ...]
    ) -> tuple[list[Any], tuple[dict[str, Any], ...]]:
        pages: list[Any] = []
        outline: tuple[dict[str, Any], ...] | None = None
        previous: VerifiedConvertedRange | None = None
        for child in children:
            if previous is not None:
                previous_pages = {page.page_no: page for page in previous.pages}
                current_pages = {page.page_no: page for page in child.pages}
                for page_no in sorted(previous_pages.keys() & current_pages.keys()):
                    assert_exact_page_evidence(
                        previous_pages[page_no],
                        current_pages[page_no],
                        path=f"aggregate.overlap[{page_no}]",
                    )
            by_page = {page.page_no: page for page in child.pages}
            pages.extend(
                restore_global_page(by_page[page_no]) for page_no in child.planned.core.pages
            )
            previous = child
            if outline is None:
                outline = child.outline
            elif child.outline != outline:
                raise ValueError(f"aggregate child outline differs: {child.planned.range_id}")
        if outline is None or len(pages) != sum(len(item.planned.core.pages) for item in children):
            raise ValueError("aggregate page/outline evidence is incomplete")
        return pages, outline

    def _write_bundle(
        self,
        staging: Path,
        spec: AggregateWorkerSpec,
        plan: RangePlan,
        children: tuple[VerifiedConvertedRange, ...],
        aggregate_id: str,
        aggregate_identity: dict[str, Any],
        prepared: PreparedContentParsing,
        assembly: GlobalAssembly,
    ) -> None:
        source_id = prepared.source.source_id
        page_count = prepared.source.source_page_count
        producer_root = staging / "documents" / source_id / "producer"
        docling_root = producer_root / "docling"
        docling_root.mkdir(parents=True)
        assets = _write_streamed_assets(assembly.document, children, producer_root)
        document_payload, overlay = split_heading_overlay(assembly.document.export_to_dict())
        write_json_atomic_streaming(docling_root / "document.json", document_payload)
        write_jsonl(docling_root / "heading_overlay.jsonl", overlay)
        alignment = core_alignment_records(children)
        _write_alignment_records(docling_root / "alignment_pages.jsonl", alignment)
        captured_warnings, warning_evidence = collect_warning_evidence(
            children,
            assembly.warnings,
        )
        write_json_atomic(
            producer_root / "asset_inventory.json",
            {
                "assets": assets,
                "image_externalization": {
                    "contract_version": "er_commons.docling_image_externalization.v1",
                    "embedded_page_images_removed": page_count,
                    "embedded_picture_images_removed": len(assembly.document.pictures),
                    "figure_crops_preserved_as_assets": True,
                    "full_page_renders_preserved": False,
                },
            },
        )
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

    def _publish_reference(self, run_root: Path, aggregate_id: str, final: Path) -> Path:
        path = run_root / "records/aggregate_reference.json"
        write_json_atomic(path, {"conversion_id": aggregate_id, "path": final.as_posix()})
        return path


def _write_streamed_assets(
    document: Any,
    children: tuple[VerifiedConvertedRange, ...],
    producer_root: Path,
) -> list[dict[str, Any]]:
    from docling_core.types.doc.items.picture.picture import PictureItem

    indexed: dict[int, list[tuple[int, Any]]] = {}
    for index, (item, _level) in enumerate(document.iterate_items(), start=1):
        if isinstance(item, PictureItem) and item.prov:
            indexed.setdefault(int(item.prov[0].page_no), []).append((index, item))
    assets_root = producer_root.parent / "assets" / "figures"
    assets_root.mkdir(parents=True)
    assets: list[dict[str, Any]] = []
    for child in children:
        for evidence in child.pages:
            pictures = indexed.get(evidence.page_no)
            if not pictures or not child.planned.core.contains(evidence.page_no):
                continue
            image = raster_from_evidence(evidence)
            for iteration_index, picture in pictures:
                crop_bbox = (
                    picture.prov[0]
                    .bbox.scaled(scale=evidence.image_scale)
                    .to_top_left_origin(
                        page_height=float(evidence.page_payload["size"]["height"])
                        * evidence.image_scale
                    )
                )
                crop = image.crop(crop_bbox.as_tuple())
                relative = Path("assets/figures") / f"figure-{iteration_index:04d}.png"
                output = producer_root.parent / relative
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


def core_alignment_records(
    children: tuple[VerifiedConvertedRange, ...],
) -> tuple[dict[str, Any], ...]:
    """Verify duplicate overlap rows and emit every core-owned page exactly once."""
    seen: dict[int, tuple[str, dict[str, Any]]] = {}
    output: list[dict[str, Any]] = []
    for child in children:
        range_id = child.planned.range_id
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
            output.extend(by_page[page_no] for page_no in child.planned.core.pages)
        except KeyError as error:
            raise ChunkedConversionError(
                "alignment_core_missing",
                stage="aggregate",
                path=f"ranges[{range_id}].alignment_pages",
                actual=int(error.args[0]),
            ) from error
    return tuple(output)


def collect_warning_evidence(
    children: tuple[VerifiedConvertedRange, ...],
    global_warnings: tuple[str, ...],
) -> tuple[tuple[str, ...], dict[str, Any]]:
    """Preserve child-order warning text and record its exact source range."""
    child_rows = tuple(
        {"range_id": child.planned.range_id, "warnings": list(child.warnings)} for child in children
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


__all__ = [
    "AggregatePublisher",
    "collect_warning_evidence",
    "core_alignment_records",
    "raster_memory_evidence",
]
