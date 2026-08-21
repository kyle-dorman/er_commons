"""Structured failures for restartable chunk-conversion workflows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ChunkedConversionError(RuntimeError):
    """Name the failed invariant and the artifact or operation that owns it."""

    def __init__(
        self,
        code: str,
        *,
        stage: str,
        path: str,
        expected: object | None = None,
        actual: object | None = None,
        context: Mapping[str, object] | None = None,
    ) -> None:
        self.code = code
        self.stage = stage
        self.path = path
        self.expected = expected
        self.actual = actual
        self.context = dict(context or {})
        super().__init__(self._message())

    def _message(self) -> str:
        detail = f"chunk conversion failed [{self.code}] stage={self.stage} path={self.path}"
        if self.expected is not None or self.actual is not None:
            detail += f" expected={self.expected!r} actual={self.actual!r}"
        if self.context:
            detail += f" context={self.context!r}"
        return detail

    def as_record(self) -> dict[str, Any]:
        """Return the stable diagnostic fields written into retained failures."""
        return {
            "error_type": type(self).__name__,
            "code": self.code,
            "stage": self.stage,
            "path": self.path,
            "expected": self.expected,
            "actual": self.actual,
            "context": self.context,
            "message": str(self),
        }


def require(
    condition: bool,
    code: str,
    *,
    stage: str,
    path: str,
    expected: object | None = None,
    actual: object | None = None,
    context: Mapping[str, object] | None = None,
) -> None:
    """Raise one contextual chunk-conversion error when an invariant is false."""
    if not condition:
        raise ChunkedConversionError(
            code,
            stage=stage,
            path=path,
            expected=expected,
            actual=actual,
            context=context,
        )
