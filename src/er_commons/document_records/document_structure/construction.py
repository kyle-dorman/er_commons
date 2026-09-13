"""Assemble the accepted hierarchy projection onto remapped canonical records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from er_commons.document_records.document_structure.aliases import (
    build_appendix_p_alias_seeds,
    build_target_aliases,
)
from er_commons.document_records.document_structure.baseline import (
    load_baseline_candidate,
    prepare_semantic_content_in_place,
    remap_candidate_namespace,
    restore_placed_content_families_in_place,
)
from er_commons.document_records.document_structure.config import DocumentStructureExpectations
from er_commons.document_records.document_structure.page_labels import build_page_label_observations
from er_commons.document_records.document_structure.parser_evidence import (
    ProducerEvidence,
    artifact_reference,
    attach_stable_keys_in_place,
    build_bridge_construction,
    load_producer_evidence,
)
from er_commons.document_records.document_structure.policies.bridge import BridgeSourceEvidence
from er_commons.document_records.document_structure.replacement_evidence import (
    hierarchy_relevant_keys,
    replacement_dispositions,
)
from er_commons.document_records.document_structure.sections import build_document_sections

JsonObject = dict[str, Any]

if TYPE_CHECKING:
    from er_commons.document_records.document_structure.missing_chapters import (
        MissingChapterDecision,
        MissingChapterProjection,
    )
    from er_commons.document_records.document_structure.repeated_headings import (
        RepeatedHeadingDecision,
    )


class _SemanticProjection(Protocol):
    """Structural result shared by the unchanged v1 and repaired v2 paths."""

    @property
    def sections(self) -> list[JsonObject]: ...

    @property
    def content(self) -> list[JsonObject]: ...

    @property
    def section_target_redirects(self) -> dict[str, str]: ...

    @property
    def heading_target_redirects(self) -> dict[str, str]: ...

    @property
    def source_section_target_correspondence(self) -> dict[str, str]: ...


@dataclass(frozen=True)
class _UnchangedProjection:
    """Dependency-free projection result for canonical-v1 construction."""

    sections: list[JsonObject]
    content: list[JsonObject]
    section_target_redirects: dict[str, str]
    heading_target_redirects: dict[str, str]
    source_section_target_correspondence: dict[str, str]


@dataclass(frozen=True)
class _SemanticPlacement:
    """Final semantic records plus the optional concrete 06E projection result."""

    final_projection: _SemanticProjection
    missing_chapter_projection: MissingChapterProjection | None


@dataclass(frozen=True)
class DocumentStructureConstructionInputs:
    """Verified paths and frozen identifiers needed for one deterministic build."""

    baseline_candidate_root: Path
    baseline_producer_root: Path
    baseline_document: JsonObject
    hierarchy_producer_root: Path
    hierarchy_document: JsonObject
    hierarchy_candidate_root: Path
    baseline_candidate_id: str
    candidate_id: str
    baseline_producer_run_id: str
    hierarchy_producer_run_id: str
    source_id: str
    page_count: int
    expectations: DocumentStructureExpectations | None
    repeated_heading_repair_enabled: bool = False
    repeated_heading_decisions: tuple[RepeatedHeadingDecision, ...] = ()
    missing_chapter_repair_enabled: bool = False
    missing_chapter_decisions: tuple[MissingChapterDecision, ...] = ()
    missing_chapter_decisions_ref: JsonObject | None = None


@dataclass(frozen=True)
class DocumentStructureBuild:
    """All candidate records and independently derived bridge evidence before sealing."""

    collections: dict[str, list[JsonObject]]
    page_label_observations: list[JsonObject]
    target_aliases: list[JsonObject]
    bridge_entries: list[JsonObject]
    bridge_evidence: dict[str, BridgeSourceEvidence]
    repeated_heading_correspondence: list[JsonObject]
    missing_chapter_correspondence: list[JsonObject]
    observed_expectations: DocumentStructureExpectations


def build_document_structure_records(
    inputs: DocumentStructureConstructionInputs,
) -> DocumentStructureBuild:
    """Build the complete v2 extension from already sealed upstream artifacts."""
    baseline = load_baseline_candidate(inputs.baseline_candidate_root)
    collections = remap_candidate_namespace(
        baseline,
        old_extraction_id=inputs.baseline_candidate_id,
        new_extraction_id=inputs.candidate_id,
    )
    evidence = load_producer_evidence(
        baseline_document=inputs.baseline_document,
        hierarchy_document=inputs.hierarchy_document,
        hierarchy_root=inputs.hierarchy_candidate_root,
    )
    block_id_by_key = attach_stable_keys_in_place(
        collections["blocks"], evidence.baseline_key_by_pointer
    )
    ordered_content_with_transient_fields = prepare_semantic_content_in_place(collections)
    semantic_placement = _place_semantic_content(
        ordered_content=ordered_content_with_transient_fields,
        document_id=collections["documents"][0]["id"],
        evidence=evidence,
        inputs=inputs,
    )
    final_projection = semantic_placement.final_projection
    sections = final_projection.sections
    restore_placed_content_families_in_place(collections, final_projection.content)
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
    alias_seeds = build_appendix_p_alias_seeds(
        collections=collections,
        sections=sections,
        evidence=evidence,
        page_labels=page_labels,
        hierarchy_root=inputs.hierarchy_candidate_root,
        baseline_root=inputs.baseline_candidate_root,
        heading_target_redirects=final_projection.heading_target_redirects,
    )
    if inputs.missing_chapter_repair_enabled:
        from er_commons.document_records.document_structure.missing_chapters import (
            build_missing_chapter_alias_seeds,
            prefer_missing_chapter_alias_evidence,
        )

        missing_projection = semantic_placement.missing_chapter_projection
        if missing_projection is None:
            raise ValueError("missing-chapter repair lacks its concrete projection result")
        alias_seeds.extend(
            build_missing_chapter_alias_seeds(inputs.missing_chapter_decisions, missing_projection)
        )
        alias_seeds = prefer_missing_chapter_alias_evidence(alias_seeds)
    aliases = build_target_aliases(
        alias_seeds,
        extraction_id=inputs.candidate_id,
        document_id=collections["documents"][0]["id"],
        source_id=inputs.source_id,
    )
    collections["sections"] = sections
    observed = DocumentStructureExpectations(
        section_count=len(sections),
        bridge_entry_count=bridge.coverage.entry_count,
        canonical_block_count=bridge.coverage.canonical_block_count,
        heading_count=sum(not item["section_kind"].startswith("synthetic_") for item in sections),
        direct_membership_count=len(evidence.hierarchy["direct_membership"]),
        mapped_block_count=sum(
            item.get("semantic_placement") == "direct_body" for item in collections["blocks"]
        ),
        table_replacement_count=bridge.coverage.table_replacement_count,
        figure_suppression_count=bridge.coverage.figure_suppression_count,
    )
    return DocumentStructureBuild(
        collections=collections,
        page_label_observations=page_labels,
        target_aliases=aliases,
        bridge_entries=bridge.entries,
        bridge_evidence=bridge.evidence,
        repeated_heading_correspondence=_repeated_heading_correspondence(inputs, final_projection),
        missing_chapter_correspondence=_missing_chapter_correspondence(
            inputs, semantic_placement.missing_chapter_projection
        ),
        observed_expectations=observed,
    )


def _place_semantic_content(
    *,
    ordered_content: list[JsonObject],
    document_id: str,
    evidence: ProducerEvidence,
    inputs: DocumentStructureConstructionInputs,
) -> _SemanticPlacement:
    """Project accepted hierarchy roles onto the remapped mixed-content stream."""
    replacement_keys = set(
        replacement_dispositions(
            baseline_document=evidence.baseline_document,
            producer_root=inputs.baseline_producer_root,
            key_by_pointer=evidence.baseline_key_by_pointer,
            relevant_keys=hierarchy_relevant_keys(evidence.hierarchy, []),
        )
    )
    sections, content = build_document_sections(
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
    if not inputs.repeated_heading_repair_enabled:
        if inputs.repeated_heading_decisions:
            raise ValueError("canonical-v1 construction cannot apply repeated-heading decisions")
        repaired_projection: _SemanticProjection = _UnchangedProjection(
            sections, content, {}, {}, {}
        )
    else:
        from er_commons.document_records.document_structure.repeated_headings import (
            project_repeated_heading_decisions,
        )

        repaired_projection = project_repeated_heading_decisions(
            sections,
            content,
            inputs.repeated_heading_decisions,
        )
    missing_projection: MissingChapterProjection | None = None
    if inputs.missing_chapter_repair_enabled:
        from er_commons.document_records.document_structure.missing_chapters import (
            project_missing_chapter_decisions,
        )

        missing_projection = project_missing_chapter_decisions(
            repaired_projection.sections,
            repaired_projection.content,
            inputs.missing_chapter_decisions,
            section_target_redirects=repaired_projection.section_target_redirects,
            heading_target_redirects=repaired_projection.heading_target_redirects,
            source_section_target_correspondence=(
                repaired_projection.source_section_target_correspondence
            ),
            decisions_ref=inputs.missing_chapter_decisions_ref,
            page_count=inputs.page_count,
        )
    elif inputs.missing_chapter_decisions:
        raise ValueError("pre-v3 construction cannot apply missing-chapter decisions")
    return _SemanticPlacement(
        final_projection=missing_projection or repaired_projection,
        missing_chapter_projection=missing_projection,
    )


def _repeated_heading_correspondence(
    inputs: DocumentStructureConstructionInputs,
    projection: _SemanticProjection,
) -> list[JsonObject]:
    """Build v2-only correspondence without importing repair code on v1."""
    if not inputs.repeated_heading_repair_enabled:
        return []
    from er_commons.document_records.document_structure.repeated_headings import (
        build_repeated_heading_correspondence,
    )

    return [
        build_repeated_heading_correspondence(decision, projection)
        for decision in inputs.repeated_heading_decisions
    ]


def _missing_chapter_correspondence(
    inputs: DocumentStructureConstructionInputs,
    projection: MissingChapterProjection | None,
) -> list[JsonObject]:
    """Build v3-only correspondence without importing repair code on v1/v2."""
    if not inputs.missing_chapter_repair_enabled:
        return []
    if projection is None:
        raise ValueError("missing-chapter repair lacks its concrete projection result")
    from er_commons.document_records.document_structure.missing_chapters import (
        build_missing_chapter_correspondence,
    )

    return [
        build_missing_chapter_correspondence(decision, projection)
        for decision in inputs.missing_chapter_decisions
    ]
