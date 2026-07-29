"""Errors raised when canonical extraction records violate project policy."""


class ContractError(ValueError):
    """A schema-valid extraction bundle violates a cross-record invariant."""
