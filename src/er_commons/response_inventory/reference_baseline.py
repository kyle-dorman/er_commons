"""Source-aware exact Draft EIR reference resolution for Task 05F."""

from __future__ import annotations

import hashlib
import re
import shutil
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    jsonl_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    read_jsonl,
)
from er_commons.document_records.document_structure.normalization import normalize_alias
from er_commons.response_inventory.contract import build_record_id
from er_commons.response_inventory.run_spec import (
    ResponseReferenceRunSpecV5,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)

type JsonObject = dict[str, Any]

SCHEMA_VERSION = "er_commons.response_inventory.v1"
OUTCOME_SCHEMA_VERSION = "er_commons.task05f.reference_outcome.v1"
RULES_SCHEMA_VERSION = "er_commons.task05f.qualified_rules.v1"
RESOLVER_RULE = "task05f_qualified_exact_rules_v5"
EXPECTED_DOMAINS = {"draft_eir": 509, "appendix_q": 2}
EXPECTED_ALL_DOMAINS = {"appendix_q": 2, "draft_eir": 509, "intra_volume": 759}
EXPECTED_DRAFT_AUTHORSHIP = {"comment": 11, "general_response": 42, "response": 456}
QUALIFIERS = ("Draft EIR \r\n", "Draft \r\nEIR ", "Draft EIR ", "DEIR ")
TARGET_TYPES = {
    "chapter": "section",
    "section": "section",
    "table": "table",
    "figure": "figure",
    "page": "page",
}
_TARGET_FORM = re.compile(r"^(chapter|section|table|figure|page)\b")
_APPENDIX_DESIGNATOR = re.compile(r"^appendix\s+([a-z])(?:[.\-]?\s*(\d+))?(?=\s|$|[-:])")
_DIRECT_REFERENCE = re.compile(r"^(chapter|section|table)\s+((?:\d+|es)(?:[.\-][a-z0-9]+)*)$")
_SECTION_ALIAS_IDENTIFIER = re.compile(r"^(?:(chapter)\s+)?((?:\d+|es)(?:\.\d+)*)\b")
_TABLE_ALIAS_IDENTIFIER = re.compile(r"^table\s+(\d+(?:[.\-][a-z0-9]+)*)\b")
_TABLE_PERIOD_SEPARATOR = re.compile(r"^table\s+(\d+\.\d+)\.(\d+[a-z]?)$")
_SECTION_HYPHEN_SEPARATOR = re.compile(r"^section\s+(\d+)-(\d+)$")
_HIERARCHICAL_SUBSECTION = re.compile(r"^section\s+(\d+(?:\.\d+)+)\.?([a-z])$")
_CHILD_SECTION_DESIGNATOR = re.compile(r"^([a-z])\s*[.)](?:\s|$)")
_INNER_TARGET = re.compile(r"\b(?:chapter|figure|page|section|table)\s+[a-z0-9]", re.I)


@dataclass(frozen=True)
class _QueryPlan:
    """Exact projected query and its source/type routing decision."""

    qualifier: str | None = None
    projected: str | None = None
    canonical: str | None = None
    requested_type: str | None = None
    routed_sources: frozenset[str] = frozenset()
    terminal_reason: str | None = None


@dataclass(frozen=True)
class _MentionContext:
    """Bounded same-sentence text immediately surrounding one accepted mention."""

    before: str = ""
    after: str = ""


@dataclass(frozen=True)
class _TargetIndexes:
    """Small derived indexes over the accepted Task 04D target rows."""

    by_key: Mapping[str, Sequence[JsonObject]]
    by_identifier: Mapping[tuple[str, str, str], Sequence[JsonObject]]
    by_hierarchical_subsection: Mapping[tuple[str, str, str], Sequence[JsonObject]]
    documents_by_source: Mapping[str, Sequence[JsonObject]]


@dataclass(frozen=True)
class _ResolutionResources:
    """Shared immutable lookup state for resolving one or many mentions."""

    indexes: _TargetIndexes
    catalog_aliases: Mapping[str, set[str]]
    catalog_designators: Mapping[str, set[str]]
    registry: Mapping[str, JsonObject]
    activity: JsonObject


@dataclass(frozen=True)
class _ResolutionResults:
    """Sorted records produced by resolving the complete mention population."""

    outcomes: list[JsonObject]
    links: list[JsonObject]
    diagnostics: list[JsonObject]


@dataclass(frozen=True)
class _CandidateRows:
    """Candidate rows after exact lookup and any one qualified fallback."""

    global_rows: Sequence[JsonObject] = ()
    source_rows: Sequence[JsonObject] = ()
    compatible_rows: Sequence[JsonObject] = ()
    resolver_rule: str = RESOLVER_RULE
    terminal_reason: str | None = None


def build_qualified_reference_rules(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
) -> JsonObject:
    """Build or byte-verify the nonterminal source-free qualified-rule result."""
    loaded, config_sha256 = load_response_inventory_run_spec(run_spec_path)
    if not isinstance(loaded, ResponseReferenceRunSpecV5):
        raise ValueError("qualified reference rules require a Task 05F v5 run specification")
    verify_repository_bindings(loaded, repository_root)
    bindings = {item.role: item.path for item in loaded.repository_bindings}
    records_schema_path = repository_root / bindings["response_record_schema"]
    outcome_schema_path = repository_root / bindings["reference_outcome_schema"]
    records_schema = read_json_object(records_schema_path)
    outcome_schema = read_json_object(outcome_schema_path)

    source_records, units = _load_task05d(loaded, artifact_root)
    _validate_task05e(loaded, artifact_root)
    registry = _load_task04a(loaded, artifact_root)
    target_rows, target_counts, direct_section_children = _load_task04d(
        loaded, repository_root, artifact_root
    )
    catalog = _load_source_catalog(loaded, artifact_root)

    activity = _activity_record(loaded, config_sha256, records_schema_path)
    all_mentions = [
        record for record in source_records if record.get("record_type") == "reference_mention"
    ]
    _validate_population(all_mentions, units)
    mentions = [
        record for record in all_mentions if record.get("reference_domain") in EXPECTED_DOMAINS
    ]
    contexts = _mention_contexts(source_records)
    resources = _ResolutionResources(
        indexes=_target_indexes(target_rows, direct_section_children),
        catalog_aliases=_catalog_aliases(catalog),
        catalog_designators=_catalog_designators(catalog),
        registry=registry,
        activity=activity,
    )
    built = _resolve_all(mentions, units, contexts, resources)
    outcomes = built.outcomes
    links = built.links
    diagnostics = built.diagnostics
    _validate_outcomes(outcomes, outcome_schema)
    _validate_record_shapes([activity, *links, *diagnostics], records_schema)
    _validate_provenance(links, diagnostics, source_records, units)
    forward, reverse = _indexes(outcomes, links)
    census = _census(outcomes, links, diagnostics, target_counts, activity)
    payloads = {
        "diagnostics/rule_census.json": json_bytes(census),
        "diagnostics/individual_diagnostics.jsonl": jsonl_bytes(diagnostics),
        "indexes/mention_to_link.jsonl": jsonl_bytes(forward),
        "indexes/target_to_links.jsonl": jsonl_bytes(reverse),
        "links/draft_eir_links.jsonl": jsonl_bytes(links),
        "outcomes/reference_outcomes.jsonl": jsonl_bytes(outcomes),
        "records/activity.json": json_bytes(activity),
        "records/dependencies.json": json_bytes(
            {"schema_version": RULES_SCHEMA_VERSION, "inputs": activity["input_refs"]}
        ),
    }
    inventory = _inventory_record(activity, payloads)
    _validate_record_shapes([inventory], records_schema)
    if inventory["dependencies"] != activity["input_refs"]:
        raise ValueError("Task 05F inventory dependencies differ from its activity")
    payloads["records/managed_file_inventory.json"] = json_bytes(inventory)
    receipt = _receipt(activity, census, built, payloads)
    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    relative_root = loaded.output_policy.artifact_relative_root / (
        loaded.output_policy.candidate_namespace_template.format(activity_hash=activity_hash)
    )
    candidate_root = (artifact_root.resolve() / relative_root).resolve()
    if not candidate_root.is_relative_to(artifact_root.resolve()):
        raise ValueError("Task 05F qualified-rule path escapes the artifact root")
    _publish_candidate(candidate_root, payloads, receipt)
    return {
        "schema_version": RULES_SCHEMA_VERSION,
        "status": "qualified_rules_complete_review_required",
        "activity_id": activity["activity_id"],
        "candidate_root": candidate_root.as_posix(),
        "semantic_digest": receipt["semantic_digest"],
        "counts": census["counts"],
        "failure_census": census["failure_census"],
        "terminal_publication_authorized": False,
        "source_pdf_accessed": False,
        "large_upstream_payloads_hashed": False,
    }


