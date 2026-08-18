"""Errors raised while mapping and validating document structure."""

from __future__ import annotations


class StructureContractError(ValueError):
    """A schema-valid semantic bundle violates a cross-record policy."""


class DocumentStructureInvariantError(ValueError):
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
