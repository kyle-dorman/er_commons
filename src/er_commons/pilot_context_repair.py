"""Refresh response context for a fixed sample without selecting any new cases."""

import copy
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

_DIRECTED = {
    "response_response",
    "response_general_response",
    "general_response_response",
    "general_response_general_response",
}


def _rows(content: bytes) -> list[dict[str, Any]]:
    """Decode persisted JSONL records in their recorded order."""
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def _index(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Reject duplicate identities before composing any context."""
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return result


def _families(outcomes: list[dict[str, Any]]) -> list[str]:
    """Collapse only the existing split-document suffix convention."""
    return sorted(
        {
            re.sub(r"_part_\d+_of_\d+$", "", source)
            for row in outcomes
            for source in row["logical_source_ids"]
        }
    )


def refresh_cases(
    original: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    views: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Follow only response-directed closure, retaining fixed selection provenance."""
    _index(original, "comment_id")
    units = _index([row for row in sources if row["record_type"] == "source_unit"], "unit_id")
    pages = _index([row for row in sources if row["record_type"] == "page"], "page_id")
    spans = _index([row for row in sources if row["record_type"] == "source_span"], "span_id")
    edge_index = _index(edges, "edge_id")
    view_index = _index(views, "root_unit_id")
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        if edge["relation_type"] in _DIRECTED:
            outgoing[edge["source_unit_id"]].append(edge)
    for outcome in outcomes:
        by_unit[outcome["source_unit_id"]].append(outcome)
    context: dict[str, dict[str, Any]] = {}
    result, changes = [], []
    for old in original:
        cid = old["comment_id"]
        view = view_index[cid]
        ids = list(view["ordered_unit_ids"])
        if len(ids) != len(set(ids)) or cid not in ids:
            raise ValueError(f"Invalid accepted view membership: {cid}")
        edge_ids = set(view["edge_ids"])
        direct = [
            edge_index[key]["target_unit_id"]
            for key in view["edge_ids"]
            if edge_index[key]["relation_type"] == "comment_response"
            and edge_index[key]["source_unit_id"] == cid
        ]
        seen = set(ids)
        for uid in ids:
            for edge in sorted(outgoing[uid], key=lambda row: row["edge_id"]):
                edge_ids.add(edge["edge_id"])
                target = edge["target_unit_id"]
                if units[target]["unit_kind"] not in {"response", "general_response"}:
                    raise ValueError("Response-directed edge points to non-response")
                if target not in seen:
                    ids.append(target)
                    seen.add(target)
        if any(units[uid]["unit_kind"] == "comment" and uid != cid for uid in ids):
            raise ValueError(f"Unrelated comment entered context: {cid}")
        if direct != old["direct_response_ids"]:
            raise ValueError(f"Direct response changed: {cid}")
        for uid in ids:
            if uid in context:
                continue
            unit = units[uid]
            fragments = [
                fragment for sid in unit["span_ids"] for fragment in spans[sid]["fragments"]
            ]
            context[uid] = {
                "unit_id": uid,
                "unit_kind": unit["unit_kind"],
                "official_label": unit["official_label"],
                "span_ids": unit["span_ids"],
                "source_pages": sorted({pages[f["page_id"]]["physical_page"] for f in fragments}),
                "text": "\n".join(
                    pages[f["page_id"]]["raw_text"][f["text_start"] : f["text_end"]]
                    for f in fragments
                ),
            }
        relevant = [row for uid in ids for row in by_unit[uid]]
        own = [row for uid in [cid, *direct] for row in by_unit[uid]]
        signals = set()
        for row in relevant:
            if row["outcome"] == "terminal_nonlink" and row["source_kind"] != "comment":
                signals.add("nonlink:" + row["terminal_reason"])
            if row.get("final_f1_warning"):
                signals.add("final_f1_warning")
            if any(
                a.get("text_only_model_eligibility") is False
                for a in row.get("target_annotations", [])
            ):
                signals.add("text_only_excluded_target")
        if not direct:
            signals.add("no_direct_response")
        case = copy.deepcopy(old)
        case.update(
            review_state="original_decision_preserved_separately",
            accepted_view_id=view["view_id"],
            accepted_view_unit_ids=view["ordered_unit_ids"],
            context_unit_ids=ids,
            relationship_ids=sorted(edge_ids),
            direct_response_ids=direct,
            general_response_ids=[
                uid for uid in ids if units[uid]["unit_kind"] == "general_response"
            ],
            direct_context_citation_families=_families(own),
            full_context_citation_families=_families(relevant),
            reference_outcome_ids=[row["outcome_id"] for row in relevant],
            reference_mention_ids=sorted(
                {
                    row["mention_id"]
                    for row in sources
                    if row["record_type"] == "reference_mention" and row["source_unit_id"] in seen
                }
            ),
            challenge_signals=sorted(signals),
            source_pages=context[cid]["source_pages"],
        )
        if set(old["context_unit_ids"]) - seen:
            raise ValueError(f"Original context removed: {cid}")
        additions = sorted(seen - set(old["context_unit_ids"]))
        added_edges = sorted(edge_ids - set(old["relationship_ids"]))
        if additions or added_edges:
            changes.append(
                {
                    "comment_id": cid,
                    "comment_label": old["comment_label"],
                    "added_context_unit_ids": additions,
                    "added_relationship_ids": added_edges,
                    "original_decision_action": "retain; optional follow-up only",
                }
            )
        result.append(case)
    return result, list(context.values()), changes


def _checked(root: Path, ref: dict[str, Any]) -> bytes:
    """Read only a pinned artifact contained within the declared root."""
    path = (root / ref["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Artifact path escapes data root")
    content: bytes = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != ref["sha256"]:
        raise ValueError(f"Checksum mismatch: {path}")
    if "size_bytes" in ref and len(content) != ref["size_bytes"]:
        raise ValueError(f"Size mismatch: {path}")
    return content


def refresh_sample(
    original_root: Path, final_result: dict[str, Any], data_root: Path, output: Path
) -> dict[str, Any]:
    """Write a fresh fixed-sample derivative after checking accepted release seals."""
    original_manifest_bytes = (original_root / "selection_manifest.json").read_bytes()
    original_manifest = json.loads(original_manifest_bytes)
    old_files = {
        name: _checked(original_root, {"path": name, "sha256": digest})
        for name, digest in original_manifest["files"].items()
    }
    refs = (
        "acceptance_pointer",
        "completion",
        "manifest",
        "components",
        "task07_task08_handoff",
        "limitations",
    )
    verified = {key: json.loads(_checked(data_root, final_result[key])) for key in refs}
    inventory_id = final_result["inventory_id"]
    if verified["acceptance_pointer"]["inventory_id"] != inventory_id:
        raise ValueError("Accepted inventory pointer differs")
    acceptance = verified["acceptance_pointer"]
    if (
        acceptance["completion_sha256"] != final_result["completion"]["sha256"]
        or acceptance["manifest_sha256"] != final_result["manifest"]["sha256"]
        or acceptance["handoff_sha256"] != final_result["task07_task08_handoff"]["sha256"]
        or verified["completion"]["manifest_sha256"] != final_result["manifest"]["sha256"]
        or verified["completion"]["plan_id"] != verified["task07_task08_handoff"]["plan_id"]
    ):
        raise ValueError("Accepted release bindings differ")
    release_root = (data_root / final_result["inventory_root"]).resolve()
    if not release_root.is_relative_to(data_root.resolve()):
        raise ValueError("Release root escapes data root")
    files = {row["path"]: row for row in verified["manifest"]["files"]}
    expected = set(files) | {"records/completion.json", "records/managed_file_inventory.json"}
    if {
        str(p.relative_to(release_root)) for p in release_root.rglob("*") if p.is_file()
    } != expected:
        raise ValueError("Release managed-file closure differs")
    for ref in files.values():
        if (release_root / ref["path"]).stat().st_size != ref["size_bytes"]:
            raise ValueError("Release managed-file size differs")
    components = _index(verified["components"], "role")
    sources = _rows(_checked(data_root, components["source_records"]))
    edges = _rows(_checked(data_root, components["edges"]))
    outcomes = _rows(_checked(data_root, components["outcomes"]))
    views = _rows(_checked(release_root, files["review_views/index.jsonl"]))
    cases, context, changes = refresh_cases(
        _rows(old_files["sample.jsonl"]), sources, edges, outcomes, views
    )
    new_context = _index(context, "unit_id")
    for old in _rows(old_files["review_context.jsonl"]):
        if new_context.get(old["unit_id"]) != old:
            raise ValueError(f"Original text, spans, or boundaries changed: {old['unit_id']}")
    output.mkdir(parents=True, exist_ok=False)
    payloads = {
        "sample.jsonl": cases,
        "review_context.jsonl": context,
        "context_changes.jsonl": changes,
    }
    seals = {}
    for name, rows in payloads.items():
        content = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode()
        (output / name).write_bytes(content)
        seals[name] = hashlib.sha256(content).hexdigest()
    manifest = {
        "schema_version": "task07a.sample.context_repair.v1",
        "inventory_id": inventory_id,
        "input_refs": {key: final_result[key] for key in refs},
        "source_components": components,
        "selection_provenance": {
            "original_manifest_sha256": hashlib.sha256(original_manifest_bytes).hexdigest(),
            "original_inventory_id": original_manifest["inventory_id"],
            "original_sample_sha256": original_manifest["files"]["sample.jsonl"],
            "selection_seed": original_manifest["selection_seed"],
            "settings": original_manifest["settings"],
            "summary": original_manifest["summary"],
            "selection_rerun": False,
        },
        "summary": {"cases": len(cases), "cases_with_added_context_or_links": len(changes)},
        "context_policy": "Accepted bounded view plus response-directed closure; no other comments",
        "decision_policy": "Retain original decisions; new context is optional follow-up",
        "limitations": verified["limitations"],
        "files": seals,
    }
    (output / "selection_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
