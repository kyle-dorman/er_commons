"""Construction and inspection of extraction-scoped record identifiers."""

from __future__ import annotations

import re

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.layout import RECORD_TYPES

EXTRACTION_ID_PATTERN = re.compile(r"^exv1-[0-9a-f]{64}$")
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]*$")
ORDINAL_PATTERN = r"[0-9]{6,}"

# Explicit prefixes make IDs recognizable when they appear outside their
# containing JSONL file. Document IDs are the one exception: their local key is
# the frozen source ID itself.
LOCAL_KEY_PATTERNS = {
    "document": re.compile(r"^[a-z0-9][a-z0-9_]*$"),
    "page": re.compile(rf"^p{ORDINAL_PATTERN}$"),
    "section": re.compile(rf"^sec{ORDINAL_PATTERN}$"),
    "block": re.compile(rf"^blk{ORDINAL_PATTERN}$"),
    "table": re.compile(rf"^tbl{ORDINAL_PATTERN}$"),
    "table-family": re.compile(rf"^fam{ORDINAL_PATTERN}$"),
    "figure": re.compile(rf"^fig{ORDINAL_PATTERN}$"),
    "image": re.compile(rf"^img{ORDINAL_PATTERN}$"),
    "asset": re.compile(rf"^[a-z0-9][a-z0-9_-]*/ast{ORDINAL_PATTERN}$"),
    "cross-reference": re.compile(rf"^xref{ORDINAL_PATTERN}$"),
    "routing-observation": re.compile(rf"^route-p{ORDINAL_PATTERN}$"),
    "table-stage-observation": re.compile(rf"^stage-p{ORDINAL_PATTERN}-o{ORDINAL_PATTERN}$"),
    "conversion-observation": re.compile(rf"^conv{ORDINAL_PATTERN}$"),
    "raw-mapping": re.compile(rf"^map{ORDINAL_PATTERN}$"),
}


def make_record_id(
    extraction_id: str,
    record_type: str,
    source_id: str,
    local_key: str | None = None,
) -> str:
    """Build a deterministic record ID within one extraction.

    Documents use the source ID as their local key. Every other record uses a
    type-specific key such as ``p000001`` or ``fig000001``.
    """
    if not EXTRACTION_ID_PATTERN.fullmatch(extraction_id):
        raise MappingContractError("invalid extraction ID")
    if record_type not in RECORD_TYPES:
        raise MappingContractError(f"unsupported record type: {record_type}")
    if not SOURCE_ID_PATTERN.fullmatch(source_id):
        raise MappingContractError("invalid source ID")

    if record_type == "document":
        if local_key is not None:
            raise MappingContractError("document IDs do not accept a local key")
        record_local_key = source_id
    else:
        if local_key is None:
            raise MappingContractError(f"{record_type} IDs require a local key")
        record_local_key = local_key

    if not LOCAL_KEY_PATTERNS[record_type].fullmatch(record_local_key):
        raise MappingContractError(f"invalid {record_type} local key")

    local_path = source_id if record_type == "document" else f"{source_id}/{local_key}"
    return f"{extraction_id}/{record_type}/{local_path}"


def record_type(record_id: str) -> str:
    """Return the record-type namespace from a schema-valid record ID."""
    return record_id.split("/", maxsplit=2)[1]


def record_local_key(record_id: str) -> str:
    """Return the portion after the extraction, type, and source namespaces."""
    parts = record_id.split("/")
    if len(parts) < 3:
        raise MappingContractError(f"invalid record ID: {record_id}")
    return "/".join(parts[3:]) if len(parts) > 3 else parts[2]


def has_valid_local_key(record_id: str, expected_type: str) -> bool:
    """Return whether an ID has the expected type and local-key grammar."""
    type_marker = f"/{expected_type}/"
    return (
        type_marker in record_id
        and LOCAL_KEY_PATTERNS[expected_type].fullmatch(record_local_key(record_id)) is not None
    )
