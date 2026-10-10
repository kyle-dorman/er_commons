"""Read-only projection of sealed 08E review authority into isolated 08F inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.pilot_citation_units import validate_units


def file_binding(path: Path) -> dict[str, str]:
    """Bind exact file bytes without changing their historical representation."""
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_bound(reference: dict[str, Any]) -> Any:
    """Read JSON only when its saved byte digest still matches."""
    path = Path(reference["path"])
    if file_binding(path)["sha256"] != reference["sha256"]:
        raise ValueError(f"Changed upstream binding: {path}")
    return json.loads(path.read_bytes())


def verify_review_seal(result_path: Path) -> dict[str, Any]:
    """Verify the final review inventory and every declared dependency, without writes."""
    result = json.loads(result_path.read_bytes())
    if result.get("schema_version") != "task08e.consolidated_review_result.v1":
        raise ValueError("Expected consolidated 08E review result")
    handoff = read_bound(result["handoff"])
    completion = read_bound(result["completion"])
    validation = read_bound(result["validation"])
    audit = read_bound(result["independent_audit"])
    if validation["status"] != "passed" or audit["status"] != "passed":
        raise ValueError("Upstream validation or audit did not pass")
    root = Path(result["completion"]["path"]).parent.resolve()
    paths = [Path(row["path"]).resolve() for row in completion["files"]]
    if len(paths) != len(set(paths)) or any(not p.is_relative_to(root) for p in paths):
        raise ValueError("Duplicate or escaping completion paths")
    actual = {p.resolve() for p in root.rglob("*") if p.is_file()}
    if actual != {*paths, Path(result["completion"]["path"]).resolve()}:
        raise ValueError("Review completion file closure changed")
    dependencies = read_bound(validation["dependencies"])
    for ref in completion["files"] + dependencies:
        if file_binding(Path(ref["path"]))["sha256"] != ref["sha256"]:
            raise ValueError(f"Changed inventory/dependency: {ref['path']}")
    rows = handoff["cases"]
    ids = [row["case_id"] for row in rows]
    eligible = [row for row in rows if row["eligibility"]["eligible"] is True]
    if len(ids) != len(set(ids)) or len(rows) != result["cases"]:
        raise ValueError("Case inventory differs")
    if len(eligible) != result["approved_eligible"]:
        raise ValueError("Eligibility accounting differs")
    return {
        "result": result,
        "handoff": handoff,
        "source_bindings": [
            file_binding(result_path),
            result["completion"],
            result["independent_audit"],
            *completion["files"],
            *dependencies,
        ],
        "validation": {
            "status": "passed",
            "completion_files": len(paths),
            "dependencies": len(dependencies),
            "exact_file_closure": True,
        },
    }


def _original_scope(
    case: dict[str, Any], checkpoint: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """Use final accepted relationships, never all citations of an accepted finding."""
    state = checkpoint["state"]
    accepted = {key: row for key, row in state["decisions"].items() if row["decision"] == "accept"}
    relationships: list[dict[str, Any]] = []
    scopes: list[Any] = []
    for decision in accepted.values():
        scope = decision.get("decision_scope", {})
        if scope not in scopes:
            scopes.append(scope)
        if isinstance(scope, dict):
            for row in scope.get("accepted_relationships", []):
                if row["finding_id"] in accepted and row not in relationships:
                    relationships.append(row)
    displays = [
        event["chat_text"]
        for event in checkpoint["journal"]["events"]
        if event["kind"] == "display" and event.get("chat_text")
    ]
    # C002's closeout predates relationship-index scopes. Its explicit narrowed
    # accepted findings and historical displays supply this one bounded adapter.
    if case["case_id"] == "C002" and not relationships:
        findings = state["packet"]["claim_findings"] + state["packet"]["beyond_claim_findings"]
        for finding in findings:
            if finding["finding_id"] not in accepted:
                continue
            for index, citation in enumerate(finding["citations"]):
                # This occurrence is attached to an accepted finding but was not
                # displayed; the explicit closeout excludes hidden extra material.
                if citation["occurrence_id"] == "C002-S011":
                    continue
                relationships.append(
                    {
                        "finding_id": finding["finding_id"],
                        "citation_index": index,
                        "occurrence_id": citation["occurrence_id"],
                        "metric_role": "required_support",
                        "scope": "Only displayed qualified propositions; no full-claim acceptance.",
                    }
                )
        scopes.append(
            {
                "adapter": "C002 explicit narrowed closeout; undisplayed S011 excluded",
                "exclusions": (
                    "Figures, Bay Trail, universal barrier coverage, exact residential "
                    "distance, and no-vegetation-benefit inference excluded."
                ),
            }
        )
    if not relationships or not displays:
        raise ValueError(
            f"Missing explicit relationship scope or readable framing: {case['case_id']}"
        )
    return relationships, displays, {"final_decision_scopes": scopes}


def _compact_anchors(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group span locators by canonical record without repeating table snapshots."""
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for anchor in anchors:
        key = (anchor.get("path", ""), anchor["record_id"])
        if key not in records:
            records[key] = {"path": key[0], "record_id": key[1], "locators": []}
        locator = {
            field: anchor[field] for field in ("text_field", "start", "end") if field in anchor
        }
        if locator not in records[key]["locators"]:
            records[key]["locators"].append(locator)
    return list(records.values())


