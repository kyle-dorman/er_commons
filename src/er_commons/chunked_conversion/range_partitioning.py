"""Assign canonical document records to independently owned page ranges."""

from __future__ import annotations

from collections.abc import Callable

from er_commons.chunked_conversion.range_contract import PlannedRange, RangePlan
from er_commons.chunked_conversion.range_graph import (
    COLLECTIONS,
    ROOT_REFS,
    DocumentGraph,
    RangeGraphError,
    parse_collection_ref,
    rewrite_references,
)
from er_commons.chunked_conversion.recomposition_diagnostics import RangeRecompositionError
from er_commons.chunked_conversion.recomposition_records import (
    OverlapEvidence,
    PartitionedEvidence,
    RangeItem,
    RangeShard,
)


class DocumentPartitioner:
    """Localize references and assign each document record to one range owner."""

    def __init__(self, plan: RangePlan, graph: DocumentGraph) -> None:
        self.plan = plan
        self.graph = graph

    def partition(self) -> PartitionedEvidence:
        """Build the global record set and one source-ordered shard per range."""
        self._require_source_page_count()
        local_index = self._local_indexes()
        items_by_range, global_items = self._partition_items(local_index)
        shards = self._build_shards(items_by_range)
        return PartitionedEvidence(
            plan_id=self.plan.plan_id,
            root=rewrite_references(self.graph.root, self._reference_localizer(local_index)),
            collection_counts={
                collection: sum(
                    1 for record in self.graph.records if record.collection == collection
                )
                for collection in COLLECTIONS
            },
            global_items=tuple(global_items),
            shards=tuple(shards),
        )

    def _require_source_page_count(self) -> None:
        expected = self.plan.inputs.source.physical_page_count
        if len(self.graph.pages) != expected:
            raise RangeRecompositionError(
                f"plan={self.plan.plan_id} path=pages invariant=source_page_count"
            )

    def _local_indexes(self) -> dict[str, tuple[PlannedRange | None, int]]:
        owner_by_page = {
            page: planned for planned in self.plan.ranges for page in planned.core.pages
        }
        owner_by_ref = {
            record.source_ref: owner_by_page[min(record.pages)] if record.pages else None
            for record in self.graph.records
        }
        local_index: dict[str, tuple[PlannedRange | None, int]] = {}
        range_counts: dict[tuple[str, str], int] = {}
        global_counts: dict[str, int] = {}
        for record in self.graph.records:
            owner = owner_by_ref[record.source_ref]
            if owner is None:
                index = global_counts.get(record.collection, 0)
                global_counts[record.collection] = index + 1
            else:
                key = (owner.range_id, record.collection)
                index = range_counts.get(key, 0)
                range_counts[key] = index + 1
            local_index[record.source_ref] = (owner, index)
        return local_index

    def _reference_localizer(
        self, local_index: dict[str, tuple[PlannedRange | None, int]]
    ) -> Callable[[str, str], str]:
        def localize(reference: str, path: str) -> str:
            if reference in ROOT_REFS:
                return f"aggregate:{reference}"
            try:
                owner, index = local_index[reference]
                collection, _ = parse_collection_ref(reference)
            except (KeyError, RangeGraphError) as error:
                raise RangeRecompositionError(
                    f"plan={self.plan.plan_id} path={path} "
                    f"invariant=known_reference actual={reference}"
                ) from error
            if owner is None:
                return f"global:#/{collection}/{index}"
            return f"range:{owner.range_id}#/{collection}/{index}"

        return localize

    def _partition_items(
        self, local_index: dict[str, tuple[PlannedRange | None, int]]
    ) -> tuple[dict[str, list[RangeItem]], list[RangeItem]]:
        localize = self._reference_localizer(local_index)
        items_by_range: dict[str, list[RangeItem]] = {
            planned.range_id: [] for planned in self.plan.ranges
        }
        global_items: list[RangeItem] = []
        for record in self.graph.records:
            owner, index = local_index[record.source_ref]
            item = RangeItem(
                collection=record.collection,
                source_index=record.index,
                local_ref=f"#/{record.collection}/{index}",
                source_ref=record.source_ref,
                pages=record.pages,
                value=rewrite_references(record.value, localize),
            )
            if owner is None:
                global_items.append(item)
            else:
                items_by_range[owner.range_id].append(item)
        return items_by_range, global_items

    def _build_shards(self, items_by_range: dict[str, list[RangeItem]]) -> list[RangeShard]:
        page_values = dict(self.graph.pages)
        return [
            RangeShard(
                plan_id=self.plan.plan_id,
                range_id=planned.range_id,
                core_pages=planned.core.pages,
                read_pages=planned.read.pages,
                pages=tuple((page, page_values[page]) for page in planned.core.pages),
                items=tuple(items_by_range[planned.range_id]),
                overlap_evidence=tuple(
                    OverlapEvidence(
                        page=page,
                        page_digest=stable_value_digest(page_values[page]),
                        record_digests=tuple(
                            (record.source_ref, stable_value_digest(record.value))
                            for record in self.graph.records
                            if page in record.pages
                        ),
                    )
                    for page in planned.read.pages
                    if page not in planned.core.pages
                ),
            )
            for planned in self.plan.ranges
        ]


def stable_value_digest(value: object) -> str:
    """Return the canonical JSON digest used by overlap evidence."""
    from er_commons.artifact_io import canonical_json_sha256

    return canonical_json_sha256(value)


__all__ = ["DocumentPartitioner", "stable_value_digest"]
