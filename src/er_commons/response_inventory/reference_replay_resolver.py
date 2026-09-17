"""Pure Task 05G exact resolver; review annotations never imply target eligibility."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory import reference_baseline as baseline

type JsonObject = dict[str, Any]

OUTCOME_SCHEMA = "er_commons.task05g.reference_outcome.v1"
RECORD_SCHEMA = "er_commons.response_inventory.v2"
DEPENDENCY_ROLES = (
    "task05d_completion",
    "task05e_completion",
    "task05f_baseline",
    "task06h_acceptance",
    "task06h_handoff",
    "task06h_registry",
    "task06h_toc_merge",
    "task06h_target_limitations",
    "task06g_handoff",
    "task06g_target_index",
    "task06g_source_correspondence",
    "source_family_catalog",
)


@dataclass(frozen=True)
class ReplayResources:
    """Already verified selected targets and review metadata, with no filesystem access."""

    indexes: baseline._TargetIndexes
    aliases: Mapping[str, set[str]]
    designators: Mapping[str, set[str]]
    sources: Mapping[str, JsonObject]
    limitations: Mapping[str, JsonObject]
    handoff: JsonObject
    activity: JsonObject
    target_rows: list[JsonObject]
    inner_references: bool
    header_qualification: bool


def keyed(rows: list[JsonObject], field: str) -> dict[str, JsonObject]:
    """Index records with duplicate rejection, including identical duplicate rows."""
    result: dict[str, JsonObject] = {}
    for row in rows:
        key = str(row[field])
        if key in result:
            raise ValueError(f"duplicate {field}: {key}")
        result[key] = row
    return result


def _identified(row: JsonObject, field: str, prefix: str) -> JsonObject:
    """Return a content-addressed record without mutating an accepted input."""
    return {**row, field: prefix + canonical_json_sha256(row)}


def _verify_f1_substitution(handoff: JsonObject, sources: Mapping[str, JsonObject]) -> JsonObject:
    """Require the selected physical candidate to agree with the accepted substitution."""
    binding: JsonObject = handoff.get("final_f1_warning_binding", {})
    substitution = binding.get("source_substitution", {})
    selected = substitution.get("selected", {})
    source = sources.get("feir_appendix_f1", {})
    if (
        substitution.get("logical_source_id") != "deir_appendix_f1"
        or selected.get("source_id") != "feir_appendix_f1"
        or not selected.get("candidate_id")
        or source.get("selected_candidate_id") != selected["candidate_id"]
        or source.get("logical_source_id") != "deir_appendix_f1"
        or substitution.get("draft_final_equivalence_proven") is not False
        or substitution.get("semantic_equivalence") is not False
    ):
        raise ValueError("unverified Final F1 logical-to-physical substitution")
    return binding


def _logical_catalog_routes(
    routes: Mapping[str, set[str]], handoff: JsonObject, sources: Mapping[str, JsonObject]
) -> dict[str, set[str]]:
    """Recover only F1's verified logical route from its selected physical catalog entry."""
    if any("feir_appendix_f1" in values for values in routes.values()):
        _verify_f1_substitution(handoff, sources)
    return {
        key: {"deir_appendix_f1" if source == "feir_appendix_f1" else source for source in values}
        for key, values in routes.items()
    }


def _f1_annotations(
    mention: JsonObject, handoff: JsonObject, sources: Mapping[str, JsonObject]
) -> JsonObject:
    """Copy the complete substitution warning and attach exact response-specific warnings."""
    binding = _verify_f1_substitution(handoff, sources)
    specific = []
    for warning in binding["response_specific"]:
        if mention["mention_id"] in warning["mention_ids"]:
            if mention["source_unit_id"] != warning["unit_id"]:
                raise ValueError("Final F1 warning source unit mismatch")
            specific.append(warning)
    return {
        "binding": binding,
        "response_specific": specific,
        "draft_final_equivalence_proven": False,
    }


def _review_annotations(
    candidates: baseline._CandidateRows, resources: ReplayResources
) -> list[JsonObject]:
    """Retain every candidate's source policy and exact target limitation independently."""
    annotations = []
    targets = {str(row["target_id"]): row for row in candidates.compatible_rows}
    for target_id, row in sorted(targets.items()):
        source_id = str(row["source_id"])
        source = resources.sources.get(source_id)
        if source is None:
            raise ValueError(f"selected target lacks accepted source usability: {source_id}")
        limitation = resources.limitations.get(target_id)
        eligibility = None if limitation is None else limitation.get("text_only_model_eligibility")
        if row["target_type"] == "figure":
            if limitation is None or eligibility is not False:
                raise ValueError(f"figure target lacks explicit text-only exclusion: {target_id}")
        annotations.append(
            {
                "target_id": target_id,
                "source_id": source_id,
                "target_type": row["target_type"],
                "source_usability": source,
                "target_limitation": limitation,
                "fresh_review_status": (
                    "no_fresh_task06h_target_review"
                    if limitation is None
                    else limitation["fresh_review_status"]
                ),
                "text_only_model_eligibility": eligibility,
            }
        )
    return annotations


