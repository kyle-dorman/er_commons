"""Read deterministic embedded-outline and PDF page-label observations."""

from __future__ import annotations

import re
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
_APPENDIX_IDENTIFIER = re.compile(r"\bappendix\s+(?P<identifier>[a-z0-9]+)\b", re.IGNORECASE)
_COMPACT_APPENDIX_IDENTIFIER = re.compile(
    r"\bapp(?P<identifier>[a-z])(?=[^a-z0-9]|$)", re.IGNORECASE
)
_DISTINCTIVE_NUMBER = re.compile(r"[0-9]{4,}")
_TITLE_TOKEN = re.compile(r"[a-z0-9]+")
_GENERIC_TITLE_TOKENS = frozenset(
    {"appendix", "app", "pdf", "final", "report", "reports", "rpt", "rpts"}
)


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


def extract_outline_observations(
    reader: Any, *, heading_features: list[ObservedItem] | None = None
) -> OutlineExtraction:
    """Flatten outline nodes and recover strictly evidenced appendix containers."""
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
        pending_invalid: tuple[Any, str] | None = None
        for node in nodes:
            if isinstance(node, list):
                if previous_id is None:
                    if pending_invalid is None:
                        raise HierarchyInferenceContractError("outline child list has no parent")
                    previous_id = _recover_appendix_container(
                        reader=reader,
                        node=pending_invalid[0],
                        title=pending_invalid[1],
                        children=node,
                        parent_id=parent_id,
                        depth=depth,
                        root_depth=root_depth,
                        heading_features=heading_features or [],
                        observations=observations,
                        diagnostics=diagnostics,
                    )
                    pending_invalid = None
                walk(node, previous_id, depth + 1, root_depth)
                continue
            if pending_invalid is not None:
                _diagnose_missing_leaf(diagnostics, pending_invalid[1])
                pending_invalid = None
            title = getattr(node, "title", None)
            if not isinstance(title, str) or not normalize_text(title):
                raise HierarchyInferenceContractError("outline title is invalid")
            try:
                page_index = reader.get_destination_page_number(node)
            except Exception as error:
                raise HierarchyInferenceContractError("outline destination is malformed") from error
            if not isinstance(page_index, int) or not 0 <= page_index < len(reader.pages):
                pending_invalid = (node, title)
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
        if pending_invalid is not None:
            _diagnose_missing_leaf(diagnostics, pending_invalid[1])

    walk(outline, None, 1, 1)
    return OutlineExtraction(tuple(observations), tuple(diagnostics))


def _recover_appendix_container(
    *,
    reader: Any,
    node: Any,
    title: str,
    children: list[Any],
    parent_id: str | None,
    depth: int,
    root_depth: int,
    heading_features: list[ObservedItem],
    observations: list[JsonObject],
    diagnostics: list[JsonObject],
) -> str:
    """Bind one non-clickable container using unique adjacent-page evidence."""
    direct_children = [child for child in children if not isinstance(child, list)]
    child_pages = [_valid_outline_page(reader, child) for child in direct_children]
    if any(page is None for page in child_pages):
        raise HierarchyInferenceContractError("outline child list has no parent")
    pages = [page for page in child_pages if page is not None]
    if not pages or pages != sorted(pages) or pages[0] <= 1:
        raise HierarchyInferenceContractError("outline child list has no parent")
    identifier = _appendix_identifier(title)
    preceding_page = pages[0] - 1
    matches = [
        feature
        for feature in heading_features
        if feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and feature["physical_page"] == preceding_page
        and _appendix_identifier(feature["text"]) == identifier
    ]
    if identifier is not None and len(matches) == 1:
        match = matches[0]
        return _append_recovered_container(
            title=title,
            normalized_title=match["normalized_text"],
            physical_page=preceding_page,
            parent_id=parent_id,
            depth=depth,
            root_depth=root_depth,
            observations=observations,
            diagnostics=diagnostics,
            reading_order_index=match["reading_order_index"],
            stable_item_key=match["stable_item_key"],
            evidence=(
                f"unique appendix identifier '{identifier}' and "
                f"{len(children)} ordered child destinations"
            ),
        )

    native_matches = [
        (page, text)
        for page in (preceding_page, pages[0])
        if (text := _native_page_text(reader, page)) and _fuzzy_container_title_matches(title, text)
    ]
    if len(native_matches) != 1:
        raise HierarchyInferenceContractError("outline child list has no parent")
    candidate_page, native_text = native_matches[0]
    return _append_recovered_container(
        title=title,
        normalized_title=normalize_text(title),
        physical_page=candidate_page,
        parent_id=parent_id,
        depth=depth,
        root_depth=root_depth,
        observations=observations,
        diagnostics=diagnostics,
        reading_order_index=None,
        stable_item_key=None,
        evidence=(
            "unique fuzzy title evidence on the preceding or first-child page "
            f"({len(native_text)} native characters)"
        ),
    )


