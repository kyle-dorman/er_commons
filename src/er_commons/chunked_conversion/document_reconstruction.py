"""Rebuild one canonical document from verified range-owned evidence."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, cast

from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.range_graph import (
    COLLECTIONS,
    ROOT_REFS,
    build_document_graph,
    rewrite_references,
)
from er_commons.chunked_conversion.range_shard_validation import (
    RangeShardValidator,
    validate_overlap_evidence,
)
from er_commons.chunked_conversion.recomposition_diagnostics import fail
from er_commons.chunked_conversion.recomposition_records import (
    PartitionedEvidence,
    RangeItem,
    RangeShard,
)


class DocumentReconstructor:
    """Restore canonical references, collection positions, pages, and seam evidence."""

    def __init__(self, plan: RangePlan, evidence: PartitionedEvidence) -> None:
        self.plan = plan
        self.evidence = evidence

    def recompose(self, shards: Iterable[RangeShard]) -> dict[str, Any]:
        """Reconstruct in plan order, independent of child completion order."""
        self._require_partition_identity()
        canonical = self._canonical_shards(shards)
        local_to_source, pages = self._index_ranges(canonical)
        collection_slots = self._restore_items(canonical, local_to_source)
        document = self._restore_document_root(local_to_source, collection_slots, pages)
        graph = build_document_graph(
            document,
            page_count=self.plan.inputs.source.physical_page_count,
        )
        validate_overlap_evidence(self.plan, canonical, graph)
        return document

    def _require_partition_identity(self) -> None:
        if self.evidence.plan_id != self.plan.plan_id:
            fail(
                self.plan,
                "partition.plan_id",
                "plan_identity",
                self.plan.plan_id,
                self.evidence.plan_id,
            )

    def _canonical_shards(self, shards: Iterable[RangeShard]) -> list[RangeShard]:
        by_id: dict[str, RangeShard] = {}
        for shard in shards:
            if shard.range_id in by_id:
                fail(self.plan, shard.range_id, "unique_range", "one shard", "duplicate")
            by_id[shard.range_id] = shard
        expected_ids = [planned.range_id for planned in self.plan.ranges]
        if set(by_id) != set(expected_ids):
            missing = [range_id for range_id in expected_ids if range_id not in by_id]
            extra = sorted(set(by_id) - set(expected_ids))
            affected = missing[0] if missing else extra[0]
            fail(
                self.plan,
                f"ranges[{affected}]",
                "exact_range_set",
                {"missing": [], "extra": []},
                {"missing": missing, "extra": extra},
            )
        return [by_id[range_id] for range_id in expected_ids]

    def _index_ranges(
        self, canonical: list[RangeShard]
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
        validator = RangeShardValidator(self.plan)
        local_to_source: dict[str, str] = {}
        pages: dict[str, dict[str, Any]] = {}
        for shard in canonical:
            validator.validate(shard)
            for page, value in shard.pages:
                key = str(page)
                if key in pages:
                    fail(self.plan, f"{shard.range_id}.pages[{page}]", "unique_page", None, page)
                pages[key] = value
            for item in shard.items:
                self._add_local_reference(
                    local_to_source,
                    f"range:{shard.range_id}{item.local_ref}",
                    item,
                    "unique_local_ref",
                )
        for item in self.evidence.global_items:
            self._add_local_reference(
                local_to_source,
                f"global:{item.local_ref}",
                item,
                "unique_global_ref",
            )
        return local_to_source, pages

    def _add_local_reference(
        self,
        local_to_source: dict[str, str],
        address: str,
        item: RangeItem,
        invariant: str,
    ) -> None:
        if address in local_to_source:
            fail(self.plan, address, invariant, None, address)
        local_to_source[address] = item.source_ref

    def _reference_restorer(self, local_to_source: dict[str, str]) -> Callable[[str, str], str]:
        def restore(reference: str, path: str) -> str:
            if reference.startswith("aggregate:#/"):
                root_reference = reference.removeprefix("aggregate:")
                if root_reference not in ROOT_REFS:
                    fail(self.plan, path, "known_root", sorted(ROOT_REFS), root_reference)
                return root_reference
            try:
                return local_to_source[reference]
            except KeyError as error:
                fail(self.plan, path, "closed_local_reference", "known local ref", reference)
                raise AssertionError from error

        return restore

    def _restore_items(
        self,
        canonical: list[RangeShard],
        local_to_source: dict[str, str],
    ) -> dict[str, list[dict[str, Any] | None]]:
        collection_slots: dict[str, list[dict[str, Any] | None]] = {
            collection: [None] * self.evidence.collection_counts[collection]
            for collection in COLLECTIONS
        }
        restore = self._reference_restorer(local_to_source)
        item_groups = [*(shard.items for shard in canonical), self.evidence.global_items]
        for items in item_groups:
            for item in items:
                slots = collection_slots.get(item.collection)
                if slots is None:
                    fail(
                        self.plan,
                        item.source_ref,
                        "source_collection",
                        sorted(collection_slots),
                        item.collection,
                    )
                if not 0 <= item.source_index < len(slots):
                    fail(
                        self.plan,
                        item.source_ref,
                        "source_index_bounds",
                        item.collection,
                        item.source_index,
                    )
                if slots[item.source_index] is not None:
                    fail(
                        self.plan,
                        item.source_ref,
                        "unique_source_index",
                        None,
                        item.source_index,
                    )
                restored = rewrite_references(item.value, restore)
                if restored.get("self_ref") != item.source_ref:
                    fail(
                        self.plan,
                        item.source_ref,
                        "self_ref_identity",
                        item.source_ref,
                        restored.get("self_ref"),
                    )
                slots[item.source_index] = restored
        return collection_slots

    def _restore_document_root(
        self,
        local_to_source: dict[str, str],
        collection_slots: dict[str, list[dict[str, Any] | None]],
        pages: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        restore = self._reference_restorer(local_to_source)
        document = cast(
            dict[str, Any],
            rewrite_references(self.evidence.root, restore),
        )
        for collection, slots in collection_slots.items():
            if any(item is None for item in slots):
                fail(self.plan, collection, "exact_item_coverage", len(slots), "missing")
            document[collection] = list(slots)
        document["pages"] = pages
        return document


__all__ = ["DocumentReconstructor"]
