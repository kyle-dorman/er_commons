"""Project sealed Docling document-index cells into a readable TOC text view."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    canonical_json_sha256,
    file_reference,
    read_json_object,
    sha256_file,
)

JsonObject = dict[str, Any]

PARSER_VERSION = "docling_document_index_text_v1"
_MODEL_DOT_LEADERS = re.compile(r"\.{2,}")
_LEADER_DESTINATION = re.compile(
    r"\.{2,}\s*(?P<label>[a-z]*\d+(?:\.\d+)*(?:-\d+)*|[ivxlcdm]+)\s*$",
    re.IGNORECASE,
)
_SPACE_DESTINATION = re.compile(
    r"\s(?P<label>[a-z]*\d+(?:\.\d+)*(?:-\d+)*|[ivxlcdm]+)\s*$",
    re.IGNORECASE,
)
_PAGE_TOKEN = re.compile(r"(?:[a-z]*\d+(?:\.\d+)*(?:-\d+)*|[ivxlcdm]+)", re.IGNORECASE)
_DECIMAL_START = re.compile(r"^\d+(?:\s*\.\s*\d+)+(?=\s|$)")
_CATALOG_START = re.compile(
    r"^(?P<kind>table|figure)\s+(?P<marker>[a-z0-9]+(?:[.-][a-z0-9]+)*)\s*:?",
    re.IGNORECASE,
)
_OUTLINE_START = re.compile(
    r"^(?:\d+(?:\s*\.\s*\d+)+|\d+\.|[a-z]\.|chapter\s+\d+|"
    r"\d{2}\s*\||appendices\b|appendix\s+[a-z]\b)",
    re.IGNORECASE,
)
_RUNNING_FURNITURE = re.compile(r"^DRAFT ENVIRONMENTAL IMPACT REPORT VOLUME \d+$", re.I)


@dataclass(frozen=True)
class TocTextProjection:
    """One effective text page and its ordered logical TOC entries."""

    page: JsonObject
    entries: list[JsonObject]
    sealed_reference: JsonObject


@dataclass
class _Line:
    cells: list[JsonObject]
    baseline: float
    baseline_min: float
    baseline_max: float


def project_toc_text(
    *,
    data_root: Path,
    task03j_root: Path,
    document_root: Path,
    source_id: str,
    candidate_id: str,
    source_page_id: str,
    physical_page: int,
    source_table_id: str,
    table_disposition_id: str,
) -> TocTextProjection:
    """Build a source-free TOC view from the core-owned sealed range page."""
    evidence, raw_page = _load_sealed_raw_page(
        data_root=data_root,
        task03j_root=task03j_root,
        document_root=document_root,
        source_id=source_id,
        physical_page=physical_page,
    )
    elements = [
        row
        for row in cast(list[JsonObject], cast(JsonObject, raw_page["assembled"])["elements"])
        if row.get("label") == "document_index"
    ]
    _require(len(elements) == 1, f"expected one document_index on page {physical_page}")
    element = elements[0]
    cluster = cast(JsonObject, element["cluster"])
    cells = cast(list[JsonObject], cluster["cells"])
    _validate_cells(cells)
    lines = _reconstruct_lines(cells)
    document_index_bbox = cast(JsonObject, cluster["bbox"])
    right_edge = float(document_index_bbox["r"])
    entry_lines = _segment_entries(lines, right_edge=right_edge)
    page_identity = {
        "source_id": source_id,
        "candidate_id": candidate_id,
        "physical_page": physical_page,
        "source_table_id": source_table_id,
        "raw_page_sha256": cast(JsonObject, evidence["page_record"])["sha256"],
        "parser_version": PARSER_VERSION,
    }
    page_id = f"navtocpagev1-{canonical_json_sha256(page_identity)[:24]}"
    entries: list[JsonObject] = []
    for entry_index, grouped in enumerate(entry_lines):
        raw_lines = [_line_text(line.cells) for line in grouped]
        raw_text = " ".join(raw_lines)
        marker_kind, raw_marker, normalized_marker = _marker(raw_text)
        destination = _destination(grouped[-1].cells, right_edge=right_edge)
        cell_indices = [int(cell["index"]) for line in grouped for cell in line.cells]
        cell_text = [str(cell["text"]) for line in grouped for cell in line.cells]
        entry_identity = {
            "toc_text_page_id": page_id,
            "entry_index": entry_index,
            "source_cell_indices": cell_indices,
            "source_cell_text_sha256": canonical_json_sha256(cell_text),
        }
        entry_id = f"navtocentryv1-{canonical_json_sha256(entry_identity)[:24]}"
        line_start = lines.index(grouped[0])
        line_end = lines.index(grouped[-1])
        entries.append(
            {
                "schema_version": "er_commons.navigation_overlay.v1.toc_text_entry",
                "link_view_id": "navlinkv1-" + "0" * 64,
                "semantic_view_id": "navsemanticv1-" + "0" * 64,
                "overlay_plan_id": "navoverlayplanv1-" + "0" * 64,
                "toc_text_entry_id": entry_id,
                "toc_text_page_id": page_id,
                "source_id": source_id,
                "candidate_id": candidate_id,
                "source_page_id": source_page_id,
                "physical_page": physical_page,
                "source_table_id": source_table_id,
                "table_disposition_id": table_disposition_id,
                "entry_index": entry_index,
                "entry_locator": {
                    "line_start": line_start,
                    "line_end": line_end,
                    "source_cell_indices": cell_indices,
                    "source_cell_text_sha256": entry_identity["source_cell_text_sha256"],
                },
                "raw_lines": raw_lines,
                "raw_text": raw_text,
                "model_text": _model_text(raw_text),
                "marker_kind": marker_kind,
                "raw_marker": raw_marker,
                "normalized_marker": normalized_marker,
                "terminal_destination_token": destination,
                "parser_version": PARSER_VERSION,
                "warnings": [],
            }
        )
    line_records = [
        {
            "line_index": index,
            "text": _line_text(line.cells),
            "bbox": _union_bbox(line.cells),
            "cell_indices": [int(cell["index"]) for cell in line.cells],
        }
        for index, line in enumerate(lines)
    ]
    page = {
        "schema_version": "er_commons.navigation_overlay.v1.toc_text_page",
        "link_view_id": "navlinkv1-" + "0" * 64,
        "semantic_view_id": "navsemanticv1-" + "0" * 64,
        "overlay_plan_id": "navoverlayplanv1-" + "0" * 64,
        "toc_text_page_id": page_id,
        "source_id": source_id,
        "candidate_id": candidate_id,
        "source_page_id": source_page_id,
        "physical_page": physical_page,
        "source_table_id": source_table_id,
        "table_disposition_id": table_disposition_id,
        "representation": "docling_text_supersedes_canonical_table_for_effective_navigation_view",
        "parser_version": PARSER_VERSION,
        "raw_docling_evidence": {
            **evidence,
            "document_index_element_id": element["id"],
            "document_index_bbox": cluster["bbox"],
            "cell_count": len(cells),
        },
        "lines": line_records,
        "entry_ids": [row["toc_text_entry_id"] for row in entries],
        "model_text": "\n".join(str(row["model_text"]) for row in entries),
        "warnings": [],
    }
    return TocTextProjection(page=page, entries=entries, sealed_reference=evidence)


def _load_sealed_raw_page(
    *,
    data_root: Path,
    task03j_root: Path,
    document_root: Path,
    source_id: str,
    physical_page: int,
) -> tuple[JsonObject, JsonObject]:
    identity_path = document_root / "records/document_identity.json"
    identity = read_json_object(identity_path)
    completions = cast(JsonObject, identity["stage_completions"])
    stable_ref = cast(JsonObject, completions["stable_content_evidence"])
    stable_completion_path = data_root / str(stable_ref["path"])
    _verify_reference(stable_completion_path, stable_ref)
    stable_root = stable_completion_path.parent.parent
    stable_completion = read_json_object(stable_completion_path)
    stable_inventory_path = stable_root / str(stable_completion["artifact_inventory"])
    _require(
        sha256_file(stable_inventory_path) == stable_completion["artifact_inventory_sha256"],
        "stable-content inventory seal differs",
    )
    stable_files = _inventory_files(stable_inventory_path)
    conversion_input_path = stable_root / "records/conversion_input.json"
    _verify_inventory_member(conversion_input_path, stable_root, stable_files)
    conversion_ref = read_json_object(conversion_input_path)
    conversion_root = data_root / str(conversion_ref["path"])
    completion_path = data_root / str(conversion_ref["completion_path"])
    inventory_path = data_root / str(conversion_ref["inventory_path"])
    _require(
        sha256_file(completion_path) == conversion_ref["completion_sha256"]
        and sha256_file(inventory_path) == conversion_ref["inventory_sha256"],
        "accepted Docling conversion seal differs",
    )
    conversion_files = _inventory_files(inventory_path)
    aggregate_path = conversion_root / "records/aggregate_observation.json"
    _verify_inventory_member(aggregate_path, conversion_root, conversion_files)
    aggregate = read_json_object(aggregate_path)
    owners = [
        row
        for row in cast(list[JsonObject], aggregate["child_observations"])
        if int(cast(JsonObject, row["core"])["start"])
        <= physical_page
        <= int(cast(JsonObject, row["core"])["end"])
    ]
    _require(len(owners) == 1, f"page {physical_page} lacks one core-owned Docling range")
    plan_id = str(aggregate["plan_id"])
    range_id = str(owners[0]["range_id"])
    parse_root = task03j_root / "document_parse_evidence"
    range_root = parse_root / "chunked_runs/plans" / plan_id / "ranges" / range_id
    range_completion_path = range_root / "records/completion_record.json"
    range_inventory_path = range_root / "records/artifact_inventory.json"
    range_completion = read_json_object(range_completion_path)
    _require(
        range_completion.get("plan_id") == plan_id
        and range_completion.get("range_id") == range_id
        and cast(JsonObject, range_completion.get("source", {})).get("source_id") == source_id,
        "raw Docling range identity differs",
    )
    _require(
        sha256_file(range_inventory_path) == range_completion["artifact_inventory_sha256"],
        "raw Docling range inventory seal differs",
    )
    range_files = _inventory_files(range_inventory_path)
    page_path = range_root / f"pages/p{physical_page:05d}.json"
    _verify_inventory_member(page_path, range_root, range_files)
    page_record = file_reference(page_path, root=data_root)
    evidence = {
        "plan_id": plan_id,
        "range_id": range_id,
        "candidate_identity": file_reference(identity_path, root=data_root),
        "stable_content_completion": file_reference(stable_completion_path, root=data_root),
        "stable_content_inventory": file_reference(stable_inventory_path, root=data_root),
        "conversion_input": file_reference(conversion_input_path, root=data_root),
        "conversion_completion": file_reference(completion_path, root=data_root),
        "conversion_inventory": file_reference(inventory_path, root=data_root),
        "aggregate_observation": file_reference(aggregate_path, root=data_root),
        "range_completion": file_reference(range_completion_path, root=data_root),
        "range_inventory": file_reference(range_inventory_path, root=data_root),
        "page_record": page_record,
    }
    return evidence, read_json_object(page_path)


def _inventory_files(path: Path) -> dict[str, JsonObject]:
    inventory = read_json_object(path)
    return {str(row["path"]): row for row in cast(list[JsonObject], inventory["files"])}


def _verify_inventory_member(path: Path, root: Path, files: dict[str, JsonObject]) -> None:
    relative = path.relative_to(root).as_posix()
    reference = files.get(relative)
    _require(reference is not None, f"unsealed input: {path}")
    _verify_reference(path, cast(JsonObject, reference))


def _verify_reference(path: Path, reference: JsonObject) -> None:
    _require(
        path.is_file()
        and path.stat().st_size == reference.get("byte_size", path.stat().st_size)
        and sha256_file(path) == reference["sha256"],
        f"changed sealed input: {path}",
    )


def _validate_cells(cells: list[JsonObject]) -> None:
    indices = [int(cell["index"]) for cell in cells]
    _require(len(indices) == len(set(indices)), "document_index cell indices are not unique")
    for cell in cells:
        _require(str(cell.get("text", "")).strip() != "", "empty document_index cell")
        _require(cell.get("from_ocr") is False, "TOC text unexpectedly came from OCR")
        _cell_bbox(cell)


def _reconstruct_lines(cells: list[JsonObject]) -> list[_Line]:
    # Six points is the sealed production threshold. It joins split leader/page
    # fragments while remaining below the observed 8--13 point adjacent-line gap.
    threshold = 6.0
    ordered = sorted(
        cells,
        key=lambda cell: (_cell_bbox(cell)[3], _cell_bbox(cell)[0], int(cell["index"])),
    )
    lines: list[_Line] = []
    for cell in ordered:
        baseline = _cell_bbox(cell)[3]
        candidates = [
            line
            for line in lines[-8:]
            if max(line.baseline_max, baseline) - min(line.baseline_min, baseline) <= threshold
        ]
        if candidates:
            line = min(candidates, key=lambda item: abs(item.baseline - baseline))
            line.cells.append(cell)
            line.baseline_min = min(line.baseline_min, baseline)
            line.baseline_max = max(line.baseline_max, baseline)
            line.baseline = sum(_cell_bbox(item)[3] for item in line.cells) / len(line.cells)
        else:
            lines.append(
                _Line(
                    cells=[cell],
                    baseline=baseline,
                    baseline_min=baseline,
                    baseline_max=baseline,
                )
            )
    lines.sort(key=lambda line: (line.baseline, min(_cell_bbox(cell)[0] for cell in line.cells)))
    for line in lines:
        line.cells.sort(key=lambda cell: (_cell_bbox(cell)[0], int(cell["index"])))
    return lines


def _segment_entries(lines: list[_Line], *, right_edge: float) -> list[list[_Line]]:
    texts = [_line_text(line.cells) for line in lines]
    catalog_mode = any(_CATALOG_START.match(text) for text in texts)
    groups: list[list[_Line]] = []
    current: list[_Line] = []
    for line, text in zip(lines, texts, strict=True):
        if _RUNNING_FURNITURE.fullmatch(text):
            continue
        starts = bool((_CATALOG_START if catalog_mode else _OUTLINE_START).match(text))
        if starts and current:
            groups.append(current)
            current = []
        current.append(line)
        if _destination(line.cells, right_edge=right_edge) is not None:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _destination(cells: list[JsonObject], *, right_edge: float) -> str | None:
    text = _line_text(cells)
    leader = _LEADER_DESTINATION.search(text)
    if leader:
        return leader.group("label")
    if _OUTLINE_START.match(text):
        spaced = _SPACE_DESTINATION.search(text)
        if spaced:
            return spaced.group("label")
    if not (_OUTLINE_START.match(text) or _CATALOG_START.match(text)):
        return None
    # Some Docling rows preserve the page label as one or more independent
    # right-margin cells rather than dot leaders. Only consume cells that are
    # themselves page-token fragments, which avoids treating title text such as
    # ``PM2.5`` or running furniture such as ``VOLUME 3`` as a destination.
    suffix: list[str] = []
    for cell in reversed(cells):
        value = "".join(str(cell["text"]).split())
        left, _, right, _ = _cell_bbox(cell)
        if right < right_edge - 36.0 or not re.fullmatch(r"[a-z0-9.-]+", value, re.I):
            break
        suffix.append(value)
        if left < right_edge - 36.0:
            break
    if not suffix:
        return None
    candidate = "".join(reversed(suffix))
    return candidate if _PAGE_TOKEN.fullmatch(candidate) else None


def _marker(text: str) -> tuple[str | None, str | None, str | None]:
    decimal = _DECIMAL_START.match(text)
    if decimal:
        raw = decimal.group(0)
        return "section", raw, re.sub(r"\s*\.\s*", ".", raw)
    catalog = _CATALOG_START.match(text)
    if catalog:
        return (
            catalog.group("kind").casefold(),
            catalog.group(0),
            catalog.group("marker").casefold(),
        )
    return None, None, None


def _model_text(text: str) -> str:
    return " ".join(_MODEL_DOT_LEADERS.sub(" ", text).split())


def _line_text(cells: list[JsonObject]) -> str:
    text = ""
    previous_right: float | None = None
    for cell in cells:
        value = " ".join(str(cell["text"]).replace("\u00a0", " ").split())
        if not value:
            continue
        left, _, right, _ = _cell_bbox(cell)
        if text and previous_right is not None and left - previous_right > 1.5:
            text += " "
        text += value
        previous_right = right
    return text


def _cell_bbox(cell: JsonObject) -> list[float]:
    rect = cast(JsonObject, cell["rect"])
    xs = [float(rect[f"r_x{index}"]) for index in range(4)]
    ys = [float(rect[f"r_y{index}"]) for index in range(4)]
    _require(rect.get("coord_origin") == "TOPLEFT", "unexpected Docling coordinate origin")
    return [min(xs), min(ys), max(xs), max(ys)]


def _union_bbox(cells: list[JsonObject]) -> list[float]:
    boxes = [_cell_bbox(cell) for cell in cells]
    return [
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    ]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
