"""Errors raised when canonical extraction records violate project policy."""


class MappingContractError(ValueError):
    """A schema-valid extraction bundle violates a cross-record invariant."""
