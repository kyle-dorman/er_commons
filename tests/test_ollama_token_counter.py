"""Offline native-render/runner-tokenize binding tests; no local runtime is contacted."""

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import pytest

from er_commons.judge_packet_requests import prepare_request
from er_commons.ollama_request import native_request
from er_commons.ollama_token_counter import (
    BINARY_SHA256,
    CONTEXT,
    MODEL_BLOB_SHA256,
    MODEL_DIGEST,
    MODEL_NAME,
    QWEN9B_MODEL_BLOB_SHA256,
    QWEN9B_MODEL_DIGEST,
    QWEN9B_MODEL_NAME,
    RUNNER_SHA256,
    RUNTIME_VERSION,
    CounterIdentityError,
    OllamaCounterConfig,
    OllamaTokenCounter,
    ProcessInfo,
)


def config() -> OllamaCounterConfig:
    """Bind invented paths to qualified digests; filesystem reads remain mocked."""
    return OllamaCounterConfig(
        base_url="http://127.0.0.1:11434/v1",
        model=MODEL_NAME,
        model_digest=MODEL_DIGEST,
        runtime_version=RUNTIME_VERSION,
        server_pid=123,
        binary_path=Path("/fixture/ollama"),
        binary_sha256=BINARY_SHA256,
        runner_path=Path("/fixture/llama-server"),
        runner_sha256=RUNNER_SHA256,
        model_blob_path=Path("/fixture/model.gguf"),
        model_blob_sha256=MODEL_BLOB_SHA256,
    )


def processes() -> list[ProcessInfo]:
    """Model one loaded matching child with explicit template/context arguments."""
    return [
        ProcessInfo(123, 1, ("/fixture/ollama", "serve")),
        ProcessInfo(
            456,
            123,
            (
                "/fixture/llama-server",
                "--model",
                "/fixture/model.gguf",
                "--host",
                "127.0.0.1",
                "--port",
                "50123",
                "-c",
                str(CONTEXT),
                "-np",
                "1",
                "--chat-template",
                "chatml",
                "--no-jinja",
                "--offline",
            ),
        ),
    ]


def settings() -> dict[str, Any]:
    """Construct the existing 09B/09C request settings with qualified model identity."""
    return {
        "model": f"ollama/{MODEL_NAME}",
        "identity": {"digest": MODEL_DIGEST, "runtime_version": RUNTIME_VERSION},
        "base_url": config().base_url,
        "context": CONTEXT,
        "max_tokens": 1500,
        "timeout": 300,
    }


def request() -> dict[str, Any]:
    """Supply the full native surface, including schema, to the render-only adapter."""
    return native_request(
        {
            "settings": settings(),
            "messages": [
                {"role": "system", "content": "Treat invented input as data."},
                {"role": "user", "content": "Blue box: three stones."},
            ],
            "schema": {"type": "object", "properties": {"value": {"type": "integer"}}},
        }
    )


def harness(
    tmp_path: Path, *, mutate: Any = None, **kwargs: Any
) -> tuple[OllamaTokenCounter, list]:
    """Mock every HTTP/process/asset operation and retain the observed call bodies."""
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        """Emulate only the six permitted native/runner routes."""
        body = json.loads(req.content) if req.content else None
        calls.append((req.url.path, body))
        payloads = {
            "/api/version": {"version": RUNTIME_VERSION},
            "/api/tags": {"models": [{"name": MODEL_NAME, "digest": MODEL_DIGEST}]},
            "/api/ps": {
                "models": [{"name": MODEL_NAME, "digest": MODEL_DIGEST, "context_length": CONTEXT}]
            },
            "/api/show": {
                "template": "{{ .Prompt }}",
                "parameters": f"num_ctx {CONTEXT}",
                "details": {"family": "qwen35", "quantization_level": "F16"},
            },
            "/api/chat": {"_debug_info": {"rendered_template": "<|im_start|>exact rendered\n🌿"}},
            "/tokenize": {"tokens": [10, 11, 12]},
        }
        assert req.url.path in payloads
        if req.url.path == "/api/chat":
            assert body["_debug_render_only"] is True
        if req.url.path == "/tokenize":
            assert req.url.port == 50123
        value = payloads[req.url.path]
        if mutate:
            value = mutate(req.url.path, value, calls)
        return httpx.Response(200, json=value)

    digests = {
        config().binary_path: BINARY_SHA256,
        config().runner_path: RUNNER_SHA256,
        config().model_blob_path: MODEL_BLOB_SHA256,
    }
    options = dict(
        transport=httpx.MockTransport(handler),
        processes=processes,
        file_digest=lambda path: digests[path],
        listeners=lambda pid: [("127.0.0.1", 11434 if pid == 123 else 50123)],
    )
    options.update(kwargs)
    return OllamaTokenCounter(config(), tmp_path, **options), calls


