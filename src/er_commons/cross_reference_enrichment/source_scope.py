"""Structural source exclusions derived from the accepted section hierarchy."""

from __future__ import annotations

import re
from dataclasses import dataclass

from er_commons.cross_reference_enrichment.types import JsonObject

REFERENCE_HEADING = re.compile(
    r"^(?:(?:[1-9][0-9]*)(?:\.[0-9]+)*\s+)?"
    r"(?:references|bibliography|works cited)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceScope:
    """Identify blocks excluded by a structurally named reference section."""

    reference_section_ids: frozenset[str]

    @classmethod
    def from_hierarchy(cls, *, sections: list[JsonObject], blocks: list[JsonObject]) -> SourceScope:
        """Find reference headings and include all descendant sections."""
        blocks_by_id = {block["id"]: block for block in blocks}
        reference_roots = {
            section["id"] for section in sections if _is_reference_section(section, blocks_by_id)
        }
        excluded = set(reference_roots)
        changed = True
        while changed:
            changed = False
            for section in sections:
                if section.get("parent_section_id") in excluded and section["id"] not in excluded:
                    excluded.add(section["id"])
                    changed = True
        return cls(frozenset(excluded))

    def exclusion_for(self, block: JsonObject) -> str | None:
        """Return the diagnostic category for an excluded block, if any."""
        if block.get("section_id") in self.reference_section_ids:
            return "reference_section"
        return None


def _is_reference_section(section: JsonObject, blocks_by_id: dict[str, JsonObject]) -> bool:
    heading_id = section.get("heading_block_id")
    if not isinstance(heading_id, str):
        return False
    heading = blocks_by_id.get(heading_id)
    if heading is None:
        return False
    text = heading.get("canonical_text")
    return isinstance(text, str) and REFERENCE_HEADING.fullmatch(text.strip()) is not None
