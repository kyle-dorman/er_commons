"""Independent semantic comparison against the sealed behavioral MVP."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.cross_reference_enrichment.detection import MentionDetector
from er_commons.cross_reference_enrichment.indexing import NamespaceRemapper
from er_commons.cross_reference_enrichment.policy import MentionPolicy
from er_commons.cross_reference_enrichment.source_scope import SourceScope
from er_commons.cross_reference_enrichment.storage import read_json, read_jsonl, write_json
from er_commons.cross_reference_enrichment.types import JsonObject

SUPPORT_PATHS = (
    "support/cross_reference_target_index.json",
    "support/cross_reference_summary.json",
    "support/cross_reference_preservation.json",
)
APPROVED_REMOVAL_DIAGNOSTICS = frozenset(
    {"bibliography", "qualified_external_section", "reference_section", "statutory"}
)


@dataclass(frozen=True)
class ComparisonResult:
    """Exact semantic comparison over every record stream and v3 support role."""

    reference_candidate_id: str
    candidate_id: str
    compared_paths: tuple[str, ...]
    mismatched_paths: tuple[str, ...]

    @property
    def status(self) -> str:
        """Return the closed comparison disposition."""
        return "equivalent" if not self.mismatched_paths else "different"

    def as_json(self) -> JsonObject:
        """Serialize compact, independently reviewable comparison evidence."""
        return {
            "schema_version": "er_commons.cross_reference_rewrite_comparison.v1",
            "reference_candidate_id": self.reference_candidate_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "compared_path_count": len(self.compared_paths),
            "compared_paths": list(self.compared_paths),
            "mismatch_count": len(self.mismatched_paths),
            "mismatched_paths": list(self.mismatched_paths),
        }


@dataclass(frozen=True)
class PolicyCorrectionResult:
    """Audit that a new candidate differs only through explained exclusions."""

    reference_candidate_id: str
    candidate_id: str
    preserved_paths: tuple[str, ...]
    mismatched_preserved_paths: tuple[str, ...]
    removed_mention_count: int
    added_mention_count: int
    changed_shared_mention_count: int
    unexplained_removed_mention_count: int
    removal_diagnostic_counts: dict[str, int]

    @property
    def status(self) -> str:
        """Pass only when every behavioral difference is policy-explained."""
        failures = (
            len(self.mismatched_preserved_paths)
            + self.added_mention_count
            + self.changed_shared_mention_count
            + self.unexplained_removed_mention_count
        )
        return "policy_corrected" if failures == 0 and self.removed_mention_count else "rejected"

    def as_json(self) -> JsonObject:
        """Serialize correction evidence without embedding document text."""
        return {
            "schema_version": "er_commons.cross_reference_policy_correction.v1",
            "reference_candidate_id": self.reference_candidate_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "preserved_path_count": len(self.preserved_paths),
            "mismatched_preserved_paths": list(self.mismatched_preserved_paths),
            "removed_mention_count": self.removed_mention_count,
            "added_mention_count": self.added_mention_count,
            "changed_shared_mention_count": self.changed_shared_mention_count,
            "unexplained_removed_mention_count": self.unexplained_removed_mention_count,
            "removal_diagnostic_counts": dict(sorted(self.removal_diagnostic_counts.items())),
        }


def compare_to_behavioral_reference(
    *, reference_root: Path, candidate_root: Path, reference_id: str, candidate_id: str
) -> ComparisonResult:
    """Compare semantic payloads after only declared candidate-derived normalization."""
    reference_manifest = read_json(reference_root / "records" / "manifest.json")
    record_paths = tuple(item["path"] for item in reference_manifest["record_files"])
    compared_paths = (*record_paths, *SUPPORT_PATHS)
    mismatches: list[str] = []
    remapper = NamespaceRemapper(reference_id, candidate_id)

    for path in record_paths:
        expected = remapper.value(read_jsonl(reference_root / path))
        observed = read_jsonl(candidate_root / path)
        if path == "canonical/cross_references.jsonl":
            expected = _remove_derived_support_checksums(expected)
            observed = _remove_derived_support_checksums(observed)
        if expected != observed:
            mismatches.append(path)
    for path in SUPPORT_PATHS:
        expected_support = remapper.value(read_json(reference_root / path))
        observed_support = read_json(candidate_root / path)
        if expected_support != observed_support:
            mismatches.append(path)
    return ComparisonResult(reference_id, candidate_id, compared_paths, tuple(mismatches))


def compare_policy_correction(
    *,
    reference_root: Path,
    candidate_root: Path,
    reference_id: str,
    candidate_id: str,
    policy: MentionPolicy,
) -> PolicyCorrectionResult:
    """Require exact preservation except for newly explained mention exclusions."""
    manifest = read_json(reference_root / "records" / "manifest.json")
    record_paths = tuple(item["path"] for item in manifest["record_files"])
    preserved_paths = tuple(
        path
        for path in (*record_paths, *SUPPORT_PATHS)
        if path
        not in {
            "canonical/cross_references.jsonl",
            "support/cross_reference_summary.json",
        }
    )
    remapper = NamespaceRemapper(reference_id, candidate_id)
    mismatches = tuple(
        path
        for path in preserved_paths
        if _read_payload(candidate_root, path)
        != remapper.value(_read_payload(reference_root, path))
    )

    reference_mentions = read_jsonl(reference_root / "canonical/cross_references.jsonl")
    candidate_mentions = read_jsonl(candidate_root / "canonical/cross_references.jsonl")
    expected = {
        _mention_key(remapper.value(item)): remapper.value(item) for item in reference_mentions
    }
    observed = {_mention_key(item): item for item in candidate_mentions}
    removed_keys = expected.keys() - observed.keys()
    added_keys = observed.keys() - expected.keys()
    shared_keys = expected.keys() & observed.keys()
    changed_shared = sum(
        _mention_payload(expected[key]) != _mention_payload(observed[key]) for key in shared_keys
    )

    blocks = read_jsonl(reference_root / "canonical/blocks.jsonl")
    scope = SourceScope.from_hierarchy(
        sections=read_jsonl(reference_root / "canonical/sections.jsonl"), blocks=blocks
    )
    detector = MentionDetector(policy, scope)
    blocks_by_local_id = {remapper.value(block["id"]): block for block in blocks}
    diagnostic_counts: dict[str, int] = {}
    unexplained = 0
    for key in removed_keys:
        block = blocks_by_local_id[expected[key]["source_record_id"]]
        detected, diagnostics = detector.detect(block)
        still_detected = any(
            mention.span.as_json() == expected[key]["source_charspan"]
            and mention.kind.value == expected[key]["mention_class"]
            for mention in detected
        )
        categories = {item.category for item in diagnostics}
        approved = sorted(categories & APPROVED_REMOVAL_DIAGNOSTICS)
        if still_detected or not approved:
            unexplained += 1
            continue
        category = approved[0]
        diagnostic_counts[category] = diagnostic_counts.get(category, 0) + 1
    return PolicyCorrectionResult(
        reference_candidate_id=reference_id,
        candidate_id=candidate_id,
        preserved_paths=preserved_paths,
        mismatched_preserved_paths=mismatches,
        removed_mention_count=len(removed_keys),
        added_mention_count=len(added_keys),
        changed_shared_mention_count=changed_shared,
        unexplained_removed_mention_count=unexplained,
        removal_diagnostic_counts=diagnostic_counts,
    )


def write_comparison_report(root: Path, result: ComparisonResult | PolicyCorrectionResult) -> Path:
    """Write one no-clobber report keyed by its complete comparison payload."""
    payload = result.as_json()
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    report = root / f"cmpv1-{digest}" / "comparison.json"
    if report.exists():
        if read_json(report) != payload:
            raise ValueError(f"comparison report collision: {report}")
        return report
    write_json(report, payload)
    return report


def _remove_derived_support_checksums(value: Any) -> Any:
    """Normalize only checksums of the remapped target-index support payload."""
    if isinstance(value, list):
        return [_remove_derived_support_checksums(item) for item in value]
    if isinstance(value, dict):
        normalized = {key: _remove_derived_support_checksums(item) for key, item in value.items()}
        if normalized.get("path") == "support/cross_reference_target_index.json":
            normalized["sha256"] = "<DERIVED_TARGET_INDEX_SHA256>"
        return normalized
    return value


def _read_payload(root: Path, path: str) -> Any:
    return read_json(root / path) if path.endswith(".json") else read_jsonl(root / path)


def _mention_key(mention: JsonObject) -> tuple[str, tuple[int, int], str, str]:
    return (
        mention["source_record_id"],
        tuple(mention["source_charspan"]),
        mention["mention_class"],
        mention["raw_text"],
    )


def _mention_payload(mention: JsonObject) -> JsonObject:
    payload = {
        key: value
        for key, value in mention.items()
        if key not in {"id", "pattern_version", "sequence"}
    }
    normalized = _remove_derived_support_checksums(payload)
    if not isinstance(normalized, dict):
        raise TypeError("normalized mention payload must remain an object")
    return normalized
