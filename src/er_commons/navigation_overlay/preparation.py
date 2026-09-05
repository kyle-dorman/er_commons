"""Source-free Task 04C Gate A correspondence and identity preparation."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    file_reference,
    iter_jsonl,
    json_bytes,
    jsonl_bytes,
    read_json_object,
    sha256_bytes,
    sha256_file,
)

JsonObject = dict[str, Any]

PRODUCTION_EXTRACTION_ID = "exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773"
SCOPE_ID = "scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893"
HANDOFF_ID = "handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325"
TASK04A_REVIEW_ID = "reviewv1-task03j-final-c17"
TASK04A_GATE_A_ID = "reviewv1-task03j-final-b19a7a36b04bda89"
EXPECTED_SOURCE_COUNT = 35
EXPECTED_CENSUS_PAGE_COUNT = 5_624
EXPECTED_DECISION_COUNT = 757
EXPECTED_DECISION_COUNTS = {"toc": 60, "not_toc": 697}
EXPECTED_AMBIGUOUS_LINK_COUNT = 725

_TASK03J_RELATIVE = "pipelines/brisbane_baylands/task_03h_clean_full_v4"
_REVIEW_RELATIVE = "pipelines/brisbane_baylands/task_04_review"
_OUTPUT_RELATIVE = "pipelines/brisbane_baylands/task_04_navigation_overlay"
_CANONICAL_FILES = (
    "content/canonical/pages.jsonl",
    "content/canonical/sections.jsonl",
    "content/canonical/blocks.jsonl",
    "content/canonical/tables.jsonl",
    "content/canonical/target_aliases.jsonl",
    "content/canonical/cross_references.jsonl",
)
_POLICY: JsonObject = {
    "schema_version": "er_commons.navigation_overlay_policy.v1",
    "correspondence": "existing_regions_on_exact_decision_page_mixed_only_when_explicit",
    "mixed_page": "fail_closed_as_insufficient_entity_evidence",
    "missing_entity": "fail_closed_as_insufficient_entity_evidence",
    "alias_closure": "sealed_visible_toc_reconciliation_provenance_only",
    "link_closure": "direct_source_or_affected_alias_or_target",
    "inherited_ambiguous_links": "remain_unresolved_unless_later_entity_evidence_is_unique",
    "source_reads": False,
    "model_reads": False,
    "large_machine_file_hashing": False,
}


@dataclass(frozen=True)
class GateAPreparationRequest:
    """Exact roots for one source-free Task 04C Gate A publication."""

    data_root: Path
    repo_root: Path
    task03j_root: Path | None = None
    gate_a_path: Path | None = None
    review_root: Path | None = None
    output_parent: Path | None = None

    def resolved_task03j_root(self) -> Path:
        """Return the explicit or production Task 03J lineage root."""
        return (self.task03j_root or self.data_root / _TASK03J_RELATIVE).resolve()

    def resolved_gate_a_path(self) -> Path:
        """Return the exact accepted Task 04A source-free census record."""
        return (
            self.gate_a_path
            or self.data_root
            / _REVIEW_RELATIVE
            / TASK04A_GATE_A_ID
            / "records/gate_a_preparation.json"
        ).resolve()

    def resolved_review_root(self) -> Path:
        """Return the exact accepted Task 04A Gate C/D root."""
        return (self.review_root or self.data_root / _REVIEW_RELATIVE / TASK04A_REVIEW_ID).resolve()

    def resolved_output_parent(self) -> Path:
        """Return the separate Task 04C derived namespace parent."""
        return (self.output_parent or self.data_root / _OUTPUT_RELATIVE).resolve()


@dataclass(frozen=True)
class _Inputs:
    """Validated human-review records and their exact byte references."""

    gate_a: JsonObject
    decisions: dict[str, str]
    selection: JsonObject
    freeze: JsonObject
    completion: JsonObject
    ambiguous: JsonObject
    refs: JsonObject


def prepare_and_publish_gate_a(request: GateAPreparationRequest) -> Path:
    """Validate, build, and no-clobber publish source-free Gate A records."""
    _validate_roots(request)
    inputs = _load_and_validate_review_inputs(request)
    machine, candidate_roots = _machine_inventory(request, inputs.gate_a)
    rows, direct = _decision_correspondence(
        inputs.gate_a, inputs.decisions, inputs.selection, candidate_roots
    )
    row_bytes = jsonl_bytes(rows)
    task03j_binding = {
        "production_extraction_id": PRODUCTION_EXTRACTION_ID,
        "scope_id": SCOPE_ID,
        "handoff_id": HANDOFF_ID,
        "handoff_identity_preimage": _mapping(
            _mapping(inputs.gate_a.get("inputs"), "gate_a.inputs").get("task03j"),
            "gate_a.inputs.task03j",
        ).get("handoff_identity_preimage"),
        "candidate_records": machine,
    }
    task04a_binding = {
        "review_run_id": TASK04A_REVIEW_ID,
        "gate_d_completion": inputs.refs["gate_d_completion"],
        "release_freeze": inputs.refs["release_freeze"],
        "toc_review_decisions": inputs.refs["toc_review_decisions"],
        "gate_a_census": inputs.refs["gate_a_preparation"],
        "selection_manifest": inputs.refs["selection_manifest"],
        "usability_registry": inputs.refs["usability_registry"],
        "ambiguous_link_dispositions": inputs.refs["ambiguous_link_dispositions"],
    }
    schema_root = request.repo_root.resolve() / "benchmarks/er_bench/schemas/navigation_overlay/v1"
    schema_refs = [
        file_reference(path, root=request.repo_root.resolve())
        for path in sorted(schema_root.glob("*.schema.json"))
    ]
    _require(len(schema_refs) == 3, "navigation overlay schema bundle is incomplete")
    implementation = _implementation_reference(request.repo_root.resolve())
    correspondence_policy_sha256 = canonical_json_sha256(
        {"correspondence": _POLICY["correspondence"]}
    )
    closure_policy_sha256 = canonical_json_sha256(
        {
            "alias_closure": _POLICY["alias_closure"],
            "link_closure": _POLICY["link_closure"],
        }
    )
    mixed_policy_sha256 = canonical_json_sha256(
        {"mixed_page": _POLICY["mixed_page"], "missing_entity": _POLICY["missing_entity"]}
    )
    preimage: JsonObject = {
        "schema_version": "er_commons.navigation_overlay.v1.identity_preimage",
        "task03j": task03j_binding,
        "task04a": task04a_binding,
        "correspondence_policy_sha256": correspondence_policy_sha256,
        "affected_closure_policy_sha256": closure_policy_sha256,
        "mixed_page_policy_sha256": mixed_policy_sha256,
        "overlay_schema_sha256": canonical_json_sha256(schema_refs),
        "implementation_sha256": implementation["sha256"],
    }
    plan_id = f"navoverlayplanv1-{canonical_json_sha256(preimage)}"
    closure = _affected_closure(
        inputs=inputs,
        candidate_roots=candidate_roots,
        direct=direct,
        task03j_root=request.resolved_task03j_root(),
        plan_id=plan_id,
        closure_policy_sha256=closure_policy_sha256,
    )
    closure_bytes = json_bytes(closure)
    accounting = _gate_a_accounting(rows)
    specification: JsonObject = {
        "schema_version": "er_commons.navigation_overlay.v1.gate_a_specification",
        "overlay_plan_id": plan_id,
        "status": "gate_a_complete",
        "inputs": {"task03j": task03j_binding, "task04a": task04a_binding},
        "identity_preimage": preimage,
        "reproduction": {
            "package_api": "er_commons.navigation_overlay.prepare_and_publish_gate_a",
            "command": "uv run python scripts/prepare_task04c_gate_a.py --repo-root .",
            "arguments": {
                "data_root": "ER_COMMONS_DATA_ROOT",
                "repo_root": ".",
                "task03j_root": _TASK03J_RELATIVE,
                "gate_a_path": inputs.refs["gate_a_preparation"]["path"],
                "review_root": str(
                    Path(cast(str, inputs.refs["release_freeze"]["path"])).parents[1]
                ),
                "output_parent": _OUTPUT_RELATIVE,
            },
        },
        "final_identity_requirements": ["implementation_sha256", "managed_output_digests"],
        "accounting": accounting,
        "source_free_boundary": {
            "source_pdf_bytes_read": False,
            "source_pdf_checksum_recomputed": False,
            "renders_generated": False,
            "model_files_read": False,
            "large_task03j_files_rehashed": False,
            "next_authorization": "gate_b_implementation_without_source_reads",
        },
        "warnings": sorted(
            {
                "mixed pages fail closed and require explicit review"
                for row in rows
                if row["mapping_outcome"] == "mixed_page_insufficient_entity_evidence"
            }
        ),
    }
    _validate_output_schemas(schema_root, rows, closure, specification)
    return _publish(
        request.resolved_output_parent(), plan_id, row_bytes, closure_bytes, specification
    )


def _validate_roots(request: GateAPreparationRequest) -> None:
    """Reject path escapes before reading or publishing any artifact."""
    data_root = request.data_root.resolve()
    if not data_root.is_dir():
        raise FileNotFoundError(data_root)
    for path in (
        request.resolved_task03j_root(),
        request.resolved_gate_a_path(),
        request.resolved_review_root(),
        request.resolved_output_parent(),
    ):
        if not path.is_relative_to(data_root):
            raise ValueError(f"Task 04C path escapes data root: {path}")


def _load_and_validate_review_inputs(request: GateAPreparationRequest) -> _Inputs:
    """Load and byte-bind the exact accepted Task 04A records."""
    review = request.resolved_review_root()
    gate_d = review / "gate_d"
    paths = {
        "gate_a_preparation": request.resolved_gate_a_path(),
        "toc_review_decisions": review / "records/toc_review_decisions.json",
        "selection_manifest": review / "records/selection_manifest.json",
        "release_freeze": gate_d / "release_freeze.json",
        "gate_d_completion": gate_d / "gate_d_completion.json",
        "usability_registry": gate_d / "usability_registry.json",
        "ambiguous_link_dispositions": gate_d / "ambiguous_link_dispositions.json",
    }
    values = {name: read_json_object(path) for name, path in paths.items()}
    refs = {
        name: file_reference(path, root=request.data_root.resolve()) for name, path in paths.items()
    }
    gate_a = values["gate_a_preparation"]
    decisions_record = values["toc_review_decisions"]
    selection = values["selection_manifest"]
    freeze = values["release_freeze"]
    completion = values["gate_d_completion"]
    ambiguous = values["ambiguous_link_dispositions"]
    _require(gate_a.get("review_run_id") == TASK04A_GATE_A_ID, "unexpected Gate A review ID")
    _require(gate_a.get("pass") == "task03j_final", "Gate A pass is not Task 03J final")
    _require(gate_a.get("status") == "source_free_prepared", "Gate A is not prepared")
    boundary = _mapping(gate_a.get("source_free_boundary"), "source_free_boundary")
    for key in ("source_pdf_bytes_read", "renders_generated", "model_files_read"):
        _require(boundary.get(key) is False, f"Gate A violates source-free boundary: {key}")
    _require(selection.get("review_run_id") == TASK04A_REVIEW_ID, "stale selection manifest")
    _require(freeze.get("review_run_id") == TASK04A_REVIEW_ID, "stale release freeze")
    _require(freeze.get("status") == "frozen", "Task 04A release is not frozen")
    _require(completion.get("review_run_id") == TASK04A_REVIEW_ID, "stale Gate D completion")
    _require(completion.get("status") == "complete", "Task 04A Gate D is incomplete")
    _require(completion.get("source_count") == EXPECTED_SOURCE_COUNT, "Gate D source count differs")
    _require(
        completion.get("toc_decision_count") == EXPECTED_DECISION_COUNT,
        "Gate D decision count differs",
    )
    machine = _mapping(freeze.get("machine_candidate"), "release_freeze.machine_candidate")
    _require(
        machine.get("production_extraction_id") == PRODUCTION_EXTRACTION_ID, "wrong extraction"
    )
    _require(machine.get("scope_id") == SCOPE_ID, "wrong scope")
    _require(machine.get("handoff_id") == HANDOFF_ID, "wrong handoff")
    _validate_managed_review_refs(completion, paths, refs)
    decision_ref = _mapping(freeze.get("human_toc_decisions"), "human_toc_decisions")
    _require(
        decision_ref.get("sha256") == refs["toc_review_decisions"]["sha256"],
        "release freeze decision checksum differs",
    )
    entries = _list(decisions_record.get("entries"), "toc_review_decisions.entries")
    decisions: dict[str, str] = {}
    for index, value in enumerate(entries):
        entry = _mapping(value, f"toc_review_decisions.entries[{index}]")
        entry_id = _string(entry.get("entry_id"), f"entries[{index}].entry_id")
        disposition = _string(entry.get("disposition"), f"entries[{index}].disposition")
        _require(disposition in EXPECTED_DECISION_COUNTS, "unsupported TOC disposition")
        _require(entry_id not in decisions, f"duplicate decision: {entry_id}")
        decisions[entry_id] = disposition
    _require(len(decisions) == EXPECTED_DECISION_COUNT, "accepted decision count differs")
    _require(
        dict(Counter(decisions.values())) == EXPECTED_DECISION_COUNTS, "decision totals differ"
    )
    _validate_selection(selection, decisions)
    ambiguous_entries = _list(ambiguous.get("entries"), "ambiguous_link_dispositions.entries")
    _require(
        len(ambiguous_entries) == EXPECTED_AMBIGUOUS_LINK_COUNT,
        "inherited ambiguous-link count differs",
    )
    return _Inputs(gate_a, decisions, selection, freeze, completion, ambiguous, refs)


def _validate_managed_review_refs(
    completion: JsonObject, paths: Mapping[str, Path], refs: Mapping[str, Mapping[str, object]]
) -> None:
    """Require Gate D's declared bytes to match the files consumed now."""
    managed = _mapping(completion.get("managed_records"), "gate_d_completion.managed_records")
    for name in ("release_freeze", "usability_registry", "ambiguous_link_dispositions"):
        declared = _mapping(managed.get(name), f"managed_records.{name}")
        _require(declared.get("sha256") == refs[name]["sha256"], f"changed Gate D record: {name}")
        _require(declared.get("byte_size") == paths[name].stat().st_size, f"changed size: {name}")


