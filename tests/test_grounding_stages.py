"""Invented stage fixtures test isolation, strict diagnostics and disagreement aggregation."""

import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError
from test_judge_packet_requests import built

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_stages import (
    CONCLUSION_PROMPT,
    POINT_PROMPT,
    aggregate,
    conclusion_input,
    conclusion_schema,
    point_inputs,
    point_schema,
    validate_conclusion,
    validate_point,
)


def point_result(point_id: str = "P2", supported: bool = True) -> dict:
    """Use the existing invented 09C qualification point and its literal source text."""
    return {
        "point_id": point_id,
        "supported": supported,
        "unsupported_assertions": []
        if supported
        else [{"assertion": "Exact caveat.", "explanation": "This assertion lacks support."}],
        "locators": [{"citation_id": "S1", "excerpt": "Exact source."}],
        "explanation": "Actual evidence evaluated.",
    }


def conclusion_result(
    supported: bool | None = True,
    *,
    point_supported: bool = True,
    clean: bool = False,
) -> dict:
    """Retain an independent point review that can explicitly disagree with the first stage."""
    return {
        "conclusion_supported": supported,
        "clean_abstention": clean,
        "point_reviews": [
            {
                "point_id": "P2",
                "supported": point_supported,
                "explanation": "Independently checked actual evidence.",
            }
        ],
        "locators": [{"citation_id": "S1", "excerpt": "Exact source."}],
        "explanation": "Conclusion checked against evidence.",
    }


def reseal(packet: dict) -> dict:
    """Update only invented packet integrity after an explicit fixture edit."""
    packet["diagnostics"]["payload_sha256"] = stable_json_sha256(packet["payload"])
    return packet


def test_point_projection_has_only_target_evidence_and_explicit_linked_context() -> None:
    """Original IDs and linked text survive; references, labels and unrelated sources do not."""
    packet = built()
    packet["restricted"] = {"reference_answer": "SECRET_REFERENCE", "expected_score": 0}
    packet["payload"]["answer"]["supporting_points"] = [
        {"point_id": "P3", "text": "Another assertion.", "citation_ids": ["S2"]}
    ]
    packet["payload"]["answer"]["qualifications"][0]["applies_to"] = ["P1", "P3"]
    packet["payload"]["evidence"].append({"citation_id": "S2", "resolution": "unresolved"})
    inputs = point_inputs(reseal(packet))
    assert [v["point"]["point_id"] for v in inputs] == ["P3", "P2"]
    first, second = inputs
    assert first["evidence"] == [{"citation_id": "S2", "resolution": "unresolved"}]
    assert first["context_points"][0] == packet["payload"]["answer"]["qualifications"][0]
    assert [p["point_id"] for p in second["context_points"]] == ["P1", "P3"]
    assert second["point"]["applies_to"] == ["P1", "P3"]
    assert [e["citation_id"] for e in second["evidence"]] == ["S1"]
    assert "SECRET" not in json.dumps(inputs)
    assert "context_points only clarifies" in POINT_PROMPT


def test_blank_nonconclusion_points_are_skipped_without_conclusion_shortcut() -> None:
    """A conclusion-only answer still reaches independent conclusion assessment."""
    packet = built()
    packet["payload"]["answer"]["qualifications"][0]["text"] = " "
    assert point_inputs(reseal(packet)) == []
    value = conclusion_input(packet, [])
    result = conclusion_result()
    result["point_reviews"] = []
    parsed = validate_conclusion(json.dumps(result), value)
    assert aggregate([], parsed) == {"status": "scored", "score": 2, "disagreement_point_ids": []}


