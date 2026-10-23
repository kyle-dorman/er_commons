"""Offline native transport, message isolation and coverage failure integration."""

import json
from pathlib import Path
from typing import Any

import httpx2
import pytest
from inspect_ai import eval as inspect_eval
from judge_native_fixtures import envelope

from er_commons import required_support_coverage as core
from er_commons import required_support_coverage_inspect as native

PACKET = {
    "question": "What must be present?",
    "required_reference_point": {"point_id": "R9", "text": "A and B."},
    "candidate_supporting_points": [
        {"point_id": "S3", "text": "A."},
        {"point_id": "S7", "text": "B."},
    ],
}


@pytest.mark.parametrize("valid", [True, False])
def test_native_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, valid: bool) -> None:
    """Use real provider serialization and logs with mocked HTTP, never paid calls."""
    monkeypatch.setenv("OPENAI_API_KEY", "offline-fixture-key")
    bodies = []
    raw = json.dumps({"covered": True, "supporting_point_ids": ["S3", "S7"], "reason": "Both."})
    if not valid:
        raw = raw.replace('"S7"', '"UNKNOWN"')

    def handler(request: Any) -> Any:
        """Capture actual provider request and return the fixed fixture result."""
        bodies.append(json.loads(request.content))
        return httpx2.Response(200, json=envelope("openai_generation", raw))

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    task = native.build_task(
        "openai_generation",
        [{"sample_id": "fixture", "packet": PACKET, "family": "HIDDEN"}],
        {"fixture": True},
        epochs=2,
        model_args={"http_client": client, "streaming": False},
    )
    log = inspect_eval(task, log_dir=str(tmp_path), display="none")[0]
    assert log.status == "success"
    assert len(bodies) == 2
    for body in bodies:
        assert "HIDDEN" not in json.dumps(body)
        assert body["reasoning"]["effort"] == "medium"
        assert body["max_output_tokens"] == 4096
        schema = body["text"]["format"]["schema"]
        assert "uniqueItems" not in schema["properties"]["supporting_point_ids"]
    for sample in log.samples or []:
        score = next(iter((sample.scores or {}).values()))
        assert score.value == {"valid": int(valid), "correct": int(valid)}
        if not valid:
            assert "covered" not in score.metadata
            assert score.metadata["status"] == "invalid_output"
    assert core.output_json_schema()["properties"]["supporting_point_ids"]["uniqueItems"]


def test_settings_and_early_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid labels and hidden fields fail before constructing the native client."""
    config = native.generation_config()
    assert config.max_connections == 16
    assert config.max_retries == 2
    assert config.cache is False
    monkeypatch.setattr(native, "native_model", lambda *args, **kwargs: pytest.fail("client built"))
    with pytest.raises(ValueError):
        native.build_task(
            "openai_generation",
            [{"sample_id": "x", "packet": {**PACKET, "conclusion": "HIDDEN"}}],
            {"x": True},
        )
    with pytest.raises(ValueError):
        native.generation_config("anthropic_generation")


@pytest.mark.parametrize(
    "stop_reason", ["max_tokens", "model_length", "tool_calls", "content_filter", "unknown"]
)
def test_noncomplete_stop_reasons_have_no_label(stop_reason: str) -> None:
    """Even parseable JSON is not a semantic judgment when completion is abnormal."""
    import asyncio
    from types import SimpleNamespace

    from inspect_ai.scorer import Target

    raw = json.dumps({"covered": True, "supporting_point_ids": ["S3", "S7"], "reason": "Both"})
    state = SimpleNamespace(output=SimpleNamespace(completion=raw, stop_reason=stop_reason))
    score = asyncio.run(native.coverage_score()(state, Target("true")))
    assert score.value == {"correct": 0, "valid": 0}
    assert score.metadata["status"] == "invalid_output"
    assert "covered" not in score.metadata
