"""Internal records shared by the region-bounded Stream fallback."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.document_parsing.table_reconstruction.learned_table_types import JsonObject

TableRows = Callable[[Any], list[list[str]]]
CleanRows = Callable[[list[list[str]], JsonObject], tuple[list[list[str]], JsonObject]]


@dataclass(frozen=True)
class RegionStreamContext:
    """Stable page inputs and callbacks needed to evaluate one layout region."""

    pdf_path: Path
    page_number: int
    page_size: tuple[float, float]
    detection: JsonObject
    cleanup: JsonObject
    table_rows: TableRows
    clean_rows: CleanRows


@dataclass(frozen=True)
class RegionStreamResult:
    """One accepted or abstained result with its unchanged evidence representation."""

    region_id: str
    status: Literal["accepted", "abstained"]
    reason: str | None
    measurements: JsonObject
    candidate: JsonObject | None = None

    @classmethod
    def abstained(
        cls,
        region_id: str,
        reason: str,
        measurements: JsonObject,
    ) -> RegionStreamResult:
        """Create an abstention without repeating evidence dictionary construction."""
        return cls(region_id, "abstained", reason, measurements)

    @classmethod
    def accepted(
        cls,
        region_id: str,
        measurements: JsonObject,
        candidate: JsonObject,
    ) -> RegionStreamResult:
        """Create an accepted result without changing serialized field names."""
        return cls(region_id, "accepted", None, measurements, candidate)

    def evidence(self) -> JsonObject:
        """Return the legacy evidence shape consumed by downstream publication."""
        return {
            "region_id": self.region_id,
            "status": self.status,
            "reason": self.reason,
            "measurements": self.measurements,
        }


__all__ = ["CleanRows", "RegionStreamContext", "RegionStreamResult", "TableRows"]
