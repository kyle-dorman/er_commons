"""Native Ollama completion and retry policy shared by local judge adapters."""

from __future__ import annotations

from typing import Any

import httpx


def is_transient_error(error: Exception) -> bool:
    """Retry only transient network or rate/server failures, never schema outcomes."""
    return isinstance(error, (httpx.TimeoutException, httpx.NetworkError)) or (
        isinstance(error, httpx.HTTPStatusError)
        and (error.response.status_code in {408, 429} or error.response.status_code >= 500)
    )


def validate_completion(output: Any, settings: dict[str, Any]) -> dict[str, Any]:
    """Validate native completion mechanics independently of the semantic schema."""
    if not isinstance(output, dict):
        return {"status": "malformed", "error": "Native completion must be an object"}
    if output.get("done") is not True or output.get("done_reason") == "length":
        return {"status": "output_limit", "error": "Incomplete or length-limited result"}
    count = output.get("prompt_eval_count")
    if type(count) is not int or count <= 0:
        return {"status": "context_evidence_missing", "error": "Missing prompt token count"}
    if count + settings["max_tokens"] > settings["context"]:
        return {"status": "context_limit", "error": "Native context exceeded"}
    message = output.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return {"status": "schema_error", "error": "Missing message.content string"}
    return {"status": "complete", "raw_judgment": message["content"]}
