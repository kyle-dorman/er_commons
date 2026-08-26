"""Domain records shared by PDF outline parsing owners."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

type JsonObject = dict[str, Any]
type RawReferenceKey = tuple[int, int]


@dataclass(frozen=True)
class OutlineExtraction:
    """Usable outline nodes plus explicit evidence omitted as invalid leaves."""

    observations: tuple[JsonObject, ...]
    diagnostics: tuple[JsonObject, ...]


@dataclass
class OutlineTreeNode:
    """One parsed pypdf outline node with explicit child ownership."""

    node: Any
    title: str
    page: int | None
    children: list[OutlineTreeNode] = field(default_factory=list)


@dataclass
class OutlineCleanResult:
    """Cleaned outline forest plus evidence removed from that forest."""

    nodes: list[OutlineTreeNode] = field(default_factory=list)
    diagnostics: list[JsonObject] = field(default_factory=list)
    invalid_leaf_titles: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
