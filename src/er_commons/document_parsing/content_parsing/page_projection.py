"""Slim page evidence exchanged before aggregate Docling interpretation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageEvidenceProjection(BaseModel):
    """Page-local routing inputs with no aggregate reading-order semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source_id: str = Field(min_length=1)
    physical_pdf_page: int = Field(gt=0)
    features: dict[str, Any]
    layout_table_observations: list[dict[str, Any]]
    boundary_markers_before_first_table: list[dict[str, Any]]
    range_id: str = Field(min_length=1)

    def as_record(self) -> dict[str, Any]:
        """Return the complete persisted page-local projection record."""
        return deepcopy(self.model_dump(mode="json"))


def project_page_evidence(
    *,
    source_id: str,
    range_id: str,
    page_number: int,
    features: dict[str, Any],
    layout_table_observations: list[dict[str, Any]],
    boundary_markers_before_first_table: list[dict[str, Any]],
) -> PageEvidenceProjection:
    """Build the narrow pre-aggregate contract without adding interpreted text."""
    return PageEvidenceProjection(
        source_id=source_id,
        physical_pdf_page=page_number,
        features=deepcopy(features),
        layout_table_observations=deepcopy(layout_table_observations),
        boundary_markers_before_first_table=deepcopy(boundary_markers_before_first_table),
        range_id=range_id,
    )


__all__ = ["PageEvidenceProjection", "project_page_evidence"]