def _load_task05d(
    spec: ResponseReferenceRunSpecV5, artifact_root: Path
) -> tuple[list[JsonObject], dict[str, JsonObject]]:
    """Validate accepted 05D metadata and read records without hashing the payload."""
    root = artifact_root.resolve()
    accepted = spec.accepted_task05d
    candidate = _contained(root, accepted.candidate_root, "05D candidate")
    acceptance = read_json_object(_contained(root, accepted.acceptance_path, "05D acceptance"))
    _validate_acceptance(
        acceptance,
        expected={
            "acceptance_id": accepted.acceptance_id,
            "activity_id": accepted.activity_id,
            "completion_id": accepted.completion_id,
            "inventory_id": accepted.inventory_id,
            "semantic_digest": accepted.semantic_digest,
            "status": "accepted",
            "working_revision": accepted.candidate_root.as_posix(),
        },
    )
    completion = read_json_object(candidate / "records/stage_completion.json")
    inventory = read_json_object(candidate / "records/managed_file_inventory.json")
    summary = read_json_object(candidate / "diagnostics/build_summary.json")
    _require_fields(
        completion,
        {
            "activity_id": accepted.activity_id,
            "completion_id": accepted.completion_id,
            "inventory_id": accepted.inventory_id,
        },
        "05D completion",
    )
    _require_fields(
        inventory,
        {"activity_id": accepted.activity_id, "inventory_id": accepted.inventory_id},
        "05D inventory",
    )
    if summary.get("semantic_digest") != accepted.semantic_digest:
        raise ValueError("05D summary semantic digest differs from acceptance")
    records_path = candidate / "inventory/source_records.jsonl"
    _verify_recorded_size(inventory, "inventory/source_records.jsonl", records_path, "05D")
    records = [cast(JsonObject, row) for row in read_jsonl(records_path)]
    units = {
        str(record["unit_id"]): record
        for record in records
        if record.get("record_type") == "source_unit"
    }
    return records, units


def _validate_task05e(spec: ResponseReferenceRunSpecV5, artifact_root: Path) -> None:
    """Bind the accepted 05E graph through compact records and payload sizes only."""
    root = artifact_root.resolve()
    accepted = spec.accepted_task05e
    candidate = _contained(root, accepted.candidate_root, "05E candidate")
    acceptance = read_json_object(_contained(root, accepted.acceptance_path, "05E acceptance"))
    _validate_acceptance(
        acceptance,
        expected={
            "acceptance_id": accepted.acceptance_id,
            "accepted_downstream_consumer": "task05f",
            "activity_id": accepted.activity_id,
            "completion_id": accepted.completion_id,
            "inventory_id": accepted.inventory_id,
            "semantic_digest": accepted.semantic_digest,
            "status": "accepted",
            "working_revision": accepted.candidate_root.as_posix(),
        },
    )
    completion = read_json_object(candidate / "records/stage_completion.json")
    inventory = read_json_object(candidate / "records/managed_file_inventory.json")
    receipt = read_json_object(candidate / "records/review_receipt.json")
    _require_fields(
        completion,
        {
            "activity_id": accepted.activity_id,
            "completion_id": accepted.completion_id,
            "inventory_id": accepted.inventory_id,
        },
        "05E completion",
    )
    _require_fields(
        inventory,
        {"inventory_id": accepted.inventory_id},
        "05E inventory",
    )
    _require_fields(
        receipt,
        {
            "activity_id": accepted.activity_id,
            "semantic_digest": accepted.semantic_digest,
            "source_pdf_accessed": False,
        },
        "05E review receipt",
    )
    _verify_recorded_size(
        inventory, "graph/review_edges.jsonl", candidate / "graph/review_edges.jsonl", "05E"
    )


def _load_task04a(spec: ResponseReferenceRunSpecV5, artifact_root: Path) -> dict[str, JsonObject]:
    """Validate compact Gate D records and index source-level usability."""
    root = _contained(artifact_root.resolve(), spec.task04.task04a_gate_d_root, "04A Gate D")
    completion_path = root / "gate_d_completion.json"
    if _sha256_small(completion_path) != spec.task04.gate_d_completion_sha256:
        raise ValueError("Task 04A Gate D completion digest mismatch")
    completion = read_json_object(completion_path)
    if (
        completion.get("review_run_id") != spec.task04.task04a_review_id
        or completion.get("status") != "complete"
    ):
        raise ValueError("Task 04A Gate D is not the accepted completed review")
    managed = cast(Mapping[str, JsonObject], completion.get("managed_records", {}))
    expected = {
        "usability_registry": spec.task04.usability_registry_sha256,
        "ambiguous_link_dispositions": spec.task04.ambiguous_dispositions_sha256,
        "unresolved_risk_report": spec.task04.unresolved_risk_sha256,
    }
    for role, digest in expected.items():
        if managed.get(role, {}).get("sha256") != digest:
            raise ValueError(f"Task 04A {role} binding mismatch")
        managed_path = root / str(managed[role]["path"])
        if managed_path.stat().st_size != managed[role].get("byte_size"):
            raise ValueError(f"Task 04A {role} recorded size mismatch")
    registry_path = root / "usability_registry.json"
    risk_path = root / "unresolved_risk_report.json"
    if _sha256_small(registry_path) != spec.task04.usability_registry_sha256:
        raise ValueError("Task 04A usability registry digest mismatch")
    if _sha256_small(risk_path) != spec.task04.unresolved_risk_sha256:
        raise ValueError("Task 04A unresolved-risk digest mismatch")
    registry = read_json_object(registry_path)
    if (
        registry.get("review_run_id") != spec.task04.task04a_review_id
        or registry.get("status") != "approved"
    ):
        raise ValueError("Task 04A usability registry is not approved")
    entries = cast(list[JsonObject], registry.get("entries", []))
    indexed = {str(item["source_id"]): item for item in entries}
    if len(entries) != 35 or len(indexed) != 35:
        raise ValueError("Task 04A usability registry must contain 35 unique sources")
    return indexed


