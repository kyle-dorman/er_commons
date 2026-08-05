"""Integrate accepted learned-table attempts into one Camelot page result."""

from __future__ import annotations

from pathlib import Path

from er_commons.table_extraction.learned_fallback import (
    LearnedFallbackRunner,
    unmatched_layout_regions,
)
from er_commons.table_extraction.learned_table_types import JsonObject


def apply_learned_fallbacks(
    *,
    runner: LearnedFallbackRunner,
    pdf_path: Path,
    page_number: int,
    page_size: tuple[float, float],
    page_output_root: Path,
    parser_evidence: JsonObject,
    layout_regions: list[JsonObject],
) -> list[JsonObject]:
    """Evaluate unmatched regions and update their explicit parser dispositions."""
    unmatched_regions = unmatched_layout_regions(parser_evidence, layout_regions)
    matches_by_region = {str(item["region_id"]): item for item in parser_evidence["region_matches"]}
    attempts: list[JsonObject] = []
    accepted_candidates: list[JsonObject] = []
    for region in unmatched_regions:
        region_id = str(region["region_id"])
        relative_evidence_root = Path("fallback") / region_id
        attempt = runner(
            pdf_path=pdf_path,
            page_number=page_number,
            page_size=page_size,
            region_id=region_id,
            region_bbox=list(region["bbox_pdf_points_bottom_left"]),
            evidence_root=page_output_root / relative_evidence_root,
        )
        attempts.append(
            {
                "region_id": region_id,
                "status": attempt.status,
                "reason": attempt.reason,
                "measurements": attempt.measurements,
                "evidence_root": relative_evidence_root.as_posix(),
            }
        )
        match = matches_by_region[region_id]
        match["camelot_matched"] = False
        match["learned_fallback_status"] = attempt.status
        match["learned_fallback_reason"] = attempt.reason
        if attempt.candidate is None:
            continue
        candidate = dict(attempt.candidate)
        candidate["learned_fallback_evidence_root"] = relative_evidence_root.as_posix()
        accepted_candidates.append(candidate)
        match["matched"] = True
    parser_evidence["learned_fallback_attempts"] = attempts
    return accepted_candidates
