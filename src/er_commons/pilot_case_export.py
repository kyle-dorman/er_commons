"""Export Task 07D cases from sealed reviews and explicit human dispositions.

The pure aggregator owns citation levels. This module owns file verification,
review normalization and the no-overwrite publication boundary. It never edits
Label Studio, source records or a prior release. A manifest written last marks
completion; a directory without that manifest is an incomplete attempt.
"""

import argparse
import copy
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.pilot_case_citations import aggregate_case_citations
from er_commons.pilot_evidence import (
    ReviewValidationError,
    digest,
    normalize_claim_review,
    validate_candidates,
)

LOGGER = logging.getLogger(__name__)


def file_hash(path: Path) -> str:
    """Hash full file bytes with bounded memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path) -> Any:
    """Report the input filename when a JSON record cannot be read."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot read JSON input {path}: {error}") from error


def write_json(path: Path, value: Any) -> None:
    """Never overwrite an output from a completed or interrupted attempt."""
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def bound_path(root: Path, relative: str) -> Path:
    """Reject absolute or escaping paths in artifact bindings."""
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError(f"Artifact path escapes its root: {relative}")
    return path


def verify_manifest(root: Path, expected_hash: str) -> dict[str, Any]:
    """Check a pinned manifest, every file hash and exact managed file closure."""
    manifest_path = root / "manifest.json"
    if file_hash(manifest_path) != expected_hash:
        raise ValueError(f"Manifest hash mismatch: {manifest_path}")
    manifest: dict[str, Any] = read_json(manifest_path)
    entries = manifest.get("managed_files", manifest.get("files"))
    if isinstance(entries, dict):
        entries = [{"path": name, "sha256": value} for name, value in entries.items()]
    if not isinstance(entries, list):
        raise ValueError(f"Missing managed files: {manifest_path}")
    names = [entry["path"] for entry in entries]
    actual = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if len(names) != len(set(names)) or set(names) != actual:
        raise ValueError(f"Managed file closure mismatch: {root}")
    for entry in entries:
        path = bound_path(root, entry["path"])
        if file_hash(path) != entry["sha256"]:
            raise ValueError(f"Managed file hash mismatch: {path}")
    return manifest


@dataclass(frozen=True)
class ExportInputs:
    """Verified inputs; prior strict errors are the only eligible MVP exceptions."""

    data_root: Path
    review_root: Path
    disposition_root: Path
    disposition: dict[str, Any]
    accepted_cases: dict[str, dict[str, Any]]
    recorded_errors: dict[int, str]
    input_bindings: dict[str, Any]


def unique_records(rows: list[dict[str, Any]], key: str) -> dict[Any, dict[str, Any]]:
    """Reject duplicate input identities before indexing instead of losing records."""
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"Duplicate input identity: {key}")
    return indexed


def validate_case_name(case: str) -> None:
    """Case labels are single filenames, never paths supplied by review data."""
    if not case or case in {".", ".."} or "/" in case or "\\" in case:
        raise ValueError(f"Invalid case label for export: {case!r}")


def load_inputs(data_root: Path, review_status: Path, claim_handoff: Path) -> ExportInputs:
    """Verify both sealed review releases and the accepted claim handoff before use."""
    status = read_json(review_status)
    reviews = bound_path(data_root, status["artifact_root_relative"])
    dispositions = bound_path(data_root, status["user_disposition_artifact"])
    verify_manifest(reviews, status["manifest_sha256"])
    verify_manifest(dispositions, status["user_disposition_manifest_sha256"])
    handoff = read_json(claim_handoff)
    claim_manifest = bound_path(data_root, handoff["export_manifest"]["path"])
    verify_manifest(claim_manifest.parent, handoff["export_manifest"]["sha256"])
    disposition = read_json(dispositions / "disposition.json")
    if disposition["source_manifest_sha256"] != status["manifest_sha256"]:
        raise ValueError("Disposition targets a different native review release")
    cases = unique_records(
        [
            review
            for review in read_json(claim_manifest.parent / "reviews.json")
            if review["eligible_for_next_stage"]
        ],
        "case_label",
    )
    for case in cases:
        validate_case_name(case)
    error_rows = [issue for case in read_json(reviews / "summary.json") for issue in case["errors"]]
    errors = {
        identity: row["error"] for identity, row in unique_records(error_rows, "task").items()
    }
    unique_records(disposition["accepted_mvp_consistency_warnings"], "task_id")
    return ExportInputs(
        data_root=data_root,
        review_root=reviews,
        disposition_root=dispositions,
        disposition=disposition,
        accepted_cases=cases,
        recorded_errors=errors,
        input_bindings={
            "review_manifest": {
                "path": str((reviews / "manifest.json").relative_to(data_root)),
                "sha256": status["manifest_sha256"],
            },
            "disposition_manifest": {
                "path": str((dispositions / "manifest.json").relative_to(data_root)),
                "sha256": status["user_disposition_manifest_sha256"],
            },
            "claim_manifest": handoff["export_manifest"],
        },
    )


