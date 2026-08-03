"""Persist resource declarations, enforcement, and attempt measurements."""

from __future__ import annotations

import resource
import sys
from pathlib import Path
from typing import Literal

from er_commons.corpus_extraction.records import (
    ObservabilityRecord,
    ResourceEnforcementRecord,
)
from er_commons.source_freeze import write_json_atomic


def record_resource_enforcement(
    root: Path,
    *,
    transaction_id: str,
    enforcement: Literal["validated_before_content_owners"],
) -> None:
    """Record how the worker enforced the declared resource policy."""
    write_json_atomic(
        root / "resource_enforcement.json",
        ResourceEnforcementRecord(
            transaction_id=transaction_id,
            enforcement=enforcement,
        ).model_dump(mode="json"),
    )


def record_observability(
    root: Path,
    *,
    transaction_id: str,
    wall_seconds: float,
    output_bytes: int,
    stage_timings: dict[str, float],
) -> None:
    """Persist timing, peak child memory, and retained output size."""
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_bytes = int(peak if sys.platform == "darwin" else peak * 1024)
    write_json_atomic(
        root / "observability.json",
        ObservabilityRecord(
            transaction_id=transaction_id,
            wall_seconds=wall_seconds,
            peak_rss_bytes=peak_bytes,
            output_bytes=output_bytes,
            stage_timings=stage_timings,
        ).model_dump(mode="json"),
    )
