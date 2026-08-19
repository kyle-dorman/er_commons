"""Build and consume the sole MVP hierarchy-alignment input."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from er_commons.artifact_io import atomic_text_writer, iter_jsonl
from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import (
    LayoutEvidence,
    normalize_text,
)

AlignmentState = Literal["unique_aligned", "ambiguous"]
JsonObject = dict[str, Any]
SCHEMA_VERSION = "er_commons.hierarchy_alignment_page.v1"


@dataclass(frozen=True)
class AlignmentPage:
    """One page's dimensions and normalized constant-time alignment index."""

    page_no: int
    width: float
    height: float
    index: dict[str, LayoutEvidence]

    def lookup(self, text: str) -> LayoutEvidence:
        """Return current exact alignment semantics without scanning page cells."""
        return self.index.get(normalize_text(text), LayoutEvidence("absent", None))


def alignment_record(
    *,
    page_no: int,
    width: float,
    height: float,
    textline_cells: list[Any],
) -> JsonObject:
    """Project one parsed page into deterministic normalized alignment entries."""
    index: dict[str, LayoutEvidence] = {}
    for cell in textline_cells:
        text = _cell_text(cell)
        normalized = normalize_text(text)
        if normalized in index:
            index[normalized] = LayoutEvidence("ambiguous", None)
        else:
            line_count = len([line for line in text.splitlines() if line.strip()]) or 1
            index[normalized] = LayoutEvidence("unique_aligned", line_count)
    return {
        "schema_version": SCHEMA_VERSION,
        "page_no": page_no,
        "width": width,
        "height": height,
        "alignment_index": [
            [text, evidence.state, evidence.line_count] for text, evidence in sorted(index.items())
        ],
    }


def result_alignment_records(result: Any) -> Iterator[JsonObject]:
    """Project in-memory Docling pages before transient conversion state is released."""
    for expected, page in enumerate(result.pages, start=1):
        if int(page.page_no) != expected or page.size is None or page.parsed_page is None:
            raise ValueError(f"Docling alignment page is incomplete or unordered: {expected}")
        yield alignment_record(
            page_no=expected,
            width=float(page.size.width),
            height=float(page.size.height),
            textline_cells=list(page.parsed_page.textline_cells),
        )


def write_result_alignment_projection(result: Any, path: Path) -> int:
    """Write one compact JSON record per in-memory Docling page."""
    count = 0
    with atomic_text_writer(path) as stream:
        for record in result_alignment_records(result):
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            stream.write("\n")
            count += 1
        return count


def load_alignment_projection(path: Path, *, expected_page_count: int) -> dict[int, AlignmentPage]:
    """Load and strictly validate the bounded page-alignment projection."""
    pages: dict[int, AlignmentPage] = {}
    for expected, record in enumerate(iter_jsonl(path), start=1):
        page = _parse_alignment_page(record, path)
        if page.page_no != expected:
            raise HierarchyInferenceContractError(
                f"alignment page order differs at {path}: {page.page_no} != {expected}"
            )
        pages[page.page_no] = page
    if len(pages) != expected_page_count:
        raise HierarchyInferenceContractError(
            f"alignment page coverage differs at {path}: {len(pages)} != {expected_page_count}"
        )
    return pages


def _parse_alignment_page(record: JsonObject, path: Path) -> AlignmentPage:
    if record.get("schema_version") != SCHEMA_VERSION:
        raise HierarchyInferenceContractError(f"alignment schema differs at {path}")
    page_no = record.get("page_no")
    width = record.get("width")
    height = record.get("height")
    entries = record.get("alignment_index")
    if (
        not isinstance(page_no, int)
        or not isinstance(width, int | float)
        or not isinstance(height, int | float)
        or not isinstance(entries, list)
    ):
        raise HierarchyInferenceContractError(f"alignment page record is invalid at {path}")
    index: dict[str, LayoutEvidence] = {}
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 3:
            raise HierarchyInferenceContractError(f"alignment index entry is invalid at {path}")
        text, state, line_count = entry
        if (
            not isinstance(text, str)
            or state not in {"unique_aligned", "ambiguous"}
            or (line_count is not None and not isinstance(line_count, int))
            or (state == "ambiguous" and line_count is not None)
            or text in index
        ):
            raise HierarchyInferenceContractError(f"alignment index semantics differ at {path}")
        index[text] = LayoutEvidence(state, line_count)
    return AlignmentPage(page_no, float(width), float(height), index)


def _cell_text(cell: Any) -> str:
    if isinstance(cell, dict):
        text = cell.get("text")
    else:
        text = getattr(cell, "text", None)
    if not isinstance(text, str):
        raise ValueError("parsed-page textline cell has no text")
    return text


__all__ = [
    "AlignmentPage",
    "SCHEMA_VERSION",
    "alignment_record",
    "load_alignment_projection",
    "result_alignment_records",
    "write_result_alignment_projection",
]
