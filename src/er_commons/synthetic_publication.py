"""Task 09A framework-independent publication and untouched final-check reservation."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    file_reference,
    jsonl_bytes,
    publish_bytes_no_clobber,
    sha256_file,
    stable_json_sha256,
)
from er_commons.synthetic_batch import history, lock, read, save, verify_inputs
from er_commons.synthetic_records import CATEGORIES, materialize_records


def reserve(expectations: list[dict[str, Any]], *, seed: str) -> dict[str, Any]:
    """Hold out roughly one fifth per category, stratified by proposed G/A pair."""
    ids = [row["variant_id"] for row in expectations]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate expectation identities")
    eligible = [
        row
        for row in expectations
        if row["verification_status"] == "model_verified"
        and row.get("comparison_eligible", row.get("agreement_eligible", True))
        and not row.get("duplicate", False)
    ]
    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        if not row.get("judge_exposed", False):
            categories[row["perturbation_id"]].append(row)
    selected: list[str] = []
    for _category, rows in sorted(categories.items()):
        strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            pair = f"{row['grounding']['score']}/{row['adequacy']['score']}"
            strata[pair].append(row)
        ordered = []
        for _, group in sorted(strata.items()):
            group.sort(key=lambda r: stable_json_sha256([seed, r["variant_id"]]))
            ordered.append(group)
        # Round-robin strata preserves rare score behavior where the small budget permits.
        interleaved = [
            row
            for index in range(max(map(len, ordered)))
            for group in ordered
            if index < len(group)
            for row in [group[index]]
        ]
        count = max(1, (len(rows) + 4) // 5)
        selected.extend(r["variant_id"] for r in interleaved[:count])
    return {
        "seed": seed,
        "method": "per-category ceil(20%), round-robin G/A strata; hash order within strata",
        "final_check_variant_ids": sorted(selected),
        "development_variant_ids": sorted(
            r["variant_id"] for r in eligible if r["variant_id"] not in selected
        ),
        "excluded_variant_ids": sorted(
            row["variant_id"] for row in expectations if row not in eligible
        ),
        "judge_exposures_before_reservation": sum(
            bool(r.get("judge_exposed")) for r in expectations
        ),
        "boundary": (
            "Within-development synthetic variants, not a new benchmark split "
            "or independent-question estimate"
        ),
    }


def reference_control(packet: dict[str, Any]) -> dict[str, Any]:
    """Preserve every projected reference independently of model execution success."""

    def digest(value: Any) -> str:
        """Match the synthetic record identity serialization exactly."""
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    return {
        "case_id": packet["case_id"],
        "parent_reference_hash": digest(packet["reference_answer"]),
        "source_packet_hash": packet.get("source_packet_sha256", digest(packet)),
        "release_id": packet.get("release_id"),
        "reference_version": packet.get("reference_version"),
        "reference_binding": packet.get("reference_binding"),
        "provenance": {
            "model": None,
            "invocation": None,
            "origin": "unchanged prepared reference; not model generated",
        },
        "variant_id": f"{packet['case_id']}-CONTROL",
        "answer": packet["reference_answer"],
    }


def review_exclusions(review: dict[str, Any]) -> dict[tuple[str, int], str]:
    """Validate source-bound uncertainty exclusions without changing proposed scores."""
    rows = review.get("exclusions", [])
    if not isinstance(rows, list):
        raise ValueError("Review exclusions must be a list")
    result: dict[tuple[str, int], str] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("case_id"), str)
            or type(row.get("variant_index")) is not int
            or row["variant_index"] < 0
            or not isinstance(row.get("reason"), str)
            or not row["reason"].strip()
        ):
            raise ValueError("Review exclusion needs case_id, nonnegative index and reason")
        key = (row["case_id"], row["variant_index"])
        if key in result:
            raise ValueError("Duplicate review exclusion")
        result[key] = row["reason"]
    return result


def inherited_partition(
    root: Path,
    expectations: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    regeneration: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Map only authorized development slots; retain reserved identities externally."""
    for key in (
        "development_slot_ids",
        "preserved_final_check_variant_ids",
        "preserved_excluded_variant_ids",
    ):
        if len(regeneration[key]) != len(set(regeneration[key])):
            raise ValueError("Duplicate inherited partition identities")
    allowed = set(regeneration["development_slot_ids"])
    reserved = set(regeneration["preserved_final_check_variant_ids"])
    prior_excluded = set(regeneration["preserved_excluded_variant_ids"])
    if allowed & (reserved | prior_excluded) or reserved & prior_excluded:
        raise ValueError("Inherited partition identities overlap")
    if any(r["variant_id"] in allowed | reserved | prior_excluded for r in expectations):
        raise ValueError("Fresh variant reuses predecessor identity")
    by_slot = {}
    for row in expectations:
        slot = row["predecessor_development_variant_id"]
        if slot not in allowed or slot in by_slot:
            raise ValueError("Absent or duplicate predecessor development slot")
        by_slot[slot] = row
    slots = []
    for row in coverage:
        packet = read(root / "cases" / row["case_id"] / "input.json")
        slot = packet["regeneration_slots"][row["perturbation_id"]]
        if slot not in allowed:
            raise ValueError("Coverage escapes development slots")
        expectation = by_slot.get(slot)
        if expectation and (
            expectation["case_id"] != row["case_id"]
            or expectation["perturbation_id"] != row["perturbation_id"]
        ):
            raise ValueError("Expectation does not match covered case/category")
        slots.append(
            {
                "predecessor_development_variant_id": slot,
                "case_id": row["case_id"],
                "perturbation_id": row["perturbation_id"],
                "variant_id": expectation["variant_id"] if expectation else None,
                "disposition": row["disposition"],
                "reason": row["reason"],
            }
        )
    identifiers = [r["predecessor_development_variant_id"] for r in slots]
    if not set(by_slot) <= set(identifiers):
        raise ValueError("Expectation lacks coverage accounting")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate slot accounting")
    if not read(root / "config.json")["smoke"] and set(identifiers) != allowed:
        raise ValueError("Incomplete inherited development slot accounting")
    return {
        "method": "Inherited development-only regeneration; no new reservation",
        "predecessor_reservation": regeneration["predecessor_reservation"],
        "final_check_variant_ids": [],
        "preserved_external_final_check_variant_ids": sorted(reserved),
        "preserved_external_excluded_variant_ids": sorted(prior_excluded),
        "development_variant_ids": sorted(
            r["variant_id"] for r in expectations if r["comparison_eligible"]
        ),
        "excluded_variant_ids": sorted(
            r["variant_id"] for r in expectations if not r["comparison_eligible"]
        ),
        "judge_exposures_before_reservation": 0,
        "boundary": "Prior reserved/test payloads untouched; fresh IDs remain development only",
    }, slots


