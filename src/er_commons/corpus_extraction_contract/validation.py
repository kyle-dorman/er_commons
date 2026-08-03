"""Human-readable façade for cross-record corpus contract validation."""

from __future__ import annotations

from er_commons.corpus_extraction_contract.accounting import validate_scope_accounting
from er_commons.corpus_extraction_contract.indexing import validate_target_index
from er_commons.corpus_extraction_contract.lifecycle import validate_document_lifecycle
from er_commons.corpus_extraction_contract.model import JsonObject
from er_commons.corpus_extraction_contract.resolution import (
    validate_candidate_handoff,
    validate_resolution_completion,
)


def validate_contract_bundle(bundle: JsonObject) -> None:
    """Validate cross-record invariants after JSON Schema validates record shapes."""
    lifecycle = validate_document_lifecycle(bundle)
    scope = validate_scope_accounting(bundle, lifecycle)
    index = validate_target_index(bundle["target_index"], bundle["accounting"], scope)
    validate_resolution_completion(
        bundle["resolution_completion"],
        bundle["target_index"],
        scope,
        index,
    )
    validate_candidate_handoff(bundle)
