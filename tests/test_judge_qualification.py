"""Exercise failure/restart and information boundaries without a live model."""

from pathlib import Path
from typing import Any

import pytest

from er_commons.judge_qualification import Judgment, messages, run


def inputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Make a fictitious saved answer and explicit local model configuration."""
    return [
        {
            "id": "short-g",
            "dimension": "grounding",
            "payload": {
                "question": "Is it supported?",
                "answer": {"conclusion": "Yes"},
                "evidence": [],
            },
        }
    ], {
        "model": "ollama/example:bf16",
        "identity": {"digest": "sha256:fixture", "runtime_version": "fixture-version"},
        "base_url": "http://127.0.0.1:11434/v1",
        "context": 32768,
        "max_tokens": 1500,
        "timeout": 300,
    }


def test_interruption_preserves_attempt_and_resume_verifies_success(tmp_path: Path) -> None:
    """An interrupted call remains immutable and only a completed success is reused."""
    packets, settings = inputs()

    def interrupt(request: dict[str, Any], directory: Path) -> dict[str, Any]:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run(packets, tmp_path, settings, interrupt)
    original = (tmp_path / "short-g/attempt-001/request.json").read_bytes()
    calls = []

    def success(request: dict[str, Any], directory: Path) -> dict[str, Any]:
        calls.append(request)
        return {"status": "success", "judgment": {"score": 2}}

    run(packets, tmp_path, settings, success)
    run(packets, tmp_path, settings, success)
    assert len(calls) == 1
    assert (tmp_path / "short-g/attempt-001/request.json").read_bytes() == original
    assert (tmp_path / "short-g/attempt-002/completion.json").exists()
    (tmp_path / "short-g/attempt-002/result.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        run(packets, tmp_path, settings, success)


def test_failure_does_not_retry_or_become_score(tmp_path: Path) -> None:
    """Timeout is retained once per invocation and never converted to a rubric value."""
    packets, settings = inputs()
    calls = []

    def timeout(request: dict[str, Any], directory: Path) -> dict[str, Any]:
        calls.append(request)
        raise TimeoutError("bounded timeout")

    results = run(packets, tmp_path, settings, timeout)
    assert len(calls) == 1
    assert results[0]["status"] == "transport_error"
    assert "judgment" not in results[0]
    run(packets, tmp_path, settings, timeout)
    assert len(calls) == 2
    assert (tmp_path / "short-g/attempt-002/completion.json").exists()
    exhausted = run(packets, tmp_path, settings, timeout)
    assert exhausted[0]["status"] == "transport_error"
    assert len(calls) == 2


def test_binding_rejects_model_change(tmp_path: Path) -> None:
    """Resume cannot silently change model or context settings."""
    packets, settings = inputs()
    run(packets, tmp_path, settings, lambda *_: {"status": "malformed", "raw": "oops"})
    settings["identity"]["digest"] = "changed"
    with pytest.raises(ValueError, match="Resume refused"):
        run(packets, tmp_path, settings)


def test_payload_boundary_and_strict_schema() -> None:
    """Outer selection labels never enter messages; extra ground-truth fields fail closed."""
    packets, _ = inputs()
    packet = packets[0]
    packet["synthetic_expectation"] = "MUST NOT APPEAR"
    assert "MUST NOT APPEAR" not in str(messages(packet))
    packet["payload"]["reference_answer"] = "secret"
    with pytest.raises(ValueError, match="payload keys"):
        messages(packet)
    for invalid in [
        '{"score":3}',
        '{"score":true,"rationale":"ok","evidence":[],"limitations":[]}',
        '{"score":"2","rationale":"ok","evidence":[],"limitations":[]}',
    ]:
        with pytest.raises(ValueError):
            Judgment.model_validate_json(invalid)


@pytest.mark.parametrize(
    "completion,status",
    [
        ('{"score":2,"rationale":"Supported","evidence":[],"limitations":[]}', "success"),
        ("not json", "malformed"),
        ("budget", "output_limit"),
        ("context", "context_limit"),
        ("missing_count", "context_evidence_missing"),
        ("version_drift", "identity_changed"),
        ("digest_drift", "identity_changed"),
        ("alias_context_drift", "identity_changed"),
        ("http400", "request_error"),
        ("timeout", "transport_error"),
        ("postflight_drift", "identity_changed"),
        ("loaded_context_drift", "identity_changed"),
        ("loaded_context_missing", "identity_changed"),
        ("trailing_slash", "success"),
        ("proxy_env", "success"),
    ],
)
def test_inspect_native_transport_receipts(
    tmp_path: Path,
    completion: str,
    status: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise actual Inspect scoring and native HTTP serialization against a fixture."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from er_commons.judge_qualification import inspect_transport

    received: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        """Serve a minimal local Ollama contract without loading any model."""

        def log_message(self, format: str, *args: Any) -> None:
            """Keep fixture request logging quiet."""

        def respond(self, value: dict[str, Any], status_code: int = 200) -> None:
            """Emit one complete JSON fixture response."""
            body = json.dumps(value).encode()
            self.send_response(status_code)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            """Resolve only the pinned fixture identity."""
            if self.path == "/api/version":
                self.respond({"version": "fixture-version"})
                return
            assert self.path in {"/api/tags", "/api/ps"}
            model_digest = (
                "changed-during-call"
                if completion == "postflight_drift" and received
                else "sha256:fixture"
            )
            self.respond(
                {
                    "models": [
                        {
                            "name": "example:bf16",
                            "digest": model_digest,
                            "runtime_version": "fixture-version",
                            "context_length": (
                                8192
                                if completion == "loaded_context_drift"
                                else None
                                if completion == "loaded_context_missing"
                                else 32768
                            ),
                        }
                    ]
                }
            )

        def do_POST(self) -> None:
            """Return identity details or the explicit model fixture output."""
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path == "/api/show":
                context = 8192 if completion == "alias_context_drift" else 32768
                self.respond({"parameters": f"num_ctx {context}"})
            else:
                assert self.path == "/api/chat"
                received.append(request)
                if completion == "http400":
                    self.respond({"error": "fixture prompt exceeds context"}, status_code=400)
                    return
                if completion == "timeout":
                    import time

                    time.sleep(2)
                    return
                self.respond(
                    {
                        "done": True,
                        "done_reason": "length" if completion == "budget" else "stop",
                        "prompt_eval_count": (
                            33000
                            if completion == "context"
                            else None
                            if completion == "missing_count"
                            else 10
                        ),
                        "message": {
                            "content": (
                                json.dumps(
                                    {
                                        "score": 2,
                                        "rationale": "Supported",
                                        "evidence": [],
                                        "limitations": [],
                                    }
                                )
                                if completion in {"trailing_slash", "proxy_env"}
                                else completion
                            )
                        },
                    }
                )

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        packets, settings = inputs()
        settings["base_url"] = f"http://127.0.0.1:{server.server_port}/v1"
        if completion == "trailing_slash":
            settings["base_url"] += "/"
        if completion == "proxy_env":
            for name in (
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
                "http_proxy",
                "https_proxy",
                "all_proxy",
            ):
                monkeypatch.setenv(name, "http://127.0.0.1:1")
            for name in ("NO_PROXY", "no_proxy"):
                monkeypatch.delenv(name, raising=False)
        if completion == "version_drift":
            settings["identity"]["runtime_version"] = "wrong"
        if completion == "digest_drift":
            settings["identity"]["digest"] = "wrong"
        if completion == "timeout":
            settings["timeout"] = 1
        results = run(packets, tmp_path, settings, inspect_transport)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert results[0]["status"] == status, results
    if completion in {"version_drift", "digest_drift", "alias_context_drift"}:
        assert not received
        assert "does not match" in results[0]["error"]
        return
    assert len(received) == 1
    assert received[0]["truncate"] is False
    assert received[0]["shift"] is False
    assert "tools" not in received[0]
    assert received[0]["options"]["num_ctx"] == 32768
    attempt = tmp_path / "short-g/attempt-001"
    if completion in {"http400", "timeout"}:
        assert results[0]["sample_errors"]
        assert "judgment" not in results[0]
    if completion == "timeout":
        assert "ReadTimeout" in str(results[0]["sample_errors"])
        assert not (attempt / "native_response.json").exists()
    else:
        assert (attempt / "native_response.json").exists()
    if completion == "http400":
        response = json.loads((attempt / "native_response.json").read_text())
        assert response["status_code"] == 400
        assert "fixture prompt exceeds context" in response["body"]
    assert list((attempt / "inspect").glob("*.eval"))
    if completion == "postflight_drift":
        assert "judgment" not in results[0]
        assert (attempt / "postflight_tags.json").exists()
        assert (attempt / "postflight_ps.json").exists()


@pytest.mark.parametrize("status", ["malformed", "output_limit", "context_limit"])
def test_nonretryable_failure(tmp_path: Path, status: str) -> None:
    """Never retry a semantic or budget failure under the same configuration."""
    packets, settings = inputs()
    run(packets, tmp_path, settings, lambda *_: {"status": status})

    def forbidden(*_: Any) -> dict[str, Any]:
        raise AssertionError("A permanent failure must not call the model again")

    result = run(packets, tmp_path, settings, forbidden)
    assert result[0]["status"] == status
    assert not (tmp_path / "short-g/attempt-002").exists()


@pytest.mark.parametrize("field", ["max_tokens", "context", "timeout"])
def test_unbounded_settings_rejected(tmp_path: Path, field: str) -> None:
    """Reject unlimited or nonsensical native generation budgets."""
    packets, settings = inputs()
    settings[field] = -1
    with pytest.raises(ValueError, match="positive integers"):
        run(packets, tmp_path, settings)


def test_adapter_snapshot_verified(tmp_path: Path) -> None:
    """Preserve reconstructable source and refuse modified source snapshots on resume."""
    packets, settings = inputs()
    run(packets, tmp_path, settings, lambda *_: {"status": "success"})
    snapshot = tmp_path / "adapter.py"
    assert "def inspect_transport(" in snapshot.read_text()
    snapshot.write_text("changed")
    with pytest.raises(ValueError, match="adapter snapshot"):
        run(packets, tmp_path, settings)


@pytest.mark.parametrize("packet_id", [[], {}, None, "../outside", ""])
def test_invalid_packet_ids_fail_before_artifacts(tmp_path: Path, packet_id: Any) -> None:
    """Malformed IDs get actionable validation, including unhashable JSON values."""
    packets, settings = inputs()
    packets[0]["id"] = packet_id
    with pytest.raises(ValueError, match="Packet IDs"):
        run(packets, tmp_path, settings)
    assert not list(tmp_path.iterdir())


def test_empty_run_rejected(tmp_path: Path) -> None:
    """A selection mistake cannot appear as an empty successful run."""
    _, settings = inputs()
    with pytest.raises(ValueError, match="At least one"):
        run([], tmp_path, settings)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("suffix", ["?redirect=remote", "#fragment"])
def test_endpoint_components_rejected(tmp_path: Path, suffix: str) -> None:
    """Only a plain local API endpoint is accepted before any provider call."""
    packets, settings = inputs()
    settings["base_url"] += suffix
    with pytest.raises(ValueError, match="query or fragment"):
        run(packets, tmp_path, settings)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("message", [None, [], {"content": None}, {"content": {"score": 2}}])
def test_malformed_message_is_not_a_transport_retry(message: Any) -> None:
    """A structurally invalid successful HTTP response is a permanent malformed result."""
    from er_commons.judge_qualification import validate_native_output

    _, settings = inputs()
    result = validate_native_output(
        {"done": True, "prompt_eval_count": 10, "message": message}, settings
    )
    assert result["status"] == "malformed"
    assert "judgment" not in result


def test_resume_continues_after_permanent_failure(tmp_path: Path) -> None:
    """A failed early packet must not prevent a later interrupted packet from resuming."""
    import copy

    packets, settings = inputs()
    packets.append(copy.deepcopy(packets[0]))
    packets[1]["id"] = "later-g"
    calls = 0

    def first_pass(request: dict[str, Any], directory: Path) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"status": "output_limit"}
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run(packets, tmp_path, settings, first_pass)
    resumed_calls = []

    def resumed(request: dict[str, Any], directory: Path) -> dict[str, Any]:
        resumed_calls.append(directory.parent.name)
        return {"status": "success", "judgment": {"score": 2}}

    results = run(packets, tmp_path, settings, resumed)
    assert [result["status"] for result in results] == ["output_limit", "success"]
    assert resumed_calls == ["later-g"]


def test_two_interruptions_exhaust_retry_without_stopping_batch(tmp_path: Path) -> None:
    """Preserve incomplete evidence and return an explicit failure once retries are spent."""
    packets, settings = inputs()

    def interrupt(*_: Any) -> dict[str, Any]:
        raise KeyboardInterrupt

    for _ in range(2):
        with pytest.raises(KeyboardInterrupt):
            run(packets, tmp_path, settings, interrupt)
    result = run(packets, tmp_path, settings, interrupt)
    assert result[0]["status"] == "retry_exhausted"
    assert result[0]["packet_id"] == "short-g"
    assert len(list((tmp_path / "short-g").glob("attempt-*"))) == 2


def test_programming_errors_surface_without_transport_classification(tmp_path: Path) -> None:
    """A bug in a transport adapter must be debuggable, not reported as provider downtime."""
    packets, settings = inputs()

    def broken(*_: Any) -> dict[str, Any]:
        raise TypeError("fixture programming bug")

    with pytest.raises(TypeError, match="programming bug"):
        run(packets, tmp_path, settings, broken)
    assert not (tmp_path / "short-g/attempt-001/completion.json").exists()
