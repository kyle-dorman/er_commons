"""Offline A provider rendering, Inspect scoring and durable log boundaries."""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx2
import pytest
from inspect_ai._util.content import ContentText
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from judge_native_fixtures import envelope
from tenacity import wait_none

from er_commons import no_answer_inspect as native

PACKET = {"candidate_conclusion": "  I cannot determine the deadline.\n"}
WIRE = {"classification": "clean_abstention", "reason": "The conclusion explicitly declines."}


def model_fixture(monkeypatch: pytest.MonkeyPatch, provider: str, handler: Any) -> Any:
    """Inject only HTTP transport; native SDK rendering and Inspect retries remain real."""
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FIREWORKS_API_KEY"):
        monkeypatch.setenv(name, "offline-fixture-key")
    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    if provider == "fireworks_glm":
        from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI

        monkeypatch.setattr(OpenAICompatibleAPI, "_create_http_client", lambda self: client)
        model = native.native_model(provider)
        model.api.stream = False
    else:
        model = native.native_model(provider, http_client=client, streaming=False)
    monkeypatch.setattr(model.api, "retry_wait", lambda: wait_none())
    return model


def messages(provider: str = "openai_generation") -> list[Any]:
    """Use exactly the native adapter's provider-specific system block."""
    prompt = native.core.system_prompt()
    content = (
        [ContentText(text=prompt, cache_breakpoint=True)]
        if provider == "anthropic_generation"
        else prompt
    )
    return [ChatMessageSystem(content=content), ChatMessageUser(content=json.dumps(PACKET))]


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation", "fireworks_glm"])
def test_native_provider_rendering_and_fresh_repetitions(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    """Exercise real SDK rendering through local HTTP mocks, including cache metadata."""
    bodies, headers = [], []

    def handler(request: Any) -> Any:
        bodies.append(json.loads(request.content))
        headers.append(dict(request.headers))
        return httpx2.Response(200, json=envelope(provider, json.dumps(WIRE)))

    model = model_fixture(monkeypatch, provider, handler)

    async def run() -> Any:
        return [await model.generate(messages(provider)) for _ in range(2)]

    outputs = asyncio.run(run())
    assert len(bodies) == 2
    assert bodies[0] == bodies[1]
    assert all(output.completion == json.dumps(WIRE) for output in outputs)
    assert outputs[0].usage.input_tokens_cache_read == 50
    body = bodies[0]
    if provider == "openai_generation":
        schema = body["text"]["format"]["schema"]
        assert body["text"]["format"]["strict"] is True
        assert body["reasoning"]["effort"] == "medium"
        assert body["store"] is False
        assert body["truncation"] == "disabled"
        assert body["prompt_cache_key"]
        assert "temperature" not in body and "seed" not in body
        assert "prompt_cache_options" not in body
    elif provider == "anthropic_generation":
        schema = body["output_format"]["schema"]
        assert body["system"][0]["text"] == native.core.system_prompt()
        assert body["system"][0]["cache_control"] == {"type": "ephemeral", "ttl": "5m"}
        assert body["thinking"]["type"] == "adaptive"
        assert body["output_config"]["effort"] == "medium"
        assert "cache_control" not in json.dumps(body["messages"])
        assert "temperature" not in body and "seed" not in body
    else:
        assert body["temperature"] == 0 and body["top_p"] == 1 and body["seed"] == 0
        assert body["reasoning_effort"] == "medium"
        assert body["user"] == body["prompt_cache_key"]
        assert body["context_length_exceeded_behavior"] == "error"
        assert headers[0]["x-session-affinity"] == body["prompt_cache_key"]
        assert "response_format" not in body
        assert body["messages"][0]["content"] == native.core.system_prompt()
        assert "Output serialization checklist:" in body["messages"][0]["content"]
        return
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"classification", "reason"}
    assert set(schema["required"]) == {"classification", "reason"}
    assert set(schema["properties"]["classification"]["enum"]) == {
        "clean_abstention",
        "substantive",
        "ambiguous",
    }