def normalize_case(case: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Project only scoped sources, preserving amendments and latest human roles."""
    checkpoint = read_bound(case["base_review"])
    packet = checkpoint["state"]["packet"]
    bindings = [case["base_review"]]
    if case["review_mode"] == "approved_display_scope_overlay":
        for key in ("approval_scope_binding", "approved_proposal_binding", "revised_checkpoint"):
            read_bound(case[key])
            bindings.append(case[key])
        roles = case["citation_roles"]
        relationships = [
            {"occurrence_id": occurrence, "metric_role": role}
            for role, occurrences in roles.items()
            if isinstance(occurrences, list) and role != "preserved_background"
            for occurrence in occurrences
        ]
        sources = case["approved_occurrence_sources"]
        framing = [case["exact_approved_display"]]
        scope = case["approval_scope"]
    else:
        relationships, framing, scope = _original_scope(case, checkpoint)
        if case["case_id"] == "C002":
            ref_paths = {
                decision["closeout_scope_ref"]
                for decision in checkpoint["state"]["decisions"].values()
                if "closeout_scope_ref" in decision
            }
            if len(ref_paths) != 1:
                raise ValueError("C002 needs its exact closeout scope")
            scope_path = Path(next(iter(ref_paths)))
            closeout = json.loads(scope_path.read_bytes())
            matching = [
                event.get("reconciled_prior_displays")
                for event in checkpoint["journal"]["events"]
                if event["kind"] == "display"
            ]
            if closeout not in matching:
                raise ValueError("C002 closeout scope differs from bound journal")
            scope["explicit_closeout"] = closeout
            bindings.append(file_binding(scope_path))
        sources = packet["sources"]
    source_index = {source["occurrence_id"]: source for source in sources}
    wanted = list(dict.fromkeys(row["occurrence_id"] for row in relationships))
    if any(not identity.startswith(case["case_id"] + "-") for identity in wanted):
        raise ValueError("Cross-case occurrence identity")
    selected = [source_index[identity] for identity in wanted]
    # Unit checks may reference separately cited units: validate the preserved
    # packet as verification context, but expose only selected sources as evidence.
    verification_sources = {row["occurrence_id"]: row for row in packet["sources"]}
    verification_sources.update(source_index)
    validate_units(list(verification_sources.values()), data_root)
    findings = {
        row["finding_id"]: row for row in packet["claim_findings"] + packet["beyond_claim_findings"]
    }
    for relationship in relationships:
        if "finding_id" in relationship:
            finding = findings[relationship["finding_id"]]
            cited = finding["citations"][relationship["citation_index"]]
            if cited["occurrence_id"] != relationship["occurrence_id"]:
                raise ValueError("Approved relationship citation index differs")
            relationship["reviewed_excerpt"] = cited.get("excerpt")
            relationship["support_limit"] = cited.get("reason")
            relationship["finding_gaps"] = finding.get("remaining_gaps", [])
            relationship["finding_limitations"] = finding.get("limitations", [])
    citations = []
    for source in selected:
        occurrence = source["occurrence_id"]
        occurrence_roles = [
            row["metric_role"] for row in relationships if row["occurrence_id"] == occurrence
        ]
        required = any(role.startswith("required") for role in occurrence_roles)
        unit = source["citation_unit"]
        citation = {
            key: value
            for key, value in source.items()
            if key not in ("anchors", "citation_unit", "quote", "printed_label_proof")
        }
        citation.update(
            {
                "role": "required" if required else "optional_context",
                "approved_roles": occurrence_roles,
                "canonical_target": {
                    "document_id": source["extraction_id"] + "/document/" + source["source_id"],
                    "edition": source["edition"],
                    "unit_id": unit.get("table_id") or unit["section_id"],
                    "unit_type": "table" if unit.get("table_id") else "section",
                    "pages": source["physical_pages"],
                    **{
                        key: value
                        for key, value in unit.items()
                        if key
                        not in (
                            "section_record",
                            "source_binding",
                            "heading_anchor",
                            "next_heading_anchor",
                        )
                    },
                },
                "excerpt": "\n\n".join(
                    dict.fromkeys(
                        row["reviewed_excerpt"]
                        for row in relationships
                        if row["occurrence_id"] == occurrence and row.get("reviewed_excerpt")
                    )
                )
                or source["quote"],
                "full_source_text": source["quote"],
                "tables": list(
                    {
                        anchor["record_id"]: {
                            key: value
                            for key, value in anchor["record"].items()
                            if key
                            in (
                                "id",
                                "cells",
                                "shape",
                                "caption_block_ids",
                                "regions",
                                "num_rows",
                                "num_cols",
                                "row_count",
                                "column_count",
                                "caption",
                                "table_family_id",
                                "continuation_of",
                            )
                        }
                        for anchor in source["anchors"]
                        if "/table/" in anchor["record_id"]
                    }.values()
                ),
                "anchors": _compact_anchors(source["anchors"]),
                "full_source_ref": {
                    "path": case.get("revised_checkpoint", case["base_review"])["path"],
                    "binding": case.get("revised_checkpoint", case["base_review"]),
                    "occurrence_id": occurrence,
                    "note": (
                        "Exact original source including canonical records retained in "
                        "upstream packet and consolidated overlay."
                    ),
                },
            }
        )
        citations.append(citation)
    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "approved_framing": framing,
        "authority_priority": (
            "Exact current question and final scope/role decisions override all earlier displays. "
            "Displays are framing history, not independent evidence; do not reproduce superseded "
            "or unsupported claims. New answer approvals remain blank."
        ),
        "exact_display_amendments": case.get("exact_display_amendments", {}),
        "scope": scope,
        "citation_role_resolutions": case.get("citation_role_resolutions", []),
        "approved_relationships": relationships,
        "citations": citations,
        "eligibility_provenance": case["eligibility"],
        "source_bindings": bindings,
        "limitations": packet.get("limitations", []),
        "remaining_gaps": packet.get("remaining_gaps", []),
        "historical_reconciliation": {
            "binding": case["base_review"],
            "json_pointer": "/state/packet/frozen_input/historical_reconciliation",
            "scope": "Historical holds remain preserved; no old approval is imported.",
        },
        "inherited_limitations": {
            "binding": case["base_review"],
            "json_pointer": "/state/packet/frozen_input/inherited_limitations",
            "scope": "Source-edition and text-only restrictions remain in each cited source.",
        },
        "source_validation": {
            "status": "passed",
            "validator": "pilot_citation_units.validate_units",
            "checked_source_count": len(verification_sources),
            "approved_source_count": len(citations),
        },
        "answer_approval": None,
        "final_disposition": None,
    }


def load_batch_intake(result_path: Path, data_root: Path) -> dict[str, Any]:
    """Verify and normalize eligible cases in saved order; author no new content."""
    seal = verify_review_seal(result_path)
    cases = []
    for row in seal["handoff"]["cases"]:
        case = read_bound(row["review"])
        if any(
            case[key] != row[key] for key in ("case_id", "question", "eligibility", "disposition")
        ):
            raise ValueError("Handoff and case authority differ")
        if row["eligibility"]["eligible"] is True:
            normalized = normalize_case(case, data_root)
            normalized["source_bindings"].append(row["review"])
            cases.append(normalized)
    return {
        "schema_version": "task08f.batch_intake.v1",
        "cases": cases,
        "source_bindings": seal["source_bindings"],
        "validation": seal["validation"],
        "upstream_dispositions": seal["handoff"]["cases"],
        "deferred_case_ids": seal["result"]["deferred_case_ids"],
        "skipped_case_ids": seal["result"]["skipped_case_ids"],
    }
