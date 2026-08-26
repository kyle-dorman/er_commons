"""One-way lifecycle invariants for the Task 04 finding register."""

from __future__ import annotations

from er_commons.human_review_support.task04.json_io import (
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue
from er_commons.human_review_support.task04.register_models import FindingRegisterStatus

PENDING_FINDING_STATUS = "user_confirmed"


def transition_register(
    current: dict[str, JsonValue], target: FindingRegisterStatus
) -> dict[str, JsonValue]:
    """Enforce the one-way overall review lifecycle and terminal item decisions."""
    current_status = require_string(current.get("status"), path="finding_register.status")
    if current_status == target.value:
        return dict(current)
    if target is FindingRegisterStatus.APPROVED:
        if current_status not in {"open_empty", "open"}:
            raise ValueError(f"cannot approve finding register from status {current_status!r}")
        pending = _pending_finding_ids(current)
        if pending:
            raise ValueError(
                f"cannot approve finding register with user_confirmed findings: {pending!r}"
            )
    elif current_status != FindingRegisterStatus.APPROVED.value:
        raise ValueError(
            f"finding register must be approved before it can be closed: current={current_status!r}"
        )
    updated = dict(current)
    updated["status"] = target.value
    return updated


def register_is_approved(register: dict[str, JsonValue]) -> bool:
    """Return whether the overall review has reached an approved terminal state."""
    status = require_string(register.get("status"), path="finding_register.status")
    return status in {
        FindingRegisterStatus.APPROVED.value,
        FindingRegisterStatus.CLOSED.value,
    }


def _pending_finding_ids(register: dict[str, JsonValue]) -> list[str]:
    rows = require_list(register.get("findings"), path="finding_register.findings")
    pending: list[str] = []
    for index, value in enumerate(rows):
        path = f"finding_register.findings[{index}]"
        row = require_mapping(value, path=path)
        if row.get("status") == PENDING_FINDING_STATUS:
            pending.append(require_string(row.get("finding_id"), path=f"{path}.finding_id"))
    return sorted(pending)


__all__ = ["register_is_approved", "transition_register"]
