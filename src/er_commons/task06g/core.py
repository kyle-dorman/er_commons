"""Deterministic, bounded artifact primitives for Task 06G orchestration."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256, json_bytes, sha256_bytes, sha256_file

JsonObject = dict[str, Any]
FORBIDDEN_PAYLOAD_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".webp",
    ".pt",
    ".pth",
    ".bin",
    ".safetensors",
}


def load_object(path: Path) -> JsonObject:
    """Load one UTF-8 JSON object with contextual errors."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: object) -> bytes:
    """Return the repository's deterministic newline-terminated JSON bytes."""
    return json_bytes(value)


def derive_identity(prefix: str, preimage: object) -> str:
    """Derive an identity from RFC 8785 canonical JSON without hidden inputs."""
    if not prefix or not prefix.endswith("-"):
        raise ValueError("identity prefix must be nonempty and end with '-'")
    return prefix + canonical_json_sha256(preimage)


def reference(path: Path, *, root: Path | None = None) -> JsonObject:
    """Return an exact path, size, and digest reference for a small artifact."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"referenced artifact is not a file: {path}")
    if resolved.suffix.lower() in FORBIDDEN_PAYLOAD_SUFFIXES:
        raise ValueError(f"prohibited payload access: {resolved}")
    rendered = str(resolved)
    if root is not None:
        resolved_root = root.resolve()
        if not resolved.is_relative_to(resolved_root):
            raise ValueError(f"artifact escapes declared root: {resolved}")
        rendered = resolved.relative_to(resolved_root).as_posix()
    return {"path": rendered, "sha256": sha256_file(resolved), "byte_size": resolved.stat().st_size}


def verify_reference(value: Mapping[str, object], *, root: Path | None = None) -> Path:
    """Verify one exact artifact reference without accepting implicit selection."""
    raw_path = value.get("path")
    digest = value.get("sha256")
    size = value.get("byte_size")
    if not isinstance(raw_path, str) or not isinstance(digest, str) or not isinstance(size, int):
        raise ValueError("artifact reference requires path, sha256, and byte_size")
    path = Path(raw_path)
    if root is not None:
        path = root / path
    observed = reference(path, root=root)
    if observed["sha256"] != digest or observed["byte_size"] != size:
        raise ValueError(f"artifact reference mismatch: {path}")
    return path.resolve()


def parse_pointer(pointer: str) -> list[str]:
    """Parse an exact RFC 6901 pointer; wildcards are never accepted."""
    if pointer == "":
        return []
    if not pointer.startswith("/") or "*" in pointer:
        raise ValueError(f"invalid or non-exact JSON pointer: {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def pointer_value(document: object, pointer: str) -> object:
    """Read one exact JSON pointer from a document."""
    current = document
    for token in parse_pointer(pointer):
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ValueError(f"JSON pointer does not exist: {pointer}")
    return current


def set_pointer(document: JsonObject, pointer: str, value: object) -> None:
    """Replace one existing exact JSON-pointer target in place."""
    tokens = parse_pointer(pointer)
    if not tokens:
        raise ValueError("runtime resolution cannot replace a document root")
    parent: object = document
    for token in tokens[:-1]:
        if isinstance(parent, dict) and token in parent:
            parent = parent[token]
        elif isinstance(parent, list) and token.isdigit() and int(token) < len(parent):
            parent = parent[int(token)]
        else:
            raise ValueError(f"JSON pointer parent does not exist: {pointer}")
    last = tokens[-1]
    if isinstance(parent, dict) and last in parent:
        parent[last] = value
    elif isinstance(parent, list) and last.isdigit() and int(last) < len(parent):
        parent[int(last)] = value
    else:
        raise ValueError(f"JSON pointer target does not exist: {pointer}")


def exact_inventory(root: Path, *, excluded: Iterable[str] = ()) -> JsonObject:
    """Build a sorted exact closure of non-payload files beneath a root."""
    excluded_set = set(excluded)
    refs = [
        reference(path, root=root)
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.relative_to(root).as_posix() not in excluded_set
    ]
    return {
        "file_count": len(refs),
        "byte_count": sum(item["byte_size"] for item in refs),
        "files": refs,
    }


def publish_directory_no_clobber(
    destination: Path,
    files: Mapping[str, bytes],
    *,
    after_write: Callable[[str], None] | None = None,
    after_rename: Callable[[], None] | None = None,
) -> None:
    """Write a complete sibling staging directory and atomically publish it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent))
    try:
        for relative, content in files.items():
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            if after_write is not None:
                after_write(relative)
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite existing directory: {destination}")
        staging.rename(destination)
        if after_rename is not None:
            after_rename()
        descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except Exception:
        # Preserve staging evidence by design.
        raise


def content_reference(path: str, content: bytes) -> JsonObject:
    """Describe deterministic bytes before publication."""
    return {"path": path, "sha256": sha256_bytes(content), "byte_size": len(content)}
