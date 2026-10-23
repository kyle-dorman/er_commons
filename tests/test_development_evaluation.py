"""Offline whole-answer routing, exact joins and projection regression fixtures."""

import json
from copy import deepcopy

import pytest

from er_commons.artifact_io import json_bytes, sha256_bytes, stable_json_sha256
from er_commons.development_evaluation import build_report, pending_items, prepare_candidate


def fixture(answer=None):
    """Build a tiny sealed-shape development packet without external artifacts."""
    point = {"point_id": "p1", "text": "A basis.", "citation_ids": ["P1"], "applies_to": []}
    answer = answer or {
        "status": "answered",
        "conclusion": {**point, "point_id": "c"},
        "supporting_points": [point],
        "qualifications": [],
        "optional_context": [],
    }
    payload = {
        "question": "Why?",
        "passages": [
            {
                "citation_id": "P1",
                "source_id": "s",
                "title": "Title",
                "heading_path": [],
                "full_source_text": "Original source.",
                "tables": [],
                "physical_pages": [1],
                "printed_labels": [],
            }
        ],
    }
    record = {"schema_version": "task10.evidence_only.v1", "case_id": "C041", "payload": payload}
    mapping = {
        "case_id": "C041",
        "split": "dev",
        "payload_sha256": stable_json_sha256(payload),
        "passages": [
            {
                "citation_id": "P1",
                "canonical_unit": ["s", "e", "section", "u"],
                "reference_role": "support",
            }
        ],
    }
    raw = json_bytes(answer)
    identity = {
        "run_id": "r",
        "case_id": "C041",
        "candidate_sha256": sha256_bytes(raw),
        "repeat": 1,
        "attempt": 1,
        "request_sha256": "req",
    }
    identity["candidate_id"] = stable_json_sha256(identity)
    receipt = {
        "input": [
            {"role": "user", "content": [{"type": "input_text", "text": json.dumps(payload)}]}
        ]
    }
    return raw, identity, record, mapping, receipt, "Reference."


def judgment(item, raw):
    """Make an exactly bound saved judge response."""
    return {
        **{
            k: item[k] for k in ("sample_id", "identity", "component", "point_id", "payload_sha256")
        },
        "status": "completed",
        "raw_output": json.dumps(raw),
    }


def a_result(plan, classification="substantive"):
    """Supply the sole conclusion-only classification."""
    return judgment(
        plan["items"][0], {"classification": classification, "reason": "Original conclusion."}
    )


def test_isolation_and_coverage():
    plan = prepare_candidate(*fixture())
    assert [i["component"] for i in pending_items(plan, [])] == ["A"]
    rest = pending_items(plan, [a_result(plan)])
    assert [i["component"] for i in rest] == ["G", "S", "C"]
    assert set(rest[0]["packet"]) == {"question", "point_text", "evidence"}
    assert rest[0]["packet"]["evidence"][0]["full_source_text"] == "Original source."
    assert "reference_conclusion" not in rest[1]["packet"]
    assert set(rest[2]["packet"]) == {"question", "candidate_conclusion", "reference_conclusion"}
    report = build_report(plan, [a_result(plan)])
    assert not report["coverage_complete"]
    assert report["automatic"]["citation"]["f1"] == 1
    assert report["automatic"]["retrieval"]["status"] == "not_applicable"


@pytest.mark.parametrize(
    "classification,route", [("clean_abstention", "mixed_abstention"), ("ambiguous", "ambiguous")]
)
def test_nonempty_guard(classification, route):
    plan = prepare_candidate(*fixture())
    assert build_report(plan, [a_result(plan, classification)])["route"] == route
    assert not pending_items(plan, [a_result(plan, classification)])


def test_clean_abstention_and_empty_support():
    answer = json.loads(fixture()[0])
    answer["supporting_points"] = []
    plan = prepare_candidate(*fixture(answer))
    report = build_report(plan, [a_result(plan, "clean_abstention")])
    assert report["route"] == "clean_abstention"
    assert report["empty_support"]
    assert not pending_items(plan, [a_result(plan, "clean_abstention")])
    assert len(pending_items(plan, [a_result(plan)])) == 2


@pytest.mark.parametrize(
    "citations,error", [([], "missing_citation"), (["unknown"], "unresolved_citation")]
)
def test_precheck_retained_when_a_missing(citations, error):
    answer = json.loads(fixture()[0])
    answer["supporting_points"][0]["citation_ids"] = citations
    plan = prepare_candidate(*fixture(answer))
    report = build_report(plan, [])
    assert report["results"][1]["error_type"] == error
    assert report["results"][1]["status"] == "precheck_failed"


