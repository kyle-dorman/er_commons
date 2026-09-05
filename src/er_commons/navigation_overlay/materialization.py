"""Materialize and read the source-free Task 04C Gate B semantic view."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
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

ACCEPTED_GATE_A_ID = (
    "navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741"
)
EXPECTED_DECISION_COUNT = 757
EXPECTED_AGREEMENT_COUNT = 351
EXPECTED_DISAGREEMENT_COUNT = 406
EXPECTED_CONFIRMED_ENTITY_COUNT = 72
EXPECTED_REJECTED_ENTITY_COUNT = 5_728
EXPECTED_BLOCK_DISPOSITION_COUNT = 5_785
EXPECTED_TABLE_DISPOSITION_COUNT = 15
EXPECTED_CONTEXT_SECTION_COUNT = 23

_TASK03J_RELATIVE = "pipelines/brisbane_baylands/task_03h_clean_full_v4"
_OUTPUT_RELATIVE = "pipelines/brisbane_baylands/task_04_navigation_overlay"
_GATE_B_SCHEMA_RELATIVE = "benchmarks/er_bench/schemas/navigation_overlay/v1/gate_b"
_SEMANTIC_RULES = [
    "human_toc_confirms_existing_mapped_blocks_and_tables_as_navigation",
    "human_not_toc_excludes_only_existing_mapped_machine_navigation_blocks_and_tables",
    "machine_human_agreements_are_immutable_read_through",
    "original_machine_placement_is_preserved_as_provenance",
    "section_associations_are_preserved_as_context_not_semantic_dispositions",
    "mixed_missing_conflicting_or_entityless_decisions_leave_machine_semantics_unchanged",
    "page_labels_never_create_entities_aliases_targets_or_links",
]
_POLICY: JsonObject = {
    "schema_version": "er_commons.navigation_overlay.v1.semantic_policy",
    "confirmed_navigation": "all_existing_mapped_blocks_and_tables",
    "rejected_machine_navigation": (
        "existing_mapped_blocks_and_tables_with_machine_toc_semantics_only"
    ),
    "sections": "context_only_never_reclassified",
    "unspecified_entities": "inherit_machine_navigation",
    "mixed_missing_conflicting_or_entityless": "fail_closed_inherit_machine_navigation",
    "machine_provenance": "preserve_without_mutation",
    "aliases_targets_links": "deferred_to_gate_c",
}
_SOURCE_FREE_BOUNDARY = {
    "source_pdf_bytes_read": False,
    "source_pdf_checksum_recomputed": False,
    "renders_generated": False,
    "model_files_read": False,
    "large_task03j_files_rehashed": False,
    "task03j_files_written": False,
    "task04a_files_written": False,
}


@dataclass(frozen=True)
class GateBMaterializationRequest:
    """Exact roots for one source-free Gate B semantic publication."""

    data_root: Path
    repo_root: Path
    gate_a_root: Path | None = None
    task03j_root: Path | None = None
    output_parent: Path | None = None

    def resolved_gate_a_root(self) -> Path:
        """Return the explicitly accepted Gate A namespace."""
        return (
            self.gate_a_root or self.data_root / _OUTPUT_RELATIVE / ACCEPTED_GATE_A_ID
        ).resolve()

    def resolved_task03j_root(self) -> Path:
        """Return the sealed Task 03J production root."""
        return (self.task03j_root or self.data_root / _TASK03J_RELATIVE).resolve()

    def resolved_output_parent(self) -> Path:
        """Return the Task 04C publication parent."""
        return (self.output_parent or self.data_root / _OUTPUT_RELATIVE).resolve()


@dataclass(frozen=True)
class _GateAInputs:
    """Validated compact Gate A records and exact references."""

    specification: JsonObject
    correspondence: list[JsonObject]
    refs: JsonObject


@dataclass(frozen=True)
class _CanonicalEntity:
    """Machine provenance required to apply one sparse semantic override."""

    source_id: str
    candidate_id: str
    entity_kind: str
    entity_id: str
    page_ids: frozenset[str]
    section_id: str | None
    semantic_placement: str
    is_toc_row: bool

    @property
    def machine_navigation(self) -> bool:
        """Return the canonical machine navigation interpretation."""
        return self.is_toc_row or self.semantic_placement == "toc_content"


@dataclass
class _PendingDisposition:
    """Aggregate same-action evidence for one unique canonical entity."""

    entity: _CanonicalEntity
    effective_navigation: bool
    decision_evidence: list[JsonObject]


def prepare_and_publish_gate_b(request: GateBMaterializationRequest) -> Path:
    """Validate Gate A, derive sparse dispositions, and publish completion-last."""
    _validate_roots(request)
    inputs = _load_and_validate_gate_a(request)
    entities = _load_bound_canonical_entities(request, inputs)
    applications, dispositions, context_sections = _materialize_semantic_view(
        inputs.correspondence, entities, semantic_view_id=None
    )
    accounting = _accounting(applications, dispositions)
    _validate_production_accounting(accounting, context_sections)

    schema_root = request.repo_root.resolve() / _GATE_B_SCHEMA_RELATIVE
    schema_refs = [
        file_reference(path, root=request.repo_root.resolve())
        for path in sorted(schema_root.glob("*.schema.json"))
    ]
    _require(len(schema_refs) == 4, "Gate B schema bundle is incomplete")
    implementation = _implementation_reference(request.repo_root.resolve())
    preimage = {
        "schema_version": "er_commons.navigation_overlay.v1.semantic_identity_preimage",
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
        "gate_a_completion_sha256": inputs.refs["gate_a_completion"]["sha256"],
        "gate_a_inventory_sha256": inputs.refs["gate_a_inventory"]["sha256"],
        "semantic_policy_sha256": canonical_json_sha256(_POLICY),
        "schema_bundle_sha256": canonical_json_sha256(schema_refs),
        "implementation_sha256": implementation["sha256"],
    }
    semantic_view_id = f"navsemanticv1-{canonical_json_sha256(preimage)}"
    applications, dispositions, context_sections = _materialize_semantic_view(
        inputs.correspondence, entities, semantic_view_id=semantic_view_id
    )
    specification: JsonObject = {
        "schema_version": "er_commons.navigation_overlay.v1.gate_b_specification",
        "semantic_view_id": semantic_view_id,
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
        "status": "gate_b_complete",
        "inputs": {
            "gate_a_specification": inputs.refs["gate_a_specification"],
            "gate_a_completion": inputs.refs["gate_a_completion"],
            "gate_a_inventory": inputs.refs["gate_a_inventory"],
            "decision_correspondence": inputs.refs["decision_correspondence"],
            "affected_closure": inputs.refs["affected_closure"],
        },
        "identity_preimage": preimage,
        "semantic_rules": _SEMANTIC_RULES,
        "accounting": accounting,
        "reproduction": {
            "package_api": (
                "er_commons.navigation_overlay.materialization.prepare_and_publish_gate_b"
            ),
            "command": "uv run python scripts/materialize_task04c_gate_b.py --repo-root .",
            "arguments": {
                "data_root": "ER_COMMONS_DATA_ROOT",
                "repo_root": ".",
                "gate_a_root": f"{_OUTPUT_RELATIVE}/{ACCEPTED_GATE_A_ID}",
                "output_parent": _OUTPUT_RELATIVE,
            },
        },
        "source_free_boundary": _SOURCE_FREE_BOUNDARY,
        "warnings": [],
    }
    _validate_output_schemas(schema_root, applications, dispositions, specification)
    return _publish(
        request.resolved_output_parent(),
        semantic_view_id,
        applications,
        dispositions,
        specification,
        accounting,
        schema_root,
    )


class EffectiveNavigationView:
    """Validated sparse semantic overrides over immutable machine navigation."""

    def __init__(self, publication: Path) -> None:
        """Load a complete Gate B publication and reject changed managed bytes."""
        self.publication = publication.resolve()
        _validate_published_namespace(self.publication)
        rows = list(iter_jsonl(self.publication / "semantic_dispositions.jsonl"))
        by_entity: dict[str, bool] = {}
        for row in rows:
            entity_id = _string(row.get("entity_id"), "semantic disposition entity_id")
            _require(
                row.get("semantic_view_id") == self.publication.name,
                f"semantic disposition view differs: {entity_id}",
            )
            _require(
                row.get("overlay_plan_id") == ACCEPTED_GATE_A_ID,
                f"semantic disposition plan differs: {entity_id}",
            )
            disposition = row.get("disposition")
            machine = row.get("machine_navigation")
            effective = row.get("effective_navigation")
            valid_relation = (disposition, machine, effective) in {
                ("human_confirmed_navigation", False, True),
                ("human_rejected_machine_navigation", True, False),
            }
            _require(valid_relation, f"invalid semantic disposition relation: {entity_id}")
            _require(entity_id not in by_entity, f"duplicate semantic disposition: {entity_id}")
            by_entity[entity_id] = cast(bool, effective)
        self._by_entity = by_entity

    def effective_navigation(self, entity_id: str, *, machine_navigation: bool) -> bool:
        """Return an override when present, otherwise inherit the machine value."""
        return self._by_entity.get(entity_id, machine_navigation)

    def has_override(self, entity_id: str) -> bool:
        """Return whether Gate B explicitly overrides this existing entity."""
        return entity_id in self._by_entity


def _validate_roots(request: GateBMaterializationRequest) -> None:
    """Reject stale identity selection and all paths outside the artifact root."""
    data_root = request.data_root.resolve()
    _require(data_root.is_dir(), f"data root is not a directory: {data_root}")
    _require(
        request.resolved_gate_a_root().name == ACCEPTED_GATE_A_ID,
        "Gate B requires the accepted Gate A overlay plan",
    )
    for path in (
        request.resolved_gate_a_root(),
        request.resolved_task03j_root(),
        request.resolved_output_parent(),
    ):
        _require(path.is_relative_to(data_root), f"Task 04C path escapes data root: {path}")


def _load_and_validate_gate_a(request: GateBMaterializationRequest) -> _GateAInputs:
    """Bind every compact Gate A record before reading machine entities."""
    root = request.resolved_gate_a_root()
    paths = {
        "gate_a_specification": root / "gate_a_specification.json",
        "gate_a_completion": root / "records/completion_record.json",
        "gate_a_inventory": root / "records/artifact_inventory.json",
        "decision_correspondence": root / "decision_correspondence.jsonl",
        "affected_closure": root / "affected_closure.json",
    }
    refs = {name: file_reference(path, root=request.data_root) for name, path in paths.items()}
    inventory = read_json_object(paths["gate_a_inventory"])
    actual_inventory = artifact_inventory(
        root, {"records/artifact_inventory.json", "records/completion_record.json"}
    )
    _require(inventory == actual_inventory, "changed Gate A managed artifact inventory")
    completion = read_json_object(paths["gate_a_completion"])
    _require(completion.get("plan_id") == ACCEPTED_GATE_A_ID, "stale Gate A completion")
    _require(completion.get("status") == "complete", "Gate A is incomplete")
    _require(completion.get("completion_last") is True, "Gate A was not completion-last")
    _require(
        completion.get("artifact_inventory_sha256") == sha256_bytes(json_bytes(inventory)),
        "Gate A completion does not bind its inventory",
    )
    specification = read_json_object(paths["gate_a_specification"])
    closure = read_json_object(paths["affected_closure"])
    _require(
        specification.get("overlay_plan_id") == ACCEPTED_GATE_A_ID,
        "stale Gate A specification",
    )
    _require(specification.get("status") == "gate_a_complete", "Gate A status differs")
    _require(
        read_json_object(root / "records/identity_preimage.json")
        == specification.get("identity_preimage"),
        "Gate A identity preimage differs",
    )
    _require_derived_identity(
        "navoverlayplanv1-",
        specification["identity_preimage"],
        ACCEPTED_GATE_A_ID,
        "Gate A",
    )
    correspondence = list(iter_jsonl(paths["decision_correspondence"]))
    _validate_gate_a_schemas(request.repo_root.resolve(), specification, closure, correspondence)
    _require(len(correspondence) == EXPECTED_DECISION_COUNT, "Gate A decision count differs")
    decision_ids = [
        _string(row.get("decision_entry_id"), "decision_entry_id") for row in correspondence
    ]
    _require(len(set(decision_ids)) == len(decision_ids), "duplicate Gate A decision")
    expected = cast(Mapping[str, Any], specification.get("accounting"))
    _require(expected.get("decision_count") == len(correspondence), "Gate A accounting differs")
    _require(expected.get("machine_human_agreement_count") == 351, "Gate A agreement differs")
    _require(expected.get("machine_human_disagreement_count") == 406, "Gate A disagreement differs")
    disagreement = {
        _string(row.get("decision_entry_id"), "decision_entry_id")
        for row in correspondence
        if row.get("machine_navigation") is not (row.get("disposition") == "toc")
    }
    seeds = cast(list[JsonObject], closure.get("material_seeds"))
    seed_ids = [_string(seed.get("decision_entry_id"), "material seed decision") for seed in seeds]
    _require(len(seed_ids) == len(set(seed_ids)), "duplicate Gate A material seed")
    _require(set(seed_ids) == disagreement, "Gate A affected closure decision coverage differs")
    closure_accounting = cast(Mapping[str, Any], closure.get("accounting"))
    _require(
        closure_accounting.get("material_seed_count") == 406,
        "Gate A closure accounting differs",
    )
    _require(
        closure_accounting.get("affected_page_count")
        == len(cast(list[Any], closure.get("affected_page_ids"))),
        "Gate A affected page accounting differs",
    )
    _require(
        closure_accounting.get("affected_source_count")
        == len(cast(list[Any], closure.get("affected_source_ids"))),
        "Gate A affected source accounting differs",
    )
    return _GateAInputs(specification, correspondence, refs)


def _validate_gate_a_schemas(
    repo_root: Path,
    specification: JsonObject,
    closure: JsonObject,
    correspondence: list[JsonObject],
) -> None:
    """Revalidate the accepted Gate A compact records before consuming them."""
    root = repo_root / "benchmarks/er_bench/schemas/navigation_overlay/v1"
    validators = {
        "specification": Draft202012Validator(
            read_json_object(root / "gate_a_specification.schema.json")
        ),
        "closure": Draft202012Validator(read_json_object(root / "affected_closure.schema.json")),
        "correspondence": Draft202012Validator(
            read_json_object(root / "decision_correspondence_row.schema.json")
        ),
    }
    for label, record in (("specification", specification), ("closure", closure)):
        errors = sorted(validators[label].iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise ValueError(f"invalid Gate A {label}: {errors[0].message}")
    for index, row in enumerate(correspondence):
        errors = sorted(
            validators["correspondence"].iter_errors(row),
            key=lambda error: list(error.path),
        )
        if errors:
            raise ValueError(f"invalid Gate A correspondence {index}: {errors[0].message}")


def _load_bound_canonical_entities(
    request: GateBMaterializationRequest, inputs: _GateAInputs
) -> dict[str, _CanonicalEntity]:
    """Read only Gate A-bound canonical blocks/tables and verify exact correspondence."""
    bound_inputs = cast(Mapping[str, Any], inputs.specification["inputs"])
    task03j = cast(Mapping[str, Any], bound_inputs["task03j"])
    candidates = cast(list[JsonObject], task03j["candidate_records"])
    candidate_by_key = {
        (
            _string(row.get("source_id"), "source_id"),
            _string(row.get("candidate_id"), "candidate_id"),
        ): row
        for row in candidates
    }
    wanted_by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    pages_by_entity: dict[str, set[str]] = defaultdict(set)
    for row in inputs.correspondence:
        key = (
            _string(row.get("source_id"), "source_id"),
            _string(row.get("candidate_id"), "candidate_id"),
        )
        _require(key in candidate_by_key, f"correspondence uses unbound candidate: {key}")
        page_id = _string(row.get("page_id"), "page_id")
        by_kind = cast(Mapping[str, Any], row.get("entity_ids_by_kind"))
        for plural in ("blocks", "tables"):
            for entity_id in cast(list[str], by_kind.get(plural, [])):
                wanted_by_key[key].add(entity_id)
                pages_by_entity[entity_id].add(page_id)

    found: dict[str, _CanonicalEntity] = {}
    documents = request.resolved_task03j_root() / "document_publications/documents"
    for key in sorted(wanted_by_key):
        source_id, candidate_id = key
        bound = candidate_by_key[key]
        candidate = documents / source_id / candidate_id
        inventory_path = candidate / "records/artifact_inventory.json"
        inventory_ref = cast(Mapping[str, Any], bound["candidate_inventory"])
        _require(
            sha256_file(inventory_path) == inventory_ref.get("sha256"),
            f"changed candidate inventory: {source_id}",
        )
        inventory = read_json_object(inventory_path)
        sealed = {
            str(item["path"]): item
            for item in cast(list[JsonObject], inventory.get("files", []))
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        for declared in cast(list[JsonObject], bound["canonical_records"]):
            declared_path = _string(declared.get("path"), "canonical record path")
            _require(
                sealed.get(declared_path) == declared,
                f"changed sealed reference: {source_id}/{declared_path}",
            )
        wanted = wanted_by_key[key]
        for kind in ("block", "table"):
            relative = f"content/canonical/{kind}s.jsonl"
            canonical_path = candidate / relative
            _require_sealed_file_size(canonical_path, sealed[relative], f"{source_id}/{relative}")
            for record in iter_jsonl(canonical_path):
                record_id = record.get("id")
                if record_id not in wanted:
                    continue
                assert isinstance(record_id, str)
                entity_id = record_id
                _require(entity_id not in found, f"duplicate canonical entity: {entity_id}")
                placement = _string(
                    record.get("semantic_placement"), f"{entity_id}.semantic_placement"
                )
                is_toc_row = record.get("is_toc_row")
                _require(isinstance(is_toc_row, bool), f"invalid machine TOC flag: {entity_id}")
                section = record.get("section_id")
                _require(
                    section is None or isinstance(section, str),
                    f"invalid section ID: {entity_id}",
                )
                record_pages = _record_page_ids(record)
                _require(
                    pages_by_entity[entity_id].issubset(record_pages),
                    f"Gate A page membership mismatch: {entity_id}",
                )
                found[entity_id] = _CanonicalEntity(
                    source_id=source_id,
                    candidate_id=candidate_id,
                    entity_kind=kind,
                    entity_id=entity_id,
                    page_ids=frozenset(record_pages),
                    section_id=cast(str | None, section),
                    semantic_placement=placement,
                    is_toc_row=cast(bool, is_toc_row),
                )
        missing = wanted - found.keys()
        _require(
            not missing,
            f"Gate A references missing canonical entities: {sorted(missing)[:1]}",
        )
    return found


def _materialize_semantic_view(
    correspondence: Iterable[JsonObject],
    entities: Mapping[str, _CanonicalEntity],
    *,
    semantic_view_id: str | None,
) -> tuple[list[JsonObject], list[JsonObject], set[str]]:
    """Build one application per decision and unique aggregate entity overrides."""
    pending: dict[str, _PendingDisposition] = {}
    applications: list[JsonObject] = []
    for row in sorted(
        correspondence,
        key=lambda item: (
            str(item.get("source_id")),
            int(cast(int, item.get("physical_page"))),
            str(item.get("decision_entry_id")),
        ),
    ):
        decision_id = _string(row.get("decision_entry_id"), "decision_entry_id")
        disposition = _string(row.get("disposition"), "disposition")
        machine_navigation = row.get("machine_navigation")
        _require(isinstance(machine_navigation, bool), f"invalid machine decision: {decision_id}")
        human_navigation = disposition == "toc"
        _require(disposition in {"toc", "not_toc"}, f"invalid human decision: {decision_id}")
        mapping = _string(row.get("mapping_outcome"), "mapping_outcome")
        _require(
            mapping
            in {"mapped", "no_existing_entity_evidence", "mixed_page_insufficient_entity_evidence"},
            f"invalid correspondence outcome: {decision_id}",
        )
        selected: list[_CanonicalEntity] = []
        outcome: str
        reason: str
        if mapping != "mapped":
            outcome = {
                "mixed_page_insufficient_entity_evidence": (
                    "unchanged_mixed_page_insufficient_entity_evidence"
                ),
                "no_existing_entity_evidence": "unchanged_no_existing_entity_evidence",
            }[mapping]
            reason = "insufficient exact entity evidence; machine semantics are inherited"
        elif machine_navigation == human_navigation:
            outcome = (
                "unchanged_machine_toc_human_toc"
                if machine_navigation
                else "unchanged_machine_not_toc_human_not_toc"
            )
            reason = "human and machine navigation decisions agree"
        else:
            by_kind = cast(Mapping[str, Any], row.get("entity_ids_by_kind"))
            entity_ids = [
                entity_id
                for plural in ("blocks", "tables")
                for entity_id in cast(list[str], by_kind.get(plural, []))
            ]
            _require(entity_ids, f"mapped disagreement has no block/table entity: {decision_id}")
            missing = sorted(set(entity_ids) - entities.keys())
            _require(not missing, f"missing canonical entity: {missing[:1]}")
            mapped = [entities[entity_id] for entity_id in entity_ids]
            selected = mapped if human_navigation else [e for e in mapped if e.machine_navigation]
            if not selected:
                outcome = "unchanged_no_existing_entity_evidence"
                reason = "no mapped entity has the machine semantic targeted by this decision"
            else:
                outcome = (
                    "applied_human_confirmed_navigation"
                    if human_navigation
                    else "applied_human_rejected_machine_navigation"
                )
                reason = "human decision applied only to exact existing canonical entities"
        applied_ids: list[str] = []
        for entity in selected:
            desired = human_navigation
            evidence = {
                "decision_entry_id": decision_id,
                "page_id": _string(row.get("page_id"), "page_id"),
                "physical_page": cast(int, row.get("physical_page")),
            }
            existing = pending.get(entity.entity_id)
            if existing is None:
                pending[entity.entity_id] = _PendingDisposition(entity, desired, [evidence])
            else:
                _require(
                    existing.effective_navigation is desired,
                    f"conflicting entity decisions: {entity.entity_id}",
                )
                existing.decision_evidence.append(evidence)
        applications.append(
            {
                "schema_version": "er_commons.navigation_overlay.v1.decision_application",
                "semantic_view_id": semantic_view_id or "navsemanticv1-" + "0" * 64,
                "overlay_plan_id": ACCEPTED_GATE_A_ID,
                "decision_entry_id": decision_id,
                "source_id": row.get("source_id"),
                "candidate_id": row.get("candidate_id"),
                "page_id": row.get("page_id"),
                "physical_page": row.get("physical_page"),
                "machine_navigation": machine_navigation,
                "human_disposition": disposition,
                "decision_origin_class": row.get("decision_origin_class"),
                "visible_review_item_id": row.get("visible_review_item_id"),
                "c17_positive_suffix_evidence": row.get("c17_positive_suffix_evidence"),
                "correspondence_outcome": mapping,
                "application_outcome": outcome,
                "semantic_disposition_ids": applied_ids,
                "reason": reason,
            }
        )

    dispositions: list[JsonObject] = []
    disposition_ids_by_decision: dict[str, list[str]] = defaultdict(list)
    context_sections: set[str] = set()
    for entity_id, value in sorted(pending.items()):
        entity = value.entity
        aggregate_evidence = sorted(
            value.decision_evidence,
            key=lambda item: (int(item["physical_page"]), str(item["decision_entry_id"])),
        )
        effective = value.effective_navigation
        evidence_pages = {str(item["page_id"]) for item in aggregate_evidence}
        _require_exact_page_membership(entity_id, set(entity.page_ids), evidence_pages)
        identity = {
            "overlay_plan_id": ACCEPTED_GATE_A_ID,
            "entity_id": entity_id,
            "effective_navigation": effective,
            "decision_entry_ids": sorted(
                {str(item["decision_entry_id"]) for item in aggregate_evidence}
            ),
        }
        disposition_id = f"navdispv1-{canonical_json_sha256(identity)[:24]}"
        for item in aggregate_evidence:
            disposition_ids_by_decision[str(item["decision_entry_id"])].append(disposition_id)
        if entity.section_id is not None:
            context_sections.add(entity.section_id)
        dispositions.append(
            {
                "schema_version": "er_commons.navigation_overlay.v1.semantic_disposition",
                "semantic_view_id": semantic_view_id or "navsemanticv1-" + "0" * 64,
                "overlay_plan_id": ACCEPTED_GATE_A_ID,
                "disposition_id": disposition_id,
                "source_id": entity.source_id,
                "candidate_id": entity.candidate_id,
                "entity_kind": entity.entity_kind,
                "entity_id": entity.entity_id,
                "canonical_record_path": f"content/canonical/{entity.entity_kind}s.jsonl",
                "decision_entry_ids": sorted(
                    {str(item["decision_entry_id"]) for item in aggregate_evidence}
                ),
                "decision_page_ids": sorted({str(item["page_id"]) for item in aggregate_evidence}),
                "decision_physical_pages": sorted(
                    {int(item["physical_page"]) for item in aggregate_evidence}
                ),
                "machine_section_id": entity.section_id,
                "machine_semantic_placement": entity.semantic_placement,
                "machine_is_toc_row": entity.is_toc_row,
                "machine_navigation": entity.machine_navigation,
                "effective_navigation": effective,
                "disposition": (
                    "human_confirmed_navigation"
                    if effective
                    else "human_rejected_machine_navigation"
                ),
                "original_machine_placement_preserved": True,
                "reason": "sparse human semantic override over immutable machine provenance",
            }
        )
    for application in applications:
        application["semantic_disposition_ids"] = sorted(
            disposition_ids_by_decision[str(application["decision_entry_id"])]
        )
    return applications, dispositions, context_sections


def _accounting(applications: list[JsonObject], dispositions: list[JsonObject]) -> JsonObject:
    """Return exact decision and sparse-override closure counts."""
    outcomes = Counter(str(row["application_outcome"]) for row in applications)
    kinds = Counter(str(row["entity_kind"]) for row in dispositions)
    effects = Counter(bool(row["effective_navigation"]) for row in dispositions)
    context_sections = {
        str(row["machine_section_id"])
        for row in dispositions
        if isinstance(row.get("machine_section_id"), str)
    }
    return {
        "decision_count": len(applications),
        "machine_toc_human_toc_count": outcomes["unchanged_machine_toc_human_toc"],
        "machine_not_toc_human_not_toc_count": outcomes["unchanged_machine_not_toc_human_not_toc"],
        "human_confirmed_navigation_decision_count": outcomes["applied_human_confirmed_navigation"],
        "human_rejected_machine_navigation_decision_count": outcomes[
            "applied_human_rejected_machine_navigation"
        ],
        "fail_closed_decision_count": outcomes["unchanged_no_existing_entity_evidence"]
        + outcomes["unchanged_mixed_page_insufficient_entity_evidence"],
        "changed_content_entity_count": len(dispositions),
        "human_confirmed_navigation_entity_count": effects[True],
        "human_rejected_machine_navigation_entity_count": effects[False],
        "changed_block_count": kinds["block"],
        "changed_table_count": kinds["table"],
        "preserved_section_association_count": len(context_sections),
    }


def _validate_production_accounting(accounting: JsonObject, context_sections: set[str]) -> None:
    """Reject any drift from Gate A's accepted production closure."""
    expected = {
        "decision_count": EXPECTED_DECISION_COUNT,
        "machine_toc_human_toc_count": 45,
        "machine_not_toc_human_not_toc_count": 303,
        "human_confirmed_navigation_decision_count": 15,
        "human_rejected_machine_navigation_decision_count": 391,
        "fail_closed_decision_count": 3,
        "changed_content_entity_count": (
            EXPECTED_CONFIRMED_ENTITY_COUNT + EXPECTED_REJECTED_ENTITY_COUNT
        ),
        "human_confirmed_navigation_entity_count": EXPECTED_CONFIRMED_ENTITY_COUNT,
        "human_rejected_machine_navigation_entity_count": EXPECTED_REJECTED_ENTITY_COUNT,
        "changed_block_count": EXPECTED_BLOCK_DISPOSITION_COUNT,
        "changed_table_count": EXPECTED_TABLE_DISPOSITION_COUNT,
        "preserved_section_association_count": EXPECTED_CONTEXT_SECTION_COUNT,
    }
    _require(accounting == expected, f"Gate B production accounting differs: {accounting}")
    _require(
        len(context_sections) == EXPECTED_CONTEXT_SECTION_COUNT,
        "Gate B contextual section accounting differs",
    )


