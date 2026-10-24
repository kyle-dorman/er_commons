"""Project and join real-answer coverage diagnostics without changing benchmark gates."""

from __future__ import annotations

from typing import Any

from jsonschema import validate  # type: ignore[import-untyped]

from er_commons import required_support_coverage as coverage
from er_commons.artifact_io import stable_json_sha256
from er_commons.target_generation import output_schema

_BINDING_FIELDS = (
    "identity",
    "candidate_sha256",
    "required_point_id",
    "prompt_version",
    "payload_sha256",
)


def project_coverage(
    answer: dict[str, Any],
    *,
    question: str,
    required_points: list[dict[str, str]],
    identity: dict[str, Any],
) -> list[dict[str, Any]]:
    """Bind singleton reference packets to a valid answer; callers own A routing."""
    validate(answer, output_schema())
    points = [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]
    ids = [point["point_id"] for point in points]
    point_ids = set(ids)
    if len(point_ids) != len(ids) or any(
        not point["point_id"].strip() or not point["text"].strip() for point in points
    ):
        raise ValueError("Duplicate or blank answer point identity/text")
    if any(not set(point["applies_to"]) <= point_ids for point in points):
        raise ValueError("Unresolved answer point reference")
    if not identity or not required_points:
        raise ValueError("Answer identity and required references are required")
    reference_ids = [point["point_id"] for point in required_points]
    if len(set(reference_ids)) != len(reference_ids):
        raise ValueError("Duplicate required reference identity")
    support = [
        {key: point[key] for key in ("point_id", "text")} for point in answer["supporting_points"]
    ]
    candidate_sha256 = stable_json_sha256(answer)
    rows = []
    for reference in required_points:
        packet = coverage.validate_input(
            {
                "question": question,
                "required_reference_point": reference,
                "candidate_supporting_points": support,
            }
        )
        binding = {
            "identity": identity,
            "candidate_sha256": candidate_sha256,
            "required_point_id": reference["point_id"],
            "prompt_version": coverage.PROMPT_VERSION,
            "payload_sha256": stable_json_sha256(packet),
        }
        rows.append({**binding, "sample_id": stable_json_sha256(binding), "packet": packet})
    return rows


def join_coverage(
    projections: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
    *,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Join bound verdicts and witness grounding, preserving missing/invalid states."""
    expected = {row["sample_id"]: row for row in projections}
    if len(expected) != len(projections):
        raise ValueError("Duplicate coverage projection")
    for row in projections:
        binding = {key: row[key] for key in _BINDING_FIELDS}
        packet = coverage.validate_input(row["packet"])
        if (
            row["sample_id"] != stable_json_sha256(binding)
            or row["required_point_id"] != packet["required_reference_point"]["point_id"]
            or row["prompt_version"] != coverage.PROMPT_VERSION
        ):
            raise ValueError("Altered coverage binding")
    if projections and any(
        evaluation.get(key) != projections[0][key] for key in ("identity", "candidate_sha256")
    ):
        raise ValueError("Cross-answer C/G evaluation binding")
    c_missing_ids = evaluation["c_missing_ids"]
    grounding = evaluation["grounding"]
    required_ids = {row["required_point_id"] for row in projections}
    if len(required_ids) != len(projections):
        raise ValueError("Duplicate required reference projection")
    if projections and any(
        row["identity"] != projections[0]["identity"]
        or row["candidate_sha256"] != projections[0]["candidate_sha256"]
        for row in projections
    ):
        raise ValueError("Cross-answer coverage projections")
    if any(stable_json_sha256(row["packet"]) != row["payload_sha256"] for row in projections):
        raise ValueError("Altered coverage projection")
    if c_missing_ids is not None and (
        len(set(c_missing_ids)) != len(c_missing_ids) or not set(c_missing_ids) <= required_ids
    ):
        raise ValueError("Unknown or duplicate C missing reference")
    indexed = {}
    for judgment in judgments:
        sid = judgment["sample_id"]
        if sid not in expected or sid in indexed:
            raise ValueError("Duplicate or orphan coverage judgment")
        projection = expected[sid]
        if any(judgment.get(key) != projection[key] for key in _BINDING_FIELDS):
            raise ValueError("Coverage judgment binding mismatch")
        indexed[sid] = judgment
    rows = []
    for projection in projections:
        saved = indexed.get(projection["sample_id"])
        status = saved["status"] if saved else "missing_judgment"
        decision = None
        error = None
        if status == "completed":
            assert saved is not None
            try:
                decision = coverage.parse_output(saved["raw_output"], payload=projection["packet"])
            except (ValueError, TypeError, KeyError) as exc:
                status, error = "invalid_output", str(exc)
        elif status not in {
            "missing_judgment",
            "execution_error",
            "invalid_output",
            "skipped_route",
        }:
            raise ValueError("Unknown coverage judgment status")
        witness_ids = decision["supporting_point_ids"] if decision else []
        witnesses = _witness_grounding(witness_ids, grounding)
        missing = (
            projection["required_point_id"] in c_missing_ids if c_missing_ids is not None else None
        )
        rows.append(
            {
                "sample_id": projection["sample_id"],
                "required_point_id": projection["required_point_id"],
                "status": status,
                "decision": decision,
                "error": error,
                "c_missing": missing,
                "support_covered_c_missing": decision["covered"] and missing
                if decision and missing is not None
                else None,
                "witness_grounding": witnesses,
            }
        )
    return {"diagnostic_only": True, "adds_overall_pass_requirement": False, "rows": rows}


def _witness_grounding(point_ids: list[str], grounding: dict[str, Any]) -> list[dict[str, Any]]:
    """Attach G results to RC witnesses; unavailable grounding is never false."""
    witnesses = []
    for point_id in point_ids:
        result = grounding.get(point_id)
        supported = (
            result.get("supported") if result and result.get("status") == "completed" else None
        )
        if supported is not None and type(supported) is not bool:
            raise ValueError("Grounding decision must be boolean or unavailable")
        witnesses.append(
            {
                "point_id": point_id,
                "status": result.get("status") if result else "unavailable",
                "supported": supported,
            }
        )
    return witnesses
