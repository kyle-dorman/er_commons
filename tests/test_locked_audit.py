"""Independent ledger audit rejects inconsistent admission and cost evidence."""

from decimal import Decimal

import pytest

from er_commons.locked_audit import audit_ledger
from er_commons.locked_dispatch import LockedDispatcher, Request


def test_audit_reconciles_unknown_actual_cost(tmp_path):
    """An accepted zero planning reserve must not become a verified zero fee."""
    with LockedDispatcher(tmp_path) as dispatcher:
        dispatcher.invoke(
            Request("count", "slot", "count", Decimal(0), 0, 0, parent_key="generation"),
            lambda: (None, None),
        )
        dispatcher.invoke(
            Request("generation", "slot", "generation", Decimal("1"), 10, 20),
            lambda: (None, Decimal("0.1")),
        )
    result = audit_ledger(tmp_path)
    assert result["counts"] == {"generation": 1, "judge": 0, "count": 1}
    assert result["settled_known_cost_usd"] == "0.1"
    assert result["unknown_actual_cost_keys"] == ["count"]
    assert result["peak_recorded_concurrency"] == 1


def test_audit_rejects_overlapping_reservations(tmp_path):
    """Independent timestamp replay detects a ledger above its concurrency cap."""
    import json

    with LockedDispatcher(tmp_path, concurrency=1) as dispatcher:
        for number in range(2):
            dispatcher.invoke(
                Request(str(number), str(number), "generation", Decimal("1"), 1, 1),
                lambda: (None, Decimal("0.1")),
            )
    for path in tmp_path.glob("*.reservation.json"):
        row = json.loads(path.read_text())
        row["started_at"] = 1
        path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match="concurrency"):
        audit_ledger(tmp_path)


def test_audit_rejects_cumulative_budget_breach(tmp_path):
    """A valid settled charge plus a later reserve cannot cross the cap."""
    import json

    with LockedDispatcher(tmp_path) as dispatcher:
        for number in range(2):
            dispatcher.invoke(
                Request(str(number), str(number), "generation", Decimal("6"), 1, 1),
                lambda: (None, Decimal("0.1")),
            )
    first = next(
        p for p in tmp_path.glob("*.settlement.json") if json.loads(p.read_text())["key"] == "0"
    )
    row = json.loads(first.read_text())
    row["actual_cost_usd"] = "5"
    first.write_text(json.dumps(row))
    with pytest.raises(ValueError, match="budget"):
        audit_ledger(tmp_path)


def test_audit_honors_explicit_extended_deadline(tmp_path):
    """Only the explicit amended ledger policy permits later evaluation admission."""
    import json

    with LockedDispatcher(tmp_path, clock=lambda: 2000) as dispatcher:
        dispatcher.invoke(
            Request("judge", "slot", "judge", Decimal("1"), 1, 1, evaluation_started_at=1000),
            lambda: (None, Decimal("0.1")),
        )
    path = next(tmp_path.glob("*.reservation.json"))
    row = json.loads(path.read_text())
    row["evaluation_started_at"] = 0
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError, match="deadline"):
        audit_ledger(tmp_path)
    policy_path = tmp_path / "policy.json"
    policy = json.loads(policy_path.read_text())
    policy.update(version=3, evaluation_seconds=5400)
    policy_path.write_text(json.dumps(policy))
    assert audit_ledger(tmp_path)["counts"]["judge"] == 1
    policy["evaluation_seconds"] = 10000
    policy_path.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="deadline policy"):
        audit_ledger(tmp_path)
