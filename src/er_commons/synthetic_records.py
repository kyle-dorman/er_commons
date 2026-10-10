"""Task 09A structural checks and deterministic records, never semantic approval."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

SPEC_ROOT = Path(__file__).resolve().parents[2] / "docs" / "specs"
CATEGORIES = tuple(
    [f"P{i:02d}" for i in range(1, 10)]
    + [f"O{i:02d}" for i in range(1, 5)]
    + [f"F{i:02d}" for i in range(1, 11)]
    + [f"C{i:02d}" for i in range(1, 6)]
    + [f"R{i:02d}" for i in range(1, 4)]
)


def output_schema() -> dict[str, Any]:
    """Read the tracked strict structured-output schema."""
    return json.loads((SPEC_ROOT / "task09a_output.schema.json").read_text())  # type: ignore[no-any-return]


def _digest(value: Any) -> str:
    """Hash canonical serialized content for stable record identities."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def make_edits(parent: dict[str, Any], answer: dict[str, Any]) -> list[dict[str, Any]]:
    """Record exact top-level field replacements, preserving all removed metadata."""
    edits = []
    for key in sorted(parent.keys() | answer.keys()):
        if key not in parent or key not in answer or parent[key] != answer[key]:
            edits.append(
                {
                    "path": f"/{key}",
                    "before_present": key in parent,
                    "after_present": key in answer,
                    "before": parent.get(key),
                    "after": answer.get(key),
                }
            )
    return edits


