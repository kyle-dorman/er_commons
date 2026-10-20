"""Pure reporting reductions over byte-verified, replayed answer observations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from er_commons.automatic_metrics import CitationMetrics

COMPONENTS = ("A", "G", "S", "C", "automatic", "joint")
STATES = ("pass", "fail", "unavailable", "not_applicable")
COUNT_BINS = ((0, 0, "0"), (1, 2, "1–2"), (3, 5, "3–5"), (6, 10, "6–10"), (11, None, "11+"))


def _exposure_groups(rows: list[dict[str, Any]]) -> list[str]:
    """Emit each named exposure once, followed by the pooled all-exposures view."""
    return sorted({row["exposure_group"] for row in rows} - {"all"}) + ["all"]


def conjunction(states: list[str]) -> str:
    """Retain known failures even if other required outcomes are unresolved."""
    if "fail" in states:
        return "fail"
    if not states or "unavailable" in states:
        return "unavailable"
    return "pass" if "pass" in states else "not_applicable"


def judgment_state(result: dict[str, Any]) -> str:
    """Interpret validated semantic decisions separately from mechanical failures."""
    status = result["status"]
    if status == "precheck_failed":
        return "fail"
    if status == "skipped_clean_abstention":
        return "not_applicable"
    if status != "completed":
        return "unavailable"
    decision = result.get("decision") or {}
    key = {"G": "supported", "S": "support_sufficient", "C": "conclusion_adequate"}
    value = decision.get(key[result["component"]])
    return "pass" if value is True else "fail" if value is False else "unavailable"


def answer_outcomes(row: dict[str, Any]) -> dict[str, str]:
    """Score answerable-case routing and same-answer joint success without imputation."""
    report = row.get("report")
    if report is None:
        return dict.fromkeys(COMPONENTS, "unavailable")
    route = report["route"]
    # This version is frozen for the released answerable benchmark condition.
    a_state = {
        "substantive": "pass",
        "clean_abstention": "fail",
        "mixed_abstention": "unavailable",
        "ambiguous": "unavailable",
        "invalid_answer": "unavailable",
    }.get(route, "unavailable")
    states = {"A": a_state}
    for component in ("G", "S", "C"):
        results = [r for r in report["results"] if r["component"] == component]
        if component != "G" and len(results) > 1:
            raise ValueError(f"Duplicate {component} result")
        if route == "clean_abstention":
            states[component] = "not_applicable"
        else:
            values = [judgment_state(r) for r in results]
            if component == "G":
                candidate = row.get("candidate") or {}
                expected = {
                    p["point_id"]
                    for group in ("supporting_points", "qualifications")
                    for p in candidate.get(group, [])
                }
                actual = [r["point_id"] for r in results]
                if len(actual) != len(set(actual)) or not set(actual) <= expected:
                    raise ValueError("Duplicate or orphan required point")
                if set(actual) != expected:
                    values.append("unavailable")
            states[component] = conjunction(values)
        if component == "G" and report["support_structure"] == "missing_basis":
            states[component] = "fail"
    auto = report["automatic"]
    checks = [
        "unavailable" if "schema" not in auto else "pass" if auto["schema"] == "valid" else "fail",
        "unavailable"
        if "delivery" not in auto
        else "pass"
        if auto["delivery"] == "exact_payload_verified"
        else "fail",
        "unavailable"
        if "resolved_citations" not in auto
        else "pass"
        if auto["resolved_citations"] is True
        else "fail",
        "unavailable"
        if "uncited_point_ids" not in auto
        else "pass"
        if not auto["uncited_point_ids"] or route == "clean_abstention"
        else "fail",
    ]
    states["automatic"] = conjunction(checks)
    states["joint"] = conjunction(list(states.values()))
    return states


def _counts(states: list[str]) -> dict[str, Any]:
    """Expose planned, applicable and observed denominators next to every rate."""
    counts = Counter(states)
    planned = len(states)
    observed = counts["pass"] + counts["fail"]
    applicable = planned - counts["not_applicable"]
    return {
        **{state: counts[state] for state in STATES},
        "planned": planned,
        "applicable": applicable,
        "observed": observed,
        "planned_pass_fraction": counts["pass"] / planned if planned else None,
        "observed_pass_fraction": counts["pass"] / observed if observed else None,
        "outcome_coverage": observed / applicable if applicable else None,
    }


def component_coverage(row: dict[str, Any]) -> dict[str, bool]:
    """Distinguish resolved outcomes from receipt-complete component evaluations."""
    report = row.get("report")
    if report is None:
        return dict.fromkeys(COMPONENTS, False)
    coverage = {}
    for component in ("A", "G", "S", "C"):
        results = [r for r in report["results"] if r["component"] == component]
        expected_count = 1
        if component == "G":
            candidate = row.get("candidate") or {}
            expected_count = sum(
                len(candidate.get(g, [])) for g in ("supporting_points", "qualifications")
            )
        coverage[component] = len(results) == expected_count and all(
            r["status"] in {"completed", "precheck_failed", "skipped_clean_abstention"}
            for r in results
        )
    coverage["automatic"] = (
        all(
            key in report["automatic"]
            for key in ("schema", "delivery", "resolved_citations", "uncited_point_ids")
        )
        or report["automatic"].get("schema") == "invalid"
    )
    coverage["joint"] = all(coverage.values())
    return coverage


def answer_tables(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Retain exact answer/point identities and derive counts within split/exposure only."""
    answers: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    seen = set()
    for row in rows:
        key = (row.get("split", "development"), row["model"], row["case_id"], row["repeat"])
        if key in seen or type(row["repeat"]) is not int or row["repeat"] not in (1, 2, 3):
            raise ValueError("Duplicate answer slot or invalid repeat")
        seen.add(key)
        report = row.get("report") or {}
        base = {
            "split": row.get("split", "development"),
            "model": row["model"],
            "model_id": row["model_id"],
            "case_id": row["case_id"],
            "repeat": row["repeat"],
            "exposure_group": row["exposure_group"],
        }
        identity = row.get("identity") or {}
        if any(key in base and base[key] != value for key, value in identity.items()):
            raise ValueError("Answer identity conflicts with its planned slot")
        base.update(identity)
        answers.append(
            {
                **base,
                **answer_outcomes(row),
                "component_evaluation_complete": component_coverage(row),
                "route": report.get("route", "unavailable"),
                "coverage_complete": report.get("coverage_complete", False),
                "required_point_roster_available": row.get("candidate") is not None,
                "source_path": row.get("source_path"),
                **(row.get("complexity") or {}),
                "citation": report.get("automatic", {}).get("citation"),
                "automatic_details": report.get("automatic", {}),
                "component_details": [
                    {
                        key: result.get(key)
                        for key in (
                            "component",
                            "point_id",
                            "sample_id",
                            "payload_sha256",
                            "identity",
                            "status",
                            "decision",
                            "error",
                            "error_type",
                            "quotation_fidelity",
                        )
                    }
                    for result in report.get("results", [])
                ],
                "retrieval_status": "not_applicable",
                "retrieval_recall": None,
                "read_evidence_recall": None,
                "ranked_recall": None,
            }
        )
        observed_ids = set()
        for result in report.get("results", []):
            if result["component"] != "G":
                continue
            observed_ids.add(result["point_id"])
            points.append(
                {
                    **base,
                    "point_id": result["point_id"],
                    "sample_id": result["sample_id"],
                    "payload_sha256": result["payload_sha256"],
                    "group": result["group"],
                    "status": result["status"],
                    "outcome": judgment_state(result),
                    "citation_ids": result["citation_ids"],
                    "decision": result.get("decision"),
                    "error": result.get("error"),
                }
            )
        for group in ("supporting_points", "qualifications"):
            for point in (row.get("candidate") or {}).get(group, []):
                if point["point_id"] not in observed_ids:
                    points.append(
                        {
                            **base,
                            "point_id": point["point_id"],
                            "sample_id": None,
                            "payload_sha256": None,
                            "group": group,
                            "status": "missing_judgment",
                            "outcome": "unavailable",
                            "citation_ids": point.get("citation_ids"),
                            "decision": None,
                            "error": "Expected candidate point has no report result",
                        }
                    )
    summaries = []
    point_summaries = []
    for split in sorted({a["split"] for a in answers}):
        split_rows = [a for a in answers if a["split"] == split]
        for model in sorted({a["model"] for a in split_rows}):
            for group in _exposure_groups([a for a in split_rows if a["model"] == model]):
                selected = [
                    a
                    for a in split_rows
                    if a["model"] == model and (group == "all" or a["exposure_group"] == group)
                ]
                for repeat in (0, 1, 2, 3):
                    subset = [a for a in selected if repeat == 0 or a["repeat"] == repeat]
                    label = dict(split=split, model=model, exposure_group=group, repeat=repeat)
                    for component in COMPONENTS:
                        summaries.append(
                            {
                                **label,
                                "component": component,
                                **_counts([a[component] for a in subset]),
                                "complete_evaluations": sum(
                                    a["component_evaluation_complete"][component] for a in subset
                                ),
                            }
                        )
                    selected_keys = {(a["case_id"], a["repeat"]) for a in subset}
                    for point_group in ("supporting_points", "qualifications", "all"):
                        pp = [
                            p
                            for p in points
                            if p["split"] == split
                            and p["model"] == model
                            and (p["case_id"], p["repeat"]) in selected_keys
                            and (point_group == "all" or p["group"] == point_group)
                        ]
                        point_summaries.append(
                            {
                                **label,
                                "point_group": point_group,
                                "evaluation_unit": "point",
                                "answers": len(subset),
                                "answers_with_unknown_point_roster": sum(
                                    not a["required_point_roster_available"] for a in subset
                                ),
                                **_counts([p["outcome"] for p in pp]),
                            }
                        )
    questions = []
    for split, model, case in sorted({(a["split"], a["model"], a["case_id"]) for a in answers}):
        selected = [
            a for a in answers if (a["split"], a["model"], a["case_id"]) == (split, model, case)
        ]
        if {a["repeat"] for a in selected} != {1, 2, 3}:
            raise ValueError(
                "Planned triples must include explicit unavailable rows for absent slots"
            )
        for component in COMPONENTS:
            states = [next(a for a in selected if a["repeat"] == r)[component] for r in (1, 2, 3)]
            resolved = "unavailable" not in states
            applicable = states.count("not_applicable") == 0
            complete = resolved and applicable
            questions.append(
                {
                    "split": split,
                    "model": model,
                    "case_id": case,
                    "exposure_group": selected[0]["exposure_group"],
                    "component": component,
                    "repeat1": states[0],
                    "repeat2": states[1],
                    "repeat3": states[2],
                    **_counts(states),
                    "triple_complete": complete,
                    "triple_outcomes_resolved": resolved,
                    "triple_evaluation_complete": all(
                        a["component_evaluation_complete"][component] for a in selected
                    ),
                    "applicable_repeats": 3 - states.count("not_applicable"),
                    "pass_count": states.count("pass") if complete else None,
                    "observed_pass_count": states.count("pass"),
                    "at_least_once": states.count("pass") >= 1 if complete else None,
                    "every_time": states.count("pass") == 3 if complete else None,
                }
            )
    repeats = []
    for summary in summaries:
        if summary["repeat"] != 0:
            continue
        selected_q = [
            q
            for q in questions
            if all(q[k] == summary[k] for k in ("split", "model", "component"))
            and (
                summary["exposure_group"] == "all"
                or q["exposure_group"] == summary["exposure_group"]
            )
        ]
        repeats.append(
            {
                **{k: summary[k] for k in ("split", "model", "component", "exposure_group")},
                "planned_questions": len(selected_q),
                "complete_triples": sum(q["triple_complete"] for q in selected_q),
                "unresolved_triples": sum(not q["triple_outcomes_resolved"] for q in selected_q),
                "not_applicable_triples": sum(q["applicable_repeats"] == 0 for q in selected_q),
                "mixed_applicability_triples": sum(
                    0 < q["applicable_repeats"] < 3 and q["triple_outcomes_resolved"]
                    for q in selected_q
                ),
                "evaluation_complete_triples": sum(
                    q["triple_evaluation_complete"] for q in selected_q
                ),
                **{f"passes_{n}": sum(q["pass_count"] == n for q in selected_q) for n in range(4)},
                "at_least_once": sum(q["at_least_once"] is True for q in selected_q),
                "every_time": sum(q["every_time"] is True for q in selected_q),
            }
        )
    return dict(
        answers=answers,
        points=points,
        model_results=summaries,
        point_results=point_summaries,
        questions=questions,
        repeatability=repeats,
    )