def _validate_selection(selection: JsonObject, decisions: Mapping[str, str]) -> None:
    """Require every visible TOC card to remain covered by an accepted decision."""
    visible: set[str] = set()
    for index, value in enumerate(_list(selection.get("items"), "selection_manifest.items")):
        item = _mapping(value, f"selection_manifest.items[{index}]")
        if item.get("queue") not in {"toc_review", "positive_toc"}:
            continue
        population = _mapping(item.get("population"), f"selection item {index}.population")
        visible.add(_string(population.get("candidate_page_id"), "candidate_page_id"))
    _require(len(visible) == 341, "visible TOC card count differs")
    _require(not (visible - decisions.keys()), "visible TOC cards lack decisions")


def _machine_inventory(
    request: GateAPreparationRequest, gate_a: JsonObject
) -> tuple[list[JsonObject], dict[tuple[str, str], Path]]:
    """Reference sealed machine rows from inventories without rehashing their files."""
    task03j = request.resolved_task03j_root()
    document_root = task03j / "document_publications/documents"
    censuses = _list(gate_a.get("toc_candidate_census"), "toc_candidate_census")
    _require(len(censuses) == EXPECTED_SOURCE_COUNT, "Task 04A source census differs")
    machine: list[JsonObject] = []
    roots: dict[tuple[str, str], Path] = {}
    census_pages = 0
    for index, value in enumerate(censuses):
        census = _mapping(value, f"toc_candidate_census[{index}]")
        source_id = _string(census.get("source_id"), f"census[{index}].source_id")
        candidate_id = _string(census.get("candidate_id"), f"census[{index}].candidate_id")
        key = (source_id, candidate_id)
        _require(key not in roots, f"duplicate source candidate: {key}")
        candidate = document_root / source_id / candidate_id
        completion = read_json_object(candidate / "records/completion_record.json")
        identity = read_json_object(candidate / "records/document_identity.json")
        inventory = read_json_object(candidate / "records/artifact_inventory.json")
        _require(completion.get("candidate_id") == candidate_id, "candidate completion differs")
        _require(completion.get("completion_last") is True, "candidate publication is incomplete")
        _require(identity.get("candidate_id") == candidate_id, "candidate identity differs")
        _require(
            identity.get("production_extraction_id") == PRODUCTION_EXTRACTION_ID, "stale candidate"
        )
        source = _mapping(identity.get("source"), "document_identity.source")
        _require(source.get("source_id") == source_id, "candidate source differs")
        candidate_inventory = _mapping(
            completion.get("candidate_inventory"), "completion_record.candidate_inventory"
        )
        _require(
            candidate_inventory.get("sha256")
            == sha256_file(candidate / "records/artifact_inventory.json"),
            "candidate inventory checksum differs",
        )
        sealed = _inventory_subset(inventory, _CANONICAL_FILES)
        stages = _mapping(identity.get("stage_completions"), "document_identity.stage_completions")
        machine.append(
            {
                "source_id": source_id,
                "source_ordinal": census.get("source_ordinal"),
                "candidate_id": candidate_id,
                "candidate_inventory": candidate_inventory,
                "canonical_records": sealed,
                "structured_document_completion": stages.get("structured_document"),
                "hierarchy_completion": stages.get("hierarchy_decisions"),
            }
        )
        roots[key] = candidate
        census_pages += len(_list(census.get("candidate_pages"), "candidate_pages"))
    _require(census_pages == EXPECTED_CENSUS_PAGE_COUNT, "Task 04A page census differs")
    machine.sort(key=lambda row: (int(row["source_ordinal"]), str(row["source_id"])))
    return machine, roots


