"""Errors raised by the schema-v3 cross-reference contract."""


class CrossReferenceContractError(ValueError):
    """Raised when a v3 bundle violates a cross-record contract invariant."""
