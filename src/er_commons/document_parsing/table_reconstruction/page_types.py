"""Shared types for one-page table reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from PIL import Image

ExplicitRoute = Literal["full_page_numeric", "layout_regions"]


@dataclass(frozen=True)
class CandidatePayload:
    """Parser-neutral content needed to persist one logical table."""

    metadata: dict[str, Any]
    raw_rows: list[list[str]]
    serialized_cells: list[dict[str, Any]]
    columns_pdf_points: list[dict[str, float]]


@dataclass(frozen=True)
class RenderedPage:
    """Native text and rendered pixels read once from one physical page."""

    width: float
    height: float
    native_text: str
    image: Image.Image
