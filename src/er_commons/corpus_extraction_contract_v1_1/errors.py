"""Stable contextual failures for the maintained corpus contract."""

from __future__ import annotations


class CorpusExtractionContractError(ValueError):
    """One machine-stable contract failure with an optional subject."""

    def __init__(self, code: str, detail: str, *, subject: str | None = None) -> None:
        self.code = code
        self.detail = detail
        self.subject = subject
        message = f"{code}: {detail}"
        if subject is not None:
            message = f"{message} [{subject}]"
        super().__init__(message)
