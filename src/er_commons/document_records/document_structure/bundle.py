"""Readable access to the record collections in a semantic fixture bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class DocumentStructureBundleView:
    """Name the collections shared by otherwise independent policy checks."""

    bundle: JsonObject
    sections_by_id: dict[str, JsonObject] = field(init=False)
    content_by_id: dict[str, JsonObject] = field(init=False)
    global_order_by_id: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        """Build the three indexes shared by hierarchy and alias policies."""
        object.__setattr__(
            self,
            "sections_by_id",
            {item["id"]: item for item in self.sections},
        )
        object.__setattr__(
            self,
            "content_by_id",
            {item["id"]: item for item in self.content},
        )
        object.__setattr__(
            self,
            "global_order_by_id",
            {
                record_id: index
                for index, record_id in enumerate(self.bundle["global_content_order_ids"])
            },
        )

    @property
    def sections(self) -> list[JsonObject]:
        """Return sections in persisted sequence order."""
        return cast(list[JsonObject], self.bundle["sections"])

    @property
    def content(self) -> list[JsonObject]:
        """Return blocks, tables, and figures in fixture collection order."""
        return cast(list[JsonObject], self.bundle["content"])

    @property
    def page_labels(self) -> list[JsonObject]:
        """Return page-label observations in physical-page order."""
        return cast(list[JsonObject], self.bundle["page_label_observations"])

    @property
    def aliases(self) -> list[JsonObject]:
        """Return target aliases in deterministic sequence order."""
        return cast(list[JsonObject], self.bundle["target_aliases"])

    @property
    def bridge_entries(self) -> list[JsonObject]:
        """Return cross-producer bridge entries in stable-item order."""
        return cast(list[JsonObject], self.bundle["bridge_entries"])

    def belongs_to_document(self, record_id: str) -> bool:
        """Return whether a canonical record ID uses this document's namespace."""
        document_parts = self.bundle["document_id"].split("/")
        record_parts = record_id.split("/")
        return bool(
            len(document_parts) == 3
            and len(record_parts) >= 3
            and document_parts[1] == "document"
            and record_parts[0] == document_parts[0]
            and record_parts[2] == document_parts[2]
        )
