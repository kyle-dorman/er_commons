"""Invocation-scoped limits for consuming accepted artifact metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from er_commons.artifact_io import JsonValue, load_json, sha256_file

COMPACT_HASH_ROLES = frozenset(
    {
        "completion",
        "managed_inventory",
        "acceptance_pointer",
        "identity_preimage",
        "source_manifest",
        "source_record",
        "run_descriptor",
        "input_binding",
        "code",
        "config",
        "schema",
    }
)


@dataclass
class VerificationBudget:
    """Account for one invocation's compact hashes and selected evidence reads.

    Owners must supply semantic roles, never infer them from a JSON suffix.
    Repeated access is charged again; this object is not a validation cache.
    """

    hash_file_limit: int = 1_048_576
    hash_total_limit: int = 33_554_432
    read_file_limit: int = 536_870_912
    read_total_limit: int = 2_147_483_648
    hashed_bytes: int = 0
    read_bytes: int = 0
    observations: list[dict[str, Any]] = field(default_factory=list)

    def check_metadata(
        self,
        path: Path,
        *,
        root: Path,
        role: str,
        source_id: str,
        byte_size: int | None = None,
    ) -> Path:
        """Check a contained regular file and optional sealed size without reading."""
        resolved = path.resolve()
        context = f"source={source_id} role={role} path={path}"
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            raise ValueError(f"accepted input missing or escapes root: {context}")
        stat = resolved.stat()
        observed = stat.st_size
        if byte_size is not None and observed != byte_size:
            raise ValueError(
                f"accepted input size mismatch: {context} expected={byte_size} observed={observed}"
            )
        self.observations.append(
            {
                "source_id": source_id,
                "role": role,
                "path": str(path),
                "byte_size": observed,
                "verification_mode": "metadata_checked",
                "file_stamp": (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino),
            }
        )
        return resolved

    def hash_file(self, path: Path, *, role: str, source_id: str, root: Path) -> str:
        """Hash an allowlisted compact record only after reserving its byte budget."""
        context = f"source={source_id} role={role} path={path}"
        if role not in COMPACT_HASH_ROLES or path.suffix.lower() in {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".safetensors",
            ".pt",
            ".bin",
        }:
            raise ValueError(f"accepted input hashing role forbidden: {context}")
        resolved = self.check_metadata(path, root=root, role=role, source_id=source_id)
        size = resolved.stat().st_size
        if size > self.hash_file_limit or self.hashed_bytes + size > self.hash_total_limit:
            raise ValueError(f"compact hash budget exceeded before open: {context} bytes={size}")
        self.hashed_bytes += size
        digest = sha256_file(resolved)
        if resolved.stat().st_size != size:
            raise ValueError(f"accepted input changed while hashing: {context}")
        self.observations.append(
            {
                "source_id": source_id,
                "role": role,
                "path": str(path),
                "byte_size": size,
                "sha256": digest,
                "verification_mode": "bytes_verified",
            }
        )
        return digest

    def read_json(self, path: Path, *, role: str, source_id: str, root: Path) -> JsonValue:
        """Read selected JSON evidence under a separate budget without hashing it."""
        resolved = self.reserve_read(path, role=role, source_id=source_id, root=root)
        return load_json(resolved)

    def reserve_read(self, path: Path, *, role: str, source_id: str, root: Path) -> Path:
        """Reserve a full-file upper bound before an owner's selected evidence stream."""
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".safetensors", ".pt", ".bin"}:
            raise ValueError(
                f"source/model read forbidden: source={source_id} role={role} path={path}"
            )
        resolved = self.check_metadata(path, root=root, role=role, source_id=source_id)
        size = resolved.stat().st_size
        if size > self.read_file_limit or self.read_bytes + size > self.read_total_limit:
            raise ValueError(
                f"evidence read budget exceeded before open: source={source_id} "
                f"role={role} path={path} bytes={size}"
            )
        self.read_bytes += size
        self.observations.append(
            {
                "source_id": source_id,
                "role": role,
                "path": str(path),
                "byte_size": size,
                "verification_mode": "evidence_read",
            }
        )
        return resolved
