"""Deterministic whole-document assembly and completion-last publication."""

from __future__ import annotations

import json
import tempfile
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
from er_commons.chunked_conversion.gate_b import assert_exact_page_evidence
from er_commons.chunked_conversion.gate_c import raster_from_evidence, restore_global_page
from er_commons.chunked_conversion.qualification.contracts import AggregateWorkerSpec
from er_commons.chunked_conversion.qualification.converted_range_store import (
    ConvertedRangeStore,
    VerifiedConvertedRange,
    retain_failure,
)
from er_commons.chunked_conversion.qualification.docling_adapter import (
    DoclingAdapter,
    GlobalAssembly,
)
from er_commons.chunked_conversion.qualification.gate_c_inputs import (
    SOURCE_ID,
    SOURCE_PAGE_COUNT,
    SOURCE_SHA256,
    verify_g1_inputs,
)
from er_commons.chunked_conversion.range_contract import RangePlan
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
        verified = verify_g1_inputs(spec.source_root, spec.config_path, spec.data_root)
        aggregate_identity = self._identity(verified.sealed_identity, plan)
        aggregate_id = f"dconv1-{canonical_json_sha256(aggregate_identity)}"
        final = spec.run_root / "aggregate" / aggregate_id
        if final.exists():
            deep_audit_conversion_bundle(final, aggregate_id)
            return self._publish_reference(spec.run_root, aggregate_id, final)
        attempts = spec.run_root / "aggregate_attempts"
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

    def _identity(self, sealed_identity: dict[str, Any], plan: RangePlan) -> dict[str, Any]:
        return {
            **cast(dict[str, Any], sealed_identity["identity"]),
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
                for page_no in (child.planned.core.start - 1, child.planned.core.start):
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
        if outline is None or len(pages) != SOURCE_PAGE_COUNT:
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
        producer_root = staging / "documents" / SOURCE_ID / "producer"
        docling_root = producer_root / "docling"
        docling_root.mkdir(parents=True)
        assets = _write_streamed_assets(assembly.document, children, producer_root)
        document_payload, overlay = split_heading_overlay(assembly.document.export_to_dict())
        write_json_atomic_streaming(docling_root / "document.json", document_payload)
        write_jsonl(docling_root / "heading_overlay.jsonl", overlay)
        alignment = tuple(record for child in children for record in child.alignment_pages)
        _write_alignment_records(docling_root / "alignment_pages.jsonl", alignment)
        write_json_atomic(
            producer_root / "asset_inventory.json",
            {
                "assets": assets,
                "image_externalization": {
                    "contract_version": "er_commons.docling_image_externalization.v1",
                    "embedded_page_images_removed": SOURCE_PAGE_COUNT,
                    "embedded_picture_images_removed": len(assembly.document.pictures),
                    "figure_crops_preserved_as_assets": True,
                    "full_page_renders_preserved": False,
                },
            },
        )
        observation = ConversionObservation(
            source_id=SOURCE_ID,
            raw_status="success",
            status=(
                "complete_with_warnings"
                if assembly.warnings or prepared.source.warnings
                else "complete"
            ),
            errors=[],
            captured_python_warnings=list(assembly.warnings),
            source_manifest_warnings=prepared.source.warnings,
            expected_physical_pages=list(range(1, SOURCE_PAGE_COUNT + 1)),
            converted_physical_pages=list(range(1, SOURCE_PAGE_COUNT + 1)),
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
                "global_warning_count": len(assembly.warnings),
                "streamed_page_rasters": True,
                "decoded_page_rasters_retained_during_global_pass": 0,
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
            source_id=SOURCE_ID,
            source_sha256=SOURCE_SHA256,
            source_manifest_sha256=sha256_file(prepared.source_manifest_path),
            artifact_inventory_sha256=sha256_file(inventory_path),
            completed_at_utc="2026-08-20T00:00:00Z",
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


def _write_alignment_records(path: Path, records: tuple[dict[str, Any], ...]) -> None:
    with atomic_text_writer(path) as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            stream.write("\n")


__all__ = ["AggregatePublisher"]