def _load_task04d(
    spec: ResponseReferenceRunSpecV5,
    repository_root: Path,
    artifact_root: Path,
) -> tuple[list[JsonObject], dict[str, int], dict[str, tuple[str, ...]]]:
    """Validate the handoff and read its target rows without hashing large files."""
    task04 = spec.task04
    root = artifact_root.resolve()
    handoff_root = _contained(root, task04.task04d_handoff_root, "04D handoff")
    handoff_path = handoff_root / "records/completion_record.json"
    if _sha256_small(handoff_path) != task04.handoff_completion_sha256:
        raise ValueError("Task 04D handoff completion digest mismatch")
    handoff = read_json_object(handoff_path)
    _require_fields(
        handoff,
        {
            "handoff_id": task04.task04d_handoff_id,
            "index_id": task04.target_index_id,
            "scope_id": task04.scope_id,
            "status": "ready",
        },
        "04D handoff",
    )
    identity_preimage = cast(JsonObject, handoff.get("identity_preimage", {}))
    _require_fields(
        identity_preimage,
        {
            "production_extraction_id": task04.production_extraction_id,
            "scope_id": task04.scope_id,
            "index_completion_sha256": task04.target_index_completion_sha256,
            "status": "ready",
        },
        "04D handoff identity preimage",
    )
    index_ref = cast(JsonObject, handoff.get("index_completion_ref", {}))
    if index_ref.get("sha256") != task04.target_index_completion_sha256:
        raise ValueError("Task 04D target-index completion binding mismatch")
    target_root = _contained(root, task04.target_index_root, "04D target index")
    completion_path = target_root / "records/completion_record.json"
    if completion_path.stat().st_size != index_ref.get("byte_size"):
        raise ValueError("Task 04D target-index completion size mismatch")
    index_completion = read_json_object(completion_path)
    _require_fields(
        index_completion,
        {"index_id": task04.target_index_id, "status": "complete"},
        "04D target-index completion",
    )
    inventory = read_json_object(target_root / "records/artifact_inventory.json")
    target_path = target_root / "target_index.jsonl"
    _verify_recorded_size(inventory, "target_index.jsonl", target_path, "04D target index")
    inventory_entry = _inventory_entry(inventory, "target_index.jsonl", "04D target index")
    entries_ref = cast(JsonObject, index_completion.get("entries_ref", {}))
    if (
        Path(str(entries_ref.get("path"))).name != "target_index.jsonl"
        or entries_ref.get("byte_size") != inventory_entry.get("byte_size")
        or entries_ref.get("sha256") != inventory_entry.get("sha256")
    ):
        raise ValueError("Task 04D target rows differ from recorded completion metadata")
    collection_spec = read_json_object(
        repository_root / _binding_path(spec, "task04d_collection_spec")
    )
    if (
        collection_spec.get("source_family_catalog_relative_path")
        != task04.source_family_catalog_path.as_posix()
    ):
        raise ValueError("Task 04D collection spec points to a different source-family catalog")
    rows = [cast(JsonObject, row) for row in read_jsonl(target_path)]
    if len(rows) != index_completion.get("entry_count"):
        raise ValueError("Task 04D target row count differs from completion metadata")
    counts = dict(sorted(Counter(str(row["target_type"]) for row in rows).items()))
    counts.setdefault("figure", 0)
    direct_section_children = _load_main_section_children(index_completion, target_root)
    return rows, counts, direct_section_children


def _load_main_section_children(
    index_completion: JsonObject,
    target_root: Path,
) -> dict[str, tuple[str, ...]]:
    """Read accepted main-document hierarchy edges without hashing the payload."""
    eligible = cast(list[JsonObject], index_completion.get("eligible_candidates", []))
    main_candidates = [item for item in eligible if item.get("source_id") == "deir_main"]
    if len(main_candidates) != 1:
        raise ValueError("Task 04D target index must bind one deir_main candidate")
    target_refs = cast(list[JsonObject], main_candidates[0].get("target_records_ref", []))
    section_refs = [
        item for item in target_refs if str(item.get("path", "")).endswith("/sections.jsonl")
    ]
    if len(section_refs) != 1:
        raise ValueError("Task 04D deir_main candidate must bind one sections payload")
    section_ref = section_refs[0]
    publication_root = _document_publication_root(target_root)
    sections_path = _contained(
        publication_root,
        Path(str(section_ref["path"])),
        "04D deir_main sections",
    )
    if sections_path.stat().st_size != section_ref.get("byte_size"):
        raise ValueError("Task 04D deir_main sections recorded size mismatch")
    sections = [cast(JsonObject, row) for row in read_jsonl(sections_path)]
    section_ids = {str(row["id"]) for row in sections}
    return {
        str(row["id"]): tuple(
            str(child_id)
            for child_id in cast(list[str], row.get("ordered_child_ids", []))
            if str(child_id) in section_ids
        )
        for row in sections
    }


def _document_publication_root(target_root: Path) -> Path:
    """Derive and validate the publication root containing an accepted target index."""
    if (
        target_root.parent.name != "target_indexes"
        or target_root.parents[2].name != "scopes"
        or target_root.parents[3].name != "document_publications"
    ):
        raise ValueError("Task 04D target-index path has an unexpected publication layout")
    return target_root.parents[3]


def _load_source_catalog(spec: ResponseReferenceRunSpecV5, artifact_root: Path) -> JsonObject:
    """Read the small catalog selected by the accepted Task 04D collection spec."""
    path = _contained(
        artifact_root.resolve(), spec.task04.source_family_catalog_path, "source-family catalog"
    )
    if _sha256_small(path) != spec.task04.source_family_catalog_sha256:
        raise ValueError("source-family catalog digest mismatch")
    catalog = read_json_object(path)
    if catalog.get("schema_version") != "er_commons.source_family_catalog.v1":
        raise ValueError("source-family catalog schema differs")
    return catalog


def _resolve_all(
    mentions: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    contexts: Mapping[str, _MentionContext],
    resources: _ResolutionResources,
) -> _ResolutionResults:
    """Resolve every mention independently through the qualified exact policy."""
    outcomes: list[JsonObject] = []
    links: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    for mention in sorted(mentions, key=lambda item: str(item["mention_id"])):
        source = units.get(str(mention["source_unit_id"]))
        if source is None:
            raise ValueError(f"reference mention has no source unit: {mention['mention_id']}")
        outcome, link = _resolve_reference(
            mention,
            source,
            resources,
            contexts.get(str(mention["mention_span_id"]), _MentionContext()),
        )
        outcomes.append(outcome)
        if link is not None:
            links.append(link)
        else:
            diagnostics.append(_diagnostic(resources.activity, outcome))
    return _ResolutionResults(
        outcomes=sorted(outcomes, key=lambda item: str(item["outcome_id"])),
        links=sorted(links, key=lambda item: str(item["link_id"])),
        diagnostics=sorted(diagnostics, key=lambda item: str(item["diagnostic_id"])),
    )


