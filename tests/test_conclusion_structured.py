"""Structured C contracts bind judgments to explicit required and optional points."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons import adequacy_binary as core


def packet() -> dict[str, Any]:
    """Reuse existing contract fixture text without creating benchmark examples."""
    return {
        "question": "Can it restore?",
        "candidate_conclusion": "No.",
        "reference_required_points": [{"point_id": "R1", "text": "No."}],
        "reference_optional_points": [{"point_id": "O1", "text": "For this snapshot."}],
    }


def judgment() -> dict[str, Any]:
    """Provide a passing wire response with the optional point omitted."""
    return {
        "judgments": [
            {
                "point_id": "R1",
                "status": "satisfied",
                "candidate_quotes": ["No."],
                "reason": "The required meaning is present.",
            },
            {
                "point_id": "O1",
                "status": "not_addressed",
                "candidate_quotes": [],
                "reason": "The optional qualification is omitted.",
            },
        ],
        "conclusion_adequate": True,
        "reason": "All required points are satisfied without contradiction.",
    }


def parse(value: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind output validation to the precise input reference inventory."""
    return core.parse_output(
        "C",
        json.dumps(value),
        prompt_version=core.CONCLUSION_STRUCTURED_PROMPT_VERSION,
        payload=packet() if payload is None else payload,
    )


def test_structured_input_preserves_text_and_permits_no_optional_points() -> None:
    """Optional content can be absent without changing the required contract."""
    payload = packet()
    payload["reference_optional_points"] = []
    payload["candidate_conclusion"] = " No. \n"
    original = copy.deepcopy(payload)
    assert (
        core.validate_input("C", payload, prompt_version=core.CONCLUSION_STRUCTURED_PROMPT_VERSION)
        == original
    )
    assert payload == original


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate",
        "wrong_required_prefix",
        "wrong_optional_prefix",
        "empty_required",
        "blank",
        "extra",
        "nonsequential",
    ],
)
def test_structured_input_rejects_invalid_point_inventory(defect: str) -> None:
    """Point IDs, nonempty requirements, and input isolation are enforceable boundaries."""
    payload = packet()
    if defect == "duplicate":
        payload["reference_required_points"] *= 2
    elif defect == "wrong_required_prefix":
        payload["reference_required_points"][0]["point_id"] = "O1"
    elif defect == "wrong_optional_prefix":
        payload["reference_optional_points"][0]["point_id"] = "R2"
    elif defect == "empty_required":
        payload["reference_required_points"] = []
    elif defect == "blank":
        payload["reference_required_points"][0]["text"] = " "
    elif defect == "nonsequential":
        payload["reference_required_points"][0]["point_id"] = "R2"
    else:
        payload["reference_required_points"][0]["expected_label"] = True
    with pytest.raises(ValueError):
        core.validate_input("C", payload, prompt_version=core.CONCLUSION_STRUCTURED_PROMPT_VERSION)


def test_optional_omission_passes_and_judgment_order_is_not_semantic() -> None:
    """The optional inventory is covered even when no optional meaning is discussed."""
    value = judgment()
    value["judgments"].reverse()
    parsed = parse(value)
    assert parsed["conclusion_adequate"] is True
    assert {row["point_id"]: row["status"] for row in parsed["judgments"]} == {
        "R1": "satisfied",
        "O1": "not_addressed",
    }


@pytest.mark.parametrize("defect", ["missing", "extra", "duplicate", "wrong_id"])
def test_output_requires_exact_reference_point_coverage(defect: str) -> None:
    """A plausible aggregate cannot conceal dropped, duplicated, or invented judgments."""
    value = judgment()
    if defect == "missing":
        value["judgments"].pop()
    elif defect == "extra":
        value["judgments"].append(value["judgments"][0] | {"point_id": "R2"})
    elif defect == "duplicate":
        value["judgments"][1] = copy.deepcopy(value["judgments"][0])
    else:
        value["judgments"][1]["point_id"] = "O2"
    with pytest.raises(ValueError):
        parse(value)


@pytest.mark.parametrize(
    ("index", "status"),
    [
        (0, "not_addressed"),
        (0, "addressed_without_contradiction"),
        (1, "missing"),
        (1, "satisfied"),
    ],
)
def test_status_is_constrained_by_reference_role(index: int, status: str) -> None:
    """Required and optional points have distinct omission and satisfaction meanings."""
    value = judgment()
    value["judgments"][index]["status"] = status
    with pytest.raises(ValueError):
        parse(value)


