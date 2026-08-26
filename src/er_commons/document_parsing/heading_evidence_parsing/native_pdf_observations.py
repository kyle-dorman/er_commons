"""Read page-label and bounded native-text evidence from source PDFs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from er_commons.document_parsing.heading_evidence_parsing.errors import (
    HierarchyInferenceContractError,
)
from er_commons.document_parsing.heading_evidence_parsing.outline_types import JsonObject
from er_commons.document_parsing.heading_evidence_parsing.text_evidence import normalize_text
from er_commons.document_parsing.heading_evidence_parsing.types import ObservedItem


def read_native_heading_observations(
    source_pdf: Path, features: list[ObservedItem]
) -> dict[str, JsonObject]:
    """Extract independent native text inside each body-heading bbox."""
    document = pdfium.PdfDocument(source_pdf)
    observations: dict[str, JsonObject] = {}
    try:
        for physical_page, page_features in _body_headings_by_page(features).items():
            page = document[physical_page - 1]
            text_page = page.get_textpage()
            try:
                for feature in page_features:
                    bbox = feature["bbox"]
                    native_text = text_page.get_text_bounded(
                        left=bbox["l"], bottom=bbox["b"], right=bbox["r"], top=bbox["t"]
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


def _body_headings_by_page(features: list[ObservedItem]) -> dict[int, list[ObservedItem]]:
    by_page: dict[int, list[ObservedItem]] = {}
    for feature in features:
        if feature["content_layer"] == "body" and feature["raw_role"] == "section_header":
            by_page.setdefault(int(feature["physical_page"]), []).append(feature)
    return by_page


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
