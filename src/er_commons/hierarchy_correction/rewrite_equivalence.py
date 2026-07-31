"""Exact semantic comparison for the human-ownership rewrite."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.hierarchy_correction.candidate_records import stable_json_bytes

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None
SEMANTIC_COLLECTIONS = (
    "features",
    "toc_entries",
    "reconciliations",
    "regimes",
    "decisions",
    "ambiguities",
    "warnings",
)
HIERARCHY_COLLECTIONS = (
    "roots",
    "edges",
    "direct_membership",
    "unassigned_content",
)


@dataclass(frozen=True)
class SemanticReference:
    """Checksum-verified MVP payload used only as rewrite evidence."""

    reference_id: str
    semantic: dict[str, Any]
    semantic_sha256: str
    source_sha256: str
    config_sha256: str
    policy_sha256: str
    schema_sha256: str


@dataclass(frozen=True)
class SemanticComparison:
    """Exact comparison result with the first actionable mismatch path."""

    reference_sha256: str
    rewritten_sha256: str
    first_mismatch_path: str | None
    counts: dict[str, int]

    @property
    def matches(self) -> bool:
        """Return whether every semantic value and serialized byte matches."""
        return self.first_mismatch_path is None and self.reference_sha256 == self.rewritten_sha256


def load_semantic_reference(reference_root: Path) -> SemanticReference:
    """Load and verify one frozen MVP manifest and semantic payload."""
    manifest = _json_object(reference_root / "reference_manifest.json")
    semantic_path = reference_root / manifest["semantic_path"]
    raw = semantic_path.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != manifest["semantic_sha256"]:
        raise ValueError(
            "rewrite reference checksum differs: "
            f"expected={manifest['semantic_sha256']}, actual={actual_sha256}, "
            f"path={semantic_path}"
        )
    semantic = _json_object(semantic_path)
    expected_bytes = stable_json_bytes(semantic)
    if raw != expected_bytes:
        raise ValueError(f"rewrite reference is not canonical JSON: path={semantic_path}")
    return SemanticReference(
        reference_id=manifest["reference_id"],
        semantic=semantic,
        semantic_sha256=actual_sha256,
        source_sha256=manifest["source_sha256"],
        config_sha256=manifest["config_sha256"],
        policy_sha256=manifest["policy_sha256"],
        schema_sha256=manifest["schema_sha256"],
    )


def compare_semantic_payloads(
    reference: SemanticReference,
    rewritten: dict[str, Any],
) -> SemanticComparison:
    """Compare the complete ordered semantic payload without normalization."""
    rewritten_bytes = stable_json_bytes(rewritten)
    mismatch = _first_mismatch(reference.semantic, rewritten, path="$semantic")
    return SemanticComparison(
        reference_sha256=reference.semantic_sha256,
        rewritten_sha256=hashlib.sha256(rewritten_bytes).hexdigest(),
        first_mismatch_path=mismatch,
        counts=_semantic_counts(rewritten),
    )


def write_equivalence_evidence(
    *,
    reference: SemanticReference,
    rewritten: dict[str, Any],
    rewritten_code_bundle_sha256: str,
    review_root: Path,
) -> Path:
    """Write one no-clobber rewritten payload and exact comparison report."""
    comparison = compare_semantic_payloads(reference, rewritten)
    identity_bytes = stable_json_bytes(
        {
            "reference_id": reference.reference_id,
            "rewritten_code_bundle_sha256": rewritten_code_bundle_sha256,
        }
    )
    comparison_id = f"cmpv1-{hashlib.sha256(identity_bytes).hexdigest()}"
    destination = review_root / comparison_id
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "reference_semantic.json").write_bytes(stable_json_bytes(reference.semantic))
    rewritten_path = destination / "rewritten_semantic.json"
    rewritten_path.write_bytes(stable_json_bytes(rewritten))
    report = {
        "record_type": "hierarchy_correction_rewrite_equivalence",
        "schema_version": "1.0.0",
        "comparison_id": comparison_id,
        "reference_id": reference.reference_id,
        "reference_semantic_sha256": comparison.reference_sha256,
        "rewritten_semantic_sha256": comparison.rewritten_sha256,
        "rewritten_code_bundle_sha256": rewritten_code_bundle_sha256,
        "first_mismatch_path": comparison.first_mismatch_path,
        "counts": comparison.counts,
        "status": "pass" if comparison.matches else "reject",
    }
    (destination / "equivalence_report.json").write_bytes(stable_json_bytes(report))
    return destination / "equivalence_report.json"


def _semantic_counts(semantic: dict[str, Any]) -> dict[str, int]:
    """Report collection sizes so equality evidence remains easy to inspect."""
    counts = {name: len(semantic[name]) for name in SEMANTIC_COLLECTIONS}
    hierarchy = semantic["hierarchy"]
    counts.update({name: len(hierarchy[name]) for name in HIERARCHY_COLLECTIONS})
    return counts


def _first_mismatch(reference: JsonValue, rewritten: JsonValue, *, path: str) -> str | None:
    """Return the first deterministic structural or scalar mismatch path."""
    if type(reference) is not type(rewritten):
        return f"{path} (type: {type(reference).__name__} != {type(rewritten).__name__})"
    if isinstance(reference, dict) and isinstance(rewritten, dict):
        reference_keys = set(reference)
        rewritten_keys = set(rewritten)
        if reference_keys != rewritten_keys:
            missing = sorted(reference_keys - rewritten_keys)
            extra = sorted(rewritten_keys - reference_keys)
            return f"{path} (missing_keys={missing}, extra_keys={extra})"
        for key in sorted(reference):
            mismatch = _first_mismatch(reference[key], rewritten[key], path=f"{path}.{key}")
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(reference, list) and isinstance(rewritten, list):
        if len(reference) != len(rewritten):
            return f"{path} (length: {len(reference)} != {len(rewritten)})"
        for index, (left, right) in enumerate(zip(reference, rewritten, strict=True)):
            mismatch = _first_mismatch(left, right, path=f"{path}[{index}]")
            if mismatch is not None:
                return mismatch
        return None
    return None if reference == rewritten else f"{path} ({reference!r} != {rewritten!r})"


def _json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object with its path in any failure."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: path={path}")
    return value
