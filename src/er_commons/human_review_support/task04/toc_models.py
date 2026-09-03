"""Typed domain objects for Task 04A TOC census and review policy.

Persisted review artifacts remain JSON dictionaries.  The rest of the TOC
pipeline should not repeatedly know their field names or silently coerce bad
values, so this module validates that boundary once and exposes named objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from er_commons.human_review_support.task04.json_io import (
    require_integer,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonObject, JsonValue

type PageKey = tuple[str, int]
type TocDisposition = Literal["toc", "not_toc"]


@dataclass(frozen=True)
class TocCandidatePage:
    """One validated candidate page from the source-free TOC census."""

    entry_id: str
    physical_page: int
    signals: frozenset[str]
    adjacent_only: bool
    substantive_table_control: bool
    record: JsonObject

    @classmethod
    def from_json(cls, value: object, *, path: str) -> TocCandidatePage:
        """Validate a persisted candidate page with path-rich diagnostics."""
        record = require_mapping(value, path=path)
        entry_id = require_string(record.get("candidate_page_id"), path=f"{path}.candidate_page_id")
        if not entry_id.startswith("tocpagev1-"):
            raise ValueError(f"expected TOC page identity at {path}.candidate_page_id")
        physical_page = require_integer(
            record.get("physical_page"), path=f"{path}.physical_page", minimum=1
        )
        raw_signals = require_list(record.get("signals"), path=f"{path}.signals")
        signals = frozenset(
            require_string(signal, path=f"{path}.signals[{index}]")
            for index, signal in enumerate(raw_signals)
        )
        return cls(
            entry_id=entry_id,
            physical_page=physical_page,
            signals=signals,
            adjacent_only=_optional_bool(record, "adjacent_only", path),
            substantive_table_control=_optional_bool(record, "substantive_table_control", path),
            record=record,
        )

    def to_json(self) -> JsonObject:
        """Return a detached JSON record safe for queue-specific enrichment."""
        return dict(self.record)


@dataclass(frozen=True)
class TocSourceCensus:
    """Validated TOC candidate pages for one source and machine candidate."""

    source_id: str
    source_ordinal: int | None
    candidate_id: str | None
    pages: tuple[TocCandidatePage, ...]

    @classmethod
    def from_json(cls, value: object, *, index: int) -> TocSourceCensus:
        """Validate one source census read from a Gate A record or fixture."""
        path = f"toc_candidate_census[{index}]"
        record = require_mapping(value, path=path)
        source_id = require_string(record.get("source_id"), path=f"{path}.source_id")
        raw_pages = require_list(record.get("candidate_pages"), path=f"{path}.candidate_pages")
        pages = tuple(
            TocCandidatePage.from_json(page, path=f"{path}.candidate_pages[{page_index}]")
            for page_index, page in enumerate(raw_pages)
        )
        _require_unique_pages(pages, path)
        ordinal = record.get("source_ordinal")
        candidate_id = record.get("candidate_id")
        return cls(
            source_id=source_id,
            source_ordinal=(
                require_integer(ordinal, path=f"{path}.source_ordinal", minimum=1)
                if ordinal is not None
                else None
            ),
            candidate_id=(
                require_string(candidate_id, path=f"{path}.candidate_id")
                if candidate_id is not None
                else None
            ),
            pages=pages,
        )

    def selection_identity(self) -> tuple[int, str]:
        """Return fields required when this census creates review items."""
        if self.source_ordinal is None or self.candidate_id is None:
            raise ValueError(
                f"TOC census for {self.source_id} lacks source_ordinal or candidate_id"
            )
        return self.source_ordinal, self.candidate_id


def parse_toc_censuses(values: object) -> tuple[TocSourceCensus, ...]:
    """Validate an ordered collection of persisted source census records."""
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, Mapping)):
        raise ValueError("expected TOC candidate census array")
    return tuple(
        TocSourceCensus.from_json(value, index=index) for index, value in enumerate(values)
    )


def contiguous_page_runs(
    pages: Iterable[TocCandidatePage],
) -> tuple[tuple[TocCandidatePage, ...], ...]:
    """Split candidate pages into deterministic contiguous physical-page runs."""
    ordered = sorted(pages, key=lambda page: page.physical_page)
    runs: list[list[TocCandidatePage]] = []
    for page in ordered:
        if not runs or page.physical_page != runs[-1][-1].physical_page + 1:
            runs.append([])
        runs[-1].append(page)
    return tuple(tuple(run) for run in runs)


def _require_unique_pages(pages: tuple[TocCandidatePage, ...], path: str) -> None:
    """Reject ambiguous page or entry identities before review selection."""
    entry_ids = [page.entry_id for page in pages]
    physical_pages = [page.physical_page for page in pages]
    if len(entry_ids) != len(set(entry_ids)):
        raise ValueError(f"duplicate candidate page identity at {path}.candidate_pages")
    if len(physical_pages) != len(set(physical_pages)):
        raise ValueError(f"duplicate physical page at {path}.candidate_pages")


def _optional_bool(record: JsonObject, field: str, path: str) -> bool:
    """Read an optional persisted boolean whose historical default is false."""
    value: JsonValue = record.get(field)
    if value is None:
        return False
    if not isinstance(value, bool):
        raise ValueError(f"expected boolean at {path}.{field}")
    return value


__all__ = [
    "PageKey",
    "TocCandidatePage",
    "TocDisposition",
    "TocSourceCensus",
    "contiguous_page_runs",
    "parse_toc_censuses",
]
