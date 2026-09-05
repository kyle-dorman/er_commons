"""Fail-closed accounting checks for the Task 04D Gate C dry run.

This module does not resolve links or publish artifacts.  It checks the
source-free decisions emitted by the reusable linker against the population
and regression controls accepted at Gate A.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class AcceptedNavigationControl:
    """Expected population and result counts for one disjoint control class."""

    population: int
    resolved: int


ACCEPTED_NAVIGATION_CONTROLS: Mapping[str, AcceptedNavigationControl] = {
    "existing_task04c_link": AcceptedNavigationControl(28, 28),
    "appendix_a_no_page_section": AcceptedNavigationControl(87, 80),
    "lettered_section": AcceptedNavigationControl(112, 109),
    "table": AcceptedNavigationControl(120, 95),
    "ordinary_numbered_section": AcceptedNavigationControl(108, 98),
    "destination_page_conflict": AcceptedNavigationControl(1, 0),
    "figure": AcceptedNavigationControl(89, 0),
    "unsupported_shape": AcceptedNavigationControl(15, 0),
}

# Mutually exclusive primary attribution.  A compositional match is credited
# to the more structural rule (for example, a GOAL projection plus punctuation
# remains R2a) so these counts sum to the 410 accepted links exactly once.
ACCEPTED_PRIMARY_RULE_COUNTS: Mapping[str, int] = {
    "R1": 28,
    "R2": 155,
    "R2a": 7,
    "R2b": 12,
    "R3": 72,
    "R4": 29,
    "R5": 12,
    "R6": 78,
    "R6a": 17,
}


def validate_gate_c_navigation_population(
    decisions: Iterable[JsonObject],
    *,
    baseline_targets: Mapping[str, str],
) -> JsonObject:
    """Validate the complete accepted navigation census and old-link targets.

    Each decision must provide ``entry_id``, ``control_class``, ``outcome``,
    and ``primary_rule_id``. Resolved rows additionally require ``target_id``.
    Baseline targets are keyed by the 28 Task 04C entry IDs.
    """
    rows = list(decisions)
    entry_ids = [_required_text(row, "entry_id") for row in rows]
    if len(rows) != 560 or len(set(entry_ids)) != 560:
        raise ValueError("Gate C navigation decisions must contain 560 unique entry IDs")
    if len(baseline_targets) != 28:
        raise ValueError("Task 04C baseline must contain exactly 28 links")

    population_counts: Counter[str] = Counter()
    resolved_counts: Counter[str] = Counter()
    primary_rule_counts: Counter[str] = Counter()
    selected_targets: dict[str, str] = {}
    for row in rows:
        control_class = _required_text(row, "control_class")
        if control_class not in ACCEPTED_NAVIGATION_CONTROLS:
            raise ValueError(f"unknown Gate C control class: {control_class!r}")
        population_counts[control_class] += 1
        outcome = _required_text(row, "outcome")
        if outcome != "resolved_unique":
            if row.get("target_id") is not None or row.get("primary_rule_id") is not None:
                raise ValueError("unresolved decisions cannot select a target or primary rule")
            continue
        target_id = _required_text(row, "target_id")
        rule_id = _required_text(row, "primary_rule_id")
        resolved_counts[control_class] += 1
        primary_rule_counts[rule_id] += 1
        selected_targets[_required_text(row, "entry_id")] = target_id

    _require_counts(
        "control populations",
        population_counts,
        {name: value.population for name, value in ACCEPTED_NAVIGATION_CONTROLS.items()},
    )
    _require_counts(
        "resolved control populations",
        resolved_counts,
        {name: value.resolved for name, value in ACCEPTED_NAVIGATION_CONTROLS.items()},
    )
    _require_counts("primary rules", primary_rule_counts, ACCEPTED_PRIMARY_RULE_COUNTS)

    invalidated = {
        entry_id: {"expected": target_id, "actual": selected_targets.get(entry_id)}
        for entry_id, target_id in baseline_targets.items()
        if selected_targets.get(entry_id) != target_id
    }
    if invalidated:
        raise ValueError(f"Task 04C baseline links changed: {invalidated}")
    return {
        "population_count": len(rows),
        "resolved_count": len(selected_targets),
        "unresolved_count": len(rows) - len(selected_targets),
        "control_population_counts": dict(sorted(population_counts.items())),
        "control_resolved_counts": dict(sorted(resolved_counts.items())),
        "primary_rule_counts": dict(sorted(primary_rule_counts.items())),
        "existing_link_invalidation_count": 0,
    }


def compare_ordinary_machine_population(
    baseline: Iterable[JsonObject], replacement: Iterable[JsonObject]
) -> JsonObject:
    """Compare complete ordinary-reference decisions by stable mention key.

    Existing resolved targets may not change or disappear. New unique links are
    reported separately because R6 body aliases are intentionally available to
    the same reusable machine linker.
    """
    old = _index_machine_rows(baseline, label="baseline")
    new = _index_machine_rows(replacement, label="replacement")
    missing = sorted(set(old).difference(new))
    added = sorted(set(new).difference(old))
    if missing or added:
        raise ValueError(
            f"ordinary-reference mention keys changed: missing={missing}, added={added}"
        )

    changed_existing: list[str] = []
    new_unique: list[str] = []
    unchanged = 0
    for key in sorted(old):
        old_target = old[key].get("target_id")
        new_target = new[key].get("target_id")
        if old_target is not None and new_target != old_target:
            changed_existing.append(key)
        elif old_target is None and new_target is not None:
            new_unique.append(key)
        else:
            unchanged += 1
    if changed_existing:
        raise ValueError(f"existing ordinary-reference targets changed: {changed_existing}")
    return {
        "population_count": len(old),
        "unchanged_count": unchanged,
        "new_unique_link_count": len(new_unique),
        "new_unique_mention_keys": new_unique,
        "existing_target_invalidation_count": 0,
    }


def _index_machine_rows(rows: Iterable[JsonObject], *, label: str) -> dict[str, JsonObject]:
    indexed: dict[str, JsonObject] = {}
    for row in rows:
        key = _required_text(row, "mention_key")
        if key in indexed:
            raise ValueError(f"duplicate {label} ordinary-reference mention key: {key!r}")
        target_id = row.get("target_id")
        if target_id is not None and (not isinstance(target_id, str) or not target_id):
            raise ValueError(f"invalid {label} target_id for {key!r}")
        indexed[key] = row
    return indexed


def _require_counts(label: str, actual: Mapping[str, int], expected: Mapping[str, int]) -> None:
    normalized = {key: actual.get(key, 0) for key in expected}
    extras = {key: count for key, count in actual.items() if key not in expected and count}
    if normalized != dict(expected) or extras:
        raise ValueError(f"unexpected {label}: actual={dict(actual)}, expected={dict(expected)}")


def _required_text(row: JsonObject, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"decision field {key!r} must be a non-empty string")
    return value


__all__ = [
    "ACCEPTED_NAVIGATION_CONTROLS",
    "ACCEPTED_PRIMARY_RULE_COUNTS",
    "AcceptedNavigationControl",
    "compare_ordinary_machine_population",
    "validate_gate_c_navigation_population",
]