def publish(root: Path, review: Path) -> dict[str, Any]:
    """Publish all case/category dispositions, preserving failed units without claiming coverage."""
    with lock(root):
        prepared = verify_inputs(root)
        intake = read(root / "intake.json")
        regeneration = intake.get("regeneration")
        review_record = read(review)
        if review_record.get("status") != "passed":
            raise ValueError("Independent review must pass before publication")
        if review_record.get("configuration_id") != prepared["configuration_id"]:
            raise ValueError("Independent review configuration does not match")
        reviewed = review_record.get("reviewed_outputs")
        if not isinstance(reviewed, list):
            raise ValueError("Independent review must bind reviewed_outputs")
        exclusions = review_exclusions(review_record)
        applied_exclusions: set[tuple[str, int]] = set()
        actual_outputs = []
        answers: list[dict[str, Any]] = []
        expectations: list[dict[str, Any]] = []
        edits: list[dict[str, Any]] = []
        controls: list[dict[str, Any]] = []
        coverage: list[dict[str, Any]] = []
        discoveries: list[dict[str, Any]] = []
        cases = []
        for case_id in prepared["case_ids"]:
            directory = root / "cases" / case_id
            packet = read(directory / "input.json")
            controls.append(reference_control(packet))
            rows = history(directory)
            if not rows:
                raise ValueError(f"Unattempted case: {case_id}")
            attempt, terminal = rows[-1]
            if terminal["status"] != "validated":
                cases.append(
                    {
                        "case_id": case_id,
                        "status": "failed",
                        "variant_count": 0,
                        "reason": terminal["reason"],
                    }
                )
                coverage.extend(
                    {
                        "case_id": case_id,
                        "perturbation_id": category,
                        "disposition": "failed",
                        "reason": terminal["reason"],
                    }
                    for category in packet["requested_categories"]
                )
                continue
            actual_outputs.append(file_reference(attempt / "raw_output.json", root=root))
            provenance = {
                "invocation": file_reference(attempt / "invocation.json", root=root),
                "raw_output": file_reference(attempt / "raw_output.json", root=root),
                "terminal": file_reference(attempt / "result.json", root=root),
                "model": read(attempt / "invocation.json")["requested_model"],
                "backend_model": read(attempt / "invocation.json")["backend_model"],
            }
            material = materialize_records(read(attempt / "raw_output.json"), packet, provenance)
            duplicate_indices = {
                d["variant_index"]
                for d in material["validation"]["diagnostics"]
                if "duplicate_of" in d or d.get("duplicate_of_control", False)
            }
            for index, expectation in enumerate(material["expectations"]):
                expectation["duplicate"] = index in duplicate_indices
                expectation["comparison_eligible"] = (
                    expectation["verification_status"] == "model_verified"
                    and index not in duplicate_indices
                )
                if (case_id, index) in exclusions:
                    expectation["review_exclusion_reason"] = exclusions[(case_id, index)]
                    expectation["comparison_eligible"] = False
                    applied_exclusions.add((case_id, index))
            answers.extend(material["answers"])
            expectations.extend(material["expectations"])
            edits.extend(material["edits"])
            for row in material["coverage"]:
                category_expectations = [
                    e
                    for e in material["expectations"]
                    if e["perturbation_id"] == row["perturbation_id"]
                ]
                eligible_count = sum(e["comparison_eligible"] for e in category_expectations)
                reported = {
                    "case_id": case_id,
                    **row,
                    "model_disposition": row["disposition"],
                    "generated_variant_count": len(category_expectations),
                    "comparison_eligible_variant_count": eligible_count,
                    "review_exclusions": [
                        e["review_exclusion_reason"]
                        for e in category_expectations
                        if "review_exclusion_reason" in e
                    ],
                }
                if category_expectations and not eligible_count:
                    reported["disposition"] = "ambiguous"
                    reported["reason"] = (
                        "Generated records retained, but no unambiguous nonduplicate "
                        "variant remains eligible after validation and independent review. "
                        "Model disposition reason: " + row["reason"]
                    )
                coverage.append(reported)
            discoveries.append({"case_id": case_id, **material["discovery"]})
            cases.append(
                {
                    "case_id": case_id,
                    "status": "validated",
                    "variant_count": len(material["answers"]),
                    "ambiguous": sum(
                        r["verification_status"] != "model_verified"
                        for r in material["expectations"]
                    ),
                    "duplicates": len(duplicate_indices),
                    "validation": material["validation"],
                }
            )
        if sorted(reviewed, key=lambda r: r["path"]) != sorted(
            actual_outputs, key=lambda r: r["path"]
        ):
            raise ValueError("Independent review raw-output identities do not match")
        if applied_exclusions != set(exclusions):
            raise ValueError("Review exclusion refers to an absent validated variant")
        ids = [a["variant_id"] for a in answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate variant identities")
        expected_coverage = (
            len(regeneration["development_slot_ids"]) if regeneration else 19 * len(CATEGORIES)
        )
        if not read(root / "config.json")["smoke"] and len(coverage) != expected_coverage:
            raise ValueError("Full publication needs exactly 19-case catalog accounting")
        if regeneration:
            reservation, slot_rows = inherited_partition(root, expectations, coverage, regeneration)
        else:
            reservation = reserve(expectations, seed=read(root / "config.json")["reservation_seed"])
        for name, records in (
            ("answers", answers),
            ("expectations", expectations),
            ("edits", edits),
            ("controls", controls),
            ("coverage", coverage),
            ("discovery", discoveries),
        ):
            publish_bytes_no_clobber(root / "published" / f"{name}.jsonl", jsonl_bytes(records))
        save(
            root / "published" / "exact_reference_controls.json",
            read(root / "intake.json")["restricted_controls"],
        )
        if regeneration:
            publish_bytes_no_clobber(
                root / "published" / "development_slots.jsonl", jsonl_bytes(slot_rows)
            )
        save(root / "published" / "reservation.json", reservation)
        publish_bytes_no_clobber(
            root / "published" / "independent_review.json", review.read_bytes()
        )
        summary = {
            "schema_version": "task09a.publication.v1",
            "status": "complete_with_limitations",
            "cases": cases,
            "case_count": len(cases),
            "variant_count": len(answers),
            "control_count": len(controls),
            "coverage_rows": len(coverage),
            "failed_cases": [c["case_id"] for c in cases if c["status"] != "validated"],
            "unresolved_variants": sum(
                r["verification_status"] != "model_verified" for r in expectations
            ),
            "duplicate_variants": sum(r["duplicate"] for r in expectations),
            "reviewed_uncertain_variants": len(applied_exclusions),
            "comparison_eligible_variants": sum(r["comparison_eligible"] for r in expectations),
            "reserved_final_checks": len(reservation["final_check_variant_ids"]),
            "coverage_dispositions": dict(Counter(r["disposition"] for r in coverage)),
            "coverage_by_category": {
                category: dict(
                    Counter(r["disposition"] for r in coverage if r["perturbation_id"] == category)
                )
                for category in CATEGORIES
            },
            "proposed_score_pairs": dict(
                Counter(f"{r['grounding']['score']}/{r['adequacy']['score']}" for r in expectations)
            ),
            "limitations": [
                (
                    "Uncalibrated synthetic model proposals; no human score validation "
                    "or judge reliability claim."
                ),
                "Literal locator validation establishes resolution, not semantic correctness.",
                "Backend model may not be independently reported; exact CLI invocation retained.",
                *read(root / "intake.json")["limitations"],
            ],
            "judge_runs": 0,
            "target_runs": 0,
            "test_evaluations": 0,
        }
        if regeneration:
            summary["annotation_version"] = intake["annotation_version"]
            summary["preserved_external_final_checks"] = len(
                regeneration["preserved_final_check_variant_ids"]
            )
            summary["requested_development_slots"] = expected_coverage
            summary["point_expectation_count"] = sum(
                len(e["grounding"]["point_expectations"]) for e in expectations
            )
            summary["not_supported_counts"] = dict(
                Counter(str(e["grounding"]["not_supported"]) for e in expectations)
            )
            summary["limitations"].append(
                "Fresh development-only generation; prior reserved payloads were not read "
                "or regenerated, and no new final-check split was created."
            )
        publish_bytes_no_clobber(
            root / "published" / "publication_source.py", Path(__file__).read_bytes()
        )
        save(root / "published" / "summary.json", summary)
        save(
            root / "completion.json",
            {
                "schema_version": "task09a.completion.v1",
                "inventory": artifact_inventory(root, {"completion.json"}),
            },
        )
    verify(root)
    return summary


def verify(root: Path) -> dict[str, Any]:
    """Verify published closure, prepared identities and every immutable case attempt."""
    if read(root / "completion.json")["inventory"] != artifact_inventory(root, {"completion.json"}):
        raise ValueError("Published inventory changed")
    prepared = verify_inputs(root, check_code=False)
    for case_id in prepared["case_ids"]:
        history(root / "cases" / case_id)
    return {"valid": True, "completion_sha256": sha256_file(root / "completion.json")}


def main() -> None:
    """Publish only after an explicit saved independent review, or verify a seal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["publish", "verify"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "publish":
        if args.review is None:
            parser.error("publish requires --review")
        result = publish(args.root, args.review)
    else:
        result = verify(args.root)
    logging.info("%s", json.dumps(result))


if __name__ == "__main__":
    main()
