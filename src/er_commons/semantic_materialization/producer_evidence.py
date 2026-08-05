"""Read accepted producer evidence and derive the independent bridge inputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.provenance import descendant_text_pointers
from er_commons.canonical_extraction.tables import load_producer_table_bundle
from er_commons.document_extraction.hierarchy.document import DocumentIndex
from er_commons.semantic_materialization.bridge import BridgeItem, build_cross_producer_bridge
from er_commons.semantic_materialization.config import SemanticExpectations
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_structure.policies.bridge import BridgeSourceEvidence

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ProducerEvidence:
    """Saved producer and corrected-hierarchy payloads used by construction."""

    baseline_document: JsonObject
    hierarchy_document: JsonObject
    item_features: list[JsonObject]
    decisions: list[JsonObject]
    hierarchy: JsonObject
    visible_toc_entries: list[JsonObject]
    toc_reconciliations: list[JsonObject]
    baseline_key_by_pointer: dict[str, str]
    hierarchy_key_by_pointer: dict[str, str]


@dataclass(frozen=True)
class BridgeCoverage:
    """The handoff counts that protect the bridge from partial construction."""

    entry_count: int
    canonical_block_count: int
    table_replacement_count: int
    figure_suppression_count: int


@dataclass(frozen=True)
class BridgeConstruction:
    """Candidate bridge rows plus the evidence needed by semantic validation."""

    entries: list[JsonObject]
    evidence: dict[str, BridgeSourceEvidence]
    coverage: BridgeCoverage


def load_producer_evidence(
    *,
    baseline_producer_root: Path,
    hierarchy_producer_root: Path,
    hierarchy_root: Path,
) -> ProducerEvidence:
    """Load only the saved evidence required by the accepted semantic join."""
    baseline_document = load_json_object(baseline_producer_root / "docling" / "document.json")
    hierarchy_document = load_json_object(hierarchy_producer_root / "docling" / "document.json")
    baseline_key_by_pointer = stable_key_by_pointer(baseline_document)
    hierarchy_key_by_pointer = stable_key_by_pointer(hierarchy_document)
    if set(baseline_key_by_pointer.values()) != set(hierarchy_key_by_pointer.values()):
        raise SemanticMaterializationInvariantError(
            stage="producer evidence",
            invariant="baseline and hierarchy producer stable-key sets agree",
            expected=len(baseline_key_by_pointer),
            observed=len(hierarchy_key_by_pointer),
            subject="producer document pair",
        )
    return ProducerEvidence(
        baseline_document=baseline_document,
        hierarchy_document=hierarchy_document,
        item_features=load_jsonl(hierarchy_root / "artifacts" / "item_features.jsonl"),
        decisions=load_jsonl(hierarchy_root / "artifacts" / "decisions.jsonl"),
        hierarchy=load_json_object(hierarchy_root / "artifacts" / "hierarchy.json"),
        visible_toc_entries=load_jsonl(hierarchy_root / "artifacts" / "visible_toc_entries.jsonl"),
        toc_reconciliations=load_jsonl(hierarchy_root / "artifacts" / "toc_reconciliation.jsonl"),
        baseline_key_by_pointer=baseline_key_by_pointer,
        hierarchy_key_by_pointer=hierarchy_key_by_pointer,
    )


def attach_stable_keys_in_place(
    blocks: list[JsonObject], key_by_pointer: dict[str, str]
) -> dict[str, str]:
    """Mutate canonical blocks with verified producer keys and index their IDs."""
    block_id_by_key: dict[str, str] = {}
    for block in blocks:
        pointer = block["raw_links"][0]["object_pointer"]
        try:
            key = key_by_pointer[pointer]
        except KeyError as error:
            raise SemanticMaterializationInvariantError(
                stage="producer evidence",
                invariant="canonical block pointer has a baseline stable key",
                expected="known producer pointer",
                observed=pointer,
                subject=block["id"],
            ) from error
        block["stable_item_key"] = key
        block_id_by_key[key] = block["id"]
    return block_id_by_key


def build_bridge_construction(
    *,
    evidence: ProducerEvidence,
    baseline_producer_root: Path,
    collections: dict[str, list[JsonObject]],
    block_id_by_key: dict[str, str],
    baseline_producer_run_id: str,
    hierarchy_producer_run_id: str,
    expected_coverage: SemanticExpectations | None,
) -> BridgeConstruction:
    """Build bridge rows from producer pointers, never candidate self-evidence."""
    relevant_keys = hierarchy_relevant_keys(evidence.hierarchy, collections["blocks"])
    dispositions = replacement_dispositions(
        baseline_document=evidence.baseline_document,
        producer_root=baseline_producer_root,
        key_by_pointer=evidence.baseline_key_by_pointer,
        relevant_keys=relevant_keys,
    )
    canonical_block_by_key = {
        key: block_id_by_key[key]
        for key in relevant_keys
        if key in block_id_by_key and key not in dispositions
    }
    hierarchy_pointer_by_key = {
        key: pointer for pointer, key in evidence.hierarchy_key_by_pointer.items()
    }
    baseline_pointer_by_key = {
        key: pointer for pointer, key in evidence.baseline_key_by_pointer.items()
    }
    bridge_items = [
        BridgeItem(key, hierarchy_pointer_by_key[key], baseline_pointer_by_key[key])
        for key in (item["stable_item_key"] for item in evidence.item_features)
        if key in relevant_keys
    ]
    entries, bridge_evidence = build_cross_producer_bridge(
        bridge_items,
        hierarchy_producer_run_id=hierarchy_producer_run_id,
        baseline_producer_run_id=baseline_producer_run_id,
        canonical_block_by_key=canonical_block_by_key,
        disposition_by_key=dispositions,
    )
    coverage = BridgeCoverage(
        entry_count=len(entries),
        canonical_block_count=len(canonical_block_by_key),
        table_replacement_count=sum(
            value == "canonical_table_replacement_descendant" for value in dispositions.values()
        ),
        figure_suppression_count=sum(
            value == "canonical_figure_suppressed_descendant" for value in dispositions.values()
        ),
    )
    if expected_coverage is not None:
        _assert_accepted_bridge_coverage(coverage, expected_coverage)
    return BridgeConstruction(entries, bridge_evidence, coverage)


def artifact_reference(root: Path, relative_path: str) -> JsonObject:
    """Create the persisted checksum reference for one verified evidence file."""
    path = root / relative_path
    return {"path": relative_path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def load_json_object(path: Path) -> JsonObject:
    """Load one persisted JSON object with an early shape check."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise SemanticMaterializationInvariantError(
            stage="producer evidence",
            invariant="JSON evidence is an object",
            expected="object",
            observed=type(value).__name__,
            subject=path.as_posix(),
        )
    return value


