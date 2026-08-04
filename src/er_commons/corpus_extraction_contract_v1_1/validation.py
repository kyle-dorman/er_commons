"""Human-readable façade for executable corpus contract v1.1 validation."""

from __future__ import annotations

from er_commons.corpus_extraction_contract_v1_1.accounting import validate_scope_accounting
from er_commons.corpus_extraction_contract_v1_1.handoff import validate_candidate_handoff
from er_commons.corpus_extraction_contract_v1_1.indexing import validate_target_index
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject
from er_commons.corpus_extraction_contract_v1_1.publication import validate_stage_attempts
from er_commons.corpus_extraction_contract_v1_1.resolution import (
    validate_resolution_completion,
)


def validate_contract_bundle(bundle: JsonObject, reader: ArtifactReader) -> None:
    """Sequence independently owned cross-record and exact-byte policies."""
    scope = validate_scope_accounting(bundle, reader)
    targets = validate_target_index(bundle, scope, reader)
    validate_resolution_completion(bundle, scope, targets, reader)
    validate_candidate_handoff(bundle, scope, reader)
    validate_stage_attempts(bundle, reader)