def _resolve_reference(
    mention: Mapping[str, Any],
    source: Mapping[str, Any],
    resources: _ResolutionResources,
    context: _MentionContext | None = None,
) -> tuple[JsonObject, JsonObject | None]:
    """Resolve one mention after source routing and target-ID deduplication."""
    labels = mention.get("target_labels")
    if not isinstance(labels, list) or len(labels) != 1 or not isinstance(labels[0], str):
        raise ValueError("Task 05F requires exactly one string target label per mention")
    raw_label = labels[0]
    domain = str(mention["reference_domain"])
    source_kind = str(source["unit_kind"])
    mention_context = context or _MentionContext()
    plan = _query_plan(
        raw_label,
        domain,
        resources.catalog_aliases,
        resources.catalog_designators,
    )
    candidates = _CandidateRows()
    reason = plan.terminal_reason
    if reason is None and "deir_appendix_f1" in plan.routed_sources:
        reason = "upstream_source_identity_repair_required"
    if reason is None and plan.canonical is not None:
        candidates = _find_candidates(plan, resources.indexes, mention_context)
        reason = candidates.terminal_reason
        if reason is None:
            reason = _candidate_reason(
                source_kind,
                candidates.global_rows,
                candidates.source_rows,
                candidates.compatible_rows,
                plan.requested_type,
            )

    global_ids = sorted({str(row["target_id"]) for row in candidates.global_rows})
    source_ids = sorted({str(row["target_id"]) for row in candidates.source_rows})
    compatible_ids = sorted({str(row["target_id"]) for row in candidates.compatible_rows})
    link: JsonObject | None = None
    registry_entry_id: str | None = None
    usability = "not_applicable"
    visual_usability = "not_applicable"
    if reason is None:
        link, registry_entry_id, usability, visual_usability = _build_resolved_link(
            mention,
            candidates,
            plan.requested_type,
            resources,
        )

    outcome: JsonObject = {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "mention_id": mention["mention_id"],
        "mention_span_id": mention["mention_span_id"],
        "source_unit_id": mention["source_unit_id"],
        "source_kind": source_kind,
        "raw_text_sha256": mention["raw_text_sha256"],
        "reference_domain": domain,
        "raw_target_label": raw_label,
        "qualifier": plan.qualifier,
        "projected_target": plan.projected,
        "canonical_target": plan.canonical,
        "requested_target_type": plan.requested_type,
        "routed_source_ids": sorted(plan.routed_sources),
        "global_candidate_target_ids": global_ids,
        "source_candidate_target_ids": source_ids,
        "compatible_target_ids": compatible_ids,
        "outcome": "resolved" if link is not None else "terminal_nonlink",
        "terminal_reason": reason,
        "link_id": link["link_id"] if link is not None else None,
        "task04a_registry_entry_id": registry_entry_id,
        "task04a_usability": usability,
        "visual_evidence_usability": visual_usability,
    }
    outcome["outcome_id"] = f"outcomev1-{canonical_json_sha256(outcome)}"
    return outcome, link


def _find_candidates(
    plan: _QueryPlan,
    indexes: _TargetIndexes,
    context: _MentionContext,
) -> _CandidateRows:
    """Apply exact lookup first, then at most one qualified fallback."""
    if plan.canonical is None:
        return _CandidateRows()
    global_rows = indexes.by_key.get(plan.canonical, ())
    source_rows = [row for row in global_rows if row["source_id"] in plan.routed_sources]
    compatible_rows = [row for row in source_rows if row["target_type"] == plan.requested_type]
    if {str(row["target_id"]) for row in compatible_rows}:
        return _CandidateRows(global_rows, source_rows, compatible_rows)

    fallback_rows, resolver_rule, terminal_reason = _fallback_candidates(plan, indexes, context)
    if not fallback_rows:
        return _CandidateRows(
            global_rows,
            source_rows,
            compatible_rows,
            resolver_rule,
            terminal_reason,
        )
    fallback_sources = [row for row in fallback_rows if row["source_id"] in plan.routed_sources]
    fallback_compatible = [
        row for row in fallback_sources if row["target_type"] == plan.requested_type
    ]
    return _CandidateRows(
        fallback_rows,
        fallback_sources,
        fallback_compatible,
        resolver_rule,
        terminal_reason,
    )


def _build_resolved_link(
    mention: Mapping[str, Any],
    candidates: _CandidateRows,
    requested_type: str | None,
    resources: _ResolutionResources,
) -> tuple[JsonObject, str, str, str]:
    """Build one link and its independent source and visual usability values."""
    compatible_ids = sorted({str(row["target_id"]) for row in candidates.compatible_rows})
    target_id = compatible_ids[0]
    target_source = str(candidates.compatible_rows[0]["source_id"])
    entry = resources.registry.get(target_source)
    if entry is None:
        raise ValueError(f"resolved target source lacks Task 04A usability: {target_source}")
    registry_entry_id = str(entry["entry_id"])
    usability = map_task04a_usability(entry)
    visual_usability = map_visual_usability(requested_type, usability)
    link: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "draft_eir_link",
        "source_unit_id": mention["source_unit_id"],
        "mention_id": mention["mention_id"],
        "target_id": target_id,
        "task04d_handoff_id": _activity_input_identity(resources.activity, "task04d_handoff"),
        "task04a_registry_id": _activity_input_identity(resources.activity, "task04a_registry"),
        "activity_id": resources.activity["activity_id"],
        "resolver_rule": candidates.resolver_rule,
        "task04a_usability": usability,
    }
    link["link_id"] = build_record_id(link)
    return link, registry_entry_id, usability, visual_usability


def _activity_input_identity(activity: JsonObject, role: str) -> str:
    """Return one activity input identity with an actionable cardinality error."""
    matches = [item for item in activity.get("input_refs", []) if item.get("role") == role]
    if len(matches) != 1:
        raise ValueError(f"Task 05F activity must contain exactly one {role!r} input")
    return str(matches[0]["identity"])


def _query_plan(
    raw_label: str,
    domain: str,
    catalog_aliases: Mapping[str, set[str]],
    catalog_designators: Mapping[str, set[str]],
) -> _QueryPlan:
    """Project qualifiers, then route by exact or structured appendix identity."""
    if domain == "appendix_q":
        return _QueryPlan(terminal_reason="appendix_q_verification_required")
    qualifier = next((value for value in QUALIFIERS if raw_label.startswith(value)), None)
    if qualifier is None:
        return _QueryPlan(terminal_reason="unsupported_reference_form")
    projected = raw_label.removeprefix(qualifier)
    canonical = normalize_alias(projected)
    form = _TARGET_FORM.match(canonical)
    if form is not None:
        return _QueryPlan(
            qualifier=qualifier,
            projected=projected,
            canonical=canonical,
            requested_type=TARGET_TYPES[form.group(1)],
            routed_sources=frozenset({"deir_main"}),
        )
    if not canonical.startswith("appendix "):
        return _QueryPlan(
            qualifier=qualifier,
            projected=projected,
            canonical=canonical,
            terminal_reason="unsupported_reference_form",
        )
    sources = frozenset(catalog_aliases.get(canonical, set()))
    if not sources:
        designator = _appendix_designator(canonical)
        if designator is not None:
            sources = frozenset(catalog_designators.get(designator, set()))
    return _QueryPlan(
        qualifier=qualifier,
        projected=projected,
        canonical=canonical,
        requested_type="document",
        routed_sources=sources,
        terminal_reason=None if sources else "appendix_source_route_absent",
    )