def clarified_annotation(task: dict[str, Any], correction: dict[str, Any]) -> dict[str, Any]:
    """Apply only the explicitly bound source-label correction to a deep copy."""
    original: dict[str, Any] = task["annotations"][0]
    data = task["data"]
    if original["id"] != correction["annotation_id"] or data["claim_id"] != correction["claim_id"]:
        raise ValueError("Clarification does not match this annotation and claim")
    slot = data["slots"][0]
    try:
        index = slot["candidate_ids"].index(correction["candidate_id"]) + 1
    except ValueError as error:
        raise ValueError("Clarified candidate is absent from the reviewed task") from error
    if correction["field"] != f"{slot['slot']}_p{index:02d}_label":
        raise ValueError("Clarification field targets a different candidate")
    revised = copy.deepcopy(original)
    matches = [field for field in revised["result"] if field["from_name"] == correction["field"]]
    if len(matches) != 1 or matches[0]["value"]["choices"] != [correction["original"]]:
        raise ValueError("Clarification original label does not match")
    matches[0]["value"]["choices"] = [correction["effective"]]
    return revised


def normalize_export_review(
    task: dict[str, Any], expected: dict[str, Any], inputs: ExportInputs, lineage: str
) -> dict[str, Any]:
    """Keep user-approved consistency warnings without a second native-field parser."""
    if task["data"] != expected["data"] or len(task["annotations"]) != 1:
        raise ValueError("Require exact trusted task data and one native annotation")
    annotation = task["annotations"][0]
    correction = inputs.disposition["task164_correction"]
    is_correction = annotation["id"] == correction["annotation_id"]
    effective = clarified_annotation(task, correction) if is_correction else annotation
    try:
        review = normalize_claim_review(
            task, effective, expected_task=expected, export_lineage=lineage
        )
    except ReviewValidationError as error:
        allowed = {
            row["task_id"] for row in inputs.disposition["accepted_mvp_consistency_warnings"]
        }
        if task["id"] not in allowed or str(error) != inputs.recorded_errors.get(task["id"]):
            raise
        review = error.review
        review["strict_validation_passed"] = False
        review["disposition"] = str(inputs.disposition_root.relative_to(inputs.data_root))
    if is_correction:
        if review["claim_review"]["outcome"] != correction["claim_outcome"]:
            raise ValueError("Clarified claim outcome differs from user disposition")
        review["effective_annotation"] = effective
        review["effective_annotation_sha256"] = digest(effective)
        review["native_annotation"] = annotation
        review["annotation_sha256"] = digest(annotation)
        review["clarification"] = correction
        review["native_label_modified"] = False
    return review


