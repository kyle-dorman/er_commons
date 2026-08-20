"""Semantic comparison and completion-last downstream report publication."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.chunked_conversion.qualification.downstream_audit import (
    audit_stage_pairs,
    validate_downstream_completion,
    verify_bounded_controls,
)
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    ACCEPTED_DOCUMENT_ID,
    ACCEPTED_PRODUCER_ID,
    AGGREGATE_ID,
    GATE_C_RUN_ID,
    SOURCE_ID,
    DownstreamCompletion,
    DownstreamPaths,
)
from er_commons.chunked_conversion.qualification.downstream_difference_policy import (
    PolicySummary,
    build_difference_policy,
)
from er_commons.chunked_conversion.qualification.downstream_publication import (
    qualify_publication,
)
from er_commons.chunked_conversion.qualification.downstream_stages import qualify_producer
from er_commons.chunked_conversion.qualification.semantic_comparison import (
    DifferencePolicy,
    FileDifferencePolicy,
    PointerPattern,
    TreeComparison,
    compare_trees,
)
from er_commons.document_parsing.content_parsing.evidence import write_inventory

TABLE_EXCLUSIONS = frozenset({"artifact_inventory.json", "environment.json"})
ARTIFACT_MARKER = f"/documents/{SOURCE_ID}/"


def qualify_report(paths: DownstreamPaths) -> Path:
    """Reuse or publish the sealed downstream equivalence report."""
    completion_path = paths.downstream / "records/completion_record.json"
    if completion_path.is_file():
        validate_downstream_completion(paths)
        return completion_path
    publication_completion = qualify_publication(paths)
    producer_completion = qualify_producer(paths)
    producer_root = producer_completion.parents[1]
    actual_document = publication_completion.parents[1]
    stage_seals = audit_stage_pairs(paths)
    verify_bounded_controls(paths, actual_document, stage_seals)
    comparisons = _compare_descendants(paths, producer_root, actual_document)
    report_path = paths.downstream / "records/gate_c_downstream_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        report_path,
        _report_record(
            producer_completion,
            publication_completion,
            stage_seals,
            comparisons,
        ),
    )
    inventory_path = write_inventory(paths.downstream)
    completion = DownstreamCompletion(
        schema_version="er_commons.task03h2_gate_c_downstream_completion.v1",
        status="complete",
        gate_c_run_id=GATE_C_RUN_ID,
        aggregate_conversion_id=AGGREGATE_ID,
        report=report_path.relative_to(paths.downstream).as_posix(),
        artifact_inventory="records/artifact_inventory.json",
        artifact_inventory_sha256=sha256_file(inventory_path),
        completion_last=True,
    )
    write_json_atomic(completion_path, completion.model_dump(mode="json"))
    validate_downstream_completion(paths)
    return completion_path


def _compare_descendants(
    paths: DownstreamPaths, producer_root: Path, actual_document: Path
) -> dict[str, dict[str, Any]]:
    accepted_producer = paths.accepted_task / "document_parse_evidence" / ACCEPTED_PRODUCER_ID
    prefix = f"documents/{SOURCE_ID}/producer"
    accepted_content = paths.accepted_task / (
        f"document_publications/documents/{SOURCE_ID}/{ACCEPTED_DOCUMENT_ID}/content"
    )
    return {
        "routing": _compare(
            accepted_producer / prefix / "routing", producer_root / prefix / "routing"
        ),
        "tables": _compare(
            accepted_producer / prefix / "tables",
            producer_root / prefix / "tables",
            exclude=TABLE_EXCLUSIONS,
        ),
        "canonical": _compare(
            accepted_content / "canonical", actual_document / "content/canonical"
        ),
        "support": _compare(
            accepted_content / "support",
            actual_document / "content/support",
            trusted_control=True,
        ),
    }


def _compare(
    expected: Path,
    actual: Path,
    *,
    exclude: frozenset[str] = frozenset(),
    trusted_control: bool = False,
) -> dict[str, Any]:
    policy, summary = build_difference_policy(
        expected,
        actual,
        artifact_marker=ARTIFACT_MARKER,
        exclude=exclude,
    )
    if trusted_control:
        policy = _allow_verified_control_seals(policy)
    comparison = compare_trees(expected, actual, policy, exclude=exclude)
    return _comparison_record(comparison, summary)


def _allow_verified_control_seals(policy: DifferencePolicy) -> DifferencePolicy:
    relative = "bounded_control_verification.json"
    current = policy.files.get(relative, FileDifferencePolicy())
    ignored = current.ignored + (
        PointerPattern("/control_provenance/artifact_inventory_sha256"),
        PointerPattern("/control_provenance/quality_gate_completion_sha256"),
    )
    replacement = FileDifferencePolicy(
        ignored=ignored,
        stable_identities=current.stable_identities,
        artifact_paths=current.artifact_paths,
        digest_references=current.digest_references,
    )
    return DifferencePolicy({**policy.files, relative: replacement})


def _comparison_record(comparison: TreeComparison, summary: PolicySummary) -> dict[str, Any]:
    return {
        "file_count": comparison.file_count,
        "all_semantic_exact": True,
        "byte_exact_count": comparison.byte_exact_count,
        "difference_policy": asdict(summary),
    }


def _report_record(
    producer_completion: Path,
    publication_completion: Path,
    stage_seals: dict[str, dict[str, dict[str, Any]]],
    comparisons: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    canonical = comparisons["canonical"]
    support = comparisons["support"]
    return {
        "schema_version": "er_commons.task03h2_gate_c_downstream_report.v1",
        "status": "complete",
        "gate_c_run_id": GATE_C_RUN_ID,
        "aggregate_conversion_id": AGGREGATE_ID,
        "producer": {
            "accepted_id": ACCEPTED_PRODUCER_ID,
            "qualification_id": producer_completion.parents[1].name,
            "completion": producer_completion.as_posix(),
        },
        "publication": {
            "accepted_id": ACCEPTED_DOCUMENT_ID,
            "qualification_id": publication_completion.parents[1].name,
            "completion": publication_completion.as_posix(),
        },
        "routing": comparisons["routing"],
        "tables": comparisons["tables"],
        "canonical_document_and_support": {
            "file_count": canonical["file_count"] + support["file_count"],
            "all_semantic_exact": True,
            "byte_exact_count": (canonical["byte_exact_count"] + support["byte_exact_count"]),
            "parts": {"canonical": canonical, "support": support},
        },
        "stage_seals": stage_seals,
        "difference_policy": {
            "context_specific_json_pointers": True,
            "shared_identity_bijection": True,
            "referenced_digest_closure": True,
            "all_other_fields_exact": True,
        },
        "g2_inspected": False,
    }


__all__ = ["qualify_report"]
