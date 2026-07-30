"""Errors raised when hierarchy-correction records violate project policy."""


class HierarchyCorrectionContractError(ValueError):
    """A schema-valid correction bundle violates a cross-record invariant."""
