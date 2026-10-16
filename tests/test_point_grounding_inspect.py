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

from er_commons import point_grounding_inspect as native

PACKET = {
    "question": "Is entry allowed?",
    "point_text": "The entrance is closed.",
    "evidence": [
        {
            "occurrence_id": "c1",
            "source_id": "doc",
            "canonical_target": {"section_id": "s1"},
            "title": "Title",
            "full_source_text": "The entrance is closed.",
            "tables": [],
            "physical_pages": [1],
            "printed_labels": ["1"],
        }
    ],
}
WIRE = {"supported": True, "reason": "The cited source states that the entrance is closed."}


def model_fixture(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    handler: Any,
    prompt_version: str = native.PROMPT_VERSION,
) -> Any:
    """Inject only HTTP transport; native SDK rendering and Inspect retries remain real."""
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FIREWORKS_API_KEY"):
        monkeypatch.setenv(name, "offline-fixture-key")
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    if provider == "fireworks_glm":
        from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI

        monkeypatch.setattr(OpenAICompatibleAPI, "_create_http_client", lambda self: client)
        model = native.native_model(provider, prompt_version=prompt_version)
        model.api.stream = False
    else:
        model = native.native_model(
            provider, prompt_version=prompt_version, http_client=client, streaming=False
        )
    monkeypatch.setattr(model.api, "retry_wait", lambda: wait_none())
    return model


def messages(
    provider: str = "openai_generation", prompt_version: str = native.PROMPT_VERSION
) -> list[Any]:
    """Use exactly the native adapter's provider-specific system block."""
    prompt = native.core.system_prompt(prompt_version)
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
        assert set(schema["properties"]) == {"supported", "reason"}
        assert set(schema["required"]) == {"supported", "reason"}
        assert "temperature" not in body and "seed" not in body
    elif provider == "anthropic_generation":
        assert body["system"][0]["cache_control"] == {"type": "ephemeral", "ttl": "5m"}
        assert body["thinking"]["type"] == "adaptive"
        assert body["output_config"]["effort"] == "medium"
        schema = body["output_format"]["schema"]
        assert schema["additionalProperties"] is False
        assert set(schema["properties"]) == {"supported", "reason"}
        assert set(schema["required"]) == {"supported", "reason"}
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
    "raw,expected,valid,semantic",
    [
        (json.dumps(WIRE), True, 1, None),
        (json.dumps(WIRE), False, 1, "false_accept"),
        ('{"supported":false,"reason":"No supporting evidence."}', True, 1, "false_reject"),
        ("not JSON", True, 0, None),
        ('{"supported":false,"reason":" "}', False, 0, None),
        ('{"supported":0,"reason":"No."}', False, 0, None),
    ],
)
@pytest.mark.parametrize(
    "prompt_version",
    [
        native.PROMPT_VERSION,
    ],
)
def test_native_eval_strict_scores_and_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    raw: str,
    expected: bool,
    valid: int,
    semantic: str | None,
    prompt_version: str,
) -> None:
    """Native logs retain independent validity, semantic errors and external provenance."""
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log

    calls = []

    def handler(request: Any) -> Any:
        """Return a fixed offline judgment without altering native generation."""
        calls.append(request)
        return httpx2.Response(200, json=envelope("openai_generation", raw))

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation",
        [
            {
                "sample_id": "fixture",
                "case_id": "fixture",
                "packet": PACKET,
                "metadata": {"mechanism": "secret mechanism", "point_id": "secret id"},
            },
        ],
        {"fixture": expected},
        epochs=2,
        provenance={"selection_hash": "sealed"},
        prompt_version=prompt_version,
    )
    logs = inspect_eval(task, log_dir=str(tmp_path), display="none", retry_on_error=0)
    log = read_eval_log(logs[0].location)
    assert log.status == "success"
    assert len(calls) == 2  # Invalid judgment is never rerolled; two requested epochs only.
    assert log.eval.metadata["panel_provenance"] == {"selection_hash": "sealed"}
    assert log.eval.metadata["prompt_version"] == prompt_version
    for sample in log.samples:
        score = next(iter(sample.scores.values()))
        assert score.metadata["prompt_version"] == prompt_version
        assert score.value["valid"] == valid
        assert score.metadata["raw_output"] == raw
        assert sample.metadata["point_id"] == "secret id"
        if valid:
            assert score.metadata["status"] == "evaluated"
            assert score.metadata["semantic_error"] == semantic
            assert score.value["false_accept"] == int(semantic == "false_accept")
            assert score.value["false_reject"] == int(semantic == "false_reject")
        else:
            assert score.metadata["status"] == "invalid_output"
            assert score.metadata["decision"] is None
            assert score.value["false_accept"] == score.value["false_reject"] == 0
    assert all("secret" not in request.content.decode() for request in calls)