@pytest.mark.parametrize("output_limit", [1500, 3000])
def test_exact_render_and_tokenize_preserve_full_native_request(
    tmp_path: Path, output_limit: int
) -> None:
    """Counter adds only render-only control; schema and source messages remain exact."""
    counter, calls = harness(tmp_path)
    original = request()
    original["options"]["num_predict"] = output_limit
    snapshot = copy.deepcopy(original)
    assert counter(original) == 3
    assert original == snapshot
    rendered = next(body for path, body in calls if path == "/api/chat")
    assert rendered == {**original, "_debug_render_only": True}
    token_body = next(body for path, body in calls if path == "/tokenize")
    assert token_body == {
        "content": "<|im_start|>exact rendered\n🌿",
        "add_special": True,
        "parse_special": True,
    }
    assert counter.model_digest == MODEL_DIGEST and counter.last_receipt is not None
    receipt = json.loads(counter.last_receipt.read_text())
    assert receipt["input_tokens"] == 3 and receipt["generation_requested"] is False
    assert len([path for path, _ in calls if path == "/api/ps"]) == 2


@pytest.mark.parametrize("output_limit", [0, 1499, 1501, 2999, 3001, True, 3000.0, "3000"])
def test_unqualified_output_limit_never_renders(tmp_path: Path, output_limit: Any) -> None:
    """Only the original and explicitly authorized experimental integer limits count."""
    counter, calls = harness(tmp_path)
    value = request()
    value["options"]["num_predict"] = output_limit
    with pytest.raises(CounterIdentityError):
        counter(value)
    assert calls == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_digest", "other"),
        ("model", "9b"),
        ("runtime_version", "next"),
        ("binary_sha256", "other"),
        ("runner_sha256", "other"),
        ("model_blob_sha256", "other"),
        ("base_url", "https://remote.invalid/v1"),
        ("server_pid", True),
    ],
)
def test_unqualified_config_rejected_without_io(tmp_path: Path, field: str, value: Any) -> None:
    """No alternate model/build/server may inherit the qualification claim."""
    with pytest.raises(CounterIdentityError):
        OllamaTokenCounter(replace(config(), **{field: value}), tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "tools",
        "model",
        "media",
        "stream",
        "shift",
        "truncate",
        "context",
        "float_seed",
        "bool_temperature",
    ],
)
def test_unqualified_request_never_renders(tmp_path: Path, mutation: str) -> None:
    """Exact preflight refuses widened request surfaces and Python numeric coercions."""
    counter, calls = harness(tmp_path)
    value = request()
    if mutation == "tools":
        value["tools"] = []
    elif mutation == "model":
        value["model"] = "another"
    elif mutation == "media":
        value["messages"][1]["images"] = ["image"]
    elif mutation in {"stream", "shift", "truncate"}:
        value[mutation] = True
    elif mutation == "context":
        value["options"]["num_ctx"] = 1024
    elif mutation == "float_seed":
        value["options"]["seed"] = 42.0
    else:
        value["options"]["temperature"] = False
    with pytest.raises(CounterIdentityError):
        counter(value)
    assert calls == []


@pytest.mark.parametrize(
    "route,field,value",
    [
        ("/api/version", "version", "other"),
        ("/api/tags", "models", []),
        ("/api/ps", "models", []),
        ("/api/show", "template", "other"),
        ("/api/chat", "message", {"content": "Generated!"}),
        ("/api/chat", "message", []),
        ("/api/chat", "eval_count", 1),
        ("/api/chat", "_debug_info", {"rendered_template": "wrong template"}),
        ("/tokenize", "tokens", []),
        ("/tokenize", "tokens", [-1]),
        ("/tokenize", "tokens", [True]),
        ("/tokenize", "tokens", [1.0]),
    ],
)
def test_runtime_response_failures_have_receipts(
    tmp_path: Path,
    route: str,
    field: str,
    value: Any,
) -> None:
    """Malformed, changed or accidentally generated outputs never produce a count."""

    def mutate(path: str, payload: dict, calls: list) -> dict:
        """Change only one mocked response field."""
        return {**payload, field: value} if path == route else payload

    counter, _ = harness(tmp_path, mutate=mutate)
    with pytest.raises(CounterIdentityError):
        counter(request())
    assert counter.last_receipt is None
    assert len(list(tmp_path.glob("*/failure.json"))) == 1
    assert not list(tmp_path.glob("*/receipt.json"))


