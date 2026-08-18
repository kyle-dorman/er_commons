"""Shared source-family contract for local and corpus cross-document resolution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

JsonObject = dict[str, Any]
DocumentRole = Literal["root_report", "top_level_appendix", "appendix_part"]
_ROLES = frozenset({"root_report", "top_level_appendix", "appendix_part"})
_FAMILY_QUALIFIER = re.compile(
    r"(?:\b(?:DEIR|EIR|Draft\s+Environmental\s+Impact\s+Report)\b\s+[^.;:]{0,24}$|"
    r"^[^.;:]{0,24}\bof\s+the\s+(?:DEIR|EIR|Draft\s+Environmental\s+Impact\s+Report)\b)",
    re.IGNORECASE,
)


def normalize_reference_alias(value: str) -> str:
    """Normalize reviewed aliases without deriving new words from mention text."""
    return " ".join(value.casefold().split())


@dataclass(frozen=True)
class FamilySource:
    """One sealed source and its explicit ownership within a document family."""

    source: JsonObject
    family_root_source_id: str
    document_role: DocumentRole
    parent_source_id: str | None
    reference_aliases: tuple[str, ...]

    @property
    def source_id(self) -> str:
        """Return the sealed source identifier."""
        return str(self.source["source_id"])


@dataclass(frozen=True)
class CrossDocumentMatch:
    """Catalog evidence authorizing one local mention for corpus resolution."""

    intended_target_source_ids: tuple[str, ...]
    matched_alias: str
    traversal_rule: str
    source_family_id: str

    def as_json(self, *, catalog_sha256: str) -> JsonObject:
        """Serialize independently verifiable eligibility evidence."""
        return {
            "catalog_sha256": catalog_sha256,
            "source_family_id": self.source_family_id,
            "matched_alias": self.matched_alias,
            "traversal_rule": self.traversal_rule,
            "intended_target_source_ids": list(self.intended_target_source_ids),
        }


@dataclass(frozen=True)
class SourceFamilyCatalog:
    """One checksummed alias and ownership vocabulary shared by both stages."""

    raw_bytes: bytes
    schema_version: str
    catalog_version: str
    source_family_id: str
    sources: tuple[FamilySource, ...]

    @classmethod
    def load(cls, path: Path) -> SourceFamilyCatalog:
        """Load and validate one contained catalog file."""
        return cls.from_bytes(path.read_bytes())

    @classmethod
    def from_bytes(cls, raw: bytes) -> SourceFamilyCatalog:
        """Parse closed source-family bytes and validate ownership references."""
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("source-family catalog must be an object")
        required = {
            "schema_version",
            "catalog_version",
            "source_family_id",
            "sources",
        }
        if set(value) != required:
            raise ValueError("source-family catalog fields differ from the closed contract")
        if value["schema_version"] != "er_commons.source_family_catalog.v1":
            raise ValueError("source-family catalog schema version differs")
        if not isinstance(value["sources"], list) or not value["sources"]:
            raise ValueError("source-family catalog lacks sources")
        sources = tuple(_family_source(item) for item in value["sources"])
        _validate_sources(sources)
        return cls(
            raw_bytes=raw,
            schema_version=value["schema_version"],
            catalog_version=str(value["catalog_version"]),
            source_family_id=str(value["source_family_id"]),
            sources=sources,
        )

    @property
    def by_source_id(self) -> dict[str, FamilySource]:
        """Index the unique sealed source records by source ID."""
        return {source.source_id: source for source in self.sources}

    @property
    def alias_lookup(self) -> dict[str, tuple[FamilySource, ...]]:
        """Return reviewed aliases mapped to one or more intended sources."""
        lookup: dict[str, list[FamilySource]] = {}
        for source in self.sources:
            for alias in source.reference_aliases:
                lookup.setdefault(alias, []).append(source)
        return {alias: tuple(matches) for alias, matches in lookup.items()}

    def cross_document_match(
        self,
        *,
        source_id: str,
        mention_class: str,
        lookup_key: str,
        source_text: str,
        mention_start: int,
        mention_end: int,
    ) -> CrossDocumentMatch | None:
        """Authorize a locally unresolved mention using family role and literal text."""
        origin = self.by_source_id.get(source_id)
        if origin is None:
            raise ValueError(f"source-family catalog lacks origin source: {source_id}")
        alias = normalize_reference_alias(lookup_key)
        targets = tuple(
            target
            for target in self.alias_lookup.get(alias, ())
            if target.source_id != source_id
            and target.family_root_source_id == origin.family_root_source_id
        )
        if not targets:
            return None
        if mention_class == "document":
            traversal = "reviewed_named_document_alias"
        elif mention_class == "appendix" and origin.document_role == "root_report":
            targets = tuple(
                target for target in targets if target.document_role == "top_level_appendix"
            )
            traversal = "root_report_to_top_level_appendix"
        elif mention_class == "appendix" and _qualified_context(
            source_text, mention_start, mention_end
        ):
            targets = tuple(
                target for target in targets if target.document_role == "top_level_appendix"
            )
            traversal = "qualified_nested_to_top_level_appendix"
        else:
            return None
        if not targets:
            return None
        return CrossDocumentMatch(
            intended_target_source_ids=tuple(target.source_id for target in targets),
            matched_alias=alias,
            traversal_rule=traversal,
            source_family_id=self.source_family_id,
        )


def _family_source(value: object) -> FamilySource:
    if not isinstance(value, dict):
        raise ValueError("source-family entry must be an object")
    required = {
        "source",
        "family_root_source_id",
        "document_role",
        "parent_source_id",
        "reference_aliases",
    }
    if set(value) != required:
        raise ValueError("source-family entry fields differ from the closed contract")
    source = value["source"]
    aliases = value["reference_aliases"]
    role = value["document_role"]
    if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
        raise ValueError("source-family entry lacks a source identity")
    if not isinstance(source.get("sha256"), str) or len(source["sha256"]) != 64:
        raise ValueError("source-family entry lacks a source checksum")
    if role not in _ROLES:
        raise ValueError("source-family entry has an invalid document role")
    if not isinstance(aliases, list) or not aliases:
        raise ValueError("source-family entry lacks reviewed reference aliases")
    normalized = tuple(normalize_reference_alias(str(alias)) for alias in aliases)
    if any(not alias for alias in normalized) or len(normalized) != len(set(normalized)):
        raise ValueError("source-family aliases must be unique and nonempty per source")
    parent = value["parent_source_id"]
    if parent is not None and not isinstance(parent, str):
        raise ValueError("source-family parent source ID is invalid")
    return FamilySource(
        source=dict(source),
        family_root_source_id=str(value["family_root_source_id"]),
        document_role=role,
        parent_source_id=parent,
        reference_aliases=normalized,
    )


def _validate_sources(sources: tuple[FamilySource, ...]) -> None:
    by_id = {source.source_id: source for source in sources}
    if len(by_id) != len(sources):
        raise ValueError("source-family source IDs must be unique")
    roots = [source for source in sources if source.document_role == "root_report"]
    if len(roots) != 1 or roots[0].parent_source_id is not None:
        raise ValueError("source-family catalog requires one parentless root report")
    root_id = roots[0].source_id
    for source in sources:
        if source.family_root_source_id != root_id:
            raise ValueError("source-family root ownership differs")
        if source.document_role != "root_report" and source.parent_source_id not in by_id:
            raise ValueError("source-family child lacks its explicit parent source")


def _qualified_context(source_text: str, start: int, end: int) -> bool:
    """Require an adjacent family qualifier, not an unrelated EIR token in the block."""
    before = source_text[max(0, start - 64) : start]
    after = source_text[end : min(len(source_text), end + 64)]
    return (
        _FAMILY_QUALIFIER.search(before) is not None or _FAMILY_QUALIFIER.search(after) is not None
    )