@pytest.mark.parametrize(
    ("index", "status"), [(0, "missing"), (0, "contradicted"), (1, "contradicted")]
)
def test_each_required_failure_or_optional_contradiction_forces_failure(
    index: int, status: str
) -> None:
    """No averaging or correct optional material can cancel a point-level failure."""
    value = judgment()
    value["judgments"][index]["status"] = status
    value["judgments"][index]["candidate_quotes"] = [] if status == "missing" else ["No."]
    value["conclusion_adequate"] = False
    assert parse(value)["conclusion_adequate"] is False
    value["conclusion_adequate"] = True
    with pytest.raises(ValueError):
        parse(value)


def test_false_aggregate_cannot_invent_failure_outside_reference_points() -> None:
    """Passing point judgments must produce a pass without an additions category."""
    value = judgment()
    value["judgments"][1]["status"] = "addressed_without_contradiction"
    value["judgments"][1]["candidate_quotes"] = ["No."]
    assert parse(value)["conclusion_adequate"] is True
    value["conclusion_adequate"] = False
    with pytest.raises(ValueError):
        parse(value)


def test_structured_parse_requires_input_binding() -> None:
    """Output-only parsing cannot verify completeness against an unknown reference."""
    with pytest.raises(ValueError):
        core.parse_output(
            "C", json.dumps(judgment()), prompt_version=core.CONCLUSION_STRUCTURED_PROMPT_VERSION
        )


def test_structured_and_historical_input_contracts_do_not_silently_mix() -> None:
    """Historical reference prose must not be implicitly relabeled into requirements."""
    with pytest.raises(ValueError):
        core.validate_input("C", packet())
    legacy = {
        "question": "Can it restore?",
        "candidate_conclusion": "No.",
        "reference_conclusion": "No.",
    }
    with pytest.raises(ValueError):
        core.validate_input("C", legacy, prompt_version=core.CONCLUSION_STRUCTURED_PROMPT_VERSION)


@pytest.mark.parametrize(
    ("index", "status", "quotes"),
    [
        (0, "missing", ["No."]),
        (0, "satisfied", []),
        (0, "contradicted", []),
        (1, "not_addressed", ["No."]),
        (1, "addressed_without_contradiction", []),
        (1, "contradicted", []),
    ],
)
def test_excerpts_follow_status_presence(index: int, status: str, quotes: list[str]) -> None:
    """Absent meanings have no excerpts; claims judged present require excerpts."""
    value = judgment()
    value["judgments"][index].update(status=status, candidate_quotes=quotes)
    value["conclusion_adequate"] = status not in {"missing", "contradicted"}
    with pytest.raises(ValueError):
        parse(value)


def test_quote_mismatch_is_diagnostic_not_a_semantic_rewrite() -> None:
    """Literal quote errors remain visible without silently flipping the C verdict."""
    value = judgment()
    value["judgments"][0]["candidate_quotes"] = ["File postdates snapshot."]
    parsed = parse(value)
    assert parsed["conclusion_adequate"] is True
    assert parsed["reason"] == value["reason"]
    diagnostics = core.quote_fidelity_diagnostics(json.dumps(value), packet())
    assert diagnostics["ok"] is False
    assert diagnostics["issues"]


@pytest.mark.parametrize(
    "version",
    [core.CONCLUSION_STRUCTURED_V2_PROMPT_VERSION, core.CONCLUSION_STRUCTURED_V3_PROMPT_VERSION],
)
@pytest.mark.parametrize(("index", "status"), [(0, "missing"), (1, "not_addressed")])
def test_relaxed_versions_allow_partial_quotes_for_absent_meaning(
    index: int, status: str, version: str
) -> None:
    """Useful insufficiency excerpts are valid only under the new explicit version."""
    value = judgment()
    value["judgments"][index].update(status=status, candidate_quotes=["No."])
    value["conclusion_adequate"] = status != "missing"
    assert (
        core.parse_output("C", json.dumps(value), prompt_version=version, payload=packet()) == value
    )
    assert core.quote_fidelity_diagnostics(json.dumps(value), packet())["ok"]
    with pytest.raises(ValueError):
        parse(value)


