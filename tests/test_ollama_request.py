"""Protect offline local preflight and immutable token-count receipts."""

import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.ollama_request import native_request, validate_settings, write_new


def settings() -> dict[str, Any]:
    """Supply a fictitious pinned local identity and bounded context."""
    return {
        "model": "ollama/example:bf16",
        "identity": {"digest": "sha256:fixture", "runtime_version": "fixture-version"},
        "base_url": "http://127.0.0.1:11434/v1",
        "context": 49152,
        "max_tokens": 1500,
        "timeout": 300,
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://127.0.0.1/v1",
        "http://example.com/v1",
        "http://user@localhost/v1",
        "http://localhost/v1?key=secret",
    ],
)
def test_preflight_rejects_nonlocal_or_credentialed_endpoints(endpoint: str) -> None:
    """Offline packet qualification cannot silently change the locality boundary."""
    config = settings()
    config["base_url"] = endpoint
    with pytest.raises(ValueError):
        validate_settings(config)


def test_preflight_requires_identity_and_output_reserve() -> None:
    """Unknown model identity and impossible output budgets fail before counting."""
    config = settings()
    validate_settings(config)
    config["max_tokens"] = config["context"]
    with pytest.raises(ValueError, match="budget"):
        validate_settings(config)
    config = settings()
    config["identity"] = {}
    with pytest.raises(ValueError, match="Pinned"):
        validate_settings(config)


def test_render_keeps_schema_and_disables_truncation() -> None:
    """Count the full schema and payload rather than a truncated approximation."""
    schema = {"type": "object", "properties": {"supported": {"type": "boolean"}}}
    messages = [{"role": "user", "content": "evidence"}]
    rendered = native_request({"settings": settings(), "schema": schema, "messages": messages})
    assert rendered["format"] == schema
    assert rendered["messages"] == messages
    assert rendered["truncate"] is False and rendered["shift"] is False
    assert rendered["options"]["num_ctx"] == 49152
    assert rendered["options"]["num_predict"] == 1500


def test_token_receipts_cannot_be_overwritten(tmp_path: Path) -> None:
    """A second observation must never replace previously recorded evidence."""
    path = tmp_path / "receipt.json"
    write_new(path, {"count": 7})
    with pytest.raises(FileExistsError):
        write_new(path, {"count": 8})
    assert json.loads(path.read_text()) == {"count": 7}
