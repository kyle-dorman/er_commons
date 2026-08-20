"""Fail-closed validation for independently owned range shards."""

from __future__ import annotations

from collections.abc import Sequence

from er_commons.chunked_conversion.range_contract import PlannedRange, RangePlan
from er_commons.chunked_conversion.range_graph import COLLECTIONS, DocumentGraph, iter_references
from er_commons.chunked_conversion.range_partitioning import stable_value_digest
from er_commons.chunked_conversion.recomposition_diagnostics import fail
from er_commons.chunked_conversion.recomposition_records import RangeShard


class RangeShardValidator:
    """Validate one shard's identity, ordering, ownership, and projections."""

    def __init__(self, plan: RangePlan) -> None:
        self.plan = plan

    def validate(self, shard: RangeShard, *, require_projections: bool = False) -> None:
        """Reject any shard that cannot be safely completed or reused."""
        planned = self._planned_range(shard)
        self._validate_identity_and_pages(planned, shard)
        owned_refs = self._validate_items(planned, shard)
        self._validate_overlap_shape(planned, shard)
        self._validate_core_projections(planned, shard, owned_refs, require_projections)

    def _planned_range(self, shard: RangeShard) -> PlannedRange:
        planned = next((item for item in self.plan.ranges if item.range_id == shard.range_id), None)
        if planned is None:
            fail(
                self.plan,
                f"{shard.range_id}.identity",
                "planned_range",
                "known range",
                shard.range_id,
            )
        return planned

    def _validate_identity_and_pages(self, planned: PlannedRange, shard: RangeShard) -> None:
        prefix = shard.range_id
        if shard.plan_id != self.plan.plan_id:
            fail(self.plan, f"{prefix}.plan_id", "plan_identity", self.plan.plan_id, shard.plan_id)
        if shard.range_id != planned.range_id:
            fail(
                self.plan,
                f"{prefix}.range_id",
                "range_identity",
                planned.range_id,
                shard.range_id,
            )
        if shard.core_pages != planned.core.pages or shard.read_pages != planned.read.pages:
            fail(
                self.plan,
                f"{prefix}.pages",
                "planned_intervals",
                planned.core.pages,
                shard.core_pages,
            )
        actual_pages = tuple(page for page, _ in shard.pages)
        if actual_pages != planned.core.pages:
            fail(
                self.plan,
                f"{prefix}.pages",
                "ordered_core_coverage",
                planned.core.pages,
                actual_pages,
            )

    def _validate_items(self, planned: PlannedRange, shard: RangeShard) -> set[str]:
        self._validate_item_order(shard)
        local_counts: dict[str, int] = {}
        owned_refs: set[str] = set()
        for item in shard.items:
            expected_index = local_counts.get(item.collection, 0)
            expected_ref = f"#/{item.collection}/{expected_index}"
            if item.local_ref != expected_ref:
                fail(self.plan, item.source_ref, "local_ref_order", expected_ref, item.local_ref)
            local_counts[item.collection] = expected_index + 1
            if not item.pages or min(item.pages) not in planned.core.pages:
                fail(self.plan, item.source_ref, "core_item_owner", planned.core.pages, item.pages)
            if any(
                not 1 <= page <= self.plan.inputs.source.physical_page_count for page in item.pages
            ):
                fail(self.plan, item.source_ref, "item_page_bounds", "source pages", item.pages)
            direct_pages = tuple(
                sorted(
                    {
                        int(provenance["page_no"])
                        for provenance in item.value.get("prov", [])
                        if isinstance(provenance, dict)
                        and isinstance(provenance.get("page_no"), int)
                    }
                )
            )
            if direct_pages and direct_pages != item.pages:
                fail(self.plan, item.source_ref, "item_provenance_pages", direct_pages, item.pages)
            expected_self = f"range:{shard.range_id}{item.local_ref}"
            if item.value.get("self_ref") != expected_self:
                fail(
                    self.plan,
                    item.source_ref,
                    "localized_self_ref",
                    expected_self,
                    item.value.get("self_ref"),
                )
            owned_refs.add(item.source_ref)
            self._validate_localized_references(item.source_ref, item.value)
        return owned_refs

    def _validate_item_order(self, shard: RangeShard) -> None:
        source_positions = [(item.collection, item.source_index) for item in shard.items]
        expected_positions = sorted(
            source_positions,
            key=lambda value: (COLLECTIONS.index(value[0]), value[1]),
        )
        if source_positions == expected_positions:
            return
        difference = next(
            index
            for index, (expected, actual) in enumerate(
                zip(expected_positions, source_positions, strict=True)
            )
            if expected != actual
        )
        fail(
            self.plan,
            f"{shard.range_id}.items[{difference}]",
            "stable_item_order",
            expected_positions[difference],
            source_positions[difference],
        )

    def _validate_localized_references(self, source_ref: str, value: object) -> None:
        for path, reference in iter_references(value):
            if (
                reference.startswith("aggregate:#/")
                or reference.startswith("global:#/")
                or any(
                    reference.startswith(f"range:{item.range_id}#/") for item in self.plan.ranges
                )
            ):
                continue
            fail(
                self.plan,
                f"{source_ref}:{path}",
                "localized_reference",
                "known owner",
                reference,
            )

    def _validate_overlap_shape(self, planned: PlannedRange, shard: RangeShard) -> None:
        expected_overlap = tuple(
            page for page in planned.read.pages if page not in planned.core.pages
        )
        actual_overlap = tuple(evidence.page for evidence in shard.overlap_evidence)
        if actual_overlap != expected_overlap:
            fail(
                self.plan,
                f"{shard.range_id}.overlap_evidence",
                "exact_overlap_coverage",
                expected_overlap,
                actual_overlap,
            )
        for evidence in shard.overlap_evidence:
            path = f"{shard.range_id}.overlap_evidence[{evidence.page}]"
            overlap_refs = {reference for reference, _digest in evidence.record_digests}
            if len(evidence.page_digest) != 64 or len(evidence.record_digests) != len(
                dict(evidence.record_digests)
            ):
                fail(self.plan, path, "overlap_shape", "unique digests", evidence)
            if (
                evidence.alignment_page is not None
                and evidence.alignment_page.get("page_no") != evidence.page
            ):
                fail(
                    self.plan,
                    f"{path}.alignment",
                    "overlap_page",
                    evidence.page,
                    evidence.alignment_page,
                )
            for record in evidence.heading_overlay:
                if record.get("raw_self_ref") not in overlap_refs:
                    fail(
                        self.plan,
                        f"{path}.heading_overlay",
                        "overlap_heading_target",
                        "overlap record",
                        record,
                    )
            for record in evidence.assets:
                if (
                    record.get("raw_object_ref") not in overlap_refs
                    or record.get("physical_pdf_page") != evidence.page
                ):
                    fail(
                        self.plan,
                        f"{path}.assets",
                        "overlap_asset_target",
                        "overlap record on page",
                        record,
                    )

    def _validate_core_projections(
        self,
        planned: PlannedRange,
        shard: RangeShard,
        owned_refs: set[str],
        require_projections: bool,
    ) -> None:
        alignment_pages = tuple(int(record.get("page_no", 0)) for record in shard.alignment_pages)
        if (require_projections or shard.alignment_pages) and alignment_pages != planned.core.pages:
            fail(
                self.plan,
                f"{shard.range_id}.alignment_pages",
                "core_alignment_coverage",
                planned.core.pages,
                alignment_pages,
            )
        for record in shard.heading_overlay:
            if record.get("raw_self_ref") not in owned_refs:
                fail(
                    self.plan,
                    f"{shard.range_id}.heading_overlay",
                    "owned_overlay_target",
                    "owned ref",
                    record,
                )
        for record in shard.assets:
            if record.get("raw_object_ref") not in owned_refs:
                fail(
                    self.plan,
                    f"{shard.range_id}.assets",
                    "owned_asset_target",
                    "owned ref",
                    record,
                )


