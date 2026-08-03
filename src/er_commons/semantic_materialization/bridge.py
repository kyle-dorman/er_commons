"""Construct the candidate-owned bridge from independently verified evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from er_commons.semantic_structure import BridgeSourceEvidence, SemanticContractError
from er_commons.semantic_structure.constants import PERMITTED_BRIDGE_DISPOSITIONS


@dataclass(frozen=True)
class BridgeItem:
    """One stable producer correspondence before canonical targets are attached."""

    stable_item_key: str
    hierarchy_raw_pointer: str
    baseline_raw_pointer: str


def build_cross_producer_bridge(
    items: list[BridgeItem],
    *,
    hierarchy_producer_run_id: str,
    baseline_producer_run_id: str,
    canonical_block_by_key: dict[str, str],
    disposition_by_key: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, BridgeSourceEvidence]]:
    """Build bridge rows and the separately supplied validation evidence index.

    Every producer item must either map one-to-one to a retained canonical block
    or carry one of the two accepted replacement dispositions. Input order is
    preserved because it is the verified hierarchy-producer reading order.
    """
    keys = [item.stable_item_key for item in items]
    if len(keys) != len(set(keys)):
        raise SemanticContractError("bridge source contains duplicate stable-item keys")
    if set(canonical_block_by_key) & set(disposition_by_key):
        raise SemanticContractError("bridge item cannot be both mapped and replaced")
    supplied = set(canonical_block_by_key) | set(disposition_by_key)
    if supplied != set(keys):
        raise SemanticContractError(
            "bridge construction coverage differs: "
            f"missing={sorted(set(keys) - supplied)}, extra={sorted(supplied - set(keys))}"
        )

    rows: list[dict[str, Any]] = []
    evidence: dict[str, BridgeSourceEvidence] = {}
    for item in items:
        key = item.stable_item_key
        disposition = disposition_by_key.get(key)
        if disposition is not None and disposition not in PERMITTED_BRIDGE_DISPOSITIONS:
            raise SemanticContractError(f"bridge disposition is not permitted: {key}")
        canonical_ids = [] if disposition else [canonical_block_by_key[key]]
        rows.append(
            {
                "stable_item_key": key,
                "hierarchy_producer_run_id": hierarchy_producer_run_id,
                "hierarchy_raw_pointer": item.hierarchy_raw_pointer,
                "baseline_producer_run_id": baseline_producer_run_id,
                "baseline_raw_pointer": item.baseline_raw_pointer,
                "status": "permitted_unmapped" if disposition else "mapped",
                "canonical_record_ids": canonical_ids,
                "disposition": disposition,
            }
        )
        evidence[key] = BridgeSourceEvidence(
            hierarchy_raw_pointer=item.hierarchy_raw_pointer,
            baseline_raw_pointer=item.baseline_raw_pointer,
            disposition=disposition,
        )
    return rows, evidence
