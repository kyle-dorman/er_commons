"""Deterministic curator obligations and sparse, explicit review decisions."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.release_storage import validate_owned_record

if TYPE_CHECKING:
    from er_commons.response_inventory.release_inputs import ReleaseInputs

type JsonObject = dict[str, Any]
type SelectionGroups = dict[tuple[str, str], list[str]]
QUESTION_VERSION = "task05h_composition_review.v1"
SELECTION_POLICY = "task05h_curator_selection.v1"
SCHEMA_VERSION = "er_commons.response_inventory_release.v1"


def _records(inputs: ReleaseInputs, kind: str, key: str) -> dict[str, JsonObject]:
    """Index one accepted record kind without transforming its payload."""
    return {row[key]: row for row in inputs.source_records if row.get("record_type") == kind}


def warning_profile(row: JsonObject) -> list[str]:
    """Extract coverage/status codes, never IDs, prose, dates or free-text warnings."""
    codes: set[str] = set()
    allowed = {
        "fresh_review_status",
        "condition",
        "status",
        "change_class",
        "target_kind",
        "coverage_kind",
        "coverage_basis",
        "text_only_model_eligibility",
    }

    def visit(value: Any) -> None:
        """Collect only the explicit categorical allowlist recursively."""
        if isinstance(value, dict):
            for key, child in value.items():
                if key in allowed and isinstance(child, (str, bool)):
                    codes.add(f"{key}:{child}")
                elif isinstance(child, (dict, list)) and key != "input_refs":
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(row)
    if row.get("final_f1_warning"):
        codes.add("final_f1_substitution")
        if row["final_f1_warning"].get("response_specific"):
            codes.add("final_f1_response_specific_revision")
    return sorted(codes)


def build_selection(inputs: ReleaseInputs) -> JsonObject:
    """Assemble review obligations from each accepted layer, then freeze their identity."""
    obligations: dict[str, JsonObject] = {}
    groups: SelectionGroups = defaultdict(list)
    _select_source_anchors(inputs, obligations, groups)
    _select_graph_relationships(inputs, obligations, groups)
    _select_official_references(inputs, obligations, groups)
    _select_source_exceptions(inputs, obligations)
    for entry in inputs.limitations.get("decision_provenance", []):
        groups[("inherited_provenance_display", entry["decision_origin"])].append(entry["entry_id"])
    # Sorting and the existing repr-based group keys preserve the frozen selection identity.
    strata = _select_stratum_representatives(groups, obligations)
    rows = []
    for subject_ref in sorted(obligations):
        row = obligations[subject_ref]
        row["reasons"] = sorted(set(row["reasons"]))
        row["stratum_ids"] = sorted(set(row["stratum_ids"]))
        rows.append(row)
    result = {
        "schema_version": SCHEMA_VERSION,
        "question_version": QUESTION_VERSION,
        "selection_policy": SELECTION_POLICY,
        "obligations": rows,
        "strata": strata,
        "input_semantic_digest": inputs.semantic_digest,
    }
    result["selection_digest"] = canonical_json_sha256(result)
    return result


def _add_obligation(
    obligations: dict[str, JsonObject],
    subject_ref: str,
    reason: str,
    *,
    members: list[str] | None = None,
    stratum: str | None = None,
) -> None:
    """Deduplicate a subject while retaining every independent obligation."""
    item = obligations.setdefault(
        subject_ref,
        {
            "subject_ref": subject_ref,
            "reasons": [],
            "stratum_ids": [],
            "member_refs": sorted(members or [subject_ref]),
            "coverage_basis": "new_rule" if members is not None else "new_individual",
        },
    )
    item["reasons"].append(reason)
    if stratum:
        item["stratum_ids"].append(stratum)


def _select_source_anchors(
    inputs: ReleaseInputs, obligations: dict[str, JsonObject], groups: SelectionGroups
) -> None:
    """Group source anchors and require every General Response and apparent orphan."""
    units = _records(inputs, "source_unit", "unit_id")
    spans = _records(inputs, "source_span", "span_id")
    connected = {
        edge[field] for edge in inputs.edges for field in ("source_unit_id", "target_unit_id")
    }
    incoming = {edge["target_unit_id"] for edge in inputs.edges}
    for unit_id, unit in units.items():
        pages = {
            fragment["page_id"]
            for span_id in unit["span_ids"]
            for fragment in spans[span_id]["fragments"]
        }
        key = [unit["unit_kind"], "single_page" if len(pages) == 1 else "cross_page"]
        groups[("source_anchor", repr(key))].append(unit_id)
        if unit["unit_kind"] == "general_response":
            _add_obligation(obligations, unit_id, "all_general_responses")
            if unit_id not in incoming:
                _add_obligation(obligations, unit_id, "general_response_zero_incoming")
        if unit_id not in connected:
            _add_obligation(obligations, unit_id, "apparent_orphan")


def _select_graph_relationships(
    inputs: ReleaseInputs, obligations: dict[str, JsonObject], groups: SelectionGroups
) -> None:
    """Sample accepted resolver rules and retain explicit graph exception classes."""
    census = inputs.limitations.get("graph_review_census", {})
    accepted_rules: dict[str, set[str]] = defaultdict(set)
    for kind in ("direct_pair_outcomes", "mention_outcomes", "membership_outcomes"):
        for result in census.get(kind, []):
            if result.get("edge_id") and result.get("outcome") == "resolved":
                accepted_rules[result["edge_id"]].add(result["rule"])
    for edge in inputs.edges:
        rules = {row["resolver_rule"] for row in edge.get("evidence_resolutions", [])}
        rules.update(accepted_rules[edge["edge_id"]])
        if not rules:
            raise ValueError(
                f"05H graph edge lacks accepted resolver-rule evidence: {edge['edge_id']}"
            )
        for rule in rules:
            groups[("graph", repr([edge["relation_type"], rule]))].append(edge["edge_id"])
    nonmatch_classes: dict[tuple[str, str], list[str]] = defaultdict(list)
    for kind in ("mention_outcomes", "membership_outcomes"):
        for result in census.get(kind, []):
            if result["outcome"] != "resolved":
                nonmatch_classes[(result["rule"], result["reason"])].append(result["input_id"])
    for diagnostic in inputs.graph_diagnostics:
        if diagnostic["code"] != "unsupported_reference_form":
            _add_obligation(
                obligations, diagnostic["diagnostic_id"], f"graph_exception:{diagnostic['code']}"
            )
    for (rule, reason), members in sorted(nonmatch_classes.items()):
        subject_ref = "graphclass05hv1-" + canonical_json_sha256([rule, reason, sorted(members)])
        _add_obligation(
            obligations, subject_ref, f"intra_volume_nonmatch:{reason}:{rule}", members=members
        )


def _select_official_references(
    inputs: ReleaseInputs, obligations: dict[str, JsonObject], groups: SelectionGroups
) -> None:
    """Keep nonlink classes separate and sample links by eligibility and warnings."""
    nonlinks: dict[tuple[str, str], list[str]] = defaultdict(list)
    for outcome in inputs.outcomes:
        subject_ref = outcome["mention_id"]
        if outcome["outcome"] != "resolved":
            nonlinks[(str(outcome["terminal_reason"]), str(outcome["resolver_rule"]))].append(
                subject_ref
            )
        else:
            annotations = outcome.get("target_annotations", [])
            key = [
                outcome["resolver_rule"],
                sorted({annotation["target_type"] for annotation in annotations}),
                sorted(
                    {
                        annotation.get("source_usability", {}).get("status", "unknown")
                        for annotation in annotations
                    }
                ),
                sorted(
                    {
                        str(annotation.get("text_only_model_eligibility"))
                        for annotation in annotations
                    }
                ),
                warning_profile(outcome),
            ]
            groups[("official_link", repr(key))].append(subject_ref)
        groups[("warning_coverage", repr(warning_profile(outcome)))].append(subject_ref)
        if outcome.get("final_f1_warning", {}) and outcome["final_f1_warning"].get(
            "response_specific"
        ):
            _add_obligation(obligations, subject_ref, "final_f1_response_specific_all_mentions")
    for (reason, rule), members in sorted(nonlinks.items()):
        subject_ref = "nonlinkclass05hv1-" + canonical_json_sha256([reason, rule, sorted(members)])
        _add_obligation(
            obligations, subject_ref, f"official_nonlink:{reason}:{rule}", members=members
        )


def _select_source_exceptions(inputs: ReleaseInputs, obligations: dict[str, JsonObject]) -> None:
    """Require source exceptions and each directly named source-unit anchor."""
    units = _records(inputs, "source_unit", "unit_id")
    for row in inputs.source_records:
        if row["record_type"] in {"source_placement_exception", "diagnostic"}:
            subject_ref = str(row.get("exception_id", row.get("diagnostic_id")))
            _add_obligation(obligations, subject_ref, "source_exception")
            for unit_id in row.get("subject_ids", []):
                if unit_id in units:
                    _add_obligation(obligations, unit_id, "source_exception_anchor")


def _select_stratum_representatives(
    groups: SelectionGroups, obligations: dict[str, JsonObject]
) -> list[JsonObject]:
    """Freeze first/last representatives; deduplicate subjects across independent strata."""
    strata: list[JsonObject] = []
    for (kind, group_key), members in sorted(groups.items()):
        members = sorted(set(members))
        stratum_id = "stratum05hv1-" + canonical_json_sha256([kind, group_key, members])
        selected = sorted({members[0], members[-1]})
        strata.append(
            {
                "stratum_id": stratum_id,
                "kind": kind,
                "key": group_key,
                "member_refs": members,
                "selected_refs": selected,
            }
        )
        for subject_ref in selected:
            _add_obligation(obligations, subject_ref, kind, stratum=stratum_id)
    return strata


def build_view_index(inputs: ReleaseInputs) -> list[JsonObject]:
    """Retain accepted comment ordering and add navigation for every remaining unit."""
    units = _records(inputs, "source_unit", "unit_id")
    spans = _records(inputs, "source_span", "span_id")
    pages = _records(inputs, "page", "page_id")

    def order(unit_id: str) -> tuple[int, int, str]:
        """Sort roots by physical source location, preserving accepted span order."""
        fragment = spans[units[unit_id]["span_ids"][0]]["fragments"][0]
        return (pages[fragment["page_id"]]["physical_page"], fragment["text_start"], unit_id)

    rows = [
        {
            "view_id": view["view_id"],
            "root_unit_id": view["root_unit_id"],
            "ordered_unit_ids": view["ordered_unit_ids"],
            "edge_ids": view["edge_ids"],
            "upstream_view_id": view["view_id"],
        }
        for view in inputs.graph_views
    ]
    covered = {unit_id for row in rows for unit_id in row["ordered_unit_ids"]}
    for unit_id in sorted(set(units) - covered):
        rows.append(
            {
                "view_id": "view05hv1-" + canonical_json_sha256(unit_id),
                "root_unit_id": unit_id,
                "ordered_unit_ids": [unit_id],
                "edge_ids": sorted(
                    edge["edge_id"]
                    for edge in inputs.edges
                    if unit_id in (edge["source_unit_id"], edge["target_unit_id"])
                ),
                "upstream_view_id": None,
            }
        )
    for row in rows:
        row["mention_ids"] = sorted(
            outcome["mention_id"]
            for outcome in inputs.outcomes
            if outcome["source_unit_id"] in row["ordered_unit_ids"]
        )
        row["target_ids"] = sorted(
            {
                annotation["target_id"]
                for outcome in inputs.outcomes
                if outcome["mention_id"] in row["mention_ids"]
                for annotation in outcome.get("target_annotations", [])
            }
        )
        row["source_order"] = list(order(row["root_unit_id"]))
    return sorted(rows, key=lambda row: row["source_order"])


def _check_decision(row: JsonObject, plan_id: str, subjects: set[str]) -> None:
    """Reject incomplete author attestations or unsupported correction authority."""
    required = {
        "decision_id",
        "schema_version",
        "plan_id",
        "subject_refs",
        "question_version",
        "coverage_basis",
        "disposition",
        "rationale",
        "evidence_refs",
        "reviewer",
        "reviewed_at",
        "supersedes",
        "action",
        "replacement_refs",
        "requires_owner_replay",
    }
    if set(row) != required or row["schema_version"] != SCHEMA_VERSION:
        raise ValueError("05H decision shape or schema differs")
    if not isinstance(row["decision_id"], str) or not row["decision_id"].strip():
        raise ValueError("05H decision ID must be a nonempty string")
    validate_owned_record(row)
    if row["plan_id"] != plan_id or row["question_version"] != QUESTION_VERSION:
        raise ValueError("05H decision plan/question differs")
    refs = row["subject_refs"]
    if (
        not isinstance(refs, list)
        or not refs
        or len(set(refs)) != len(refs)
        or not set(refs) <= subjects
    ):
        raise ValueError("05H decision has missing, duplicate or unknown subjects")
    if row["coverage_basis"] not in {"new_individual", "new_rule"}:
        raise ValueError("05H assembled-view review must declare new review coverage")
    if row["disposition"] not in {
        "confirmed_composition",
        "confirmed_with_limitation",
        "correction_required",
    }:
        raise ValueError("05H decision disposition differs")
    if not row["reviewer"].strip() or not row["rationale"].strip():
        raise ValueError("05H decision requires reviewer and rationale")
    if datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("05H decision time must include timezone")
    if not row["evidence_refs"]:
        raise ValueError("05H decision requires retained sealed evidence")
    for evidence in row["evidence_refs"]:
        if not all(evidence.get(field) for field in ("identity", "path", "sha256", "record_id")):
            raise ValueError("05H decision evidence lacks identity/path/digest/record ID")
        path = PurePosixPath(evidence["path"])
        if (
            path.is_absolute()
            or ".." in path.parts
            or not re.fullmatch(r"[0-9a-f]{64}", evidence["sha256"])
        ):
            raise ValueError("05H decision evidence path/digest is invalid")
    if row["action"] not in {"none", "review_metadata", "display_disposition", "owner_finding"}:
        raise ValueError("05H decision action exceeds overlay authority")
    if row["replacement_refs"]:
        raise ValueError("05H cannot replace upstream records")
    if not isinstance(row["requires_owner_replay"], bool) or not isinstance(
        row["supersedes"], list
    ):
        raise ValueError("05H decision replay/supersession types differ")


def validate_decisions(
    selection: JsonObject, decisions: list[JsonObject], plan_id: str
) -> JsonObject:
    """Require explicit acyclic supersession and all selected review obligations closed."""
    subjects = {obligation["subject_ref"] for obligation in selection["obligations"]}
    by_id: dict[str, JsonObject] = {}
    for row in decisions:
        _check_decision(row, plan_id, subjects)
        bases = {
            obligation["coverage_basis"]
            for obligation in selection["obligations"]
            if obligation["subject_ref"] in row["subject_refs"]
        }
        if bases != {row["coverage_basis"]}:
            raise ValueError("05H decision coverage basis differs from selected obligations")
        if (
            row["disposition"] == "correction_required"
            or row["requires_owner_replay"]
            or row["action"] == "owner_finding"
        ):
            raise ValueError(
                "05H correction requires a separately approved amendment; affected strata pending"
            )
        decision_id = row["decision_id"]
        if decision_id in by_id and by_id[decision_id] != row:
            raise ValueError(f"05H conflicting repeated decision ID: {decision_id}")
        by_id[decision_id] = row
    superseded: set[str] = set()
    for decision_id, row in by_id.items():
        for prior in row["supersedes"]:
            if prior not in by_id or prior == decision_id:
                raise ValueError("05H supersession requires an existing distinct decision")
            if set(row["subject_refs"]) != set(by_id[prior]["subject_refs"]):
                raise ValueError("05H supersession must renew the same subjects")
            if datetime.fromisoformat(
                row["reviewed_at"].replace("Z", "+00:00")
            ) <= datetime.fromisoformat(by_id[prior]["reviewed_at"].replace("Z", "+00:00")):
                raise ValueError("05H supersession requires later renewed review")
            superseded.add(prior)
    active = [row for decision_id, row in by_id.items() if decision_id not in superseded]
    closed: dict[str, str] = {}
    for row in active:
        for subject_ref in row["subject_refs"]:
            if subject_ref in closed:
                raise ValueError(
                    f"05H conflicting decisions for {subject_ref}; explicit supersession required"
                )
            closed[subject_ref] = row["decision_id"]
    pending = subjects - closed.keys()
    if pending:
        raise ValueError(f"05H pending review obligations: {', '.join(sorted(pending)[:5])}")
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "selection_digest": selection["selection_digest"],
        "status": "complete_with_limitations",
        "question_version": QUESTION_VERSION,
        "pending_count": 0,
        "conflicting_count": 0,
        "decision_refs": dict(sorted(closed.items())),
        "decisions_digest": canonical_json_sha256(
            sorted(by_id.values(), key=lambda row: row["decision_id"])
        ),
    }


PRIMARY_IDS = {
    "source_unit": "unit_id",
    "source_span": "span_id",
    "page": "page_id",
    "reference_mention": "mention_id",
    "marker_candidate": "marker_id",
    "diagnostic": "diagnostic_id",
    "source_placement_exception": "exception_id",
    "membership_claim": "membership_id",
    "semantic_edge": "edge_id",
    "review_view": "view_id",
    "draft_eir_link": "link_id",
}


def primary_id(row: JsonObject) -> str | None:
    """Return the owned identifier, never an incidental foreign-key reference."""
    field = PRIMARY_IDS.get(row.get("record_type", ""))
    if field is not None:
        return str(row[field])
    if "outcome_id" in row or ("outcome" in row and "mention_id" in row):
        return str(row["mention_id"])
    return None


def validate_decision_evidence(
    inputs: ReleaseInputs, selection: JsonObject, decisions: list[JsonObject]
) -> None:
    """Bind every cited member to its exact accepted payload or semantic-validated receipt."""
    dependencies = {d.get("role"): d for d in inputs.dependencies}
    allowed: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for role, rows, receipt_role in (
        ("source_records", inputs.source_records, "task05d_completion"),
        ("edges", inputs.edges, "task05e_completion"),
        ("graph_diagnostics", inputs.graph_diagnostics, "task05e_completion"),
        ("outcomes", inputs.outcomes, None),
    ):
        component = next((c for c in inputs.components if c["role"] == role), None)
        receipt = dependencies.get(receipt_role) if receipt_role is not None else None
        for row in rows:
            record_id = primary_id(row)
            if record_id is None:
                continue
            if component and component.get("sha256"):
                allowed[record_id].add(
                    (component["owner_revision"], component["path"], component["sha256"])
                )
            if receipt:
                allowed[record_id].add((receipt["identity"], receipt["path"], receipt["sha256"]))
    provenance_ref = dependencies.get("task06h_decision_provenance")
    if provenance_ref:
        for entry in inputs.limitations.get("decision_provenance", []):
            allowed[entry["entry_id"]].add(
                (provenance_ref["identity"], provenance_ref["path"], provenance_ref["sha256"])
            )
    obligations = {obligation["subject_ref"]: obligation for obligation in selection["obligations"]}
    for row in decisions:
        covered: set[str] = set()
        for evidence in row["evidence_refs"]:
            record_id = evidence["record_id"]
            seal = evidence["identity"], evidence["path"], evidence["sha256"]
            if seal not in allowed.get(record_id, set()):
                raise ValueError(f"05H evidence is not a retained accepted member: {record_id}")
            covered.add(record_id)
        for subject_ref in row["subject_refs"]:
            if subject_ref not in obligations:
                raise ValueError(f"05H evidence cites unknown obligation: {subject_ref}")
            members = obligations[subject_ref]["member_refs"]
            required = {members[0], members[-1]}
            if not required <= covered:
                raise ValueError(
                    f"05H evidence is unrelated or incomplete for subject: {subject_ref}"
                )
