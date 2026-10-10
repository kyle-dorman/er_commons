"""Explicit research-only reopening and immutable composition of 08E prepared batches."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from er_commons.group_claims_batch import read_reference, reference, write_new
from er_commons.group_evidence_batch import _project_case, load_inputs

REOPENED = ["C014", "C020", "C024"]
AUTHORIZATION_VERSION = "task08e.research_reopening.v1"


def validate_authorization(authorization: dict[str, Any], upstream: dict[str, Any]) -> None:
    """Require an exact, scoped user instruction without changing historical approvals."""
    if (
        authorization.get("schema_version") != AUTHORIZATION_VERSION
        or authorization.get("actor") != "Kyle"
        or not authorization.get("verbatim_user_instruction", "").strip()
        or authorization.get("reopened_case_ids") != REOPENED
        or authorization.get("upstream_result") != upstream["upstream_result"]
        or authorization.get("upstream_handoff") != upstream["upstream_handoff"]
        or authorization.get("scope") != "research_preparation_only"
        or authorization.get("historical_decisions_unchanged") is not True
        or authorization.get("human_evidence_review_authorized") is not False
        or authorization.get("08f_authorized") is not False
        or set(authorization.get("research_directions", {})) != set(REOPENED)
        or any(not value for value in authorization.get("research_directions", {}).values())
    ):
        raise ValueError("Explicit research-only reopening authorization required")
    if upstream["held_case_ids"] != REOPENED:
        raise ValueError("Reopening does not match the exact historical holds")


def load_supplement_inputs(result_path: Path, authorization_path: Path) -> dict[str, Any]:
    """Verify the full historical seal and project held cases without promoting claims."""
    upstream = load_inputs(result_path)
    authorization = json.loads(authorization_path.read_bytes())
    validate_authorization(authorization, upstream)
    result = json.loads(result_path.read_bytes())
    handoff = read_reference(upstream["upstream_handoff"])
    review = read_reference(handoff["review"])
    required = read_reference(handoff["required_context"])
    readings = [
        {"binding": ref, "content": read_reference(ref)} for ref in required["required_reading"]
    ]
    cases = []
    for source in review["source_context"]["cases"]:
        cid = source["case_id"]
        if cid not in REOPENED:
            continue
        state = review["cases"][cid]
        advancing = [row for row in review["advancing"] if row["case_id"] == cid]
        if state["case_decision"]["decision"] != "hold" or advancing:
            raise ValueError(
                "Reopened case must retain its historical hold and zero approved claims"
            )
        case = _project_case(source, state, [], required, readings, review, handoff, result)
        case["research_reopening"] = {
            "authorization": reference(authorization_path),
            "scope": "research_preparation_only",
            "research_direction": copy.deepcopy(authorization["research_directions"][cid]),
            "historical_case_decision": copy.deepcopy(state["case_decision"]),
            "claim_policy": "No approved direct/supporting claims; findings remain beyond claims.",
        }
        cases.append(case)
    if [case["case_id"] for case in cases] != REOPENED:
        raise ValueError("Reopened cases differ from saved upstream order")
    return {
        "schema_version": "task08e.supplement_inputs.v1",
        "cases": cases,
        "held_case_ids": [],
        "historical_held_case_ids": REOPENED,
        "deferred_case_ids": upstream["deferred_case_ids"],
        "upstream_result": upstream["upstream_result"],
        "upstream_handoff": upstream["upstream_handoff"],
        "authorization": reference(authorization_path),
    }


def prepare_supplement_inputs(
    result_path: Path, authorization_path: Path, output: Path
) -> dict[str, Any]:
    """Persist restartable immutable input snapshots before any supplemental research."""
    inputs = load_supplement_inputs(result_path, authorization_path)
    refs = []
    for case in inputs["cases"]:
        path = output / "cases" / case["case_id"] / "input.json"
        write_new(path, case)
        refs.append({"case_id": case["case_id"], "input": reference(path)})
    register = {key: value for key, value in inputs.items() if key != "cases"}
    register.update(cases=refs, status="inputs verified; research not started")
    write_new(output / "inputs.json", register)
    return register


def _combined_rows(
    base: dict[str, Any], supplement: dict[str, Any], review: dict[str, Any]
) -> list[dict[str, Any]]:
    """Combine disjoint exact rows in upstream saved order, excluding the four deferrals."""
    if (
        len(base["cases"]) != 50
        or base["held_case_ids"] != REOPENED
        or [row["case_id"] for row in supplement["cases"]] != REOPENED
        or supplement["approved_claims"] != 0
        or supplement["held_case_ids"]
        or base["upstream_handoff"] != supplement["upstream_handoff"]
        or base["deferred_case_ids"] != supplement["deferred_case_ids"]
    ):
        raise ValueError("Prepared component membership or lineage differs")
    all_rows = base["cases"] + supplement["cases"]
    rows = {row["case_id"]: row for row in all_rows}
    order = [row["case_id"] for row in review["source_context"]["cases"]]
    if len(rows) != 53 or len(order) != 53 or set(order) != set(rows):
        raise ValueError("Combined rows must cover exactly 53 unique upstream cases")
    return [copy.deepcopy(rows[cid]) for cid in order]


def publish_combined_result(
    base_result_path: Path,
    supplement_result_path: Path,
    output_root: Path,
    *,
    qualification_path: Path,
) -> dict[str, Any]:
    """Seal a 53-case reference composition without rewriting either prepared component."""
    from er_commons.group_evidence_publication import verify_prepared_result

    for component_path in (base_result_path, supplement_result_path):
        component_result = json.loads(component_path.read_bytes())
        component_root = Path(component_result["completion"]["path"]).parent.resolve()
        if output_root.resolve().is_relative_to(component_root) or component_root.is_relative_to(
            output_root.resolve()
        ):
            raise ValueError("Combined output must be separate from both immutable component roots")
    base = verify_prepared_result(base_result_path)
    supplement = verify_prepared_result(supplement_result_path)
    authorization = read_reference(supplement["research_reopening_authorization"])
    upstream_path = Path(authorization["upstream_result"]["path"])
    read_reference(authorization["upstream_result"])
    inputs = load_inputs(upstream_path)
    validate_authorization(authorization, inputs)
    upstream = read_reference(inputs["upstream_handoff"])
    review = read_reference(upstream["review"])
    rows = _combined_rows(base, supplement, review)
    if base["upstream_handoff"] != inputs["upstream_handoff"]:
        raise ValueError("Prepared components differ from authorized upstream")
    qualification = reference(qualification_path)
    if read_reference(qualification).get("status") != "pass":
        raise ValueError("Combined publication requires passed qualification")
    handoff = {
        "schema_version": "task08e.combined_prepared_batch.v1",
        "status": "prepared, awaiting human review",
        "components": [reference(base_result_path), reference(supplement_result_path)],
        "cases": rows,
        "held_case_ids": [],
        "historical_held_case_ids": REOPENED,
        "research_reopened_case_ids": REOPENED,
        "deferred_case_ids": inputs["deferred_case_ids"],
        "research_reopening_authorization": supplement["research_reopening_authorization"],
        "upstream_handoff": inputs["upstream_handoff"],
        "phase_a_complete": True,
        "phase_b_started": False,
        "08f_started": False,
        "resume_case_id": rows[0]["case_id"],
        "human_decisions": 0,
        "eligibility": None,
        "qualification": qualification,
        "review_instructions": reference(output_root / "REVIEW_INSTRUCTIONS.md"),
        **{
            key: base[key] + supplement[key]
            for key in (
                "approved_claims",
                "source_occurrences",
                "beyond_claim_findings",
                "query_receipts",
            )
        },
    }
    write_new(output_root / "prepared_handoff.json", handoff)
    write_new(
        output_root / "completion.json",
        {
            "schema_version": "task08e.combined_prepared_completion.v1",
            "handoff": reference(output_root / "prepared_handoff.json"),
            "files": [
                reference(path)
                for path in sorted(output_root.rglob("*"))
                if path.is_file() and path != output_root / "completion.json"
            ],
        },
    )
    return {
        "schema_version": "task08e.combined_prepared_result.v1",
        "handoff": reference(output_root / "prepared_handoff.json"),
        "completion": reference(output_root / "completion.json"),
        "cases": 53,
        **{
            key: handoff[key]
            for key in (
                "status",
                "approved_claims",
                "source_occurrences",
                "beyond_claim_findings",
                "query_receipts",
                "held_case_ids",
                "historical_held_case_ids",
                "research_reopened_case_ids",
                "deferred_case_ids",
                "human_decisions",
            )
        },
        "next_action": "Separate question-by-question human review chat",
    }


def verify_combined_result(result_path: Path) -> dict[str, Any]:
    """Verify exact composite closure, original component seals and ordered row fidelity."""
    from er_commons.group_evidence_publication import verify_prepared_result

    result = json.loads(result_path.read_bytes())
    if result.get("schema_version") != "task08e.combined_prepared_result.v1":
        raise ValueError("Unknown combined prepared result")
    handoff: dict[str, Any] = read_reference(result["handoff"])
    completion = read_reference(result["completion"])
    if completion["handoff"] != result["handoff"]:
        raise ValueError("Combined completion handoff differs")
    root = Path(result["completion"]["path"]).parent.resolve()
    paths = [Path(ref["path"]).resolve() for ref in completion["files"]]
    if len(paths) != len(set(paths)) or any(not p.is_relative_to(root) for p in paths):
        raise ValueError("Combined inventory has duplicate or escaping paths")
    if {p.resolve() for p in root.rglob("*") if p.is_file()} != {
        *paths,
        Path(result["completion"]["path"]).resolve(),
    }:
        raise ValueError("Combined file closure changed")
    for ref in completion["files"]:
        if reference(Path(ref["path"])) != ref:
            raise ValueError("Combined file bytes changed")
    if len(handoff["components"]) != 2:
        raise ValueError("Combined preparation requires exactly two components")
    components = []
    for ref in handoff["components"]:
        read_reference(ref)
        components.append(verify_prepared_result(Path(ref["path"])))
    base, supplement = components
    authorization = read_reference(handoff["research_reopening_authorization"])
    read_reference(authorization["upstream_result"])
    inputs = load_inputs(Path(authorization["upstream_result"]["path"]))
    validate_authorization(authorization, inputs)
    upstream = read_reference(inputs["upstream_handoff"])
    expected = _combined_rows(base, supplement, read_reference(upstream["review"]))
    if handoff["cases"] != expected or result["cases"] != len(expected):
        raise ValueError("Combined rows differ from sealed components")
    if (
        handoff["research_reopening_authorization"]
        != supplement["research_reopening_authorization"]
        or base["upstream_handoff"] != inputs["upstream_handoff"]
        or handoff["upstream_handoff"] != inputs["upstream_handoff"]
        or handoff["held_case_ids"] != []
        or handoff["historical_held_case_ids"] != REOPENED
        or handoff["research_reopened_case_ids"] != REOPENED
        or handoff["deferred_case_ids"] != inputs["deferred_case_ids"]
        or handoff["status"] != "prepared, awaiting human review"
        or handoff["phase_a_complete"] is not True
        or handoff["phase_b_started"] is not False
        or handoff["08f_started"] is not False
        or handoff["human_decisions"] != 0
        or handoff["eligibility"] is not None
        or handoff["resume_case_id"] != expected[0]["case_id"]
    ):
        raise ValueError("Combined phase, authorization or membership differs")
    for key in ("approved_claims", "source_occurrences", "beyond_claim_findings", "query_receipts"):
        if handoff[key] != base[key] + supplement[key]:
            raise ValueError("Combined totals differ")
    for key in (
        "status",
        "approved_claims",
        "source_occurrences",
        "beyond_claim_findings",
        "query_receipts",
        "held_case_ids",
        "historical_held_case_ids",
        "research_reopened_case_ids",
        "deferred_case_ids",
        "human_decisions",
    ):
        if result.get(key) != handoff[key]:
            raise ValueError("Combined result summary differs")
    if read_reference(handoff["qualification"]).get("status") != "pass":
        raise ValueError("Combined qualification is not passed")
    if reference(Path(handoff["review_instructions"]["path"])) != handoff["review_instructions"]:
        raise ValueError("Combined review instructions changed")
    return handoff
