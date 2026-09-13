"""Closed identity preimages for versioned record-target indexes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from er_commons.collection_processing.contract import (
    JsonObject,
    canonical_sha256,
    collection_identity_fields,
)
from er_commons.collection_processing.storage import bytes_ref, inventory_ref

if TYPE_CHECKING:
    from er_commons.collection_processing.record_target_indexing import RecordTargetIndexInputs


def build_index_preimage(
    inputs: RecordTargetIndexInputs,
    eligible: list[JsonObject],
    payloads: dict[str, bytes],
    entry_count: int,
    document_target_count: int,
) -> JsonObject:
    return {
        "schema_version": (
            "er_commons.record_target_index_identity.v3"
            if inputs.collection_production_id is not None
            else "er_commons.record_target_index_identity.v2"
        ),
        **collection_identity_fields(
            inputs.production_extraction_id,
            inputs.collection_production_id,
            inputs.imported_selection_sha256,
        ),
        "scope_id": inputs.scope_id,
        "accounting_sha256": inputs.accounting_stage.completion_ref["sha256"],
        "eligible_candidates_sha256": canonical_sha256(eligible),
        "unavailable_sources_sha256": bytes_ref("unused", payloads["unavailable_sources.jsonl"])[
            "sha256"
        ],
        "entries_sha256": bytes_ref("unused", payloads["target_index.jsonl"])["sha256"],
        "entry_count": entry_count,
        "document_targets_sha256": bytes_ref("unused", payloads["document_targets.jsonl"])[
            "sha256"
        ],
        "document_target_count": document_target_count,
        "ordering_policy_version": inputs.ordering_policy_version,
        "target_policy_sha256": inputs.target_policy_sha256,
        "managed_inventory_sha256": inventory_ref("unused", payloads)["sha256"],
    }
