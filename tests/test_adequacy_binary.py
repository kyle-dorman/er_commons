"""Selected adequacy contracts preserve strict boundaries and diagnostic semantics."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.adequacy_binary import (
    CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION,
    output_json_schema,
    parse_output,
    quotation_fidelity,
    quote_fidelity_diagnostics,
    system_prompt,
    validate_input,
)


def c_input() -> dict[str, Any]:
    """Return an invented conclusion-only example."""
    return {
        "question": "Can it restore?",
        "candidate_conclusion": "No.",
        "reference_conclusion": "No.",
    }


def s_input() -> dict[str, Any]:
    """Return an invented argument with plain-text qualification scope."""
    return {
        "question": "Can it restore?",
        "candidate_conclusion": "No.",
        "candidate_supporting_points": [{"point_id": "P1", "text": "File postdates snapshot."}],
        "candidate_qualifications": ["For this snapshot."],
    }


@pytest.mark.parametrize("field", ["support", "case_id", "expected_label", "citations"])
def test_conclusion_rejects_leakage(field: str) -> None:
    """Metadata and source content cannot sneak into a conclusion call."""
    with pytest.raises(ValueError):
        validate_input("C", c_input() | {field: "leaked"})


@pytest.mark.parametrize("bad", ["  ", 1, False, None])
def test_required_text_is_strict(bad: object) -> None:
    """Blank strings and coercible values remain invalid inputs."""
    with pytest.raises(ValueError):
        validate_input("C", c_input() | {"question": bad})


def test_payload_preservation_and_reference_isolation() -> None:
    """Validation preserves text, permits absent basis, and separates reference arms."""
    c = c_input() | {"candidate_conclusion": " No. \n"}
    assert validate_input("C", c) == c
    s = s_input()
    assert validate_input("S", s) == s
    assert (
        validate_input("S", s | {"candidate_supporting_points": []})["candidate_supporting_points"]
        == []
    )
    reference = {
        "reference_conclusion": "No.",
        "reference_supporting_points": [{"point_id": "P1", "text": "The file is newer."}],
        "reference_qualifications": [],
    }
    paired = s | {"reference_example": reference}
    assert validate_input("S", paired, with_reference=True) == paired
    with pytest.raises(ValueError):
        validate_input("S", paired)
    with pytest.raises(ValueError):
        validate_input("S", s, with_reference=True)
    with pytest.raises(ValueError):
        validate_input(
            "S",
            paired | {"reference_example": {"reference_conclusion": "No."}},
            with_reference=True,
        )


def test_support_ids_and_qualifications() -> None:
    """Disallow duplicate point IDs and the retired structured qualifications."""
    s = s_input()
    with pytest.raises(ValueError):
        validate_input(
            "S", s | {"candidate_supporting_points": s["candidate_supporting_points"] * 2}
        )
    with pytest.raises(ValueError):
        validate_input(
            "S", s | {"candidate_qualifications": [{"text": "Condition", "applies_to": "P1"}]}
        )
    with pytest.raises(ValueError):
        validate_input(
            "S",
            s
            | {
                "candidate_supporting_points": [
                    {"point_id": "P1", "text": "x", "citation_id": "S1"}
                ]
            },
        )


def c_wire() -> dict[str, Any]:
    """Return a valid selected conclusion judgment."""
    return {
        "comparison": [
            {
                "reference_quotes": ["No."],
                "candidate_quotes": ["No."],
                "status": "matched",
                "reason": "Same position.",
            }
        ],
        "conclusion_adequate": True,
        "reason_codes": [],
        "reason": "Equivalent.",
    }


@pytest.mark.parametrize("component", ["C", "S"])
def test_selected_identities(component: Any) -> None:
    """Selected prompt and wire schema identities survive implementation cleanup."""
    selected = json.loads(
        (Path(__file__).resolve().parents[1] / "configs/adequacy_selected_v1.json").read_text()
    )["components"][component]
    assert (
        hashlib.sha256(system_prompt(component).encode()).hexdigest() == selected["prompt_sha256"]
    )
    assert (
        hashlib.sha256(
            json.dumps(output_json_schema(component), sort_keys=True).encode()
        ).hexdigest()
        == selected["schema_sha256"]
    )
    assert system_prompt(component, prompt_version=selected["prompt_version"]) == system_prompt(
        component
    )
    with pytest.raises(ValueError):
        system_prompt(component, prompt_version="task09f.binary_adequacy.v1")
    with pytest.raises(ValueError):
        system_prompt(component, with_reference=True)


def test_candidate_selection_preserves_frozen_default() -> None:
    """The new rubric is explicit and cannot impersonate the frozen native selection."""
    from er_commons import adequacy_inspect, judge_inspect

    version = CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION
    candidate = system_prompt("C", prompt_version=version)
    assert candidate != system_prompt("C")
    assert output_json_schema("C", prompt_version=version) == output_json_schema("C")
    assert adequacy_inspect.selected_condition("C") == "openai_generation"
    with pytest.raises(ValueError, match="version the selection"):
        judge_inspect.selected_condition(
            "C", version, candidate, output_json_schema("C", prompt_version=version)
        )
    with pytest.raises(ValueError):
        system_prompt("C", prompt_version=version, with_reference=True)


@pytest.mark.parametrize(
    "component,prompt_version",
    [("C", "unknown"), ("S", CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION)],
)
def test_version_rejected_across_core_entrypoints(component: Any, prompt_version: str) -> None:
    """Unknown and cross-component versions fail even when the wire schema matches."""
    with pytest.raises(ValueError):
        system_prompt(component, prompt_version=prompt_version)
    with pytest.raises(ValueError):
        output_json_schema(component, prompt_version=prompt_version)
    with pytest.raises(ValueError):
        parse_output(component, json.dumps(c_wire()), prompt_version=prompt_version)


@pytest.mark.parametrize(
    "component,prompt_version",
    [("C", None), ("C", CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION), ("S", None)],
)
@pytest.mark.parametrize("passed", [True, False])
def test_selected_wire_and_canonical_diagnostics(
    component: Any, prompt_version: str | None, passed: bool
) -> None:
    """Preserve strict decisions and canonical explanation fields without repair."""
    wire = (
        c_wire()
        if component == "C"
        else {"support_sufficient": True, "reason_codes": [], "reason": "Basis."}
    )
    field = "conclusion_adequate" if component == "C" else "support_sufficient"
    wire[field] = passed
    wire["reason_codes"] = (
        [] if passed else ["incorrect_answer" if component == "C" else "missing_basis"]
    )
    result = parse_output(component, json.dumps(wire), prompt_version=prompt_version)
    assert result[field] is passed
    assert result["explanation"] == wire["reason"]
    assert "reason" not in result
    if component == "C":
        assert result["comparison"][0]["explanation"] == "Same position."


@pytest.mark.parametrize(
    "component,prompt_version",
    [("C", None), ("C", CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION), ("S", None)],
)
@pytest.mark.parametrize(
    "defect",
    [
        "boolean",
        "blank",
        "alias",
        "extra",
        "codes",
        "duplicate_codes",
        "duplicate_key",
        "wrapper",
        "nan",
    ],
)
def test_invalid_output(component: Any, prompt_version: str | None, defect: str) -> None:
    """Invalid output cannot acquire a semantic decision or an automatic repair."""
    wire = (
        c_wire()
        if component == "C"
        else {"support_sufficient": True, "reason_codes": [], "reason": "Basis."}
    )
    field = "conclusion_adequate" if component == "C" else "support_sufficient"
    if defect == "boolean":
        wire[field] = 1
    if defect == "blank":
        wire["reason"] = "  "
    if defect == "alias":
        wire["explanation"] = wire.pop("reason")
    if defect == "extra":
        wire["score"] = 1
    if defect == "codes":
        wire["reason_codes"] = ["incorrect_answer" if component == "C" else "missing_basis"]
    if defect == "duplicate_codes":
        wire[field] = False
        wire["reason_codes"] = ["incorrect_answer" if component == "C" else "missing_basis"] * 2
    if defect == "nan":
        wire["reason"] = float("nan")
    raw = json.dumps(wire)
    if defect == "wrapper":
        raw = "```json\n" + raw + "\n```"
    if defect == "duplicate_key":
        raw = raw[:-1] + ', "reason": "Repeated"}'
    with pytest.raises(ValueError):
        parse_output(component, raw, prompt_version=prompt_version)


@pytest.mark.parametrize("defect", ["alias", "missing", "type", "blank", "status", "extra"])
@pytest.mark.parametrize("prompt_version", [None, CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION])
def test_nested_comparison_contract(defect: str, prompt_version: str | None) -> None:
    """Selected nested reason fields are mandatory and strictly typed."""
    wire = c_wire()
    entry = wire["comparison"][0]
    if defect == "alias":
        entry["explanation"] = entry.pop("reason")
    if defect == "missing":
        del entry["reason"]
    if defect == "type":
        entry["reason"] = 1
    if defect == "blank":
        entry["reason"] = " "
    if defect == "status":
        entry["status"] = "unknown"
    if defect == "extra":
        entry["score"] = 1
    with pytest.raises(ValueError):
        parse_output("C", json.dumps(wire), prompt_version=prompt_version)


def test_quote_diagnostics_do_not_change_decision() -> None:
    """Invented quotations remain separately visible rather than rewriting the verdict."""
    wire = c_wire()
    wire["comparison"][0]["candidate_quotes"] = ["Invented quote."]
    parsed = parse_output("C", json.dumps(wire))
    assert parsed["conclusion_adequate"] is True
    audit = quotation_fidelity(parsed, c_input())
    assert audit["ok"] is False
    assert audit["issues"][0]["code"] == "invented_excerpt"
    assert quote_fidelity_diagnostics("not JSON", c_input())["ok"] is False


@pytest.mark.parametrize("status", ["missing", "internal_contradiction"])
def test_quote_conventions_are_diagnostic(status: str) -> None:
    """Questionable quote conventions never silently become Boolean failures."""
    wire = c_wire()
    wire["comparison"][0]["status"] = status
    parsed = parse_output("C", json.dumps(wire))
    assert parsed["conclusion_adequate"] is True
    assert quotation_fidelity(parsed, c_input())["ok"] is False
