"""Errors raised when heading evidence violates the accepted v1 contract."""


class HierarchyInferenceContractError(ValueError):
    """Legacy v1 evidence violates a parsing or cross-record invariant."""
