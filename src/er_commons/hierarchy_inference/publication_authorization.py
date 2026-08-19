"""Candidate-neutral machine authorization for hierarchy publication."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_inference.digests import canonical_json_sha256

SEMANTIC_PATHS = (
    "artifacts/item_features.jsonl",
    "artifacts/visible_toc_entries.jsonl",
    "artifacts/toc_reconciliation.jsonl",
    "artifacts/regimes.jsonl",
    "artifacts/decisions.jsonl",
    "artifacts/hierarchy.json",
    "artifacts/ambiguities.jsonl",
    "artifacts/warnings.jsonl",
)


class VerifiedPublicationAuthorization:
    """Nominal candidate and semantic binding accepted by the publication seam."""

    __slots__ = ("_publication_authorization_marker",)

    candidate_id: str
    candidate_semantic_sha256: str


_PUBLICATION_AUTHORIZATION_MARKER = object()


def _mark_verified_authorization(
    authorization: VerifiedPublicationAuthorization,
) -> None:
    """Mark a nominal authorization created by an owning verifier."""
    object.__setattr__(
        authorization,
        "_publication_authorization_marker",
        _PUBLICATION_AUTHORIZATION_MARKER,
    )


def is_verified_publication_authorization(value: object) -> bool:
    """Reject nominal or structural lookalikes not produced by an owning verifier."""
    return (
        isinstance(value, VerifiedPublicationAuthorization)
        and getattr(value, "_publication_authorization_marker", None)
        is _PUBLICATION_AUTHORIZATION_MARKER
    )


def candidate_semantic_sha256(candidate_root: Path) -> str:
    """Hash exact semantic file checksums under the accepted digest contract."""
    records: list[dict[str, str]] = []
    for relative in SEMANTIC_PATHS:
        path = candidate_root / relative
        if not path.is_file():
            raise ValueError(f"candidate semantic file is missing: {relative}")
        records.append(
            {
                "path": relative,
                "sha256": _sha256_file(path),
            }
        )
    return canonical_json_sha256({"semantic_files": records})


def candidate_semantic_sha256_from_inventory(inventory: dict[str, Any]) -> str:
    """Derive the semantic digest from an already completion-sealed inventory."""
    by_path = {item["path"]: item for item in inventory["files"]}
    if not all(relative in by_path for relative in SEMANTIC_PATHS):
        raise ValueError("candidate inventory omits semantic files")
    records = [
        {"path": relative, "sha256": by_path[relative]["sha256"]} for relative in SEMANTIC_PATHS
    ]
    return canonical_json_sha256({"semantic_files": records})


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash one semantic file without allocating its complete byte content."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, init=False)
class VerifiedMachinePublication(VerifiedPublicationAuthorization):
    """Opaque binding created after active schema and cross-record validation."""

    candidate_id: str
    candidate_semantic_sha256: str


def _machine_authorization_from_verified_seal(
    candidate_id: str,
    candidate_semantic_sha256: str,
) -> VerifiedMachinePublication:
    """Mint the nominal capability only from validation/seal owning modules."""
    authorization = object.__new__(VerifiedMachinePublication)
    object.__setattr__(authorization, "candidate_id", candidate_id)
    object.__setattr__(
        authorization,
        "candidate_semantic_sha256",
        candidate_semantic_sha256,
    )
    _mark_verified_authorization(authorization)
    return authorization
