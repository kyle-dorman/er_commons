"""Exercise native Inspect SDK transports offline, without replacing model.generate."""

import asyncio
import json
from typing import Any

import httpx2
import pytest
from inspect_ai._util.content import ContentText
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from judge_native_fixtures import envelope
from tenacity import RetryError, wait_none

from er_commons import adequacy_inspect as native

PACKET = {
    "question": "Is entry allowed?",
    "reference_conclusion": "No.",
    "candidate_conclusion": "No.",
}
WIRE = {
    "comparison": [
        {
            "reference_quotes": ["No."],
            "candidate_quotes": ["No."],
            "status": "matched",
            "reason": "The outcomes agree.",
        }
    ],
    "conclusion_adequate": True,
    "reason_codes": [],
    "reason": "The answer agrees.",
}


def model_fixture(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    handler: Any,
    *,
    prompt_version: str | None = None,
) -> Any:
    """Inject only HTTP transport; native SDK rendering and Inspect retries remain real."""
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FIREWORKS_API_KEY"):
        monkeypatch.setenv(name, "offline-fixture-key")
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    if provider == "fireworks_glm":
        from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI

        monkeypatch.setattr(OpenAICompatibleAPI, "_create_http_client", lambda self: client)
        model = native.native_model(provider, "C", prompt_version=prompt_version)
        model.api.stream = False
    else:
        model = native.native_model(
            provider, "C", prompt_version=prompt_version, http_client=client, streaming=False
        )
    monkeypatch.setattr(model.api, "retry_wait", lambda: wait_none())
    return model


def messages(provider: str = "openai_generation") -> list[Any]:
    """Use exactly the native adapter's provider-specific system block."""
    prompt = native.core.system_prompt("C", prompt_version=native.VERSIONS["C"])
    content = (
        [ContentText(text=prompt, cache_breakpoint=True)]
        if provider == "anthropic_generation"
        else prompt
    )
    return [ChatMessageSystem(content=content), ChatMessageUser(content=json.dumps(PACKET))]


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation", "fireworks_glm"])
def test_native_rendering_cache_and_usage(monkeypatch: pytest.MonkeyPatch, provider: str) -> None:
    bodies = []
    headers = []

    def handler(request: Any) -> Any:
        bodies.append(json.loads(request.content))
        headers.append(dict(request.headers))
        return httpx2.Response(
            200,
            json=envelope(provider, json.dumps(WIRE)),
            headers={"x-request-id": "req_fixture", "request-id": "req_fixture"},
        )

    model = model_fixture(monkeypatch, provider, handler)

    async def run() -> Any:
        first = await model.generate(messages(provider))
        second = await model.generate(messages(provider))
        return first, second

    outputs = asyncio.run(run())
    assert len(bodies) == 2  # Inspect response cache must not consume repeatability runs.
    assert bodies[0] == bodies[1]
    assert all(output.completion == json.dumps(WIRE) for output in outputs)
    assert outputs[0].usage.input_tokens_cache_read == 50
    body = bodies[0]
    if provider == "openai_generation":
        assert "text" in body, body
        assert body["text"]["format"]["strict"] is True
        assert body["reasoning"]["effort"] == "medium"
        assert body["prompt_cache_key"] == bodies[1]["prompt_cache_key"]
        # Native Inspect uses provider-default retention; historical 30m is unsupported.
        assert "prompt_cache_options" not in body
        schema = body["text"]["format"]["schema"]
        assert schema["additionalProperties"] is False
        assert "reason" in schema["properties"]["comparison"]["items"].get("required", []), schema
        assert "temperature" not in body and "seed" not in body
    elif provider == "anthropic_generation":
        assert body["system"][0]["cache_control"] == {"type": "ephemeral", "ttl": "5m"}
        assert body["thinking"]["type"] == "adaptive"
        assert body["output_config"]["effort"] == "medium"
        schema = body["output_format"]["schema"]
        assert schema["additionalProperties"] is False
        assert "reason" in schema["properties"]["comparison"]["items"].get("required", []), schema
        assert "temperature" not in body and "seed" not in body
        assert "cache_control" not in json.dumps(body["messages"])
    else:
        assert body["temperature"] == 0 and body["top_p"] == 1 and body["seed"] == 0
        assert body["reasoning_effort"] == "medium"
        assert body["user"] == body["prompt_cache_key"]
        assert "response_format" not in body
        assert headers[0]["x-session-affinity"] == headers[1]["x-session-affinity"]


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation", "fireworks_glm"])
@pytest.mark.parametrize("failure", ["connection", "429"])
@pytest.mark.parametrize("exhaust", [False, True])
def test_inspect_retries_are_bounded(
    monkeypatch: pytest.MonkeyPatch, provider: str, failure: str, exhaust: bool
) -> None:
    calls = []

    def handler(request: Any) -> Any:
        calls.append(request)
        if exhaust or len(calls) == 1:
            if failure == "connection":
                raise httpx2.ConnectError("offline fixture", request=request)
            return httpx2.Response(
                429, json={"error": {"message": "fixture", "type": "rate_limit_error"}}
            )
        return httpx2.Response(200, json=envelope(provider, json.dumps(WIRE)))

    model = model_fixture(monkeypatch, provider, handler)
    if exhaust:
        with pytest.raises(RetryError):
            asyncio.run(model.generate(messages(provider)))
        assert len(calls) == (9 if provider == "fireworks_glm" else 3)
    else:
        assert asyncio.run(model.generate(messages(provider))).completion == json.dumps(WIRE)
        assert len(calls) == 2


