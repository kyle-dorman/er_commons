"""Appendix G1 qualification profile and document-driven range plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

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


@dataclass(frozen=True)
class BoundaryEvidence:
    """One reviewed source-authored divider that begins a new core range."""

    next_page: int
    outline_title: str
    previous_page_evidence: str
    next_page_evidence: str = "divider"


@dataclass(frozen=True)
class G1CodeIdentity:
    """Behavior-owned code digests with separate child and aggregate invalidation."""

    page_evidence: str
    range_conversion: str
    planning: str
    aggregate: str


G1_BOUNDARIES = (
    BoundaryEvidence(233, "Building Construction Blocks A8 and A9", "report page 67/67"),
    BoundaryEvidence(448, "Building Construction Blocks B1 through B4", "report page 76/76"),
    BoundaryEvidence(670, "Building Construction Blocks B10 and B11", "report page 76/76"),
    BoundaryEvidence(888, "Building Construction Blocks C4 and C5 alternate", "report end"),
    BoundaryEvidence(1108, "Open Spaces", "report page 72/72"),
    BoundaryEvidence(1333, "Earthwork", "report end"),
    BoundaryEvidence(1591, "Area D, OS-E, and G Earthwork West", "report end"),
    BoundaryEvidence(1812, "Middle School", "report page 39/39"),
    BoundaryEvidence(1958, "Relocated Fire Station", "report end"),
    BoundaryEvidence(2147, "Substation", "report page 76/76"),
    BoundaryEvidence(2233, "Water Recycling Facility", "report page 85/85"),
)


def g1_core_intervals(page_count: int = 2488) -> tuple[PageInterval, ...]:
    """Return the twelve reviewed G1 ranges in canonical physical-page order."""
    starts = (1, *(boundary.next_page for boundary in G1_BOUNDARIES))
    ends = (*(page - 1 for page in starts[1:]), page_count)
    return tuple(
        PageInterval(start=start, end=end) for start, end in zip(starts, ends, strict=True)
    )


def build_g1_plan(
    sealed_identity: dict[str, Any], code: G1CodeIdentity, *, page_count: int = 2488
) -> RangePlan:
    """Build the G1 plan while keeping CLI/report code outside semantic identities."""
    identity = cast(dict[str, Any], sealed_identity["identity"])
    source = cast(dict[str, Any], identity["source"])
    cores = g1_core_intervals(page_count)
    definitions = tuple(_range_definition(core, cores, page_count) for core in cores)
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id=str(source["source_id"]),
                sha256=str(source["sha256"]),
                byte_size=int(source["byte_size"]),
                physical_page_count=page_count,
            ),
            sealed_source_release_identity=canonical_json_sha256(identity["sealed_release"]),
            converter_identity=str(sealed_identity["conversion_id"]),
            package_identity=canonical_json_sha256(identity["package_versions"]),
            model_identity=canonical_json_sha256(identity["model_inventory"]),
            adapter_identity=code.page_evidence,
            page_evidence_contract_identity=f"compact_typed_page_evidence:{code.page_evidence}",
            range_conversion_identity=code.range_conversion,
            range_planner_identity=code.planning,
            aggregate_merge_identity=code.aggregate,
            target_range_size=225,
            hard_maximum=275,
            overlap_policy=OverlapPolicy(max_left_pages=1, max_right_pages=1),
            ranges=definitions,
            aggregate_output_schema_identity="accepted_g1_stable_outputs.v1",
            global_interpretation_policy_identity="docling_reading_order_heading_once.v1",
        )
    )


def boundary_evidence_record() -> dict[str, Any]:
    """Serialize the reviewed boundary rationale independently of execution state."""
    return {
        "schema_version": "er_commons.task03h2_gate_c_boundaries.v1",
        "target_core_pages": 225,
        "hard_maximum_core_pages": 275,
        "overlap_pages_per_available_side": 1,
        "boundaries": [
            {
                **boundary.__dict__,
                "cut_after_page": boundary.next_page - 1,
                "classification": "source_authored_divider",
            }
            for boundary in G1_BOUNDARIES
        ],
        "core_ranges": [core.model_dump(mode="json") for core in g1_core_intervals()],
        "visual_review": (
            "passed: every prior page is a terminal report page and every next page "
            "is a source-authored report divider"
        ),
        "g2_inspected": False,
    }


def _range_definition(
    core: PageInterval, cores: tuple[PageInterval, ...], page_count: int
) -> RangeDefinition:
    read = PageInterval(start=max(1, core.start - 1), end=min(page_count, core.end + 1))
    owners = tuple(
        OverlapOwner(page=page, owner_core=next(owner for owner in cores if owner.contains(page)))
        for page in read.pages
        if not core.contains(page)
    )
    return RangeDefinition(core=core, read=read, overlap_owners=owners)