def _target_indexes(
    target_rows: Sequence[JsonObject],
    direct_section_children: Mapping[str, Sequence[str]] | None = None,
) -> _TargetIndexes:
    """Derive exact and hierarchy-aware indexes without inventing targets."""
    by_key: dict[str, list[JsonObject]] = defaultdict(list)
    by_identifier: dict[tuple[str, str, str], list[JsonObject]] = defaultdict(list)
    by_target: dict[str, list[JsonObject]] = defaultdict(list)
    by_hierarchical_subsection: dict[tuple[str, str, str], list[JsonObject]] = defaultdict(list)
    documents_by_source: dict[str, list[JsonObject]] = defaultdict(list)
    for row in target_rows:
        lookup_key = str(row["lookup_key"])
        source_id = str(row["source_id"])
        target_type = str(row["target_type"])
        by_key[lookup_key].append(row)
        by_target[str(row["target_id"])].append(row)
        identifier = _leading_identifier(lookup_key, target_type)
        if identifier is not None:
            by_identifier[(source_id, target_type, identifier)].append(row)
        if target_type == "document":
            documents_by_source[source_id].append(row)
    by_hierarchical_subsection = _hierarchical_subsection_index(
        by_target,
        direct_section_children or {},
    )
    return _TargetIndexes(
        by_key,
        by_identifier,
        by_hierarchical_subsection,
        documents_by_source,
    )


def _hierarchical_subsection_index(
    rows_by_target: Mapping[str, Sequence[JsonObject]],
    direct_section_children: Mapping[str, Sequence[str]],
) -> dict[tuple[str, str, str], list[JsonObject]]:
    """Index exact alphabetic children beneath independently accepted parents."""
    indexed: dict[tuple[str, str, str], list[JsonObject]] = defaultdict(list)
    for parent_id, child_ids in (direct_section_children or {}).items():
        for parent_row in rows_by_target.get(parent_id, ()):
            if parent_row["target_type"] != "section":
                continue
            parent_identifier = _leading_identifier(str(parent_row["lookup_key"]), "section")
            if parent_identifier is None:
                continue
            source_id = str(parent_row["source_id"])
            for child_id in child_ids:
                for child_row in rows_by_target.get(str(child_id), ()):
                    if child_row["target_type"] != "section" or child_row["source_id"] != source_id:
                        continue
                    match = _CHILD_SECTION_DESIGNATOR.match(str(child_row["lookup_key"]))
                    if match is not None:
                        indexed[(source_id, parent_identifier, match.group(1))].append(child_row)
    return indexed


def _leading_identifier(lookup_key: str, target_type: str) -> str | None:
    """Return an independently published chapter, section, or table identifier."""
    pattern = _SECTION_ALIAS_IDENTIFIER if target_type == "section" else _TABLE_ALIAS_IDENTIFIER
    if target_type not in {"section", "table"}:
        return None
    match = pattern.match(lookup_key)
    if match is None:
        return None
    if target_type == "section" and match.group(1) is not None:
        return f"chapter {match.group(2)}"
    return match.group(2) if target_type == "section" else match.group(1)


def _fallback_candidates(
    plan: _QueryPlan,
    indexes: _TargetIndexes,
    context: _MentionContext,
) -> tuple[list[JsonObject], str, str | None]:
    """Apply the qualified exact fallbacks in fixed order and fail closed."""
    if plan.requested_type in {"section", "table"} and plan.canonical is not None:
        subsection = _HIERARCHICAL_SUBSECTION.fullmatch(plan.canonical)
        if plan.requested_type == "section" and subsection is not None:
            parent_identifier, child_designator = subsection.groups()
            rows = [
                row
                for source_id in sorted(plan.routed_sources)
                for row in indexes.by_hierarchical_subsection.get(
                    (source_id, parent_identifier, child_designator), ()
                )
            ]
            return rows, "task05f_hierarchical_subsection_exact_v1", None
        table_separator = _TABLE_PERIOD_SEPARATOR.fullmatch(plan.canonical)
        if plan.requested_type == "table" and table_separator is not None:
            identifier = f"{table_separator.group(1)}-{table_separator.group(2)}"
            rows = _identifier_rows(plan, indexes, identifier)
            return rows, "task05f_table_separator_normalization_v1", None
        section_separator = _SECTION_HYPHEN_SEPARATOR.fullmatch(plan.canonical)
        if plan.requested_type == "section" and section_separator is not None:
            identifier = f"{section_separator.group(1)}.{section_separator.group(2)}"
            rows = _identifier_rows(plan, indexes, identifier)
            return rows, "task05f_section_separator_normalization_v1", None
        direct = _DIRECT_REFERENCE.fullmatch(plan.canonical)
        if direct is not None:
            identifier = (
                f"chapter {direct.group(2)}" if direct.group(1) == "chapter" else direct.group(2)
            )
            rows = _identifier_rows(plan, indexes, identifier)
            if len({str(row["target_id"]) for row in rows}) > 1:
                titled = _attached_title_rows(rows, plan.requested_type, identifier, context.after)
                if len({str(row["target_id"]) for row in titled}) == 1:
                    return titled, "task05f_attached_title_exact_v1", None
            rule = (
                "task05f_es_identifier_exact_v1"
                if identifier.startswith("es")
                else "task05f_leading_identifier_exact_v1"
            )
            return rows, rule, None
    if plan.requested_type == "document" and plan.routed_sources:
        if _has_attached_inner_target(context):
            return [], RESOLVER_RULE, "more_specific_appendix_target_requires_resolution"
        rows = [
            row
            for source_id in sorted(plan.routed_sources)
            for row in indexes.documents_by_source.get(source_id, ())
        ]
        return rows, "task05f_unique_appendix_document_v1", None
    return [], RESOLVER_RULE, None


def _identifier_rows(
    plan: _QueryPlan,
    indexes: _TargetIndexes,
    identifier: str,
) -> list[JsonObject]:
    """Return all same-source, same-type rows for one normalized identifier."""
    if plan.requested_type is None:
        return []
    return [
        row
        for source_id in sorted(plan.routed_sources)
        for row in indexes.by_identifier.get((source_id, plan.requested_type, identifier), ())
    ]