def _inventory_subset(inventory: JsonObject, wanted: Iterable[str]) -> list[JsonObject]:
    """Select already sealed references without reading or hashing payload bytes."""
    by_path = {
        str(row.get("path")): row
        for row in (
            _mapping(value, "artifact_inventory.files[]")
            for value in _list(inventory.get("files"), "artifact_inventory.files")
        )
    }
    result = []
    for path in wanted:
        _require(path in by_path, f"candidate inventory lacks {path}")
        result.append(dict(by_path[path]))
    return result


def _decision_correspondence(
    gate_a: JsonObject,
    decisions: Mapping[str, str],
    selection: JsonObject,
    candidate_roots: Mapping[tuple[str, str], Path],
) -> tuple[list[JsonObject], dict[tuple[str, str], dict[str, Any]]]:
    """Join every accepted page decision to exact existing canonical entities."""
    page_map: dict[str, tuple[JsonObject, JsonObject]] = {}
    for source_value in _list(gate_a.get("toc_candidate_census"), "toc_candidate_census"):
        source = _mapping(source_value, "toc_candidate_census[]")
        for page_value in _list(source.get("candidate_pages"), "candidate_pages"):
            page = _mapping(page_value, "candidate_pages[]")
            entry_id = _string(page.get("candidate_page_id"), "candidate_page_id")
            candidate_id = _string(source.get("candidate_id"), "candidate_id")
            physical_page = page.get("physical_page")
            _require(isinstance(physical_page, int) and physical_page >= 1, "invalid physical page")
            expected_entry_id = (
                "tocpagev1-"
                + sha256_bytes(
                    json.dumps(
                        {"candidate_id": candidate_id, "physical_page": physical_page},
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                )[:24]
            )
            _require(entry_id == expected_entry_id, f"stale candidate page ID: {entry_id}")
            _require(entry_id not in page_map, f"duplicate census page ID: {entry_id}")
            page_map[entry_id] = (source, page)
    _require(not (decisions.keys() - page_map.keys()), "decisions are absent from Gate A census")
    by_candidate: dict[tuple[str, str], list[tuple[str, str, JsonObject]]] = defaultdict(list)
    for entry_id, disposition in decisions.items():
        source, page = page_map[entry_id]
        key = (
            _string(source.get("source_id"), "source_id"),
            _string(source.get("candidate_id"), "candidate_id"),
        )
        by_candidate[key].append((entry_id, disposition, page))
    rows: list[JsonObject] = []
    direct: dict[tuple[str, str], dict[str, Any]] = {}
    for key in sorted(by_candidate):
        candidate = candidate_roots[key]
        wanted_pages = {
            _string(page.get("page_id"), "page_id"): (entry_id, disposition, page)
            for entry_id, disposition, page in by_candidate[key]
        }
        canonical = candidate / "content/canonical"
        page_rows = {
            str(row["id"]): row
            for row in iter_jsonl(canonical / "pages.jsonl")
            if row.get("id") in wanted_pages
        }
        _require(page_rows.keys() == wanted_pages.keys(), f"canonical pages differ for {key[0]}")
        entities: dict[str, list[JsonObject]] = defaultdict(list)
        for family in ("block", "table"):
            for record in iter_jsonl(canonical / f"{family}s.jsonl"):
                for page_id in _record_page_ids(record) & wanted_pages.keys():
                    entities[page_id].append(
                        {
                            "record_id": record.get("id"),
                            "record_type": family,
                            "section_id": record.get("section_id"),
                            "semantic_placement": record.get("semantic_placement"),
                            "is_toc_row": record.get("is_toc_row"),
                        }
                    )
        for page_id, (entry_id, disposition, page) in wanted_pages.items():
            content = sorted(entities.get(page_id, []), key=lambda row: str(row["record_id"]))
            explicitly_mixed = page.get("page_role") == "mixed" or page.get("mixed") is True
            if explicitly_mixed:
                outcome = "mixed_page_insufficient_entity_evidence"
                reason = "explicit mixed-page evidence requires later entity-level review"
                mapped_content: list[JsonObject] = []
            elif not content:
                outcome = "no_existing_entity_evidence"
                reason = "the accepted page has no existing canonical block table or section"
                mapped_content = []
            else:
                outcome = "mapped"
                reason = "existing page-resident canonical entities map uniquely"
                mapped_content = content
            machine_navigation = any(
                signal in {"canonical_toc_block", "canonical_toc_placement"}
                for signal in cast(list[str], page.get("signals", []))
            )
            by_kind = {
                "blocks": sorted(
                    str(item["record_id"])
                    for item in mapped_content
                    if item["record_type"] == "block"
                ),
                "tables": sorted(
                    str(item["record_id"])
                    for item in mapped_content
                    if item["record_type"] == "table"
                ),
                "sections": sorted(
                    {str(item["section_id"]) for item in mapped_content if item.get("section_id")}
                ),
            }
            navigation_content = [
                item
                for item in mapped_content
                if item["is_toc_row"] is True or item["semantic_placement"] == "toc_content"
            ]
            navigation_by_kind = {
                "blocks": sorted(
                    str(item["record_id"])
                    for item in navigation_content
                    if item["record_type"] == "block"
                ),
                "tables": sorted(
                    str(item["record_id"])
                    for item in navigation_content
                    if item["record_type"] == "table"
                ),
                "sections": sorted(
                    {
                        str(item["section_id"])
                        for item in navigation_content
                        if item.get("section_id")
                    }
                ),
            }
            row = {
                "schema_version": "er_commons.navigation_overlay.v1.decision_correspondence",
                "decision_entry_id": entry_id,
                "disposition": disposition,
                "source_id": key[0],
                "candidate_id": key[1],
                "physical_page": page.get("physical_page"),
                "page_id": page_id,
                "machine_navigation": machine_navigation,
                "machine_signals": sorted(set(cast(list[str], page.get("signals", [])))),
                "decision_origin_class": "accepted_nonvisible_origin_not_preserved",
                "visible_review_item_id": None,
                "c17_positive_suffix_evidence": None,
                "entity_ids_by_kind": by_kind,
                "mapping_outcome": outcome,
                "reason": reason,
            }
            rows.append(row)
            direct[(key[0], page_id)] = {
                "decision_entry_id": entry_id,
                "disposition": disposition,
                "candidate_id": key[1],
                "physical_page": page.get("physical_page"),
                "machine_navigation": machine_navigation,
                "mapping_outcome": outcome,
                "entity_ids_by_kind": by_kind,
                "navigation_entity_ids_by_kind": navigation_by_kind,
                "entity_ids": {str(entity["record_id"]) for entity in mapped_content},
                "section_ids": {
                    str(entity["section_id"])
                    for entity in mapped_content
                    if entity.get("section_id")
                },
            }
    # Selection identities are applied after canonical joins so review provenance
    # cannot influence entity correspondence.
    visible, suffix_evidence = _selection_origins(selection)
    for row in rows:
        entry_id = str(row["decision_entry_id"])
        if entry_id in visible:
            row["decision_origin_class"] = "visible_c17_card"
            row["visible_review_item_id"] = visible[entry_id]
        if entry_id in suffix_evidence:
            row["c17_positive_suffix_evidence"] = suffix_evidence[entry_id]
    rows.sort(
        key=lambda row: (
            str(row["source_id"]),
            int(row["physical_page"]),
            str(row["decision_entry_id"]),
        )
    )
    _require(len(rows) == EXPECTED_DECISION_COUNT, "correspondence does not cover all decisions")
    return rows, direct


def _selection_origins(selection: JsonObject) -> tuple[dict[str, str], dict[str, JsonObject]]:
    """Map visible cards and positive-run suffixes to accepted decision IDs."""
    visible: dict[str, str] = {}
    suffix: dict[str, JsonObject] = {}
    for value in _list(selection.get("items"), "selection_manifest.items"):
        item = _mapping(value, "selection_manifest.items[]")
        if item.get("queue") not in {"toc_review", "positive_toc"}:
            continue
        population = _mapping(item.get("population"), "selection item population")
        entry_id = _string(population.get("candidate_page_id"), "candidate_page_id")
        review_item_id = _string(item.get("review_item_id"), "review_item_id")
        visible[entry_id] = review_item_id
        run = population.get("positive_run")
        if not isinstance(run, dict):
            continue
        evidence = {
            "review_item_id": review_item_id,
            "run_start_page": int(run["start_page"]),
            "run_end_page": int(run["end_page"]),
        }
        for suffix_id in cast(list[str], run.get("suffix_entry_ids", [])):
            suffix[suffix_id] = evidence
    return visible, suffix


def _gate_a_accounting(rows: list[JsonObject]) -> JsonObject:
    """Return the exact accepted review and machine-disagreement accounting."""
    visible = sum(row["decision_origin_class"] == "visible_c17_card" for row in rows)
    newly_confirmed = sum(
        row["disposition"] == "toc" and row["machine_navigation"] is False for row in rows
    )
    rejected = sum(
        row["disposition"] == "not_toc" and row["machine_navigation"] is True for row in rows
    )
    _require(visible == 341, "visible decision accounting differs")
    _require(newly_confirmed == 15, "newly confirmed navigation accounting differs")
    _require(rejected == 391, "rejected machine navigation accounting differs")
    disagreement = newly_confirmed + rejected
    return {
        "source_count": EXPECTED_SOURCE_COUNT,
        "census_page_count": EXPECTED_CENSUS_PAGE_COUNT,
        "decision_count": len(rows),
        "toc_decision_count": EXPECTED_DECISION_COUNTS["toc"],
        "not_toc_decision_count": EXPECTED_DECISION_COUNTS["not_toc"],
        "visible_decision_count": visible,
        "nonvisible_decision_count": len(rows) - visible,
        "machine_human_agreement_count": len(rows) - disagreement,
        "machine_human_disagreement_count": disagreement,
        "newly_confirmed_navigation_count": newly_confirmed,
        "rejected_machine_navigation_count": rejected,
        "inherited_ambiguous_link_count": EXPECTED_AMBIGUOUS_LINK_COUNT,
    }


def _affected_closure(
    *,
    inputs: _Inputs,
    candidate_roots: Mapping[tuple[str, str], Path],
    direct: Mapping[tuple[str, str], dict[str, Any]],
    task03j_root: Path,
    plan_id: str,
    closure_policy_sha256: str,
) -> JsonObject:
    """Census conservative alias and local/collection-link dependencies."""
    by_source: dict[str, JsonObject] = {}
    affected_alias_ids: set[str] = set()
    affected_target_ids: set[str] = set()
    affected_reference_ids: set[str] = set()
    material_seeds: list[JsonObject] = []
    material_pages = {
        (source_id, page_id)
        for (source_id, page_id), facts in direct.items()
        if bool(facts["machine_navigation"]) != (facts["disposition"] == "toc")
    }
    for source_id, page_id in sorted(material_pages):
        facts = direct[(source_id, page_id)]
        entity_ids = (
            facts["entity_ids_by_kind"]
            if facts["disposition"] == "toc"
            else facts["navigation_entity_ids_by_kind"]
        )
        mapping_outcome = facts["mapping_outcome"]
        if not any(entity_ids.values()):
            mapping_outcome = "no_existing_entity_evidence"
        material_seeds.append(
            {
                "decision_entry_id": facts["decision_entry_id"],
                "source_id": source_id,
                "candidate_id": facts["candidate_id"],
                "page_id": page_id,
                "physical_page": facts["physical_page"],
                "change_kind": (
                    "newly_confirmed_navigation"
                    if facts["disposition"] == "toc"
                    else "rejected_machine_navigation"
                ),
                "entity_ids_by_kind": entity_ids,
                "mapping_outcome": mapping_outcome,
            }
        )
    for (source_id, candidate_id), candidate in sorted(candidate_roots.items()):
        pages = {page_id for source, page_id in material_pages if source == source_id}
        if not pages:
            continue
        entity_ids = set().union(*(direct[(source_id, page)]["entity_ids"] for page in pages))
        v2_alias_ids, v2_targets = _visible_toc_alias_provenance(
            candidate,
            source_id,
            {int(direct[(source_id, page)]["physical_page"]) for page in pages},
            task03j_root,
        )
        aliases: list[JsonObject] = []
        for alias in iter_jsonl(candidate / "content/canonical/target_aliases.jsonl"):
            reasons: list[str] = []
            if alias.get("upstream_alias_id") in v2_alias_ids:
                reasons.append("visible_toc_reconciliation_on_decision_page")
            for target in cast(list[JsonObject], alias.get("targets", [])):
                if target.get("evidence_page_id") in pages:
                    reasons.append("alias_evidence_on_decision_page")
                if target.get("evidence_source_record_id") in entity_ids:
                    reasons.append("alias_source_entity_on_decision_page")
            if reasons:
                aliases.append(
                    {
                        "alias_id": alias["id"],
                        "reasons": sorted(set(reasons)),
                        "upstream_alias_id": alias.get("upstream_alias_id"),
                    }
                )
                affected_alias_ids.add(str(alias["id"]))
                affected_target_ids.update(
                    str(t.get("target_id"))
                    for t in cast(list[JsonObject], alias.get("targets", []))
                )
        affected_target_ids.update(v2_targets)
        references: list[JsonObject] = []
        for reference in iter_jsonl(candidate / "content/canonical/cross_references.jsonl"):
            reasons = []
            if (
                reference.get("source_record_id") in entity_ids
                or _record_page_ids(reference) & pages
            ):
                reasons.append("mention_source_on_decision_page")
            candidate_aliases = set(
                _nested_strings(reference.get("candidates"), "alias_record_ids")
            )
            candidate_targets = set(
                _nested_strings(reference.get("candidates"), "target_record_id")
            )
            if candidate_aliases & affected_alias_ids:
                reasons.append("candidate_uses_affected_alias")
            if candidate_targets & affected_target_ids:
                reasons.append("candidate_uses_affected_target")
            if reasons:
                references.append(
                    {
                        "reference_id": reference["id"],
                        "status": reference.get("resolution_status"),
                        "reasons": sorted(set(reasons)),
                    }
                )
                affected_reference_ids.add(str(reference["id"]))
        by_source[source_id] = {"candidate_id": candidate_id}
    collection = _collection_closure(
        task03j_root, affected_reference_ids, affected_alias_ids, affected_target_ids
    )
    all_ambiguous_ids = sorted(
        _string(_mapping(value, "ambiguous entries[]").get("reference_id"), "reference_id")
        for value in _list(inputs.ambiguous.get("entries"), "ambiguous entries")
    )
    in_closure = sorted(set(all_ambiguous_ids) & affected_reference_ids)
    outside = sorted(set(all_ambiguous_ids) - affected_reference_ids)
    affected_entity_ids = {
        entity
        for seed in material_seeds
        for ids in cast(dict[str, list[str]], seed["entity_ids_by_kind"]).values()
        for entity in ids
    }
    return {
        "schema_version": "er_commons.navigation_overlay.v1.affected_closure",
        "overlay_plan_id": plan_id,
        "status": "complete",
        "closure_policy_sha256": closure_policy_sha256,
        "closure_rules": [
            "page_resident_navigation_entities_on_machine_human_disagreement_pages",
            "aliases_owned_or_derived_from_affected_entities",
            "links_touching_affected_reference_alias_or_target_entities",
            "collection_resolutions_referencing_affected_links",
        ],
        "affected_source_ids": sorted(by_source),
        "affected_page_ids": sorted(page_id for _, page_id in material_pages),
        "material_seeds": material_seeds,
        "affected_alias_ids": sorted(affected_alias_ids),
        "affected_link_ids": sorted(affected_reference_ids),
        "affected_collection_resolution_ids": sorted(
            str(row["mention_id"]) for row in cast(list[JsonObject], collection["resolutions"])
        ),
        "inherited_ambiguous_links": {
            "all_ids": all_ambiguous_ids,
            "in_closure_ids": in_closure,
            "outside_closure_ids": outside,
            "default_disposition": "unresolved_unless_unique_entity_level_evidence",
        },
        "accounting": {
            "material_seed_count": len(material_seeds),
            "affected_source_count": len(by_source),
            "affected_page_count": len(material_pages),
            "affected_entity_count": len(affected_entity_ids),
            "affected_alias_count": len(affected_alias_ids),
            "affected_link_count": len(affected_reference_ids),
            "affected_collection_resolution_count": len(collection["resolutions"]),
            "inherited_ambiguous_link_count": len(all_ambiguous_ids),
            "inherited_ambiguous_link_in_closure_count": len(in_closure),
            "inherited_ambiguous_link_outside_closure_count": len(outside),
        },
    }


def _visible_toc_alias_provenance(
    candidate: Path, source_id: str, physical_pages: set[int], task03j_root: Path
) -> tuple[set[str], set[str]]:
    """Trace final aliases back to exact sealed v2 visible-TOC evidence."""
    identity = read_json_object(candidate / "records/document_identity.json")
    stages = _mapping(identity.get("stage_completions"), "stage_completions")
    structured_ref = _mapping(stages.get("structured_document"), "structured_document")
    structured_completion = (
        task03j_root.parent.parent.parent / str(structured_ref["path"])
    ).resolve()
    # Stage references are rooted at ER_COMMONS_DATA_ROOT, three levels above Task 03J.
    if not structured_completion.is_file():
        data_root = task03j_root.parents[2]
        structured_completion = (data_root / str(structured_ref["path"])).resolve()
    structured_root = structured_completion.parent.parent
    extraction_identity = read_json_object(structured_root / "records/extraction_identity.json")
    hierarchy = _mapping(extraction_identity.get("hierarchy_correction"), "hierarchy_correction")
    hierarchy_completion_ref = _mapping(hierarchy.get("completion"), "hierarchy completion")
    data_root = task03j_root.parents[2]
    hierarchy_completion = (data_root / str(hierarchy_completion_ref["path"])).resolve()
    hierarchy_root = hierarchy_completion.parent.parent
    visible = {
        str(row["toc_entry_id"]): row
        for row in iter_jsonl(hierarchy_root / "artifacts/visible_toc_entries.jsonl")
        if row.get("physical_page") in physical_pages
    }
    reconciliations = {
        str(row["toc_entry_id"]): row
        for row in iter_jsonl(hierarchy_root / "artifacts/toc_reconciliation.jsonl")
        if str(row.get("toc_entry_id")) in visible
    }
    sections_by_key = {
        str(row.get("source_stable_item_key")): str(row["id"])
        for row in iter_jsonl(structured_root / "canonical/sections.jsonl")
        if row.get("source_stable_item_key") is not None
    }
    matched_targets = {
        sections_by_key[str(row["target_key"])]
        for row in reconciliations.values()
        if row.get("state") == "exact" and str(row.get("target_key")) in sections_by_key
    }
    alias_ids: set[str] = set()
    for alias in iter_jsonl(structured_root / "canonical/target_aliases.jsonl"):
        if any(
            target.get("evidence_kind") == "visible_toc_reconciliation"
            and target.get("target_id") in matched_targets
            for target in cast(list[JsonObject], alias.get("targets", []))
        ):
            alias_ids.add(str(alias["id"]))
    return alias_ids, matched_targets


def _collection_closure(
    task03j_root: Path,
    reference_ids: set[str],
    alias_ids: set[str],
    target_ids: set[str],
) -> JsonObject:
    """Use the exact handoff-pinned collection index and resolution IDs."""
    scope = task03j_root / "document_publications/scopes" / SCOPE_ID
    handoff_path = scope / "handoffs" / HANDOFF_ID / "records/completion_record.json"
    handoff = read_json_object(handoff_path)
    _require(handoff.get("handoff_id") == HANDOFF_ID, "collection handoff differs")
    index_id = _string(handoff.get("index_id"), "handoff.index_id")
    resolution_id = _string(handoff.get("resolution_id"), "handoff.resolution_id")
    index_root = scope / "target_indexes" / index_id
    resolution_root = scope / "resolutions" / resolution_id
    index_entries = []
    for row in iter_jsonl(index_root / "target_index.jsonl"):
        if row.get("alias_id") in alias_ids or row.get("target_id") in target_ids:
            index_entries.append(
                {
                    "alias_id": row.get("alias_id"),
                    "target_id": row.get("target_id"),
                    "lookup_key": row.get("lookup_key"),
                }
            )
    resolutions = []
    for row in iter_jsonl(resolution_root / "resolutions.jsonl"):
        strings = set(_all_strings(row.get("candidate_targets")))
        reasons = []
        if row.get("mention_id") in reference_ids:
            reasons.append("affected_mention")
        if strings & (alias_ids | target_ids):
            reasons.append("affected_candidate_target")
        if reasons:
            resolutions.append(
                {
                    "mention_id": row.get("mention_id"),
                    "status": row.get("status"),
                    "reasons": reasons,
                }
            )
    return {
        "index_id": index_id,
        "resolution_id": resolution_id,
        "index_completion_ref": handoff.get("index_completion_ref"),
        "resolution_completion_ref": handoff.get("resolution_completion_ref"),
        "target_index_entries": sorted(
            index_entries, key=lambda row: (str(row["alias_id"]), str(row["target_id"]))
        ),
        "resolutions": sorted(resolutions, key=lambda row: str(row["mention_id"])),
    }


def _publish(
    output_parent: Path,
    plan_id: str,
    row_bytes: bytes,
    closure_bytes: bytes,
    specification: JsonObject,
) -> Path:
    """Publish completion-last through a fresh directory rename."""
    final = output_parent / plan_id
    if final.exists():
        expected = {
            "decision_correspondence.jsonl": row_bytes,
            "affected_closure.json": closure_bytes,
            "gate_a_specification.json": json_bytes(specification),
            "records/identity_preimage.json": json_bytes(specification["identity_preimage"]),
        }
        for relative, content in expected.items():
            path = final / relative
            if not path.is_file() or path.read_bytes() != content:
                raise FileExistsError(f"refusing to reuse changed Task 04C plan artifact: {path}")
        inventory_path = final / "records/artifact_inventory.json"
        completion_path = final / "records/completion_record.json"
        existing_inventory = read_json_object(inventory_path)
        actual_inventory = artifact_inventory(
            final, {"records/artifact_inventory.json", "records/completion_record.json"}
        )
        if existing_inventory != actual_inventory:
            raise FileExistsError(f"refusing to reuse changed Task 04C plan inventory: {final}")
        completion = read_json_object(completion_path)
        if completion.get("status") != "complete" or completion.get(
            "artifact_inventory_sha256"
        ) != sha256_bytes(json_bytes(existing_inventory)):
            raise FileExistsError(f"refusing to reuse incomplete Task 04C plan: {final}")
        return final
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{plan_id}.", dir=output_parent))
    try:
        (staging / "decision_correspondence.jsonl").write_bytes(row_bytes)
        (staging / "affected_closure.json").write_bytes(closure_bytes)
        (staging / "gate_a_specification.json").write_bytes(json_bytes(specification))
        records = staging / "records"
        records.mkdir()
        (records / "identity_preimage.json").write_bytes(
            json_bytes(specification["identity_preimage"])
        )
        inventory = artifact_inventory(
            staging, {"records/artifact_inventory.json", "records/completion_record.json"}
        )
        (records / "artifact_inventory.json").write_bytes(json_bytes(inventory))
        completion = {
            "schema_version": "er_commons.navigation_overlay_gate_a_completion.v1",
            "plan_id": plan_id,
            "status": "complete",
            "artifact_inventory_sha256": sha256_bytes(json_bytes(inventory)),
            "completion_last": True,
        }
        (records / "completion_record.json").write_bytes(json_bytes(completion))
        os.rename(staging, final)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return final


def _implementation_reference(repo_root: Path) -> JsonObject:
    """Bind the package implementation that defines this plan."""
    paths = (
        repo_root / "src/er_commons/navigation_overlay/__init__.py",
        repo_root / "src/er_commons/navigation_overlay/preparation.py",
        repo_root / "scripts/prepare_task04c_gate_a.py",
    )
    refs = [file_reference(path, root=repo_root) for path in paths]
    return {"files": refs, "sha256": canonical_json_sha256(refs)}


def _validate_output_schemas(
    schema_root: Path,
    rows: list[JsonObject],
    closure: JsonObject,
    specification: JsonObject,
) -> None:
    """Validate every emitted semantic record before creating its namespace."""
    schemas = {
        "decision_correspondence": read_json_object(
            schema_root / "decision_correspondence_row.schema.json"
        ),
        "affected_closure": read_json_object(schema_root / "affected_closure.schema.json"),
        "gate_a_specification": read_json_object(schema_root / "gate_a_specification.schema.json"),
    }
    row_validator = Draft202012Validator(schemas["decision_correspondence"])
    for index, row in enumerate(rows):
        errors = sorted(row_validator.iter_errors(row), key=lambda error: list(error.path))
        if errors:
            raise ValueError(f"invalid correspondence row {index}: {errors[0].message}")
    for name, record in (
        ("affected_closure", closure),
        ("gate_a_specification", specification),
    ):
        errors = sorted(
            Draft202012Validator(schemas[name]).iter_errors(record),
            key=lambda error: list(error.path),
        )
        if errors:
            location = ".".join(str(part) for part in errors[0].absolute_path) or "<root>"
            raise ValueError(f"invalid {name} at {location}: {errors[0].message}")


def _record_page_ids(record: Mapping[str, Any]) -> set[str]:
    return {
        str(region["page_id"])
        for value in cast(list[Any], record.get("regions", []))
        if isinstance(value, dict)
        for region in [cast(dict[str, Any], value)]
        if isinstance(region.get("page_id"), str)
    }


def _nested_strings(value: Any, key: str) -> Iterator[str]:
    if isinstance(value, dict):
        for name, child in value.items():
            if name == key:
                if isinstance(child, str):
                    yield child
                elif isinstance(child, list):
                    yield from (item for item in child if isinstance(item, str))
            yield from _nested_strings(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_strings(child, key)


def _all_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _all_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_strings(child)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _mapping(value: Any, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"expected object at {path}")
    return cast(JsonObject, value)


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"expected array at {path}")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"expected non-empty string at {path}")
    return value


__all__ = ["GateAPreparationRequest", "prepare_and_publish_gate_a"]