def _routed_query(
    mention: JsonObject, resources: ReplayResources
) -> tuple[str, baseline._QueryPlan, list[str], JsonObject | None]:
    """Keep logical source identity while routing an approved F1 substitute physically."""
    labels = mention.get("target_labels")
    if not isinstance(labels, list) or len(labels) != 1 or not isinstance(labels[0], str):
        raise ValueError("Task 05G requires one string target label")
    plan = baseline._query_plan(
        labels[0], mention["reference_domain"], resources.aliases, resources.designators
    )
    logical_sources = sorted(plan.routed_sources)
    f1 = (
        _f1_annotations(mention, resources.handoff, resources.sources)
        if "deir_appendix_f1" in logical_sources
        else None
    )
    if f1 is not None:
        plan = replace(
            plan,
            routed_sources=frozenset(
                "feir_appendix_f1" if value == "deir_appendix_f1" else value
                for value in plan.routed_sources
            ),
        )
    return labels[0], plan, logical_sources, f1


def _select_candidates(
    plan: baseline._QueryPlan,
    source_kind: str,
    previous: JsonObject,
    context: baseline._MentionContext,
    resources: ReplayResources,
) -> tuple[baseline._QueryPlan, baseline._CandidateRows, str | None, JsonObject | None]:
    """Apply exact lookup and optional inner rules without weakening specificity guards."""
    reason = plan.terminal_reason
    candidates = baseline._CandidateRows()
    inner_evidence: JsonObject | None = None
    proposal = None
    legacy_specific = (
        baseline._has_attached_inner_target(context)
        or previous.get("terminal_reason") == "more_specific_appendix_target_requires_resolution"
    )
    # This rule cycle repairs existing guarded nonlinks, never reinterprets links.
    # Eligibility is the prior rule's general predicate, not document/mention IDs.
    if (
        resources.inner_references
        and legacy_specific
        and plan.requested_type == "document"
        and reason is None
    ):
        from er_commons.response_inventory.reference_replay_inner import propose_inner

        proposal = propose_inner(context, plan.routed_sources, resources.target_rows)
        if proposal.selected is not None:
            inner_evidence = {
                "rule": proposal.rule,
                "syntax": list(proposal.evidence),
                "unverified_page_qualifier": proposal.unverified_page_qualifier,
                "selected_alias": proposal.selected,
            }
            plan = replace(plan, requested_type=proposal.requested_type)
            candidates = baseline._CandidateRows(
                global_rows=proposal.candidates,
                source_rows=proposal.candidates,
                compatible_rows=proposal.candidates,
                resolver_rule="task05g_general_inner_reference_v1",
            )
    # Preserve exact diagnostic options while preventing generic document resolution.
    attached_specific = (
        proposal.specific if proposal is not None else baseline._has_attached_inner_target(context)
    ) or previous.get("terminal_reason") == "more_specific_appendix_target_requires_resolution"
    if reason is None and plan.requested_type == "document" and attached_specific:
        # The accepted fallback guard retained these exact lookup diagnostics.
        # Do not invoke the generic document fallback or erase outside-source options.
        global_rows = (
            resources.indexes.by_key.get(plan.canonical, ()) if plan.canonical is not None else ()
        )
        candidates = baseline._CandidateRows(
            global_rows=global_rows,
            source_rows=[row for row in global_rows if row["source_id"] in plan.routed_sources],
        )
        reason = "more_specific_appendix_target_requires_resolution"
    if reason is None and inner_evidence is None:
        query_context = context
        if proposal is not None and not proposal.specific:
            # The legacy fallback must not reintroduce its partial-token guard.
            query_context = baseline._MentionContext()
        candidates = baseline._find_candidates(plan, resources.indexes, query_context)
        reason = candidates.terminal_reason or baseline._candidate_reason(
            source_kind,
            candidates.global_rows,
            candidates.source_rows,
            candidates.compatible_rows,
            plan.requested_type,
        )
    return plan, candidates, reason, inner_evidence


