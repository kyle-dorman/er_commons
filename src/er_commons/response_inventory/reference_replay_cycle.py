"""Sealed prior-candidate comparison for a bounded general-rule trial."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.response_inventory.reference_replay_spec import contained_path
from er_commons.response_inventory.reference_replay_storage import read_checkpoint


def prior_outcomes(binding: dict[str, Any], artifact_root: Path) -> list[dict[str, Any]]:
    """Verify the exact prior checkpoint before reading its comparison population."""
    root = contained_path(artifact_root, binding["candidate_root"])
    raw = (root / "completion.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["completion_sha256"]:
        raise ValueError("prior replay completion digest differs")
    completion = json.loads(raw)
    read_checkpoint(root, completion["bindings"])
    return [
        json.loads(line)
        for line in (root / "outcomes/reference_outcomes.jsonl").read_text().splitlines()
    ]


def compare_rule_cycle(
    before: list[dict[str, Any]], after: list[dict[str, Any]], allowed_ids: list[str]
) -> dict[str, Any]:
    """Reject any out-of-scope behavior drift, historical link loss or warning change."""
    old = {row["mention_id"]: row for row in before}
    new = {row["mention_id"]: row for row in after}
    if len(old) != len(before) or len(new) != len(after) or set(old) != set(new):
        raise ValueError("rule cycle population differs")
    allowed = set(allowed_ids)
    if not allowed <= set(old):
        raise ValueError("rule cycle allowed population is not a subset")
    ignored = {"outcome_id", "link_id", "inner_reference_evidence"}
    rows = []
    for key, previous in sorted(old.items()):
        current = new[key]
        changed_fields = sorted(
            field
            for field in (set(previous) | set(current)) - ignored
            if previous.get(field) != current.get(field)
        )
        changed = bool(changed_fields)
        if key not in allowed and changed:
            raise ValueError(
                f"rule cycle changed an out-of-scope outcome: {key}; fields={changed_fields}"
            )
        for field in ("final_f1_warning", "coverage_boundary", "source_usability", "input_refs"):
            if previous[field] != current[field]:
                raise ValueError(f"rule cycle changed inherited limitation: {field}; mention={key}")
        if previous["outcome"] == "resolved" and (
            current["outcome"] != "resolved"
            or previous["compatible_target_ids"] != current["compatible_target_ids"]
            or previous["target_annotations"] != current["target_annotations"]
        ):
            raise ValueError(f"rule cycle lost or changed an existing link: {key}")
        if changed:
            rows.append({"mention_id": key, "before": previous, "after": current})
    return {
        "schema_version": "er_commons.task05g.rule_cycle_comparison.v1",
        "total": len(old),
        "allowed_change_mentions": sorted(allowed),
        "changed_count": len(rows),
        "changes": rows,
        "link_gains": sum(
            r["before"]["outcome"] != "resolved" and r["after"]["outcome"] == "resolved"
            for r in rows
        ),
        "link_losses": 0,
        "unchanged_outside_scope": len(old) - len(allowed),
    }
