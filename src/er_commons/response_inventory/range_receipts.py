"""Small operational receipts for restartable Task 05C pilot ranges."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any, Final, Literal, cast

from er_commons.response_inventory.pilot_policy import TASK05C_PILOT_RANGES

type JsonObject = dict[str, Any]
type PageRange = tuple[int, int]

RECEIPT_SCHEMA_VERSION: Final = "er_commons.response_inventory.range_receipt.v1"

_DIGEST_FIELDS: Final = (
    "code_sha256",
    "config_sha256",
    "run_spec_sha256",
    "schema_sha256",
)
_RECEIPT_FIELDS: Final = {
    "schema_version",
    "range_key",
    "page_range",
    "status",
    "bindings",
    "digests",
    "files",
    "semantic_digest",
    "failure",
}
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}")


def contiguous_range_key(page_range: PageRange) -> str:
    """Return the exact stable key for one inclusive contiguous page range."""
    start, end = page_range
    if start < 1 or end < start:
        raise ValueError(f"invalid contiguous page range: {start}-{end}")
    return f"{start:06d}-{end:06d}"


def build_range_receipt(
    page_range: PageRange,
    *,
    status: Literal["complete", "failed"],
    bindings: Iterable[Mapping[str, object]],
    digests: Mapping[str, str],
    files: Iterable[Mapping[str, object]],
    semantic_digest: str | None,
    failure: str | None = None,
) -> JsonObject:
    """Build one deterministic receipt after validating its restart evidence."""
    range_key = contiguous_range_key(page_range)
    normalized_bindings = _normalize_bindings(bindings)
    normalized_digests = _normalize_digests(digests)
    normalized_files = _normalize_files(files)

    if status == "complete":
        _require_sha256(semantic_digest, "semantic_digest")
        if failure is not None:
            raise ValueError("a complete range receipt cannot contain a failure")
        if not normalized_files:
            raise ValueError("a complete range receipt requires at least one managed file")
    else:
        if semantic_digest is not None:
            _require_sha256(semantic_digest, "semantic_digest")
        if not failure:
            raise ValueError("a failed range receipt requires a failure message")

    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "range_key": range_key,
        "page_range": list(page_range),
        "status": status,
        "bindings": normalized_bindings,
        "digests": normalized_digests,
        "files": normalized_files,
        "semantic_digest": semantic_digest,
        "failure": failure,
    }


def range_receipt_is_reusable(
    receipt: Mapping[str, object],
    page_range: PageRange,
    *,
    bindings: Iterable[Mapping[str, object]],
    digests: Mapping[str, str],
    files: Iterable[Mapping[str, object]],
    semantic_digest: str,
) -> bool:
    """Decide reuse by exact comparison with currently observed range evidence."""
    return not range_receipt_reuse_mismatches(
        receipt,
        page_range,
        bindings=bindings,
        digests=digests,
        files=files,
        semantic_digest=semantic_digest,
    )


def range_receipt_reuse_mismatches(
    receipt: Mapping[str, object],
    page_range: PageRange,
    *,
    bindings: Iterable[Mapping[str, object]],
    digests: Mapping[str, str],
    files: Iterable[Mapping[str, object]],
    semantic_digest: str,
) -> tuple[str, ...]:
    """Name the bounded receipt fields that prevent safe cache reuse."""
    try:
        expected = build_range_receipt(
            page_range,
            status="complete",
            bindings=bindings,
            digests=digests,
            files=files,
            semantic_digest=semantic_digest,
        )
    except (TypeError, ValueError):
        return ("expected_receipt_invalid",)
    observed = dict(receipt)
    fields = sorted(set(observed) | set(expected))
    return tuple(field for field in fields if observed.get(field) != expected.get(field))


def pilot_aggregation_is_ready(receipts: Iterable[Mapping[str, object]]) -> bool:
    """Accept aggregation only after all 14 exact pilot ranges close successfully."""
    return aggregation_is_ready(receipts, TASK05C_PILOT_RANGES)


def aggregation_is_ready(
    receipts: Iterable[Mapping[str, object]], expected_ranges: Iterable[PageRange]
) -> bool:
    """Accept aggregation only after every exact expected range closes successfully."""
    materialized = list(receipts)
    expected = tuple(expected_ranges)
    if not expected or len(materialized) != len(expected):
        return False

    expected_by_key = {contiguous_range_key(page_range): page_range for page_range in expected}
    if len(expected_by_key) != len(expected):
        return False
    observed_by_key: dict[str, JsonObject] = {}
    shared_bindings: object | None = None
    shared_digests: object | None = None
    for receipt in materialized:
        normalized = _validated_receipt(receipt)
        if normalized is None or normalized["status"] != "complete":
            return False
        key = normalized["range_key"]
        if not isinstance(key, str) or key not in expected_by_key or key in observed_by_key:
            return False
        if normalized["page_range"] != list(expected_by_key[key]):
            return False
        if shared_bindings is None:
            shared_bindings = normalized["bindings"]
            shared_digests = normalized["digests"]
        elif normalized["bindings"] != shared_bindings or normalized["digests"] != shared_digests:
            return False
        observed_by_key[key] = normalized
    return set(observed_by_key) == set(expected_by_key)


def _validated_receipt(receipt: Mapping[str, object]) -> JsonObject | None:
    if set(receipt) != _RECEIPT_FIELDS:
        return None
    page_range = receipt.get("page_range")
    status = receipt.get("status")
    if (
        not isinstance(page_range, list)
        or len(page_range) != 2
        or not all(isinstance(value, int) for value in page_range)
        or status not in {"complete", "failed"}
    ):
        return None
    try:
        normalized = build_range_receipt(
            (page_range[0], page_range[1]),
            status=cast(Literal["complete", "failed"], status),
            bindings=_mapping_list(receipt.get("bindings"), "bindings"),
            digests=_string_mapping(receipt.get("digests"), "digests"),
            files=_mapping_list(receipt.get("files"), "files"),
            semantic_digest=_optional_string(receipt.get("semantic_digest")),
            failure=_optional_string(receipt.get("failure")),
        )
    except (TypeError, ValueError):
        return None
    return normalized if dict(receipt) == normalized else None


def _normalize_bindings(bindings: Iterable[Mapping[str, object]]) -> list[JsonObject]:
    normalized: list[JsonObject] = []
    required = {"role", "identity", "authority", "path"}
    for binding in bindings:
        if set(binding) != required or not all(
            isinstance(binding[field], str) and binding[field] for field in required
        ):
            raise ValueError("range receipt bindings require four nonempty string fields")
        normalized.append({field: binding[field] for field in sorted(required)})
    normalized.sort(key=lambda item: (item["role"], item["identity"], item["path"]))
    roles = [item["role"] for item in normalized]
    if not normalized or len(roles) != len(set(roles)):
        raise ValueError("range receipt bindings require unique dependency roles")
    return normalized


def _normalize_digests(digests: Mapping[str, str]) -> JsonObject:
    if set(digests) != set(_DIGEST_FIELDS):
        raise ValueError("range receipt digest fields are incomplete")
    for field in _DIGEST_FIELDS:
        _require_sha256(digests[field], field)
    return {field: digests[field] for field in _DIGEST_FIELDS}


def _normalize_files(files: Iterable[Mapping[str, object]]) -> list[JsonObject]:
    normalized: list[JsonObject] = []
    for item in files:
        if set(item) != {"path", "byte_size"}:
            raise ValueError("range receipt files require path and byte_size")
        path = item["path"]
        byte_size = item["byte_size"]
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("range receipt file path must be a safe relative path")
        if not isinstance(byte_size, int) or isinstance(byte_size, bool) or byte_size < 0:
            raise ValueError("range receipt file size must be a nonnegative integer")
        normalized.append({"path": path, "byte_size": byte_size})
    normalized.sort(key=lambda item: item["path"])
    paths = [item["path"] for item in normalized]
    if len(paths) != len(set(paths)):
        raise ValueError("range receipt file paths must be unique")
    return normalized


def _require_sha256(value: object, field: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _mapping_list(value: object, field: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ValueError(f"{field} must be a list of objects")
    return value


def _string_mapping(value: object, field: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError(f"{field} must be an object of strings")
    return value


def _optional_string(value: object) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise ValueError("expected a string or null")


__all__ = [
    "aggregation_is_ready",
    "build_range_receipt",
    "contiguous_range_key",
    "pilot_aggregation_is_ready",
    "range_receipt_is_reusable",
    "range_receipt_reuse_mismatches",
]