def _qualify_header_collision(
    plan: baseline._QueryPlan,
    candidates: baseline._CandidateRows,
    reason: str | None,
    *,
    source_kind: str,
    enabled: bool,
) -> tuple[baseline._CandidateRows, str | None, JsonObject | None]:
    """Resolve a section collision only when corroborated header exclusions leave one target."""
    header_evidence: JsonObject | None = None
    if (
        enabled
        and reason == "exact_target_collision"
        and plan.requested_type == "section"
        and source_kind == "response"
    ):
        rejected = {
            row["target_id"]: row["header_qualification"]
            for row in candidates.compatible_rows
            if row.get("header_qualification")
        }
        remaining = [row for row in candidates.compatible_rows if row["target_id"] not in rejected]
        if rejected and len({row["target_id"] for row in remaining}) == 1:
            header_evidence = {
                "rule": "corroborated_running_header_exclusion_v1",
                "excluded_targets": dict(sorted(rejected.items())),
                "selected_target_id": remaining[0]["target_id"],
                "fresh_human_review": False,
            }
            candidates = baseline._CandidateRows(
                global_rows=candidates.global_rows,
                source_rows=candidates.source_rows,
                compatible_rows=remaining,
                resolver_rule="task05g_header_qualified_section_v1",
            )
            reason = None
    return candidates, reason, header_evidence


def _resolve_one(
    mention: JsonObject,
    source: JsonObject,
    previous: JsonObject,
    context: baseline._MentionContext,
    resources: ReplayResources,
) -> tuple[JsonObject, JsonObject | None, JsonObject | None]:
    """Resolve one mention, then serialize its link or diagnostic with review evidence."""
    label, plan, logical_sources, f1 = _routed_query(mention, resources)
    plan, candidates, reason, inner_evidence = _select_candidates(
        plan, str(source["unit_kind"]), previous, context, resources
    )
    candidates, reason, header_evidence = _qualify_header_collision(
        plan,
        candidates,
        reason,
        source_kind=str(source["unit_kind"]),
        enabled=resources.header_qualification,
    )
    # Authorship exclusion applies even when the cited target is uniquely identified.
    if source["unit_kind"] == "comment":
        reason = "comment_authored_reference_no_official_response_link"
    annotations = _review_annotations(candidates, resources)
    dependencies = resources.activity["input_refs"]
    link = None
    if reason is None:
        if len(annotations) != 1:
            raise ValueError("resolved outcome must select exactly one target")
        link = _identified(
            {
                "schema_version": RECORD_SCHEMA,
                "record_type": "draft_eir_link",
                "mention_id": mention["mention_id"],
                "source_unit_id": mention["source_unit_id"],
                "target_id": annotations[0]["target_id"],
                "activity_id": resources.activity["activity_id"],
                "resolver_rule": candidates.resolver_rule,
                "input_refs": dependencies,
                "target_annotation": annotations[0],
                "final_f1_warning": f1,
            },
            "link_id",
            "linkv2-",
        )
    outcome = _identified(
        {
            "schema_version": OUTCOME_SCHEMA,
            **(
                {"header_qualification_evidence": header_evidence}
                if header_evidence is not None
                else {}
            ),
            **({"inner_reference_evidence": inner_evidence} if inner_evidence is not None else {}),
            **{
                key: mention[key]
                for key in (
                    "mention_id",
                    "mention_span_id",
                    "source_unit_id",
                    "raw_text_sha256",
                    "reference_domain",
                )
            },
            "source_kind": source["unit_kind"],
            "source_usability": [resources.sources[value] for value in sorted(plan.routed_sources)],
            "raw_target_label": label,
            "qualifier": plan.qualifier,
            "projected_target": plan.projected,
            "canonical_target": plan.canonical,
            "requested_target_type": plan.requested_type,
            "logical_source_ids": logical_sources,
            "routed_source_ids": sorted(plan.routed_sources),
            "global_candidate_target_ids": sorted(
                {row["target_id"] for row in candidates.global_rows}
            ),
            "source_candidate_target_ids": sorted(
                {row["target_id"] for row in candidates.source_rows}
            ),
            "compatible_target_ids": sorted(
                {row["target_id"] for row in candidates.compatible_rows}
            ),
            "outcome": "resolved" if link else "terminal_nonlink",
            "terminal_reason": reason,
            "link_id": link["link_id"] if link else None,
            "resolver_rule": candidates.resolver_rule,
            "target_annotations": annotations,
            "final_f1_warning": f1,
            "input_refs": dependencies,
            "coverage_boundary": resources.handoff["coverage_boundary"],
        },
        "outcome_id",
        "outcomev2-",
    )
    diagnostic = (
        None
        if link
        else _identified(
            {
                "schema_version": RECORD_SCHEMA,
                "record_type": "diagnostic",
                "stage": "05g",
                "mention_id": mention["mention_id"],
                "mention_span_id": mention["mention_span_id"],
                "activity_id": resources.activity["activity_id"],
                "terminal_reason": reason,
                "input_refs": dependencies,
            },
            "diagnostic_id",
            "diagnosticv2-",
        )
    )
    return outcome, link, diagnostic