def _attached_title_rows(
    rows: Sequence[JsonObject],
    target_type: str,
    identifier: str,
    after: str,
) -> list[JsonObject]:
    """Select rows whose complete published alias is attached after one comma."""
    normalized_after = normalize_alias(after)
    prefix = identifier if target_type == "section" else f"table {identifier}"
    matched: list[tuple[int, JsonObject]] = []
    for row in rows:
        lookup_key = str(row["lookup_key"])
        if not lookup_key.startswith(f"{prefix} "):
            continue
        title = lookup_key[len(prefix) :].strip()
        pattern = re.compile(rf"^,\s*{re.escape(title)}(?=$|[,.();:]|\s)")
        if title and pattern.match(normalized_after):
            matched.append((len(title), row))
    if not matched:
        return []
    longest = max(length for length, _row in matched)
    return [row for length, row in matched if length == longest]


def _has_attached_inner_target(context: _MentionContext) -> bool:
    """Prevent an outer document link from replacing an attached inner citation."""
    return (
        _INNER_TARGET.search(context.before) is not None
        or _INNER_TARGET.search(context.after) is not None
    )


def _mention_contexts(records: Sequence[JsonObject]) -> dict[str, _MentionContext]:
    """Derive bounded same-sentence context from accepted page and span records."""
    pages = {
        str(record["page_id"]): str(record["raw_text"])
        for record in records
        if record.get("record_type") == "page"
    }
    contexts: dict[str, _MentionContext] = {}
    for record in records:
        if record.get("record_type") != "source_span":
            continue
        fragments = cast(list[JsonObject], record.get("fragments", []))
        if not fragments:
            continue
        first = fragments[0]
        last = fragments[-1]
        first_text = pages.get(str(first["page_id"]), "")
        last_text = pages.get(str(last["page_id"]), "")
        before = first_text[max(0, int(first["text_start"]) - 180) : int(first["text_start"])]
        after = last_text[int(last["text_end"]) : int(last["text_end"]) + 180]
        contexts[str(record["span_id"])] = _MentionContext(
            before=_same_sentence_before(before),
            after=_same_sentence_after(after),
        )
    return contexts


def _same_sentence_before(value: str) -> str:
    """Keep text after the nearest strong sentence boundary."""
    parts = re.split(r"[.!?;]\s+", value)
    return parts[-1] if parts else value


def _same_sentence_after(value: str) -> str:
    """Keep text before the nearest strong sentence boundary."""
    match = re.search(r"[.!?;](?:\s|$)", value)
    return value[: match.start()] if match is not None else value


def _appendix_designator(value: str, *, allow_catalog_suffix: bool = False) -> str | None:
    """Parse one top-level appendix letter and optional numeric suffix."""
    match = _APPENDIX_DESIGNATOR.match(value)
    if match is None or (not allow_catalog_suffix and match.end() != len(value)):
        return None
    suffix = f":{int(match.group(2))}" if match.group(2) is not None else ""
    return f"appendix:{match.group(1)}{suffix}"


def _candidate_reason(
    source_kind: str,
    global_rows: Sequence[JsonObject],
    source_rows: Sequence[JsonObject],
    compatible_rows: Sequence[JsonObject],
    requested_type: str | None,
) -> str | None:
    """Classify exact candidates after source and type filtering."""
    target_ids = {str(row["target_id"]) for row in compatible_rows}
    if source_kind == "comment":
        return "comment_authored_reference_no_official_response_link"
    if len(target_ids) == 1:
        return None
    if len(target_ids) > 1:
        return "exact_target_collision"
    if source_rows:
        return "target_type_incompatible"
    if global_rows:
        return "exact_alias_only_outside_routed_source"
    if requested_type == "figure":
        return "exact_figure_target_absent"
    return "exact_target_absent"


def map_task04a_usability(entry: Mapping[str, Any] | None) -> str:
    """Map one explicit Task 04A source disposition into 05F link usability."""
    if entry is None:
        return "not_applicable"
    status = entry.get("status")
    if status == "eligible":
        return "usable"
    if status in {"eligible_with_warning", "usable_with_limitation", "limited"}:
        return "usable_with_warning"
    if status in {"ineligible", "repair_required", "unresolved", "excluded"}:
        return "unusable"
    if status in {"not_applicable", "not_evaluated"}:
        return "not_applicable"
    raise ValueError(f"unsupported Task 04A usability disposition: {status!r}")


def map_visual_usability(target_type: str | None, task04a_usability: str) -> str:
    """Keep figure visual review independent from structural link usability."""
    if target_type != "figure":
        return "not_applicable"
    if task04a_usability == "unusable":
        return "unusable"
    return "not_reviewed"


def _catalog_aliases(catalog: JsonObject) -> dict[str, set[str]]:
    """Index only exact aliases declared by the accepted source-family catalog."""
    aliases: dict[str, set[str]] = defaultdict(set)
    for entry in cast(list[JsonObject], catalog.get("sources", [])):
        source_id = str(cast(JsonObject, entry["source"])["source_id"])
        for alias in cast(list[str], entry.get("reference_aliases", [])):
            aliases[normalize_alias(alias)].add(source_id)
    return aliases


def _catalog_designators(catalog: JsonObject) -> dict[str, set[str]]:
    """Index structured appendix designators while retaining multipart cardinality."""
    designators: dict[str, set[str]] = defaultdict(set)
    for entry in cast(list[JsonObject], catalog.get("sources", [])):
        source_id = str(cast(JsonObject, entry["source"])["source_id"])
        for alias in cast(list[str], entry.get("reference_aliases", [])):
            designator = _appendix_designator(normalize_alias(alias), allow_catalog_suffix=True)
            if designator is not None:
                designators[designator].add(source_id)
    return designators


def _diagnostic(activity: JsonObject, outcome: JsonObject) -> JsonObject:
    """Create one schema-valid terminal diagnostic for one nonlink outcome."""
    reason = str(outcome["terminal_reason"])
    code = {
        "appendix_q_verification_required": "appendix_q_verification_required",
        "exact_target_collision": "ambiguous_reference",
        "unsupported_reference_form": "unsupported_reference_form",
        "comment_authored_reference_no_official_response_link": "unsupported_reference_form",
        "target_type_incompatible": "unsupported_reference_form",
    }.get(reason, "unresolved_target")
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "diagnostic",
        "stage": "05f",
        "activity_id": activity["activity_id"],
        "code": code,
        "severity": "info",
        "terminal": True,
        "subject_ids": [outcome["mention_id"]],
        "evidence_ids": [outcome["mention_span_id"]],
        "message": f"Task 05F exact reference outcome: {reason}",
    }
    record["diagnostic_id"] = build_record_id(record)
    return record


