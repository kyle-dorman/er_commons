"""Public validation facade for the canonical cross-reference contract."""

from er_commons.cross_reference_contract.errors import CrossReferenceContractError
from er_commons.cross_reference_contract.validation import validate_cross_reference_contract

__all__ = ["CrossReferenceContractError", "validate_cross_reference_contract"]