def resolve_references(
    source_records: list[JsonObject],
    target_rows: list[JsonObject],
    direct_section_children: dict[str, list[str]],
    catalog: JsonObject,
    registry: JsonObject,
    target_limitations: JsonObject,
    handoff: JsonObject,
    activity: JsonObject,
    baseline_outcomes: list[JsonObject],
    *,
    inner_references: bool = False,
    header_qualification: bool = False,
) -> JsonObject:
    """Resolve an exactly preserved baseline population without reading sources or writing files."""
    roles = [entry["role"] for entry in activity["input_refs"]]
    if roles != list(DEPENDENCY_ROLES):
        raise ValueError("Task 05G ordered dependency roles differ")
    target_identity: dict[str, tuple[str, str]] = {}
    for row in target_rows:
        target_id = str(row["target_id"])
        identity = (str(row["source_id"]), str(row["target_type"]))
        if target_id in target_identity and target_identity[target_id] != identity:
            raise ValueError("conflicting selected target identity")
        target_identity[target_id] = identity
    previous = keyed(baseline_outcomes, "mention_id")
    mentions = keyed(
        [
            row
            for row in source_records
            if row.get("record_type") == "reference_mention"
            and row.get("reference_domain") in {"draft_eir", "appendix_q"}
        ],
        "mention_id",
    )
    if set(mentions) != set(previous):
        raise ValueError("replay mention population differs from baseline")
    units = keyed(
        [row for row in source_records if row.get("record_type") == "source_unit"], "unit_id"
    )
    contexts = baseline._mention_contexts(source_records)
    limitations = keyed(target_limitations["entries"], "target_id")
    for candidate_id, target_id in target_limitations.get("document_target_mapping", {}).items():
        if candidate_id in limitations:
            if target_id in limitations and limitations[target_id] != limitations[candidate_id]:
                raise ValueError("conflicting document target limitation mapping")
            limitations[target_id] = limitations[candidate_id]
    sources = keyed(registry["entries"], "selected_source_id")
    resources = ReplayResources(
        indexes=baseline._target_indexes(target_rows, direct_section_children),
        aliases=_logical_catalog_routes(baseline._catalog_aliases(catalog), handoff, sources),
        designators=_logical_catalog_routes(
            baseline._catalog_designators(catalog), handoff, sources
        ),
        sources=sources,
        limitations=limitations,
        handoff=handoff,
        activity=activity,
        target_rows=target_rows,
        inner_references=inner_references,
        header_qualification=header_qualification,
    )
    outcomes, links, diagnostics = [], [], []
    for mention_id, mention in sorted(mentions.items()):
        source = units[str(mention["source_unit_id"])]
        old = previous[mention_id]
        for field, value in (
            ("source_unit_id", mention["source_unit_id"]),
            ("mention_span_id", mention["mention_span_id"]),
            ("raw_text_sha256", mention["raw_text_sha256"]),
            ("reference_domain", mention["reference_domain"]),
            ("source_kind", source["unit_kind"]),
        ):
            if old.get(field) != value:
                raise ValueError(f"baseline immutable mention field differs: {field}")
        outcome, link, diagnostic = _resolve_one(
            mention,
            source,
            old,
            contexts.get(str(mention["mention_span_id"]), baseline._MentionContext()),
            resources,
        )
        outcomes.append(outcome)
        if link is not None:
            links.append(link)
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    forward, reverse = baseline._indexes(outcomes, links)
    return {
        "outcomes": outcomes,
        "links": links,
        "diagnostics": diagnostics,
        "forward": forward,
        "reverse": reverse,
        "census": {
            "total": len(outcomes),
            "links": len(links),
            "explicit_nonlinks": len(diagnostics),
            "terminal_reasons": dict(
                sorted(
                    Counter(
                        row["terminal_reason"]
                        for row in outcomes
                        if row["terminal_reason"] is not None
                    ).items()
                )
            ),
        },
    }