def _append_recovered_container(
    *,
    title: str,
    normalized_title: str,
    physical_page: int,
    parent_id: str | None,
    depth: int,
    root_depth: int,
    observations: list[JsonObject],
    diagnostics: list[JsonObject],
    reading_order_index: int | None,
    stable_item_key: str | None,
    evidence: str,
) -> str:
    """Append one uniquely evidenced synthetic outline parent."""
    outline_id = f"outline-{len(observations):08d}"
    observations.append(
        {
            "outline_id": outline_id,
            "parent_outline_id": parent_id,
            "title": title,
            "normalized_title": normalized_title,
            "physical_page": physical_page,
            "raw_depth": depth,
            "source_root_depth": root_depth,
            "effective_level": min(6, depth - root_depth + 1),
        }
    )
    diagnostics.append(
        {
            "reading_order_index": reading_order_index,
            "stable_item_key": stable_item_key,
            "code": "OUTLINE_CONTAINER_RECOVERED",
            "detail": (
                f"Bound destinationless PDF outline container '{title}' to physical page "
                f"{physical_page} from {evidence}."
            ),
        }
    )
    return outline_id


def _valid_outline_page(reader: Any, node: Any) -> int | None:
    if isinstance(node, list):
        return None
    try:
        page_index = reader.get_destination_page_number(node)
    except Exception:
        return None
    return (
        page_index + 1
        if isinstance(page_index, int) and 0 <= page_index < len(reader.pages)
        else None
    )


def _appendix_identifier(value: str) -> str | None:
    match = _APPENDIX_IDENTIFIER.search(normalize_text(value))
    if match is not None:
        return match.group("identifier")
    compact_match = _COMPACT_APPENDIX_IDENTIFIER.search(normalize_text(value))
    return compact_match.group("identifier") if compact_match is not None else None


def _native_page_text(reader: Any, physical_page: int) -> str:
    """Return normalized native text for one narrowly selected candidate page."""
    try:
        text = reader.pages[physical_page - 1].extract_text()
    except (AttributeError, IndexError, TypeError):
        return ""
    return normalize_text(text) if isinstance(text, str) else ""


def _fuzzy_container_title_matches(title: str, page_text: str) -> bool:
    """Require distinctive numeric or appendix-plus-token agreement."""
    title_digits = set(_DISTINCTIVE_NUMBER.findall(title))
    page_digits = set(_DISTINCTIVE_NUMBER.findall(page_text))
    if title_digits & page_digits:
        return True
    identifier = _appendix_identifier(title)
    if identifier is None or _appendix_identifier(page_text) != identifier:
        return False
    expanded_title = normalize_text(title).replace("datavalrpts", "data validation reports")
    title_tokens = set(_TITLE_TOKEN.findall(expanded_title)) - _GENERIC_TITLE_TOKENS
    page_tokens = set(_TITLE_TOKEN.findall(page_text))
    expanded_title_tokens = {
        "validation" if token == "val" else "reports" if token == "rpts" else token
        for token in title_tokens
    }
    return len(expanded_title_tokens & page_tokens) >= 2


def _diagnose_missing_leaf(diagnostics: list[JsonObject], title: str) -> None:
    diagnostics.append(
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "TOC_TARGET_MISSING",
            "detail": f"PDF outline leaf has no valid destination and was omitted: {title}",
        }
    )
