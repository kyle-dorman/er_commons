"""Single-required-point support coverage contract; no execution or grounding checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.judge_context import baylands_overview

PROMPT_VERSION = "task15y.required_support_coverage.v1"
PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "docs/prompts/task15y_required_support_coverage_v1.txt"
)


def system_prompt() -> str:
    """Compose approved instructions with the checksum-verified shared overview."""
    return PROMPT_PATH.read_text().rstrip("\n") + "\n\nPROJECT OVERVIEW\n" + baylands_overview()


def _string_schema() -> dict[str, Any]:
    """Describe nonempty text; local validation also rejects whitespace-only text."""
    return {"type": "string", "minLength": 1}


def input_json_schema() -> dict[str, Any]:
    """Expose only one reference point and candidate support, without provenance."""
    point = {
        "type": "object",
        "additionalProperties": False,
        "required": ["point_id", "text"],
        "properties": {"point_id": _string_schema(), "text": _string_schema()},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["question", "required_reference_point", "candidate_supporting_points"],
        "properties": {
            "question": _string_schema(),
            "required_reference_point": point,
            "candidate_supporting_points": {"type": "array", "items": point},
        },
    }


def output_json_schema() -> dict[str, Any]:
    """Return the approved schema; request-dependent witness checks remain local."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["covered", "supporting_point_ids", "reason"],
        "properties": {
            "covered": {"type": "boolean"},
            "supporting_point_ids": {
                "type": "array",
                "items": _string_schema(),
                "uniqueItems": True,
            },
            "reason": _string_schema(),
        },
    }


def _text(value: object) -> bool:
    """Check nonblank strings without changing their original bytes."""
    return isinstance(value, str) and bool(value.strip())


def _point(value: object) -> dict[str, str]:
    """Validate a two-field point and preserve its canonical identifier and text."""
    if not isinstance(value, dict) or set(value) != {"point_id", "text"}:
        raise ValueError("Point must contain exactly point_id and text")
    if not all(_text(item) for item in value.values()):
        raise ValueError("Point ID and text must be nonblank strings")
    return {"point_id": value["point_id"], "text": value["text"]}


def validate_input(packet: object) -> dict[str, Any]:
    """Reject hidden context and duplicate support IDs before provider construction."""
    keys = {"question", "required_reference_point", "candidate_supporting_points"}
    if not isinstance(packet, dict) or set(packet) != keys or not _text(packet["question"]):
        raise ValueError("Coverage input must contain exactly the three approved fields")
    points = packet["candidate_supporting_points"]
    if not isinstance(points, list):
        raise ValueError("Candidate supporting points must be a list")
    support = [_point(point) for point in points]
    ids = [point["point_id"] for point in support]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate supporting IDs must be unique")
    return {
        "question": packet["question"],
        "required_reference_point": _point(packet["required_reference_point"]),
        "candidate_supporting_points": support,
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys rather than silently keeping the last value."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    """Reject nonstandard JSON numeric constants."""
    raise ValueError(f"Invalid JSON constant: {value}")


def parse_output(raw: str, *, payload: object) -> dict[str, Any]:
    """Validate one judgment strictly; failures never acquire a semantic label."""
    packet = validate_input(payload)
    if not isinstance(raw, str):
        raise ValueError("Coverage output must be JSON text")
    result = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    if not isinstance(result, dict) or set(result) != {"covered", "supporting_point_ids", "reason"}:
        raise ValueError("Coverage output must contain exactly the approved fields")
    covered, ids = result["covered"], result["supporting_point_ids"]
    if type(covered) is not bool or not isinstance(ids, list) or not _text(result["reason"]):
        raise ValueError("Invalid coverage output field types or blank reason")
    if not all(_text(value) for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Witness IDs must be nonblank and unique")
    allowed = {point["point_id"] for point in packet["candidate_supporting_points"]}
    if not set(ids) <= allowed:
        raise ValueError("Unknown supporting-point ID")
    if covered != bool(ids):
        raise ValueError("True requires witnesses; false requires empty supporting IDs")
    return dict(result)