@pytest.mark.parametrize(
    "raw,valid,fidelity",
    [
        (json.dumps(WIRE), 1, True),
        ("not JSON", 0, False),
        (
            json.dumps(WIRE).replace(
                '"reason": "The outcomes agree."', '"explanation": "The outcomes agree."'
            ),
            0,
            True,
        ),
        (json.dumps(WIRE).replace("No.", "Invented."), 1, False),
    ],
)
def test_native_eval_strict_scoring_and_logs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, raw: str, valid: int, fidelity: bool
) -> None:
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log

    calls = []

    def handler(request: Any) -> Any:
        calls.append(request)
        return httpx2.Response(
            200, json=envelope("openai_generation", raw), headers={"x-request-id": "req_fixture"}
        )

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation",
        "C",
        [{"sample_id": "fixture", "case_id": "fixture", "packet": PACKET}],
        {"fixture": True},
    )
    logs = inspect_eval(task, log_dir=str(tmp_path), display="none")
    log = read_eval_log(logs[0].location)
    assert log.status == "success"
    assert len(calls) == 1
    score = next(iter(log.samples[0].scores.values()))
    assert score.value["valid"] == valid
    assert score.metadata["raw_output"] == raw
    if valid:
        assert score.value["correct"] == 1  # Quotation fidelity must never flip the label.
        assert score.metadata["quotation_fidelity"]["ok"] is fidelity
        assert score.metadata["result"]["comparison"][0]["explanation"] == "The outcomes agree."
    else:
        assert score.metadata["status"] == "invalid_output"
    assert log.samples[0].output.usage.input_tokens_cache_read == 50
    events = [event for event in log.samples[0].events if event.event == "model"]
    assert len(events) == 1
    assert "req_fixture" in events[0].model_dump_json()


def test_support_task_has_no_reference_and_native_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """All native task variants retain explicit resource and sampling bounds."""
    packet = {
        "question": "Is entry allowed?",
        "candidate_conclusion": "No.",
        "candidate_supporting_points": [{"point_id": "p1", "text": "The entrance is closed."}],
        "candidate_qualifications": [],
    }
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: None)
    for provider in native.PROVIDERS:
        task = native.build_task(
            provider,
            "S",
            [{"sample_id": "s", "case_id": "fixture", "packet": packet}],
            {"s": True},
            epochs=5,
        )
        assert task.epochs == 5
        assert json.loads(task.dataset[0].input[1].content) == packet
        assert "reference_support" not in task.dataset[0].input[1].content
        config = native.generation_config(provider, "S")
        assert config.max_tokens == 4096 and config.max_retries == 2
        assert config.timeout == 120 and config.attempt_timeout == 45
        assert config.max_connections == (1 if provider.startswith("ollama") else 4)
        assert config.adaptive_connections is False
        assert config.cache is False


