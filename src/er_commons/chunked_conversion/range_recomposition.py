"""Stable public API for partitioning and recomposing chunked document evidence."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from er_commons.chunked_conversion.document_reconstruction import DocumentReconstructor
from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_graph import DocumentGraph
from er_commons.chunked_conversion.range_partitioning import (
    DocumentPartitioner,
)
from er_commons.chunked_conversion.range_shard_validation import RangeShardValidator
from er_commons.chunked_conversion.recomposition_diagnostics import RangeRecompositionError
from er_commons.chunked_conversion.recomposition_records import (
    OverlapEvidence,
    PartitionedEvidence,
    RangeItem,
    RangeShard,
)


def partition_document(plan: RangePlan, graph: DocumentGraph) -> PartitionedEvidence:
    """Localize references and assign every document record to one range owner."""
    return DocumentPartitioner(plan, graph).partition()


def recompose_document(
    plan: RangePlan,
    evidence: PartitionedEvidence,
    shards: Iterable[RangeShard],
) -> dict[str, Any]:
    """Restore one canonical document independent of child completion order."""
    return DocumentReconstructor(plan, evidence).recompose(shards)


def validate_range_shard(
    plan: RangePlan,
    shard: RangeShard,
    *,
    require_projections: bool = False,
) -> None:
    """Validate one child semantically before completion or reuse."""
    RangeShardValidator(plan).validate(shard, require_projections=require_projections)


__all__ = [
    "OverlapEvidence",
    "PartitionedEvidence",
    "RangeItem",
    "RangeRecompositionError",
    "RangeShard",
    "partition_document",
    "recompose_document",
    "validate_range_shard",
]
