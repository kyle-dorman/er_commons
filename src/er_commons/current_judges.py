"""Current offline judge planning: A/G/S/C decisions plus mandatory RC diagnostics."""

from __future__ import annotations

import json
from typing import Any

from er_commons import conclusion_structured, development_evaluation, support_material
from er_commons.artifact_io import stable_json_sha256
from er_commons.task15ad_coverage import join_coverage, project_coverage

RC_NAME = "Required-point Coverage"
RC_COMPONENT = "RC"


def prepare_candidate(
    candidate_bytes: bytes,
    identity: dict[str, Any],
    target_record: dict[str, Any],
    mapping: dict[str, Any],
    delivery_receipt: dict[str, Any],
    reference_conclusion: str,
    *,
    structured_reference: dict[str, Any],
    expected_split: str = "dev",
) -> dict[str, Any]:
    """Select accepted C/S versions and require RC without modifying legacy plans."""
    decision_plan = development_evaluation.prepare_candidate(
        candidate_bytes,
        identity,
        target_record,
        mapping,
        delivery_receipt,
        reference_conclusion,
        structured_reference=structured_reference,
        expected_split=expected_split,
        conclusion_prompt_version=conclusion_structured.VERSION_V6,
        support_prompt_version=support_material.VERSION,
    )
    required = structured_reference["reference_required_points"]
    projections = []
    if decision_plan["automatic"]["schema"] == "valid":
        projections = project_coverage(
            json.loads(candidate_bytes),
            question=target_record["payload"]["question"],
            required_points=required,
            identity=decision_plan["identity"],
        )
    body = {
        "schema_version": "current_judges.plan.v1",
        "decision_plan": decision_plan,
        "rc_plan": {
            "component": RC_COMPONENT,
            "name": RC_NAME,
            "required_point_ids": [point["point_id"] for point in required],
            "projections": projections,
        },
    }
    return {**body, "plan_sha256": stable_json_sha256(body)}


def build_report(
    plan: dict[str, Any],
    judgments: list[dict[str, Any]],
    rc_judgments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Replay both channels; RC completeness never changes the decision report."""
    if plan["plan_sha256"] != stable_json_sha256(
        {key: value for key, value in plan.items() if key != "plan_sha256"}
    ):
        raise ValueError("Altered current judge plan binding")
    report = development_evaluation.build_report(plan["decision_plan"], judgments)
    rc_plan = plan["rc_plan"]
    projections = rc_plan["projections"]
    required_ids = rc_plan["required_point_ids"]
    route = report["route"]
    if route != "substantive":
        if rc_judgments:
            raise ValueError("RC judgment contradicts answer routing")
        status = "blocked_a_unavailable" if route == "a_unavailable" else "skipped_" + route
        rows = [
            {
                "required_point_id": point_id,
                "status": status,
                "decision": None,
                "c_status": "unavailable",
                "comparison": "unavailable",
            }
            for point_id in required_ids
        ]
        complete = route in {"clean_abstention", "mixed_abstention", "ambiguous"}
    else:
        c_result = next(row for row in report["results"] if row["component"] == "C")
        c_statuses = {}
        if c_result["status"] == "completed":
            c_statuses = {
                point["point_id"]: point["status"]
                for point in c_result["decision"]["judgments"]
                if point["point_id"] in required_ids
            }
            if set(c_statuses) != set(required_ids):
                raise ValueError("Incomplete required C point inventory")
        c_missing_ids = (
            [point_id for point_id, status in c_statuses.items() if status == "missing"]
            if c_statuses
            else None
        )
        grounding = {
            row["point_id"]: {"status": row["status"], **(row["decision"] or {})}
            for row in report["results"]
            if row["component"] == "G"
        }
        joined = join_coverage(
            projections,
            rc_judgments,
            evaluation={
                "identity": report["identity"],
                "candidate_sha256": projections[0]["candidate_sha256"],
                "c_missing_ids": c_missing_ids,
                "grounding": grounding,
            },
        )
        rows = joined["rows"]
        for row in rows:
            row["c_status"] = c_statuses.get(row["required_point_id"], "unavailable")
            decision = row["decision"]
            row["comparison"] = "unavailable"
            if decision is not None and row["c_status"] != "unavailable":
                coverage_status = "covered" if decision["covered"] else "not_covered"
                row["comparison"] = f"{coverage_status}/{row['c_status']}"
        complete = all(row["status"] == "completed" for row in rows)
    return {
        "report": report,
        "rc": {
            "component": RC_COMPONENT,
            "name": RC_NAME,
            "diagnostic_only": True,
            "adds_overall_pass_requirement": False,
            "rows": rows,
        },
        "rc_complete": complete,
    }


def pending_items(
    plan: dict[str, Any],
    judgments: list[dict[str, Any]],
    rc_judgments: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Expose separate dispatch queues after A routing, without retrying failures."""
    result = build_report(plan, judgments, rc_judgments)
    missing = {
        row["sample_id"] for row in result["rc"]["rows"] if row["status"] == "missing_judgment"
    }
    return {
        "decision_items": development_evaluation.pending_items(plan["decision_plan"], judgments),
        "rc_items": [row for row in plan["rc_plan"]["projections"] if row["sample_id"] in missing],
    }