@pytest.mark.parametrize("field", ["identity", "point_id", "payload_sha256", "sample_id"])
def test_cross_identity_rejected(field):
    plan = prepare_candidate(*fixture())
    j = a_result(plan)
    j[field] = "wrong"
    with pytest.raises(ValueError):
        build_report(plan, [j])


def test_duplicate_and_invalid_output():
    plan = prepare_candidate(*fixture())
    j = a_result(plan)
    with pytest.raises(ValueError, match="Duplicate"):
        build_report(plan, [j, j])
    j["raw_output"] = "truncated"
    report = build_report(plan, [j])
    assert report["results"][0]["status"] == "invalid_output"
    assert not pending_items(plan, [j])


def test_repeat_and_delivery_integrity():
    args = list(fixture())
    first = prepare_candidate(*args)
    args[1] = deepcopy(args[1])
    args[1]["repeat"] = 2
    args[1]["candidate_id"] = stable_json_sha256(
        {k: v for k, v in args[1].items() if k != "candidate_id"}
    )
    second = prepare_candidate(*args)
    assert first["items"][0]["sample_id"] != second["items"][0]["sample_id"]
    args[4]["input"][0]["content"][0]["text"] = "{}"
    with pytest.raises(ValueError, match="Delivered"):
        prepare_candidate(*args)


def test_malformed_duplicate_points_and_unknown_prose():
    for mutate in (
        lambda a: a.update(extra="hidden"),
        lambda a: a["supporting_points"][0].update(point_id="c"),
    ):
        answer = json.loads(fixture()[0])
        mutate(answer)
        plan = prepare_candidate(*fixture(answer))
        assert build_report(plan, [])["route"] == "invalid_answer"
        assert not pending_items(plan, [])


def test_complete_report_keeps_semantic_failure_and_raw_response():
    plan = prepare_candidate(*fixture())
    judgments = [a_result(plan)]
    responses = {
        "G": {"supported": False, "reason": "Contradiction."},
        "S": {"support_sufficient": False, "reason_codes": ["invalid_inference"], "reason": "Gap."},
        "C": {
            "conclusion_adequate": True,
            "reason_codes": [],
            "reason": "Match.",
            "comparison": [
                {
                    "reference_quotes": ["Reference."],
                    "candidate_quotes": ["A basis."],
                    "status": "matched",
                    "reason": "Same claim.",
                }
            ],
        },
    }
    for item in pending_items(plan, judgments):
        judgments.append(judgment(item, responses[item["component"]]))
    report = build_report(plan, judgments)
    assert report["coverage_complete"]
    assert report["results"][1]["decision"]["supported"] is False
    assert report["results"][2]["decision"]["support_sufficient"] is False
    assert report["results"][3]["quotation_fidelity"]["ok"]
    assert report["results"][1]["raw_output"]
    assert not pending_items(plan, judgments)


def test_optional_context_blocks_abstention_but_is_not_grounding_dispatch():
    answer = json.loads(fixture()[0])
    answer["optional_context"] = [
        {"point_id": "o", "text": "Context.", "citation_ids": ["P1"], "applies_to": []}
    ]
    plan = prepare_candidate(*fixture(answer))
    assert len(plan["items"]) == 4
    report = build_report(plan, [a_result(plan, "clean_abstention")])
    assert report["route"] == "mixed_abstention"
    assert report["optional_context"]["points"] == answer["optional_context"]


def test_blocked_route_rejects_orphan_semantic_results():
    plan = prepare_candidate(*fixture())
    rows = [
        a_result(plan, "ambiguous"),
        judgment(plan["items"][1], {"supported": True, "reason": "Evidence."}),
    ]
    with pytest.raises(ValueError, match="routing"):
        build_report(plan, rows)


def test_known_g_failure_survives_s_provider_error():
    plan = prepare_candidate(*fixture())
    rows = [a_result(plan), judgment(plan["items"][1], {"supported": False, "reason": "Wrong."})]
    s = judgment(plan["items"][2], {})
    s.update(status="execution_error", error="Provider unavailable")
    report = build_report(plan, [*rows, s])
    assert report["results"][1]["decision"]["supported"] is False
    assert report["results"][2]["status"] == "execution_error"
    assert report["results"][3]["status"] == "missing_judgment"


def test_qualification_owned_tables_preserved():
    answer = json.loads(fixture()[0])
    answer["qualifications"] = [
        {"point_id": "q", "text": "Qualified.", "citation_ids": ["P1"], "applies_to": ["c"]}
    ]
    args = list(fixture(answer))
    p = args[2]["payload"]["passages"][0]
    p["heading_path"] = ["Conditional scenario"]
    p["tables"] = [{"cells": [{"text": "42", "row_index": 0, "column_index": 0}]}]
    args[3]["payload_sha256"] = stable_json_sha256(args[2]["payload"])
    args[4]["input"][0]["content"][0]["text"] = json.dumps(args[2]["payload"])
    plan = prepare_candidate(*args)
    g = [i for i in plan["items"] if i["component"] == "G"]
    assert [i["point_id"] for i in g] == ["p1", "q"]
    evidence = g[1]["packet"]["evidence"][0]
    assert evidence["tables"] == p["tables"]
    assert evidence["canonical_target"]["breadcrumb"] == [{"heading_text": "Conditional scenario"}]
    assert "A basis." not in json.dumps(g[1]["packet"])