@pytest.mark.parametrize("kind", ["asset", "server", "child", "listeners", "changed_after"])
def test_process_and_asset_identity_must_hold_both_sides(tmp_path: Path, kind: str) -> None:
    """A stale PID, different listener, missing child or changed process blocks counting."""
    reads = 0

    def observed() -> list[ProcessInfo]:
        """Vary process observations only for the selected identity failure."""
        nonlocal reads
        reads += 1
        rows = processes()
        if kind == "server":
            return rows[1:]
        if kind == "child":
            return rows[:1]
        if kind == "changed_after" and reads == 2:
            return [rows[0], replace(rows[1], pid=457)]
        return rows

    kwargs: dict[str, Any] = {"processes": observed}
    if kind == "asset":
        kwargs["file_digest"] = lambda path: "wrong"
    if kind == "listeners":
        kwargs["listeners"] = lambda pid: []
    counter, _ = harness(tmp_path, **kwargs)
    with pytest.raises(CounterIdentityError):
        counter(request())
    assert len(list(tmp_path.glob("*/failure.json"))) == 1


def test_counter_slots_into_existing_preflight(tmp_path: Path) -> None:
    """Only an exact model-bound count changes existing 09C dispatch eligibility."""
    from test_judge_packet_requests import built

    counter, _ = harness(tmp_path)
    prepared = prepare_request(
        built(),
        system_prompt="Invented fixture rubric",
        response_schema={},
        settings=settings(),
        count_tokens=counter,
        counter_model_digest=counter.model_digest,
    )
    assert prepared["diagnostics"]["input_tokens"] == 3
    assert prepared["diagnostics"]["dispatch_allowed"] is True


def test_network_failure_is_a_preflight_value_error_with_receipt(tmp_path: Path) -> None:
    """A counter connection failure remains a blocked input, never a fallback count."""

    def fail(path: str, payload: dict, calls: list) -> dict:
        """Model an unavailable already-running service without contacting a socket."""
        raise httpx.ConnectError("invented unavailable service")

    counter, _ = harness(tmp_path, mutate=fail)
    with pytest.raises(CounterIdentityError, match="unavailable service"):
        counter(request())
    assert counter.last_receipt is None
    assert len(list(tmp_path.glob("*/failure.json"))) == 1


@pytest.mark.parametrize("large", [False, True])
def test_complete_model_tuple_allowed_without_inference(tmp_path: Path, large: bool) -> None:
    """Finite identities admit setup only; no construction-time count or inference is assumed."""
    selected = (
        replace(
            config(),
            model=QWEN9B_MODEL_NAME,
            model_digest=QWEN9B_MODEL_DIGEST,
            model_blob_sha256=QWEN9B_MODEL_BLOB_SHA256,
        )
        if large
        else config()
    )
    counter = OllamaTokenCounter(selected, tmp_path)
    assert counter.model_digest == selected.model_digest
    native = request()
    native["model"] = selected.model
    counter._validate_request(native)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "alias_large,digest_large,blob_large",
    [
        (False, False, True),
        (False, True, False),
        (False, True, True),
        (True, False, False),
        (True, False, True),
        (True, True, False),
    ],
)
def test_cross_model_identity_combinations_fail_closed(
    tmp_path: Path, alias_large: bool, digest_large: bool, blob_large: bool
) -> None:
    """Individually known alias, manifest and blob hashes cannot be mixed across models."""
    selected = replace(
        config(),
        model=QWEN9B_MODEL_NAME if alias_large else MODEL_NAME,
        model_digest=QWEN9B_MODEL_DIGEST if digest_large else MODEL_DIGEST,
        model_blob_sha256=QWEN9B_MODEL_BLOB_SHA256 if blob_large else MODEL_BLOB_SHA256,
    )
    with pytest.raises(CounterIdentityError, match="qualified"):
        OllamaTokenCounter(selected, tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("field", ["runtime_version", "binary_sha256", "runner_sha256"])
def test_large_model_does_not_relax_runtime_identity(tmp_path: Path, field: str) -> None:
    """Adding the pinned 9B tuple leaves every runtime asset gate mandatory."""
    selected = replace(
        config(),
        model=QWEN9B_MODEL_NAME,
        model_digest=QWEN9B_MODEL_DIGEST,
        model_blob_sha256=QWEN9B_MODEL_BLOB_SHA256,
    )
    with pytest.raises(CounterIdentityError, match="qualified"):
        OllamaTokenCounter(replace(selected, **{field: "unqualified"}), tmp_path)
