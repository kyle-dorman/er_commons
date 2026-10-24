"""Real-answer coverage isolates fields and preserves diagnostic uncertainty."""

import json

import pytest

from er_commons.task15ad_coverage import join_coverage, project_coverage


def point(pid, text):
    return {"point_id": pid, "text": text, "citation_ids": [], "applies_to": []}


def projected():
    answer = {
        "status": "answered",
        "conclusion": point("C", "Hidden conclusion"),
        "supporting_points": [point("P1", "Visible support")],
        "qualifications": [point("Q1", "Hidden qualification")],
        "optional_context": [point("O1", "Hidden context")],
    }
    return project_coverage(
        answer,
        question="Question?",
        required_points=[{"point_id": "R1", "text": "Required claim"}],
        identity={"case_id": "fixture", "repeat": 1},
    )


def judgment(row, **overrides):
    return {
        **{k: v for k, v in row.items() if k != "packet"},
        "status": "completed",
        "raw_output": json.dumps(
            {"covered": True, "supporting_point_ids": ["P1"], "reason": "Supported"}
        ),
        **overrides,
    }


def evaluation(rows, missing=None, grounding=None):
    return {
        "identity": rows[0]["identity"],
        "candidate_sha256": rows[0]["candidate_sha256"],
        "c_missing_ids": missing,
        "grounding": grounding or {},
    }


def test_isolation_and_identity():
    row = projected()[0]
    assert "Hidden" not in json.dumps(row["packet"])
    assert set(row["packet"]) == {
        "question",
        "required_reference_point",
        "candidate_supporting_points",
    }
    assert row["required_point_id"] == "R1"


def test_diagnostic_join_preserves_unavailable_grounding():
    rows = projected()
    result = join_coverage(rows, [judgment(rows[0])], evaluation=evaluation(rows, ["R1"]))
    assert result["diagnostic_only"] and not result["adds_overall_pass_requirement"]
    row = result["rows"][0]
    assert row["support_covered_c_missing"] is True
    assert row["witness_grounding"] == [
        {"point_id": "P1", "status": "unavailable", "supported": None}
    ]


def test_invalid_output_has_no_semantic_verdict():
    rows = projected()
    bad = json.dumps({"covered": False, "supporting_point_ids": ["P1"], "reason": "Missing"})
    row = join_coverage(rows, [judgment(rows[0], raw_output=bad)], evaluation=evaluation(rows))[
        "rows"
    ][0]
    assert row["status"] == "invalid_output"
    assert row["decision"] is None and row["support_covered_c_missing"] is None


def test_cross_answer_and_unknown_reference_rejected():
    rows = projected()
    with pytest.raises(ValueError, match="binding"):
        join_coverage(
            rows, [judgment(rows[0], candidate_sha256="different")], evaluation=evaluation(rows, [])
        )
    with pytest.raises(ValueError, match="reference"):
        join_coverage(rows, [], evaluation=evaluation(rows, ["R2"]))


def test_no_judgment_is_unavailable_not_false():
    rows = projected()
    row = join_coverage(rows, [], evaluation=evaluation(rows, []))["rows"][0]
    assert row["status"] == "missing_judgment" and row["decision"] is None


def test_cross_answer_evaluation_and_changed_bindings_rejected():
    rows = projected()
    other = evaluation(rows)
    other["candidate_sha256"] = "another-answer"
    with pytest.raises(ValueError, match="C/G"):
        join_coverage(rows, [], evaluation=other)
    for key in ("required_point_id", "sample_id"):
        changed = [{**rows[0], key: "changed"}]
        with pytest.raises(ValueError, match="binding"):
            join_coverage(changed, [], evaluation=evaluation(rows))
