"""Small shared policy for selecting one section's logical start record."""

from __future__ import annotations

from collections.abc import Mapping


def logical_section_start_id(section: Mapping[str, object]) -> str | None:
    """Return a restored chapter's scope start, otherwise its ordinary heading anchor."""
    if section.get("section_kind") in {"composite_semantic", "derived_chapter"}:
        start = section.get("start_record_id")
        return start if isinstance(start, str) else None
    heading = section.get("heading_block_id")
    if isinstance(heading, str):
        return heading
    start = section.get("start_record_id")
    return start if isinstance(start, str) else None