def validate_overlap_evidence(
    plan: RangePlan,
    shards: Sequence[RangeShard],
    graph: DocumentGraph,
) -> None:
    """Compare every duplicated seam projection with the rebuilt document graph."""
    pages = dict(graph.pages)
    records = graph.record_by_ref
    canonical_overlay = sorted(
        (record for shard in shards for record in shard.heading_overlay),
        key=lambda record: str(record["raw_self_ref"]),
    )
    overlay_by_page = {
        page: tuple(
            record
            for record in canonical_overlay
            if page in records[str(record["raw_self_ref"])].pages
        )
        for shard in shards
        for page in shard.read_pages
    }
    alignment_by_page = {
        int(record["page_no"]): record for shard in shards for record in shard.alignment_pages
    }
    assets_by_page = {
        page: tuple(
            sorted(
                (
                    record
                    for shard in shards
                    for record in shard.assets
                    if record.get("physical_pdf_page") == page
                ),
                key=lambda record: int(str(record["raw_object_ref"]).rsplit("/", 1)[1]),
            )
        )
        for shard in shards
        for page in shard.read_pages
    }
    for shard in shards:
        for evidence in shard.overlap_evidence:
            path = f"{shard.range_id}.overlap_evidence[{evidence.page}]"
            page_value = pages.get(evidence.page)
            actual_page = stable_value_digest(page_value) if page_value is not None else None
            if actual_page != evidence.page_digest:
                fail(
                    plan,
                    f"{path}.page_digest",
                    "overlap_page_identity",
                    evidence.page_digest,
                    actual_page,
                )
            actual_records = tuple(
                (record.source_ref, stable_value_digest(record.value))
                for record in graph.records
                if evidence.page in record.pages
            )
            if actual_records != evidence.record_digests:
                fail(
                    plan,
                    f"{path}.record_digests",
                    "overlap_semantic_identity",
                    evidence.record_digests,
                    actual_records,
                )
            comparisons = (
                ("heading_overlay", overlay_by_page[evidence.page], evidence.heading_overlay),
                ("alignment_page", alignment_by_page[evidence.page], evidence.alignment_page),
                ("assets", assets_by_page[evidence.page], evidence.assets),
            )
            for field, expected, actual in comparisons:
                if actual != expected:
                    fail(
                        plan,
                        f"{path}.{field}",
                        "overlap_projection_identity",
                        expected,
                        actual,
                    )


__all__ = ["RangeShardValidator", "validate_overlap_evidence"]
