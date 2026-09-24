"""Source/graph-only replay may renew provenance but not report-reference behavior."""

from copy import deepcopy
from typing import Any

import pytest
from test_task05g_resolver import fixture

from er_commons.response_inventory.reference_replay_cycle import compare_source_graph_cycle
from er_commons.response_inventory.reference_replay_resolver import resolve_references


def cycle_inputs() -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    """Make an unchanged resolved outcome under exactly two replaced source owners."""
    before = resolve_references(**fixture())["outcomes"]
    prior_refs = [
        {"role": "task05d_completion", "sha256": "old-source"},
        {"role": "task05e_completion", "sha256": "old-graph"},
        {"role": "task06h_handoff", "sha256": "same-report-handoff"},
    ]
    before[0]["input_refs"] = prior_refs
    before[0]["inner_reference_evidence"] = {"rule": "same", "target": "same"}
    dependencies = [
        {"role": "task05d_completion", "sha256": "new-source"},
        {"role": "task05e_completion", "sha256": "new-graph"},
        {"role": "task06h_handoff", "sha256": "same-report-handoff"},
    ]
    after = deepcopy(before)
    after[0]["input_refs"] = deepcopy(dependencies)
    after[0]["outcome_id"] = "renewed-outcome"
    after[0]["link_id"] = "renewed-link"
    return before, after, dependencies, deepcopy(prior_refs[:2])


def test_source_graph_cycle_allows_only_bound_provenance_replacement() -> None:
    """Both source owners may change while all report-target evidence remains exact."""
    before, after, dependencies, replaced = cycle_inputs()
    result = compare_source_graph_cycle(before, after, dependencies, replaced)
    assert result["changed_count"] == 0
    assert result["total"] == 1
    assert result["provenance_replacement"] == ["task05d_completion", "task05e_completion"]
    assert before[0]["input_refs"][0]["sha256"] == "old-source"
    assert after[0]["input_refs"] == dependencies


@pytest.mark.parametrize(
    "mutation",
    ["outcome_dependency", "historical_dependency", "handoff", "target", "annotation", "inner"],
)
def test_source_graph_cycle_rejects_dependency_or_target_drift(mutation: str) -> None:
    """Changed source bindings cannot conceal changed inherited reference behavior."""
    before, after, dependencies, replaced = cycle_inputs()
    if mutation == "outcome_dependency":
        after[0]["input_refs"][0]["sha256"] = "unexpected-source"
    elif mutation == "historical_dependency":
        replaced[0]["sha256"] = "not-the-accepted-source"
        after[0]["input_refs"] = deepcopy(dependencies)
    elif mutation == "handoff":
        dependencies[2]["sha256"] = "changed-report-handoff"
        after[0]["input_refs"] = deepcopy(dependencies)
    elif mutation == "target":
        after[0]["compatible_target_ids"] = ["different-target"]
    elif mutation == "annotation":
        after[0]["target_annotations"] = [{"silently_changed": True}]
    else:
        after[0]["inner_reference_evidence"] = {"rule": "different"}
    with pytest.raises(ValueError):
        compare_source_graph_cycle(before, after, dependencies, replaced)
