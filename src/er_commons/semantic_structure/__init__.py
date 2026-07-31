"""Executable Task 03E.3 semantic-structure contract."""

from er_commons.semantic_structure.errors import SemanticContractError
from er_commons.semantic_structure.handoff import verify_task03e2d_control
from er_commons.semantic_structure.normalization import normalize_alias
from er_commons.semantic_structure.policies.bridge import BridgeSourceEvidence
from er_commons.semantic_structure.validation import validate_semantic_contract

__all__ = [
    "BridgeSourceEvidence",
    "SemanticContractError",
    "normalize_alias",
    "validate_semantic_contract",
    "verify_task03e2d_control",
]
