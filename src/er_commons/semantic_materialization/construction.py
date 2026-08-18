"""Assemble the accepted hierarchy projection onto remapped canonical records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.semantic_materialization.aliases import (
    build_appendix_p_alias_seeds,
    build_target_aliases,
)
from er_commons.semantic_materialization.baseline import (
    load_baseline_candidate,
    prepare_semantic_content_in_place,
    remap_candidate_namespace,
    restore_placed_content_families_in_place,
)
from er_commons.semantic_materialization.config import SemanticExpectations
from er_commons.semantic_materialization.page_labels import build_page_label_observations
from er_commons.semantic_materialization.producer_evidence import (
    ProducerEvidence,
    artifact_reference,
    attach_stable_keys_in_place,
    build_bridge_construction,
    hierarchy_relevant_keys,
    load_producer_evidence,
    replacement_dispositions,
)
from er_commons.semantic_materialization.sections import build_semantic_sections
from er_commons.semantic_structure.policies.bridge import BridgeSourceEvidence

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class SemanticConstructionInputs:
    """Verified paths and frozen identifiers needed for one deterministic build."""

    baseline_candidate_root: Path
    baseline_producer_root: Path
    hierarchy_producer_root: Path
    hierarchy_candidate_root: Path
    baseline_candidate_id: str
    candidate_id: str
    baseline_producer_run_id: str
    hierarchy_producer_run_id: str
    source_id: str
    page_count: int
    expectations: SemanticExpectations | None


@dataclass(frozen=True)
class SemanticBuild:
    """All candidate records and independently derived bridge evidence before sealing."""

    collections: dict[str, list[JsonObject]]
    page_label_observations: list[JsonObject]
    target_aliases: list[JsonObject]
    bridge_entries: list[JsonObject]
    bridge_evidence: dict[str, BridgeSourceEvidence]
    observed_expectations: SemanticExpectations


def build_semantic_records(inputs: SemanticConstructionInputs) -> SemanticBuild:
    """Build the complete v2 extension from already sealed upstream artifacts."""
    baseline = load_baseline_candidate(inputs.baseline_candidate_root)
    collections = remap_candidate_namespace(
        baseline,
        old_extraction_id=inputs.baseline_candidate_id,
        new_extraction_id=inputs.candidate_id,
    )
    evidence = load_producer_evidence(
        baseline_producer_root=inputs.baseline_producer_root,
        hierarchy_producer_root=inputs.hierarchy_producer_root,
        hierarchy_root=inputs.hierarchy_candidate_root,
    )
    block_id_by_key = attach_stable_keys_in_place(
        collections["blocks"], evidence.baseline_key_by_pointer
    )
    ordered_content_with_transient_fields = prepare_semantic_content_in_place(collections)
    sections, placed_content = _place_semantic_content(
        ordered_content=ordered_content_with_transient_fields,
        document_id=collections["documents"][0]["id"],
        evidence=evidence,
        inputs=inputs,
    )
    restore_placed_content_families_in_place(collections, placed_content)
    bridge = build_bridge_construction(
        evidence=evidence,
        baseline_producer_root=inputs.baseline_producer_root,
        collections=collections,
        block_id_by_key=block_id_by_key,
        baseline_producer_run_id=inputs.baseline_producer_run_id,
        hierarchy_producer_run_id=inputs.hierarchy_producer_run_id,
        expected_coverage=inputs.expectations,
    )
    page_labels = build_page_label_observations(
        page_count=inputs.page_count,
        item_features=evidence.item_features,
        visible_evidence_ref=artifact_reference(
            inputs.hierarchy_candidate_root, "artifacts/item_features.jsonl"
        ),
    )
    for page, observation in zip(collections["pages"], page_labels, strict=True):
        page["printed_page_label"] = observation["resolved_label"]
    aliases = build_target_aliases(
        build_appendix_p_alias_seeds(
            collections=collections,
            sections=sections,
            evidence=evidence,
            page_labels=page_labels,
            hierarchy_root=inputs.hierarchy_candidate_root,
            baseline_root=inputs.baseline_candidate_root,
        ),
        extraction_id=inputs.candidate_id,
        document_id=collections["documents"][0]["id"],
        source_id=inputs.source_id,
    )
    collections["sections"] = sections
    observed = SemanticExpectations(
        section_count=len(sections),
        bridge_entry_count=bridge.coverage.entry_count,
        canonical_block_count=bridge.coverage.canonical_block_count,
        heading_count=sum(item.get("corrected_role") == "heading" for item in evidence.decisions),
        direct_membership_count=len(evidence.hierarchy["direct_membership"]),
        mapped_block_count=sum(
            item.get("semantic_placement") == "direct_body" for item in collections["blocks"]
        ),
        table_replacement_count=bridge.coverage.table_replacement_count,
        figure_suppression_count=bridge.coverage.figure_suppression_count,
    )
    return SemanticBuild(
        collections=collections,
        page_label_observations=page_labels,
        target_aliases=aliases,
        bridge_entries=bridge.entries,
        bridge_evidence=bridge.evidence,
        observed_expectations=observed,
    )


def _place_semantic_content(
    *,
    ordered_content: list[JsonObject],
    document_id: str,
    evidence: ProducerEvidence,
    inputs: SemanticConstructionInputs,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Project accepted hierarchy roles onto the remapped mixed-content stream."""
    replacement_keys = set(
        replacement_dispositions(
            baseline_document=evidence.baseline_document,
            producer_root=inputs.baseline_producer_root,
            key_by_pointer=evidence.baseline_key_by_pointer,
            relevant_keys=hierarchy_relevant_keys(evidence.hierarchy, []),
        )
    )
    return build_semantic_sections(
        ordered_content,
        document_id=document_id,
        extraction_id=inputs.candidate_id,
        source_id=inputs.source_id,
        features=evidence.item_features,
        decisions=evidence.decisions,
        hierarchy=evidence.hierarchy,
        evidence_ref=artifact_reference(
            inputs.hierarchy_candidate_root, "artifacts/decisions.jsonl"
        ),
        replacement_keys=replacement_keys,
    )
