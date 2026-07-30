"""Held-out annotation validation and evidence-derived comparison."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from er_commons.hierarchy_correction.checks import require, require_unique
from er_commons.hierarchy_correction.digests import canonical_json_sha256

JsonRecord = dict[str, Any]


class MismatchKind(StrEnum):
    """Frozen held-out error categories."""

    FALSE_BOUNDARY = "false_boundary"
    FALSE_DEMOTION = "false_demotion"
    MISSED_BOUNDARY = "missed_boundary"
    WRONG_LEVEL_OR_PARENT = "wrong_level_or_parent"
    REGIME_ERROR = "regime_error"


@dataclass(frozen=True)
class ReviewMismatch:
    """One evidence-derived difference from a sealed annotation."""

    stable_item_key: str
    kind: MismatchKind

    def to_record(self) -> JsonRecord:
        """Serialize the mismatch in schema order."""
        return {
            "stable_item_key": self.stable_item_key,
            "kind": self.kind.value,
        }


@dataclass(frozen=True)
class HeldOutEvaluation:
    """Complete comparison result before JSON serialization."""

    candidate_id: str
    annotation_bundle_sha256: str
    mismatches: tuple[ReviewMismatch, ...]
    source_ambiguous_count: int

    @property
    def status(self) -> str:
        """Derive the terminal status from ambiguity and mismatches."""
        if self.source_ambiguous_count:
            return "inconclusive"
        return "reject" if self.mismatches else "pass"

    def to_record(self) -> JsonRecord:
        """Serialize mismatches, derived counts, and terminal status."""
        counts = Counter(mismatch.kind for mismatch in self.mismatches)
        return {
            "record_type": "held_out_evaluation",
            "schema_version": "1.0.0",
            "candidate_id": self.candidate_id,
            "annotation_bundle_sha256": self.annotation_bundle_sha256,
            "evaluated_once": True,
            "mismatches": [mismatch.to_record() for mismatch in self.mismatches],
            "false_boundary_count": counts[MismatchKind.FALSE_BOUNDARY],
            "false_demotion_count": counts[MismatchKind.FALSE_DEMOTION],
            "missed_boundary_count": counts[MismatchKind.MISSED_BOUNDARY],
            "wrong_level_or_parent_count": counts[MismatchKind.WRONG_LEVEL_OR_PARENT],
            "regime_error_count": counts[MismatchKind.REGIME_ERROR],
            "source_ambiguous_count": self.source_ambiguous_count,
            "status": self.status,
        }


def validate_held_out_review_record(
    record: JsonRecord,
    *,
    expected_pages: set[int] | None = None,
) -> None:
    """Validate annotation completeness or evaluation accounting."""
    if record["record_type"] == "held_out_annotations":
        _validate_annotation_bundle(record, expected_pages)
    else:
        _validate_evaluation_record(record)


def build_held_out_evaluation(
    annotations: JsonRecord,
    candidate: JsonRecord,
) -> JsonRecord:
    """Compare sealed source annotations with one correction candidate."""
    identity = candidate["identity"]
    for field_name in ("source_sha256", "policy_sha256", "code_bundle_sha256"):
        require(
            annotations[field_name] == identity[field_name],
            f"annotation {field_name} differs from candidate",
        )

    decisions_by_key = {item["stable_item_key"]: item for item in candidate["decisions"]}
    parents_by_key = {
        item["child_key"]: item["parent_key"] for item in candidate["hierarchy"]["edges"]
    }
    regime_actions_by_key = _regime_actions(candidate["regimes"])

    mismatches: list[ReviewMismatch] = []
    source_ambiguous_count = 0
    for page in annotations["pages"]:
        for expected in page["annotations"]:
            if expected["source_ambiguous"]:
                source_ambiguous_count += 1
                continue
            key = expected["stable_item_key"]
            require(key in decisions_by_key, f"annotation references unknown item: {key}")
            mismatches.extend(
                _compare_annotation(
                    expected=expected,
                    decision=decisions_by_key[key],
                    actual_parent_key=parents_by_key.get(key),
                    actual_regime_action=regime_actions_by_key.get(key, "none"),
                )
            )

    evaluation = HeldOutEvaluation(
        candidate_id=identity["candidate_id"],
        annotation_bundle_sha256=canonical_json_sha256(annotations),
        mismatches=tuple(mismatches),
        source_ambiguous_count=source_ambiguous_count,
    )
    return evaluation.to_record()


def _validate_annotation_bundle(
    record: JsonRecord,
    expected_pages: set[int] | None,
) -> None:
    """Require complete, ordered annotation coverage for each held-out page."""
    page_numbers = [page["physical_page"] for page in record["pages"]]
    require_unique(page_numbers, "duplicate review page")
    if expected_pages is not None:
        require(set(page_numbers) == expected_pages, "held-out page coverage differs")

    for page in record["pages"]:
        expected_keys = page["eligible_item_keys"]
        annotated_keys = [annotation["stable_item_key"] for annotation in page["annotations"]]
        require_unique(
            annotated_keys,
            f"duplicate review annotation on page {page['physical_page']}",
        )
        require(
            annotated_keys == expected_keys,
            f"review annotation coverage or order differs on page {page['physical_page']}",
        )


def _validate_evaluation_record(record: JsonRecord) -> None:
    """Recompute mismatch counts and status from serialized details."""
    counts = Counter(mismatch["kind"] for mismatch in record["mismatches"])
    for kind in MismatchKind:
        require(
            record[f"{kind.value}_count"] == counts[kind.value],
            f"{kind.value} count differs",
        )

    if record["source_ambiguous_count"]:
        expected_status = "inconclusive"
    else:
        expected_status = "reject" if record["mismatches"] else "pass"
    require(record["status"] == expected_status, "held-out evaluation status differs")


def _regime_actions(regimes: list[JsonRecord]) -> dict[str, str]:
    """Index persisted start/end actions by their stable item key."""
    actions: dict[str, str] = {}
    for regime in regimes:
        actions[regime["start_item_key"]] = "start"
        if regime["end_item_key"] is not None:
            actions[regime["end_item_key"]] = "end"
    return actions


def _compare_annotation(
    *,
    expected: JsonRecord,
    decision: JsonRecord,
    actual_parent_key: str | None,
    actual_regime_action: str,
) -> list[ReviewMismatch]:
    """Classify every mismatch for one unambiguous source annotation."""
    key = expected["stable_item_key"]
    mismatches = []
    predicted_boundary = decision["corrected_role"] == "heading"

    if expected["expected_boundary"] and not predicted_boundary:
        kind = (
            MismatchKind.FALSE_DEMOTION
            if decision["selected_rule_id"] == "R02_DEMOTE_BULLET_HEADING"
            else MismatchKind.MISSED_BOUNDARY
        )
        mismatches.append(ReviewMismatch(key, kind))
    elif not expected["expected_boundary"] and predicted_boundary:
        mismatches.append(ReviewMismatch(key, MismatchKind.FALSE_BOUNDARY))
    elif expected["expected_boundary"] and (
        decision["corrected_level"] != expected["expected_level"]
        or actual_parent_key != expected["expected_parent_key"]
    ):
        mismatches.append(ReviewMismatch(key, MismatchKind.WRONG_LEVEL_OR_PARENT))

    if actual_regime_action != expected["expected_regime_action"]:
        mismatches.append(ReviewMismatch(key, MismatchKind.REGIME_ERROR))
    return mismatches
