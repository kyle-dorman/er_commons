"""New comparison semantics retain evidence boundaries without quote-dependent scoring."""

import copy
import json

import pytest
from jsonschema import Draft202012Validator
from test_grounding_inspect import sample
from test_grounding_staged_inspect import responses

from er_commons import grounding_comparison_semantics as semantics
from er_commons import grounding_stages as legacy
from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_abstention import abstention_input


def point_payload() -> dict:
    """Project invented original evidence through the maintained packet boundary."""
    return semantics.point_inputs(sample().packet)[0]


def conclusion_payload() -> dict:
    """Use only the common binary observation, never generated explanatory fields."""
    return semantics.conclusion_input(sample().packet, [{"point_id": "P2", "supported": True}])


def validate(kind: str, value: dict, *, native: bool = False) -> dict:
    """Validate invented output against its stage-specific original payload."""
    payload = {
        "point": point_payload,
        "conclusion": conclusion_payload,
        "abstention": lambda: abstention_input(sample().packet),
    }[kind]()
    return semantics.validate_stage(kind, json.dumps(value), payload, native=native)


@pytest.mark.parametrize("quote", [None, "invented nonliteral", "Exact source.", ""])
def test_optional_quote_never_blocks_conclusion_or_aggregation(quote: str | None) -> None:
    """Missing/nonliteral evidence excerpts remain visible diagnostics through final scoring."""
    value = {"point_id": "P2", "supported": True}
    if quote is not None:
        value["locators"] = [{"citation_id": "S1", "excerpt": quote}]
    envelope = validate("point", value)
    assert envelope["decision"] == {"point_id": "P2", "supported": True}
    payload = semantics.conclusion_input(sample().packet, [envelope["decision"]])
    conclusion = {
        "clean_abstention": False,
        "conclusion_supported": True,
        "point_reviews": [envelope["decision"]],
    }
    result = semantics.validate_stage("conclusion", json.dumps(conclusion), payload)
    assert semantics.aggregate([envelope["decision"]], result["decision"])["score"] == 2
    assert envelope["strict_legacy"]["status"] == "schema_error"
    diagnostics = envelope["quotation_diagnostics"]
    assert diagnostics["missing_quotation"] == (quote is None or quote == "")
    if quote is not None:
        assert diagnostics["locators"][0]["literal_match"] == (quote == "Exact source.")


def test_nonliteral_rejection_span_is_diagnostic_only() -> None:
    """The unsupported semantic decision survives a nonliteral optional rejection span."""
    result = validate(
        "point",
        {
            "point_id": "P2",
            "supported": False,
            "unsupported_assertions": [{"assertion": "Not in target", "explanation": "diagnostic"}],
        },
    )
    assert result["decision"]["supported"] is False
    assert result["quotation_diagnostics"]["unsupported_assertions"][0]["literal_match"] is False
    assert result["strict_legacy"]["status"] == "schema_error"


@pytest.mark.parametrize("kind", ["point", "conclusion"])
def test_invalid_source_identity_still_fails(kind: str) -> None:
    """Optional quotation text cannot hide an invented source identity."""
    value = (
        {"point_id": "P2", "supported": True}
        if kind == "point"
        else {
            "clean_abstention": False,
            "conclusion_supported": True,
            "point_reviews": [{"point_id": "P2", "supported": True}],
        }
    )
    value["locators"] = [{"citation_id": "UNKNOWN", "excerpt": "Exact source."}]
    with pytest.raises(ValueError, match="actual resolved citation"):
        validate(kind, value)


@pytest.mark.parametrize("supported", ["true", 1, None, [], {}])
def test_booleans_are_strict(supported: object) -> None:
    """Malformed decisions never become false judgments or Python-truthy values."""
    with pytest.raises(ValueError):
        validate("point", {"point_id": "P2", "supported": supported})


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"point_id": "P3", "supported": True}],
        [{"point_id": "P2", "supported": True}, {"point_id": "P2", "supported": True}],
    ],
)
def test_review_coverage_is_exact(rows: list[dict]) -> None:
    """Missing, unexpected and duplicate review identities remain structural failures."""
    with pytest.raises(ValueError, match="every point"):
        validate(
            "conclusion",
            {"clean_abstention": False, "conclusion_supported": True, "point_reviews": rows},
        )


