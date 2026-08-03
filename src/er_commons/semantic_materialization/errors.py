"""Actionable failures for the Task 03E.4 application boundary."""

from __future__ import annotations


class SemanticMaterializationInvariantError(ValueError):
    """Name a failed construction invariant with its observed evidence."""

    def __init__(
        self,
        *,
        stage: str,
        invariant: str,
        expected: object,
        observed: object,
        subject: str,
    ) -> None:
        self.stage = stage
        self.invariant = invariant
        self.expected = expected
        self.observed = observed
        self.subject = subject
        super().__init__(
            f"{stage}: {invariant} for {subject}; expected {expected!r}, observed {observed!r}"
        )
