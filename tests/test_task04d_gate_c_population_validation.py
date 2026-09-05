"""Tests for Task 04D Gate C whole-population controls."""

from __future__ import annotations

import pytest

from er_commons.navigation_overlay.gate_c_validation import (
    ACCEPTED_NAVIGATION_CONTROLS,
    ACCEPTED_PRIMARY_RULE_COUNTS,
    compare_ordinary_machine_population,
    validate_gate_c_navigation_population,
)


def _accepted_decisions() -> tuple[list[dict[str, object]], dict[str, str]]:
    rules = [rule for rule, count in ACCEPTED_PRIMARY_RULE_COUNTS.items() for _ in range(count)]
    rows: list[dict[str, object]] = []
    baseline: dict[str, str] = {}
    resolved_index = 0
    entry_index = 0
    for control_class, control in ACCEPTED_NAVIGATION_CONTROLS.items():
        for class_index in range(control.population):
            entry_id = f"entry-{entry_index:03d}"
            row: dict[str, object] = {
                "entry_id": entry_id,
                "control_class": control_class,
                "outcome": "unresolved",
                "target_id": None,
                "primary_rule_id": None,
            }
            if class_index < control.resolved:
                row.update(
                    outcome="resolved_unique",
                    target_id=f"target-{entry_index:03d}",
                    primary_rule_id=rules[resolved_index],
                )
                resolved_index += 1
            if control_class == "existing_task04c_link":
                baseline[entry_id] = str(row["target_id"])
            rows.append(row)
            entry_index += 1
    return rows, baseline


def test_gate_c_navigation_controls_close_to_410_of_560() -> None:
    rows, baseline = _accepted_decisions()

    summary = validate_gate_c_navigation_population(rows, baseline_targets=baseline)

    assert summary["resolved_count"] == 410
    assert summary["unresolved_count"] == 150
    assert summary["existing_link_invalidation_count"] == 0


def test_gate_c_navigation_controls_reject_baseline_target_change() -> None:
    rows, baseline = _accepted_decisions()
    rows[0]["target_id"] = "changed"

    with pytest.raises(ValueError, match="baseline links changed"):
        validate_gate_c_navigation_population(rows, baseline_targets=baseline)


def test_gate_c_navigation_controls_reject_rule_accounting_drift() -> None:
    rows, baseline = _accepted_decisions()
    rows[0]["primary_rule_id"] = "R7"

    with pytest.raises(ValueError, match="unexpected primary rules"):
        validate_gate_c_navigation_population(rows, baseline_targets=baseline)


def test_machine_population_allows_additions_but_not_invalidations() -> None:
    baseline = [
        {"mention_key": "m1", "target_id": "t1"},
        {"mention_key": "m2", "target_id": None},
    ]
    replacement = [
        {"mention_key": "m1", "target_id": "t1"},
        {"mention_key": "m2", "target_id": "t2"},
    ]

    summary = compare_ordinary_machine_population(baseline, replacement)

    assert summary["existing_target_invalidation_count"] == 0
    assert summary["new_unique_mention_keys"] == ["m2"]


def test_machine_population_rejects_changed_existing_target() -> None:
    baseline = [{"mention_key": "m1", "target_id": "t1"}]
    replacement = [{"mention_key": "m1", "target_id": "t2"}]

    with pytest.raises(ValueError, match="existing ordinary-reference targets changed"):
        compare_ordinary_machine_population(baseline, replacement)
