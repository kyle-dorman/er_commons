"""Named failures for the restartable extraction contract."""


class CorpusExtractionContractError(ValueError):
    """A cross-record corpus extraction invariant failed."""

    def __init__(self, code: str, detail: str, *, subject: str | None = None) -> None:
        message = f"{code}: {detail}"
        if subject is not None:
            message += f" [{subject}]"
        super().__init__(message)
        self.code = code
        self.detail = detail
        self.subject = subject
