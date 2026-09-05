"""Source-free Task 04D reconciliation over accepted TOC text and body aliases."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from er_commons.artifact_io import iter_jsonl
from er_commons.document_records.document_references.exact_resolution import (
    ExactAliasEvidence,
    ExactResolutionOutcome,
    normalize_exact_text,
)
from er_commons.document_records.document_references.linking_policy import (
    DocumentLinkingPolicy,
)
from er_commons.navigation_overlay.link_resolution import resolve_toc_heading

JsonObject = dict[str, Any]


class Task04DEntryOutcome(StrEnum):
    """Inspectable reconciliation outcomes before artifact publication."""

    UNSUPPORTED_ENTRY_SHAPE = "unsupported_entry_shape"
    NO_DESTINATION_PAGE = "no_destination_page"
    NO_TARGET_ALIAS = "no_target_alias"
    PARENT_SCOPE_MISMATCH = "parent_scope_mismatch"
    DESTINATION_TARGET_PAGE_MISMATCH = "destination_target_page_mismatch"
    AMBIGUOUS_TARGET = "ambiguous_target"
    RESOLVED_UNIQUE = "resolved_unique"


@dataclass(frozen=True)
class Task04DDocumentIndex:
    """Eligible exact aliases and printed-page destinations for one document."""

    exact_aliases: tuple[ExactAliasEvidence, ...]
    destination_page_ids: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        """Copy the destination index so a frozen instance is actually immutable."""
        copied = {
            key: tuple(sorted(value)) for key, value in sorted(self.destination_page_ids.items())
        }
        object.__setattr__(self, "destination_page_ids", MappingProxyType(copied))


def load_task04d_document_index(document_root: Path) -> Task04DDocumentIndex:
    """Load validated resolver evidence without changing sealed target aliases."""
    canonical = document_root / "content/canonical"
    required = {
        "pages": canonical / "pages.jsonl",
        "blocks": canonical / "blocks.jsonl",
        "sections": canonical / "sections.jsonl",
        "tables": canonical / "tables.jsonl",
        "figures": canonical / "figures.jsonl",
        "aliases": canonical / "target_aliases.jsonl",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise ValueError(f"Task 04D canonical evidence is incomplete: missing={missing}")

    pages = list(iter_jsonl(required["pages"]))
    page_by_id = {_required_text(page, "id", path=required["pages"]): page for page in pages}
    entities: dict[str, JsonObject] = {}
    entity_kinds: dict[str, str] = {}
    entity_pages: dict[str, tuple[str, ...]] = {}
    for name, target_type in (
        ("blocks", "block"),
        ("sections", "section"),
        ("tables", "table"),
        ("figures", "figure"),
    ):
        path = required[name]
        for entity in iter_jsonl(path):
            entity_id = _required_text(entity, "id", path=path)
            if entity_id in entities:
                raise ValueError(f"duplicate canonical entity id {entity_id!r}: {path}")
            entities[entity_id] = entity
            entity_kinds[entity_id] = target_type
            if target_type != "section":
                entity_pages[entity_id] = _region_page_ids(entity, path=path)
    for entity_id, entity in entities.items():
        if entity_kinds[entity_id] != "section":
            continue
        heading_id = entity.get("heading_block_id")
        if heading_id is not None and not isinstance(heading_id, str):
            raise ValueError(
                f"canonical section {entity_id!r} has a non-string heading_block_id: "
                f"{required['sections']}"
            )
        entity_pages[entity_id] = (
            entity_pages.get(heading_id, ()) if isinstance(heading_id, str) else ()
        )

    exact_aliases: list[ExactAliasEvidence] = []
    destinations: dict[str, set[str]] = defaultdict(set)
    for alias in iter_jsonl(required["aliases"]):
        kind = _required_text(alias, "alias_kind", path=required["aliases"])
        lookup_key = normalize_exact_text(
            _required_text(alias, "normalized_alias", path=required["aliases"])
        )
        targets = alias.get("targets")
        if not isinstance(targets, list):
            raise ValueError(f"alias targets must be a list: {required['aliases']}")
        for target in targets:
            if not isinstance(target, dict):
                raise ValueError(f"alias target must be an object: {required['aliases']}")
            target_id = _required_text(target, "target_id", path=required["aliases"])
            target_type = _required_text(target, "target_type", path=required["aliases"])
            if kind == "printed_page" and target_type == "page":
                page = page_by_id.get(target_id)
                if page is None:
                    raise ValueError(
                        f"printed-page alias targets unknown page {target_id!r}: "
                        f"{required['aliases']}"
                    )
                printed_label = page.get("printed_page_label")
                if isinstance(printed_label, str) and normalize_exact_text(
                    printed_label
                ) == normalize_exact_text(lookup_key):
                    destinations[lookup_key].add(target_id)
                continue
            target_entity = entities.get(target_id)
            if kind not in {"section", "table", "figure"}:
                continue
            if target_entity is None or entity_kinds[target_id] != kind or target_type != kind:
                raise ValueError(
                    f"{kind} alias targets incompatible entity {target_id!r}: {required['aliases']}"
                )
            if not _body_non_navigation(target_entity):
                continue
            exact_aliases.append(
                ExactAliasEvidence(
                    lookup_keys=(lookup_key,),
                    target_type=kind,
                    alias_id=_required_text(alias, "id", path=required["aliases"]),
                    target_id=target_id,
                    target_page_ids=entity_pages.get(target_id, ()),
                    parent_target_id=(
                        str(target_entity["parent_section_id"])
                        if kind == "section" and target_entity.get("parent_section_id") is not None
                        else None
                    ),
                )
            )
    return Task04DDocumentIndex(
        exact_aliases=tuple(
            sorted(
                exact_aliases,
                key=lambda alias: (alias.target_type, alias.alias_id, alias.target_id),
            )
        ),
        destination_page_ids={key: tuple(sorted(value)) for key, value in destinations.items()},
    )


def reconcile_task04d_entry(
    entry: JsonObject,
    index: Task04DDocumentIndex,
    *,
    policy: DocumentLinkingPolicy,
    resolved_parent_target_ids: tuple[str, ...] | None = None,
) -> JsonObject:
    """Return one inspectable Task 04D decision without publishing an artifact."""
    marker_kind = entry.get("marker_kind")
    if marker_kind not in {"section", "table", "figure"}:
        return _decision_record(
            entry,
            Task04DEntryOutcome.UNSUPPORTED_ENTRY_SHAPE,
            (),
            (),
            (),
            False,
        )
    terminal = entry.get("terminal_destination_token")
    terminal_text = str(terminal) if isinstance(terminal, str) else None
    destination_ids = (
        index.destination_page_ids.get(normalize_exact_text(terminal_text), ())
        if terminal_text is not None
        else None
    )
    decision = resolve_toc_heading(
        raw_entry_text=str(entry["raw_text"]),
        terminal_destination_token=terminal_text,
        target_type=str(marker_kind),
        aliases=index.exact_aliases,
        policy=policy,
        destination_page_ids=destination_ids,
        resolved_parent_target_ids=resolved_parent_target_ids,
    )
    if terminal_text is not None and not destination_ids:
        outcome = Task04DEntryOutcome.NO_DESTINATION_PAGE
    elif decision.outcome is ExactResolutionOutcome.NO_TEXT_MATCH:
        outcome = Task04DEntryOutcome.NO_TARGET_ALIAS
    elif decision.outcome is ExactResolutionOutcome.PARENT_SCOPE_MISMATCH:
        outcome = Task04DEntryOutcome.PARENT_SCOPE_MISMATCH
    elif decision.outcome is ExactResolutionOutcome.DESTINATION_PAGE_MISMATCH:
        outcome = Task04DEntryOutcome.DESTINATION_TARGET_PAGE_MISMATCH
    elif decision.outcome is ExactResolutionOutcome.AMBIGUOUS_TARGET:
        outcome = Task04DEntryOutcome.AMBIGUOUS_TARGET
    else:
        outcome = Task04DEntryOutcome.RESOLVED_UNIQUE
    return _decision_record(
        entry,
        outcome,
        tuple(candidate.target_id for candidate in decision.candidates),
        tuple(
            sorted(
                {alias_id for candidate in decision.candidates for alias_id in candidate.alias_ids}
            )
        ),
        decision.match_basis,
        decision.parent_scope_applied,
        resolver_outcome=decision.outcome,
        unscoped_text_candidate_count=decision.unscoped_text_candidate_count,
        scoped_text_candidate_count=decision.scoped_text_candidate_count,
    )


def reconcile_task04d_no_page_sections(
    *,
    entries_path: Path,
    document_publications_root: Path,
    policy: DocumentLinkingPolicy,
) -> tuple[list[JsonObject], JsonObject]:
    """Reconcile no-page sections read from explicitly selected artifact paths."""
    indexes: dict[tuple[str, str], Task04DDocumentIndex] = {}
    records: list[JsonObject] = []
    for entry in iter_jsonl(entries_path):
        if (
            entry.get("marker_kind") != "section"
            or entry.get("terminal_destination_token") is not None
        ):
            continue
        key = (str(entry["source_id"]), str(entry["candidate_id"]))
        if key not in indexes:
            indexes[key] = load_task04d_document_index(
                document_publications_root / "documents" / key[0] / key[1]
            )
        records.append(reconcile_task04d_entry(entry, indexes[key], policy=policy))
    counts = Counter(str(record["outcome"]) for record in records)
    summary: JsonObject = {
        "population_count": len(records),
        "outcome_counts": dict(sorted(counts.items())),
        "resolved_unique_count": counts["resolved_unique"],
        "unresolved_count": len(records) - counts["resolved_unique"],
    }
    return records, summary


def _decision_record(
    entry: JsonObject,
    outcome: Task04DEntryOutcome,
    target_ids: tuple[str, ...],
    alias_ids: tuple[str, ...],
    match_basis: tuple[str, ...],
    parent_scope_applied: bool,
    *,
    resolver_outcome: ExactResolutionOutcome | None = None,
    unscoped_text_candidate_count: int = 0,
    scoped_text_candidate_count: int = 0,
) -> JsonObject:
    return {
        "toc_text_entry_id": entry["toc_text_entry_id"],
        "source_id": entry["source_id"],
        "candidate_id": entry["candidate_id"],
        "raw_entry_text": entry["raw_text"],
        "terminal_destination_token": entry.get("terminal_destination_token"),
        "outcome": outcome.value,
        "target_ids": list(target_ids),
        "supporting_alias_ids": list(alias_ids),
        "match_basis": list(match_basis),
        "parent_scope_applied": parent_scope_applied,
        "resolver_outcome": resolver_outcome.value if resolver_outcome is not None else None,
        "unscoped_text_candidate_count": unscoped_text_candidate_count,
        "scoped_text_candidate_count": scoped_text_candidate_count,
    }


def _body_non_navigation(entity: JsonObject) -> bool:
    return (
        entity.get("content_layer") == "body"
        and not bool(entity.get("is_toc_row", False))
        and entity.get("semantic_placement") != "toc_content"
    )


def _region_page_ids(entity: JsonObject, *, path: Path) -> tuple[str, ...]:
    regions = entity.get("regions", [])
    if not isinstance(regions, list):
        raise ValueError(f"canonical entity regions must be a list: {path}")
    page_ids: set[str] = set()
    for region in regions:
        if not isinstance(region, dict):
            raise ValueError(f"canonical entity region must be an object: {path}")
        page_ids.add(_required_text(region, "page_id", path=path))
    return tuple(sorted(page_ids))


def _required_text(value: JsonObject, key: str, *, path: Path) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"required non-empty string {key!r} is missing: {path}")
    return item


__all__ = [
    "Task04DDocumentIndex",
    "Task04DEntryOutcome",
    "load_task04d_document_index",
    "reconcile_task04d_entry",
    "reconcile_task04d_no_page_sections",
]
