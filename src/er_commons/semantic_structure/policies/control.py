"""Policy for the compact, checksum-bound Task 03E.2d control reference."""

from __future__ import annotations

from typing import Any

from er_commons.semantic_structure.constants import (
    EXPECTED_AUTHORIZED_USES,
    EXPECTED_CONTROL_FIELDS,
    EXPECTED_LIMITATIONS,
    EXPECTED_SEMANTIC_COUNTS,
)
from er_commons.semantic_structure.errors import SemanticContractError


def validate_control_provenance(control: dict[str, Any]) -> None:
    """Fail closed if the accepted hierarchy or its authorization changed."""
    if control.get("control_kind") == "strict_quality_gate":
        required = {
            "candidate_id",
            "completion_status",
            "artifact_inventory_sha256",
            "quality_gate_completion_sha256",
            "source_id",
            "physical_page_count",
            "corpus_wide_acceptance",
        }
        if set(control) != required | {"control_kind"}:
            raise SemanticContractError("strict hierarchy control field set differs")
        if control["corpus_wide_acceptance"] is not False:
            raise SemanticContractError("strict document control cannot claim corpus acceptance")
        return
    changed_fields = [
        name for name, expected in EXPECTED_CONTROL_FIELDS.items() if control.get(name) != expected
    ]
    if changed_fields:
        raise SemanticContractError(
            "Task 03E.2d control binding differs: " + ", ".join(changed_fields)
        )

    if tuple(control.get("authorized_uses", ())) != EXPECTED_AUTHORIZED_USES:
        raise SemanticContractError("bounded-acceptance authorized scope differs")
    if tuple(control.get("limitations", ())) != EXPECTED_LIMITATIONS:
        raise SemanticContractError("bounded-acceptance limitation inventory differs")
    if control.get("semantic_counts") != EXPECTED_SEMANTIC_COUNTS:
        raise SemanticContractError("accepted semantic counts differ")