@pytest.mark.parametrize("raw", [b"", b'{"status":', b"null"])
def test_malformed_saved_bytes_remain_visible(raw):
    args = list(fixture())
    args[0] = raw
    args[1]["candidate_sha256"] = sha256_bytes(raw)
    args[1]["candidate_id"] = stable_json_sha256(
        {k: v for k, v in args[1].items() if k != "candidate_id"}
    )
    plan = prepare_candidate(*args)
    assert build_report(plan, [])["route"] == "invalid_answer"


def test_known_evidence_loading_error_is_not_invalid_citation(monkeypatch):
    from er_commons import point_grounding

    original = point_grounding.prepare_point

    def broken_loader(question, text, citations, **kwargs):
        def unavailable(_citation):
            raise OSError("Unavailable artifact")

        return original(
            question,
            text,
            citations,
            allowed_citation_ids=kwargs["allowed_citation_ids"],
            load_evidence=unavailable,
        )

    monkeypatch.setattr(point_grounding, "prepare_point", broken_loader)
    report = build_report(prepare_candidate(*fixture()), [])
    assert report["results"][1]["status"] == "execution_error"
    assert report["results"][1]["error_type"] == "source_loading_error"
    assert report["automatic"]["resolved_citations"]


def structured_plan():
    """Make a v6 plan while preserving all non-conclusion inputs."""
    from er_commons.conclusion_structured import VERSION_V6

    return prepare_candidate(
        *fixture(),
        structured_reference={
            "reference_required_points": [{"point_id": "R1", "text": "A basis."}],
            "reference_optional_points": [{"point_id": "O1", "text": "Additional detail."}],
        },
        conclusion_prompt_version=VERSION_V6,
    )


def structured_judgment(plan, *, missing_optional=False):
    """Keep a model pass that disagrees with its internal contradiction flag."""
    item = plan["items"][-1]
    output = {
        "judgments": [
            {
                "point_id": "R1",
                "status": "satisfied",
                "candidate_quotes": ["A basis."],
                "reason": "Present.",
            },
            {
                "point_id": "O1",
                "status": "not_addressed",
                "candidate_quotes": [],
                "reason": "Absent.",
            },
        ],
        "internal_contradictions": [{"reason": "Claims conflict."}],
        "conclusion_adequate": True,
        "reason": "Model verdict retained for consistency diagnostics.",
    }
    if missing_optional:
        output["judgments"].pop()
    return {**judgment(item, output), **{k: item[k] for k in ("prompt_version", "input_version")}}


def test_structured_opt_in_preserves_routing_and_non_c_projections():
    legacy, current = prepare_candidate(*fixture()), structured_plan()
    assert legacy["items"][:-1] == current["items"][:-1]
    assert current["items"][-1]["sample_id"] != legacy["items"][-1]["sample_id"]
    assert [i["component"] for i in pending_items(current, [])] == ["A"]
    assert [i["component"] for i in pending_items(current, [a_result(current)])] == ["G", "S", "C"]
    assert set(current["items"][-1]["packet"]) == {
        "question",
        "candidate_conclusion",
        "reference_required_points",
        "reference_optional_points",
    }
    report = build_report(current, [a_result(current), structured_judgment(current)])
    c = report["results"][-1]
    assert c["status"] == "completed"
    assert c["decision"]["conclusion_adequate"] is True
    assert c["model_decision"] is True and c["aggregate_decision"] is False
    assert c["aggregation_consistent"] is False
    assert c["internal_contradictions_pass_inconsistent"] is True


def test_structured_inventory_failure_is_unavailable_not_semantic_fail():
    plan = structured_plan()
    c = build_report(plan, [a_result(plan), structured_judgment(plan, missing_optional=True)])[
        "results"
    ][-1]
    assert c["status"] == "invalid_output" and c["decision"] is None
    assert "aggregate_decision" not in c


def test_structured_join_rejects_changed_version():
    plan = structured_plan()
    result = structured_judgment(plan)
    result["input_version"] = "changed"
    with pytest.raises(ValueError, match="version mismatch"):
        build_report(plan, [a_result(plan), result])


def test_structured_reference_requires_explicit_version():
    with pytest.raises(ValueError, match="explicit conclusion v6"):
        prepare_candidate(*fixture(), structured_reference={})