def test_native_task_bounds_and_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each profile uses the exact ID-free packet and independent G configuration."""
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: None)
    for provider in native.PROVIDERS:
        task = native.build_task(
            provider,
            [
                {"sample_id": "s", "case_id": "fixture", "packet": PACKET},
            ],
            {"s": True},
            epochs=3,
        )
        assert task.epochs == 3
        assert json.loads(task.dataset[0].input[1].content) == PACKET
        config = native.generation_config(provider)
        assert config.max_connections == (1 if provider.startswith("ollama") else 4)
        assert config.adaptive_connections is False
        assert config.max_retries == 2 and config.cache is False
        assert config.max_tokens == 4096 and config.timeout == 120
        assert config.attempt_timeout == 45
        assert (config.response_schema is None) == (provider == "fireworks_glm")


def test_truncation_invalid_even_when_json_parses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    """A truncated completion cannot masquerade as a semantic false judgment."""
    from inspect_ai import eval as inspect_eval

    calls = []

    def handler(request: Any) -> Any:
        """Simulate native output-cap termination with otherwise valid JSON."""
        calls.append(request)
        body = envelope("openai_generation", json.dumps(WIRE))
        body.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        return httpx2.Response(200, json=body)

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation",
        [
            {"sample_id": "s", "case_id": "fixture", "packet": PACKET},
        ],
        {"s": True},
    )
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    score = next(iter(log.samples[0].scores.values()))
    assert len(calls) == 1
    assert score.metadata["decision"] is None
    assert score.metadata["error_type"] == "truncated_output"
    assert score.value["valid"] == 0


def test_cli_factory_forwards_epochs_and_panel_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI supports requested repetitions without accessing non-calibration pools."""
    from er_commons import point_grounding_panel

    monkeypatch.setattr(
        point_grounding_panel,
        "load_panel",
        lambda: (
            [{"sample_id": "s", "case_id": "fixture", "packet": PACKET}],
            {"s": True},
            {"locked": True},
        ),
    )
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: None)
    task = native.point_grounding(epochs=3, prompt_version=native.core.PROMPT_VERSION)
    assert task.metadata["prompt_version"] == native.core.PROMPT_VERSION
    assert task.epochs == 3
    assert task.metadata["panel_provenance"] == {"locked": True}
    with pytest.raises(ValueError, match="locked calibration"):
        native.point_grounding(panel="held_out")


@pytest.mark.parametrize(
    "metadata",
    [
        {"owned_citation_ids": ["different"]},
        {"status": "precheck_failed"},
        {"status": "execution_error"},
        {"status": "invalid_input"},
    ],
)
def test_invalid_ownership_or_prechecks_fail_before_provider(
    monkeypatch: pytest.MonkeyPatch,
    metadata: dict[str, Any],
) -> None:
    """Never initialize generation for mismatched ownership or failed evaluator checks."""

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        """Fail if provider construction precedes complete input validation."""
        pytest.fail("provider must not be constructed")

    monkeypatch.setattr(native, "native_model", forbidden)
    with pytest.raises(ValueError):
        native.build_task(
            "openai_generation",
            [
                {"sample_id": "s", "case_id": "fixture", "packet": PACKET, "metadata": metadata},
            ],
            {"s": True},
        )
