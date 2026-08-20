"""Read deterministic embedded-outline and PDF page-label observations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
)

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
_TECHNICAL_FILENAME_CONTAINER = re.compile(
    r"(?:^|[_\s])(?:appendix[_\s]+complete[_\s]+[0-9]+|pages)(?:\.pdf)?$",
    re.IGNORECASE,
)
_RawReferenceKey = tuple[int, int]


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


@dataclass
class _OutlineTreeNode:
    """One parsed pypdf outline node with explicit child ownership."""

    node: Any
    title: str
    page: int | None
    children: list[_OutlineTreeNode] = field(default_factory=list)


@dataclass
class _OutlineCleanResult:
    """Cleaned outline forest plus evidence removed from that forest."""

    nodes: list[_OutlineTreeNode] = field(default_factory=list)
    diagnostics: list[JsonObject] = field(default_factory=list)
    invalid_leaf_titles: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)


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
    malformed_filename_containers = _normalize_malformed_filename_destinations(reader)
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
    if malformed_filename_containers:
        outline, cleanup_diagnostics = _clean_malformed_outline_tree(
            reader=reader,
            outline=outline,
            malformed_filename_containers=malformed_filename_containers,
            heading_features=heading_features or [],
        )
        diagnostics.extend(cleanup_diagnostics)

    def walk(nodes: list[Any], parent_id: str | None, depth: int, root_depth: int) -> None:
        previous_id: str | None = None
        pending_invalid: tuple[Any, str] | None = None
        for node in nodes:
            if isinstance(node, list):
                if previous_id is None:
                    if pending_invalid is None:
                        raise HierarchyInferenceContractError("outline child list has no parent")
                    if _omit_transparent_filename_container(
                        reader=reader,
                        node=pending_invalid[0],
                        title=pending_invalid[1],
                        children=node,
                        malformed_filename_containers=malformed_filename_containers,
                        diagnostics=diagnostics,
                    ):
                        pending_invalid = None
                        walk(node, parent_id, depth, root_depth)
                        continue
                    recovered_id = _recover_appendix_container(
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
                    if recovered_id is None:
                        raise HierarchyInferenceContractError("outline child list has no parent")
                    previous_id = recovered_id
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


def _clean_malformed_outline_tree(
    *,
    reader: Any,
    outline: list[Any],
    malformed_filename_containers: frozenset[_RawReferenceKey],
    heading_features: list[ObservedItem],
) -> tuple[list[Any], list[JsonObject]]:
    """Flatten broken technical folders and remove only evidenced duplicate leaves."""
    trees = _parse_outline_tree(reader, outline)
    valid_titles = {
        normalize_text(node.title) for node in _iter_outline_tree(trees) if node.page is not None
    }
    cleaned = _clean_outline_nodes(
        trees,
        malformed_filename_containers=malformed_filename_containers,
        valid_titles=valid_titles,
        heading_features=heading_features,
        anchored_parent=False,
    )
    return _serialize_outline_tree(cleaned.nodes), cleaned.diagnostics


def _parse_outline_tree(reader: Any, nodes: list[Any]) -> list[_OutlineTreeNode]:
    parsed: list[_OutlineTreeNode] = []
    previous: _OutlineTreeNode | None = None
    for node in nodes:
        if isinstance(node, list):
            if previous is None:
                raise HierarchyInferenceContractError("outline child list has no parent")
            previous.children = _parse_outline_tree(reader, node)
            continue
        title = getattr(node, "title", None)
        if not isinstance(title, str) or not normalize_text(title):
            raise HierarchyInferenceContractError("outline title is invalid")
        parsed_node = _OutlineTreeNode(
            node=node,
            title=title,
            page=_valid_outline_page(reader, node),
        )
        parsed.append(parsed_node)
        previous = parsed_node
    return parsed


def _iter_outline_tree(nodes: list[_OutlineTreeNode]) -> list[_OutlineTreeNode]:
    flattened: list[_OutlineTreeNode] = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_iter_outline_tree(node.children))
    return flattened


def _clean_outline_nodes(
    nodes: list[_OutlineTreeNode],
    *,
    malformed_filename_containers: frozenset[_RawReferenceKey],
    valid_titles: set[str],
    heading_features: list[ObservedItem],
    anchored_parent: bool,
) -> _OutlineCleanResult:
    result = _OutlineCleanResult()
    for tree in nodes:
        supported_container = bool(
            tree.page is None
            and tree.children
            and _is_supported_technical_container(
                tree, malformed_filename_containers=malformed_filename_containers
            )
        )
        if tree.page is None and tree.children and not supported_container:
            result.nodes.append(tree)
            result.pages.extend(
                node.page for node in _iter_outline_tree(tree.children) if node.page is not None
            )
            continue
        children = _clean_outline_nodes(
            tree.children,
            malformed_filename_containers=malformed_filename_containers,
            valid_titles=valid_titles,
            heading_features=heading_features,
            anchored_parent=tree.page is not None,
        )
        if tree.page is not None:
            result.nodes.append(_OutlineTreeNode(tree.node, tree.title, tree.page, children.nodes))
            result.diagnostics.extend(children.diagnostics)
            result.invalid_leaf_titles.extend(children.invalid_leaf_titles)
            result.pages.extend([tree.page, *children.pages])
            continue
        if not tree.children:
            result.invalid_leaf_titles.append(tree.title)
            result.diagnostics.append(_missing_leaf_diagnostic(tree.title))
            continue
        if children.nodes:
            if not children.pages or children.pages != sorted(children.pages):
                raise HierarchyInferenceContractError(
                    "transparent outline container children are unordered"
                )
            result.nodes.extend(children.nodes)
            result.diagnostics.append(
                _container_omission_diagnostic(
                    tree.title,
                    retained_count=len(_iter_outline_tree(children.nodes)),
                    invalid_count=len(children.invalid_leaf_titles),
                    duplicate_subtree=False,
                )
            )
            result.diagnostics.extend(children.diagnostics)
            result.invalid_leaf_titles.extend(children.invalid_leaf_titles)
            result.pages.extend(children.pages)
            continue
        if children.invalid_leaf_titles and all(
            _invalid_leaf_has_replacement(
                title,
                valid_titles=valid_titles,
                heading_features=heading_features,
            )
            for title in children.invalid_leaf_titles
        ):
            result.diagnostics.append(
                _container_omission_diagnostic(
                    tree.title,
                    retained_count=0,
                    invalid_count=len(children.invalid_leaf_titles),
                    duplicate_subtree=True,
                )
            )
            continue
        if anchored_parent and children.invalid_leaf_titles:
            result.diagnostics.append(
                _container_omission_diagnostic(
                    tree.title,
                    retained_count=0,
                    invalid_count=len(children.invalid_leaf_titles),
                    duplicate_subtree=False,
                )
            )
            result.diagnostics.extend(children.diagnostics)
            continue
        raise HierarchyInferenceContractError("outline child list has no parent")
    return result


def _is_supported_technical_container(
    tree: _OutlineTreeNode,
    *,
    malformed_filename_containers: frozenset[_RawReferenceKey],
) -> bool:
    normalized = normalize_text(tree.title)
    return (
        _outline_reference_key(tree.node) in malformed_filename_containers
        or normalized.endswith(".pdf")
        or _TECHNICAL_FILENAME_CONTAINER.search(normalized) is not None
    )


def _invalid_leaf_has_replacement(
    title: str,
    *,
    valid_titles: set[str],
    heading_features: list[ObservedItem],
) -> bool:
    normalized = normalize_text(title)
    if normalized in valid_titles:
        return True
    title_tokens = _semantic_title_tokens(normalized)
    if len(title_tokens) < 3:
        return False
    matches = [
        feature
        for feature in heading_features
        if feature["content_layer"] == "body"
        and feature["raw_role"] == "section_header"
        and title_tokens <= _semantic_title_tokens(feature["normalized_text"])
    ]
    return len(matches) == 1


def _semantic_title_tokens(value: str) -> set[str]:
    return {
        token
        for token in _TITLE_TOKEN.findall(normalize_text(value))
        if token not in _GENERIC_TITLE_TOKENS and not token.isdigit()
    }


def _serialize_outline_tree(nodes: list[_OutlineTreeNode]) -> list[Any]:
    serialized: list[Any] = []
    for tree in nodes:
        serialized.append(tree.node)
        if tree.children:
            serialized.append(_serialize_outline_tree(tree.children))
    return serialized


def _container_omission_diagnostic(
    title: str,
    *,
    retained_count: int,
    invalid_count: int,
    duplicate_subtree: bool,
) -> JsonObject:
    if duplicate_subtree:
        detail = (
            f"Omitted duplicate broken outline subtree '{title}'; all {invalid_count} "
            "invalid leaf bookmarks have valid duplicate or unique visible-heading evidence."
        )
    else:
        detail = (
            f"Omitted technical filename container '{title}' and retained "
            f"{retained_count} ordered descendant bookmarks; {invalid_count} invalid "
            "leaf bookmarks remain omissions."
        )
    return {
        "reading_order_index": None,
        "stable_item_key": None,
        "code": "OUTLINE_FILENAME_CONTAINER_OMITTED",
        "detail": detail,
    }


def _omit_transparent_filename_container(
    *,
    reader: Any,
    node: Any,
    title: str,
    children: list[Any],
    malformed_filename_containers: frozenset[_RawReferenceKey],
    diagnostics: list[JsonObject],
) -> bool:
    """Flatten one supported PDF-filename folder while preserving valid children."""
    malformed_destination = _outline_reference_key(node) in malformed_filename_containers
    if not normalize_text(title).endswith(".pdf") or (
        not malformed_destination
        and (
            _appendix_identifier(title) is not None or _DISTINCTIVE_NUMBER.search(title) is not None
        )
    ):
        return False
    direct_children = [child for child in children if not isinstance(child, list)]
    child_pages = [_valid_outline_page(reader, child) for child in direct_children]
    if not malformed_destination and any(page is None for page in child_pages):
        return False
    pages = [page for page in child_pages if page is not None]
    if not pages or pages != sorted(pages):
        return False
    missing_count = sum(page is None for page in child_pages)
    diagnostics.append(
        {
            "reading_order_index": None,
            "stable_item_key": None,
            "code": "OUTLINE_FILENAME_CONTAINER_OMITTED",
            "detail": (
                f"Omitted {'malformed' if malformed_destination else 'destinationless'} "
                f"PDF filename container '{title}' and flattened {len(pages)} ordered "
                f"child bookmarks"
                + (
                    f"; {missing_count} invalid child bookmarks remain leaf omissions."
                    if missing_count
                    else "."
                )
            ),
        }
    )
    return True


def _normalize_malformed_filename_destinations(
    reader: Any,
) -> frozenset[_RawReferenceKey]:
    """Make null-page numeric-fit filename containers readable in memory only."""
    try:
        root = _resolve_pdf_object(reader.trailer["/Root"])
        outlines = _resolve_pdf_object(root.get("/Outlines"))
        first = outlines.get("/First")
    except (AttributeError, KeyError, TypeError):
        return frozenset()
    if first is None:
        return frozenset()

    normalized: set[_RawReferenceKey] = set()
    visited: set[_RawReferenceKey | tuple[str, int]] = set()

    def walk(first_reference: Any) -> None:
        current = first_reference
        while current is not None:
            reference_key = _raw_object_key(current)
            if reference_key in visited:
                raise HierarchyInferenceContractError("source PDF outline contains a cycle")
            visited.add(reference_key)
            node = _resolve_pdf_object(current)
            if not hasattr(node, "get"):
                raise HierarchyInferenceContractError("source PDF outline node is invalid")
            title = node.get("/Title")
            destination = _resolve_pdf_object(node.get("/Dest"))
            if _is_malformed_filename_destination(title, destination, node.get("/First")):
                node[NameObject("/Dest")] = ArrayObject([NullObject(), NameObject("/Fit")])
                indirect_key = _indirect_reference_key(current)
                if indirect_key is None:
                    raise HierarchyInferenceContractError(
                        "malformed outline filename container is not indirect"
                    )
                normalized.add(indirect_key)
            child = node.get("/First")
            if child is not None:
                walk(child)
            current = node.get("/Next")

    walk(first)
    return frozenset(normalized)


def _is_malformed_filename_destination(title: Any, destination: Any, first_child: Any) -> bool:
    """Recognize the bounded null-page/numeric-fit container defect."""
    return (
        isinstance(title, str)
        and normalize_text(title).endswith(".pdf")
        and first_child is not None
        and isinstance(destination, (list, ArrayObject))
        and len(destination) >= 2
        and isinstance(_resolve_pdf_object(destination[0]), NullObject)
        and isinstance(destination[1], (FloatObject, NumberObject))
    )


def _resolve_pdf_object(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def _indirect_reference_key(value: Any) -> _RawReferenceKey | None:
    if not isinstance(value, IndirectObject):
        return None
    return (value.idnum, value.generation)


def _raw_object_key(value: Any) -> _RawReferenceKey | tuple[str, int]:
    return _indirect_reference_key(value) or ("direct", id(value))


def _outline_reference_key(value: Any) -> _RawReferenceKey | None:
    return _indirect_reference_key(getattr(value, "indirect_reference", None))


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
) -> str | None:
    """Bind one non-clickable container using unique adjacent-page evidence."""
    direct_children = [child for child in children if not isinstance(child, list)]
    child_pages = [_valid_outline_page(reader, child) for child in direct_children]
    if any(page is None for page in child_pages):
        return None
    pages = [page for page in child_pages if page is not None]
    if not pages or pages != sorted(pages) or pages[0] <= 1:
        return None
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
        return None
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
    diagnostics.append(_missing_leaf_diagnostic(title))


def _missing_leaf_diagnostic(title: str) -> JsonObject:
    return {
        "reading_order_index": None,
        "stable_item_key": None,
        "code": "TOC_TARGET_MISSING",
        "detail": f"PDF outline leaf has no valid destination and was omitted: {title}",
    }
