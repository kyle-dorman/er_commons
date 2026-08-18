"""Read-only inventory seals used to prove a downstream-only replay."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from er_commons.task03g2f_replay.errors import ReplayValidationError


@dataclass(frozen=True)
class DirectoryInventory:
    """Stable summary of directory names below one attempt root."""

    root_exists: bool
    directory_count: int
    path_digest: str


AttemptSnapshot = dict[str, DirectoryInventory]


def snapshot_attempts(roots: dict[str, Path]) -> AttemptSnapshot:
    """Describe attempt directories without reading or changing their artifacts."""
    snapshot: AttemptSnapshot = {}
    for label, root in roots.items():
        paths = sorted(
            path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()
        )
        snapshot[label] = DirectoryInventory(
            root_exists=root.is_dir(),
            directory_count=len(paths),
            path_digest=hashlib.sha256("\n".join(paths).encode()).hexdigest(),
        )
    return snapshot


def require_unchanged(
    before: AttemptSnapshot,
    after: AttemptSnapshot,
    *,
    operation: str,
) -> None:
    """Reject any upstream or document-attempt allocation during replay."""
    if after != before:
        raise ReplayValidationError(
            "ATTEMPT_INVENTORY_CHANGED",
            "downstream replay changed a forbidden attempt namespace",
            operation=operation,
            before=serialize_snapshot(before),
            after=serialize_snapshot(after),
        )


def serialize_snapshot(snapshot: AttemptSnapshot) -> dict[str, object]:
    """Convert a typed snapshot to report-safe JSON values."""
    return {label: asdict(inventory) for label, inventory in snapshot.items()}