def test_supported_and_compound_unsupported_point_results() -> None:
    """Each unsupported subclaim is a literal candidate substring, separate from source quotes."""
    value = point_inputs(built())[0]
    schema = point_schema(value)
    Draft202012Validator.check_schema(schema)
    for supported in (True, False):
        result = point_result(supported=supported)
        Draft202012Validator(schema).validate(result)
        assert validate_point(json.dumps(result), value)["supported"] is supported
    compound = copy.deepcopy(value)
    compound["point"]["text"] = "Exact caveat. Added invented assertion."
    result = point_result(supported=False)
    result["unsupported_assertions"].append(
        {"assertion": "Added invented assertion.", "explanation": "Also unsupported."}
    )
    assert len(validate_point(json.dumps(result), compound)["unsupported_assertions"]) == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_id",
        "true_with_issues",
        "false_without_issues",
        "no_source",
        "wrong_source",
        "invented_quote",
        "invented_assertion",
        "whitespace_assertion",
        "bool_coercion",
        "extra",
    ],
)
def test_point_result_failure_modes(mutation: str) -> None:
    """Bad IDs, source links, subclaim spans and coercions remain stage failures."""
    value = point_inputs(built())[0]
    result = point_result()
    if mutation == "wrong_id":
        result["point_id"] = "P1"
    elif mutation == "true_with_issues":
        result["unsupported_assertions"] = point_result(supported=False)["unsupported_assertions"]
    elif mutation == "false_without_issues":
        result["supported"] = False
    elif mutation == "no_source":
        result["locators"] = []
    elif mutation == "wrong_source":
        result["locators"][0]["citation_id"] = "S99"
    elif mutation == "invented_quote":
        result["locators"][0]["excerpt"] = "Exact caveat."
    elif mutation == "invented_assertion":
        result = point_result(supported=False)
        result["unsupported_assertions"][0]["assertion"] = "Not in the candidate point."
    elif mutation == "whitespace_assertion":
        result = point_result(supported=False)
        result["unsupported_assertions"][0]["assertion"] = " "
    elif mutation == "bool_coercion":
        result["supported"] = 1
    else:
        result["expected_score"] = 2
    with pytest.raises(ValueError):
        validate_point(json.dumps(result), value)


def test_multi_source_repeated_locators_and_table_quotes_are_allowed() -> None:
    """Joint support and excerpt reuse are not rejected by artificial uniqueness rules."""
    value = point_inputs(built())[0]
    value["point"]["citation_ids"].append("S2")
    other = copy.deepcopy(value["evidence"][0])
    other.update(citation_id="S2", full_source_text="Other actual source.")
    value["evidence"].append(other)
    result = point_result()
    result["locators"].extend(
        [
            copy.deepcopy(result["locators"][0]),
            {"citation_id": "S2", "excerpt": "Other actual source."},
            {"citation_id": "S1", "excerpt": "5"},
        ]
    )
    assert len(validate_point(json.dumps(result), value)["locators"]) == 4


def test_point_projection_rejects_unowned_evidence_and_hidden_fields() -> None:
    """A forged projection cannot append unrestricted metadata or uncited source units."""
    value = point_inputs(built())[0]
    value["evidence"].append({"citation_id": "S99", "resolution": "unresolved"})
    with pytest.raises(ValueError, match="match exactly"):
        point_schema(value)
    value = point_inputs(built())[0]
    value["reference_answer"] = "SECRET"
    with pytest.raises(ValueError):
        point_schema(value)


def test_conclusion_projection_preserves_original_payload_and_only_valid_predictions() -> None:
    """Prediction text is explicitly separated from unchanged source evidence."""
    packet = built()
    result = point_result()
    projected = conclusion_input(packet, [result])
    for key in ("question", "answer", "evidence"):
        assert projected[key] == packet["payload"][key]
    assert projected["point_assessments"] == [result]
    assert "SECRET" not in json.dumps(projected)
    assert "predictions, never evidence" in CONCLUSION_PROMPT
    result["expected_score"] = 2
    with pytest.raises(ValueError):
        conclusion_input(packet, [result])
    with pytest.raises(ValueError, match="all point assessments"):
        conclusion_input(packet, [])


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "wrong_id", "foreign_quote", "extra", "null", "clean"]
)
def test_conclusion_rejects_invalid_reviews_and_abstention(mutation: str) -> None:
    """Stage two cannot drop reviews, invent evidence or hide assertions under N/A."""
    value = conclusion_input(built(), [point_result()])
    result = conclusion_result()
    if mutation == "missing":
        result["point_reviews"] = []
    elif mutation == "duplicate":
        result["point_reviews"].append(copy.deepcopy(result["point_reviews"][0]))
    elif mutation == "wrong_id":
        result["point_reviews"][0]["point_id"] = "P99"
    elif mutation == "foreign_quote":
        result["locators"][0]["excerpt"] = "Actual evidence evaluated."
    elif mutation == "extra":
        result["score"] = 2
    elif mutation == "null":
        result["conclusion_supported"] = None
    else:
        result.update(clean_abstention=True, conclusion_supported=None)
    with pytest.raises(ValueError):
        validate_conclusion(json.dumps(result), value)