def _validate_output_schemas(
    schema_root: Path,
    applications: list[JsonObject],
    dispositions: list[JsonObject],
    specification: JsonObject,
) -> None:
    """Validate all Gate B records before publication."""
    pairs = (
        ("decision application", "decision_application_row.schema.json", applications),
        ("semantic disposition", "semantic_disposition_row.schema.json", dispositions),
    )
    for label, filename, rows in pairs:
        validator = Draft202012Validator(read_json_object(schema_root / filename))
        for index, row in enumerate(rows):
            errors = sorted(validator.iter_errors(row), key=lambda error: list(error.path))
            if errors:
                raise ValueError(f"invalid {label} {index}: {errors[0].message}")
    errors = sorted(
        Draft202012Validator(
            read_json_object(schema_root / "gate_b_specification.schema.json")
        ).iter_errors(specification),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(f"invalid Gate B specification: {errors[0].message}")


def _publish(
    output_parent: Path,
    semantic_view_id: str,
    applications: list[JsonObject],
    dispositions: list[JsonObject],
    specification: JsonObject,
    accounting: JsonObject,
    schema_root: Path,
) -> Path:
    """Publish the immutable semantic namespace through an atomic rename."""
    application_bytes = jsonl_bytes(applications)
    disposition_bytes = jsonl_bytes(dispositions)
    expected = {
        "decision_applications.jsonl": application_bytes,
        "semantic_dispositions.jsonl": disposition_bytes,
        "semantic_view_manifest.json": json_bytes(specification),
        "records/identity_preimage.json": json_bytes(specification["identity_preimage"]),
    }
    final = output_parent / semantic_view_id
    if final.exists():
        for relative, content in expected.items():
            path = final / relative
            if not path.is_file() or path.read_bytes() != content:
                raise FileExistsError(f"refusing to reuse changed Gate B artifact: {path}")
        _validate_published_namespace(final)
        return final

    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{semantic_view_id}.", dir=output_parent))
    try:
        for relative, content in expected.items():
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        inventory = artifact_inventory(
            staging, {"records/artifact_inventory.json", "records/completion_record.json"}
        )
        inventory_path = staging / "records/artifact_inventory.json"
        inventory_path.write_bytes(json_bytes(inventory))
        managed = [
            file_reference(staging / name, root=staging)
            for name in (
                "decision_applications.jsonl",
                "semantic_dispositions.jsonl",
                "semantic_view_manifest.json",
            )
        ]
        completion = {
            "schema_version": "er_commons.navigation_overlay.v1.gate_b_completion",
            "semantic_view_id": semantic_view_id,
            "overlay_plan_id": ACCEPTED_GATE_A_ID,
            "status": "complete",
            "artifact_inventory_sha256": sha256_bytes(json_bytes(inventory)),
            "gate_b_specification": file_reference(
                staging / "semantic_view_manifest.json", root=staging
            ),
            "managed_files": [
                managed[1],
                managed[0],
                managed[2],
                file_reference(staging / "records/identity_preimage.json", root=staging),
                file_reference(inventory_path, root=staging),
            ],
            "accounting": accounting,
            "validation": {
                "schema_validation_passed": True,
                "decision_coverage_complete": True,
                "entity_ids_exist_in_bound_canonical_records": True,
                "disposition_ids_unique": True,
                "output_order_deterministic": True,
                "repeated_build_reused_identical_namespace": True,
            },
            "source_free_boundary": _SOURCE_FREE_BOUNDARY,
        }
        completion_validator = Draft202012Validator(
            read_json_object(schema_root / "gate_b_completion.schema.json")
        )
        errors = sorted(
            completion_validator.iter_errors(completion), key=lambda error: list(error.path)
        )
        if errors:
            raise ValueError(f"invalid Gate B completion: {errors[0].message}")
        (staging / "records/completion_record.json").write_bytes(json_bytes(completion))
        os.rename(staging, final)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return final


def _validate_published_namespace(publication: Path) -> None:
    """Reject incomplete, stale, or changed Gate B managed bytes."""
    inventory_path = publication / "records/artifact_inventory.json"
    completion_path = publication / "records/completion_record.json"
    inventory = read_json_object(inventory_path)
    actual = artifact_inventory(
        publication, {"records/artifact_inventory.json", "records/completion_record.json"}
    )
    _require(inventory == actual, "changed Gate B artifact inventory")
    completion = read_json_object(completion_path)
    _require(completion.get("status") == "complete", "Gate B publication is incomplete")
    _require(completion.get("semantic_view_id") == publication.name, "stale Gate B identity")
    _require(
        completion.get("artifact_inventory_sha256") == sha256_bytes(json_bytes(inventory)),
        "Gate B completion does not bind its inventory",
    )
    manifest = read_json_object(publication / "semantic_view_manifest.json")
    _require(manifest.get("semantic_view_id") == publication.name, "stale Gate B manifest")
    _require_derived_identity(
        "navsemanticv1-",
        manifest.get("identity_preimage"),
        publication.name,
        "Gate B",
    )
    _require(
        read_json_object(publication / "records/identity_preimage.json")
        == manifest.get("identity_preimage"),
        "Gate B identity preimage differs",
    )
    managed = cast(list[JsonObject], completion.get("managed_files"))
    for reference in managed:
        path = publication / _string(reference.get("path"), "managed path")
        _require(
            file_reference(path, root=publication) == reference,
            f"changed Gate B file: {path}",
        )


def _implementation_reference(repo_root: Path) -> JsonObject:
    """Bind only the new Gate B owner and its thin command wrapper."""
    paths = (
        repo_root / "src/er_commons/navigation_overlay/materialization.py",
        repo_root / "scripts/materialize_task04c_gate_b.py",
    )
    refs = [file_reference(path, root=repo_root) for path in paths]
    return {"files": refs, "sha256": canonical_json_sha256(refs)}


def _record_page_ids(record: Mapping[str, Any]) -> set[str]:
    """Return exact canonical region page membership."""
    return {
        str(region["page_id"])
        for value in cast(list[Any], record.get("regions", []))
        if isinstance(value, dict)
        for region in [cast(dict[str, Any], value)]
        if isinstance(region.get("page_id"), str)
    }


def _string(value: object, label: str) -> str:
    """Return a required non-empty string."""
    _require(isinstance(value, str) and bool(value), f"missing or invalid {label}")
    return cast(str, value)


def _require_derived_identity(prefix: str, preimage: object, expected: str, label: str) -> None:
    """Require a content-derived artifact ID to match its exact preimage."""
    actual = prefix + canonical_json_sha256(preimage)
    _require(actual == expected, f"{label} identity digest differs")


def _require_sealed_file_size(path: Path, reference: Mapping[str, Any], label: str) -> None:
    """Catch replaced or truncated canonical inputs without rehashing large bytes."""
    declared = reference.get("byte_size")
    _require(isinstance(declared, int) and declared >= 0, f"invalid sealed size: {label}")
    _require(path.is_file() and path.stat().st_size == declared, f"changed sealed size: {label}")


def _require_exact_page_membership(
    entity_id: str, record_pages: set[str], decision_pages: set[str]
) -> None:
    """Reject whole-entity changes that would extend beyond reviewed pages."""
    _require(
        record_pages == decision_pages,
        f"Gate A page membership mismatch: {entity_id}",
    )


def _require(condition: object, message: str) -> None:
    """Raise a stable validation error when an artifact invariant fails."""
    if not condition:
        raise ValueError(message)
