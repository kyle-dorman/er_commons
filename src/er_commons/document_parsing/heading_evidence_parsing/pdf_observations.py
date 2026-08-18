"""Read deterministic embedded-outline and PDF page-label observations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from pypdf import PdfReader

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class OutlineExtraction:
    """Usable outline nodes plus explicit evidence omitted as invalid leaves."""

    observations: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]


@dataclass(frozen=True)
class PdfObservations:
    """Independent source-PDF observations consumed by hierarchy correction."""

    outline_observations: tuple[JsonObject, ...]
    page_labels: dict[int, str]
    diagnostics: tuple[JsonObject, ...]


def read_pdf_observations(source_pdf: Path) -> PdfObservations:
    """Read outline nodes and page labels without converting source content."""
    reader = PdfReader(source_pdf, strict=True)
    outline = extract_outline_observations(reader)
    return PdfObservations(
        outline_observations=outline.observations,
        page_labels=extract_page_labels(reader),
        diagnostics=outline.diagnostics,
    )


def read_native_heading_observations(
    source_pdf: Path, features: list[ObservedItem]
) -> dict[str, JsonObject]:
    """Extract independent native text inside each body-heading bbox."""
    document = pdfium.PdfDocument(source_pdf)
    observations: dict[str, JsonObject] = {}
    try:
        by_page: dict[int, list[ObservedItem]] = {}
        for feature in features:
            if feature["content_layer"] == "body" and feature["raw_role"] == "section_header":
                by_page.setdefault(int(feature["physical_page"]), []).append(feature)
        for physical_page, page_features in by_page.items():
            page = document[physical_page - 1]
            text_page = page.get_textpage()
            try:
                for feature in page_features:
                    bbox = feature["bbox"]
                    native_text = text_page.get_text_bounded(
                        left=bbox["l"],
                        bottom=bbox["b"],
                        right=bbox["r"],
                        top=bbox["t"],
                    )
                    observations[feature["stable_item_key"]] = {
                        "physical_page": physical_page,
                        "bbox": dict(bbox),
                        "normalized_text": normalize_text(native_text),
                    }
            finally:
                text_page.close()
                page.close()
    finally:
        document.close()
    return observations


def extract_page_labels(reader: Any) -> dict[int, str]:
    """Map one-based physical pages to retained pypdf page-label strings."""
    try:
        labels = reader.page_labels
    except Exception as error:  # pragma: no cover - pypdf exception types vary by defect
        raise HierarchyInferenceContractError("source PDF page labels are malformed") from error
    if not isinstance(labels, list) or len(labels) != len(reader.pages):
        raise HierarchyInferenceContractError("source PDF page-label coverage differs")
    if not all(isinstance(label, str) for label in labels):
        raise HierarchyInferenceContractError("source PDF page label is invalid")
    return {index: label for index, label in enumerate(labels, start=1)}


def extract_outline_observations(reader: Any) -> OutlineExtraction:
    """Flatten valid outline nodes and diagnose destinationless leaf entries."""
    try:
        outline = reader.outline
    except Exception as error:  # pragma: no cover - pypdf exception types vary by defect
        raise HierarchyInferenceContractError("source PDF outline is malformed") from error
    if not outline:
        return OutlineExtraction((), ())
    if not isinstance(outline, list):
        raise HierarchyInferenceContractError("source PDF outline is invalid")

    observations: list[JsonObject] = []
    diagnostics: list[JsonObject] = []

    def walk(nodes: list[Any], parent_id: str | None, depth: int, root_depth: int) -> None:
        previous_id: str | None = None
        for node in nodes:
            if isinstance(node, list):
                if previous_id is None:
                    raise HierarchyInferenceContractError("outline child list has no parent")
                walk(node, previous_id, depth + 1, root_depth)
                continue
            title = getattr(node, "title", None)
            if not isinstance(title, str) or not normalize_text(title):
                raise HierarchyInferenceContractError("outline title is invalid")
            try:
                page_index = reader.get_destination_page_number(node)
            except Exception as error:
                raise HierarchyInferenceContractError("outline destination is malformed") from error
            if not isinstance(page_index, int) or not 0 <= page_index < len(reader.pages):
                diagnostics.append(
                    {
                        "reading_order_index": None,
                        "stable_item_key": None,
                        "code": "TOC_TARGET_MISSING",
                        "detail": (
                            f"PDF outline leaf has no valid destination and was omitted: {title}"
                        ),
                    }
                )
                previous_id = None
                continue
            outline_id = f"outline-{len(observations):08d}"
            observations.append(
                {
                    "outline_id": outline_id,
                    "parent_outline_id": parent_id,
                    "title": title,
                    "normalized_title": normalize_text(title),
                    "physical_page": page_index + 1,
                    "raw_depth": depth,
                    "source_root_depth": root_depth,
                    "effective_level": min(6, depth - root_depth + 1),
                }
            )
            previous_id = outline_id

    walk(outline, None, 1, 1)
    return OutlineExtraction(tuple(observations), tuple(diagnostics))
