"""Stat-only closure checks for sealed imported-candidate inventories."""

from __future__ import annotations

import re
import stat
from pathlib import Path, PurePosixPath

from er_commons.collection_processing.contract import JsonObject

_EXCLUDED_SEALS = {"records/artifact_inventory.json", "records/completion_record.json"}


def verify_managed_inventory_closure(
    *, authority_root: Path, root_relative_path: str, inventory: JsonObject
) -> None:
    """Verify exact managed membership and sizes without reading payload files."""
    relative_root = PurePosixPath(root_relative_path)
    if (
        relative_root.is_absolute()
        or relative_root == PurePosixPath(".")
        or ".." in relative_root.parts
        or "\\" in root_relative_path
        or relative_root.as_posix() != root_relative_path
    ):
        raise ValueError("managed inventory root must be normalized POSIX")
    _reject_symlink_components(authority_root, relative_root)
    managed_root = authority_root.joinpath(*relative_root.parts)
    if managed_root.is_symlink() or not managed_root.is_dir():
        raise ValueError("managed inventory root must be a real directory")
    resolved_root = managed_root.resolve()
    if not resolved_root.is_relative_to(authority_root):
        raise ValueError("managed inventory root escapes its authority")
    expected = _inventory_sizes(inventory)
    observed: dict[str, int] = {}
    for path in managed_root.rglob("*"):
        relative = path.relative_to(managed_root).as_posix()
        if path.is_symlink():
            raise ValueError(f"managed inventory contains a symlink: {relative}")
        metadata = path.stat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"managed inventory contains a non-regular file: {relative}")
        if relative not in _EXCLUDED_SEALS:
            observed[relative] = metadata.st_size
    if observed != expected:
        raise ValueError("managed inventory file set or byte sizes differ")


def _inventory_sizes(inventory: JsonObject) -> dict[str, int]:
    files = inventory.get("files")
    if not isinstance(files, list):
        raise ValueError("managed inventory files must be a list")
    expected: dict[str, int] = {}
    total = 0
    for row in files:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "byte_size"}:
            raise ValueError("managed inventory row is malformed")
        path = row.get("path")
        digest = row.get("sha256")
        byte_size = row.get("byte_size")
        if not isinstance(path, str):
            raise ValueError("managed inventory row is invalid")
        pure = PurePosixPath(path)
        if (
            pure.is_absolute()
            or pure == PurePosixPath(".")
            or ".." in pure.parts
            or "\\" in path
            or pure.as_posix() != path
            or path in expected
            or path in _EXCLUDED_SEALS
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not isinstance(byte_size, int)
            or isinstance(byte_size, bool)
            or byte_size < 0
        ):
            raise ValueError("managed inventory row is invalid")
        expected[path] = byte_size
        total += byte_size
    if inventory.get("file_count") != len(expected):
        raise ValueError("managed inventory file count differs")
    declared_total = inventory.get("byte_count", inventory.get("byte_size"))
    if (
        not isinstance(declared_total, int)
        or isinstance(declared_total, bool)
        or declared_total != total
    ):
        raise ValueError("managed inventory byte total differs")
    return expected


def _reject_symlink_components(root: Path, relative: PurePosixPath) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"managed inventory root contains a symlink: {relative}")


__all__ = ["verify_managed_inventory_closure"]
