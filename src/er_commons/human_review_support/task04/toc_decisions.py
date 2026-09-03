"""Load and preserve stable TOC decisions across review regenerations."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonObject
from er_commons.human_review_support.task04.toc_models import TocDisposition

VALID_DISPOSITIONS = {"toc", "not_toc"}


def load_toc_decisions(path: Path | None) -> dict[str, TocDisposition]:
    """Load one exported or previously imported stable decision mapping."""
    if path is None:
        return {}
    record = read_json_object(path)
    entries = require_list(record.get("entries"), path=f"{path}:$.entries")
    decisions: dict[str, TocDisposition] = {}
    for index, entry in enumerate(entries):
        entry_path = f"{path}:$.entries[{index}]"
        item = require_mapping(entry, path=entry_path)
        entry_id = require_string(item.get("entry_id"), path=f"{entry_path}.entry_id")
        disposition = require_string(item.get("disposition"), path=f"{entry_path}.disposition")
        if not entry_id.startswith("tocpagev1-"):
            raise ValueError(f"expected TOC page identity at {entry_path}.entry_id")
        if disposition not in VALID_DISPOSITIONS:
            raise ValueError(f"invalid TOC disposition at {entry_path}.disposition")
        typed_disposition = cast(TocDisposition, disposition)
        previous = decisions.get(entry_id)
        if previous is not None and previous != typed_disposition:
            raise ValueError(f"conflicting TOC decisions for {entry_id}")
        decisions[entry_id] = typed_disposition
    return decisions


def discover_prior_toc_decisions(output_parent: Path) -> Path | None:
    """Return the newest completed c-run decision record, if one exists."""
    candidates = sorted(
        output_parent.glob("reviewv1-task03j-final-c*/records/toc_review_decisions.json"),
        key=lambda path: path.stat().st_mtime_ns,
    )
    return candidates[-1] if candidates else None


def decision_record(review_run_id: str, decisions: dict[str, TocDisposition]) -> JsonObject:
    """Serialize stable decisions for automatic reuse by the next c-run."""
    return {
        "schema_version": "er_commons.task04a_toc_review_decisions.v1",
        "review_run_id": review_run_id,
        "status": "imported_pending_positive_confirmation",
        "entries": [
            {"entry_id": entry_id, "disposition": disposition}
            for entry_id, disposition in sorted(decisions.items())
        ],
    }


__all__ = [
    "decision_record",
    "discover_prior_toc_decisions",
    "load_toc_decisions",
]