def build_case(
    case: str, accepted: dict[str, Any], inputs: ExportInputs, lineage: str
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Validate one case's unchanged approved claims, source units and review coverage."""
    validate_case_name(case)
    case_root = inputs.review_root / case
    tasks = read_json(case_root / "trusted_tasks.json")
    task_claim_ids = [task["data"]["claim_id"] for task in tasks]
    if len(task_claim_ids) != len(set(task_claim_ids)):
        raise ValueError(f"Duplicate trusted claim tasks: {case}")
    expected = dict(zip(task_claim_ids, tasks, strict=True))
    packet = tasks[0]["data"]["packet"]
    claims = unique_records(packet["claims"], "claim_id")
    prior = unique_records(accepted["claims"], "claim_id")
    if set(claims) != set(accepted["evidence_candidate_claim_ids"]) or set(claims) != set(expected):
        raise ValueError(f"Claim membership differs from accepted handoff: {case}")
    if any(claim != prior[identity] for identity, claim in claims.items()):
        raise ValueError(f"Claim content differs from accepted handoff: {case}")
    validate_candidates(packet, inputs.data_root)
    reviews = []
    for path in sorted(case_root.glob("task_*.json")):
        task = read_json(path)
        if task["data"]["packet"] != packet:
            raise ValueError(f"Inconsistent source packet: {path}")
        reviews.append(
            normalize_export_review(task, expected[task["data"]["claim_id"]], inputs, lineage)
        )
    bundle = aggregate_case_citations(packet, reviews)
    audit = bundle.pop("audit")
    audit["source_packet"] = packet
    bundle["reviewed_concerns"] = accepted["data"]["claim_input"]["reviewed_concerns"]
    bundle["comment_id"] = accepted["data"]["claim_input"]["comment_id"]
    bundle["limitations"] = {
        "context_optional_for_required_coverage": True,
        "claim_relevance_noise_retained_by_user": True,
        "accepted_mvp_warning_tasks": sorted(
            review["task_id"]
            for review in reviews
            if review.get("strict_validation_passed") is False
        ),
        "source_discovery_gaps": packet.get("discovery_scope"),
        "provenance": f"../audit/{case}.json",
    }
    return bundle, audit, reviews


def export_cases(inputs: ExportInputs, output: Path) -> dict[str, Any]:
    """Publish new case/audit files and write a completion manifest only after validation."""
    for case in inputs.accepted_cases:
        validate_case_name(case)
    protected_roots = [inputs.review_root, inputs.disposition_root]
    claim_binding = inputs.input_bindings.get("claim_manifest")
    if claim_binding:
        protected_roots.append(bound_path(inputs.data_root, claim_binding["path"]).parent)
    if any(output.resolve().is_relative_to(root.resolve()) for root in protected_roots):
        raise ValueError("Output cannot be inside a sealed input release")
    output.mkdir(parents=True, exist_ok=False)
    (output / "cases").mkdir()
    (output / "audit").mkdir()
    summaries = []
    seen_warnings: set[int] = set()
    correction_count = 0
    lineage = str(output)
    for case, accepted in sorted(inputs.accepted_cases.items()):
        LOGGER.info("Validating and exporting case %s", case)
        bundle, audit, reviews = build_case(case, accepted, inputs, lineage)
        write_json(output / "cases" / f"{case}.json", bundle)
        write_json(output / "audit" / f"{case}.json", audit)
        write_json(output / "audit" / f"{case}.effective_reviews.json", reviews)
        correction_count += sum("clarification" in review for review in reviews)
        warning_ids = bundle["limitations"]["accepted_mvp_warning_tasks"]
        seen_warnings.update(warning_ids)
        summaries.append(
            {
                "case_id": case,
                "claims": len(bundle["claims"]),
                "citations": len(bundle["citations"]),
                "support": sum(c["level"] == "support" for c in bundle["citations"]),
                "context": sum(c["level"] == "context" for c in bundle["citations"]),
                "accepted_mvp_warning_tasks": warning_ids,
            }
        )
    allowed = {row["task_id"] for row in inputs.disposition["accepted_mvp_consistency_warnings"]}
    if correction_count != 1:
        raise ValueError("Expected exactly one applied user clarification")
    if seen_warnings != allowed:
        raise ValueError("Accepted warning task coverage differs from the disposition")
    if sum(row["claims"] for row in summaries) != inputs.disposition["claim_count_retained"]:
        raise ValueError("Exported claim count differs from the user disposition")
    summary = {"status": "complete_with_explicit_mvp_warnings", "cases": summaries}
    write_json(output / "summary.json", summary)
    files = [
        {"path": str(path.relative_to(output)), "sha256": file_hash(path)}
        for path in sorted(output.rglob("*"))
        if path.is_file()
    ]
    write_json(
        output / "manifest.json",
        {"input_bindings": inputs.input_bindings, "managed_files": files, **summary},
    )
    return summary


def main() -> None:
    """Provide a restartable CLI with explicit roots and no embedded machine paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--review-status", type=Path, required=True)
    parser.add_argument("--claim-handoff", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        inputs = load_inputs(args.data_root, args.review_status, args.claim_handoff)
        export_cases(inputs, args.output)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Export failed: {error}\n")


if __name__ == "__main__":
    main()
