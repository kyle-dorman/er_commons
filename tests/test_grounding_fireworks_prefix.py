"""Exact semantic text preservation and stable Fireworks cache routing boundaries."""

import asyncio
import copy

import pytest
from test_grounding_comparison_inspect import envelopes
from test_grounding_comparison_providers import CONCLUSION, CONDITIONS, POINT, SCHEMA
from test_grounding_inspect import sample

from er_commons.grounding_comparison_inspect import run_comparison_stage
from er_commons.grounding_comparison_providers import render_request
from er_commons.grounding_comparison_safety import RunBudget
from er_commons.grounding_comparison_semantics import point_inputs


def configured(name="fireworks_glm", **settings):
    """Build an explicit opt-in without changing historical checked-in conditions."""
    base = CONDITIONS[name]
    data = base.model_dump()
    data["settings"].update(
        fireworks_reasoning_mode="prompt_schema",
        reasoning_effort="medium",
        fireworks_evidence_cache_prefix=True,
    )
    data["settings"].update(settings)
    return type(base).model_validate(data)


@pytest.mark.parametrize("name", ["fireworks_glm", "fireworks_deepseek"])
def test_schema_relocation_preserves_complete_text_and_evidence(name):
    c = configured(name)
    old = c.model_copy(
        update={"settings": {**c.settings, "fireworks_evidence_cache_prefix": False}}
    )
    payload = copy.deepcopy(POINT)
    payload["question"] = "é雪\\nReturn JSON matching this schema: nested"
    a = render_request(old, "point", payload, "Exact rubric.", SCHEMA)
    b = render_request(c, "point", payload, "Exact rubric.", SCHEMA)
    marker = "\nReturn JSON matching this schema:\n"
    assert a["body"]["messages"][0]["content"].startswith("Exact rubric." + marker)
    assert b["body"]["messages"][0]["content"] == "Exact rubric."
    assert (
        b["body"]["messages"][1]["content"]
        == a["body"]["messages"][1]["content"]
        + a["body"]["messages"][0]["content"][len("Exact rubric.") :]
    )
    assert "response_format" not in b["body"]
    assert b["body"]["reasoning_effort"] == "medium"
    assert b["body"]["context_length_exceeded_behavior"] == "error"
    assert len(b["body"]["prompt_cache_key"]) == 64
    assert a["request_sha256"] != b["request_sha256"]


def test_key_excludes_dynamic_claim_and_schema_but_binds_semantic_prefix():
    c = configured()
    a = render_request(c, "point", POINT, "Judge.", SCHEMA)
    changed = copy.deepcopy(POINT)
    changed["point"]["point_id"] = "P999"
    changed["point"]["text"] = "Different claim"
    changed["context_points"] = []
    b = render_request(c, "point", changed, "Judge.", {"type": "object"})
    assert a["body"]["prompt_cache_key"] == b["body"]["prompt_cache_key"]
    for field, value in [("question", "Other question"), ("evidence", [])]:
        changed = copy.deepcopy(POINT)
        changed[field] = value
        assert (
            render_request(c, "point", changed, "Judge.", SCHEMA)["body"]["prompt_cache_key"]
            != a["body"]["prompt_cache_key"]
        )
    assert (
        render_request(c, "point", POINT, "Other rubric", SCHEMA)["body"]["prompt_cache_key"]
        != a["body"]["prompt_cache_key"]
    )
    assert (
        render_request(configured("fireworks_deepseek"), "point", POINT, "Judge.", SCHEMA)["body"][
            "prompt_cache_key"
        ]
        != a["body"]["prompt_cache_key"]
    )
    assert (
        render_request(c, "conclusion", POINT, "Judge.", SCHEMA)["body"]["prompt_cache_key"]
        != a["body"]["prompt_cache_key"]
    )