@pytest.mark.parametrize(
    ("index", "status"),
    [
        (0, "satisfied"),
        (0, "contradicted"),
        (1, "addressed_without_contradiction"),
        (1, "contradicted"),
    ],
)
def test_v2_still_requires_quotes_for_present_claims(index: int, status: str) -> None:
    """Relaxing omission evidence must not remove positive or contradictory evidence."""
    value = judgment()
    value["judgments"][index].update(status=status, candidate_quotes=[])
    value["conclusion_adequate"] = status != "contradicted"
    with pytest.raises(ValueError, match="require candidate quotes"):
        core.parse_output(
            "C",
            json.dumps(value),
            prompt_version=core.CONCLUSION_STRUCTURED_V2_PROMPT_VERSION,
            payload=packet(),
        )


@pytest.mark.parametrize("defect", ["aggregate", "role", "coverage", "duplicate", "blank_quote"])
def test_v2_keeps_nonquote_contract_checks(defect: str) -> None:
    """The relaxed quote rule does not weaken aggregate, role, inventory or text checks."""
    value = judgment()
    if defect == "aggregate":
        value["conclusion_adequate"] = False
    elif defect == "role":
        value["judgments"][1]["status"] = "missing"
    elif defect == "coverage":
        value["judgments"].pop()
    elif defect == "duplicate":
        value["judgments"].append(copy.deepcopy(value["judgments"][0]))
    else:
        value["judgments"][1]["candidate_quotes"] = [" "]
    with pytest.raises(ValueError):
        core.parse_output(
            "C",
            json.dumps(value),
            prompt_version=core.CONCLUSION_STRUCTURED_V2_PROMPT_VERSION,
            payload=packet(),
        )


@pytest.mark.parametrize(
    "contract_name",
    [
        "task15g_structured_conclusion_judge_v1.json",
        "task15j_structured_conclusion_judge_v2.json",
        "task15k_structured_conclusion_judge_v3.json",
    ],
)
def test_versioned_contract_identities_remain_reproducible(contract_name: str) -> None:
    """A prompt-only revision preserves sealed predecessors and exact schema identities."""
    from er_commons import conclusion_structured
    from er_commons.artifact_io import stable_json_sha256

    contract = json.loads((Path(__file__).parents[1] / "docs/specs" / contract_name).read_text())
    version = contract["prompt_version"]
    assert (
        stable_json_sha256(core.system_prompt("C", prompt_version=version))
        == contract["system_prompt_sha256"]
    )
    assert (
        stable_json_sha256(core.output_json_schema("C", prompt_version=version))
        == contract["output_schema_sha256"]
    )
    assert (
        stable_json_sha256(conclusion_structured.ConclusionInput.model_json_schema())
        == contract["input_schema_sha256"]
    )


def test_v3_prompt_only_change_leaves_v2_validation_and_defaults_intact() -> None:
    """The new instruction cannot silently change schemas or production prompt selection."""
    from er_commons import conclusion_structured

    v2 = core.CONCLUSION_STRUCTURED_V2_PROMPT_VERSION
    v3 = core.CONCLUSION_STRUCTURED_V3_PROMPT_VERSION
    assert core.output_json_schema("C", prompt_version=v3) == core.output_json_schema(
        "C", prompt_version=v2
    )
    assert core.system_prompt("C") == core.CONCLUSION_PROMPT
    assert conclusion_structured.PROMPT_V2 in conclusion_structured.PROMPT_V3.replace(
        "First check whether any candidate claim contradicts each reference point,\n"
        "regardless of whether the candidate supplies numbers or otherwise addresses its\n"
        "details. Only if there is no contradiction, decide whether the point is addressed.\n"
        "The numerical-coverage requirement applies only when choosing between\n"
        "not_addressed and addressed_without_contradiction; it must never prevent\n"
        "contradicted.\n",
        "",
    )


def v4_fixture():
    """Reuse existing fixture with a second exact candidate segment."""
    payload = packet()
    payload["candidate_conclusion"] = "No. Yes."
    payload["candidate_statements"] = [
        {"statement_id": "A1", "text": "No."},
        {"statement_id": "A2", "text": "Yes."},
    ]
    value = judgment()
    value["contradicting_points"] = []
    return payload, value


def test_v4_preserves_model_verdict_and_independent_aggregate():
    """A consistency error is measurable rather than discarded as a parse error."""
    from er_commons import conclusion_structured as structured

    payload, value = v4_fixture()
    value["contradicting_points"] = [["A2", "A1"]]
    result = structured.validate_output(value, payload, version=structured.VERSION_V4)
    assert result["conclusion_adequate"] is True
    assert structured.aggregate_diagnostics(value, payload) == {
        "model_decision": True,
        "aggregate_decision": False,
        "aggregation_consistent": False,
    }
    value["contradicting_points"] = []
    value["conclusion_adequate"] = False
    assert structured.aggregate_diagnostics(value, payload)["aggregate_decision"] is True
    value["judgments"][1].update(status="contradicted", candidate_quotes=["Yes."])
    assert structured.aggregate_diagnostics(value, payload)["aggregate_decision"] is False


