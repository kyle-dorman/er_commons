"""Offline Ollama request rendering for exact token preflight; never dispatch inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def encoded(value: Any) -> bytes:
    """Serialize consistently for exact request and resumption bindings."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def write_new(path: Path, value: Any) -> None:
    """Create a JSON receipt without ever overwriting previous evidence."""
    with path.open("xb") as stream:
        stream.write(encoded(value))


def validate_settings(settings: dict[str, Any]) -> None:
    """Require explicit local operation and bounded, reproducible settings."""
    endpoint = urlparse(settings["base_url"])
    if endpoint.scheme != "http" or endpoint.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Ollama preflight only permits an explicit loopback HTTP endpoint")
    if (
        endpoint.path.rstrip("/") != "/v1"
        or endpoint.username
        or endpoint.password
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError(
            "Expected local Ollama /v1 endpoint without credentials, query or fragment"
        )
    if not settings["model"].startswith("ollama/"):
        raise ValueError("Only the agreed Ollama provider is permitted")
    if not settings["identity"].get("digest") or not settings["identity"].get("runtime_version"):
        raise ValueError("Pinned model digest and runtime_version are required")
    if any(
        type(settings[key]) is not int or settings[key] <= 0
        for key in ("context", "max_tokens", "timeout")
    ):
        raise ValueError("Budgets must be positive integers")
    if settings["context"] <= settings["max_tokens"]:
        raise ValueError("Invalid context/output/timeout budget")


def native_request(request: dict[str, Any]) -> dict[str, Any]:
    """Render the historical packet format for exact offline token counting only."""
    settings = request["settings"]
    model = settings["model"].removeprefix("ollama/")
    return {
        "model": model,
        "messages": request["messages"],
        "format": request["schema"],
        "think": False,
        "stream": False,
        "truncate": False,
        "shift": False,
        "keep_alive": "5m",
        "options": {
            "num_ctx": settings["context"],
            "num_predict": settings["max_tokens"],
            "temperature": 0,
            "seed": 42,
        },
    }
