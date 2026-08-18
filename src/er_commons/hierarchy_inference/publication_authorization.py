"""Candidate-neutral machine authorization for hierarchy publication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

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
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return canonical_json_sha256({"semantic_files": records})


@dataclass(frozen=True)
class VerifiedMachinePublication:
    """Opaque binding created after active schema and cross-record validation."""

    candidate_id: str
    candidate_semantic_sha256: str


def authorize_validated_candidate(
    candidate_root: Path,
    candidate_id: str,
) -> VerifiedMachinePublication:
    """Bind publication to the staged candidate that active validators accepted."""
    identity_path = candidate_root / "records/identity.json"
    if (
        not identity_path.is_file()
        or json.loads(identity_path.read_bytes()).get("candidate_id") != candidate_id
    ):
        raise ValueError("machine publication candidate identity differs")
    return VerifiedMachinePublication(
        candidate_id=candidate_id,
        candidate_semantic_sha256=candidate_semantic_sha256(candidate_root),
    )
