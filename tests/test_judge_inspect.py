"""Cross-component invariants and native Ollama wire tests, entirely offline."""

import asyncio
import json
from typing import Any

import httpx2
import pytest
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from judge_native_fixtures import envelope

from er_commons import adequacy_inspect as adequacy
from er_commons import judge_inspect as shared
from er_commons import no_answer_inspect as no_answer
from er_commons import point_grounding_inspect as grounding


def adapter(component: str) -> Any:
    """Keep component-specific interfaces explicit in cross-provider assertions."""
    return adequacy if component in {"C", "S"} else no_answer if component == "A" else grounding


@pytest.mark.parametrize("component", ["A", "G", "C", "S"])
@pytest.mark.parametrize("condition", list(shared.PROVIDERS))
def test_shared_config_and_selected_identity(component: str, condition: str) -> None:
    """All judges retain bounded generation and independently locked semantics."""
    module = adapter(component)
    config = (
        module.generation_config(condition, component)
        if component in {"C", "S"}
        else module.generation_config(condition)
    )
    selected = (
        module.selected_condition(component)
        if component in {"C", "S"}
        else module.selected_condition()
    )
    assert selected == ("anthropic_generation" if component == "S" else "openai_generation")
    assert config.max_retries == 2 and config.max_tokens == 4096
    assert config.timeout == 120 and config.attempt_timeout == 45
    assert config.cache is False and config.adaptive_connections is False
    assert config.max_connections == (1 if condition.startswith("ollama") else 4)
    if component == "G" and condition != "fireworks_glm":
        schema = config.response_schema.json_schema
        assert list(schema.properties) == ["reason", "supported"]
        assert schema.required == ["reason", "supported"]


@pytest.mark.parametrize("component", ["A", "G", "C", "S"])
@pytest.mark.parametrize("condition", ["ollama_small", "ollama_9b"])
def test_native_ollama_requests(
    monkeypatch: pytest.MonkeyPatch, component: str, condition: str
) -> None:
    """The installed Inspect Ollama adapter sends structured outputs through its SDK."""
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI

    bodies = []

    def handler(request: Any) -> Any:
        bodies.append(json.loads(request.content))
        response = envelope("fireworks_glm", '{"fixture": true}')
        response["model"] = shared.profile(condition).model
        return httpx2.Response(200, json=response)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    monkeypatch.setattr(OpenAICompatibleAPI, "_create_http_client", lambda self: client)
    module = adapter(component)
    model = (
        module.native_model(condition, component)
        if component in {"C", "S"}
        else module.native_model(condition)
    )
    model.api.stream = False
    output = asyncio.run(
        model.generate(
            [ChatMessageSystem(content="fixture system"), ChatMessageUser(content="fixture user")]
        )
    )
    assert output.completion == '{"fixture": true}'
    assert len(bodies) == 1
    body = bodies[0]
    assert body["model"] == shared.profile(condition).model
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["max_tokens"] == 4096
    assert body["temperature"] == 0 and body["seed"] == 0
    assert "prompt_cache_key" not in body
    assert shared.profile(condition).pricing is None


@pytest.mark.parametrize("component", ["A", "G", "C", "S"])
def test_selected_prompt_drift_rejected(monkeypatch: pytest.MonkeyPatch, component: str) -> None:
    """Every component validates selected semantics, including explicit build paths."""
    module = adapter(component)
    monkeypatch.setattr(module.core, "system_prompt", lambda *args, **kwargs: "changed")
    with pytest.raises(ValueError, match="version the selection"):
        module.selected_condition(component) if component in {
            "C",
            "S",
        } else module.selected_condition()


def test_selected_profile_drift_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """Changing shared prices or provider identities requires a versioned selection."""
    doc = json.loads(shared.CONFIG_PATH.read_text())
    doc["profiles"]["openai_generation"]["model"] = "changed-model"
    changed = tmp_path / "profiles.json"
    changed.write_text(json.dumps(doc))
    monkeypatch.setattr(shared, "CONFIG_PATH", changed)
    with pytest.raises(ValueError, match="version the selection"):
        no_answer.selected_condition()


@pytest.mark.parametrize(
    "samples,labels,epochs",
    [
        ([], {}, 1),
        ([{"sample_id": "x"}] * 2, {"x": True}, 1),
        ([{"sample_id": " "}], {" ": True}, 1),
        ([{"sample_id": "x"}], {"x": True, "y": False}, 1),
        ([{"sample_id": "x"}], {"x": True}, True),
    ],
)
def test_shared_sample_validation(samples: Any, labels: Any, epochs: Any) -> None:
    """Identity mismatches never create providers or silently omit labels."""
    with pytest.raises(ValueError):
        shared.validate_samples(samples, labels, epochs)
