"""Validate fresh author proposals for binary point and conclusion support."""

from __future__ import annotations

from typing import Any

ANNOTATION_VERSION = "task09a2.stage_expectations.v1"


def validate_stage_expectations(variant: dict[str, Any], sources: dict[str, Any]) -> list[str]:
    """Check literal provenance and logical consistency, never semantic entailment."""
    errors: list[str] = []
    answer = variant["answer"]
    expectation = variant["expectation"]
    grounding = expectation["grounding"]
    unresolved = expectation["verification_status"] == "unresolved"
    points = [*answer["supporting_points"], *answer["qualifications"], *answer["optional_context"]]
    rows = grounding["point_expectations"]
    ids = [p["point_id"] for p in points]
    if [r["point_id"] for r in rows] != ids:
        errors.append("point expectations must cover every non-conclusion point in answer order")
    point_by_id = {p["point_id"]: p for p in points}

    def evidence_checks(evidence: list[dict[str, Any]], allowed: set[str]) -> None:
        """Require exact source text and point-owned citation identities."""
        for item in evidence:
            source = sources.get(item["citation_id"])
            if item["citation_id"] not in allowed:
                errors.append("stage evidence must belong to the assessed point's actual citations")
            if source is None:
                errors.append("stage evidence does not resolve")
            elif (
                item["locator"] != source["canonical_target"]["unit_id"]
                or not item["excerpt"].strip()
                or item["excerpt"] not in source["full_source_text"]
            ):
                errors.append(
                    "stage evidence must have an exact source locator and literal excerpt"
                )

    for row in rows:
        point = point_by_id.get(row["point_id"])
        if point is None:
            continue
        issues = row["unsupported_assertions"]
        if not row["rationale"].strip():
            errors.append("point expectation needs rationale")
        if row["supported"] is True and (issues or not row["evidence"]):
            errors.append("supported point requires evidence and no unsupported assertions")
        if row["supported"] is False and not issues:
            errors.append("unsupported point requires a literal unsupported assertion")
        for issue in issues:
            if (
                not issue["assertion_span"].strip()
                or issue["assertion_span"] not in point["text"]
                or not issue["reason"].strip()
            ):
                errors.append(
                    "unsupported assertion must be a literal nonblank point span with reason"
                )
        evidence_checks(row["evidence"], set(point["citation_ids"]))

    clean = grounding["clean_abstention"]
    conclusion = grounding["conclusion_supported"]
    premise_ids = grounding["unsupported_premise_point_ids"]
    false_ids = {row["point_id"] for row in rows if row["supported"] is False}
    if len(premise_ids) != len(set(premise_ids)) or not set(premise_ids) <= false_ids:
        errors.append("unsupported premise IDs must uniquely reference unsupported points")
    if premise_ids and conclusion is not False:
        errors.append("a necessary unsupported premise requires an unsupported conclusion")
    if clean is True:
        if (
            answer["status"] != "abstained"
            or points
            or answer["conclusion"]["citation_ids"]
            or conclusion is not None
            or grounding["score"] is not None
            or expectation["adequacy"]["score"] != 0
            or grounding["not_supported"] is not False
            or premise_ids
        ):
            errors.append(
                "clean abstention requires no substantive points, G null, A 0 and no failures"
            )
    elif conclusion is True:
        if not grounding["evidence"]:
            errors.append("supported conclusion needs actual cited evidence")
    all_citations = {c for p in [answer["conclusion"], *points] for c in p["citation_ids"]}
    evidence_checks(grounding["evidence"], all_citations)

    support_unknown = (
        clean is None
        or (clean is not True and conclusion is None)
        or any(row["supported"] is None for row in rows)
    )
    unknown = support_unknown or grounding["insufficient_evidence_response"] is None
    if unknown and (not unresolved or grounding["score"] is not None):
        errors.append("unknown stage labels require unresolved status and null grounding score")
    failures = conclusion is False or bool(false_ids)
    expected_not_supported = True if failures else None if support_unknown else False
    if grounding["not_supported"] is not expected_not_supported:
        errors.append(
            "not_supported must reflect unsupported assertions, separately from uncertainty"
        )
    if not unknown and clean is False:
        expected_score = 0 if conclusion is False else 1 if false_ids else 2
        if grounding["score"] != expected_score:
            # A semantically disputed proposal may preserve known components but decline a score.
            if not (unresolved and grounding["score"] is None):
                errors.append("grounding score disagrees with point and conclusion support")
    return errors