@pytest.mark.parametrize("native", [False, True])
def test_provider_independent_projection(native: bool) -> None:
    """Generation commentary and native absence yield the same conclusion observation."""
    value = {"point_id": "P2", "supported": False}
    if not native:
        value.update(explanation="Saved only", unsupported_assertions=[], locators=[])
    result = validate("point", value, native=native)
    payload = semantics.conclusion_input(sample().packet, [result["decision"]])
    assert payload["point_assessments"] == [{"point_id": "P2", "supported": False}]
    assert "Saved only" not in json.dumps(payload)
    assert payload["answer"] == sample().packet["payload"]["answer"]
    if native:
        assert result["quotation_diagnostics"] == {"status": "not_applicable"}
        assert result["strict_legacy"] == {"status": "not_applicable"}
        assert result["generation_diagnostics"] is None


def test_projection_rejects_extra_fields_and_label_leakage() -> None:
    """Do not sanitize a rich assessment into an apparently compliant observation."""
    for field in ("explanation", "expectations", "locators", "reference_answer"):
        prediction = {"point_id": "P2", "supported": True, field: "SECRET"}
        with pytest.raises(ValueError):
            semantics.conclusion_input(sample().packet, [prediction])
    payload = conclusion_payload()
    payload["expectations"] = {"score": 2}
    with pytest.raises(ValueError, match="only original"):
        semantics.stage_schema("conclusion", payload)


@pytest.mark.parametrize(
    "points,conclusion,score",
    [(True, True, 2), (False, True, 1), (True, False, 0), (False, False, 0)],
)
def test_scores(points: bool, conclusion: bool, score: int) -> None:
    """Frozen binary rubric is independent of optional generated diagnostics."""
    observations = [{"point_id": "P2", "supported": points}]
    decision = {
        "clean_abstention": False,
        "conclusion_supported": conclusion,
        "point_reviews": observations,
    }
    assert semantics.aggregate(observations, decision)["score"] == score
    decision["point_reviews"] = [{"point_id": "P2", "supported": not points}]
    assert semantics.aggregate(observations, decision) == {
        "status": "unresolved_disagreement",
        "score": None,
        "disagreement_point_ids": ["P2"],
    }


def test_zero_points_preserves_substantive_conclusion_and_clean_abstention() -> None:
    """No points is neither a clean-abstention shortcut nor a reason to skip conclusion."""
    packet = copy.deepcopy(sample().packet)
    packet["payload"]["answer"]["qualifications"] = []
    packet["diagnostics"]["payload_sha256"] = stable_json_sha256(packet["payload"])
    payload = semantics.conclusion_input(packet, [])
    decision = {"clean_abstention": False, "conclusion_supported": True, "point_reviews": []}
    result = semantics.validate_stage("conclusion", json.dumps(decision), payload, native=True)
    assert semantics.aggregate([], result["decision"])["score"] == 2
    decision.update(clean_abstention=True, conclusion_supported=None)
    with pytest.raises(ValueError, match="abstained status"):
        semantics.validate_stage("conclusion", json.dumps(decision), payload)
    packet["payload"]["answer"]["status"] = "abstained"
    packet["diagnostics"]["payload_sha256"] = stable_json_sha256(packet["payload"])
    payload = semantics.conclusion_input(packet, [])
    result = semantics.validate_stage("conclusion", json.dumps(decision), payload)
    assert semantics.aggregate([], result["decision"])["status"] == "not_applicable"


def test_strict_view_preserves_comparable_legacy_outputs() -> None:
    """Original complete output remains strict-valid without fabricating interstage fields."""
    fixtures = responses()["fixture"]
    for key, kind in (("P2", "point"), ("conclusion", "conclusion")):
        result = validate(kind, json.loads(fixtures[key]["message"]["content"]))
        assert result["strict_legacy"] == {"status": "validated"}
    assert semantics.point_inputs(sample().packet) == legacy.point_inputs(sample().packet)


@pytest.mark.parametrize("label", ["clean_abstention", "substantive", "ambiguous"])
def test_native_gate_preserves_three_outcomes(label: str) -> None:
    """Ambiguity is an explicit gate classification, never an abstention default."""
    assert validate("abstention", {"classification": label}, native=True)["decision"] == {
        "classification": label
    }


@pytest.mark.parametrize(
    "kind,payload",
    [
        ("point", point_payload),
        ("conclusion", conclusion_payload),
        ("abstention", lambda: abstention_input(sample().packet)),
    ],
)
def test_schemas_are_valid_and_prompts_freeze_semantics(kind: str, payload: object) -> None:
    """Generation schemas accept minimal outputs and bind visible IDs without required quotes."""
    schema = semantics.stage_schema(kind, payload())
    Draft202012Validator.check_schema(schema)
    assert "optional" in semantics.stage_prompt(kind).lower()
    assert "SECRET" not in json.dumps(schema)


