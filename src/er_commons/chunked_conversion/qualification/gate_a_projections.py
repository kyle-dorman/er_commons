"""Attach globally materialized G1 projections to source-free range shards."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from er_commons.chunked_conversion.qualification.diagnostics import require
from er_commons.chunked_conversion.range_recomposition import PartitionedEvidence


def attach_gate_a_projections(
    partition: PartitionedEvidence,
    overlay: list[dict[str, Any]],
    alignment: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> PartitionedEvidence:
    """Assign core and overlap projections using explicit page/ref ownership maps."""
    owner_by_ref, pages_by_ref, owner_by_page = _ownership_maps(partition)
    raw_assets = inventory.get("assets")
    require(
        isinstance(raw_assets, list) and all(isinstance(item, dict) for item in raw_assets),
        "asset_inventory_shape",
        stage="gate_a_partition",
        path="asset_inventory.assets",
        expected="list[object]",
        actual=type(raw_assets).__name__,
    )
    assert isinstance(raw_assets, list)
    assets = list(raw_assets)
    core = _core_projections(partition, overlay, alignment, assets, owner_by_ref, owner_by_page)
    alignment_by_page = _unique_alignment_pages(alignment)
    return replace(
        partition,
        shards=tuple(
            replace(
                shard,
                heading_overlay=tuple(core["overlay"][shard.range_id]),
                alignment_pages=tuple(core["alignment"][shard.range_id]),
                assets=tuple(core["assets"][shard.range_id]),
                overlap_evidence=tuple(
                    replace(
                        evidence,
                        heading_overlay=tuple(
                            row
                            for row in overlay
                            if evidence.page
                            in _required(
                                pages_by_ref,
                                str(row["raw_self_ref"]),
                                "heading_overlay.raw_self_ref",
                            )
                        ),
                        alignment_page=_required(
                            alignment_by_page,
                            evidence.page,
                            "alignment_pages.overlap",
                        ),
                        assets=tuple(
                            row for row in assets if int(row["physical_pdf_page"]) == evidence.page
                        ),
                    )
                    for evidence in shard.overlap_evidence
                ),
            )
            for shard in partition.shards
        ),
    )


def _ownership_maps(
    partition: PartitionedEvidence,
) -> tuple[dict[str, str], dict[str, tuple[int, ...]], dict[int, str]]:
    owner_by_ref = {
        item.source_ref: shard.range_id for shard in partition.shards for item in shard.items
    }
    pages_by_ref = {
        item.source_ref: item.pages for shard in partition.shards for item in shard.items
    }
    owner_by_page = {
        page: shard.range_id for shard in partition.shards for page in shard.core_pages
    }
    return owner_by_ref, pages_by_ref, owner_by_page


def _core_projections(
    partition: PartitionedEvidence,
    overlay: list[dict[str, Any]],
    alignment: list[dict[str, Any]],
    assets: list[dict[str, Any]],
    owner_by_ref: dict[str, str],
    owner_by_page: dict[int, str],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: dict[str, dict[str, list[dict[str, Any]]]] = {
        name: {shard.range_id: [] for shard in partition.shards}
        for name in ("overlay", "alignment", "assets")
    }
    for record in overlay:
        owner = _required(owner_by_ref, str(record["raw_self_ref"]), "heading_overlay")
        result["overlay"][owner].append(record)
    for record in alignment:
        owner = _required(owner_by_page, int(record["page_no"]), "alignment_pages")
        result["alignment"][owner].append(record)
    for record in assets:
        owner = _required(owner_by_ref, str(record["raw_object_ref"]), "asset_inventory")
        result["assets"][owner].append(record)
    return result


def _unique_alignment_pages(
    alignment: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for record in alignment:
        page = int(record["page_no"])
        require(
            page not in result,
            "duplicate_alignment_page",
            stage="gate_a_partition",
            path=f"alignment_pages[page_no={page}]",
            expected="one record",
            actual="duplicate record",
        )
        result[page] = record
    return result


def _required(mapping: dict[Any, Any], key: Any, path: str) -> Any:
    require(
        key in mapping,
        "projection_target",
        stage="gate_a_partition",
        path=f"{path}[{key}]",
        expected="known canonical owner",
        actual="missing target",
    )
    return mapping[key]
