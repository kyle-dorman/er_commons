"""Path-rich JSON readers at the Task 04 untyped artifact boundary."""

from __future__ import annotations

import json
from pathlib import Path

from er_commons.human_review_support.task04.models import JsonValue


def read_json_object(path: Path) -> dict[str, JsonValue]:
    """Read one JSON object and include its path in every parse failure."""
    try:
        value: JsonValue = json.loads(path.read_text())
    except OSError as error:
        raise ValueError(f"cannot read JSON file {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid JSON in {path}:{error.lineno}:{error.colno}: {error.msg}"
        ) from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object at {path}, found {type(value).__name__}")
    return value


def read_jsonl_objects(path: Path) -> list[dict[str, JsonValue]]:
    """Read one bounded JSONL artifact with exact line diagnostics."""
    rows: list[dict[str, JsonValue]] = []
    try:
        stream = path.open(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot open JSONL file {path}: {error}") from error
    with stream:
        for number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                value: JsonValue = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON in {path}:{number}: {error.msg}") from error
            if not isinstance(value, dict):
                raise ValueError(
                    f"expected a JSON object at {path}:{number}, found {type(value).__name__}"
                )
            rows.append(value)
    return rows


def require_mapping(value: object, *, path: str) -> dict[str, JsonValue]:
    """Narrow an untyped JSON value to an object with a logical path."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"expected object at {path}")
    return value


def require_list(value: object, *, path: str) -> list[JsonValue]:
    """Narrow an untyped JSON value to a list with a logical path."""
    if not isinstance(value, list):
        raise ValueError(f"expected array at {path}")
    return value


def require_string(value: object, *, path: str) -> str:
    """Narrow a required JSON value to a non-empty string."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"expected non-empty string at {path}")
    return value


def optional_string(value: object, *, path: str) -> str | None:
    """Narrow an optional JSON value to a string or null."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"expected string or null at {path}")
    return value


def require_integer(value: object, *, path: str, minimum: int = 0) -> int:
    """Narrow a required JSON number to a bounded integer."""
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"expected integer >= {minimum} at {path}")
    return value


__all__ = [
    "optional_string",
    "read_json_object",
    "read_jsonl_objects",
    "require_integer",
    "require_list",
    "require_mapping",
    "require_string",
]