def _activity_record(
    spec: ResponseReferenceRunSpecV5, config_sha256: str, records_schema_path: Path
) -> JsonObject:
    """Bind 05D, 05E, 04A, and 04D without hashing their large payloads."""
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05f",
        "source_id": None,
        "page_ranges": [],
        "config_sha256": config_sha256,
        "schema_sha256": hashlib.sha256(records_schema_path.read_bytes()).hexdigest(),
        "code_sha256": spec.producer_code_sha256,
        "tool_versions": {"resolver_policy": RESOLVER_RULE},
        "input_refs": [
            {
                "role": "task04a_registry",
                "identity": spec.task04.task04a_review_id,
                "authority": "artifact_root",
                "path": (spec.task04.task04a_gate_d_root / "usability_registry.json").as_posix(),
            },
            {
                "role": "task04d_handoff",
                "identity": spec.task04.task04d_handoff_id,
                "authority": "artifact_root",
                "path": (
                    spec.task04.task04d_handoff_root / "records/completion_record.json"
                ).as_posix(),
            },
            {
                "role": "task05d_completion",
                "identity": spec.accepted_task05d.completion_id,
                "authority": "artifact_root",
                "path": (
                    spec.accepted_task05d.candidate_root / "records/stage_completion.json"
                ).as_posix(),
            },
            {
                "role": "task05e_completion",
                "identity": spec.accepted_task05e.completion_id,
                "authority": "artifact_root",
                "path": (
                    spec.accepted_task05e.candidate_root / "records/stage_completion.json"
                ).as_posix(),
            },
        ],
    }
    record["activity_id"] = build_record_id(record)
    return record


def _validate_population(mentions: Sequence[JsonObject], units: Mapping[str, JsonObject]) -> None:
    """Fail closed unless the accepted mention population matches the contract."""
    domains = Counter(str(item["reference_domain"]) for item in mentions)
    draft_kinds = Counter(
        str(units[str(item["source_unit_id"])]["unit_kind"])
        for item in mentions
        if item["reference_domain"] == "draft_eir"
    )
    if dict(domains) != EXPECTED_ALL_DOMAINS or dict(draft_kinds) != EXPECTED_DRAFT_AUTHORSHIP:
        raise ValueError(
            "Task 05F population mismatch: "
            f"domains={dict(domains)}, draft_authorship={dict(draft_kinds)}"
        )


def _validate_outcomes(outcomes: Sequence[JsonObject], schema: JsonObject) -> None:
    """Validate every outcome and enforce one-to-one mention accounting."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for outcome in outcomes:
        validator.validate(outcome)
    mention_ids = [str(item["mention_id"]) for item in outcomes]
    if len(mention_ids) != 511 or len(set(mention_ids)) != 511:
        raise ValueError("Task 05F outcomes do not account for 511 unique mentions")


def _validate_record_shapes(
    records: Sequence[JsonObject],
    schema: JsonObject,
) -> None:
    """Validate shared-schema records and their content-derived identities."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for record in records:
        validator.validate(record)
        if _record_id(record) != build_record_id(record):
            raise ValueError(f"Task 05F derived record ID mismatch: {_record_id(record)}")


def _validate_provenance(
    links: Sequence[JsonObject],
    diagnostics: Sequence[JsonObject],
    source_records: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
) -> None:
    """Validate link and diagnostic provenance against accepted 05D records."""
    mentions = {
        str(record["mention_id"]): record
        for record in source_records
        if record.get("record_type") == "reference_mention"
    }
    spans = {
        str(record["span_id"])
        for record in source_records
        if record.get("record_type") == "source_span"
    }
    for link in links:
        mention = mentions.get(str(link["mention_id"]))
        if (
            mention is None
            or mention.get("reference_domain") != "draft_eir"
            or mention.get("source_unit_id") != link.get("source_unit_id")
            or str(link["source_unit_id"]) not in units
        ):
            raise ValueError("Task 05F link provenance differs from its accepted mention")
    for diagnostic in diagnostics:
        if (
            len(diagnostic["subject_ids"]) != 1
            or str(diagnostic["subject_ids"][0]) not in mentions
            or len(diagnostic["evidence_ids"]) != 1
            or str(diagnostic["evidence_ids"][0]) not in spans
        ):
            raise ValueError("Task 05F diagnostic provenance is incomplete")


def _record_id(record: Mapping[str, Any]) -> str:
    """Return the identity field for one shared-schema record."""
    fields = {
        "activity": "activity_id",
        "draft_eir_link": "link_id",
        "diagnostic": "diagnostic_id",
        "managed_file_inventory": "inventory_id",
    }
    return str(record[fields[str(record["record_type"])]])


