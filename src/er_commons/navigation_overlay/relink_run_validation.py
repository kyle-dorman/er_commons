"""Run the source-free Task 04D Gate C population and regression controls."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    canonical_json_sha256,
    iter_jsonl,
    jsonl_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    sha256_file,
)
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_records.document_references.construction import CandidateSource
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.document_records.document_references.policy import default_mention_policy
from er_commons.document_records.document_references.publication import (
    verify_completed_candidate,
)
from er_commons.document_records.document_references.relink_publication import (
    validate_relink_build_products,
)
from er_commons.document_records.document_references.relinking import (
    DocumentRelinkBuilder,
    NavigationInputs,
)
from er_commons.document_records.document_references.relinking_config import (
    DocumentLinkRunSpec,
    load_document_link_run_spec,
)
from er_commons.document_records.document_structure.publication import (
    deep_audit_completed_document_structure,
)
from er_commons.navigation_overlay.gate_c_validation import (
    AcceptedNavigationControl,
    compare_ordinary_machine_population,
    validate_gate_c_navigation_population,
)
from er_commons.navigation_overlay.seal_audit import deep_audit_navigation_root
from er_commons.source_family_catalog import SourceFamilyCatalog

JsonObject = dict[str, Any]
LOGGER = logging.getLogger(__name__)
_LETTERED = re.compile(r"^[a-z]\.\s+", re.IGNORECASE)


@dataclass(frozen=True)
class ValidatedRunInputs:
    """Exact checked-in and sealed inputs selected for the Gate C replay."""

    spec: DocumentLinkRunSpec
    spec_sha256: str
    policy_path: Path
    policy_schema_path: Path
    catalog_path: Path
    production_extraction_id: str


def prepare_reviewed_navigation_inputs(
    *,
    navigation_root: Path,
    semantic_dispositions_path: Path,
    output_root: Path,
    validation: JsonObject,
) -> JsonObject:
    """Write deterministic corpus evidence consumed by the generic materializer."""
    deep_audit_navigation_root(navigation_root)
    navigation, _, _ = _navigation_inputs(navigation_root, validation=validation)
    return _write_reviewed_inputs(
        navigation,
        semantic_dispositions_path=semantic_dispositions_path,
        output_root=output_root,
        validation=validation,
    )


def _write_reviewed_inputs(
    navigation: NavigationInputs,
    *,
    semantic_dispositions_path: Path,
    output_root: Path,
    validation: JsonObject,
) -> JsonObject:
    """Publish selected review rows only after their navigation seal has passed audit."""
    dispositions = [
        row
        for row in iter_jsonl(semantic_dispositions_path)
        if str(row.get("source_id")) in validation["reviewed_source_ids"]
    ]
    rows = {
        "text_entries": navigation.entries,
        "dispositions": dispositions,
        "parent_relations": navigation.relations,
    }
    outputs = {output_root / f"{name}.jsonl": jsonl_bytes(values) for name, values in rows.items()}
    for path, content in outputs.items():
        if path.exists() and path.read_bytes() != content:
            raise ValueError(
                f"role=reviewed_inputs path={path}: refusing to replace existing bytes"
            )
    for path, content in outputs.items():
        publish_bytes_no_clobber(path, content)
    counts = {name: len(values) for name, values in rows.items()}
    return counts


def run_gate_c_validation(
    *,
    data_root: Path,
    link_spec_path: Path,
    navigation_root: Path,
    validation: JsonObject,
    repository_root: Path,
    reviewed_input_root: Path | None = None,
    semantic_dispositions_path: Path | None = None,
) -> JsonObject:
    """Replay the selected structured inputs without publishing any candidate."""
    repo_root = repository_root
    selected = _validated_run_inputs(
        data_root=data_root.resolve(),
        repository_root=repo_root,
        link_spec_path=link_spec_path.resolve(),
    )
    policy = load_document_linking_policy(
        selected.policy_path, schema_path=selected.policy_schema_path
    )
    catalog = SourceFamilyCatalog.load(selected.catalog_path)
    catalog_sha256 = sha256(selected.catalog_path.read_bytes()).hexdigest()
    navigation_completion_sha256 = deep_audit_navigation_root(navigation_root)
    navigation, baseline_targets, reconciliations = _navigation_inputs(
        navigation_root, validation=validation
    )
    output_schema_paths = {
        role: getattr(selected.spec.output_schema_refs, role).resolve(
            repository_root=repo_root,
            artifact_root=data_root,
        )
        for role in selected.spec.output_schema_refs.__class__.model_fields
    }

    decisions: list[JsonObject] = []
    baseline_machine: list[JsonObject] = []
    replacement_machine: list[JsonObject] = []
    derived_alias_count = 0
    for document in selected.spec.documents:
        published_completion = document.source_document.completion_ref.resolve(
            repository_root=repo_root, artifact_root=data_root
        )
        published_inventory = document.source_document.inventory_ref.resolve(
            repository_root=repo_root, artifact_root=data_root
        )
        published_root = _candidate_root(
            published_completion,
            inventory_path=published_inventory,
            expected_id=document.source_document.candidate_id,
            source_id=document.source_id,
        )
        structured_completion = document.structured_document.completion_ref.resolve(
            repository_root=repo_root, artifact_root=data_root
        )
        structured_inventory = document.structured_document.inventory_ref.resolve(
            repository_root=repo_root, artifact_root=data_root
        )
        structured_root = _candidate_root(
            structured_completion,
            inventory_path=structured_inventory,
            expected_id=document.structured_document.candidate_id,
            source_id=document.source_id,
        )
        baseline_source = CandidateSource.load(published_root / "content")
        source = CandidateSource.load(structured_root)
        baseline_id = str(baseline_source.manifest["extraction_id"])
        upstream_id = str(source.manifest["extraction_id"])
        verify_completed_candidate(published_root / "content", baseline_id)
        deep_audit_completed_document_structure(structured_root, upstream_id)
        build = DocumentRelinkBuilder(
            source=source,
            upstream_candidate_id=upstream_id,
            candidate_id=upstream_id,
            source_id=document.source_id,
            mention_policy=default_mention_policy(),
            linking_policy=policy,
            source_family_catalog=catalog,
            source_family_catalog_sha256=catalog_sha256,
            navigation=navigation.remap_namespace(baseline_id, upstream_id),
        ).build()
        validate_relink_build_products(build, schema_paths=output_schema_paths)
        derived_alias_count += int(build.support["preservation"]["derived_alias_count"])
        decisions.extend(
            _validation_decisions(
                build.products.navigation_decisions,
                entries=navigation.entries,
                baseline_targets=baseline_targets,
                reconciliations=reconciliations,
            )
        )
        baseline_machine.extend(
            _machine_rows(baseline_source.record_files["canonical/cross_references.jsonl"])
        )
        replacement_machine.extend(_machine_rows(build.products.ordinary_references))

    source_count = len(selected.spec.documents)
    if source_count != validation["expected_source_count"]:
        raise ValueError(
            f"source population differs: expected={validation['expected_source_count']} "
            f"observed={source_count}"
        )
    navigation_summary = validate_gate_c_navigation_population(
        decisions,
        baseline_targets=baseline_targets,
        controls={
            name: AcceptedNavigationControl(**value)
            for name, value in validation["navigation_controls"].items()
        },
        primary_rule_counts=validation["primary_rule_counts"],
        expected_baseline_count=validation["expected_baseline_count"],
    )
    machine_summary = compare_ordinary_machine_population(baseline_machine, replacement_machine)
    if reviewed_input_root is not None and semantic_dispositions_path is not None:
        _write_reviewed_inputs(
            navigation,
            semantic_dispositions_path=semantic_dispositions_path,
            output_root=reviewed_input_root,
            validation=validation,
        )
    return {
        "schema_version": "er_commons.task04d_gate_c_validation.v1",
        "source_free": True,
        "production_artifact_published": False,
        "identity_binding": {
            "link_run_spec_sha256": selected.spec_sha256,
            "production_extraction_id": selected.production_extraction_id,
            "linking_policy_sha256": sha256_file(selected.policy_path),
            "reviewed_navigation_bundle_id": (
                selected.spec.reviewed_navigation.bundle_id
                if selected.spec.reviewed_navigation is not None
                else None
            ),
            "validation_script_sha256": sha256_file(Path(__file__)),
            "validation_spec_sha256": canonical_json_sha256(validation),
            "navigation_completion_sha256": navigation_completion_sha256,
        },
        "sealed_document_count": source_count,
        "derived_r6_alias_count": derived_alias_count,
        "navigation": navigation_summary,
        "ordinary_machine": machine_summary,
    }


def _validated_run_inputs(
    *, data_root: Path, repository_root: Path, link_spec_path: Path
) -> ValidatedRunInputs:
    """Verify the run selection and current production recipe without executing it."""
    spec, spec_sha256 = load_document_link_run_spec(link_spec_path)
    policy_path = spec.linking_policy_ref.resolve(
        repository_root=repository_root, artifact_root=data_root
    )
    policy_schema_path = spec.linking_policy_schema_ref.resolve(
        repository_root=repository_root, artifact_root=data_root
    )
    catalog_path = spec.source_family_catalog_ref.resolve(
        repository_root=repository_root, artifact_root=data_root
    )
    identity_path = spec.replacement_production_identity_recipe_ref.resolve(
        repository_root=repository_root, artifact_root=data_root
    )
    spec.document_publication_spec_ref.resolve(
        repository_root=repository_root, artifact_root=data_root
    )
    spec.collection_run_spec_ref.resolve(repository_root=repository_root, artifact_root=data_root)
    identity = read_json_object(identity_path)
    validated = validate_production_identity(
        identity,
        expected_source_ids=list(spec.selected_source_ids),
        expected_scope_kind="production_full",
    )
    return ValidatedRunInputs(
        spec=spec,
        spec_sha256=spec_sha256,
        policy_path=policy_path,
        policy_schema_path=policy_schema_path,
        catalog_path=catalog_path,
        production_extraction_id=validated.value,
    )


def _candidate_root(
    completion_path: Path, *, inventory_path: Path, expected_id: str, source_id: str
) -> Path:
    """Return the candidate owning one selected completion record."""
    root = completion_path.parent.parent
    if inventory_path.parent.parent != root or root.name != expected_id:
        raise ValueError(
            f"source={source_id} role=candidate_seal path={completion_path}: identity differs; "
            f"observed={root.name!r} expected={expected_id!r}"
        )
    return root


def _navigation_inputs(
    root: Path,
    *,
    validation: JsonObject,
) -> tuple[NavigationInputs, dict[str, str], dict[str, JsonObject]]:
    entries = list(iter_jsonl(root / "toc_text_entries.jsonl"))
    by_id = {str(row["toc_text_entry_id"]): row for row in entries}
    reconciliations = {
        str(row["toc_text_entry_id"]): row
        for row in iter_jsonl(root / "toc_entry_reconciliations.jsonl")
    }
    baseline = {
        str(row["source_toc_entry_id"]): _identity_relative_id(str(row["target_id"]))
        for row in iter_jsonl(root / "link_overlay.jsonl")
    }
    left = _entry_left_edges(root / "toc_text_pages.jsonl", by_id)
    relations = _lettered_relations(entries, left)

    context = validation["context_entries"]
    relations.extend(validation["parent_relations"])

    prepared: list[JsonObject] = []
    for row in entries:
        item = dict(row)
        reconciliation = reconciliations[str(row["toc_text_entry_id"])]
        item["link_claim"] = True
        raw_destination_ids = reconciliation["distinct_destination_page_ids"]
        if not isinstance(raw_destination_ids, list) or not all(
            isinstance(page_id, str) for page_id in raw_destination_ids
        ):
            msg = (
                "Task04C reconciliation has invalid distinct_destination_page_ids "
                f"for {row['toc_text_entry_id']}"
            )
            raise ValueError(msg)
        destination_ids = raw_destination_ids
        item["destination_page_ids"] = (
            destination_ids
            if len(destination_ids) == 1
            or reconciliation["entry_outcome"] == "destination_target_page_mismatch"
            else None
        )
        prepared.append(item)
    navigation = NavigationInputs(tuple((*prepared, *context)), tuple(relations))
    return navigation, baseline, reconciliations


def _entry_left_edges(path: Path, entries: dict[str, JsonObject]) -> dict[str, float]:
    result: dict[str, float] = {}
    for page in iter_jsonl(path):
        entry_ids = cast(list[str], page["entry_ids"])
        lines = cast(list[JsonObject], page["lines"])
        for entry_id in entry_ids:
            row = entries[str(entry_id)]
            locator = cast(JsonObject, row["entry_locator"])
            line = lines[int(locator["line_start"])]
            bbox = cast(list[float], line["bbox"])
            result[str(entry_id)] = float(bbox[0])
    return result


def _lettered_relations(entries: list[JsonObject], left: dict[str, float]) -> list[JsonObject]:
    relations: list[JsonObject] = []
    stacks: dict[tuple[str, str], list[tuple[float, int, str]]] = {}
    last_page: dict[tuple[str, str], int] = {}
    for order, row in enumerate(entries):
        key = (str(row["source_id"]), str(row["candidate_id"]))
        page = int(row["physical_page"])
        if last_page.get(key) not in {None, page, page - 1}:
            stacks[key] = []
        last_page[key] = page
        entry_id = str(row["toc_text_entry_id"])
        edge = left[entry_id]
        if _LETTERED.match(str(row["raw_text"])):
            candidates = [item for item in stacks.get(key, []) if item[0] < edge - 5]
            if candidates:
                parent = max(candidates, key=lambda item: (item[0], item[1]))[2]
                relations.append(_relation(str(row["source_id"]), entry_id, parent))
        elif row.get("marker_kind") == "section":
            stack = [item for item in stacks.get(key, []) if item[0] < edge - 5]
            stack.append((edge, order, entry_id))
            stacks[key] = stack
    return relations


def _relation(source_id: str, child: str, parent: str) -> JsonObject:
    return {
        "relation_id": f"task04d-parent-{child}",
        "source_id": source_id,
        "child_entry_id": child,
        "parent_entry_id": parent,
    }


def _validation_decisions(
    rows: tuple[JsonObject, ...],
    *,
    entries: tuple[JsonObject, ...],
    baseline_targets: dict[str, str],
    reconciliations: dict[str, JsonObject],
) -> list[JsonObject]:
    source_entries = {
        str(row.get("navigation_entry_id", row.get("toc_text_entry_id"))): row
        for row in entries
        if row.get("context_only") is not True
    }
    result: list[JsonObject] = []
    for row in rows:
        entry_id = str(row["navigation_entry_id"])
        entry = source_entries[entry_id]
        outcome = str(row["outcome"])
        target_ids = row.get("candidate_target_ids", [])
        target_id = (
            _identity_relative_id(str(target_ids[0])) if outcome == "resolved_unique" else None
        )
        is_baseline = entry_id in baseline_targets
        result.append(
            {
                "entry_id": entry_id,
                "control_class": (
                    "existing_task04c_link"
                    if is_baseline
                    else _control_class(entry, reconciliations[entry_id])
                ),
                "outcome": outcome,
                "target_id": target_id,
                "primary_rule_id": (
                    ("R1" if is_baseline else _primary_rule(entry, row))
                    if outcome == "resolved_unique"
                    else None
                ),
            }
        )
    return result


def _control_class(entry: JsonObject, reconciliation: JsonObject) -> str:
    text = str(entry["raw_text"])
    if reconciliation["entry_outcome"] == "destination_target_page_mismatch":
        return "destination_page_conflict"
    if _LETTERED.match(text):
        return "lettered_section"
    if entry.get("marker_kind") == "table":
        return "table"
    if entry.get("marker_kind") == "figure":
        return "figure"
    if entry.get("marker_kind") == "section":
        if (
            entry["source_id"] == "deir_appendix_a"
            and entry.get("terminal_destination_token") is None
        ):
            return "appendix_a_no_page_section"
        return "ordinary_numbered_section"
    return "unsupported_shape"


def _primary_rule(entry: JsonObject, decision: JsonObject) -> str:
    control = _control_class(entry, {"entry_outcome": "not_conflict"})
    basis = set(decision.get("match_basis", []))
    if control == "lettered_section":
        if "retained_ascii_hyphen_adjacent_whitespace" in basis:
            return "R5"
        if decision.get("parent_scope_applied"):
            return "R4"
        return "R3"
    if control == "table":
        return "R6" if basis == {"exact"} else "R6a"
    if any(str(value).startswith("goal_prefix") for value in basis):
        return "R2a"
    if basis == {"retained_ascii_hyphen_adjacent_whitespace"}:
        return "R5"
    return "R2" if basis == {"exact"} else "R2b"


def _machine_rows(rows: Any) -> list[JsonObject]:
    result: list[JsonObject] = []
    for row in rows:
        candidates = row.get("candidates", [])
        target = (
            candidates[0]["target_record_id"]
            if row.get("resolution_status") == "resolved" and len(candidates) == 1
            else None
        )
        result.append(
            {
                "mention_key": _identity_relative_id(str(row["id"])),
                "target_id": _identity_relative_id(str(target)) if target is not None else None,
            }
        )
    return result


def _identity_relative_id(value: str) -> str:
    """Remove only the extraction namespace from a canonical record ID."""
    _, separator, relative = value.partition("/")
    if not separator or not relative:
        raise ValueError(f"canonical record ID lacks an extraction namespace: {value!r}")
    return relative
