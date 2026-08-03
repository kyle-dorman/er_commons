"""Errors raised by the Task 03E.5 materializer."""


class CrossReferenceMaterializationError(RuntimeError):
    """Report a failed cross-reference invariant without hiding its stage."""
