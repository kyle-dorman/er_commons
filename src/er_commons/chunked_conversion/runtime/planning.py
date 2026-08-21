"""Deterministic source-neutral fallback planning from prepared source facts."""

from __future__ import annotations

from er_commons.artifact_io import canonical_json_sha256
from er_commons.chunked_conversion.range_contract import (
    OverlapOwner,
    OverlapPolicy,
    PageInterval,
    RangeDefinition,
    RangePlan,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
)
from er_commons.chunked_conversion.runtime.inputs import RuntimeCodeIdentity
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing


def build_fixed_size_plan(
    prepared: PreparedContentParsing,
    code: RuntimeCodeIdentity,
    *,
    target_range_size: int = 225,
    hard_maximum: int = 275,
    overlap_pages: int = 1,
) -> RangePlan:
    """Build contiguous fixed-size cores without inspecting source PDF content."""
    if not 1 <= target_range_size <= hard_maximum:
        raise ValueError("target range size must be within the hard maximum")
    if overlap_pages not in {0, 1}:
        raise ValueError("the maintained fallback supports zero or one overlap page")
    page_count = prepared.source.source_page_count
    cores = tuple(
        PageInterval(start=start, end=min(start + target_range_size - 1, page_count))
        for start in range(1, page_count + 1, target_range_size)
    )
    definitions = tuple(_definition(core, cores, page_count, overlap_pages) for core in cores)
    conversion = prepared.conversion_identity.payload
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id=prepared.source.source_id,
                sha256=prepared.source.source_sha256,
                byte_size=prepared.source.source_byte_size,
                physical_page_count=page_count,
            ),
            sealed_source_release_identity=canonical_json_sha256(conversion["sealed_release"]),
            converter_identity=prepared.conversion_identity.run_id,
            package_identity=canonical_json_sha256(conversion["package_versions"]),
            model_identity=canonical_json_sha256(conversion["model_inventory"]),
            adapter_identity=code.page_evidence,
            page_evidence_contract_identity=f"compact_typed_page_evidence:{code.page_evidence}",
            range_conversion_identity=code.range_conversion,
            range_planner_identity=code.planning,
            aggregate_merge_identity=code.aggregate,
            target_range_size=target_range_size,
            hard_maximum=hard_maximum,
            overlap_policy=OverlapPolicy(
                max_left_pages=overlap_pages,
                max_right_pages=overlap_pages,
            ),
            ranges=definitions,
            aggregate_output_schema_identity="docling_conversion_bundle.v1",
            global_interpretation_policy_identity="docling_reading_order_heading_once.v1",
        )
    )


def _definition(
    core: PageInterval,
    cores: tuple[PageInterval, ...],
    page_count: int,
    overlap_pages: int,
) -> RangeDefinition:
    read = PageInterval(
        start=max(1, core.start - overlap_pages),
        end=min(page_count, core.end + overlap_pages),
    )
    owners = tuple(
        OverlapOwner(page=page, owner_core=next(item for item in cores if item.contains(page)))
        for page in read.pages
        if not core.contains(page)
    )
    return RangeDefinition(core=core, read=read, overlap_owners=owners)


__all__ = ["build_fixed_size_plan"]