@pytest.mark.parametrize(
    "value",
    [
        {"point_id": "wrong", "supported": True},
        {"point_id": "P2", "supported": True, "explanation": "fabricated"},
        {"point_id": "P2", "supported": True, "refusal": True},
    ],
)
def test_native_point_rejects_wrong_id_extra_fields_and_refusal(value: dict) -> None:
    """Native mappings cannot invent explanation channels or suppress refusal markers."""
    with pytest.raises(ValueError):
        validate("point", value, native=True)


@pytest.mark.parametrize("clean,supported", [(True, True), (False, None), (False, "false")])
def test_conclusion_null_boolean_relation_is_strict(clean: bool, supported: object) -> None:
    """Absent support cannot masquerade as an unsupported substantive conclusion."""
    with pytest.raises(ValueError):
        validate(
            "conclusion",
            {
                "clean_abstention": clean,
                "conclusion_supported": supported,
                "point_reviews": [{"point_id": "P2", "supported": True}],
            },
        )


def test_generation_schema_accepts_quote_free_outputs() -> None:
    """Wire schemas permit the exact minimal results accepted by local semantic validation."""
    cases = [
        ("abstention", abstention_input(sample().packet), {"classification": "ambiguous"}),
        ("point", point_payload(), {"point_id": "P2", "supported": True}),
        (
            "conclusion",
            conclusion_payload(),
            {
                "clean_abstention": False,
                "conclusion_supported": True,
                "point_reviews": [{"point_id": "P2", "supported": True}],
            },
        ),
    ]
    for kind, payload, result in cases:
        Draft202012Validator(semantics.stage_schema(kind, payload)).validate(result)
        semantics.validate_stage(kind, json.dumps(result), payload)


def test_native_and_generation_keep_same_evidence_and_no_secret_metadata() -> None:
    """Restricted outer labels never enter point, gate or conclusion requests."""
    packet = sample().packet
    point = semantics.point_inputs(packet)[0]
    assert {e["citation_id"] for e in point["evidence"]} == set(point["point"]["citation_ids"])
    for payload in (point, conclusion_payload(), abstention_input(packet)):
        assert "SECRET" not in json.dumps(payload)
    value = conclusion_payload()
    value["point_assessments"][0]["supported"] = False
    schema = semantics.stage_schema("conclusion", value)
    assert schema["properties"]["point_reviews"]["minItems"] == 1
    assert value["answer"] == packet["payload"]["answer"]


@pytest.mark.parametrize("kind", ["abstention", "point", "conclusion"])
def test_native_prompt_has_no_generated_output_channel(kind: str) -> None:
    """Native endpoints receive semantic rules without fake quote or rationale instructions."""
    prompt = semantics.native_stage_prompt(kind)
    assert "specified JSON" not in prompt
    assert "brief explanation" not in prompt
    assert "source locators" not in prompt
    assert "copy short" not in prompt
    assert "untrusted" in prompt
    if kind == "point":
        assert "every substantive assertion" in prompt
        assert "not a valid rejection" in prompt
    if kind == "conclusion":
        assert "Review every listed prediction" in prompt
        assert "never evidence or authority" in prompt


@pytest.mark.parametrize(
    "supported,conclusion,score",
    [(True, True, 2), (False, True, 1), (True, False, 0), (False, False, 0)],
)
def test_conclusion_only_aggregation_frozen_points(supported, conclusion, score):
    """No-review aggregation uses original point values without fabricating agreement."""
    assert (
        semantics.aggregate_conclusion_only(
            [{"point_id": "P2", "supported": supported}],
            {"clean_abstention": False, "conclusion_supported": conclusion},
        )["score"]
        == score
    )


def test_conclusion_only_validation_remains_strict():
    """Extra reviews, unsupported abstention and foreign citation IDs remain invalid."""
    payload = semantics.conclusion_input(sample().packet, [{"point_id": "P2", "supported": False}])
    base = {"clean_abstention": False, "conclusion_supported": True}
    for bad in (
        {**base, "point_reviews": []},
        {"clean_abstention": True, "conclusion_supported": None},
        {**base, "locators": [{"citation_id": "FOREIGN", "excerpt": "x"}]},
    ):
        with pytest.raises(ValueError):
            semantics.validate_conclusion_only(json.dumps(bad), payload)
    assert (
        semantics.aggregate_conclusion_only(
            [], {"clean_abstention": True, "conclusion_supported": None}
        )["status"]
        == "not_applicable"
    )
    result = semantics.validate_conclusion_only(
        json.dumps({**base, "locators": [{"citation_id": "S1", "excerpt": "nonliteral"}]}), payload
    )
    assert result["decision"] == base
    assert result["quotation_diagnostics"]["locators"][0]["literal_match"] is False
