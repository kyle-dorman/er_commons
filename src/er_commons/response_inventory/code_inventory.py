"""Small output-affecting code inventory shared by Task 05 response stages."""

from __future__ import annotations

import hashlib
from pathlib import Path

from er_commons.artifact_io import canonical_json_sha256


def owned_code_paths(repository_root: Path) -> tuple[Path, ...]:
    """Return shared response-inventory modules and packaging that affect output."""
    package = repository_root / "src/er_commons/response_inventory"
    paths = {path.resolve() for path in package.glob("*.py") if path.name not in {"__main__.py"}}
    paths.add((repository_root / "pyproject.toml").resolve())
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"response-inventory code path is missing: {missing[0]}")
    return tuple(sorted(paths))


def owned_code_digest(repository_root: Path) -> str:
    """Hash paths and bytes for all output-affecting response-inventory code."""
    root = repository_root.resolve()
    inventory = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in owned_code_paths(root)
    ]
    return canonical_json_sha256(inventory)


__all__ = ["owned_code_digest", "owned_code_paths"]