@pytest.mark.parametrize(
    "pairs",
    [
        [["A1", "A1"]],
        [["A1", "A3"]],
        [["A1", "R1"]],
        [["A1"]],
        [["A1", "A2", "A3"]],
        [["A1", "A2"], ["A2", "A1"]],
        [["A1", "A2"], ["A1", "A2"]],
    ],
)
def test_v4_rejects_malformed_or_unbound_pairs(pairs):
    """Conflict identities refer to distinct supplied candidates, uniquely per pair."""
    from er_commons import conclusion_structured as structured

    payload, value = v4_fixture()
    value["contradicting_points"] = pairs
    with pytest.raises(ValueError):
        structured.aggregate_diagnostics(value, payload)


@pytest.mark.parametrize("defect", ["text", "ids", "empty", "missing_point", "duplicate_point"])
def test_v4_rejects_incomplete_inventory(defect):
    """Unbound segmentation or incomplete judgments cannot produce an aggregate."""
    from er_commons import conclusion_structured as structured

    payload, value = v4_fixture()
    if defect == "text":
        payload["candidate_statements"][1]["text"] = "YES."
    elif defect == "ids":
        payload["candidate_statements"][1]["statement_id"] = "A1"
    elif defect == "empty":
        payload["candidate_statements"] = []
    elif defect == "missing_point":
        value["judgments"].pop()
    else:
        value["judgments"].append(value["judgments"][0])
    with pytest.raises(ValueError):
        structured.aggregate_diagnostics(value, payload)


def test_v4_quote_diagnostics_remain_independent():
    """Transcription diagnostics do not discard structurally valid verdicts."""
    from er_commons import conclusion_structured as structured

    payload, value = v4_fixture()
    value["judgments"][0]["candidate_quotes"] = ["NO."]
    assert structured.validate_output(value, payload, version=structured.VERSION_V4)
    assert not structured.quote_diagnostics(value, payload)["ok"]
    value["judgments"][0]["candidate_quotes"] = []
    with pytest.raises(ValueError):
        structured.validate_output(value, payload, version=structured.VERSION_V4)


def test_v5_statement_ids_without_pair_output():
    """The ablation keeps lossless input IDs and independent point-only aggregation."""
    from er_commons import conclusion_structured as structured

    payload, value = v4_fixture()
    value.pop("contradicting_points")
    version = structured.VERSION_V5
    assert core.validate_input("C", payload, prompt_version=version) == payload
    value["conclusion_adequate"] = False
    assert structured.aggregate_diagnostics(value, payload, version=version) == {
        "model_decision": False,
        "aggregate_decision": True,
        "aggregation_consistent": False,
    }
    value["conclusion_adequate"] = True
    value["judgments"][1].update(status="contradicted", candidate_quotes=["Yes."])
    assert (
        structured.aggregate_diagnostics(value, payload, version=version)["aggregate_decision"]
        is False
    )
    value["contradicting_points"] = []
    with pytest.raises(ValueError):
        structured.validate_output(value, payload, version=version)
    value.pop("contradicting_points")
    value["judgments"].pop()
    with pytest.raises(ValueError):
        structured.aggregate_diagnostics(value, payload, version=version)


def test_v5_prompt_ablation_preserves_v4_identity():
    """Only the new version loses pair instructions; the sealed v4 stays reproducible."""
    from er_commons import conclusion_structured as structured
    from er_commons.artifact_io import stable_json_sha256

    contract = json.loads(
        (
            Path(__file__).parents[1] / "docs/specs/task15n_structured_conclusion_judge_v4.json"
        ).read_text()
    )
    assert (
        stable_json_sha256(core.system_prompt("C", prompt_version=structured.VERSION_V4))
        == contract["system_prompt_sha256"]
    )
    assert (
        stable_json_sha256(core.output_json_schema("C", prompt_version=structured.VERSION_V4))
        == contract["output_schema_sha256"]
    )
    assert (
        stable_json_sha256(structured.ConclusionInputV4.model_json_schema())
        == contract["input_schema_sha256"]
    )
    prompt = core.system_prompt("C", prompt_version=structured.VERSION_V5)
    assert "candidate_statements" in prompt
    assert "contradicting_points" not in prompt
    assert "contradiction pair" not in prompt
    assert "Scan all statements" in prompt
    assert "Correct claims never cancel conflicting claims" in prompt
    assert "Return every optional judgment" in prompt
    assert "no separate judgment unless it contradicts a reference point" in prompt
    assert set(
        core.output_json_schema("C", prompt_version=structured.VERSION_V5)["properties"]
    ) == {"judgments", "conclusion_adequate", "reason"}