def apply_edits(parent: dict[str, Any], edits: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct a variant, rejecting edits bound to a different parent."""
    answer = copy.deepcopy(parent)
    for edit in edits:
        key = edit["path"].removeprefix("/")
        if (key in answer) != edit["before_present"] or answer.get(key) != edit["before"]:
            raise ValueError(f"Edit precondition mismatch: {key}")
        if edit["after_present"]:
            answer[key] = copy.deepcopy(edit["after"])
        else:
            answer.pop(key)
    return answer


def _points(answer: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect all cited answer units without assigning semantic roles."""
    return [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]


def validate_proposal(proposal: Any, packet: dict[str, Any]) -> dict[str, Any]:
    """Validate identities, accounting, edit reconstruction and literal evidence."""
    errors = [
        f"{list(e.absolute_path)}: {e.message}"
        for e in Draft202012Validator(output_schema()).iter_errors(proposal)
    ]
    diagnostics: list[dict[str, Any]] = []
    if errors:
        return {"valid": False, "errors": errors, "diagnostics": diagnostics}
    if proposal["case_id"] != packet["case_id"]:
        errors.append("case_id differs from dev packet")
    requested = set(packet.get("requested_categories", CATEGORIES))
    coverage = proposal["coverage"]
    if len(coverage) != len(requested) or {c["perturbation_id"] for c in coverage} != requested:
        errors.append("coverage must account exactly once for each requested category")
    sources = {s["occurrence_id"]: s for s in packet["sources"]}
    for candidate in proposal["discovery"]["candidates"]:
        if candidate["citation_id"] not in sources:
            errors.append("discovery candidate does not resolve to allowed packet source")
    supplemental_used = bool(packet.get("supplemental_discovery_provenance"))
    if proposal["discovery"]["supplemental_pass_used"] != supplemental_used:
        errors.append("supplemental discovery claim differs from packet provenance")
    parent = packet["reference_answer"]
    parent_ids = {p["point_id"] for p in _points(parent)}
    fingerprints: dict[str, int] = {}
    counts: dict[str, int] = {}
    for index, variant in enumerate(proposal["variants"]):
        prefix = f"variant[{index}]"
        category = variant["perturbation_id"]
        counts[category] = counts.get(category, 0) + 1
        if category not in requested:
            errors.append(f"{prefix}: category not requested")
        answer = variant["answer"]
        points = _points(answer)
        ids = [p["point_id"] for p in points]
        if len(ids) != len(set(ids)) or any(not i.strip() for i in ids):
            errors.append(f"{prefix}: point IDs must be unique and nonempty")
        if any(not p["text"].strip() for p in points):
            errors.append(f"{prefix}: answer units require readable nonempty text")
        attachable = {
            answer["conclusion"]["point_id"],
            *(p["point_id"] for p in answer["supporting_points"]),
        }
        for q in answer["qualifications"]:
            if not q["applies_to"] or not set(q["applies_to"]) <= attachable:
                errors.append(f"{prefix}: dangling qualification attachment")
        actual_invalid = {c for p in points for c in p["citation_ids"] if c not in sources}
        if actual_invalid != set(variant["expected_invalid_citation_ids"]):
            errors.append(f"{prefix}: undeclared or absent expected citation defect")
        if actual_invalid:
            diagnostics.append(
                {"variant_index": index, "expected_invalid_citations": sorted(actual_invalid)}
            )
        for mapping in variant["point_mapping"]:
            if not set(mapping["parent_point_ids"]) <= parent_ids:
                errors.append(f"{prefix}: mapping references absent parent point")
            if not set(mapping["variant_point_ids"]) <= set(ids):
                errors.append(f"{prefix}: mapping references absent variant point")
        if category in {"P03", "P04"}:
            split = category == "P04"
            reorganized = [
                m
                for m in variant["point_mapping"]
                if (
                    (len(m["parent_point_ids"]) == 1 and len(m["variant_point_ids"]) > 1)
                    if split
                    else (len(m["parent_point_ids"]) > 1 and len(m["variant_point_ids"]) == 1)
                )
            ]
            if not reorganized:
                errors.append(f"{prefix}: split/combine requires explicit mapping")
            if any(set(m["variant_point_ids"]) & parent_ids for m in reorganized):
                errors.append(f"{prefix}: split/combined points require new IDs")
        expectation = variant["expectation"]
        clean = (
            category == "R01"
            and answer["status"] == "abstained"
            and not answer["supporting_points"]
            and not answer["qualifications"]
            and not answer["optional_context"]
            and not answer["conclusion"]["citation_ids"]
        )
        if category == "R01" and expectation["verification_status"] == "model_verified":
            if (
                not clean
                or expectation["grounding"]["score"] is not None
                or expectation["adequacy"]["score"] != 0
            ):
                errors.append(f"{prefix}: verified clean abstention requires G null and A 0")
        for dimension in ("grounding", "adequacy"):
            value = expectation[dimension]
            if not value["rationale"].strip():
                errors.append(f"{prefix}: missing {dimension} rationale")
            if expectation["verification_status"] == "model_verified":
                if value["score"] is None and not (dimension == "grounding" and clean):
                    errors.append(f"{prefix}: verified expectation has unresolved score")
                if not value["evidence"] and not clean:
                    errors.append(f"{prefix}: verified expectation lacks {dimension} evidence")
            for evidence in value["evidence"]:
                source = sources.get(evidence["citation_id"])
                if source is None:
                    errors.append(f"{prefix}: rationale evidence ID does not resolve")
                    continue
                if evidence["locator"] != source["canonical_target"]["unit_id"]:
                    errors.append(f"{prefix}: rationale locator mismatch")
                if (
                    not evidence["excerpt"].strip()
                    or evidence["excerpt"] not in source["full_source_text"]
                ):
                    errors.append(f"{prefix}: rationale excerpt not an exact source substring")
        if (
            expectation["verification_status"] == "unresolved"
            and not expectation["ambiguity"].strip()
        ):
            errors.append(f"{prefix}: unresolved expectation needs ambiguity explanation")
        if expectation["verification_status"] == "unresolved" and all(
            expectation[d]["score"] is not None for d in ("grounding", "adequacy")
        ):
            errors.append(f"{prefix}: unresolved expectation must leave uncertain score null")
        edits = make_edits(parent, answer)
        if apply_edits(parent, edits) != answer:
            errors.append(f"{prefix}: edit reconstruction failed")
        fingerprint = _digest(answer)
        if fingerprint == _digest({k: v for k, v in parent.items() if k != "citation_locators"}):
            diagnostics.append({"variant_index": index, "duplicate_of_control": True})
        if fingerprint in fingerprints:
            diagnostics.append({"variant_index": index, "duplicate_of": fingerprints[fingerprint]})
        fingerprints[fingerprint] = index
    for c in coverage:
        count = counts.get(c["perturbation_id"], 0)
        if c["disposition"] == "generated" and not count:
            errors.append(f"{c['perturbation_id']}: generated without variant")
        if c["disposition"] not in {"generated", "ambiguous"} and count:
            errors.append(f"{c['perturbation_id']}: variants contradict disposition")
        if count > 2:
            errors.append(f"{c['perturbation_id']}: more than two initial variants")
        if not c["reason"].strip():
            errors.append(f"{c['perturbation_id']}: disposition needs reason")
    return {
        "valid": not errors,
        "errors": errors,
        "diagnostics": diagnostics,
        "semantic_support_verified": False,
        "human_approval": False,
    }


def materialize_records(
    proposal: dict[str, Any], packet: dict[str, Any], provenance: dict[str, Any]
) -> dict[str, Any]:
    """Separate judge-safe answers from author expectations and exact edit metadata."""
    report = validate_proposal(proposal, packet)
    if not report["valid"]:
        raise ValueError(f"Invalid synthetic proposal: {report['errors']}")
    parent = packet["reference_answer"]
    binding = {
        "case_id": packet["case_id"],
        "parent_reference_hash": _digest(parent),
        "source_packet_hash": packet.get("source_packet_sha256", _digest(packet)),
        "release_id": packet.get("release_id"),
        "reference_version": packet.get("reference_version"),
        "reference_binding": packet.get("reference_binding"),
        "provenance": provenance,
    }
    answers, expectations, edits = [], [], []
    for index, variant in enumerate(proposal["variants"]):
        variant_id = (
            f"{packet['case_id']}-{variant['perturbation_id']}-{index + 1:02d}"
            f"-{_digest(variant)[:12]}"
        )
        shared = {**binding, "variant_id": variant_id}
        answers.append({**shared, "answer": variant["answer"]})
        expectations.append(
            {
                **shared,
                "perturbation_id": variant["perturbation_id"],
                "severity": variant["severity"],
                "agreement_eligible": variant["expectation"]["verification_status"]
                == "model_verified",
                **variant["expectation"],
                "intended_effect": variant["intended_effect"],
                "secondary_effects": variant["secondary_effects"],
                "expected_invalid_citation_ids": variant["expected_invalid_citation_ids"],
            }
        )
        edits.append(
            {
                **shared,
                "operations": make_edits(parent, variant["answer"]),
                "point_mapping": variant["point_mapping"],
            }
        )
    return {
        "answers": answers,
        "expectations": expectations,
        "edits": edits,
        "coverage": proposal["coverage"],
        "discovery": proposal["discovery"],
        "control": {
            **binding,
            "variant_id": f"{packet['case_id']}-CONTROL",
            "answer": copy.deepcopy(parent),
        },
        "validation": report,
    }
