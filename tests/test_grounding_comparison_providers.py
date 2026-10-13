"""Invented, credential-free provider protocol regressions for the supported conditions."""

import copy
import json
from pathlib import Path

import pytest

from er_commons.grounding_comparison_providers import (
    cache_prefix_text,
    count_request,
    decision_questions,
    load_conditions,
    parse_response,
    parse_usage,
    render_request,
)

CONDITIONS = load_conditions(Path("configs/task09e1_conditions_v2.json"))
SCHEMA = {
    "type": "object",
    "properties": {"supported": {"type": "boolean"}},
    "required": ["supported"],
    "additionalProperties": False,
}
POINT = {
    "point": {"point_id": "p1", "text": "Annual inspections.", "citation_ids": ["s1"]},
    "question": "When?",
    "evidence": [{"citation_id": "s1", "text": "Inspect annually."}],
}
GATE = {"points": [{"point_id": "p1", "text": "I cannot determine."}]}
CONCLUSION = {
    "answer": {"conclusion": {"text": "Annual."}},
    "evidence": [],
    "question": "When?",
    "point_assessments": [{"point_id": "p1", "supported": False}],
}


def native_response(condition, kind, payload, values=None):
    """Construct only documented native fields for an invented endpoint fixture."""
    response = {"model": condition.model, "usage": {"input_tokens": 30, "output_tokens": 1}}
    if condition.kind == "generation":
        text = json.dumps({"point_id": "p1", "supported": True})
        if condition.api == "openai_responses":
            response.update(
                status="completed",
                output=[{"type": "message", "content": [{"type": "output_text", "text": text}]}],
            )
        elif condition.api == "anthropic_messages":
            response.update(stop_reason="end_turn", content=[{"type": "text", "text": text}])
        else:
            response.update(
                choices=[{"finish_reason": "stop", "message": {"content": text}}],
                usage={"prompt_tokens": 30, "completion_tokens": 1},
            )
    else:
        questions = decision_questions(kind, payload)
        probabilities = values or {item["name"]: 0.8 for item in questions}
        if condition.api == "openai_decisions":
            response["answers"] = [
                {"name": q["name"], "type": "predicate", "probability": probabilities[q["name"]]}
                for q in questions
            ]
        else:
            response["answers"] = {
                q["name"]: {"type": "noul", "noul": probabilities[q["name"]]} for q in questions
            }
    return response


@pytest.mark.parametrize("condition", CONDITIONS.values(), ids=CONDITIONS)
def test_supported_conditions_render_and_parse(condition):
    rendered = render_request(condition, "point", POINT, "Judge support.", SCHEMA)
    assert rendered == render_request(condition, "point", POINT, "Judge support.", SCHEMA)
    assert rendered["body"]["model"] == condition.model
    assert rendered["endpoint"] == condition.endpoint
    assert len(rendered["request_sha256"]) == 64
    assert "api_key" not in json.dumps(rendered)
    parsed = parse_response(condition, "point", POINT, native_response(condition, "point", POINT))
    assert parsed["decision"] == {"point_id": "p1", "supported": True}
    assert parsed["usage"]["input_tokens"] == 30
    assert bool(parsed["probabilities"]) == (condition.kind == "decision")


@pytest.mark.parametrize("condition", CONDITIONS.values(), ids=CONDITIONS)
def test_wire_changes_bind_identity_and_evidence_precedes_claim(condition):
    first = render_request(condition, "point", POINT, "Judge support.", SCHEMA)
    changed = copy.deepcopy(POINT)
    changed["point"]["text"] = "Monthly inspections."
    second = render_request(condition, "point", changed, "Judge support.", SCHEMA)
    assert first["request_sha256"] != second["request_sha256"]
    visible = cache_prefix_text(first)
    assert visible.index("Inspect annually.") < visible.index("Annual inspections.")
    assert POINT["point"]["text"] == "Annual inspections."