def load_jsonl(path: Path) -> list[JsonObject]:
    """Load one ordered JSONL evidence collection."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def stable_key_by_pointer(document: JsonObject) -> dict[str, str]:
    """Index saved Docling text-item pointers by their stable item keys."""
    index = DocumentIndex.build(document)
    return {item["self_ref"]: key for key, item in index.text_items.items()}


def hierarchy_relevant_keys(hierarchy: JsonObject, blocks: list[JsonObject]) -> set[str]:
    """Return every correction-controlled key plus retained furniture keys."""
    keys = set(hierarchy["roots"])
    keys.update(edge["child_key"] for edge in hierarchy["edges"])
    keys.update(item["item_key"] for item in hierarchy["direct_membership"])
    keys.update(hierarchy["unassigned_content"])
    keys.update(
        item["stable_item_key"] for item in blocks if item["semantic_placement"] == "furniture"
    )
    return keys


def replacement_dispositions(
    *,
    baseline_document: JsonObject,
    producer_root: Path,
    key_by_pointer: dict[str, str],
    relevant_keys: set[str],
) -> dict[str, str]:
    """Explain text hidden beneath canonical table and figure replacements."""
    table_bundle = load_producer_table_bundle(producer_root)
    mapped_table_refs = {
        mapping.raw_object_ref
        for mapping in table_bundle.region_mappings
        if mapping.clean_table_ids
    }
    table_pointers: set[str] = set()
    for raw_ref in sorted(mapped_table_refs):
        index = int(raw_ref.rsplit("/", 1)[-1])
        table = baseline_document["tables"][index]
        captions = {item["$ref"] for item in table.get("captions", [])}
        roots = [item for item in table["children"] if item["$ref"] not in captions]
        table_pointers.update(descendant_text_pointers(baseline_document, roots))
    picture_pointers: set[str] = set()
    for picture in baseline_document["pictures"]:
        captions = {item["$ref"] for item in picture.get("captions", [])}
        roots = [item for item in picture["children"] if item["$ref"] not in captions]
        picture_pointers.update(descendant_text_pointers(baseline_document, roots))
    dispositions = {
        key_by_pointer[pointer]: "canonical_table_replacement_descendant"
        for pointer in table_pointers
        if key_by_pointer[pointer] in relevant_keys
    }
    dispositions.update(
        {
            key_by_pointer[pointer]: "canonical_figure_suppressed_descendant"
            for pointer in picture_pointers
            if key_by_pointer[pointer] in relevant_keys
        }
    )
    return dispositions


def _assert_accepted_bridge_coverage(
    coverage: BridgeCoverage, expected_counts: SemanticExpectations
) -> None:
    expected = BridgeCoverage(
        expected_counts.bridge_entry_count,
        expected_counts.canonical_block_count,
        expected_counts.table_replacement_count,
        expected_counts.figure_suppression_count,
    )
    if coverage != expected:
        raise SemanticMaterializationInvariantError(
            stage="bridge construction",
            invariant="accepted Task 03E.3 bridge coverage",
            expected=expected,
            observed=coverage,
            subject="configured producer evidence",
        )
