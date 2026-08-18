"""Mechanical ready-or-blocked handoff derivation."""

from __future__ import annotations

from dataclasses import dataclass

from er_commons.collection_processing.contract import (
    JsonObject,
    build_collection_handoff_id,
    canonical_sha256,
    unavailable_source_digest,
)
from er_commons.collection_processing.domain import PublishedStage, StageBuild, StageName
from er_commons.collection_processing.storage import bytes_ref, inventory_ref, json_bytes


@dataclass(frozen=True)
class HandoffAssemblyInputs:
    """Exact prerequisites and policy for one candidate handoff."""

    production_extraction_id: str
    scope_id: str
    accounting: JsonObject
    accounting_stage: PublishedStage
    index: JsonObject
    index_stage: PublishedStage
    resolution: JsonObject
    resolution_stage: PublishedStage
    blocking_policy: str


class HandoffAssembler:
    """Derive handoff status entirely from verified prerequisite evidence."""

    def build(self, inputs: HandoffAssemblyInputs) -> StageBuild:
        """Return deterministic handoff evidence without making Task 04 claims."""
        reasons = self._blocking_reasons(inputs)
        status = "blocked" if reasons else "ready"
        policy_bytes = json_bytes(inputs.blocking_policy)
        semantic_payloads = {"blocking_policy.json": policy_bytes}
        preimage = self._preimage(inputs, reasons, status, policy_bytes, semantic_payloads)
        handoff_id = build_collection_handoff_id(preimage)
        final_relative = f"scopes/{inputs.scope_id}/handoffs/{handoff_id}"
        payloads = {
            **semantic_payloads,
            "records/identity_preimage.json": json_bytes(preimage),
        }
        completion: JsonObject = {
            "record_type": "collection_handoff",
            "schema_version": "er_commons.collection_handoff.v2",
            "handoff_id": handoff_id,
            "scope_id": inputs.scope_id,
            "index_id": inputs.index["index_id"],
            "resolution_id": inputs.resolution["resolution_id"],
            "identity_preimage": preimage,
            "identity_preimage_ref": bytes_ref(
                f"{final_relative}/records/identity_preimage.json",
                payloads["records/identity_preimage.json"],
            ),
            "accounting_completion_ref": inputs.accounting_stage.completion_ref,
            "index_completion_ref": inputs.index_stage.completion_ref,
            "resolution_completion_ref": inputs.resolution_stage.completion_ref,
            "blocking_policy": inputs.blocking_policy,
            "blocking_policy_ref": bytes_ref(
                f"{final_relative}/blocking_policy.json", policy_bytes
            ),
            "blocking_reasons": reasons,
            "status": status,
            "task04_status": "not_evaluated",
            "artifact_inventory": inventory_ref(final_relative, payloads),
            "completion_last": True,
        }
        return StageBuild(StageName.HANDOFF, handoff_id, payloads, completion)

    @staticmethod
    def _blocking_reasons(inputs: HandoffAssemblyInputs) -> list[JsonObject]:
        if inputs.blocking_policy == "terminal_failures_allowed":
            return []
        unavailable = {
            row["source"]["source_id"]: row for row in inputs.index["unavailable_sources"]
        }
        return [
            {
                "code": "terminal_source_failure",
                "source_id": row["source_id"],
                "transaction_id": row["transaction_id"],
                "unavailable_source_sha256": unavailable_source_digest(
                    unavailable[row["source_id"]]
                ),
            }
            for row in inputs.accounting["rows"]
            if row["terminal_state"] == "failed_terminal"
        ]

    @staticmethod
    def _preimage(
        inputs: HandoffAssemblyInputs,
        reasons: list[JsonObject],
        status: str,
        policy_bytes: bytes,
        payloads: dict[str, bytes],
    ) -> JsonObject:
        return {
            "schema_version": "er_commons.collection_handoff_identity.v2",
            "production_extraction_id": inputs.production_extraction_id,
            "scope_id": inputs.scope_id,
            "accounting_completion_sha256": inputs.accounting_stage.completion_ref["sha256"],
            "index_completion_sha256": inputs.index_stage.completion_ref["sha256"],
            "resolution_completion_sha256": inputs.resolution_stage.completion_ref["sha256"],
            "blocking_policy_sha256": bytes_ref("unused", policy_bytes)["sha256"],
            "status": status,
            "blocking_reasons_sha256": canonical_sha256(reasons),
            "task04_status": "not_evaluated",
            "managed_inventory_sha256": inventory_ref("unused", payloads)["sha256"],
        }
