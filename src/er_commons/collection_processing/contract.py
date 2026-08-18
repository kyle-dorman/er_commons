"""Native v2 collection-contract types, digests, and identity recipes."""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785

type JsonObject = dict[str, Any]

INDEX_PREIMAGE_FIELDS = frozenset(
    {
        "schema_version",
        "production_extraction_id",
        "scope_id",
        "accounting_sha256",
        "eligible_candidates_sha256",
        "unavailable_sources_sha256",
        "entries_sha256",
        "entry_count",
        "document_targets_sha256",
        "document_target_count",
        "ordering_policy_version",
        "target_policy_sha256",
        "managed_inventory_sha256",
    }
)
LINK_PREIMAGE_FIELDS = frozenset(
    {
        "schema_version",
        "production_extraction_id",
        "scope_id",
        "index_completion_sha256",
        "mention_input_manifest_sha256",
        "resolutions_sha256",
        "counts_sha256",
        "before_after_inventories_sha256",
        "resolution_policy_sha256",
        "managed_inventory_sha256",
    }
)
HANDOFF_PREIMAGE_FIELDS = frozenset(
    {
        "schema_version",
        "production_extraction_id",
        "scope_id",
        "accounting_completion_sha256",
        "index_completion_sha256",
        "resolution_completion_sha256",
        "blocking_policy_sha256",
        "status",
        "blocking_reasons_sha256",
        "task04_status",
        "managed_inventory_sha256",
    }
)


def canonical_sha256(value: Any) -> str:
    """Hash one JSON-compatible value using RFC 8785 canonical bytes."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def unavailable_source_digest(record: JsonObject) -> str:
    """Derive the stable negative-evidence digest used by links and handoffs."""
    return canonical_sha256(record)


def build_record_target_index_id(preimage: JsonObject) -> str:
    """Derive a record-target index ID from its closed v2 preimage."""
    return _typed_id(
        "idxv1",
        preimage,
        fields=INDEX_PREIMAGE_FIELDS,
        schema="er_commons.record_target_index_identity.v2",
    )


def build_cross_document_link_id(preimage: JsonObject) -> str:
    """Derive a cross-document link ID from its closed v2 preimage."""
    return _typed_id(
        "resv1",
        preimage,
        fields=LINK_PREIMAGE_FIELDS,
        schema="er_commons.cross_document_link_identity.v2",
    )


def build_collection_handoff_id(preimage: JsonObject) -> str:
    """Derive a collection handoff ID from its closed v2 preimage."""
    return _typed_id(
        "handoffv1",
        preimage,
        fields=HANDOFF_PREIMAGE_FIELDS,
        schema="er_commons.collection_handoff_identity.v2",
    )


def _typed_id(
    prefix: str,
    preimage: JsonObject,
    *,
    fields: frozenset[str],
    schema: str,
) -> str:
    observed = set(preimage)
    if observed != fields:
        raise ValueError(
            f"{prefix} identity fields differ: "
            f"missing={sorted(fields - observed)}, extra={sorted(observed - fields)}"
        )
    if preimage.get("schema_version") != schema:
        raise ValueError(f"unexpected {prefix} identity schema: {preimage.get('schema_version')}")
    return f"{prefix}-{canonical_sha256(preimage)}"


__all__ = [
    "JsonObject",
    "build_collection_handoff_id",
    "build_cross_document_link_id",
    "build_record_target_index_id",
    "canonical_sha256",
    "unavailable_source_digest",
]