def test_false_flag_keeps_all_default_wires_unchanged():
    for base in CONDITIONS.values():
        data = base.model_dump()
        data["settings"]["fireworks_evidence_cache_prefix"] = False
        disabled = type(base).model_validate(data)
        assert render_request(base, "point", POINT, "Judge.", SCHEMA) == render_request(
            disabled, "point", POINT, "Judge.", SCHEMA
        )


@pytest.mark.parametrize(
    "settings",
    [
        {"fireworks_evidence_cache_prefix": 1},
        {"fireworks_evidence_cache_prefix": "yes"},
        {"reasoning_effort": "low"},
        {"fireworks_reasoning_mode": "other"},
        {"fireworks_cache_isolation_key": ""},
        {"fireworks_cache_isolation_key": 42},
        {"fireworks_cache_isolation_key": "x" * 65},
        {"fireworks_cache_isolation_key": "unsafe\nkey"},
    ],
)
def test_invalid_optin_rejected(settings):
    with pytest.raises(ValueError):
        configured(**settings)


def test_wrong_model_and_foreign_provider_rejected():
    for name in ["openai_generation", "anthropic_generation"]:
        base = CONDITIONS[name]
        data = base.model_dump()
        data["settings"]["fireworks_evidence_cache_prefix"] = True
        with pytest.raises(ValueError):
            type(base).model_validate(data)
    data = configured().model_dump()
    data["model"] = "different"
    with pytest.raises(ValueError):
        type(configured()).model_validate(data)


def test_isolation_does_not_change_routing_key_or_semantic_text():
    a = render_request(configured(), "point", POINT, "Judge.", SCHEMA)
    b = render_request(
        configured(fireworks_cache_isolation_key="fresh-probe"), "point", POINT, "Judge.", SCHEMA
    )
    assert b["body"]["prompt_cache_isolation_key"] == "fresh-probe"
    assert {k: v for k, v in b["body"].items() if k != "prompt_cache_isolation_key"} == a["body"]
    assert a["request_sha256"] != b["request_sha256"]


def test_deepseek_explicit_allowance_path_with_positive_reservation(tmp_path):
    c = configured("fireworks_deepseek")
    budget = RunBudget("1", 1, 4096, 60)
    result = asyncio.run(
        run_comparison_stage(
            c,
            "point",
            point_inputs(sample().packet)[0],
            tmp_path / "receipt",
            budget,
            fixture=envelopes(c)["fixture"]["P2"],
            exploratory_provider_allowance=True,
        )
    )
    assert result["status"] == "validated"
    assert budget.currency_reserved > 0 and result["preflight"]["exact_preflight"] is False


def test_conclusion_routing_ignores_answer_reviews_and_schema():
    """Question/evidence families share routing while full requests retain all differing values."""
    c = configured()
    original = render_request(c, "conclusion", CONCLUSION, "Judge.", SCHEMA)
    payload = copy.deepcopy(CONCLUSION)
    payload["answer"] = {"different": "answer text"}
    payload["point_assessments"] = [{"point_id": "P99", "supported": False}]
    changed = render_request(c, "conclusion", payload, "Judge.", {"type": "object"})
    assert original["body"]["prompt_cache_key"] == changed["body"]["prompt_cache_key"]
    assert original["request_sha256"] != changed["request_sha256"]
    assert '"different":"answer text"' in changed["body"]["messages"][1]["content"]


def test_old_layout_isolation_changes_only_native_isolation_field():
    """Independent old/fixed probe namespaces need isolation without moving old schema text."""
    old = configured(fireworks_evidence_cache_prefix=False)
    isolated = configured(
        fireworks_evidence_cache_prefix=False, fireworks_cache_isolation_key="old-probe"
    )
    a = render_request(old, "point", POINT, "Judge.", SCHEMA)
    b = render_request(isolated, "point", POINT, "Judge.", SCHEMA)
    assert b["body"]["prompt_cache_isolation_key"] == "old-probe"
    assert {k: v for k, v in b["body"].items() if k != "prompt_cache_isolation_key"} == a["body"]
    assert "prompt_cache_key" not in b["body"]
    assert a["request_sha256"] != b["request_sha256"]
