"""Build and validate sections, page labels, aliases, and structure evidence."""

from er_commons.document_records.document_structure.config import (
    DocumentStructureConfig,
    load_document_structure_config,
)
from er_commons.document_records.document_structure.errors import StructureContractError
from er_commons.document_records.document_structure.handoff import verify_bounded_hierarchy_control
from er_commons.document_records.document_structure.identity import (
    build_document_structure_identity,
    normalized_bridge_preimage_sha256,
)
from er_commons.document_records.document_structure.inputs import (
    DocumentStructureInputs,
    load_document_structure_inputs,
)
from er_commons.document_records.document_structure.normalization import normalize_alias
from er_commons.document_records.document_structure.policies.bridge import (
    BridgeSourceEvidence,
)
from er_commons.document_records.document_structure.validation import (
    validate_document_structure_contract,
)
from er_commons.document_records.document_structure.workflow import map_document_structure

__all__ = [
    "BridgeSourceEvidence",
    "StructureContractError",
    "DocumentStructureConfig",
    "DocumentStructureInputs",
    "build_document_structure_identity",
    "load_document_structure_config",
    "load_document_structure_inputs",
    "map_document_structure",
    "normalize_alias",
    "normalized_bridge_preimage_sha256",
    "validate_document_structure_contract",
    "verify_bounded_hierarchy_control",
]