def test_conclusion_schema_covers_reviews_and_clean_abstention_branches() -> None:
    """JSON Schema encodes review identity, evidence presence and clean-abstention eligibility."""
    value = conclusion_input(built(), [point_result()])
    schema = conclusion_schema(value)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(conclusion_result())
    invalid = conclusion_result()
    invalid["locators"] = []
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(invalid)
    packet = built()
    packet["payload"]["answer"].update(status="abstained", qualifications=[])
    value = conclusion_input(reseal(packet), [])
    clean = conclusion_result(None, clean=True)
    clean["point_reviews"] = []
    clean["locators"] = []
    Draft202012Validator(conclusion_schema(value)).validate(clean)
    parsed = validate_conclusion(json.dumps(clean), value)
    assert aggregate([], parsed)["status"] == "not_applicable"
    # The same abstained status also permits a substantive unsupported conclusion.
    substantive = conclusion_result(False)
    substantive["point_reviews"] = []
    Draft202012Validator(conclusion_schema(value)).validate(substantive)
    assert aggregate([], validate_conclusion(json.dumps(substantive), value))["score"] == 0


@pytest.mark.parametrize(
    "conclusion_supported,point_supported,expected",
    [(False, True, 0), (False, False, 0), (True, False, 1), (True, True, 2)],
)
def test_aggregation_is_deterministic_only_when_stages_agree(
    conclusion_supported: bool,
    point_supported: bool,
    expected: int,
) -> None:
    """Conclusion support determines zero; supported conclusions distinguish one from two."""
    result = aggregate(
        [point_result(supported=point_supported)],
        conclusion_result(conclusion_supported, point_supported=point_supported),
    )
    assert result == {"status": "scored", "score": expected, "disagreement_point_ids": []}


@pytest.mark.parametrize("conclusion_supported", [False, True])
def test_review_disagreement_always_blocks_numeric_score(conclusion_supported: bool) -> None:
    """Even an unsupported conclusion cannot conceal disagreement behind a zero score."""
    value = conclusion_input(built(), [point_result(supported=False)])
    reviewed = validate_conclusion(json.dumps(conclusion_result(conclusion_supported)), value)
    assert aggregate([point_result(supported=False)], reviewed) == {
        "status": "unresolved_disagreement",
        "score": None,
        "disagreement_point_ids": ["P2"],
    }


def test_conclusion_input_rejects_extra_metadata_and_inconsistent_prediction_order() -> None:
    """Only sanitized predictions in original point order can enter the independent reviewer."""
    value = conclusion_input(built(), [point_result()])
    value["reference_answer"] = "SECRET"
    with pytest.raises(ValueError, match="only original"):
        conclusion_schema(value)
    packet = built()
    packet["payload"]["answer"]["optional_context"] = [
        {"point_id": "P3", "text": "Exact caveat.", "citation_ids": ["S1"]}
    ]
    reseal(packet)
    with pytest.raises(ValueError, match="exact target point ID"):
        conclusion_input(packet, [point_result("P3"), point_result("P2")])
    projected = conclusion_input(packet, [point_result("P2"), point_result("P3")])
    reviewed = conclusion_result()
    reviewed["point_reviews"].append(
        {"point_id": "P3", "supported": True, "explanation": "Checked."}
    )
    reviewed["point_reviews"].reverse()
    with pytest.raises(ValueError, match="packet order"):
        validate_conclusion(json.dumps(reviewed), projected)
