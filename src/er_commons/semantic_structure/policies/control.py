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
