"""Read deterministic embedded-outline and PDF page-label observations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from pypdf import PdfReader

from er_commons.hierarchy_correction.errors import HierarchyCorrectionContractError
from er_commons.hierarchy_correction.features import normalize_text

JsonObject = dict[str, Any]


def read_pdf_observations(source_pdf: Path) -> tuple[tuple[JsonObject, ...], dict[int, str]]:
    """Read outline nodes and page labels without converting source content."""
    reader = PdfReader(source_pdf, strict=True)
    return extract_outline_observations(reader), extract_page_labels(reader)


def read_native_heading_observations(
    source_pdf: Path, features: list[JsonObject]
) -> dict[str, JsonObject]:
    """Extract independent native text inside each body-heading bbox."""
    document = pdfium.PdfDocument(source_pdf)
    observations: dict[str, JsonObject] = {}
    try:
        by_page: dict[int, list[JsonObject]] = {}
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
        raise HierarchyCorrectionContractError("source PDF page labels are malformed") from error
    if not isinstance(labels, list) or len(labels) != len(reader.pages):
        raise HierarchyCorrectionContractError("source PDF page-label coverage differs")
    if not all(isinstance(label, str) for label in labels):
        raise HierarchyCorrectionContractError("source PDF page label is invalid")
    return {index: label for index, label in enumerate(labels, start=1)}


def extract_outline_observations(reader: Any) -> tuple[JsonObject, ...]:
    """Flatten pypdf's nested outline while retaining parent and raw depth."""
    try:
        outline = reader.outline
    except Exception as error:  # pragma: no cover - pypdf exception types vary by defect
        raise HierarchyCorrectionContractError("source PDF outline is malformed") from error
    if not outline:
        return ()
    if not isinstance(outline, list):
        raise HierarchyCorrectionContractError("source PDF outline is invalid")

    observations: list[JsonObject] = []

    def walk(nodes: list[Any], parent_id: str | None, depth: int, root_depth: int) -> None:
        previous_id: str | None = None
        for node in nodes:
            if isinstance(node, list):
                if previous_id is None:
                    raise HierarchyCorrectionContractError("outline child list has no parent")
                walk(node, previous_id, depth + 1, root_depth)
                continue
            title = getattr(node, "title", None)
            if not isinstance(title, str) or not normalize_text(title):
                raise HierarchyCorrectionContractError("outline title is invalid")
            try:
                page_index = reader.get_destination_page_number(node)
            except Exception as error:
                raise HierarchyCorrectionContractError(
                    "outline destination is malformed"
                ) from error
            if not isinstance(page_index, int) or not 0 <= page_index < len(reader.pages):
                raise HierarchyCorrectionContractError("outline destination page is invalid")
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
    return tuple(observations)
