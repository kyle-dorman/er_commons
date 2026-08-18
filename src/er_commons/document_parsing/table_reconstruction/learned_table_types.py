"""Domain types shared by the learned-table fallback components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

JsonObject = dict[str, Any]
Position = tuple[int, int]
BoundingBox = tuple[float, float, float, float]
FallbackStatus = Literal["accepted", "abstained"]
AbstentionReason = Literal[
    "insufficient_native_tokens",
    "invalid_shape",
    "invalid_otsl",
    "invalid_grid_coverage",
    "out_of_bounds_geometry",
    "non_monotonic_grid_geometry",
    "unmatched_leading_text",
    "native_text_coverage_below_threshold",
    "duplicate_native_text",
    "cleanup_empty",
    "model_failure",
]


@dataclass(frozen=True)
class FallbackAttempt:
    """One terminal learned-fallback decision and optional accepted candidate."""

    region_id: str
    status: FallbackStatus
    reason: AbstentionReason | None
    measurements: JsonObject
    candidate: JsonObject | None


def abstain(
    region_id: str,
    reason: AbstentionReason,
    measurements: JsonObject,
) -> FallbackAttempt:
    """Build an explicit terminal abstention without a table candidate."""
    return FallbackAttempt(
        region_id=region_id,
        status="abstained",
        reason=reason,
        measurements=measurements,
        candidate=None,
    )


class LearnedFallbackRunner(Protocol):
    """External seam invoked by the page parser and replaced by test fakes."""

    def __call__(
        self,
        *,
        pdf_path: Path,
        page_number: int,
        page_size: tuple[float, float],
        region_id: str,
        region_bbox: list[float],
        evidence_root: Path,
    ) -> FallbackAttempt: ...