def _indexes(
    outcomes: Sequence[JsonObject], links: Sequence[JsonObject]
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Derive ID-only forward and reverse indexes from the canonical link list."""
    forward = [
        {"mention_id": item["mention_id"], "link_id": item["link_id"]}
        for item in sorted(outcomes, key=lambda row: str(row["mention_id"]))
    ]
    by_target: dict[str, list[str]] = defaultdict(list)
    for link in links:
        by_target[str(link["target_id"])].append(str(link["link_id"]))
    reverse = [
        {"target_id": target_id, "link_ids": sorted(link_ids)}
        for target_id, link_ids in sorted(by_target.items())
    ]
    linked_ids = {str(item["link_id"]) for item in links}
    indexed_ids = {str(item["link_id"]) for item in forward if item["link_id"] is not None}
    reverse_ids = {str(link_id) for item in reverse for link_id in item["link_ids"]}
    if indexed_ids != linked_ids or reverse_ids != linked_ids:
        raise ValueError("Task 05F forward/reverse indexes do not close the link set")
    return forward, reverse


def _census(
    outcomes: Sequence[JsonObject],
    links: Sequence[JsonObject],
    diagnostics: Sequence[JsonObject],
    target_counts: Mapping[str, int],
    activity: JsonObject,
) -> JsonObject:
    """Build the complete qualified-rule population and failure census."""
    reasons = Counter(
        str(item["terminal_reason"]) for item in outcomes if item["outcome"] == "terminal_nonlink"
    )
    failure_classes = [
        "appendix_q_verification_required",
        "appendix_source_route_absent",
        "comment_authored_reference_no_official_response_link",
        "exact_figure_target_absent",
        "exact_target_absent",
        "exact_target_collision",
        "target_type_incompatible",
        "unsupported_reference_form",
        "exact_alias_only_outside_routed_source",
        "more_specific_appendix_target_requires_resolution",
        "upstream_source_identity_repair_required",
    ]
    usability = Counter(str(item["task04a_usability"]) for item in links)
    visual = Counter(str(item["visual_evidence_usability"]) for item in outcomes)
    target_types = Counter(
        str(item["requested_target_type"])
        for item in outcomes
        if item["requested_target_type"] is not None
    )
    qualifier_counts = Counter(
        repr(item["qualifier"]) for item in outcomes if item["reference_domain"] == "draft_eir"
    )
    counts = {
        "reference_mentions": len(outcomes),
        "draft_eir_mentions": sum(item["reference_domain"] == "draft_eir" for item in outcomes),
        "appendix_q_mentions": sum(item["reference_domain"] == "appendix_q" for item in outcomes),
        "resolved_links": len(links),
        "terminal_nonlinks": len(diagnostics),
        "comment_authored_draft_eir_mentions": sum(
            item["reference_domain"] == "draft_eir" and item["source_kind"] == "comment"
            for item in outcomes
        ),
    }
    if counts["reference_mentions"] != counts["resolved_links"] + counts["terminal_nonlinks"]:
        raise ValueError("Task 05F census does not close every reference mention")
    return {
        "schema_version": RULES_SCHEMA_VERSION,
        "status": "qualified_rules_complete_review_required",
        "activity_id": activity["activity_id"],
        "counts": counts,
        "domain_population_census": {
            key: sum(item["reference_domain"] == key for item in outcomes)
            for key in ("draft_eir", "appendix_q", "final_eir", "external", "unknown")
        },
        "draft_eir_authorship_census": {
            key: sum(
                item["reference_domain"] == "draft_eir" and item["source_kind"] == key
                for item in outcomes
            )
            for key in ("response", "general_response", "comment")
        },
        "failure_census": {key: reasons.get(key, 0) for key in failure_classes},
        "requested_target_type_census": dict(sorted(target_types.items())),
        "task04a_link_usability_census": {
            key: usability.get(key, 0)
            for key in ("usable", "usable_with_warning", "unusable", "not_applicable")
        },
        "visual_evidence_usability_census": {
            key: visual.get(key, 0)
            for key in (
                "usable",
                "usable_with_warning",
                "unusable",
                "not_reviewed",
                "not_applicable",
            )
        },
        "target_index_type_census": dict(sorted(target_counts.items())),
        "qualifier_census": dict(sorted(qualifier_counts.items())),
        "collision_mention_ids": sorted(
            str(item["mention_id"])
            for item in outcomes
            if item["terminal_reason"] == "exact_target_collision"
        ),
        "outside_routed_source_mention_ids": sorted(
            str(item["mention_id"])
            for item in outcomes
            if item["terminal_reason"] == "exact_alias_only_outside_routed_source"
        ),
        "terminal_publication_authorized": False,
        "source_pdf_accessed": False,
        "large_upstream_payloads_hashed": False,
    }


def _inventory_record(activity: JsonObject, payloads: Mapping[str, bytes]) -> JsonObject:
    """Create one compact inventory over newly authored qualified-rule bytes."""
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "managed_file_inventory",
        "stage": "05f",
        "activity_id": activity["activity_id"],
        "dependencies": activity["input_refs"],
        "files": [
            {
                "authority": "bundle",
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_size": len(content),
            }
            for path, content in sorted(payloads.items())
        ],
    }
    record["inventory_id"] = build_record_id(record)
    return record


def _receipt(
    activity: JsonObject,
    census: JsonObject,
    results: _ResolutionResults,
    payloads: Mapping[str, bytes],
) -> JsonObject:
    """Describe qualified-rule bytes without creating completion state."""
    semantic_digest = canonical_json_sha256(
        {
            "outcomes": results.outcomes,
            "links": results.links,
            "diagnostics": results.diagnostics,
        }
    )
    return {
        "schema_version": RULES_SCHEMA_VERSION,
        "status": "qualified_rules_complete_review_required",
        "activity_id": activity["activity_id"],
        "semantic_digest": semantic_digest,
        "census_digest": canonical_json_sha256(census),
        "files": [
            {"path": path, "byte_size": len(content), "sha256": hashlib.sha256(content).hexdigest()}
            for path, content in sorted(payloads.items())
        ],
        "completion_written": False,
        "terminal_publication_authorized": False,
        "source_pdf_accessed": False,
        "large_upstream_payloads_hashed": False,
    }


def _publish_candidate(
    candidate_root: Path, payloads: Mapping[str, bytes], receipt: JsonObject
) -> None:
    """Publish atomically, reuse identical output, and reject partial state."""
    expected_receipt = json_bytes(receipt)
    if candidate_root.exists():
        _verify_existing_candidate(candidate_root, payloads, expected_receipt)
        return
    staging = candidate_root.parent / f".{candidate_root.name}.staging"
    if staging.exists():
        raise ValueError(f"stale Task 05F staging directory exists: {staging}")
    staging.mkdir(parents=True)
    try:
        for relative_path, content in sorted(payloads.items()):
            publish_bytes_no_clobber(staging / relative_path, content)
        publish_bytes_no_clobber(staging / "records/rule_receipt.json", expected_receipt)
        staging.rename(candidate_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    if (candidate_root / "records/stage_completion.json").exists():
        raise ValueError("Task 05F qualified rules must not publish stage completion")


def _verify_existing_candidate(
    candidate_root: Path,
    payloads: Mapping[str, bytes],
    expected_receipt: bytes,
) -> None:
    """Require exact managed files and bytes before reusing a candidate."""
    receipt_path = candidate_root / "records/rule_receipt.json"
    if not receipt_path.is_file():
        raise ValueError("existing Task 05F candidate is partial: receipt is absent")
    expected_paths = {*payloads, "records/rule_receipt.json"}
    actual_paths = {
        path.relative_to(candidate_root).as_posix()
        for path in candidate_root.rglob("*")
        if path.is_file()
    }
    if actual_paths != expected_paths:
        raise ValueError(
            "existing Task 05F candidate file set differs: "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"unexpected={sorted(actual_paths - expected_paths)}"
        )
    for relative_path, content in payloads.items():
        path = candidate_root / relative_path
        if path.read_bytes() != content:
            raise ValueError(f"existing Task 05F candidate differs: {relative_path}")
    if receipt_path.read_bytes() != expected_receipt:
        raise ValueError("existing Task 05F candidate receipt differs")


def _validate_acceptance(record: JsonObject, *, expected: Mapping[str, Any]) -> None:
    """Require exact pointer fields and its content-derived acceptance ID."""
    _require_fields(record, expected, "acceptance pointer")
    payload = dict(record)
    observed = payload.pop("acceptance_id", None)
    if observed != f"acceptancev1-{canonical_json_sha256(payload)}":
        raise ValueError("acceptance pointer ID does not match its content")


def _require_fields(record: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    mismatches = {
        key: {"expected": value, "observed": record.get(key)}
        for key, value in expected.items()
        if record.get(key) != value
    }
    if mismatches:
        raise ValueError(f"{label} binding mismatch: {mismatches}")


def _verify_recorded_size(
    inventory: JsonObject, relative_path: str, path: Path, label: str
) -> None:
    entry = _inventory_entry(inventory, relative_path, label)
    if path.stat().st_size != entry.get("byte_size"):
        raise ValueError(f"{label} recorded payload size mismatch: {relative_path}")


def _inventory_entry(inventory: JsonObject, relative_path: str, label: str) -> JsonObject:
    """Return one inventory entry with an actionable cardinality error."""
    files = cast(list[JsonObject], inventory.get("files", []))
    matches = [item for item in files if item.get("path") == relative_path]
    if len(matches) != 1:
        raise ValueError(f"{label} must inventory {relative_path!r} exactly once")
    return matches[0]


def _sha256_small(path: Path) -> str:
    """Hash only metadata inputs that are explicitly small in the 05F contract."""
    if path.stat().st_size > 100_000:
        raise ValueError(f"refusing to hash non-small upstream file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contained(root: Path, relative: Path, label: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.exists():
        raise ValueError(f"{label} is missing or escapes the artifact root")
    return path


def _binding_path(spec: ResponseReferenceRunSpecV5, role: str) -> Path:
    """Return one repository binding with an actionable cardinality error."""
    matches = [item.path for item in spec.repository_bindings if item.role == role]
    if len(matches) != 1:
        raise ValueError(f"Task 05F requires exactly one repository binding for {role!r}")
    return matches[0]


__all__ = [
    "build_qualified_reference_rules",
    "map_task04a_usability",
    "map_visual_usability",
]
