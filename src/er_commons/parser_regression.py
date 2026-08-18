"""Typed, checksum-bound affected-page regression support."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ClosedRecord(BaseModel):
    """Regression records reject misspelled or undeclared policy fields."""

    model_config = ConfigDict(extra="forbid")


class WarningScopeRegression(ClosedRecord):
    """Expected source-warning accounting for one checksum-bound input."""

    source_id: str
    source_sha256: Sha256
    expected_raw_source_warning_count: int = Field(ge=0)
    expected_unique_source_warning_count: int = Field(ge=0)


class RoutingCase(ClosedRecord):
    """One fixed before/after routing claim."""

    page: int = Field(gt=0)
    expected_rotation_degrees: Literal[0, 90, 180, 270]
    baseline_route: Literal["full_page_numeric", "layout_regions", "no_table_route"]
    expected_route: Literal["full_page_numeric", "layout_regions", "no_table_route"]
    expected_strict_table_dominant: bool
    expected_dense_partial_table: bool


class RoutingGeometryRegression(ClosedRecord):
    """Checksum-bound routing cases for one source."""

    source_id: str
    source_sha256: Sha256
    cases: list[RoutingCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_pages(self) -> RoutingGeometryRegression:
        """Reject duplicate routing claims for one physical page."""
        pages = [case.page for case in self.cases]
        if len(pages) != len(set(pages)):
            raise ValueError("routing regression pages must be unique")
        return self


class LearnedPositiveSource(ClosedRecord):
    """One positive source and its exact bounded physical pages."""

    source_id: str
    source_sha256: Sha256
    pages: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_positive_pages(self) -> LearnedPositiveSource:
        if len(self.pages) != len(set(self.pages)) or any(page <= 0 for page in self.pages):
            raise ValueError("learned positive pages must be unique and positive")
        return self


class ExistingTableNegativeControl(ClosedRecord):
    """A page where an existing Camelot table must prevent fallback."""

    source_id: str
    source_sha256: Sha256
    page: int = Field(gt=0)
    expected_disposition: Literal["not_triggered_existing_camelot_table"]


class HistoricalNegativeControl(ClosedRecord):
    """Named prior evidence that cannot support family or continuation claims."""

    evidence: str
    pages: list[int] = Field(min_length=1)
    expected_disposition: Literal["not_family_or_continuation_evidence"]


class LearnedFallbackRegression(ClosedRecord):
    """Bounded positive sources, negative controls, and the recovery gate."""

    minimum_recovered_positive_pages: int = Field(gt=0)
    positive_sources: list[LearnedPositiveSource] = Field(min_length=1)
    negative_controls: list[ExistingTableNegativeControl | HistoricalNegativeControl] = Field(
        min_length=1
    )


class ContinuationRegression(ClosedRecord):
    """One checksum-bound adjacent boundary with an expected disposition."""

    source_id: str
    source_sha256: Sha256
    left_page: int = Field(gt=0)
    right_page: int = Field(gt=0)
    expected_status: Literal["accepted", "rejected", "ambiguous"]

    @model_validator(mode="after")
    def adjacent_pages(self) -> ContinuationRegression:
        if self.right_page != self.left_page + 1:
            raise ValueError("continuation regression pages must be adjacent")
        return self


class RegressionManifest(ClosedRecord):
    """Top-level Task 03G.1a manifest with typed routing claims."""

    schema_version: Literal["er_commons.task03g1a_regression.v1"]
    source_release_version: str
    baseline_smoke_id: str = Field(pattern=r"^smokev1-[0-9a-f]{64}$")
    warning_scope: WarningScopeRegression
    routing_geometry: RoutingGeometryRegression
    learned_fallback: LearnedFallbackRegression
    continuations: list[ContinuationRegression]


def load_regression_manifest(path: Path) -> tuple[RegressionManifest, str]:
    """Validate a regression manifest and return its byte-level digest."""
    raw = path.read_bytes()
    return RegressionManifest.model_validate_json(raw), hashlib.sha256(raw).hexdigest()
