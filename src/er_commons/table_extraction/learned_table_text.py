"""Assign native PDF text to predicted cells and define table text scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.table_extraction.learned_table_geometry import bbox_center, parse_bbox
from er_commons.table_extraction.learned_table_types import BoundingBox, JsonObject, Position
from er_commons.table_extraction.otsl import OtslTopology, response_owner


@dataclass(frozen=True)
class NativeTextMatch:
    """Native text assigned to OTSL owners plus auditable assignment counts."""

    text_by_owner: dict[Position, str]
    tableformer_matched_token_count: int
    geometry_recovered_token_count: int
    unmatched_token_ids: list[int]

    def measurements(self) -> JsonObject:
        """Return the persisted measurement names owned by acceptance evidence."""
        return {
            "tableformer_matched_native_token_count": self.tableformer_matched_token_count,
            "geometry_recovered_native_token_count": self.geometry_recovered_token_count,
            "unmatched_native_token_ids": self.unmatched_token_ids,
        }


def _native_text_by_id(native_tokens: list[JsonObject]) -> dict[int, str]:
    """Index well-formed native tokens by their stable crop-local ID."""
    return {
        int(token["id"]): str(token["text"])
        for token in native_tokens
        if isinstance(token.get("id"), int)
        and not isinstance(token.get("id"), bool)
        and isinstance(token.get("text"), str)
    }


def _grouped_text(grouped: dict[Position, list[tuple[int, str]]]) -> dict[Position, str]:
    """Join tokens in stable native-token order for each logical cell."""
    return {
        owner: " ".join(text for _token_id, text in sorted(items))
        for owner, items in grouped.items()
    }


def _unique_containing_owner(
    token: JsonObject,
    structural_bboxes: dict[Position, BoundingBox],
) -> Position | None:
    """Return an owner only when one structural cell contains the token center."""
    token_bbox = parse_bbox(token.get("bbox_crop_pixels_top_left"))
    if token_bbox is None:
        return None
    center_x, center_y = bbox_center(token_bbox)
    owners = [
        owner
        for owner, (left, top, right, bottom) in structural_bboxes.items()
        if left <= center_x <= right and top <= center_y <= bottom
    ]
    return owners[0] if len(owners) == 1 else None


def _match_original_responses(
    *,
    details: JsonObject,
    native_tokens: list[JsonObject],
    topology: OtslTopology,
    structural_bboxes: dict[Position, BoundingBox],
) -> NativeTextMatch | None:
    """Map uncompressed Docling responses, then recover uniquely contained tokens."""
    original_responses = details.get("docling_responses")
    pdf_cells = details.get("pdf_cells")
    if not isinstance(original_responses, list) or not isinstance(pdf_cells, list):
        return None
    native_by_id = _native_text_by_id(native_tokens)
    pdf_by_id = {
        cell.get("id"): cell
        for cell in pdf_cells
        if isinstance(cell, dict)
        and isinstance(cell.get("id"), int)
        and not isinstance(cell.get("id"), bool)
    }
    if len(pdf_by_id) != len(pdf_cells):
        return None

    assigned_ids: set[int] = set()
    grouped: dict[Position, list[tuple[int, str]]] = {}
    for item in original_responses:
        if not isinstance(item, dict):
            return None
        owner = response_owner(item, topology)
        cell_id = item.get("cell_id")
        if (
            owner is None
            or not isinstance(cell_id, int)
            or isinstance(cell_id, bool)
            or cell_id in assigned_ids
        ):
            return None
        pdf_cell = pdf_by_id.get(cell_id)
        if pdf_cell is None:
            return None
        text = pdf_cell.get("text")
        if not isinstance(text, str) or native_by_id.get(cell_id) != text:
            return None
        assigned_ids.add(cell_id)
        grouped.setdefault(owner, []).append((cell_id, text))

    tableformer_match_count = len(assigned_ids)
    recovered_count = 0
    for token in native_tokens:
        token_id = token.get("id")
        token_text = token.get("text")
        if (
            not isinstance(token_id, int)
            or isinstance(token_id, bool)
            or token_id in assigned_ids
            or not isinstance(token_text, str)
        ):
            continue
        owner = _unique_containing_owner(token, structural_bboxes)
        if owner is None:
            continue
        assigned_ids.add(token_id)
        grouped.setdefault(owner, []).append((token_id, token_text))
        recovered_count += 1

    return NativeTextMatch(
        text_by_owner=_grouped_text(grouped),
        tableformer_matched_token_count=tableformer_match_count,
        geometry_recovered_token_count=recovered_count,
        unmatched_token_ids=sorted(set(native_by_id) - assigned_ids),
    )


def _match_processed_responses(
    responses: list[Any],
    topology: OtslTopology,
) -> NativeTextMatch | None:
    """Read the public response form when original matching evidence is absent."""
    grouped: dict[Position, list[tuple[int, str]]] = {}
    seen_owners: set[Position] = set()
    for ordinal, item in enumerate(responses):
        if not isinstance(item, dict):
            return None
        owner = response_owner(item, topology)
        if owner is None or owner in seen_owners:
            return None
        seen_owners.add(owner)
        response_text = item.get("text")
        if isinstance(response_text, str):
            text = response_text
        else:
            matched_boxes = item.get("text_cell_bboxes", [])
            if not isinstance(matched_boxes, list):
                return None
            text = " ".join(
                str(box.get("token", ""))
                for box in matched_boxes
                if isinstance(box, dict) and box.get("token")
            )
        grouped.setdefault(owner, []).append((ordinal, text))
    return NativeTextMatch(
        text_by_owner=_grouped_text(grouped),
        tableformer_matched_token_count=len(responses),
        geometry_recovered_token_count=0,
        unmatched_token_ids=[],
    )


def match_native_text(
    *,
    details: JsonObject,
    responses: list[Any],
    native_tokens: list[JsonObject],
    topology: OtslTopology,
    structural_bboxes: dict[Position, BoundingBox],
) -> NativeTextMatch | None:
    """Recover native text at original OTSL positions before index compression."""
    if isinstance(details.get("docling_responses"), list) and isinstance(
        details.get("pdf_cells"), list
    ):
        return _match_original_responses(
            details=details,
            native_tokens=native_tokens,
            topology=topology,
            structural_bboxes=structural_bboxes,
        )
    return _match_processed_responses(responses, topology)


def top_boundary_fringe_token_ids(
    *,
    native_tokens: list[JsonObject],
    structural_bboxes: dict[Position, BoundingBox],
    boundary_tolerance: float,
) -> set[int]:
    """Find a top-edge-connected text line wholly above the structural grid."""
    structural_top = min(bbox[1] for bbox in structural_bboxes.values())
    candidates: dict[int, BoundingBox] = {}
    for token in native_tokens:
        token_id = token.get("id")
        token_bbox = parse_bbox(token.get("bbox_crop_pixels_top_left"))
        if (
            isinstance(token_id, int)
            and not isinstance(token_id, bool)
            and token_bbox is not None
            and token_bbox[3] <= structural_top
        ):
            candidates[token_id] = token_bbox

    fringe = {
        token_id
        for token_id, (_left, top, _right, _bottom) in candidates.items()
        if top <= boundary_tolerance
    }
    while True:
        intervals = [(candidates[token_id][1], candidates[token_id][3]) for token_id in fringe]
        connected = {
            token_id
            for token_id, (_left, top, _right, bottom) in candidates.items()
            if token_id not in fringe
            and any(
                min(bottom, other_bottom) > max(top, other_top)
                for other_top, other_bottom in intervals
            )
        }
        if not connected:
            return fringe
        fringe.update(connected)


def unmatched_leading_tokens(
    *,
    native_tokens: list[JsonObject],
    unmatched_ids: list[int],
    topology: OtslTopology,
    structural_bboxes: dict[Position, BoundingBox],
    crop_size: tuple[int, int],
    boundary_tolerance: float,
    ignored_ids: set[int],
) -> list[JsonObject]:
    """Return unmatched in-scope text preceding the first predicted body row."""
    header_rows = [
        row_index
        for row_index, row in enumerate(topology.grid)
        if any(token == "ched" for token in row)
    ]
    if not header_rows:
        return []
    last_header = min(header_rows)
    while last_header + 1 in header_rows:
        last_header += 1
    first_body_tops = [
        bbox[1] for owner, bbox in structural_bboxes.items() if owner[0] == last_header + 1
    ]
    if not first_body_tops:
        return []
    first_body_top = min(first_body_tops)
    table_left = min(bbox[0] for bbox in structural_bboxes.values())
    table_right = max(bbox[2] for bbox in structural_bboxes.values())
    crop_width, _crop_height = crop_size
    unmatched = set(unmatched_ids) - ignored_ids
    result: list[JsonObject] = []
    for token in native_tokens:
        if token.get("id") not in unmatched:
            continue
        token_bbox = parse_bbox(token.get("bbox_crop_pixels_top_left"))
        if token_bbox is None:
            continue
        left, top, right, _bottom = token_bbox
        if (
            left <= boundary_tolerance
            or top <= boundary_tolerance
            or right >= crop_width - boundary_tolerance
        ):
            continue
        center_x, center_y = bbox_center(token_bbox)
        if table_left <= center_x <= table_right and center_y < first_body_top:
            result.append(token)
    return result
