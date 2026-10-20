"""Offline reporting truth tables with invented answers and explicit planned slots."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from er_commons.reporting import (
    answer_outcomes,
    answer_tables,
    citation_tables,
    complexity_tables,
)


def observation(repeat: int = 1) -> dict[str, Any]:
    """Make an invented complete answer with one required point and isolated decisions."""
    results = [
        {
            "component": component,
            "point_id": "p1" if component == "G" else None,
            "sample_id": f"sample-{repeat}-{component}",
            "payload_sha256": f"payload-{repeat}-{component}",
            "group": "supporting_points" if component == "G" else None,
            "citation_ids": ["P1"],
            "status": "completed",
            "decision": decision,
        }
        for component, decision in (
            ("A", {"classification": "substantive"}),
            ("G", {"supported": True}),
            ("S", {"support_sufficient": True}),
            ("C", {"conclusion_adequate": True}),
        )
    ]
    return {
        "model": "luna",
        "model_id": "invented-model",
        "case_id": "invented-case",
        "repeat": repeat,
        "split": "development",
        "exposure_group": "fixed_six",
        "identity": {
            "run_id": "invented-run",
            "candidate_id": f"invented-candidate-{repeat}",
            "candidate_sha256": f"invented-bytes-{repeat}",
            "attempt": 1,
            "request_sha256": f"invented-request-{repeat}",
        },
        "candidate": {
            "supporting_points": [{"point_id": "p1", "citation_ids": ["P1"]}],
            "qualifications": [],
        },
        "report": {
            "route": "substantive",
            "coverage_complete": True,
            "support_structure": "present",
            "results": results,
            "automatic": {
                "schema": "valid",
                "delivery": "exact_payload_verified",
                "resolved_citations": True,
                "uncited_point_ids": [],
            },
        },
        "complexity": {"citation_occurrences": 2, "response_units": 1, "documents": 1},
    }


def result(row: dict[str, Any], component: str) -> dict[str, Any]:
    """Find an invented component for one deliberate fixture mutation."""
    return next(r for r in row["report"]["results"] if r["component"] == component)


def select(rows: list[dict[str, Any]], **fields: Any) -> dict[str, Any]:
    """Require one unambiguous table row for an independently calculated expectation."""
    matches = [row for row in rows if all(row[k] == v for k, v in fields.items())]
    assert len(matches) == 1
    return matches[0]


def test_known_failure_survives_missing_required_point_and_evaluator_error() -> None:
    row = observation()
    row["candidate"]["qualifications"] = [{"point_id": "q1", "citation_ids": ["P1"]}]
    result(row, "G")["decision"]["supported"] = False
    result(row, "S").update(status="execution_error", decision=None)
    row["report"]["coverage_complete"] = False
    states = answer_outcomes(row)
    assert states["G"] == states["joint"] == "fail"
    assert states["S"] == "unavailable"

    rows = [deepcopy(row) for _ in range(3)]
    for repeat, item in enumerate(rows, 1):
        item["repeat"] = repeat
    question = select(answer_tables(rows)["questions"], component="G")
    assert question["triple_outcomes_resolved"]
    assert not question["triple_evaluation_complete"]
    assert question["pass_count"] == 0


def test_missing_required_point_never_becomes_vacuous_success() -> None:
    row = observation()
    row["candidate"]["qualifications"] = [{"point_id": "q1", "citation_ids": ["P1"]}]
    assert answer_outcomes(row)["G"] == "unavailable"
    assert answer_outcomes(row)["joint"] == "unavailable"
    row["report"]["support_structure"] = "missing_basis"
    assert answer_outcomes(row)["G"] == "fail"


@pytest.mark.parametrize("orphan", [False, True])
def test_duplicate_or_orphan_required_points_are_rejected(orphan: bool) -> None:
    row = observation()
    added = deepcopy(result(row, "G"))
    if orphan:
        added["point_id"] = "not-in-answer"
    row["report"]["results"].append(added)
    with pytest.raises(ValueError, match="Duplicate or orphan"):
        answer_outcomes(row)


def test_clean_abstention_has_no_measured_semantic_zero_pass_triple() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    for row in rows:
        row["candidate"]["supporting_points"] = []
        row["report"].update(route="clean_abstention", support_structure="not_applicable")
        row["report"]["results"] = [r for r in row["report"]["results"] if r["component"] != "G"]
        for component in ("S", "C"):
            result(row, component).update(status="skipped_clean_abstention", decision=None)
    tables = answer_tables(rows)
    for component in ("G", "S", "C"):
        question = select(tables["questions"], component=component)
        assert question["applicable_repeats"] == 0
        assert question["triple_outcomes_resolved"]
        assert not question["triple_complete"]
        assert question["pass_count"] is None
        assert question["at_least_once"] is None
        repeat = select(tables["repeatability"], component=component, exposure_group="all")
        assert repeat["not_applicable_triples"] == 1
        assert repeat["passes_0"] == 0
    assert select(tables["questions"], component="A")["pass_count"] == 0
    assert select(tables["questions"], component="joint")["pass_count"] == 0


def test_missing_repeat_keeps_planned_and_observed_denominators() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    result(rows[1], "C")["decision"]["conclusion_adequate"] = False
    rows[2]["report"] = None
    tables = answer_tables(rows)
    summary = select(tables["model_results"], component="joint", repeat=0, exposure_group="all")
    assert summary["planned"] == 3
    assert summary["observed"] == 2
    assert summary["unavailable"] == 1
    assert summary["planned_pass_fraction"] == pytest.approx(1 / 3)
    assert summary["observed_pass_fraction"] == 0.5
    question = select(tables["questions"], component="joint")
    assert question["pass_count"] is None
    assert question["observed_pass_count"] == 1
    assert not question["triple_complete"]
    repeat = select(tables["repeatability"], component="joint", exposure_group="all")
    assert repeat["unresolved_triples"] == 1
    assert sum(repeat[f"passes_{n}"] for n in range(4)) == 0


def test_complementary_component_passes_cannot_be_stitched_across_repeats() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    for row, component, key in zip(
        rows,
        ("G", "S", "C"),
        ("supported", "support_sufficient", "conclusion_adequate"),
        strict=True,
    ):
        result(row, component)["decision"][key] = False
    questions = answer_tables(rows)["questions"]
    assert select(questions, component="joint")["pass_count"] == 0
    assert all(select(questions, component=c)["pass_count"] == 2 for c in ("G", "S", "C"))


def test_missing_automatic_field_is_unavailable_not_an_invented_failure() -> None:
    row = observation()
    del row["report"]["automatic"]["delivery"]
    assert answer_outcomes(row)["automatic"] == "unavailable"
    assert answer_outcomes(row)["joint"] == "unavailable"
    row["report"]["automatic"]["resolved_citations"] = False
    assert answer_outcomes(row)["automatic"] == "fail"
    assert answer_outcomes(row)["joint"] == "fail"


def test_split_identity_remains_separate_and_duplicate_slots_rejected() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    # Invented test-shaped rows exercise schema separation without loading held-out material.
    other = deepcopy(rows)
    for row in other:
        row["split"] = "invented_other_split"
        result(row, "C")["decision"]["conclusion_adequate"] = False
    summaries = answer_tables(rows + other)["model_results"]
    assert (
        select(summaries, split="development", exposure_group="all", component="joint", repeat=0)[
            "pass"
        ]
        == 3
    )
    assert (
        select(
            summaries,
            split="invented_other_split",
            exposure_group="all",
            component="joint",
            repeat=0,
        )["fail"]
        == 3
    )
    with pytest.raises(ValueError, match="Duplicate"):
        answer_tables(rows + [deepcopy(rows[0])])
    with pytest.raises(ValueError, match="triples"):
        answer_tables(rows[:2])


def test_pooled_exposure_is_not_aggregated_twice() -> None:
    """A new cohort already labeled all must have one summary for each metric."""
    rows = [observation(r) for r in (1, 2, 3)]
    for row in rows:
        row["exposure_group"] = "all"
    tables = answer_tables(rows)
    summary = select(tables["model_results"], component="joint", repeat=0)
    assert summary["planned"] == summary["pass"] == 3
    assert select(tables["repeatability"], component="joint")["every_time"] == 1
    assert select(tables["point_results"], point_group="all", repeat=0)["planned"] == 3
    assert select(citation_tables(tables["answers"]), repeat=0)["planned"] == 3


@pytest.mark.parametrize("field,value", [("case_id", "other-case"), ("repeat", 2)])
def test_nested_identity_cannot_overwrite_planned_slot(field: str, value: Any) -> None:
    """Reject mismatched provenance instead of silently changing grouping keys."""
    rows = [observation(r) for r in (1, 2, 3)]
    rows[0]["identity"][field] = value
    with pytest.raises(ValueError, match="identity conflicts"):
        answer_tables(rows)


def test_citation_macro_micro_and_unavailable_populations() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    for row, values in zip(
        rows[:2],
        (
            dict(
                hits=1,
                support_count=1,
                precision_denominator=1,
                precision=1.0,
                recall=1.0,
                f1=1.0,
                neutral_count=2,
            ),
            dict(
                hits=1,
                support_count=3,
                precision_denominator=2,
                precision=0.5,
                recall=1 / 3,
                f1=0.4,
                neutral_count=0,
            ),
        ),
        strict=True,
    ):
        row["report"]["automatic"]["citation"] = {"status": "eligible", **values}
    tables = citation_tables(answer_tables(rows)["answers"])
    summary = select(tables, exposure_group="all", repeat=0)
    assert (summary["planned"], summary["eligible"], summary["unavailable"]) == (3, 2, 1)
    assert summary["macro_precision"] == 0.75
    assert summary["macro_recall"] == pytest.approx(2 / 3)
    assert summary["macro_f1"] == 0.7
    assert summary["micro_precision"] == pytest.approx(2 / 3)
    assert summary["micro_recall"] == 0.5
    assert summary["micro_f1"] == pytest.approx(4 / 7)
    assert summary["neutral_count"] == 2
    empty = select(tables, exposure_group="all", repeat=3)
    assert empty["micro_f1"] is None and empty["macro_f1"] is None


def test_complexity_bins_preserve_question_and_repeat_denominators() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    rows[2]["complexity"]["response_units"] = None
    result(rows[1], "C")["decision"]["conclusion_adequate"] = False
    table = complexity_tables(answer_tables(rows)["answers"])
    citations = select(table, covariate="citation_occurrences", bin="1–2", component="joint")
    assert citations["planned"] == 3
    assert citations["unique_questions"] == 1
    assert [citations[f"repeat{r}_n"] for r in (1, 2, 3)] == [1, 1, 1]
    assert citations["observed_pass_fraction"] == pytest.approx(2 / 3)
    unavailable = select(table, covariate="response_units", bin="unavailable", component="joint")
    assert unavailable["planned"] == 1


def test_complexity_model_selection_is_explicit_and_preserves_denominators() -> None:
    """Future model variants use their own labels and never emit empty Luna statistics."""
    rows = [observation(r) for r in (1, 2, 3)]
    for row in rows:
        row["model"] = "future-model"
    answers = answer_tables(rows)["answers"]
    table = complexity_tables(answers, primary_model="future-model")
    assert {row["model"] for row in table} == {"future-model"}
    assert select(table, covariate="response_units", bin="1–2", component="joint")["planned"] == 3
    with pytest.raises(ValueError, match="primary model"):
        complexity_tables(answers)
    with pytest.raises(ValueError, match="primary model"):
        complexity_tables(answers, primary_model="")


def test_missing_required_judgments_remain_in_point_denominators() -> None:
    rows = [observation(r) for r in (1, 2, 3)]
    for row in rows:
        row["candidate"]["qualifications"] = [{"point_id": "q1", "citation_ids": ["P1"]}]
        row["report"]["coverage_complete"] = False
    tables = answer_tables(rows)
    summary = select(tables["point_results"], exposure_group="all", repeat=0, point_group="all")
    assert (summary["planned"], summary["pass"], summary["unavailable"]) == (6, 3, 3)
    qualifications = select(
        tables["point_results"], exposure_group="all", repeat=0, point_group="qualifications"
    )
    assert qualifications["planned"] == qualifications["unavailable"] == 3
    missing = [p for p in tables["points"] if p["point_id"] == "q1"]
    assert len(missing) == 3
    assert all(p["status"] == "missing_judgment" for p in missing)
    assert all(p["sample_id"] is None and p["decision"] is None for p in missing)


def test_invalid_answer_fails_automatic_checks_without_inventing_a_judgment() -> None:
    row = observation()
    row["candidate"] = None
    row["report"].update(
        route="invalid_answer",
        coverage_complete=False,
        support_structure="unavailable",
        results=[],
        automatic={"schema": "invalid"},
    )
    states = answer_outcomes(row)
    assert states["A"] == "unavailable"
    assert states["automatic"] == states["joint"] == "fail"
    assert all(states[c] == "unavailable" for c in ("G", "S", "C"))


def test_citation_chart_renders_no_eligible_observations(tmp_path: Path) -> None:
    from er_commons.reporting_charts import _citation_chart

    rows = [
        {
            "model": model,
            "exposure_group": "all",
            "repeat": 0,
            "eligible": 0,
            "planned": 3,
            **{
                f"{aggregation}_{metric}": None
                for aggregation in ("macro", "micro")
                for metric in ("precision", "recall", "f1")
            },
        }
        for model in ("luna", "haiku")
    ]
    _citation_chart(rows, tmp_path)
    png = (tmp_path / "returned_citations.png").read_bytes()
    svg = (tmp_path / "returned_citations.svg").read_text()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert "<svg" in svg
    assert "Unavailable / no eligible observations" in svg
