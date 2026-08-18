"""Construct deterministic target-side aliases without extracting mentions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from er_commons.semantic_materialization.producer_evidence import (
    ProducerEvidence,
    artifact_reference,
)
from er_commons.semantic_structure.errors import SemanticContractError
from er_commons.semantic_structure.normalization import normalize_alias

JsonObject = dict[str, Any]

TARGET_TYPE_ORDER = {"document": 0, "section": 1, "table": 2, "figure": 3, "page": 4}


@dataclass(frozen=True)
class AliasSeed:
    """One source spelling and target before normalized collisions are grouped."""

    alias_kind: str
    raw_value: str
    target_id: str
    target_type: str
    target_order: int
    evidence_kind: str
    evidence_ref: JsonObject
    toc_reconciliation_ref: JsonObject | None = None

    @classmethod
    def canonical_target(
        cls,
        *,
        alias_kind: str,
        raw_value: str,
        target_id: str,
        target_type: str,
        target_order: int,
        evidence_kind: str,
        evidence_ref: JsonObject,
    ) -> AliasSeed:
        """Name an alias derived directly from one canonical target."""
        return cls(
            alias_kind=alias_kind,
            raw_value=raw_value,
            target_id=target_id,
            target_type=target_type,
            target_order=target_order,
            evidence_kind=evidence_kind,
            evidence_ref=evidence_ref,
        )

    @classmethod
    def reconciled_toc_target(
        cls,
        *,
        alias_kind: str,
        raw_value: str,
        target_id: str,
        target_order: int,
        toc_reconciliation_ref: JsonObject,
    ) -> AliasSeed:
        """Name an alias that visible-TOC evidence reconciles to one section."""
        return cls(
            alias_kind=alias_kind,
            raw_value=raw_value,
            target_id=target_id,
            target_type="section",
            target_order=target_order,
            evidence_kind="visible_toc_reconciliation",
            evidence_ref=toc_reconciliation_ref,
            toc_reconciliation_ref=toc_reconciliation_ref,
        )


def build_appendix_p_alias_seeds(
    *,
    collections: dict[str, list[JsonObject]],
    sections: list[JsonObject],
    evidence: ProducerEvidence,
    page_labels: list[JsonObject],
    hierarchy_root: Path,
    baseline_root: Path,
) -> list[AliasSeed]:
    """Derive Appendix P target aliases from canonical and accepted evidence."""
    blocks_by_key = {
        item["stable_item_key"]: item
        for item in collections["blocks"]
        if item.get("stable_item_key") is not None
    }
    sections_by_key = {
        item["source_stable_item_key"]: item
        for item in sections
        if item["section_kind"] == "semantic"
    }
    features_by_key = {item["stable_item_key"]: item for item in evidence.item_features}
    decisions_ref = artifact_reference(hierarchy_root, "artifacts/decisions.jsonl")
    item_features_ref = artifact_reference(hierarchy_root, "artifacts/item_features.jsonl")
    toc_ref = artifact_reference(hierarchy_root, "artifacts/toc_reconciliation.jsonl")
    document_ref = artifact_reference(baseline_root, "canonical/documents.jsonl")
    document = collections["documents"][0]
    seeds = [
        AliasSeed.canonical_target(
            alias_kind="document",
            raw_value=document["title"],
            target_id=document["id"],
            target_type="document",
            target_order=0,
            evidence_kind="canonical_title",
            evidence_ref=document_ref,
        )
    ]
    for key, section in sections_by_key.items():
        block = blocks_by_key[key]
        text = block["canonical_text"]
        seeds.append(
            AliasSeed.canonical_target(
                alias_kind="appendix" if text.casefold().startswith("appendix ") else "section",
                raw_value=text,
                target_id=section["id"],
                target_type="section",
                target_order=block["sequence"],
                evidence_kind="heading_text",
                evidence_ref=decisions_ref,
            )
        )
    reconciliation_by_id = {item["toc_entry_id"]: item for item in evidence.toc_reconciliations}
    for toc in evidence.visible_toc_entries:
        reconciliation = reconciliation_by_id[toc["toc_entry_id"]]
        if reconciliation["state"] != "exact":
            continue
        target_key = reconciliation["target_key"]
        if (
            not isinstance(target_key, str)
            or target_key not in features_by_key
            or target_key not in sections_by_key
            or target_key not in blocks_by_key
        ):
            raise SemanticContractError("exact TOC alias target is absent from semantic content")
        raw_value = features_by_key[target_key]["text"]
        seeds.append(
            AliasSeed.reconciled_toc_target(
                alias_kind=(
                    "appendix" if raw_value.casefold().startswith("appendix ") else "section"
                ),
                raw_value=toc["title_with_marker_normalized"],
                target_id=sections_by_key[target_key]["id"],
                target_order=blocks_by_key[target_key]["sequence"],
                toc_reconciliation_ref=toc_ref,
            )
        )
    for observation, page in zip(page_labels, collections["pages"], strict=True):
        if observation["resolved_state"] == "resolved":
            seeds.append(
                AliasSeed.canonical_target(
                    alias_kind="printed_page",
                    raw_value=observation["resolved_label"],
                    target_id=page["id"],
                    target_type="page",
                    target_order=page["physical_page_number"],
                    evidence_kind="resolved_printed_page_label",
                    evidence_ref=item_features_ref,
                )
            )
    return prefer_reconciled_toc_evidence(seeds)


def prefer_reconciled_toc_evidence(seeds: list[AliasSeed]) -> list[AliasSeed]:
    """Prefer visible-TOC evidence when it names an already-known target alias."""
    preferred = {
        (seed.alias_kind, normalize_alias(seed.raw_value), seed.target_id): seed
        for seed in seeds
        if seed.evidence_kind == "visible_toc_reconciliation"
    }
    return [
        replace(
            seed,
            evidence_kind=chosen.evidence_kind,
            evidence_ref=chosen.evidence_ref,
            toc_reconciliation_ref=chosen.toc_reconciliation_ref,
        )
        if (
            chosen := preferred.get(
                (seed.alias_kind, normalize_alias(seed.raw_value), seed.target_id)
            )
        )
        else seed
        for seed in seeds
    ]


def build_target_aliases(
    seeds: list[AliasSeed],
    *,
    extraction_id: str,
    document_id: str,
    source_id: str,
) -> list[JsonObject]:
    """Group normalized keys, order targets, and allocate candidate-local IDs."""
    groups: dict[tuple[str, str], list[AliasSeed]] = {}
    for seed in seeds:
        normalized = normalize_alias(seed.raw_value)
        if not normalized:
            raise SemanticContractError("target alias normalizes to an empty value")
        groups.setdefault((seed.alias_kind, normalized), []).append(seed)

    prepared: list[tuple[tuple[Any, ...], str, str, list[str], list[AliasSeed]]] = []
    for (alias_kind, normalized), group in groups.items():
        target_types = {seed.target_type for seed in group}
        if len(target_types) != 1:
            raise SemanticContractError(f"one alias key has mixed target types: {alias_kind}")
        by_target: dict[str, list[AliasSeed]] = {}
        for seed in group:
            by_target.setdefault(seed.target_id, []).append(seed)
        ordered = []
        for target_group in by_target.values():
            representative = target_group[0]
            target_facts = {
                (
                    seed.target_type,
                    seed.target_order,
                    seed.evidence_kind,
                    repr(seed.evidence_ref),
                    repr(seed.toc_reconciliation_ref),
                )
                for seed in target_group
            }
            if len(target_facts) != 1:
                raise SemanticContractError(
                    f"one alias target has contradictory evidence: {representative.target_id}"
                )
            ordered.append(representative)
        ordered.sort(key=lambda seed: (seed.target_order, seed.target_id))
        target_type = ordered[0].target_type
        prepared.append(
            (
                (
                    TARGET_TYPE_ORDER[target_type],
                    ordered[0].target_order,
                    alias_kind,
                    normalized.encode(),
                ),
                alias_kind,
                normalized,
                sorted(
                    set(seed.raw_value for seed in group), key=lambda value: value.encode("utf-8")
                ),
                ordered,
            )
        )

    aliases = []
    for sequence, (_, alias_kind, normalized, raw_values, targets) in enumerate(
        sorted(prepared), start=1
    ):
        aliases.append(
            {
                "id": f"{extraction_id}/target-alias/{source_id}/alias{sequence:06d}",
                "document_id": document_id,
                "sequence": sequence,
                "alias_kind": alias_kind,
                "raw_values": raw_values,
                "normalized_alias": normalized,
                "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
                "resolution_status": "unique" if len(targets) == 1 else "ambiguous",
                "targets": [
                    {
                        "target_id": seed.target_id,
                        "target_type": seed.target_type,
                        "evidence_kind": seed.evidence_kind,
                        "evidence_ref": seed.evidence_ref,
                        "toc_reconciliation_ref": seed.toc_reconciliation_ref,
                    }
                    for seed in targets
                ],
            }
        )
    return aliases
