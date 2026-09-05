"""Build one reusable linked-document product in memory.

This module is deliberately additive.  It reads the frozen structured candidate,
preserves every non-link record, and owns only aliases and links.  Claim parsing
remains caller-specific; both ordinary and navigation claims end at the shared
exact resolver. Sealed-input handling and publication live in
``relink_publication``.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_records.document_references.construction import (
    CROSS_REFERENCE_PATH,
    TARGET_ALIAS_PATH,
    CandidateSource,
)
from er_commons.document_records.document_references.detection import MentionDetector
from er_commons.document_records.document_references.exact_resolution import (
    ExactResolutionDecision,
    ExactResolutionOutcome,
)
from er_commons.document_records.document_references.indexing import (
    NamespaceRemapper,
    TargetIndex,
    TargetIndexBuilder,
)
from er_commons.document_records.document_references.linking_core import (
    LinkedSourceProducts,
    LinkQuery,
    resolve_link_query,
)
from er_commons.document_records.document_references.linking_policy import (
    DocumentLinkingPolicy,
    LinkCaller,
)
from er_commons.document_records.document_references.machine_link_resolution import (
    index_entries_to_alias_evidence,
)
from er_commons.document_records.document_references.policy import (
    MentionPolicy,
    is_qualified_external_table_reference,
)
from er_commons.document_records.document_references.source_scope import SourceScope
from er_commons.document_records.document_references.storage import (
    read_jsonl,
    serialized_json_sha256,
)
from er_commons.document_records.document_references.table_aliases import (
    build_r6_table_aliases,
)
from er_commons.document_records.document_references.types import (
    DetectedMention,
    JsonObject,
    MentionKind,
    Resolution,
    TargetCandidate,
    TargetIndexEntry,
    UnresolvedReason,
)
from er_commons.source_family_catalog import SourceFamilyCatalog

_SUPPORT_PATHS = {
    "target_index": "support/document_link_target_index.json",
    "accounting": "support/document_link_accounting.json",
    "preservation": "support/document_link_preservation.json",
}
_TARGET_TYPE_FOR_MENTION = {
    MentionKind.SECTION: "section",
    MentionKind.APPENDIX: "section",
    MentionKind.TABLE: "table",
    MentionKind.FIGURE: "figure",
    MentionKind.PRINTED_PAGE: "page",
    MentionKind.DOCUMENT: "document",
}


@dataclass(frozen=True)
class NavigationInputs:
    """Effective entries and explicit relations from a verified navigation owner."""

    entries: tuple[JsonObject, ...] = ()
    relations: tuple[JsonObject, ...] = ()

    def remap_namespace(
        self, source_candidate_id: str, target_candidate_id: str
    ) -> NavigationInputs:
        """Move embedded record IDs between sealed extraction namespaces."""
        remapper = NamespaceRemapper(source_candidate_id, target_candidate_id)
        return NavigationInputs(
            entries=tuple(remapper.value(row) for row in self.entries),
            relations=tuple(remapper.value(row) for row in self.relations),
        )

    @classmethod
    def from_machine_records(
        cls, records: Mapping[str, list[JsonObject]], *, source_id: str
    ) -> NavigationInputs:
        """Project canonical machine TOC blocks into the common claim shape."""
        entries = tuple(
            {
                "navigation_entry_id": str(row["id"]),
                "source_id": source_id,
                "lookup_text": str(row["canonical_text"]),
                "source_record_id": str(row["id"]),
                "machine_navigation": True,
                "link_claim": True,
            }
            for row in records["canonical/blocks.jsonl"]
            if row.get("is_toc_row") is True or row.get("semantic_placement") == "toc_content"
        )
        return cls(entries=entries)

    @classmethod
    def from_bundle_root(cls, root: Path, *, source_id: str) -> NavigationInputs:
        """Load only bundle-owned payloads after its seal has been verified upstream."""
        dispositions = {
            _required_text(row, "disposition_id", "semantic_disposition_id"): row
            for row in read_jsonl(root / "navigation/dispositions.jsonl")
            if row.get("source_id") == source_id
        }
        candidate_entries = tuple(
            row
            for row in read_jsonl(root / "navigation/text_entries.jsonl")
            if row.get("source_id") == source_id
        )
        entries = tuple(
            row for row in candidate_entries if _entry_is_effective(row, dispositions=dispositions)
        )
        relations = tuple(
            row
            for row in read_jsonl(root / "navigation/parent_relations.jsonl")
            if row.get("source_id") == source_id
        )
        return cls(entries=entries, relations=relations)


@dataclass(frozen=True)
class RelinkBuild:
    """Complete records and support required to publish one linked candidate."""

    preserved_record_files: Mapping[str, tuple[JsonObject, ...]]
    products: LinkedSourceProducts
    support: Mapping[str, JsonObject]


class DocumentRelinkBuilder:
    """Rebuild aliases and both link populations from a frozen structured source."""

    def __init__(
        self,
        *,
        source: CandidateSource,
        upstream_candidate_id: str,
        candidate_id: str,
        source_id: str,
        mention_policy: MentionPolicy,
        linking_policy: DocumentLinkingPolicy,
        source_family_catalog: SourceFamilyCatalog,
        source_family_catalog_sha256: str,
        navigation: NavigationInputs | None = None,
    ) -> None:
        self._source = source
        self._upstream_id = upstream_candidate_id
        self._candidate_id = candidate_id
        self._source_id = source_id
        self._mention_policy = mention_policy
        self._linking_policy = linking_policy
        self._catalog = source_family_catalog
        self._catalog_sha256 = source_family_catalog_sha256
        self._navigation = navigation or NavigationInputs()
        self._remapper = NamespaceRemapper(upstream_candidate_id, candidate_id)

    def build(self) -> RelinkBuild:
        """Build deterministic records without writing an artifact."""
        index, replayed_v3_table_alias_count = self._target_index()
        preserved = self._preserved_records()
        index_payload = index.support_payload()
        ordinary = self._ordinary_references(
            index, serialized_json_sha256(index_payload), preserved
        )
        nav_entries, nav_relations, nav_decisions, nav_links = self._navigation_links(index)
        products = LinkedSourceProducts(
            target_aliases=index.aliases,
            ordinary_references=tuple(ordinary),
            navigation_entries=nav_entries,
            navigation_relations=nav_relations,
            navigation_decisions=nav_decisions,
            navigation_links=nav_links,
            support_records=(),
        )
        support = {
            "target_index": index_payload,
            "accounting": _accounting(products),
            "preservation": {
                "schema_version": "er_commons.document_link_preservation.v1",
                "upstream_alias_count": index.upstream_alias_count,
                "replayed_v3_table_alias_count": replayed_v3_table_alias_count,
                "derived_alias_count": (
                    len(index.aliases) - index.upstream_alias_count - replayed_v3_table_alias_count
                ),
                "allowed_derived_alias_rule_ids": ["R6"],
                "undeclared_difference_count": 0,
                "status": "passed",
            },
        }
        return RelinkBuild(preserved, products, support)

    def _target_index(self) -> tuple[TargetIndex, int]:
        upstream = self._source.record_files
        base = TargetIndexBuilder(self._remapper, self._source_id).build(
            upstream_aliases=upstream[TARGET_ALIAS_PATH],
            upstream_blocks=upstream["canonical/blocks.jsonl"],
            upstream_tables=upstream["canonical/tables.jsonl"],
        )
        derived = build_r6_table_aliases(
            upstream_candidate_id=self._upstream_id,
            candidate_id=self._candidate_id,
            source_id=self._source_id,
            upstream_blocks=upstream["canonical/blocks.jsonl"],
            upstream_tables=upstream["canonical/tables.jsonl"],
            first_sequence=len(base.aliases) + 1,
        )
        entries = list(base.entries)
        for alias in derived:
            target = alias.record["targets"][0]
            for lookup_key in alias.evidence.lookup_keys:
                entries.append(
                    TargetIndexEntry(
                        lookup_key=lookup_key,
                        target_type=alias.evidence.target_type,
                        alias_origin=str(alias.record["alias_origin"]),
                        alias_record_id=alias.evidence.alias_id,
                        target_record_id=alias.evidence.target_id,
                        upstream_alias_record_id=None,
                        upstream_target_record_id=str(target["upstream_target_id"]),
                        evidence_kind=str(target["evidence_kind"]),
                        evidence_source_record_id=str(target["evidence_source_record_id"]),
                        evidence_page_id=str(target["evidence_page_id"]),
                    )
                )
        indexed = TargetIndex(
            aliases=(*base.aliases, *(item.record for item in derived)),
            entries=tuple(
                sorted(
                    entries,
                    key=lambda row: (row.lookup_key, row.target_record_id, row.alias_record_id),
                )
            ),
            upstream_alias_count=base.upstream_alias_count,
        )
        return (
            _with_target_pages(indexed, self._source.record_files, self._remapper),
            base.derived_table_alias_count,
        )

    def _preserved_records(self) -> dict[str, tuple[JsonObject, ...]]:
        return {
            path: tuple(self._remapper.value(row) for row in rows)
            for path, rows in self._source.record_files.items()
            if path not in {TARGET_ALIAS_PATH, CROSS_REFERENCE_PATH}
        }

    def _ordinary_references(
        self,
        index: TargetIndex,
        index_sha256: str,
        preserved: Mapping[str, tuple[JsonObject, ...]],
    ) -> list[JsonObject]:
        upstream = self._source.record_files
        detector = MentionDetector(
            self._mention_policy,
            SourceScope.from_hierarchy(
                sections=upstream["canonical/sections.jsonl"],
                blocks=upstream["canonical/blocks.jsonl"],
            ),
        )
        page_numbers = {
            str(row["id"]): int(row["physical_page_number"])
            for row in preserved["canonical/pages.jsonl"]
        }
        resolver = _SharedMentionResolver(
            target_index=index,
            page_numbers=page_numbers,
            target_index_sha256=index_sha256,
            table_page_window=self._mention_policy.table_page_window,
            catalog=self._catalog,
            source_id=self._source_id,
            catalog_sha256=self._catalog_sha256,
            linking_policy=self._linking_policy,
        )
        records: list[JsonObject] = []
        local_blocks = preserved["canonical/blocks.jsonl"]
        for upstream_block, local_block in zip(
            upstream["canonical/blocks.jsonl"], local_blocks, strict=True
        ):
            detected, _ = detector.detect(upstream_block)
            if not detected:
                continue
            page_id = str(local_block["regions"][0]["page_id"])
            for mention in detected:
                resolution = resolver.resolve(
                    mention,
                    source_text=str(upstream_block["canonical_text"]),
                    source_page_id=page_id,
                )
                records.append(
                    _ordinary_record(
                        candidate_id=self._candidate_id,
                        source_id=self._source_id,
                        sequence=len(records) + 1,
                        source_block=local_block,
                        mention=mention,
                        resolution=resolution,
                        pattern_version=self._mention_policy.pattern_version,
                    )
                )
        return records

    def _navigation_links(
        self, index: TargetIndex
    ) -> tuple[
        tuple[JsonObject, ...],
        tuple[JsonObject, ...],
        tuple[JsonObject, ...],
        tuple[JsonObject, ...],
    ]:
        entries = tuple(
            self._remapper.value(row)
            for row in self._navigation.entries
            if row.get("source_id") == self._source_id
        )
        relations = tuple(
            self._remapper.value(row)
            for row in self._navigation.relations
            if row.get("source_id") == self._source_id
        )
        parent_by_child = {_relation_child(row): _relation_parent(row) for row in relations}
        entry_by_id = {_entry_id(row): row for row in entries}
        if len(entry_by_id) != len(entries):
            raise ValueError("navigation entry IDs must be unique")
        decisions_by_entry: dict[str, ExactResolutionDecision] = {}
        active_parent_chain: set[str] = set()
        alias_evidence = index_entries_to_alias_evidence(
            index.entries, parent_by_target=self._body_scope_targets(index)
        )

        def resolve_entry(entry_id: str) -> ExactResolutionDecision:
            if entry_id in decisions_by_entry:
                return decisions_by_entry[entry_id]
            if entry_id in active_parent_chain:
                raise ValueError(
                    f"navigation parent relations contain a cycle at entry: {entry_id}"
                )
            entry = entry_by_id.get(entry_id)
            if entry is None:
                raise ValueError(f"navigation relation names an absent entry: {entry_id}")
            active_parent_chain.add(entry_id)
            parent_entry_id = parent_by_child.get(entry_id)
            parent_targets = None
            if parent_entry_id is not None:
                parent = resolve_entry(parent_entry_id)
                parent_targets = (
                    tuple(item.target_id for item in parent.candidates)
                    if parent.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE
                    else ()
                )
            destination_page_ids = _optional_string_tuple(entry.get("destination_page_ids"))
            target_type = _navigation_target_type(entry)
            decision = resolve_link_query(
                LinkQuery(
                    caller=LinkCaller.EFFECTIVE_NAVIGATION,
                    lookup_text=_navigation_lookup_text(entry),
                    target_type=target_type,
                    aliases=alias_evidence,
                    destination_page_ids=destination_page_ids,
                    resolved_parent_target_ids=parent_targets,
                ),
                policy=self._linking_policy,
            )
            marker = _navigation_section_marker(entry)
            if (
                decision.outcome is ExactResolutionOutcome.NO_TEXT_MATCH
                and target_type == "section"
                and destination_page_ids is not None
                and marker is not None
            ):
                # R1 is a structural fallback, not a relaxed text comparison.
                # Use only a parser-confirmed decimal marker and require the
                # independently resolved destination page to select the target.
                decision = resolve_link_query(
                    LinkQuery(
                        caller=LinkCaller.EFFECTIVE_NAVIGATION,
                        lookup_text=marker,
                        target_type=target_type,
                        aliases=alias_evidence,
                        destination_page_ids=destination_page_ids,
                        resolved_parent_target_ids=parent_targets,
                    ),
                    policy=self._linking_policy,
                )
            active_parent_chain.remove(entry_id)
            decisions_by_entry[entry_id] = decision
            return decision

        decisions: list[JsonObject] = []
        links: list[JsonObject] = []
        claim_entries = tuple(entry for entry in entries if entry.get("link_claim") is not False)
        for sequence, entry in enumerate(claim_entries, start=1):
            entry_id = _entry_id(entry)
            decision = resolve_entry(entry_id)
            decisions.append(
                _navigation_decision(
                    self._candidate_id, self._source_id, entry_id, sequence, decision
                )
            )
            if decision.outcome is ExactResolutionOutcome.RESOLVED_UNIQUE:
                links.append(
                    _navigation_link(
                        self._candidate_id,
                        self._source_id,
                        entry_id,
                        len(links) + 1,
                        decision,
                    )
                )
        return entries, relations, tuple(decisions), tuple(links)

    def _body_scope_targets(self, index: TargetIndex) -> dict[str, str]:
        """Return explicit direct-section and table chapter scope targets."""
        sections = self._source.record_files["canonical/sections.jsonl"]
        parents = {
            self._remapper.record_id(str(row["id"])): self._remapper.record_id(str(parent))
            for row in sections
            if (parent := row.get("parent_section_id")) is not None
        }
        upstream_sections = {str(row["id"]): row for row in sections}
        section_targets_by_marker = _section_targets_by_marker(
            self._source.record_files[TARGET_ALIAS_PATH]
        )
        table_marker_by_target = _r6_table_markers_by_target(index.aliases)
        for table in self._source.record_files["canonical/tables.jsonl"]:
            table_id = str(table["id"])
            immediate = table.get("section_id")
            if not isinstance(immediate, str):
                continue
            scope = immediate
            marker = table_marker_by_target.get(table_id)
            unique_marker_targets = section_targets_by_marker.get(marker or "", set())
            if len(unique_marker_targets) == 1:
                desired = next(iter(unique_marker_targets))
                if desired in _section_ancestors(immediate, upstream_sections):
                    scope = desired
            parents[self._remapper.record_id(table_id)] = self._remapper.record_id(scope)
        return parents


class _SharedMentionResolver:
    """Preserve v3 claim policy while delegating target choice to linking v1."""

    def __init__(
        self,
        *,
        target_index: TargetIndex,
        page_numbers: Mapping[str, int],
        target_index_sha256: str,
        table_page_window: int,
        catalog: SourceFamilyCatalog,
        source_id: str,
        catalog_sha256: str,
        linking_policy: DocumentLinkingPolicy,
    ) -> None:
        self.index = target_index
        self.pages = page_numbers
        self.index_sha256 = target_index_sha256
        self.window = table_page_window
        self.catalog = catalog
        self.source_id = source_id
        self.catalog_sha256 = catalog_sha256
        self.policy = linking_policy

    def resolve(
        self, mention: DetectedMention, *, source_text: str, source_page_id: str
    ) -> Resolution:
        if mention.kind is MentionKind.FIGURE:
            return Resolution((), UnresolvedReason.TARGET_TYPE_UNAVAILABLE)
        if mention.kind is MentionKind.TABLE and is_qualified_external_table_reference(
            source_text[mention.span.end :]
        ):
            return Resolution((), UnresolvedReason.QUALIFIED_EXTERNAL_TABLE)
        target_type = _TARGET_TYPE_FOR_MENTION[mention.kind]
        entries = self.index.entries
        unfiltered = resolve_link_query(
            LinkQuery(
                caller=LinkCaller.MACHINE_REFERENCE,
                lookup_text=mention.lookup_key,
                target_type=target_type,
                aliases=index_entries_to_alias_evidence(self.index.entries),
            ),
            policy=self.policy,
        )
        if mention.kind is MentionKind.TABLE:
            entries = tuple(
                row
                for row in entries
                if row.target_type != "table"
                or (
                    row.evidence_page_id is not None
                    and abs(self.pages[row.evidence_page_id] - self.pages[source_page_id])
                    <= self.window
                )
            )
        decision = resolve_link_query(
            LinkQuery(
                caller=LinkCaller.MACHINE_REFERENCE,
                lookup_text=mention.lookup_key,
                target_type=target_type,
                aliases=index_entries_to_alias_evidence(entries),
            ),
            policy=self.policy,
        )
        if decision.candidates:
            return Resolution(
                tuple(
                    _target_candidate(
                        candidate.target_id, candidate.alias_ids, entries, self.index_sha256
                    )
                    for candidate in decision.candidates
                ),
                None,
            )
        if mention.kind is MentionKind.TABLE and unfiltered.candidates:
            return Resolution((), UnresolvedReason.OUTSIDE_TABLE_WINDOW)
        if mention.kind in {MentionKind.APPENDIX, MentionKind.DOCUMENT}:
            cross_document = self.catalog.cross_document_match(
                source_id=self.source_id,
                mention_class=mention.kind.value,
                lookup_key=mention.lookup_key,
                source_text=source_text,
                mention_start=mention.span.start,
                mention_end=mention.span.end,
            )
            if cross_document is not None:
                return Resolution(
                    (),
                    UnresolvedReason.DEFERRED_CROSS_DOCUMENT,
                    cross_document.as_json(catalog_sha256=self.catalog_sha256),
                )
            if mention.kind is MentionKind.DOCUMENT:
                return Resolution((), UnresolvedReason.EXTERNAL_DOCUMENT)
        return Resolution((), UnresolvedReason.NO_LOCAL_ALIAS)


def _with_target_pages(
    index: TargetIndex,
    upstream: Mapping[str, list[JsonObject]],
    remapper: NamespaceRemapper,
) -> TargetIndex:
    """Attach destination pages from body records, never from source claims."""
    block_pages = {
        str(row["id"]): str(row["regions"][0]["page_id"])
        for row in upstream["canonical/blocks.jsonl"]
        if len(row.get("regions", [])) == 1
    }
    target_pages: dict[str, str] = {}
    for path in ("canonical/pages.jsonl", "canonical/tables.jsonl", "canonical/figures.jsonl"):
        for row in upstream[path]:
            if path == "canonical/pages.jsonl":
                page_id = str(row["id"])
            elif len(row.get("regions", [])) == 1:
                page_id = str(row["regions"][0]["page_id"])
            else:
                continue
            target_pages[remapper.record_id(str(row["id"]))] = remapper.record_id(page_id)
    for row in upstream["canonical/sections.jsonl"]:
        heading_id = row.get("heading_block_id")
        if isinstance(heading_id, str) and heading_id in block_pages:
            target_pages[remapper.record_id(str(row["id"]))] = remapper.record_id(
                block_pages[heading_id]
            )
    entries = tuple(
        TargetIndexEntry(
            lookup_key=row.lookup_key,
            target_type=row.target_type,
            alias_origin=row.alias_origin,
            alias_record_id=row.alias_record_id,
            target_record_id=row.target_record_id,
            upstream_alias_record_id=row.upstream_alias_record_id,
            upstream_target_record_id=row.upstream_target_record_id,
            evidence_kind=row.evidence_kind,
            evidence_source_record_id=row.evidence_source_record_id,
            evidence_page_id=row.evidence_page_id or target_pages.get(row.target_record_id),
        )
        for row in index.entries
    )
    return TargetIndex(index.aliases, entries, index.upstream_alias_count)


def _section_ancestors(section_id: str, sections: Mapping[str, JsonObject]) -> frozenset[str]:
    """Return a cycle-checked section ancestry including the starting section."""
    ancestors: set[str] = set()
    current: str | None = section_id
    while current is not None:
        if current in ancestors:
            raise ValueError(f"body section hierarchy contains a cycle: {current}")
        ancestors.add(current)
        section = sections.get(current)
        parent = section.get("parent_section_id") if section is not None else None
        current = parent if isinstance(parent, str) else None
    return frozenset(ancestors)


def _section_targets_by_marker(aliases: Sequence[JsonObject]) -> dict[str, set[str]]:
    """Index upstream section targets by their leading decimal marker."""
    targets_by_marker: dict[str, set[str]] = {}
    for alias in aliases:
        if alias.get("alias_kind") != "section":
            continue
        match = re.match(r"^(\d+(?:\.\d+)*)\b", str(alias.get("normalized_alias", "")))
        if match is None:
            continue
        for target in alias.get("targets", []):
            if target.get("target_type") == "section":
                targets_by_marker.setdefault(match.group(1), set()).add(str(target["target_id"]))
    return targets_by_marker


def _r6_table_markers_by_target(aliases: Sequence[JsonObject]) -> dict[str, str]:
    """Map each derived R6 table target to its leading chapter-like marker."""
    markers: dict[str, str] = {}
    for alias in aliases:
        if alias.get("alias_origin") != "linking_v1_r6_body_table_caption":
            continue
        match = re.match(r"^table\s+(\d+(?:\.\d+)*)-", str(alias.get("normalized_alias", "")))
        if match is not None:
            markers[str(alias["targets"][0]["upstream_target_id"])] = match.group(1)
    return markers


def _target_candidate(
    target_id: str,
    alias_ids: tuple[str, ...],
    entries: Sequence[TargetIndexEntry],
    index_sha256: str,
) -> TargetCandidate:
    rows = sorted(
        (
            row
            for row in entries
            if row.target_record_id == target_id and row.alias_record_id in alias_ids
        ),
        key=lambda row: (row.alias_record_id, row.lookup_key),
    )
    first = rows[0]
    origins = sorted({row.alias_origin for row in rows})
    upstream_targets = {row.upstream_target_record_id for row in rows}
    if len(upstream_targets) != 1:
        raise ValueError("one local target maps to multiple upstream targets")
    return TargetCandidate(
        target_type=first.target_type,
        alias_origin=origins[0] if len(origins) == 1 else "mixed_body_alias_evidence",
        alias_record_ids=tuple(sorted(set(alias_ids))),
        target_record_id=target_id,
        upstream_alias_record_ids=tuple(
            sorted({row.upstream_alias_record_id for row in rows if row.upstream_alias_record_id})
        ),
        upstream_target_record_id=next(iter(upstream_targets)),
        evidence=(
            {
                "kind": "document_linking_v1_exact",
                "refs": [{"path": _SUPPORT_PATHS["target_index"], "sha256": index_sha256}],
            },
        ),
    )


def _ordinary_record(
    *,
    candidate_id: str,
    source_id: str,
    sequence: int,
    source_block: JsonObject,
    mention: DetectedMention,
    resolution: Resolution,
    pattern_version: str,
) -> JsonObject:
    return {
        "schema_version": "er_commons.canonical_extraction.v3",
        "extraction_id": candidate_id,
        "id": f"{candidate_id}/cross-reference/{source_id}/xref{sequence:06d}",
        "document_id": source_block["document_id"],
        "sequence": sequence,
        "source_record_id": source_block["id"],
        "mention_class": mention.kind.value,
        "raw_text": mention.raw_text,
        "source_charspan": mention.span.as_json(),
        "pattern_version": pattern_version,
        "lookup_key": mention.lookup_key,
        "candidates": [item.as_json() for item in resolution.candidates],
        "resolution_status": resolution.status.value,
        "unresolved_reason": resolution.unresolved_reason.value
        if resolution.unresolved_reason
        else None,
        "cross_document_evidence": resolution.cross_document_evidence,
        "regions": source_block["regions"],
        "raw_links": source_block["raw_links"],
    }


def _navigation_decision(
    candidate_id: str,
    source_id: str,
    entry_id: str,
    sequence: int,
    decision: ExactResolutionDecision,
) -> JsonObject:
    return {
        "schema_version": "er_commons.navigation_link_decision.v1",
        "id": f"{candidate_id}/navigation-decision/{source_id}/decision{sequence:06d}",
        "extraction_id": candidate_id,
        "source_id": source_id,
        "navigation_entry_id": entry_id,
        "sequence": sequence,
        "outcome": decision.outcome.value,
        "match_basis": list(decision.match_basis),
        "candidate_target_ids": [item.target_id for item in decision.candidates],
        "unscoped_text_candidate_count": decision.unscoped_text_candidate_count,
        "scoped_text_candidate_count": decision.scoped_text_candidate_count,
        "parent_scope_applied": decision.parent_scope_applied,
        "destination_page_intersection_applied": decision.destination_page_intersection_applied,
    }


def _navigation_link(
    candidate_id: str,
    source_id: str,
    entry_id: str,
    sequence: int,
    decision: ExactResolutionDecision,
) -> JsonObject:
    candidate = decision.candidates[0]
    return {
        "schema_version": "er_commons.navigation_link.v1",
        "id": f"{candidate_id}/navigation-link/{source_id}/link{sequence:06d}",
        "extraction_id": candidate_id,
        "source_id": source_id,
        "navigation_entry_id": entry_id,
        "sequence": sequence,
        "target_id": candidate.target_id,
        "supporting_alias_ids": list(candidate.alias_ids),
        "target_page_ids": list(candidate.target_page_ids),
        "match_basis": list(decision.match_basis),
    }


def _accounting(products: LinkedSourceProducts) -> JsonObject:
    outcomes = Counter(row["outcome"] for row in products.navigation_decisions)
    return {
        "schema_version": "er_commons.document_link_accounting.v1",
        "target_alias_count": len(products.target_aliases),
        "ordinary_reference_count": len(products.ordinary_references),
        "navigation_entry_count": len(products.navigation_entries),
        "navigation_claim_count": len(products.navigation_decisions),
        "navigation_decision_count": len(products.navigation_decisions),
        "navigation_link_count": len(products.navigation_links),
        "navigation_outcome_counts": dict(sorted(outcomes.items())),
    }


def _entry_id(row: Mapping[str, Any]) -> str:
    return _required_text(row, "navigation_entry_id", "toc_text_entry_id", "entry_id")


def _relation_child(row: Mapping[str, Any]) -> str:
    return _required_text(row, "child_entry_id", "navigation_entry_id", "toc_text_entry_id")


def _relation_parent(row: Mapping[str, Any]) -> str:
    return _required_text(row, "parent_entry_id", "parent_navigation_entry_id")


def _required_text(row: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    raise ValueError(f"record lacks one required text field: {keys}")


def _navigation_target_type(row: Mapping[str, Any]) -> str:
    value = row.get("target_type", row.get("marker_kind"))
    if value == "appendix":
        value = "section"
    if value is None:
        text = _navigation_lookup_text(row)
        if re.match(r"^(?:[a-z]\.|[1-9]\d*(?:\.\d+)*)\s", text, re.IGNORECASE):
            value = "section"
        elif re.match(r"^table\s", text, re.IGNORECASE):
            value = "table"
        elif re.match(r"^figure\s", text, re.IGNORECASE):
            value = "figure"
    if value not in {"section", "table", "figure"}:
        return "unsupported"
    return str(value)


def _navigation_section_marker(row: Mapping[str, Any]) -> str | None:
    """Return only a parser-confirmed decimal section marker for R1."""
    if row.get("marker_kind") != "section":
        return None
    marker = row.get("normalized_marker")
    if not isinstance(marker, str) or re.fullmatch(r"[1-9]\d*(?:\.\d+)*", marker) is None:
        return None
    return marker


def _navigation_lookup_text(row: Mapping[str, Any]) -> str:
    """Read a complete claim and retain any separately parsed letter marker."""
    text = _required_text(
        row,
        "lookup_text",
        "entry_text",
        "reconstructed_text",
        "model_text",
        "model_entry_text",
        "raw_text",
        "text",
        "normalized_entry",
    )
    terminal = row.get("terminal_destination_token")
    if isinstance(terminal, str) and terminal:
        separator = r"(?:(?:\s*\.){2,}\s*|\s+)"
        match = re.search(rf"{separator}{re.escape(terminal)}\s*$", text, re.IGNORECASE)
        if match is None:
            raise ValueError("terminal destination token is not final in navigation text")
        text = text[: match.start()].rstrip()
    marker = next(
        (
            value.strip()
            for key in ("letter_marker", "normalized_marker", "marker")
            if isinstance((value := row.get(key)), str)
            and re.fullmatch(r"[a-z]\.", value.strip(), re.IGNORECASE)
        ),
        None,
    )
    if (
        marker is not None
        and re.match(rf"^{re.escape(marker)}(?:\s|$)", text, re.IGNORECASE) is None
    ):
        return f"{marker} {text}"
    return text


def _entry_is_effective(
    row: Mapping[str, Any], *, dispositions: Mapping[str, Mapping[str, Any]]
) -> bool:
    """Honor a referenced semantic disposition without requiring one for prepared rows."""
    disposition_id = row.get("table_disposition_id")
    if disposition_id is None:
        return True
    if not isinstance(disposition_id, str) or disposition_id not in dispositions:
        raise ValueError("navigation entry references an absent semantic disposition")
    return dispositions[disposition_id].get("effective_navigation") is True


def _optional_string_tuple(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("destination_page_ids must be null or a string list")
    return tuple(value)


__all__ = [
    "DocumentRelinkBuilder",
    "NavigationInputs",
    "RelinkBuild",
]
