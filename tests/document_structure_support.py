"""Named fixture access for semantic-structure policy tests."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

JsonObject = dict[str, Any]


def record_with(records: Iterable[JsonObject], field: str, value: object) -> JsonObject:
    """Return the unique fixture record whose named field has the given value."""
    matches = [record for record in records if record[field] == value]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one fixture record with {field}={value!r}, got {len(matches)}"
        )
    return matches[0]


def record_ending_with(records: Iterable[JsonObject], local_id: str) -> JsonObject:
    """Return the unique fixture record with the recognizable local ID suffix."""
    matches = [record for record in records if record["id"].endswith(local_id)]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one fixture record ending in {local_id}, got {len(matches)}"
        )
    return matches[0]


def page_label(bundle: JsonObject, physical_page: int) -> JsonObject:
    """Return the label outcome for one physical page."""
    return record_with(bundle["page_label_observations"], "physical_page_number", physical_page)


def alias_named(bundle: JsonObject, normalized_alias: str) -> JsonObject:
    """Return one target alias by its human-recognizable normalized spelling."""
    return record_with(bundle["target_aliases"], "normalized_alias", normalized_alias)


def add_printed_page_alias(
    bundle: JsonObject,
    physical_page: int,
    raw_label: str,
) -> JsonObject:
    """Append one readable printed-page alias and return it for mutation."""
    extraction_id, _, source_id = bundle["document_id"].split("/", maxsplit=2)
    sequence = len(bundle["target_aliases"]) + 1
    alias = {
        "id": (f"{extraction_id}/target-alias/{source_id}/alias{sequence:06d}"),
        "document_id": bundle["document_id"],
        "sequence": sequence,
        "alias_kind": "printed_page",
        "raw_values": [raw_label],
        "normalized_alias": raw_label.casefold(),
        "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
        "resolution_status": "unique",
        "targets": [
            {
                "target_id": f"{extraction_id}/page/{source_id}/p{physical_page:06d}",
                "target_type": "page",
                "evidence_kind": "resolved_printed_page_label",
                "evidence_ref": {
                    "path": f"canonical/page_label_observations.jsonl/{physical_page - 1}",
                    "sha256": "f" * 64,
                },
                "toc_reconciliation_ref": None,
            }
        ],
    }
    bundle["target_aliases"].append(alias)
    return alias


_MENTION_FIELD = re.compile(r"(?:mention|source_charspan|raw_text)", re.IGNORECASE)


def fixture_has_no_mentions(value: Any) -> bool:
    """Return whether a fixture contains only target-side alias evidence."""
    if isinstance(value, dict):
        return all(
            _MENTION_FIELD.search(key) is None and fixture_has_no_mentions(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return all(fixture_has_no_mentions(child) for child in value)
    return True