@pytest.mark.parametrize("defect", ["blank", "empty", "extra", "string", "missing"])
def test_v6_reason_list_shape(defect):
    """Reasons must be nonblank objects, but their semantic content is not graded."""
    from er_commons import conclusion_structured as structured

    value = judgment()
    value["internal_contradictions"] = [{"reason": "A working explanation."}]
    if defect == "blank":
        value["internal_contradictions"][0]["reason"] = " "
    elif defect == "empty":
        value["internal_contradictions"][0]["reason"] = ""
    elif defect == "extra":
        value["internal_contradictions"][0]["point_id"] = "A1"
    elif defect == "string":
        value["internal_contradictions"] = ["A working explanation."]
    else:
        value.pop("internal_contradictions")
    with pytest.raises(ValueError):
        structured.validate_output(value, packet(), version=structured.VERSION_V6)


def test_v6_plain_input_and_independent_internal_aggregate():
    """A conflict-list/pass mismatch is diagnostic; empty list cannot cover missing R."""
    from er_commons import conclusion_structured as structured

    payload = packet()
    value = judgment()
    value["internal_contradictions"] = [{"reason": "Unscored working explanation."}]
    version = structured.VERSION_V6
    assert core.validate_input("C", payload, prompt_version=version) == payload
    assert structured.aggregate_diagnostics(value, payload, version=version) == {
        "model_decision": True,
        "aggregate_decision": False,
        "aggregation_consistent": False,
        "internal_contradictions_pass_inconsistent": True,
    }
    value["internal_contradictions"] = []
    assert (
        structured.aggregate_diagnostics(value, payload, version=version)["aggregate_decision"]
        is True
    )
    value["judgments"][0].update(status="missing", candidate_quotes=[])
    diag = structured.aggregate_diagnostics(value, payload, version=version)
    assert diag["aggregate_decision"] is False
    assert diag["internal_contradictions_pass_inconsistent"] is False
    payload["candidate_statements"] = [{"statement_id": "A1", "text": "No."}]
    with pytest.raises(ValueError):
        core.validate_input("C", payload, prompt_version=version)
    payload.pop("candidate_statements")
    value["contradicting_points"] = []
    with pytest.raises(ValueError):
        structured.validate_output(value, payload, version=version)
    value.pop("contradicting_points")
    value["judgments"].pop()
    with pytest.raises(ValueError):
        structured.aggregate_diagnostics(value, payload, version=version)


def test_v6_paragraph_prompt_preserves_v5_identity():
    """V6 removes candidate identities while preserving the sealed v5 contract."""
    from er_commons import conclusion_structured as structured
    from er_commons.artifact_io import stable_json_sha256

    contract = json.loads(
        (
            Path(__file__).parents[1] / "docs/specs/task15o_structured_conclusion_judge_v5.json"
        ).read_text()
    )
    assert (
        stable_json_sha256(core.system_prompt("C", prompt_version=structured.VERSION_V5))
        == contract["system_prompt_sha256"]
    )
    assert (
        stable_json_sha256(core.output_json_schema("C", prompt_version=structured.VERSION_V5))
        == contract["output_schema_sha256"]
    )
    prompt = core.system_prompt("C", prompt_version=structured.VERSION_V6)
    assert "candidate_statements" not in prompt
    assert "statement_id" not in prompt
    assert "contradicting_points" not in prompt
    assert "internal_contradictions" in prompt
    assert "No exhaustive inventory of claim pairs is required" in prompt
    assert "An empty list alone does not imply a pass" in prompt
    assert "Only reference points have IDs" in prompt
    assert "may overlap" in prompt
    assert "not separately matched or scored" not in prompt
    assert "identifies the incompatible claims" in prompt
    assert "they cannot both hold" in prompt
    assert set(
        core.output_json_schema("C", prompt_version=structured.VERSION_V6)["properties"]
    ) == {"judgments", "internal_contradictions", "conclusion_adequate", "reason"}
