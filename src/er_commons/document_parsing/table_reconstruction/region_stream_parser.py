"""Camelot invocation boundary for region-bounded Stream recovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import camelot


def read_region_tables(
    pdf_path: Path,
    page_number: int,
    region_bbox: list[float],
) -> list[Any]:
    """Run Camelot Stream once for an exact bottom-left PDF region."""
    left, bottom, right, top = region_bbox
    return list(
        camelot.read_pdf(  # type: ignore[attr-defined]
            pdf_path,
            pages=str(page_number),
            flavor="stream",
            table_areas=[f"{left},{top},{right},{bottom}"],
            suppress_stdout=False,
            parallel=False,
        )
    )


__all__ = ["read_region_tables"]
