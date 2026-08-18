"""Small shape and artifact helpers shared by native collection validators."""

from __future__ import annotations

from pathlib import PurePosixPath

from er_commons.collection_processing.artifact_reader import CollectionArtifactReader
from er_commons.collection_processing.contract import JsonObject


def object_field(value: JsonObject, field: str) -> JsonObject:
    """Return one required object field with a diagnostic name."""
    return object_value(value.get(field), field)


def object_value(value: object, label: str) -> JsonObject:
    """Narrow an arbitrary JSON value to an object."""
    if not isinstance(value, dict):
        raise ValueError(f"collection contract field must be an object: {label}")
    return value


def object_array(value: JsonObject, field: str) -> list[JsonObject]:
    """Return one required array containing only objects."""
    observed = value.get(field)
    if not isinstance(observed, list) or not all(isinstance(item, dict) for item in observed):
        raise ValueError(f"collection contract field must be an object array: {field}")
    return observed


def verify_inventory(record: JsonObject, reader: CollectionArtifactReader) -> None:
    """Verify one managed inventory and every stage-relative file it lists."""
    reference = object_field(record, "artifact_inventory")
    inventory = reader.read_json(reference)
    files = inventory.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise ValueError("collection artifact inventory lacks files")
    inventory_path = reference.get("path")
    if not isinstance(inventory_path, str):
        raise ValueError("collection artifact inventory path is invalid")
    stage_root = PurePosixPath(inventory_path).parent.parent
    paths: list[object] = []
    for item in files:
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ValueError("collection artifact inventory entry path is invalid")
        reader.read({**item, "path": (stage_root / relative).as_posix()})
        paths.append(relative)
    if len(paths) != len(set(paths)):
        raise ValueError("collection artifact inventory repeats a path")


def verify_digest_ref(
    record: JsonObject,
    reference_field: str,
    preimage: JsonObject,
    digest_field: str,
    reader: CollectionArtifactReader,
) -> None:
    """Verify prerequisite bytes and their identity-preimage digest binding."""
    reference = object_field(record, reference_field)
    reader.read(reference)
    if reference.get("sha256") != preimage.get(digest_field):
        raise ValueError(f"collection prerequisite digest differs: {reference_field}")


__all__ = [
    "object_array",
    "object_field",
    "object_value",
    "verify_digest_ref",
    "verify_inventory",
]
