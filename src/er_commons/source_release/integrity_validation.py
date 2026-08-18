"""Path-aware type narrowing for persisted source-release integrity records."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import JsonObject, JsonValue


def required(record: JsonObject, key: str, path: Path, *, parent: str = "") -> JsonValue:
    """Return one required integrity-record value with path and key context."""
    location = f"{parent}.{key}" if parent else key
    if key not in record:
        raise ValueError(f"invalid integrity record {path}: missing required key {location}")
    return record[key]


def required_object(
    record: JsonObject,
    key: str,
    path: Path,
    *,
    parent: str = "",
) -> JsonObject:
    """Return one required object-valued field with path and key context."""
    value = required(record, key, path, parent=parent)
    location = f"{parent}.{key}" if parent else key
    if not isinstance(value, dict):
        raise ValueError(f"invalid integrity record {path}: {location} must be an object")
    return value


def required_string(record: JsonObject, key: str, path: Path, *, parent: str = "") -> str:
    """Return one required non-empty string with path and key context."""
    value = required(record, key, path, parent=parent)
    location = f"{parent}.{key}" if parent else key
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid integrity record {path}: {location} must be a non-empty string")
    return value


def required_integer(record: JsonObject, key: str, path: Path, *, parent: str = "") -> int:
    """Return one required non-negative integer with path and key context."""
    value = required(record, key, path, parent=parent)
    location = f"{parent}.{key}" if parent else key
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"invalid integrity record {path}: {location} must be a non-negative integer"
        )
    return value


def required_list(
    record: JsonObject,
    key: str,
    path: Path,
    *,
    parent: str = "",
) -> list[JsonValue]:
    """Return one required list with path and key context."""
    value = required(record, key, path, parent=parent)
    location = f"{parent}.{key}" if parent else key
    if not isinstance(value, list):
        raise ValueError(f"invalid integrity record {path}: {location} must be a list")
    return value


def expect_string(
    record: JsonObject,
    key: str,
    expected: str,
    path: Path,
    *,
    label: str,
) -> None:
    """Require an exact string-valued integrity field."""
    if required_string(record, key, path) != expected:
        raise ValueError(f"{label} mismatch in {path}: key={key}")


def expect_strings(
    record: JsonObject,
    path: Path,
    fields: tuple[tuple[str, str, str], ...],
) -> None:
    """Require several exact string fields without obscuring their error labels."""
    for key, expected, label in fields:
        expect_string(record, key, expected, path, label=label)


def validate_inventory_shape(record: JsonObject, path: Path) -> None:
    """Validate nested inventory types before comparing regenerated content."""
    required_string(record, "schema_version", path)
    required_string(record, "source_release_version", path)
    for page_index, page_value in enumerate(required_list(record, "pages", path)):
        page_location = f"pages[{page_index}]"
        page = _as_object(page_value, path, page_location)
        required_string(page, "key", path, parent=page_location)
        required_string(page, "url", path, parent=page_location)
        links = required_list(page, "links", path, parent=page_location)
        for link_index, link_value in enumerate(links):
            link_location = f"{page_location}.links[{link_index}]"
            link = _as_object(link_value, path, link_location)
            required_integer(link, "position", path, parent=link_location)
            required_integer(link, "document_center_id", path, parent=link_location)
            required_string(link, "label", path, parent=link_location)
            required_string(link, "linked_url", path, parent=link_location)
            required_string(link, "disposition", path, parent=link_location)
            _require_nullable_string(link, "source_id", path, parent=link_location)
            _require_nullable_string(link, "source_role", path, parent=link_location)


def _as_object(value: JsonValue, path: Path, location: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"invalid integrity record {path}: {location} must be an object")
    return value


def _require_nullable_string(record: JsonObject, key: str, path: Path, *, parent: str) -> None:
    value = required(record, key, path, parent=parent)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"invalid integrity record {path}: {parent}.{key} must be string or null")


__all__ = [
    "expect_string",
    "expect_strings",
    "required_integer",
    "required_object",
    "required_string",
    "validate_inventory_shape",
]
