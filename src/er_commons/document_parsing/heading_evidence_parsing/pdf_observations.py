"""Public facade for deterministic source-PDF hierarchy observations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from er_commons.document_parsing.heading_evidence_parsing.native_pdf_observations import (
    extract_page_labels,
    read_native_heading_observations,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_extraction import (
    extract_outline_observations,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import (
    JsonObject,
    OutlineExtraction,
)
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem

__all__ = [
    "OutlineExtraction",
    "PdfObservations",
    "extract_outline_observations",
    "extract_page_labels",
    "read_native_heading_observations",
    "read_pdf_observations",
]


@dataclass(frozen=True)
class PdfObservations:
    """Independent source-PDF observations consumed by hierarchy correction."""

    outline_observations: tuple[JsonObject, ...]
    page_labels: dict[int, str]
    diagnostics: tuple[JsonObject, ...]


def read_pdf_observations(
    source_pdf: Path, *, heading_features: list[ObservedItem] | None = None
) -> PdfObservations:
    """Read outline nodes and page labels without converting source content."""
    reader = PdfReader(source_pdf, strict=True)
    outline = extract_outline_observations(reader, heading_features=heading_features)
    return PdfObservations(
        outline_observations=outline.observations,
        page_labels=extract_page_labels(reader),
        diagnostics=outline.diagnostics,
    )
