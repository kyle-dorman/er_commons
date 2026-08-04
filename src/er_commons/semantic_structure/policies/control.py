"""Structural policy for checksum-bound hierarchy control references."""

from __future__ import annotations

import re
from typing import Any

from er_commons.semantic_structure.constants import SEMANTIC_COUNT_FIELDS
from er_commons.semantic_structure.errors import SemanticContractError

_CANDIDATE_ID = re.compile(r"^hcorv1-[0-9a-f]{64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_control_provenance(control: dict[str, Any]) -> None:
    """Validate control shape while leaving candidate values to verified evidence."""
    if control.get("control_kind") == "strict_quality_gate":
        _validate_strict_control(control)
        return
    required = {
        "candidate_id",
        "completion_status",
        "artifact_inventory_sha256",
        "semantic_file_set_sha256",
        "aggregate_semantic_sha256",
        "bounded_acceptance_sha256",
        "authorization_id",
        "acceptance_status",
        "source_id",
        "physical_page_count",
        "corpus_wide_acceptance",
        "authorized_uses",
        "limitations",
        "semantic_counts",
        "producer_comparison_sha256",
    }
    if set(control) != required:
        raise SemanticContractError("bounded hierarchy control field set differs")
    if not isinstance(control["candidate_id"], str) or not _CANDIDATE_ID.fullmatch(
        control["candidate_id"]
    ):
        raise SemanticContractError("bounded hierarchy candidate ID is invalid")
    for field in (
        "artifact_inventory_sha256",
        "semantic_file_set_sha256",
        "aggregate_semantic_sha256",
        "bounded_acceptance_sha256",
        "producer_comparison_sha256",
    ):
        value = control[field]
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise SemanticContractError(f"bounded hierarchy {field} is invalid")
    if control["completion_status"] not in {"complete", "complete_with_ambiguities"}:
        raise SemanticContractError("bounded hierarchy completion status is invalid")
    if control["acceptance_status"] != "accepted_with_known_limitations":
        raise SemanticContractError("bounded hierarchy acceptance status differs")
    if control["corpus_wide_acceptance"] is not False:
        raise SemanticContractError("bounded document control cannot claim corpus acceptance")
    if not isinstance(control["physical_page_count"], int) or control["physical_page_count"] < 1:
        raise SemanticContractError("bounded hierarchy page count is invalid")
    for field in ("authorization_id", "source_id"):
        if not isinstance(control[field], str) or not control[field]:
            raise SemanticContractError(f"bounded hierarchy {field} is invalid")
    for field in ("authorized_uses", "limitations"):
        value = control[field]
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item for item in value)
        ):
            raise SemanticContractError(f"bounded hierarchy {field} is invalid")
    counts = control["semantic_counts"]
    if not isinstance(counts, dict) or set(counts) != SEMANTIC_COUNT_FIELDS:
        raise SemanticContractError("bounded hierarchy semantic count fields differ")
    if not all(isinstance(value, int) and value >= 0 for value in counts.values()):
        raise SemanticContractError("bounded hierarchy semantic counts are invalid")


def _validate_strict_control(control: dict[str, Any]) -> None:
    required = {
        "control_kind",
        "candidate_id",
        "completion_status",
        "artifact_inventory_sha256",
        "quality_gate_completion_sha256",
        "source_id",
        "physical_page_count",
        "corpus_wide_acceptance",
    }
    if set(control) != required:
        raise SemanticContractError("strict hierarchy control field set differs")
    if control["corpus_wide_acceptance"] is not False:
        raise SemanticContractError("strict document control cannot claim corpus acceptance")