def test_truncated_structured_response_is_invalid_without_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Even parseable JSON cannot conceal provider truncation."""
    from inspect_ai import eval as inspect_eval

    calls = []

    def handler(request: Any) -> Any:
        calls.append(request)
        body = envelope("openai_generation", json.dumps(WIRE))
        body.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        return httpx2.Response(200, json=body)

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation",
        "C",
        [{"sample_id": "fixture", "case_id": "fixture", "packet": PACKET}],
        {"fixture": True},
    )
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    score = next(iter(log.samples[0].scores.values()))
    assert len(calls) == 1
    assert score.value == {"correct": 0, "valid": 0}
    assert score.metadata["status"] == "invalid_output"
    assert score.metadata["raw_output"] == json.dumps(WIRE)


@pytest.mark.parametrize(
    ("component", "expected"), [("C", "openai_generation"), ("S", "anthropic_generation")]
)
def test_selected_default_routes_component(monkeypatch, component, expected):
    """Default routing honors the chosen pair without dispatching a provider call."""
    from inspect_ai import Task

    from er_commons import adequacy_calibration

    monkeypatch.setattr(adequacy_calibration, "load_panel", lambda component: ([], {}, {}))
    monkeypatch.setattr(
        native,
        "build_task",
        lambda condition_id, component, samples, labels: Task(
            metadata={"selected_condition": condition_id}
        ),
    )
    assert native.adequacy(component=component).metadata["selected_condition"] == expected
    assert (
        native.adequacy(condition_id="fireworks_glm", component=component).metadata[
            "selected_condition"
        ]
        == "fireworks_glm"
    )


def test_selected_default_rejects_prompt_drift(monkeypatch):
    """A changed selected prompt cannot silently inherit the accepted identity."""
    monkeypatch.setattr(native.core, "system_prompt", lambda *args, **kwargs: "changed prompt")
    with pytest.raises(ValueError, match="version the selection"):
        native.selected_condition("S")


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation"])
def test_explicit_candidate_binds_native_prompt_and_scoring(monkeypatch, tmp_path, provider):
    """The explicit candidate reaches native messages, parsing and log provenance."""
    from inspect_ai import eval as inspect_eval

    version = native.core.CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=envelope(provider, json.dumps(WIRE)))

    model = model_fixture(monkeypatch, provider, handler, prompt_version=version)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        provider,
        "C",
        [{"sample_id": "fixture", "case_id": "fixture", "packet": PACKET}],
        {"fixture": True},
        prompt_version=version,
    )
    prompt = native.core.system_prompt("C", prompt_version=version)
    assert task.metadata["prompt_version"] == version
    assert task.metadata["prompt_sha256"] == native.shared.stable_json_sha256(prompt)
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    assert log.status == "success"
    assert len(bodies) == 1
    assert json.dumps(prompt, ensure_ascii=False) in json.dumps(bodies[0], ensure_ascii=False)
    score = next(iter(log.samples[0].scores.values()))
    assert score.value == {"correct": 1, "valid": 1}
    assert score.metadata["prompt_version"] == version
    assert native.VERSIONS["C"] == native.core.CONCLUSION_COMPARISON_REASON_PROMPT_VERSION
    assert native.selected_condition("C") == "openai_generation"


@pytest.mark.parametrize(
    "entrypoint", ["generation_config", "native_model", "adequacy_score", "build_task"]
)
@pytest.mark.parametrize(
    "component,version",
    [("S", native.core.CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION), ("C", "unknown")],
)
def test_candidate_selection_rejects_other_semantics(monkeypatch, entrypoint, component, version):
    """Unsupported versions fail before provider construction, including C on S."""

    def forbidden(*args, **kwargs):
        raise AssertionError("provider constructed")

    monkeypatch.setattr(native.shared, "native_model", forbidden)
    args = [component] if entrypoint == "adequacy_score" else ["openai_generation", component]
    if entrypoint == "build_task":
        args += [
            [{"sample_id": "fixture", "case_id": "fixture", "packet": PACKET}],
            {"fixture": True},
        ]
    with pytest.raises(ValueError, match="Unsupported native adequacy prompt"):
        getattr(native, entrypoint)(*args, prompt_version=version)


def test_explicit_candidate_still_checks_frozen_selection(monkeypatch):
    """Candidate dispatch cannot bypass frozen selection integrity verification."""
    monkeypatch.setattr(native.core, "system_prompt", lambda *args, **kwargs: "changed prompt")
    with pytest.raises(ValueError, match="version the selection"):
        native.build_task(
            "openai_generation",
            "C",
            [{"sample_id": "fixture", "case_id": "fixture", "packet": PACKET}],
            {"fixture": True},
            prompt_version=native.core.CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION,
        )


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation"])
@pytest.mark.parametrize("version", sorted(native.core.CONCLUSION_STRUCTURED_PROMPT_VERSIONS))
def test_structured_c_native_transport_and_point_scoring(monkeypatch, tmp_path, provider, version):
    """Both native test providers receive canonical context and validate point coverage."""
    from inspect_ai import eval as inspect_eval

    from er_commons.judge_context import baylands_overview

    packet = {
        "question": "Is entry allowed?",
        "candidate_conclusion": "No.",
        "reference_required_points": [{"point_id": "R1", "text": "Entry is not allowed."}],
        "reference_optional_points": [{"point_id": "O1", "text": "The entrance is closed."}],
    }
    wire = {
        "judgments": [
            {
                "point_id": "R1",
                "status": "satisfied",
                "candidate_quotes": ["No."],
                "reason": "The answer states entry is not allowed.",
            },
            {
                "point_id": "O1",
                "status": "not_addressed",
                "candidate_quotes": [],
                "reason": "The optional entrance detail is omitted.",
            },
        ],
        "conclusion_adequate": True,
        "reason": "The required point is satisfied and neither point is contradicted.",
    }
    if version in {
        native.core.CONCLUSION_STRUCTURED_V4_PROMPT_VERSION,
        native.core.CONCLUSION_STRUCTURED_V5_PROMPT_VERSION,
    }:
        packet["candidate_statements"] = [{"statement_id": "A1", "text": "No."}]
        if version == native.core.CONCLUSION_STRUCTURED_V4_PROMPT_VERSION:
            wire["contradicting_points"] = []
        wire["conclusion_adequate"] = False

    if version == native.core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION:
        wire["internal_contradictions"] = [{"reason": "Working conflict explanation."}]
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=envelope(provider, json.dumps(wire)))

    model = model_fixture(monkeypatch, provider, handler, prompt_version=version)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        provider,
        "C",
        [{"sample_id": "fixture", "case_id": "fixture", "packet": packet}],
        {"fixture": True},
        prompt_version=version,
    )
    prompt = native.core.system_prompt("C", prompt_version=version)
    assert prompt.startswith("<project_context>\n" + baylands_overview())
    assert prompt.count("<project_context>") == 1
    assert task.metadata["prompt_sha256"] == native.shared.stable_json_sha256(prompt)
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    assert log.status == "success"
    assert len(bodies) == 1
    assert json.dumps(prompt, ensure_ascii=False) in json.dumps(bodies[0], ensure_ascii=False)
    score = next(iter(log.samples[0].scores.values()))
    if version in {
        native.core.CONCLUSION_STRUCTURED_V4_PROMPT_VERSION,
        native.core.CONCLUSION_STRUCTURED_V5_PROMPT_VERSION,
    }:
        assert score.value == {"correct": 0, "valid": 1}
        assert score.metadata["model_decision"] is False
        assert score.metadata["aggregate_decision"] is True
        assert score.metadata["aggregation_consistent"] is False
    else:
        assert score.value == {"correct": 1, "valid": 1}
    if version == native.core.CONCLUSION_STRUCTURED_V6_PROMPT_VERSION:
        assert score.metadata["model_decision"] is True
        assert score.metadata["aggregate_decision"] is False
        assert score.metadata["internal_contradictions_pass_inconsistent"] is True
        assert "candidate_statements" not in packet
    assert score.metadata["result"]["judgments"] == wire["judgments"]
    assert score.explanation == wire["reason"]
