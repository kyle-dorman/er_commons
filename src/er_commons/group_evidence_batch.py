"""Verified combined 08D intake for independent question research packets."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from er_commons.group_claims_batch import read_reference, reference, write_new
from er_commons.group_claims_chat import export_review
from er_commons.group_claims_chat_cli import load_journal


def _verify_bindings(value: Any) -> None:
    """Verify every nested explicit file reference, including optional byte sizes."""
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            path = Path(value["path"])
            if reference(path)["sha256"] != value["sha256"]:
                raise ValueError(f"Upstream binding changed: {path}")
            if "bytes" in value and path.stat().st_size != value["bytes"]:
                raise ValueError(f"Upstream byte size changed: {path}")
        for member in value.values():
            _verify_bindings(member)
    elif isinstance(value, list):
        for member in value:
            _verify_bindings(member)


def _verify_preparation(preparation: dict[str, Any], queue_ref: dict[str, Any]) -> None:
    """Check the complete sealed preparation manifest and exact consumed queue."""
    _verify_bindings(preparation)
    if preparation["queue"] != queue_ref:
        raise ValueError("Preparation and review queue bindings differ")
    manifest = read_reference(preparation["manifest"])
    _verify_bindings(manifest)


def load_inputs(result_path: Path) -> dict[str, Any]:
    """Verify sealed review, supplemental closure and replay before projecting cases."""
    result = json.loads(result_path.read_bytes())
    handoff = read_reference(result["handoff"])
    for key in ("required_context", "validation"):
        if result[key] != handoff[key]:
            raise ValueError(f"Result/handoff binding differs: {key}")
    objects = {
        key: read_reference(value)
        for key, value in handoff.items()
        if isinstance(value, dict)
        and "path" in value
        and "sha256" in value
        and key not in {"resume", "journal_source"}
    }
    # Non-JSON records still require exact byte verification.
    for key in ("resume", "journal_source"):
        if reference(Path(handoff[key]["path"])) != handoff[key]:
            raise ValueError(f"Upstream file changed: {key}")
    queue, review = objects["prepared_queue"], objects["review"]
    _verify_preparation(objects["preparation_handoff"], handoff["prepared_queue"])
    journal = load_journal(Path(handoff["journal_source"]["path"]), queue)
    if journal != objects["journal_snapshot"] or export_review(queue, journal) != review:
        raise ValueError("Upstream review does not reproduce from exact journal")
    required = objects["required_context"]
    if required["all_supplemental_context"] != handoff["supplemental_inventory"]:
        raise ValueError("Required-context supplemental inventory binding differs")
    _verify_bindings(required)
    supplemental = objects["supplemental_inventory"]
    root = Path(supplemental["root"])
    files = supplemental["files"]
    # Inventory format is explicit; no newest-file or glob-selected replacement.
    expected = {str(Path(row["path"]).relative_to(root)) for row in files}
    actual = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and "exports" not in path.relative_to(root).parts[:1]
    }
    if actual != expected:
        raise ValueError("Supplemental file closure differs")
    for row in files:
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Supplemental path escapes root")
        if reference(path)["sha256"] != row["sha256"]:
            raise ValueError(f"Supplemental bytes changed: {path}")
        if path.stat().st_size != row["bytes"]:
            raise ValueError(f"Supplemental byte size changed: {path}")
    readings = [
        {"binding": ref, "content": read_reference(ref)} for ref in required["required_reading"]
    ]
    cases = []
    held = []
    for source in review["source_context"]["cases"]:
        cid = source["case_id"]
        state = review["cases"][cid]
        if state["case_decision"]["decision"] != "investigate":
            held.append(cid)
            continue
        advancing = [row for row in review["advancing"] if row["case_id"] == cid]
        cases.append(
            _project_case(source, state, advancing, required, readings, review, handoff, result)
        )

    deferred = review["context_notes"]["all_57_decisions"]["deferred_neutral_ids"]
    if (
        len(cases) != 50
        or held != ["C014", "C020", "C024"]
        or deferred != ["C013", "C023", "C038", "C057"]
        or sum(len(case["approved_claims"]) for case in cases) != 385
    ):
        raise ValueError("Combined-pass membership differs")
    return {
        "schema_version": "task08e.batch_inputs.v1",
        "cases": cases,
        "held_case_ids": held,
        "deferred_case_ids": deferred,
        "upstream_result": reference(result_path),
        "upstream_handoff": result["handoff"],
    }


def _project_case(
    source: dict[str, Any],
    state: dict[str, Any],
    advancing: list[dict[str, Any]],
    required: dict[str, Any],
    readings: list[dict[str, Any]],
    review: dict[str, Any],
    handoff: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Preserve the exact source and human history for released or reopened research."""
    cid = source["case_id"]
    return {
        "case_id": cid,
        "question": copy.deepcopy(source["question"]),
        "approved_claims": [copy.deepcopy(row["claim"]) for row in advancing],
        "support_chains": copy.deepcopy(advancing),
        "source_context": copy.deepcopy(source),
        "reviewed_case": copy.deepcopy(state),
        "required_context": copy.deepcopy(required),
        "required_reading": copy.deepcopy(readings),
        "context_notes_binding": handoff["review"],
        "historical_reconciliation": {
            key: copy.deepcopy(value)
            for key, value in review["context_notes"].items()
            if key != "all_57_decisions"
        },
        "inherited_limitations": copy.deepcopy(review["source_context"]["limitations"]),
        "supplemental_inventory": handoff["supplemental_inventory"],
        "upstream_handoff": result["handoff"],
    }


def prepare_inputs(result_path: Path, output: Path) -> dict[str, Any]:
    """Save exact per-case intake in saved order, safely resuming identical writes."""
    inputs = load_inputs(result_path)
    refs = []
    for case in inputs["cases"]:
        path = output / "cases" / case["case_id"] / "input.json"
        write_new(path, case)
        refs.append({"case_id": case["case_id"], "input": reference(path)})
    register = {key: value for key, value in inputs.items() if key != "cases"}
    register.update(cases=refs, status="inputs verified; research not started")
    write_new(output / "inputs.json", register)
    return register
