"""Current RC planning retains decision scoring and exact C comparison statuses."""

import json
from copy import deepcopy

import pytest
from test_development_evaluation import a_result, fixture, judgment

from er_commons import current_judges, development_evaluation
from er_commons.reporting import answer_outcomes

REFERENCE = {
    "reference_required_points": [{"point_id": "R1", "text": "A basis."}],
    "reference_optional_points": [],
}


def plan_for(answer=None):
    return current_judges.prepare_candidate(*fixture(answer), structured_reference=REFERENCE)


def c_judgment(plan, status):
    item = next(i for i in plan["decision_plan"]["items"] if i["component"] == "C")
    output = {
        "judgments": [
            {
                "point_id": "R1",
                "status": status,
                "candidate_quotes": ["A basis."] if status != "missing" else [],
                "reason": "Fixture.",
            }
        ],
        "internal_contradictions": [],
        "conclusion_adequate": status == "satisfied",
        "reason": "Fixture.",
    }
    return {**judgment(item, output), **{k: item[k] for k in ("prompt_version", "input_version")}}


def rc_judgment(plan, covered=True):
    projection = plan["rc_plan"]["projections"][0]
    return {
        **{k: v for k, v in projection.items() if k != "packet"},
        "status": "completed",
        "raw_output": json.dumps(
            {
                "covered": covered,
                "supporting_point_ids": ["p1"] if covered else [],
                "reason": "Fixture.",
            }
        ),
    }


@pytest.mark.parametrize("status", ["satisfied", "missing", "contradicted"])
@pytest.mark.parametrize("covered", [True, False])
def test_exact_c_status_comparison_does_not_change_scoring(status, covered):
    plan = plan_for()
    judges = [a_result(plan["decision_plan"]), c_judgment(plan, status)]
    baseline = development_evaluation.build_report(plan["decision_plan"], judges)
    with_rc = current_judges.build_report(plan, judges, [rc_judgment(plan, covered)])
    missing_rc = current_judges.build_report(plan, judges, [])
    assert with_rc["report"] == missing_rc["report"] == baseline
    candidate = json.loads(fixture()[0])
    assert answer_outcomes({"report": baseline, "candidate": candidate}) == answer_outcomes(
        {**with_rc, "candidate": candidate}
    )
    row = with_rc["rc"]["rows"][0]
    assert row["c_status"] == status
    assert row["comparison"] == ("covered" if covered else "not_covered") + "/" + status
    assert with_rc["rc_complete"] and not missing_rc["rc_complete"]
    assert missing_rc["rc"]["rows"][0]["decision"] is None


def test_pending_routes_a_first_and_requires_rc_afterward():
    plan = plan_for()
    before = current_judges.pending_items(plan, [], [])
    assert [i["component"] for i in before["decision_items"]] == ["A"]
    assert before["rc_items"] == []
    after = current_judges.pending_items(plan, [a_result(plan["decision_plan"])], [])
    assert len(after["rc_items"]) == 1
    assert after["rc_items"][0]["packet"]["candidate_supporting_points"] == [
        {"point_id": "p1", "text": "A basis."}
    ]
    c = next(i for i in after["decision_items"] if i["component"] == "C")
    s = next(i for i in after["decision_items"] if i["component"] == "S")
    assert c["prompt_version"].endswith(".v6")
    assert s["prompt_version"].endswith(".v9")


def test_c_unavailable_is_not_missing_or_satisfied():
    plan = plan_for()
    result = current_judges.build_report(
        plan, [a_result(plan["decision_plan"])], [rc_judgment(plan)]
    )
    row = result["rc"]["rows"][0]
    assert row["decision"]["covered"] is True
    assert row["c_status"] == row["comparison"] == "unavailable"


def test_skipped_and_invalid_answers_retain_required_rows():
    plan = plan_for()
    judges = [a_result(plan["decision_plan"], "ambiguous")]
    result = current_judges.build_report(plan, judges, [])
    assert result["rc"]["rows"][0]["status"] == "skipped_ambiguous"
    assert result["rc_complete"]
    with pytest.raises(ValueError, match="routing"):
        current_judges.build_report(plan, judges, [rc_judgment(plan)])
    invalid = plan_for({"status": "bad"})
    result = current_judges.build_report(invalid, [], [])
    assert result["rc"]["rows"][0]["status"] == "skipped_invalid_answer"
    assert not result["rc_complete"]


def test_changed_plan_and_cross_answer_judgments_rejected():
    plan = plan_for()
    changed = deepcopy(plan)
    changed["rc_plan"]["required_point_ids"] = []
    with pytest.raises(ValueError, match="binding"):
        current_judges.build_report(changed, [], [])
    judges = [a_result(plan["decision_plan"])]
    rc = rc_judgment(plan)
    rc["candidate_sha256"] = "other"
    with pytest.raises(ValueError, match="binding"):
        current_judges.build_report(plan, judges, [rc])
    c = c_judgment(plan, "satisfied")
    c["identity"] = {**c["identity"], "candidate_id": "other"}
    with pytest.raises(ValueError, match="mismatch"):
        current_judges.build_report(plan, [*judges, c], [])


def test_invalid_rc_is_unavailable_and_not_retried():
    plan = plan_for()
    judges = [a_result(plan["decision_plan"])]
    rc = rc_judgment(plan)
    rc["raw_output"] = "not json"
    result = current_judges.build_report(plan, judges, [rc])
    assert result["rc"]["rows"][0]["status"] == "invalid_output"
    assert result["rc"]["rows"][0]["decision"] is None
    assert not result["rc_complete"]
    assert current_judges.pending_items(plan, judges, [rc])["rc_items"] == []


def test_false_and_missing_rc_preserve_an_actual_joint_pass():
    plan = plan_for()
    judges = [a_result(plan["decision_plan"]), c_judgment(plan, "satisfied")]
    for item in plan["decision_plan"]["items"]:
        if item["component"] not in {"G", "S"}:
            continue
        key = "supported" if item["component"] == "G" else "support_sufficient"
        output = {key: True, "reason": "Established."}
        if item["component"] == "S":
            output["reason_codes"] = []
        receipt = judgment(item, output)
        receipt.update({k: item[k] for k in ("prompt_version", "input_version") if k in item})
        judges.append(receipt)
    for rc in ([], [rc_judgment(plan, False)]):
        result = current_judges.build_report(plan, judges, rc)
        assert answer_outcomes({**result, "candidate": json.loads(fixture()[0])})["joint"] == "pass"
