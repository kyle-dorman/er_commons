"""Memory-bounded reuse of core-owned projections from sealed ranges."""

from __future__ import annotations

import gc

from er_commons.chunked_conversion.range_contract import RangePlan
from er_commons.chunked_conversion.runtime.range_store import ConvertedRangeStore
from er_commons.document_parsing.content_parsing.page_projection import PageEvidenceProjection


def verified_core_page_projections(
    store: ConvertedRangeStore, plan: RangePlan, source_page_count: int
) -> list[PageEvidenceProjection]:
    """Select core projections while releasing each decoded range immediately."""
    projections: list[PageEvidenceProjection] = []
    for planned in plan.ranges:
        verified = store.verify(planned.range_id)
        projections.extend(
            projection
            for projection in verified.projections
            if planned.core.contains(projection.physical_pdf_page)
        )
        del verified
        gc.collect()
    expected_pages = list(range(1, source_page_count + 1))
    actual_pages = [item.physical_pdf_page for item in projections]
    if actual_pages != expected_pages:
        raise ValueError("page projections do not cover the complete source")
    return projections


__all__ = ["verified_core_page_projections"]
