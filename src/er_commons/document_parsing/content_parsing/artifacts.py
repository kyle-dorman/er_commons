"""Serialize Docling error records for the maintained conversion path."""

from __future__ import annotations

from typing import Any


def result_errors(result: Any) -> list[dict[str, Any]]:
    """Serialize Docling conversion errors without losing structured fields."""
    return [
        error.model_dump(mode="json") if hasattr(error, "model_dump") else {"message": str(error)}
        for error in result.errors
    ]
