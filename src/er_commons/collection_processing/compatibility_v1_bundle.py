"""Project v2 workflow evidence into the immutable v1.1 validation contract."""

from __future__ import annotations

from copy import deepcopy

from er_commons.corpus_extraction_contract_v1_1.model import JsonObject


def as_v1_validation_view(bundle: JsonObject) -> JsonObject:
    """Return a detached view expected by the legacy semantic validator."""
    value = deepcopy(bundle)
    value["schema_version"] = "er_commons.corpus_extraction_contract_fixture.v1_1"
    value["fixture_scope"] = value.pop("collection_scope")
    accounting = value["accounting"]
    accounting["record_type"] = "scope_accounting"
    accounting["schema_version"] = "er_commons.scope_accounting.v1_1"
    index = value["target_index"]
    index["record_type"] = "target_index_completion"
    index["schema_version"] = "er_commons.target_index_completion.v1_1"
    index["identity_preimage"]["schema_version"] = "er_commons.corpus_target_index_identity.v1_1"
    index["identity_preimage"]["ordering_policy_version"] = "corpus_target_order_v1"
    links = value["resolution_completion"]
    links["record_type"] = "resolution_completion"
    links["schema_version"] = "er_commons.resolution_completion.v1_1"
    links["identity_preimage"]["schema_version"] = "er_commons.corpus_resolution_identity.v1_1"
    manifest = links["mention_input_manifest"]
    manifest["schema_version"] = "er_commons.corpus_mention_input_manifest.v1_1"
    manifest["corpus_catalog_ref"] = manifest.pop("source_family_catalog_ref")
    handoff = value["handoff"]
    handoff["record_type"] = "candidate_handoff"
    handoff["schema_version"] = "er_commons.candidate_handoff.v1_1"
    handoff["identity_preimage"]["schema_version"] = "er_commons.candidate_handoff_identity.v1_1"
    stage_attempts = value.pop("collection_stage_attempts")
    for attempt in stage_attempts:
        attempt["schema_version"] = "er_commons.corpus_stage_attempt.v1"
    value["corpus_stage_attempts"] = stage_attempts
    for replay in value["downstream_replays"]:
        replay["replacement_cross_reference_completion_ref"] = replay.pop(
            "replacement_linked_document_completion_ref"
        )
    return value


__all__ = ["as_v1_validation_view"]