@pytest.mark.parametrize(
    "prediction,expected,flags",
    [
        ("clean_abstention", "clean_abstention", (False, False, False)),
        ("clean_abstention", "substantive", (True, False, False)),
        ("substantive", "clean_abstention", (False, True, False)),
        ("clean_abstention", "ambiguous", (True, False, True)),
        ("ambiguous", "clean_abstention", (False, True, True)),
        ("substantive", "ambiguous", (False, False, True)),
        ("ambiguous", "substantive", (False, False, True)),
        ("ambiguous", "ambiguous", (False, False, False)),
    ],
)
def test_native_semantic_scoring_and_logs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    prediction: str,
    expected: str,
    flags: tuple[bool, bool, bool],
) -> None:
    """Errors retain independent ambiguous/abstention flags in normal Inspect logs."""
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log

    calls = []
    raw = json.dumps({"classification": prediction, "reason": "Fixture reason."})

    def handler(request: Any) -> Any:
        calls.append(request)
        return httpx2.Response(
            200, json=envelope("openai_generation", raw), headers={"x-request-id": "req_A_fixture"}
        )

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation",
        [{"sample_id": "fixture", "case_id": "case", "mechanism": "HIDDEN", "packet": PACKET}],
        {"fixture": expected},
        provenance={"selection_sha256": "fixture_hash"},
    )
    log = read_eval_log(inspect_eval(task, log_dir=str(tmp_path), display="none")[0].location)
    assert log.status == "success"
    assert len(calls) == 1
    sample = log.samples[0]
    score = next(iter(sample.scores.values()))
    assert score.value == {"valid": 1, "correct": int(prediction == expected)}
    assert score.metadata["classification"] == prediction
    assert score.metadata["expected_classification"] == expected
    assert score.metadata["raw_output"] == raw
    assert score.metadata["guard_status"] == "not_run"
    assert (
        tuple(
            score.metadata[key]
            for key in ("false_abstention", "missed_abstention", "ambiguous_class_error")
        )
        == flags
    )
    assert score.metadata["substantive_false_abstention"] is (
        prediction == "clean_abstention" and expected == "substantive"
    )
    assert sample.metadata["mechanism"] == "HIDDEN"
    assert log.eval.metadata["panel"] == {"selection_sha256": "fixture_hash"}
    assert log.eval.metadata["component"] == "A"
    for key in ("prompt_sha256", "schema_sha256", "provider_config_sha256"):
        assert len(log.eval.metadata[key]) == 64
    events = [event for event in sample.events if event.event == "model"]
    assert len(events) == 1
    assert "req_A_fixture" in events[0].model_dump_json()
    assert "HIDDEN" not in json.dumps(json.loads(calls[0].content))


@pytest.mark.parametrize(
    "raw,truncated",
    [
        ("not JSON", False),
        ('{"classification":"substantive","reason":" "}', False),
        ('{"classification":"ambiguous","reason":"ok","extra":1}', False),
        (json.dumps(WIRE), True),
    ],
)
def test_invalid_output_is_not_a_classification_or_rerolled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, raw: str, truncated: bool
) -> None:
    """Parseable JSON with a truncation signal is still a distinct output failure."""
    from inspect_ai import eval as inspect_eval

    calls = []

    def handler(request: Any) -> Any:
        calls.append(request)
        body = envelope("openai_generation", raw)
        if truncated:
            body.update(status="incomplete", incomplete_details={"reason": "max_output_tokens"})
        return httpx2.Response(200, json=body)

    model = model_fixture(monkeypatch, "openai_generation", handler)
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: model)
    task = native.build_task(
        "openai_generation", [{"sample_id": "f", "packet": PACKET}], {"f": "substantive"}
    )
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    score = next(iter(log.samples[0].scores.values()))
    assert len(calls) == 1
    assert score.value == {"valid": 0, "correct": 0}
    assert score.metadata["status"] == "invalid_output"
    assert score.metadata["error_family"] == "output_failure"
    assert score.metadata["raw_output"] == raw
    assert "classification" not in score.metadata
    assert "false_abstention" not in score.metadata


@pytest.mark.parametrize("provider", ["openai_generation", "anthropic_generation", "fireworks_glm"])
def test_task_input_target_separation_and_resource_limits(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    """Targets and diagnostic tags stay outside the exact two-message input."""
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: None)
    task = native.build_task(
        provider,
        [{"sample_id": "s", "packet": PACKET, "mechanism_tag": "hidden"}],
        {"s": "substantive"},
        epochs=3,
    )
    sample = task.dataset[0]
    assert task.epochs == 3
    assert task.time_limit == 150
    assert len(sample.input) == 2
    assert sample.input[0].text == native.core.system_prompt()
    assert json.loads(sample.input[1].text) == PACKET
    assert sample.target == "substantive"
    assert sample.metadata["mechanism_tag"] == "hidden"
    assert sample.metadata["guard_status"] == "not_run"
    config = task.config
    assert config.max_tokens == 4096 and config.max_retries == 2
    assert config.timeout == 120 and config.attempt_timeout == 45
    assert config.max_connections == 4 and config.adaptive_connections is False
    assert config.cache is False


@pytest.mark.parametrize("epochs", [0, -1, True, 1.5])
def test_task_rejects_invalid_epochs(epochs: Any) -> None:
    with pytest.raises(ValueError, match="epochs"):
        native.build_task("openai_generation", [], {}, epochs=epochs)


@pytest.mark.parametrize(
    "samples,labels",
    [
        ([], {}),
        ([{"sample_id": "s", "packet": PACKET}], {}),
        ([{"sample_id": "s", "packet": PACKET}], {"s": "unsupported"}),
        ([{"sample_id": "s", "packet": PACKET}] * 2, {"s": "substantive"}),
        ([{"sample_id": "s", "packet": {**PACKET, "question": "leak"}}], {"s": "substantive"}),
        ([{"sample_id": "s", "packet": PACKET}], {"s": "substantive", "extra": "ambiguous"}),
    ],
)
def test_task_rejects_bad_identity_labels_or_projection(samples: Any, labels: Any) -> None:
    with pytest.raises((ValueError, KeyError)):
        native.build_task("openai_generation", samples, labels)