def citation_tables(answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reuse 09D eligibility and counts for macro means and pooled micro arithmetic."""
    output = []
    for split, model in sorted({(a["split"], a["model"]) for a in answers}):
        model_rows = [a for a in answers if a["split"] == split and a["model"] == model]
        for group in _exposure_groups(model_rows):
            for repeat in (0, 1, 2, 3):
                rows = [
                    a
                    for a in answers
                    if a["split"] == split
                    and a["model"] == model
                    and (group == "all" or a["exposure_group"] == group)
                    and (repeat == 0 or a["repeat"] == repeat)
                ]
                metrics = [
                    CitationMetrics.model_validate(a["citation"])
                    for a in rows
                    if a["citation"] is not None
                ]
                eligible = [m for m in metrics if m.status == "eligible"]
                hits = sum(m.hits for m in eligible)
                support = sum(m.support_count for m in eligible)
                denominator = sum(m.precision_denominator for m in eligible)
                precision = hits / denominator if denominator else 0.0
                recall = hits / support if support else 0.0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
                output.append(
                    {
                        "split": split,
                        "model": model,
                        "exposure_group": group,
                        "repeat": repeat,
                        "planned": len(rows),
                        "eligible": len(eligible),
                        "not_applicable": sum(m.status == "not_applicable" for m in metrics),
                        "unavailable": len(rows) - sum(m.status != "unavailable" for m in metrics),
                        "hits": hits,
                        "support_count": support,
                        "precision_denominator": denominator,
                        "neutral_count": sum(m.neutral_count for m in eligible),
                        "invalid_token_observations": sum(
                            a.get("invalid_id_count", 0) for a in rows
                        ),
                        "answers_with_invalid_ids": sum(bool(a.get("invalid_ids")) for a in rows),
                        "invalid_id_audit_available": sum("invalid_ids" in a for a in rows),
                        "verified_delivery_answers": sum(
                            a.get("delivery_coverage") == 1.0 for a in rows
                        ),
                        "delivery_audit_available": sum(
                            a.get("delivery_coverage") is not None for a in rows
                        ),
                        "delivered_units": sum(a.get("delivered_citations") or 0 for a in rows),
                        "supplied_units": sum(a.get("input_citations") or 0 for a in rows),
                        **{
                            f"macro_{k}": sum(getattr(m, k) for m in eligible) / len(eligible)
                            if eligible
                            else None
                            for k in ("precision", "recall", "f1")
                        },
                        "micro_precision": precision if eligible else None,
                        "micro_recall": recall if eligible else None,
                        "micro_f1": f1 if eligible else None,
                    }
                )
    return output


def complexity_tables(
    answers: list[dict[str, Any]], *, primary_model: str = "luna"
) -> list[dict[str, Any]]:
    """Describe one explicit model's output associations using the frozen count bins."""
    if not primary_model or primary_model not in {a["model"] for a in answers}:
        raise ValueError("Complexity primary model must be present in the answer rows")
    output = []
    model_rows = [a for a in answers if a["model"] == primary_model]
    for split in sorted({a["split"] for a in model_rows}):
        rows = [a for a in model_rows if a["split"] == split]
        for covariate in (
            "citation_occurrences",
            "response_units",
            "documents",
            "input_response_units",
            "input_documents",
        ):
            for low, high, label in (*COUNT_BINS, (0, 0, "unavailable")):
                subset = [
                    a
                    for a in rows
                    if (
                        a.get(covariate) is None
                        if label == "unavailable"
                        else a.get(covariate) is not None
                        and a[covariate] >= low
                        and (high is None or a[covariate] <= high)
                    )
                ]
                for component in COMPONENTS:
                    per_question = []
                    for case in {a["case_id"] for a in subset}:
                        states = [a[component] for a in subset if a["case_id"] == case]
                        observed = [s for s in states if s in {"pass", "fail"}]
                        if observed:
                            per_question.append(observed.count("pass") / len(observed))
                    output.append(
                        {
                            "split": split,
                            "model": primary_model,
                            "covariate": covariate,
                            "bin": label,
                            "component": component,
                            **_counts([a[component] for a in subset]),
                            "unique_questions": len({a["case_id"] for a in subset}),
                            "repeat1_n": sum(a["repeat"] == 1 for a in subset),
                            "repeat2_n": sum(a["repeat"] == 2 for a in subset),
                            "repeat3_n": sum(a["repeat"] == 3 for a in subset),
                            "question_rate_min": min(per_question) if per_question else None,
                            "question_rate_max": max(per_question) if per_question else None,
                            "interpretation": (
                                "descriptive association; no causal or independent-sample claim"
                            ),
                        }
                    )
    return output
