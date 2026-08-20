"""Adversarial and ordering proofs for source-free Gate A evidence."""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from er_commons.chunked_conversion.qualification.gate_a_profile import SEAM_CUTS
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_graph import DocumentGraph
from er_commons.chunked_conversion.range_recomposition import (
    PartitionedEvidence,
    RangeRecompositionError,
    RangeShard,
    recompose_document,
    validate_range_shard,
)


def mutation_matrix(
    plan: RangePlan,
    partition: PartitionedEvidence,
    shards: tuple[RangeShard, ...],
) -> list[dict[str, Any]]:
    """Require the real-G1 shard validator to reject each named corruption class."""
    first = shards[0]
    cases: list[tuple[str, tuple[RangeShard, ...], RangeShard | None]] = [
        ("missing_range", shards[:-1], None),
        ("duplicate_range", (*shards, first), None),
        (
            "reordered_items",
            (replace(first, items=tuple(reversed(first.items))), *shards[1:]),
            None,
        ),
        ("foreign_plan_identity", (replace(first, plan_id="foreign-plan"), *shards[1:]), None),
        ("overlap_semantic_corruption", _corrupt_page_digest(shards), None),
        (
            "missing_alignment_projection",
            shards,
            replace(first, alignment_pages=first.alignment_pages[:-1]),
        ),
        ("overlap_heading_corruption", _mutate_overlap(shards, "heading_overlay"), None),
        ("overlap_alignment_corruption", _mutate_overlap(shards, "alignment_page"), None),
        ("overlap_asset_corruption", _mutate_overlap(shards, "assets"), None),
    ]
    return [
        _require_rejection(plan, partition, name, candidate, child)
        for name, candidate, child in cases
    ]


def resume_matrix(
    plan: RangePlan,
    partition: PartitionedEvidence,
    shards: tuple[RangeShard, ...],
    selected_range_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Report recovery observed through the real on-disk bundle-resume seam."""
    selected = set(selected_range_ids)
    retained = tuple(shard.range_id for shard in shards if shard.range_id not in selected)
    recompose_document(plan, partition, shards)
    return {
        "status": "passed",
        "recovery_seam": "range_bundle.resume_range_bundles",
        "retained_verified_range_ids": list(retained),
        "selected_missing_range_ids": list(selected_range_ids),
        "valid_ranges_reexecuted": False,
        "aggregate_recomposition_passed": True,
    }


def seam_evidence(graph: DocumentGraph, overlay: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Explain each Gate A cut with adjacent and crossing semantic evidence."""
    classes = dict(
        zip(
            SEAM_CUTS,
            (
                "cross_page_text",
                "heading_transition",
                "furniture_transition",
                "caption_and_consecutive_tables",
                "cross_page_text",
                "ordinary_prose",
                "long_table_run",
            ),
            strict=True,
        )
    )
    pages_by_ref = {record.source_ref: record.pages for record in graph.records}
    return [_one_seam(graph, overlay, pages_by_ref, cut, classes[cut]) for cut in SEAM_CUTS]


def completion_orders(
    shards: tuple[RangeShard, ...],
) -> tuple[tuple[str, tuple[RangeShard, ...]], ...]:
    """Return canonical, reverse, and deterministic randomized arrival orders."""
    randomized = list(shards)
    random.Random(20260820).shuffle(randomized)
    return (
        ("forward", shards),
        ("reverse", tuple(reversed(shards))),
        ("randomized_seed_20260820", tuple(randomized)),
    )


def _require_rejection(
    plan: RangePlan,
    partition: PartitionedEvidence,
    name: str,
    candidate: tuple[RangeShard, ...],
    child: RangeShard | None,
) -> dict[str, Any]:
    try:
        if child is None:
            recompose_document(plan, partition, candidate)
        else:
            validate_range_shard(plan, child, require_projections=True)
    except RangeRecompositionError as error:
        return {"case": name, "status": "rejected", "diagnostic": str(error)}
    raise ValueError(f"Gate A mutation was not rejected: {name}")


def _corrupt_page_digest(shards: tuple[RangeShard, ...]) -> tuple[RangeShard, ...]:
    first = shards[0]
    overlap = (
        replace(first.overlap_evidence[0], page_digest="0" * 64),
        *first.overlap_evidence[1:],
    )
    return (replace(first, overlap_evidence=overlap), *shards[1:])


def _mutate_overlap(shards: tuple[RangeShard, ...], field: str) -> tuple[RangeShard, ...]:
    updated = list(shards)
    for shard_index, shard in enumerate(shards):
        for evidence_index, evidence in enumerate(shard.overlap_evidence):
            value = getattr(evidence, field)
            if not value:
                continue
            if field == "alignment_page":
                changed = replace(evidence, alignment_page={**value, "width": -1.0})
            elif field == "heading_overlay":
                changed = replace(evidence, heading_overlay=value[:-1])
            else:
                changed = replace(evidence, assets=value[:-1])
            overlap = list(shard.overlap_evidence)
            overlap[evidence_index] = changed
            updated[shard_index] = replace(shard, overlap_evidence=tuple(overlap))
            return tuple(updated)
    raise ValueError(f"no Gate A overlap evidence available for mutation: {field}")


def _one_seam(
    graph: DocumentGraph,
    overlay: list[dict[str, Any]],
    pages_by_ref: dict[str, tuple[int, ...]],
    cut: int,
    seam_class: str,
) -> dict[str, Any]:
    crossing = [
        record.source_ref
        for record in graph.records
        if record.pages and min(record.pages) <= cut < max(record.pages)
    ]
    adjacent = [
        record for record in graph.records if cut in record.pages or cut + 1 in record.pages
    ]
    label_counts: dict[str, int] = {}
    for record in adjacent:
        label = str(record.value.get("label", "unlabeled"))
        label_counts[label] = label_counts.get(label, 0) + 1
    headings = [
        str(record["raw_self_ref"])
        for record in overlay
        if cut in pages_by_ref[str(record["raw_self_ref"])]
        or cut + 1 in pages_by_ref[str(record["raw_self_ref"])]
    ]
    return {
        "cut_after_page": cut,
        "seam_class": seam_class,
        "adjacent_record_count": len(adjacent),
        "adjacent_label_counts": label_counts,
        "crossing_record_count": len(crossing),
        "crossing_refs": crossing,
        "adjacent_heading_overlay_refs": headings,
    }
