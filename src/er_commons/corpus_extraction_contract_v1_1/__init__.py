"""Public validation boundary for restartable corpus extraction contract v1.1."""

from er_commons.corpus_extraction_contract_v1_1.checks import verify_ref
from er_commons.corpus_extraction_contract_v1_1.fixture_validation import (
    validate_fixture_directory,
)
from er_commons.corpus_extraction_contract_v1_1.identity import (
    HANDOFF_PREIMAGE_FIELDS,
    INDEX_PREIMAGE_FIELDS,
    RESOLUTION_PREIMAGE_FIELDS,
    build_handoff_id,
    build_index_id,
    build_resolution_id,
    validate_handoff_id,
    validate_index_id,
    validate_production_identity,
    validate_resolution_id,
)
from er_commons.corpus_extraction_contract_v1_1.model import (
    ArtifactReader,
    DerivedIdentity,
    JsonObject,
)
from er_commons.corpus_extraction_contract_v1_1.validation import validate_contract_bundle

__all__ = [
    "HANDOFF_PREIMAGE_FIELDS",
    "INDEX_PREIMAGE_FIELDS",
    "RESOLUTION_PREIMAGE_FIELDS",
    "ArtifactReader",
    "DerivedIdentity",
    "JsonObject",
    "build_handoff_id",
    "build_index_id",
    "build_resolution_id",
    "validate_handoff_id",
    "validate_index_id",
    "validate_production_identity",
    "validate_resolution_id",
    "validate_contract_bundle",
    "validate_fixture_directory",
    "verify_ref",
]
