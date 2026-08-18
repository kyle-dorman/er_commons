"""Typed in-memory boundaries for table-reconstruction orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.document_parsing.table_reconstruction.learned_fallback import (
    LearnedFallbackRunner,
)

ExplicitRoute = Literal["full_page_numeric", "layout_regions"]

JsonRecord = dict[str, Any]


@dataclass(frozen=True)
class TableCandidate:
    """One validated serialized table record crossing the page/run boundary."""

    record: JsonRecord

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> TableCandidate:
        """Validate the fields consumed by run-level assembly."""
        copied = dict(record)
        if not isinstance(copied.get("table_id"), str):
            raise ValueError("page table candidate has no table_id")
        for role in ("raw_csv", "clean_csv", "cells"):
            artifact = copied.get(role)
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
                raise ValueError(f"table candidate has invalid {role} artifact")
        return cls(copied)


@dataclass(frozen=True)
class PageExtractionResult:
    """Validated page result plus its typed table candidates."""

    record: JsonRecord
    tables: tuple[TableCandidate, ...]

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> PageExtractionResult:
        """Validate the run-level fields before orchestration consumes them."""
        copied = dict(record)
        page = copied.get("physical_pdf_page")
        tables = copied.get("tables")
        if not isinstance(page, int) or page < 1:
            raise ValueError("page extraction result has invalid physical page")
        if not isinstance(tables, list):
            raise ValueError(f"page {page} extraction result has no table list")
        if copied.get("table_count") != len(tables):
            raise ValueError(f"page {page} table count differs from table records")
        return cls(copied, tuple(TableCandidate.from_record(item) for item in tables))


@dataclass(frozen=True)
class PageExtractionRequest:
    """All inputs required to extract one restartable physical page."""

    source_path: Path
    physical_pdf_page: int
    detection: JsonRecord
    cleanup: JsonRecord
    output_root: Path
    route: ExplicitRoute | None
    layout_regions: list[list[float]] | None
    table_id_prefix: str
    retain_review_derivatives: bool
    learned_fallback_runner: LearnedFallbackRunner | None


PageExtractor = Callable[[PageExtractionRequest], PageExtractionResult]
