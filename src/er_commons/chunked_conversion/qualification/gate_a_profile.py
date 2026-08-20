"""Source-free Gate A profile and narrowly owned identity recipes."""

from __future__ import annotations

from pathlib import Path
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
from er_commons.document_parsing.content_parsing.identity import code_identity

SOURCE_CONVERSION_ID = "dconv1-97a8d4048839d9ba26c78151d0446e1c1bbef9848183f1ce9b9140c92e4c3f68"
SEAM_CUTS = (13, 24, 52, 59, 70, 86, 2190)
RANGE_ENDS = (*SEAM_CUTS, 2488)


def build_gate_a_plan(identity: dict[str, Any], *, project_root: Path) -> RangePlan:
    """Build the source-free plan without coupling identity to its CLI shell."""
    source = cast(dict[str, Any], identity["source"])
    cores = _core_intervals()
    definitions = tuple(_range_definition(core, cores) for core in cores)
    conversion_policy = identity["conversion_policy"]
    chunk_root = project_root / "src/er_commons/chunked_conversion"
    qualification = chunk_root / "qualification"
    planner = code_identity(
        [chunk_root / "range_contract.py", qualification / "gate_a_profile.py"],
        repo_root=project_root,
    )["sha256"]
    child = code_identity(
        [
            chunk_root / "range_bundle.py",
            chunk_root / "range_graph.py",
            chunk_root / "range_recomposition.py",
            chunk_root / "recomposition_records.py",
            chunk_root / "recomposition_diagnostics.py",
            chunk_root / "range_partitioning.py",
            chunk_root / "range_shard_validation.py",
            qualification / "gate_a_projections.py",
        ],
        repo_root=project_root,
    )["sha256"]
    aggregate = code_identity(
        [
            chunk_root / "document_reconstruction.py",
            qualification / "gate_a_application.py",
            qualification / "gate_a_inputs.py",
            qualification / "gate_a_proofs.py",
            qualification / "gate_a_publication.py",
            qualification / "gate_a_report.py",
        ],
        repo_root=project_root,
    )["sha256"]
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id=str(source["source_id"]),
                sha256=str(source["sha256"]),
                byte_size=int(source["byte_size"]),
                physical_page_count=int(source["pdf_page_count"]),
            ),
            sealed_source_release_identity=canonical_json_sha256(identity["sealed_release"]),
            converter_identity=canonical_json_sha256(conversion_policy),
            package_identity=canonical_json_sha256(identity["package_versions"]),
            model_identity=canonical_json_sha256(identity["model_inventory"]),
            adapter_identity=code_identity([chunk_root / "range_graph.py"], repo_root=project_root)[
                "sha256"
            ],
            page_evidence_contract_identity="er_commons.docling_page_evidence.v1",
            range_conversion_identity=child,
            range_planner_identity=planner,
            aggregate_merge_identity=aggregate,
            target_range_size=350,
            hard_maximum=2104,
            overlap_policy=OverlapPolicy(max_left_pages=1, max_right_pages=1),
            ranges=definitions,
            aggregate_output_schema_identity="accepted_g1_stable_outputs.v1",
            global_interpretation_policy_identity="preserve_materialized_global_semantics.v1",
        )
    )


def aggregate_id(plan: RangePlan) -> str:
    """Derive aggregate identity from ordered children and aggregate policy only."""
    digest = canonical_json_sha256(
        {
            "schema_version": "er_commons.docling_range_aggregate_identity.v1",
            "plan_id": plan.plan_id,
            "range_ids": [item.range_id for item in plan.ranges],
            "aggregate_merge_identity": plan.inputs.aggregate_merge_identity,
            "aggregate_output_schema_identity": plan.inputs.aggregate_output_schema_identity,
            "global_interpretation_policy_identity": (
                plan.inputs.global_interpretation_policy_identity
            ),
        }
    )
    return f"dagg1-{digest}"


def _core_intervals() -> tuple[PageInterval, ...]:
    starts = (1, *(page + 1 for page in RANGE_ENDS[:-1]))
    return tuple(
        PageInterval(start=start, end=end) for start, end in zip(starts, RANGE_ENDS, strict=True)
    )


def _range_definition(core: PageInterval, cores: tuple[PageInterval, ...]) -> RangeDefinition:
    read = PageInterval(start=max(1, core.start - 1), end=min(2488, core.end + 1))
    overlaps = tuple(
        OverlapOwner(page=page, owner_core=next(owner for owner in cores if owner.contains(page)))
        for page in read.pages
        if not core.contains(page)
    )
    return RangeDefinition(core=core, read=read, overlap_owners=overlaps)