def test_provider_specific_controls_are_explicit():
    rendered = {
        key: render_request(condition, "point", POINT, "Judge.", SCHEMA)["body"]
        for key, condition in CONDITIONS.items()
    }
    assert rendered["openai_generation"]["reasoning"] == {"effort": "low"}
    assert rendered["openai_generation"]["prompt_cache_options"]["ttl"] == "30m"
    assert rendered["anthropic_generation"]["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in rendered["anthropic_generation"]
    assert rendered["fireworks_glm"]["response_format"]["type"] == "json_schema"
    assert "schema" in rendered["fireworks_glm"]["messages"][0]["content"]
    for key in ("openai_decisions", "typesafe_jev"):
        assert not {"max_tokens", "max_output_tokens", "temperature"} & rendered[key].keys()


@pytest.mark.parametrize("key", ["openai_decisions", "typesafe_jev"])
@pytest.mark.parametrize(
    "substantive,clean,result",
    [(0.1, 0.9, "clean_abstention"), (0.9, 0.1, "substantive"), (0.1, 0.1, "ambiguous")],
)
def test_native_gate_preserves_three_categories(key, substantive, clean, result):
    condition = CONDITIONS[key]
    response = native_response(
        condition, "abstention", GATE, {"substantive": substantive, "clean_abstention": clean}
    )
    assert parse_response(condition, "abstention", GATE, response)["decision"] == {
        "classification": result
    }


@pytest.mark.parametrize("key", ["openai_decisions", "typesafe_jev"])
@pytest.mark.parametrize("bad", [True, "0.9", None, -0.1, 1.1, float("nan"), float("inf"), 0.5])
def test_native_probabilities_fail_closed(key, bad):
    condition = CONDITIONS[key]
    response = native_response(condition, "point", POINT, {"supported": bad})
    with pytest.raises(ValueError):
        parse_response(condition, "point", POINT, response)


@pytest.mark.parametrize("key", ["openai_decisions", "typesafe_jev"])
def test_native_gate_rejects_contradiction_and_conclusion_preserves_reviews(key):
    condition = CONDITIONS[key]
    response = native_response(condition, "abstention", GATE)
    with pytest.raises(ValueError, match="Inconsistent"):
        parse_response(condition, "abstention", GATE, response)
    response = native_response(
        condition,
        "conclusion",
        CONCLUSION,
        {"clean_abstention": 0.1, "conclusion_supported": 0.8, "review_0": 0.2},
    )
    assert parse_response(condition, "conclusion", CONCLUSION, response)["decision"] == {
        "clean_abstention": False,
        "conclusion_supported": True,
        "point_reviews": [{"point_id": "p1", "supported": False}],
    }


@pytest.mark.parametrize("key", ["openai_decisions", "typesafe_jev"])
def test_native_missing_unexpected_ids_refusal_and_wrong_model(key):
    condition = CONDITIONS[key]
    response = native_response(condition, "point", POINT)
    response["model"] = "substituted-model"
    with pytest.raises(ValueError, match="model"):
        parse_response(condition, "point", POINT, response)
    for answers in (
        [],
        {},
        [{"type": "refusal", "name": "supported"}],
        {"supported": {"type": "refusal"}},
    ):
        response = native_response(condition, "point", POINT)
        response["answers"] = answers
        with pytest.raises(ValueError):
            parse_response(condition, "point", POINT, response)


def test_openai_duplicate_names_fail():
    condition = CONDITIONS["openai_decisions"]
    response = native_response(condition, "point", POINT)
    response["answers"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        parse_response(condition, "point", POINT, response)


def test_exact_count_binding_only_for_responses():
    for condition in CONDITIONS.values():
        rendered = render_request(condition, "point", POINT, "Judge.", SCHEMA)
        if condition.id != "openai_generation":
            with pytest.raises(ValueError, match="No qualified"):
                count_request(rendered)
            continue
        count = count_request(rendered)
        assert count["counted_request_sha256"] == rendered["request_sha256"]
        assert count["body"]["input"] == rendered["body"]["input"]
        assert count["body"]["text"] == rendered["body"]["text"]
        assert count["body"]["reasoning"] == rendered["body"]["reasoning"]


def test_native_cache_bucket_arithmetic():
    condition = CONDITIONS["openai_generation"]
    usage = parse_usage(
        condition,
        {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 2,
                "input_tokens_details": {"cached_tokens": 30, "cache_write_tokens": 20},
            }
        },
    )
    assert usage["ordinary_input_tokens"] == 50
    condition = CONDITIONS["anthropic_generation"]
    usage = parse_usage(
        condition,
        {
            "usage": {
                "input_tokens": 50,
                "output_tokens": 2,
                "cache_read_input_tokens": 30,
                "cache_creation_input_tokens": 20,
            }
        },
    )
    assert usage["input_tokens"] == 100
    assert usage["ordinary_input_tokens"] == 50
    for value in (-1, True, 1.5):
        with pytest.raises(ValueError):
            parse_usage(condition, {"usage": {"input_tokens": value, "output_tokens": 0}})


def test_unknown_cache_usage_stays_unknown():
    for key in ("typesafe_jev", "fireworks_glm", "anthropic_generation"):
        condition = CONDITIONS[key]
        response = native_response(condition, "point", POINT)
        assert parse_usage(condition, response)["cache_read_tokens"] is None
        assert parse_usage(condition, response)["cache_write_tokens"] is None


@pytest.mark.parametrize(
    "key", ["openai_generation", "anthropic_generation", "fireworks_glm", "fireworks_deepseek"]
)
def test_generation_truncation_refusal_and_malformed_json(key):
    condition = CONDITIONS[key]
    response = native_response(condition, "point", POINT)
    if condition.api == "openai_responses":
        response["status"] = "incomplete"
    elif condition.api == "anthropic_messages":
        response["stop_reason"] = "max_tokens"
    else:
        response["choices"][0]["finish_reason"] = "length"
    with pytest.raises(ValueError):
        parse_response(condition, "point", POINT, response)


def test_config_retains_capability_blockers():
    assert CONDITIONS["typesafe_jev"].state_question_limit == 32000
    assert CONDITIONS["openai_decisions"].context_limit is None
    assert (
        "authoritative_counter_documented_as_estimate"
        in CONDITIONS["anthropic_generation"].blockers
    )


def test_openai_strict_schema_keeps_empty_optional_diagnostics_valid():
    """Strict transport requires fields while semantic validation permits empty diagnostics."""
    from er_commons.grounding_comparison_semantics import GenerationPoint

    schema = GenerationPoint.model_json_schema()
    original = copy.deepcopy(schema)
    condition = CONDITIONS["openai_generation"]
    rendered = render_request(condition, "point", POINT, "Judge.", schema)
    strict = rendered["body"]["text"]["format"]["schema"]
    assert set(strict["required"]) == set(strict["properties"])
    assert strict["$defs"]["Quote"]["required"] == ["citation_id", "excerpt"]
    assert "default" not in strict["properties"]["explanation"]
    assert schema == original
    parsed = GenerationPoint.model_validate(
        {
            "point_id": "p1",
            "supported": True,
            "explanation": "",
            "locators": [],
            "unsupported_assertions": [],
        }
    )
    assert parsed.supported is True


@pytest.mark.parametrize("condition", CONDITIONS.values(), ids=CONDITIONS)
@pytest.mark.parametrize(
    "mutation",
    [
        {"usage": []},
        {"usage": {"input_tokens": 2, "output_tokens": 1, "input_tokens_details": []}},
        {"output": [None], "content": [None], "choices": [None], "answers": [None]},
    ],
)
def test_malformed_native_shapes_raise_value_error(condition, mutation):
    response = native_response(condition, "point", POINT)
    response.update(mutation)
    with pytest.raises(ValueError):
        parse_response(condition, "point", POINT, response)


def test_generation_duplicate_json_fields_fail():
    condition = CONDITIONS["openai_generation"]
    response = native_response(condition, "point", POINT)
    response["output"][0]["content"][0]["text"] = '{"supported":false,"supported":true}'
    with pytest.raises(ValueError, match="Duplicate"):
        parse_response(condition, "point", POINT, response)


@pytest.mark.parametrize("key", ["openai_generation", "anthropic_generation"])
@pytest.mark.parametrize("ids", [[], ["p1"], ["p1", "p2", "p3"]])
def test_portable_conclusion_schema_preserves_order_in_local_contract(key, ids):
    """Unsupported positional arrays become item unions, never implicit acceptance of bad order."""
    from er_commons.grounding_comparison_semantics import GenerationConclusion

    schema = GenerationConclusion.model_json_schema()
    array = schema["properties"]["point_reviews"]
    array.pop("items")
    if ids:
        array["prefixItems"] = []
        for point_id in ids:
            item = copy.deepcopy(schema["$defs"]["GenerationReview"])
            item["properties"]["point_id"]["const"] = point_id
            array["prefixItems"].append(item)
    array.update(minItems=len(ids), maxItems=len(ids))
    rendered = render_request(CONDITIONS[key], "conclusion", CONCLUSION, "Review.", schema)
    body = rendered["body"]
    wire = (
        body["text"]["format"]["schema"]
        if key == "openai_generation"
        else body["output_config"]["format"]["schema"]
    )
    reviews = wire["properties"]["point_reviews"]
    assert "prefixItems" not in json.dumps(wire)
    assert "items" in reviews
    if ids:
        assert json.dumps(ids, separators=(",", ":")) in reviews["description"]
    else:
        assert "empty array" in reviews["description"]
    if key == "anthropic_generation":
        assert "maxItems" not in reviews
        assert reviews.get("minItems", 0) in {0, 1}
    else:
        assert reviews["maxItems"] == len(ids)
    assert schema["properties"]["point_reviews"]["maxItems"] == len(ids)


def test_openai_completed_nullable_error_and_reasoning_envelope():
    """Successful Responses envelopes include null error fields and optional reasoning items."""
    condition = CONDITIONS["openai_generation"]
    response = native_response(condition, "point", POINT)
    response.update(error=None, incomplete_details=None)
    response["output"].insert(0, {"id": "invented-reasoning", "type": "reasoning", "summary": []})
    parsed = parse_response(condition, "point", POINT, response)
    assert parsed["decision"] == {"point_id": "p1", "supported": True}
    assert parsed["usage"]["input_tokens"] == 30
    assert parsed["usage"]["output_tokens"] == 1


@pytest.mark.parametrize(
    "error", [{"code": "server_error", "message": "invented"}, {}, "", False, 0]
)
def test_nonnull_native_error_is_rejected_even_with_completed_output(error):
    """Only absence or null means no provider error; falsey nonnull payloads still fail."""
    condition = CONDITIONS["openai_generation"]
    response = native_response(condition, "point", POINT)
    response["error"] = error
    with pytest.raises(ValueError, match="Native provider error"):
        parse_response(condition, "point", POINT, response)


@pytest.mark.parametrize(
    "settings",
    [
        {"temperature": 0},
        {"temperature": 2},
        {"top_p": 0.1},
        {"top_p": 1},
        {"temperature": 0.5, "top_p": 0.8},
    ],
)
def test_explicit_sampling_settings_render_and_bind_count(settings):
    """Sampling controls are opt-in and remain part of exact request/count identities."""
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"].update(settings)
    value["settings"]["reasoning_effort"] = "none"
    condition = type(base).model_validate(value)
    original = render_request(base, "point", POINT, "Judge.", SCHEMA)
    rendered = render_request(condition, "point", POINT, "Judge.", SCHEMA)
    counted = count_request(rendered)
    assert not {"temperature", "top_p"} & original["body"].keys()
    for key, expected in settings.items():
        assert rendered["body"][key] == expected
        assert key not in counted["body"]
    assert rendered["request_sha256"] != original["request_sha256"]
    assert counted["counted_request_sha256"] == rendered["request_sha256"]


@pytest.mark.parametrize(
    "name,value",
    [
        ("temperature", True),
        ("temperature", -0.1),
        ("temperature", 2.1),
        ("temperature", float("nan")),
        ("temperature", float("inf")),
        ("temperature", "0"),
        ("temperature", None),
        ("top_p", 0),
        ("top_p", 1.1),
        ("top_p", False),
        ("top_p", float("nan")),
    ],
)
def test_explicit_sampling_settings_reject_invalid_values(name, value):
    """Falsey, coerced and nonfinite configuration values cannot become native controls."""
    base = CONDITIONS["openai_generation"]
    data = base.model_dump()
    data["settings"][name] = value
    data["settings"]["reasoning_effort"] = "none"
    with pytest.raises(ValueError, match="sampling setting"):
        type(base).model_validate(data)


@pytest.mark.parametrize("retention", [None, "in_memory", "24h"])
def test_older_openai_cache_controls_are_explicit_and_optional(retention):
    """Models lacking new cache controls can omit them without inheriting Luna settings."""
    base = CONDITIONS["openai_generation"]
    data = base.model_dump()
    data["model"] = "gpt-5.4"
    del data["settings"]["prompt_cache_options"]
    if retention is not None:
        data["settings"]["prompt_cache_retention"] = retention
    condition = type(base).model_validate(data)
    request = render_request(condition, "point", POINT, "Judge.", SCHEMA)
    assert "prompt_cache_options" not in request["body"]
    assert request["body"].get("prompt_cache_retention") == retention
    assert "prompt_cache_retention" not in count_request(request)["body"]


@pytest.mark.parametrize("retention", [None, "30m", 24, True, [], {}])
def test_invalid_explicit_cache_retention_rejected(retention):
    base = CONDITIONS["openai_generation"]
    data = base.model_dump()
    data["settings"]["prompt_cache_retention"] = retention
    with pytest.raises(ValueError, match="cache retention"):
        type(base).model_validate(data)


@pytest.mark.parametrize("setting", ["temperature", "top_p"])
def test_luna_sampling_requires_no_reasoning(setting):
    base = CONDITIONS["openai_generation"]
    data = base.model_dump()
    data["settings"][setting] = 1
    with pytest.raises(ValueError, match="reasoning effort none"):
        type(base).model_validate(data)


@pytest.mark.parametrize("setting,first,second", [("temperature", 0, 1), ("top_p", 0.2, 1)])
def test_sampling_changes_bind_full_request_but_not_counter_body(setting, first, second):
    """Sampling affects generation identity while authoritative counting sees identical input."""
    base = CONDITIONS["openai_generation"]
    rendered = []
    for value in (first, second):
        data = base.model_dump()
        data["settings"].update(reasoning_effort="none", **{setting: value})
        condition = type(base).model_validate(data)
        rendered.append(render_request(condition, "point", POINT, "Judge.", SCHEMA))
    counts = [count_request(request) for request in rendered]
    assert counts[0]["body"] == counts[1]["body"]
    assert counts[0]["request_sha256"] == counts[1]["request_sha256"]
    assert rendered[0]["request_sha256"] != rendered[1]["request_sha256"]
    assert counts[0]["counted_request_sha256"] != counts[1]["counted_request_sha256"]
    for count, request in zip(counts, rendered, strict=True):
        assert count["counted_request_sha256"] == request["request_sha256"]
        assert "temperature" not in count["body"] and "top_p" not in count["body"]


@pytest.mark.parametrize("kind,payload", [("point", POINT), ("conclusion", CONCLUSION)])
def test_evidence_breakpoint_preserves_exact_text_schema_and_counter(kind, payload):
    """Split only at complete evidence/question values, including nested escaped content."""
    base = CONDITIONS["openai_generation"]
    payload = copy.deepcopy(payload)
    payload["evidence"] = [{"text": 'é雪 },"question":"fake",\\\n', "nested": {"answer": [1, 2]}}]
    payload["question"] = 'Which "point", and \\ path?'
    if kind == "point":
        payload["context_points"] = [{"text": "Dynamic context."}]
    original = render_request(base, kind, payload, "Judge.", SCHEMA)
    value = base.model_dump()
    value["settings"].update(evidence_cache_breakpoint=True, prompt_cache_key="fixture-cache-key")
    enabled = type(base).model_validate(value)
    rendered = render_request(enabled, kind, payload, "Judge.", SCHEMA)
    content = rendered["body"]["input"][1]["content"]
    assert len(content) == 2
    assert (
        "".join(block["text"] for block in content)
        == original["body"]["input"][1]["content"][0]["text"]
    )
    assert json.loads(content[0]["text"][:-1] + "}") == {
        "evidence": payload["evidence"],
        "question": payload["question"],
    }
    assert content[1]["text"].startswith('"context_points":' if kind == "point" else '"answer":')
    assert content[0]["prompt_cache_breakpoint"] == {"mode": "explicit"}
    assert "prompt_cache_breakpoint" not in content[1]
    assert rendered["body"]["text"] == original["body"]["text"]
    assert rendered["body"]["prompt_cache_options"] == original["body"]["prompt_cache_options"]
    assert rendered["body"]["prompt_cache_key"] == "fixture-cache-key"
    counter = count_request(rendered)
    assert counter["body"]["input"] == rendered["body"]["input"]
    assert "prompt_cache_key" not in counter["body"]
    assert "prompt_cache_options" not in counter["body"]
    assert counter["counted_request_sha256"] == rendered["request_sha256"]
    assert rendered["request_sha256"] != original["request_sha256"]


def test_disabled_breakpoint_default_and_abstention_wire_unchanged():
    """An absent/false flag does not change any provider wire request; gate stays intact."""
    for base in CONDITIONS.values():
        value = base.model_dump()
        value["settings"]["evidence_cache_breakpoint"] = False
        disabled = type(base).model_validate(value)
        assert render_request(disabled, "point", POINT, "Judge.", SCHEMA) == render_request(
            base, "point", POINT, "Judge.", SCHEMA
        )
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"]["evidence_cache_breakpoint"] = True
    enabled = type(base).model_validate(value)
    assert render_request(enabled, "abstention", GATE, "Judge.", SCHEMA) == render_request(
        base, "abstention", GATE, "Judge.", SCHEMA
    )


@pytest.mark.parametrize("flag", [None, "true", 0, 1, [], {}])
def test_evidence_breakpoint_rejects_nonboolean(flag):
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"]["evidence_cache_breakpoint"] = flag
    with pytest.raises(ValueError, match="boolean"):
        type(base).model_validate(value)


@pytest.mark.parametrize(
    "change",
    [
        {"model": "gpt-5.4"},
        {"api": "anthropic_messages"},
        {"options": None},
        {"options": {"mode": "implicit", "ttl": "24h"}},
        {"options": {"mode": "unknown", "ttl": "30m"}},
    ],
)
def test_evidence_breakpoint_rejects_incompatible_condition(change):
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"]["evidence_cache_breakpoint"] = True
    change = dict(change)
    if "options" in change:
        value["settings"]["prompt_cache_options"] = change.pop("options")
    value.update(change)
    with pytest.raises(ValueError, match="Luna Responses"):
        type(base).model_validate(value)


@pytest.mark.parametrize("key", [None, "", " ", 1, True, "x" * 65])
def test_cache_key_rejects_invalid_values(key):
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"]["prompt_cache_key"] = key
    with pytest.raises(ValueError, match="cache key"):
        type(base).model_validate(value)


def test_cache_key_provider_guard_and_explicit_mode():
    base = CONDITIONS["anthropic_generation"]
    value = base.model_dump()
    value["settings"]["prompt_cache_key"] = "fixture"
    with pytest.raises(ValueError, match="cache key"):
        type(base).model_validate(value)
    base = CONDITIONS["openai_generation"]
    value = base.model_dump()
    value["settings"].update(evidence_cache_breakpoint=True, prompt_cache_key="x" * 64)
    value["settings"]["prompt_cache_options"]["mode"] = "explicit"
    assert type(base).model_validate(value).settings["prompt_cache_key"] == "x" * 64


@pytest.mark.parametrize("kind,payload", [("point", POINT), ("conclusion", CONCLUSION)])
def test_anthropic_optin_prefix_and_estimate_preserve_input(kind, payload):
    """Split only stable evidence; counter includes native schema/thinking and exact blocks."""
    from er_commons.grounding_comparison_providers import estimated_count_request

    base = CONDITIONS["anthropic_generation"]
    data = base.model_dump()
    data["settings"]["anthropic_evidence_cache_breakpoint"] = True
    enabled = type(base).model_validate(data)
    unusual = copy.deepcopy(payload)
    unusual["question"] = 'é雪 },"question":"fake"'
    original = render_request(base, kind, unusual, "Judge unchanged.", SCHEMA)
    rendered = render_request(enabled, kind, unusual, "Judge unchanged.", SCHEMA)
    blocks = rendered["body"]["messages"][0]["content"]
    assert len(blocks) == 2
    assert (
        "".join(b["text"] for b in blocks) == original["body"]["messages"][0]["content"][0]["text"]
    )
    assert json.loads(blocks[0]["text"][:-1] + "}") == {
        "evidence": unusual["evidence"],
        "question": unusual["question"],
    }
    assert blocks[0]["cache_control"] == {"type": "ephemeral", "ttl": "5m"}
    assert "cache_control" not in blocks[1]
    assert rendered["body"]["system"] == original["body"]["system"]
    counter = estimated_count_request(rendered)
    assert counter["body"] == {k: v for k, v in rendered["body"].items() if k != "max_tokens"}
    assert counter["counting_mode"] == "provider_estimate"
    assert counter["counted_request_sha256"] == rendered["request_sha256"]
    assert counter["request_sha256"] != rendered["request_sha256"]
    counter["body"]["messages"].clear()
    assert rendered["body"]["messages"]
    with pytest.raises(ValueError, match="exact counter"):
        count_request(rendered)


def test_estimated_counter_rejects_other_endpoints_and_unreviewed_fields():
    """Future input-bearing settings cannot be silently omitted from qualification."""
    from er_commons.grounding_comparison_providers import estimated_count_request

    for base in CONDITIONS.values():
        rendered = render_request(base, "point", POINT, "Judge.", SCHEMA)
        if base.api != "anthropic_messages":
            with pytest.raises(ValueError, match="estimated counter"):
                estimated_count_request(rendered)
        else:
            rendered["body"]["new_field"] = "unreviewed"
            with pytest.raises(ValueError, match="Unreviewed"):
                estimated_count_request(rendered)


def test_fireworks_prompt_schema_reasoning_is_optin():
    """New reasoning mode preserves all prompt/schema text; historical mode stays native strict."""
    base = CONDITIONS["fireworks_glm"]
    data = base.model_dump()
    data["settings"].update(fireworks_reasoning_mode="prompt_schema", reasoning_effort="medium")
    condition = type(base).model_validate(data)
    old = render_request(base, "point", POINT, "Judge.", SCHEMA)
    new = render_request(condition, "point", POINT, "Judge.", SCHEMA)
    assert new["body"]["messages"] == old["body"]["messages"]
    assert "response_format" not in new["body"]
    assert old["body"]["response_format"]["type"] == "json_schema"
    assert new["body"]["reasoning_effort"] == "medium"
    assert new["body"]["context_length_exceeded_behavior"] == "error"
    assert "reasoning_effort" not in old["body"]
    assert new["request_sha256"] != old["request_sha256"]


@pytest.mark.parametrize("flag", [None, 1, "true"])
def test_anthropic_breakpoint_rejects_coercion(flag):
    """Cache opt-in is a genuine boolean, never truthy input."""
    base = CONDITIONS["anthropic_generation"]
    data = base.model_dump()
    data["settings"]["anthropic_evidence_cache_breakpoint"] = flag
    with pytest.raises(ValueError, match="Anthropic evidence"):
        type(base).model_validate(data)


@pytest.mark.parametrize("key", ["openai_generation", "fireworks_glm", "fireworks_deepseek"])
def test_anthropic_breakpoint_rejects_foreign_provider(key):
    """New Anthropic mode cannot accidentally enable on another provider."""
    base = CONDITIONS[key]
    data = base.model_dump()
    data["settings"]["anthropic_evidence_cache_breakpoint"] = True
    with pytest.raises(ValueError, match="Anthropic evidence"):
        type(base).model_validate(data)


@pytest.mark.parametrize(
    "change", [{"mode": None}, {"mode": "strict"}, {"effort": "low"}, {"model": "other"}]
)
def test_fireworks_reasoning_mode_rejects_unqualified_combinations(change):
    """Only the specifically qualified medium GLM Flash condition gets the new mode."""
    base = CONDITIONS["fireworks_glm"]
    data = base.model_dump()
    data["settings"].update(
        fireworks_reasoning_mode=change.get("mode", "prompt_schema"),
        reasoning_effort=change.get("effort", "medium"),
    )
    data["model"] = change.get("model", data["model"])
    with pytest.raises(ValueError, match="Fireworks prompt-schema"):
        type(base).model_validate(data)


def test_disabled_anthropic_breakpoint_keeps_historical_requests():
    """False remains a no-op for all providers; enabled Haiku gate remains unsplit."""
    for base in CONDITIONS.values():
        data = base.model_dump()
        data["settings"]["anthropic_evidence_cache_breakpoint"] = False
        disabled = type(base).model_validate(data)
        assert render_request(base, "point", POINT, "Judge.", SCHEMA) == render_request(
            disabled, "point", POINT, "Judge.", SCHEMA
        )
    base = CONDITIONS["anthropic_generation"]
    data = base.model_dump()
    data["settings"]["anthropic_evidence_cache_breakpoint"] = True
    enabled = type(base).model_validate(data)
    payload = {"points": []}
    assert render_request(base, "abstention", payload, "Judge.", SCHEMA) == render_request(
        enabled, "abstention", payload, "Judge.", SCHEMA
    )
