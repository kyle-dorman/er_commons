"""Source-free exact-only relationship baseline for Task 05E Gate 1."""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    jsonl_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    read_jsonl,
)
from er_commons.response_inventory.acceptance import validate_task05d_candidate
from er_commons.response_inventory.contract import (
    build_record_id,
    semantic_bundle_digest,
    validate_record_bundle,
)
from er_commons.response_inventory.run_spec import (
    ResponseRelationshipReviewRunSpecV4,
    ResponseRelationshipRunSpecV3,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)

type JsonObject = dict[str, Any]
type EdgeKey = tuple[str, str, str]
type EdgeRules = dict[EdgeKey, dict[str, str]]

SCHEMA_VERSION = "er_commons.response_inventory.v1"
BASELINE_SCHEMA_VERSION = "er_commons.task05e.exact_baseline.v1"
REVIEW_PASS_SCHEMA_VERSION = "er_commons.task05e.bounded_review.v1"
EXACT_MENTION_RULE = "exact_official_label_v1"
EXACT_MEMBERSHIP_RULE = "exact_comment_label_v1"
EXACT_DIRECT_PAIR_RULE = "exact_typed_label_suffix_v1"
CASE_RULE = "casefold_official_label_v1"
WHITESPACE_RULE = "collapsed_whitespace_official_label_v1"
WHITESPACE_CASE_RULE = "collapsed_whitespace_casefold_official_label_v1"
CONTROL_SEPARATOR_RULE = "u0002_separator_to_hyphen_reference_mention_v1"
CONTROL_SEPARATOR_CASE_RULE = "u0002_separator_to_hyphen_casefold_reference_mention_v1"
TERMINAL_PERIOD_RULE = "one_terminal_period_official_label_v1"
TERMINAL_PERIOD_CASE_RULE = "one_terminal_period_casefold_official_label_v1"
TERMINAL_PERIOD_WHITESPACE_RULE = "collapsed_whitespace_one_terminal_period_v1"
TERMINAL_PERIOD_WHITESPACE_CASE_RULE = "collapsed_whitespace_one_terminal_period_casefold_v1"
RUNNING_HEADER_RULE = "running_header_mention_classification_v1"
RESPONSE_SECTION_RULE = "response_section_heading_classification_v1"
TYPED_MEMBERSHIP_RULE = "typed_comment_suffix_v1"
MEMBERSHIP_ALIAS_RULE = "reviewed_o_osec_to_m_osec_membership_alias_v1"

_RANGE_TOKEN = re.compile(
    r"(?:[0-9].*\b(?:through|to)\b|\b(?:through|to)\b.*[0-9]|[0-9][\-\u2013\u2014][0-9])",
    re.IGNORECASE,
)
_LETTER_SUFFIX = re.compile(r"^(?P<prefix>(?:Comment|Response) .+?[0-9])(?P<suffix>[A-Za-z])$")
_OBVIOUS_PROSE_TARGETS = frozenset({"response is", "response to", "response the"})
_RUNNING_HEADER_RE = re.compile(
    r"^13\.2\. General Responses to Comments Raised in Multiple Letters \| "
    r"13\.2\.[0-9]+\. General Response [0-9]+:"
)
_RESPONSE_SECTION_MENTION_RE = re.compile(r"Response\r?\n[A-Za-z]+", re.IGNORECASE)
_ORDINARY_RESPONSE_PROSE_RE = re.compile(r"response [A-Za-z]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class _ResolutionPolicy:
    """Small immutable switchboard for exact or reviewed bounded resolution."""

    name: str
    normalize_case: bool = False
    collapse_whitespace: bool = False
    recover_control_separator: bool = False
    classify_self_mentions: bool = False
    allow_general_response_response: bool = False
    allow_general_response_general_response: bool = False
    classify_running_headers: bool = False
    classify_response_section_headings: bool = False
    classify_ordinary_response_prose: bool = False
    strip_one_terminal_period: bool = False
    terminal_unresolved_reference_labels: frozenset[str] = frozenset()
    terminal_unpaired_source_labels: frozenset[str] = frozenset()
    typed_memberships: bool = False
    membership_aliases: Mapping[str, str] | None = None


_EXACT_POLICY = _ResolutionPolicy(name="exact_official_label_v1")


def build_exact_relationship_baseline(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
) -> JsonObject:
    """Build or byte-verify the nonterminal exact-only Gate 1 baseline."""
    loaded, config_sha256 = load_response_inventory_run_spec(run_spec_path)
    if not isinstance(loaded, ResponseRelationshipRunSpecV3):
        raise ValueError("relationship baseline requires a Task 05E v3 run specification")
    verify_repository_bindings(loaded, repository_root)
    records_schema_path = repository_root / _binding_path(loaded, "response_record_schema")
    records_schema = read_json_object(records_schema_path)
    upstream_records, acceptance = _load_accepted_task05d(loaded, artifact_root, records_schema)
    activity = _activity_record(loaded, config_sha256, records_schema_path)
    built = _build_records(upstream_records, activity)
    derived_records = [
        activity,
        *built["edges"],
        *built["diagnostics"],
        *built["views"],
    ]
    validate_record_bundle([*upstream_records, *derived_records], records_schema)

    census = _census_report(
        loaded,
        activity,
        acceptance,
        upstream_records,
        cast(list[JsonObject], built["edges"]),
        cast(list[JsonObject], built["diagnostics"]),
        cast(list[JsonObject], built["views"]),
        cast(list[JsonObject], built["mention_outcomes"]),
        cast(list[JsonObject], built["membership_outcomes"]),
        cast(list[JsonObject], built["direct_pair_outcomes"]),
    )
    payloads = {
        "records/activity.json": json_bytes(activity),
        "graph/exact_edges.jsonl": jsonl_bytes(cast(list[JsonObject], built["edges"])),
        "diagnostics/individual_diagnostics.jsonl": jsonl_bytes(
            cast(list[JsonObject], built["diagnostics"])
        ),
        "diagnostics/exact_baseline_census.json": json_bytes(census),
        "review_views/exact_review_views.jsonl": jsonl_bytes(
            cast(list[JsonObject], built["views"])
        ),
    }
    receipt = _baseline_receipt(activity, census, derived_records, payloads)
    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    relative_root = (
        loaded.output_policy.artifact_relative_root
        / loaded.output_policy.baseline_namespace_template.format(activity_hash=activity_hash)
    )
    baseline_root = (artifact_root / relative_root).resolve()
    if not baseline_root.is_relative_to(artifact_root.resolve()):
        raise ValueError("Task 05E baseline path escapes the artifact root")
    for relative_path, content in sorted(payloads.items()):
        publish_bytes_no_clobber(baseline_root / relative_path, content)
    publish_bytes_no_clobber(baseline_root / "records/baseline_receipt.json", json_bytes(receipt))
    _verify_published_baseline(baseline_root, payloads, receipt)
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "status": "exact_baseline_complete_review_required",
        "activity_id": activity["activity_id"],
        "baseline_root": baseline_root.as_posix(),
        "semantic_digest": receipt["semantic_digest"],
        "counts": census["counts"],
        "mention_failure_categories": census["mention_failure_categories"],
        "gate2_authorized": False,
        "source_pdf_accessed": False,
    }


def build_bounded_relationship_review(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
) -> JsonObject:
    """Replay only accepted bounded rules into a nonterminal Gate 2 review pass."""
    loaded, config_sha256 = load_response_inventory_run_spec(run_spec_path)
    if not isinstance(loaded, ResponseRelationshipReviewRunSpecV4):
        raise ValueError("bounded relationship review requires a Task 05E v4 run specification")
    verify_repository_bindings(loaded, repository_root)
    records_schema_path = repository_root / _binding_path(loaded, "response_record_schema")
    records_schema = read_json_object(records_schema_path)
    upstream_records, acceptance = _load_accepted_task05d(loaded, artifact_root, records_schema)
    gate1_census = _load_gate1_census(loaded, artifact_root)
    activity = _review_activity_record(loaded, config_sha256, records_schema_path)
    policy = _ResolutionPolicy(
        name="reviewed_bounded_rules_v1",
        normalize_case=loaded.resolution_policy.normalize_case,
        collapse_whitespace=loaded.resolution_policy.collapse_whitespace,
        recover_control_separator=(
            loaded.resolution_policy.recover_u0002_separator_in_reference_mentions
        ),
        classify_self_mentions=loaded.resolution_policy.classify_self_mentions_without_edges,
        allow_general_response_response=(
            loaded.resolution_policy.allow_general_response_response_edges
        ),
        allow_general_response_general_response=(
            loaded.resolution_policy.allow_general_response_general_response_edges
        ),
        classify_running_headers=(loaded.resolution_policy.classify_running_headers_without_edges),
        classify_response_section_headings=(
            loaded.resolution_policy.classify_response_section_headings_without_edges
        ),
        classify_ordinary_response_prose=(
            loaded.resolution_policy.classify_ordinary_response_prose_without_edges
        ),
        strip_one_terminal_period=loaded.resolution_policy.strip_one_terminal_period,
        terminal_unresolved_reference_labels=frozenset(
            loaded.resolution_policy.terminal_unresolved_reference_labels
        ),
        terminal_unpaired_source_labels=frozenset(
            loaded.resolution_policy.terminal_unpaired_source_labels
        ),
        typed_memberships=loaded.resolution_policy.typed_membership_suffix,
        membership_aliases={
            str(key): str(value)
            for key, value in loaded.resolution_policy.membership_aliases.items()
        },
    )
    built = _build_records(upstream_records, activity, policy=policy)
    derived_records = [activity, *built["edges"], *built["diagnostics"], *built["views"]]
    validate_record_bundle([*upstream_records, *derived_records], records_schema)
    census = _census_report(
        loaded,
        activity,
        acceptance,
        upstream_records,
        cast(list[JsonObject], built["edges"]),
        cast(list[JsonObject], built["diagnostics"]),
        cast(list[JsonObject], built["views"]),
        cast(list[JsonObject], built["mention_outcomes"]),
        cast(list[JsonObject], built["membership_outcomes"]),
        cast(list[JsonObject], built["direct_pair_outcomes"]),
    )
    census.update(
        {
            "schema_version": REVIEW_PASS_SCHEMA_VERSION,
            "status": "bounded_review_complete_review_required",
            "accepted_gate1": {
                "activity_id": gate1_census["activity_id"],
                "census_digest": loaded.accepted_gate1.census_digest,
            },
            "policy": loaded.resolution_policy.model_dump(mode="json"),
            "gate2_authorized": True,
        }
    )
    payloads = {
        "records/activity.json": json_bytes(activity),
        "graph/review_edges.jsonl": jsonl_bytes(cast(list[JsonObject], built["edges"])),
        "diagnostics/individual_diagnostics.jsonl": jsonl_bytes(
            cast(list[JsonObject], built["diagnostics"])
        ),
        "diagnostics/review_census.json": json_bytes(census),
        "review_views/review_views.jsonl": jsonl_bytes(cast(list[JsonObject], built["views"])),
    }
    receipt = _review_receipt(activity, census, derived_records, payloads)
    activity_hash = str(activity["activity_id"]).removeprefix("activityv1-")
    relative_root = (
        loaded.output_policy.artifact_relative_root
        / loaded.output_policy.review_namespace_template.format(activity_hash=activity_hash)
    )
    review_root = (artifact_root / relative_root).resolve()
    if not review_root.is_relative_to(artifact_root.resolve()):
        raise ValueError("Task 05E review-pass path escapes the artifact root")
    for relative_path, content in sorted(payloads.items()):
        publish_bytes_no_clobber(review_root / relative_path, content)
    publish_bytes_no_clobber(review_root / "records/review_receipt.json", json_bytes(receipt))
    _verify_published_review(review_root, payloads, receipt)
    return {
        "schema_version": REVIEW_PASS_SCHEMA_VERSION,
        "status": "bounded_review_complete_review_required",
        "activity_id": activity["activity_id"],
        "review_root": review_root.as_posix(),
        "semantic_digest": receipt["semantic_digest"],
        "counts": census["counts"],
        "mention_failure_categories": census["mention_failure_categories"],
        "gate2_authorized": True,
        "source_pdf_accessed": False,
    }


def _load_accepted_task05d(
    spec: ResponseRelationshipRunSpecV3 | ResponseRelationshipReviewRunSpecV4,
    artifact_root: Path,
    records_schema: JsonObject,
) -> tuple[list[JsonObject], JsonObject]:
    """Validate the compact acceptance and unchanged terminal 05D candidate."""
    root = artifact_root.resolve()
    accepted = spec.accepted_task05d
    candidate_root = (root / accepted.candidate_root).resolve()
    acceptance_path = (root / accepted.acceptance_path).resolve()
    if not candidate_root.is_relative_to(root) or not acceptance_path.is_relative_to(root):
        raise ValueError("accepted Task 05D paths escape the artifact root")
    validation = validate_task05d_candidate(candidate_root, root)
    expected_validation = {
        "activity_id": accepted.activity_id,
        "completion_id": accepted.completion_id,
        "inventory_id": accepted.inventory_id,
        "semantic_digest": accepted.semantic_digest,
        "working_revision": accepted.candidate_root.as_posix(),
    }
    mismatches = {
        key: {"expected": value, "observed": validation.get(key)}
        for key, value in expected_validation.items()
        if validation.get(key) != value
    }
    if mismatches:
        raise ValueError(f"accepted Task 05D candidate binding mismatch: {mismatches}")
    acceptance = read_json_object(acceptance_path)
    _validate_acceptance(acceptance, spec)
    upstream_records = [
        cast(JsonObject, record)
        for record in read_jsonl(candidate_root / "inventory/source_records.jsonl")
    ]
    validate_record_bundle(upstream_records, records_schema)
    return upstream_records, acceptance


def _load_gate1_census(
    spec: ResponseRelationshipReviewRunSpecV4, artifact_root: Path
) -> JsonObject:
    """Verify the exact Gate 1 census identity without reading any source payload."""
    root = artifact_root.resolve()
    baseline_root = (root / spec.accepted_gate1.baseline_root).resolve()
    if not baseline_root.is_relative_to(root):
        raise ValueError("accepted Gate 1 path escapes the artifact root")
    census = read_json_object(baseline_root / "diagnostics/exact_baseline_census.json")
    if census.get("activity_id") != spec.accepted_gate1.activity_id:
        raise ValueError("accepted Gate 1 activity mismatch")
    if canonical_json_sha256(census) != spec.accepted_gate1.census_digest:
        raise ValueError("accepted Gate 1 census digest mismatch")
    return census


def _validate_acceptance(
    acceptance: JsonObject,
    spec: ResponseRelationshipRunSpecV3 | ResponseRelationshipReviewRunSpecV4,
) -> None:
    """Require the adjacent pointer to designate this exact candidate for 05E."""
    accepted = spec.accepted_task05d
    expected = {
        "schema_version": "er_commons.task05d.acceptance.v1",
        "task_id": "05D",
        "status": "accepted",
        "working_revision": accepted.candidate_root.as_posix(),
        "activity_id": accepted.activity_id,
        "completion_id": accepted.completion_id,
        "inventory_id": accepted.inventory_id,
        "semantic_digest": accepted.semantic_digest,
        "acceptance_id": accepted.acceptance_id,
        "downstream_consumers": ["05E"],
    }
    mismatches = {
        key: {"expected": value, "observed": acceptance.get(key)}
        for key, value in expected.items()
        if acceptance.get(key) != value
    }
    if mismatches:
        raise ValueError(f"Task 05D acceptance pointer mismatch: {mismatches}")
    identity_payload = dict(acceptance)
    observed_id = identity_payload.pop("acceptance_id", None)
    expected_id = f"acceptancev1-{canonical_json_sha256(identity_payload)}"
    if observed_id != expected_id:
        raise ValueError("Task 05D acceptance identity does not match its content")


def _activity_record(
    spec: ResponseRelationshipRunSpecV3,
    config_sha256: str,
    records_schema_path: Path,
) -> JsonObject:
    """Bind exact policy, code, schema, and the accepted 05D completion."""
    accepted = spec.accepted_task05d
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05e",
        "source_id": None,
        "page_ranges": [],
        "config_sha256": config_sha256,
        "schema_sha256": hashlib.sha256(records_schema_path.read_bytes()).hexdigest(),
        "code_sha256": spec.producer_code_sha256,
        "tool_versions": {"resolver_policy": EXACT_MENTION_RULE},
        "input_refs": [
            {
                "role": "task05d_completion",
                "identity": accepted.completion_id,
                "authority": "artifact_root",
                "path": (accepted.candidate_root / "records/stage_completion.json").as_posix(),
            }
        ],
    }
    record["activity_id"] = build_record_id(record)
    return record


def _review_activity_record(
    spec: ResponseRelationshipReviewRunSpecV4,
    config_sha256: str,
    records_schema_path: Path,
) -> JsonObject:
    """Bind the accepted 05D/Gate 1 inputs and bounded review policy."""
    accepted = spec.accepted_task05d
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "activity",
        "stage": "05e",
        "source_id": None,
        "page_ranges": [],
        "config_sha256": config_sha256,
        "schema_sha256": hashlib.sha256(records_schema_path.read_bytes()).hexdigest(),
        "code_sha256": spec.producer_code_sha256,
        "tool_versions": {"resolver_policy": "reviewed_bounded_rules_v1"},
        "input_refs": [
            {
                "role": "task05d_completion",
                "identity": accepted.completion_id,
                "authority": "artifact_root",
                "path": (accepted.candidate_root / "records/stage_completion.json").as_posix(),
            },
            {
                "role": "task05e_gate1_census",
                "identity": spec.accepted_gate1.activity_id,
                "authority": "artifact_root",
                "path": (
                    spec.accepted_gate1.baseline_root / "diagnostics/exact_baseline_census.json"
                ).as_posix(),
            },
        ],
    }
    record["activity_id"] = build_record_id(record)
    return record


def _build_records(
    records: Sequence[JsonObject],
    activity: JsonObject,
    *,
    policy: _ResolutionPolicy = _EXACT_POLICY,
) -> JsonObject:
    """Resolve endpoints under one explicit policy and materialize deterministic records."""
    units = {
        str(record["unit_id"]): record
        for record in records
        if record.get("record_type") == "source_unit"
    }
    markers = {
        str(record["marker_id"]): record
        for record in records
        if record.get("record_type") == "marker_candidate"
    }
    mentions = sorted(
        (
            record
            for record in records
            if record.get("record_type") == "reference_mention"
            and record.get("reference_domain") == "intra_volume"
        ),
        key=lambda record: str(record["mention_id"]),
    )
    memberships = sorted(
        (record for record in records if record.get("record_type") == "membership_claim"),
        key=lambda record: str(record["membership_id"]),
    )
    spans = {
        str(record["span_id"]): record
        for record in records
        if record.get("record_type") == "source_span"
    }
    pages = {
        str(record["page_id"]): record for record in records if record.get("record_type") == "page"
    }
    labels = _unique_label_index(units.values(), markers)
    edge_evidence: dict[EdgeKey, set[str]] = defaultdict(set)
    edge_rules: EdgeRules = defaultdict(dict)
    direct_outcomes = _resolve_direct_pairs(units, labels, edge_evidence, policy=policy)
    mention_outcomes, mention_diagnostics = _resolve_mentions(
        mentions,
        units,
        labels,
        spans,
        pages,
        edge_evidence,
        edge_rules,
        activity,
        policy,
    )
    membership_outcomes, membership_diagnostics = _resolve_memberships(
        memberships, units, labels, edge_evidence, edge_rules, activity, policy
    )
    edges = _edge_records(edge_evidence, activity, edge_rules=edge_rules)
    edge_ids = {
        (str(edge["relation_type"]), str(edge["source_unit_id"]), str(edge["target_unit_id"])): str(
            edge["edge_id"]
        )
        for edge in edges
    }
    _attach_edge_ids(mention_outcomes, edge_ids)
    _attach_edge_ids(membership_outcomes, edge_ids)
    _attach_edge_ids(direct_outcomes, edge_ids)
    orphan_diagnostics = _direct_pair_orphan_diagnostics(direct_outcomes, units, activity)
    cycle_diagnostics = _cycle_diagnostics(edges, units, activity)
    diagnostics = sorted(
        [
            *mention_diagnostics,
            *membership_diagnostics,
            *orphan_diagnostics,
            *cycle_diagnostics,
        ],
        key=lambda record: str(record["diagnostic_id"]),
    )
    views = _review_views(units, edges, activity)
    return {
        "edges": edges,
        "diagnostics": diagnostics,
        "views": views,
        "mention_outcomes": mention_outcomes,
        "membership_outcomes": membership_outcomes,
        "direct_pair_outcomes": direct_outcomes,
    }


def _unique_label_index(
    units: Iterable[JsonObject], markers: Mapping[str, JsonObject]
) -> dict[str, JsonObject]:
    """Require accepted official labels to be unique and marker-identical."""
    labels: dict[str, JsonObject] = {}
    for unit in sorted(units, key=lambda record: str(record["unit_id"])):
        label = str(unit["official_label"])
        if label in labels:
            raise ValueError(f"accepted 05D official label is not unique: {label}")
        marker = markers.get(str(unit["start_marker_id"]))
        if marker is None or marker.get("observed_label") != label:
            raise ValueError(f"accepted 05D unit label differs from its start marker: {label}")
        labels[label] = unit
    return labels


def _resolve_direct_pairs(
    units: Mapping[str, JsonObject],
    labels: Mapping[str, JsonObject],
    edge_evidence: dict[EdgeKey, set[str]],
    *,
    policy: _ResolutionPolicy = _EXACT_POLICY,
) -> list[JsonObject]:
    """Pair only byte-identical typed label suffixes and report both populations."""
    outcomes: list[JsonObject] = []
    for unit in sorted(units.values(), key=lambda record: str(record["unit_id"])):
        kind = str(unit["unit_kind"])
        if kind not in {"comment", "response"}:
            continue
        prefix = "Comment " if kind == "comment" else "Response "
        opposite = "Response " if kind == "comment" else "Comment "
        label = str(unit["official_label"])
        if not label.startswith(prefix):
            raise ValueError(f"accepted {kind} label lacks its exact prefix: {label}")
        counterpart = labels.get(f"{opposite}{label.removeprefix(prefix)}")
        outcome: JsonObject = {
            "input_type": "source_unit",
            "input_id": unit["unit_id"],
            "official_label": label,
            "rule": EXACT_DIRECT_PAIR_RULE,
        }
        if counterpart is None or counterpart.get("unit_kind") == kind:
            reason = (
                "reviewed_non_pair_source_form"
                if label in policy.terminal_unpaired_source_labels
                else "exact_counterpart_absent"
            )
            outcome.update({"outcome": "unresolved", "reason": reason})
        else:
            comment = unit if kind == "comment" else counterpart
            response = counterpart if kind == "comment" else unit
            key = ("comment_response", str(comment["unit_id"]), str(response["unit_id"]))
            edge_evidence[key].update(
                {str(comment["start_marker_id"]), str(response["start_marker_id"])}
            )
            outcome.update({"outcome": "resolved", "edge_key": list(key)})
        outcomes.append(outcome)
    return outcomes


def _resolve_mentions(
    mentions: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    labels: Mapping[str, JsonObject],
    spans: Mapping[str, JsonObject],
    pages: Mapping[str, JsonObject],
    edge_evidence: dict[EdgeKey, set[str]],
    edge_rules: EdgeRules,
    activity: JsonObject,
    policy: _ResolutionPolicy,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Resolve each mention through exact identity or one accepted bounded rule."""
    outcomes: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    for mention in mentions:
        target_labels = cast(list[str], mention["target_labels"])
        if len(target_labels) != 1:
            raise ValueError(
                "Task 05E requires exactly one target occurrence per intra-Volume mention"
            )
        raw_label = target_labels[0]
        source = units[str(mention["source_unit_id"])]
        structural_reason, structural_rule = _classify_structural_mention(
            raw_label, mention, spans, pages, policy
        )
        if structural_reason is not None:
            structural_outcome: JsonObject = {
                "input_type": "reference_mention",
                "input_id": mention["mention_id"],
                "source_unit_id": source["unit_id"],
                "source_kind": source["unit_kind"],
                "target_label": raw_label,
                "normalized_target_label": raw_label,
                "rule": structural_rule,
                "outcome": "terminal_unresolved",
                "reason": structural_reason,
            }
            diagnostics.append(
                _diagnostic(
                    activity,
                    code="unsupported_reference_form",
                    severity="info",
                    subjects=[str(mention["mention_id"])],
                    evidence=[str(mention["mention_span_id"])],
                    message=(
                        f"structural text does not create an edge: {structural_reason}; "
                        f"target={raw_label!r}"
                    ),
                )
            )
            outcomes.append(structural_outcome)
            continue
        target_label, target, rule = _resolve_mention_target(
            raw_label, mention, labels, spans, pages, policy
        )
        outcome: JsonObject = {
            "input_type": "reference_mention",
            "input_id": mention["mention_id"],
            "source_unit_id": source["unit_id"],
            "source_kind": source["unit_kind"],
            "target_label": raw_label,
            "normalized_target_label": target_label,
            "rule": rule,
        }
        if target is None:
            category = _classify_nonmatch(
                raw_label,
                labels,
                classify_ordinary_response_prose=policy.classify_ordinary_response_prose,
                terminal_unresolved_labels=policy.terminal_unresolved_reference_labels,
            )
            code = (
                "unsupported_reference_form"
                if category in {"ordinary_prose", "prose_like", "range_like"}
                else "dangling_reference"
            )
            diagnostics.append(
                _diagnostic(
                    activity,
                    code=code,
                    severity="info",
                    subjects=[str(mention["mention_id"])],
                    evidence=[str(mention["mention_span_id"])],
                    message=(f"{policy.name} mention outcome: {category}; target={raw_label!r}"),
                )
            )
            outcome.update({"outcome": "terminal_unresolved", "reason": category})
        elif policy.classify_self_mentions and target["unit_id"] == source["unit_id"]:
            diagnostics.append(
                _diagnostic(
                    activity,
                    code="unsupported_reference_form",
                    severity="info",
                    subjects=[str(mention["mention_id"])],
                    evidence=[str(mention["mention_span_id"])],
                    message=(
                        f"self-identifying mention does not create an edge: target={raw_label!r}"
                    ),
                )
            )
            outcome.update(
                {
                    "outcome": "terminal_unresolved",
                    "reason": "self_mention",
                    "target_unit_id": target["unit_id"],
                    "target_kind": target["unit_kind"],
                }
            )
        else:
            relation = _relation_type(
                str(source["unit_kind"]),
                str(target["unit_kind"]),
                allow_general_response_response=policy.allow_general_response_response,
                allow_general_response_general_response=(
                    policy.allow_general_response_general_response
                ),
            )
            if relation is None:
                diagnostics.append(
                    _diagnostic(
                        activity,
                        code="unsupported_reference_form",
                        severity="info",
                        subjects=[str(mention["mention_id"])],
                        evidence=[str(mention["mention_span_id"]), str(target["unit_id"])],
                        message=(
                            "exact target has an unsupported endpoint-kind pair: "
                            f"{source['unit_kind']}->{target['unit_kind']}; target={raw_label!r}"
                        ),
                    )
                )
                outcome.update(
                    {
                        "outcome": "terminal_unresolved",
                        "reason": "unsupported_endpoint_kinds",
                        "target_unit_id": target["unit_id"],
                        "target_kind": target["unit_kind"],
                    }
                )
            else:
                key = (relation, str(source["unit_id"]), str(target["unit_id"]))
                edge_evidence[key].add(str(mention["mention_id"]))
                if rule != EXACT_MENTION_RULE:
                    edge_rules[key][str(mention["mention_id"])] = rule
                outcome.update(
                    {
                        "outcome": "resolved",
                        "reason": "unique_endpoint",
                        "target_unit_id": target["unit_id"],
                        "target_kind": target["unit_kind"],
                        "edge_key": list(key),
                    }
                )
        outcomes.append(outcome)
    return outcomes, diagnostics


def _resolve_memberships(
    memberships: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    labels: Mapping[str, JsonObject],
    edge_evidence: dict[EdgeKey, set[str]],
    edge_rules: EdgeRules,
    activity: JsonObject,
    policy: _ResolutionPolicy,
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Resolve General Response memberships through exact or reviewed typed labels."""
    outcomes: list[JsonObject] = []
    diagnostics: list[JsonObject] = []
    for membership in memberships:
        source = units[str(membership["general_response_unit_id"])]
        label = str(membership["target_label"])
        target_label, target, rule = _resolve_membership_target(label, labels, policy)
        outcome: JsonObject = {
            "input_type": "membership_claim",
            "input_id": membership["membership_id"],
            "source_unit_id": source["unit_id"],
            "target_label": label,
            "normalized_target_label": target_label,
            "rule": rule,
        }
        if target is None or target.get("unit_kind") != "comment":
            reason = "exact_comment_target_absent" if target is None else "target_is_not_comment"
            diagnostics.append(
                _diagnostic(
                    activity,
                    code="dangling_reference" if target is None else "unsupported_reference_form",
                    severity="info",
                    subjects=[str(membership["membership_id"])],
                    evidence=[str(membership["mention_span_id"])],
                    message=f"{policy.name} membership outcome: {reason}; target={label!r}",
                )
            )
            outcome.update({"outcome": "terminal_unresolved", "reason": reason})
        else:
            key = (
                "general_response_membership",
                str(source["unit_id"]),
                str(target["unit_id"]),
            )
            edge_evidence[key].add(str(membership["membership_id"]))
            if rule != EXACT_MEMBERSHIP_RULE:
                edge_rules[key][str(membership["membership_id"])] = rule
            outcome.update(
                {
                    "outcome": "resolved",
                    "reason": "exact_unique_comment_endpoint",
                    "target_unit_id": target["unit_id"],
                    "edge_key": list(key),
                }
            )
        outcomes.append(outcome)
    return outcomes, diagnostics


def _resolve_mention_target(
    raw_label: str,
    mention: JsonObject,
    labels: Mapping[str, JsonObject],
    spans: Mapping[str, JsonObject],
    pages: Mapping[str, JsonObject],
    policy: _ResolutionPolicy,
) -> tuple[str, JsonObject | None, str]:
    """Select one endpoint by ordered exact, whitespace, case, or separator rules."""
    exact = labels.get(raw_label)
    if exact is not None:
        return raw_label, exact, EXACT_MENTION_RULE
    if policy.collapse_whitespace:
        collapsed = " ".join(raw_label.split())
        target = labels.get(collapsed)
        if target is not None:
            return collapsed, target, WHITESPACE_RULE
    else:
        collapsed = raw_label
    if policy.normalize_case:
        case_match = _unique_casefold_target(collapsed, labels)
        if case_match is not None:
            rule = WHITESPACE_CASE_RULE if collapsed != raw_label else CASE_RULE
            return case_match, labels[case_match], rule
    period_match = _terminal_period_target(
        collapsed,
        labels,
        enabled=policy.strip_one_terminal_period,
        normalize_case=policy.normalize_case,
        whitespace_collapsed=collapsed != raw_label,
    )
    if period_match is not None:
        return period_match
    if policy.recover_control_separator:
        recovered = _recover_u0002_separator(raw_label, mention, spans, pages)
        if recovered is not None:
            separator_match = _control_separator_target(recovered, labels, policy.normalize_case)
            if separator_match is not None:
                return separator_match
    return raw_label, None, EXACT_MENTION_RULE


def _unique_casefold_target(candidate: str, labels: Mapping[str, JsonObject]) -> str | None:
    """Return the sole case-insensitive label match, never an arbitrary candidate."""
    matches = [label for label in labels if label.casefold() == candidate.casefold()]
    return matches[0] if len(matches) == 1 else None


def _terminal_period_target(
    candidate: str,
    labels: Mapping[str, JsonObject],
    *,
    enabled: bool,
    normalize_case: bool,
    whitespace_collapsed: bool,
) -> tuple[str, JsonObject, str] | None:
    """Resolve exactly one terminal period through exact then optional case matching."""
    if not enabled or not candidate.endswith(".") or candidate.endswith(".."):
        return None
    without_period = candidate[:-1]
    target = labels.get(without_period)
    if target is not None:
        rule = TERMINAL_PERIOD_WHITESPACE_RULE if whitespace_collapsed else TERMINAL_PERIOD_RULE
        return without_period, target, rule
    case_match = _unique_casefold_target(without_period, labels) if normalize_case else None
    if case_match is None:
        return None
    rule = (
        TERMINAL_PERIOD_WHITESPACE_CASE_RULE if whitespace_collapsed else TERMINAL_PERIOD_CASE_RULE
    )
    return case_match, labels[case_match], rule


def _control_separator_target(
    recovered: str,
    labels: Mapping[str, JsonObject],
    normalize_case: bool,
) -> tuple[str, JsonObject, str] | None:
    """Resolve one source-supported U+0002 recovery without broad fuzzy matching."""
    target = labels.get(recovered)
    if target is not None:
        return recovered, target, CONTROL_SEPARATOR_RULE
    case_match = _unique_casefold_target(recovered, labels) if normalize_case else None
    if case_match is None:
        return None
    return case_match, labels[case_match], CONTROL_SEPARATOR_CASE_RULE


def _recover_u0002_separator(
    raw_label: str,
    mention: JsonObject,
    spans: Mapping[str, JsonObject],
    pages: Mapping[str, JsonObject],
) -> str | None:
    """Recover one label only when U+0002 replaces its internal hyphen in source text."""
    span = spans.get(str(mention["mention_span_id"]))
    if span is None or not isinstance(span.get("fragments"), list) or not span["fragments"]:
        return None
    fragment = span["fragments"][-1]
    if not isinstance(fragment, dict):
        return None
    page = pages.get(str(fragment["page_id"]))
    if page is None:
        return None
    page_text = str(page["raw_text"])
    suffix = page_text[int(fragment["text_end"]) : int(fragment["text_end"]) + 32]
    match = re.match(r"\x02(?P<tail>[A-Z]+-[0-9]+[A-Za-z]?)\b", suffix)
    if match is None or not re.fullmatch(r"(?:Comment|Response) [A-Z]", raw_label, re.IGNORECASE):
        return None
    return f"{raw_label}-{match.group('tail')}"


def _resolve_membership_target(
    raw_label: str,
    labels: Mapping[str, JsonObject],
    policy: _ResolutionPolicy,
) -> tuple[str, JsonObject | None, str]:
    """Resolve exact memberships, typed suffixes, and five reviewed source typos."""
    exact = labels.get(raw_label)
    if exact is not None:
        return raw_label, exact, EXACT_MEMBERSHIP_RULE
    if not policy.typed_memberships:
        return raw_label, None, EXACT_MEMBERSHIP_RULE
    aliases = policy.membership_aliases or {}
    corrected = aliases.get(raw_label, raw_label)
    typed_label = f"Comment {corrected}"
    rule = MEMBERSHIP_ALIAS_RULE if corrected != raw_label else TYPED_MEMBERSHIP_RULE
    return typed_label, labels.get(typed_label), rule


def _relation_type(
    source_kind: str,
    target_kind: str,
    *,
    allow_general_response_response: bool = False,
    allow_general_response_general_response: bool = False,
) -> str | None:
    """Map endpoint kinds, optionally including the reviewed General-Response relation."""
    relations = {
        ("comment", "response"): "comment_response",
        ("response", "response"): "response_response",
        ("response", "general_response"): "response_general_response",
        ("general_response", "comment"): "general_response_membership",
    }
    if allow_general_response_response:
        relations[("general_response", "response")] = "general_response_response"
    if allow_general_response_general_response:
        relations[("general_response", "general_response")] = "general_response_general_response"
    return relations.get((source_kind, target_kind))


def _classify_structural_mention(
    raw_label: str,
    mention: JsonObject,
    spans: Mapping[str, JsonObject],
    pages: Mapping[str, JsonObject],
    policy: _ResolutionPolicy,
) -> tuple[str | None, str]:
    """Classify reviewed page furniture and response-section labels without edges."""
    span = spans.get(str(mention["mention_span_id"]))
    if span is None or not isinstance(span.get("fragments"), list):
        return None, EXACT_MENTION_RULE
    fragments = span["fragments"]
    if len(fragments) != 1 or not isinstance(fragments[0], dict):
        return None, EXACT_MENTION_RULE
    fragment = fragments[0]
    page = pages.get(str(fragment["page_id"]))
    if page is None:
        return None, EXACT_MENTION_RULE
    page_text = str(page["raw_text"])
    start = int(fragment["text_start"])
    end = int(fragment["text_end"])
    if policy.classify_running_headers and _inside_running_header(page_text, start, end):
        return "running_header", RUNNING_HEADER_RULE
    if (
        policy.classify_response_section_headings
        and page_text[max(0, start - 3) : start] == "b. "
        and _RESPONSE_SECTION_MENTION_RE.fullmatch(raw_label)
    ):
        return "response_section_heading", RESPONSE_SECTION_RULE
    return None, EXACT_MENTION_RULE


def _inside_running_header(page_text: str, start: int, end: int) -> bool:
    """Return whether one mention lies wholly within the known top breadcrumb line."""
    cursor = 0
    for line in page_text.splitlines(keepends=True)[:3]:
        line_end = cursor + len(line.rstrip("\r\n"))
        if cursor <= start and end <= line_end:
            return _RUNNING_HEADER_RE.search(line.rstrip("\r\n")) is not None
        cursor += len(line)
    return False


def _classify_nonmatch(
    label: str,
    labels: Mapping[str, JsonObject],
    *,
    classify_ordinary_response_prose: bool = False,
    terminal_unresolved_labels: frozenset[str] = frozenset(),
) -> str:
    """Describe observed exact failures without changing matching behavior."""
    collapsed = " ".join(label.split())
    if label in terminal_unresolved_labels:
        return "reviewed_source_label_typo_unresolved"
    if collapsed != label and collapsed in labels:
        return "whitespace_variant"
    casefold_matches = [
        existing for existing in labels if existing.casefold() == collapsed.casefold()
    ]
    if len(casefold_matches) == 1:
        return "whitespace_case_variant" if collapsed != label else "case_variant"
    without_terminal = collapsed.rstrip(".,;:")
    if without_terminal != collapsed and without_terminal in labels:
        return "punctuation_variant"
    suffix_match = _LETTER_SUFFIX.fullmatch(collapsed)
    if suffix_match and suffix_match.group("prefix") in labels:
        return "parent_subanswer_candidate"
    if any(
        _LETTER_SUFFIX.fullmatch(existing)
        and cast(re.Match[str], _LETTER_SUFFIX.fullmatch(existing)).group("prefix") == collapsed
        for existing in labels
    ):
        return "parent_subanswer_candidate"
    if _RANGE_TOKEN.search(collapsed):
        return "range_like"
    if classify_ordinary_response_prose and _ORDINARY_RESPONSE_PROSE_RE.fullmatch(collapsed):
        return "ordinary_prose"
    if collapsed.casefold() in _OBVIOUS_PROSE_TARGETS:
        return "prose_like"
    return "other_nonexact"


def _edge_records(
    edge_evidence: Mapping[EdgeKey, set[str]],
    activity: JsonObject,
    *,
    edge_rules: Mapping[EdgeKey, Mapping[str, str]] | None = None,
) -> list[JsonObject]:
    """Aggregate repeated evidence into one stable edge per endpoints and type."""
    records: list[JsonObject] = []
    for relation, source_id, target_id in sorted(edge_evidence):
        record: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "semantic_edge",
            "relation_type": relation,
            "source_unit_id": source_id,
            "target_unit_id": target_id,
            "activity_id": activity["activity_id"],
            "evidence_ids": sorted(edge_evidence[(relation, source_id, target_id)]),
        }
        rules = (edge_rules or {}).get((relation, source_id, target_id), {})
        if rules:
            record["evidence_resolutions"] = [
                {"evidence_id": evidence_id, "resolver_rule": rules[evidence_id]}
                for evidence_id in sorted(rules)
            ]
        record["edge_id"] = build_record_id(record)
        records.append(record)
    return sorted(records, key=lambda record: str(record["edge_id"]))


def _diagnostic(
    activity: JsonObject,
    *,
    code: str,
    severity: str,
    subjects: Sequence[str],
    evidence: Sequence[str],
    message: str,
) -> JsonObject:
    """Create one deterministic terminal Task 05E diagnostic."""
    record: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "diagnostic",
        "stage": "05e",
        "activity_id": activity["activity_id"],
        "code": code,
        "severity": severity,
        "terminal": True,
        "subject_ids": sorted(set(subjects)),
        "evidence_ids": sorted(set(evidence)),
        "message": message,
    }
    record["diagnostic_id"] = build_record_id(record)
    return record


def _direct_pair_orphan_diagnostics(
    outcomes: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    activity: JsonObject,
) -> list[JsonObject]:
    """Preserve every comment or response lacking an exact typed counterpart."""
    diagnostics: list[JsonObject] = []
    for outcome in outcomes:
        if outcome["outcome"] == "resolved":
            continue
        unit = units[str(outcome["input_id"])]
        diagnostics.append(
            _diagnostic(
                activity,
                code="orphan_unit",
                severity="info",
                subjects=[str(unit["unit_id"])],
                evidence=[str(unit["start_marker_id"])],
                message=(
                    "exact typed-label counterpart is absent; "
                    f"official_label={unit['official_label']!r}"
                ),
            )
        )
    return diagnostics


def _cycle_diagnostics(
    edges: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    activity: JsonObject,
) -> list[JsonObject]:
    """Emit one diagnostic for every deterministic strongly connected cycle."""
    adjacency: dict[str, list[str]] = defaultdict(list)
    edge_ids_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    for edge in edges:
        source = str(edge["source_unit_id"])
        target = str(edge["target_unit_id"])
        adjacency[source].append(target)
        edge_ids_by_pair[(source, target)].append(str(edge["edge_id"]))
    components = _strongly_connected_components(units, adjacency)
    diagnostics: list[JsonObject] = []
    for component in components:
        component_set = set(component)
        self_loop = any(node in adjacency.get(node, ()) for node in component)
        if len(component) == 1 and not self_loop:
            continue
        evidence = sorted(
            edge_id
            for (source, target), edge_ids in edge_ids_by_pair.items()
            if source in component_set and target in component_set
            for edge_id in edge_ids
        )
        diagnostics.append(
            _diagnostic(
                activity,
                code="cycle_detected",
                severity="info",
                subjects=component,
                evidence=evidence,
                message=f"relationship graph cycle contains {len(component)} source units",
            )
        )
    return diagnostics


def _strongly_connected_components(
    units: Mapping[str, JsonObject], adjacency: Mapping[str, Sequence[str]]
) -> list[list[str]]:
    """Return deterministic Tarjan components without a graph dependency."""
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for target in sorted(set(adjacency.get(node, ()))):
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in active:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                active.remove(member)
                component.append(member)
                if member == node:
                    break
            components.append(sorted(component))

    for unit_id in sorted(units):
        if unit_id not in indices:
            visit(unit_id)
    return sorted(components)


def _review_views(
    units: Mapping[str, JsonObject], edges: Sequence[JsonObject], activity: JsonObject
) -> list[JsonObject]:
    """Build ID-only comment-rooted views from the current relationship edges."""
    direct_by_comment: dict[str, list[JsonObject]] = defaultdict(list)
    outgoing_by_response: dict[str, list[JsonObject]] = defaultdict(list)
    outgoing_by_general: dict[str, list[JsonObject]] = defaultdict(list)
    memberships_by_comment: dict[str, list[JsonObject]] = defaultdict(list)
    for edge in edges:
        relation = edge["relation_type"]
        if relation == "comment_response":
            direct_by_comment[str(edge["source_unit_id"])].append(edge)
        elif relation in {"response_response", "response_general_response"}:
            outgoing_by_response[str(edge["source_unit_id"])].append(edge)
        elif relation in {
            "general_response_response",
            "general_response_general_response",
        }:
            outgoing_by_general[str(edge["source_unit_id"])].append(edge)
        elif relation == "general_response_membership":
            memberships_by_comment[str(edge["target_unit_id"])].append(edge)
    views: list[JsonObject] = []
    comments = sorted(
        (unit for unit in units.values() if unit["unit_kind"] == "comment"),
        key=lambda unit: str(unit["official_label"]),
    )
    for comment in comments:
        comment_id = str(comment["unit_id"])
        direct_edges = sorted(
            direct_by_comment.get(comment_id, ()), key=lambda edge: str(edge["edge_id"])
        )
        linked_edges = sorted(
            (
                linked
                for direct in direct_edges
                for linked in outgoing_by_response.get(str(direct["target_unit_id"]), ())
            ),
            key=lambda edge: str(edge["edge_id"]),
        )
        membership_edges = sorted(
            memberships_by_comment.get(comment_id, ()), key=lambda edge: str(edge["edge_id"])
        )
        general_response_edges = sorted(
            (
                linked
                for membership in membership_edges
                for linked in outgoing_by_general.get(str(membership["source_unit_id"]), ())
            ),
            key=lambda edge: str(edge["edge_id"]),
        )
        ordered_ids = _ordered_view_units(
            comment,
            direct_edges,
            [*linked_edges, *general_response_edges],
            membership_edges,
            units,
        )
        selected_edges = [
            *direct_edges,
            *linked_edges,
            *membership_edges,
            *general_response_edges,
        ]
        record: JsonObject = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "review_view",
            "root_unit_id": comment_id,
            "ordered_unit_ids": ordered_ids,
            "edge_ids": sorted({str(edge["edge_id"]) for edge in selected_edges}),
            "anchor_span_ids": [str(units[unit_id]["span_ids"][0]) for unit_id in ordered_ids],
            "rendering_recipe": "source_text_with_accepted_overlays",
            "activity_id": activity["activity_id"],
        }
        record["view_id"] = build_record_id(record)
        views.append(record)
    return sorted(views, key=lambda record: str(record["view_id"]))


def _ordered_view_units(
    comment: JsonObject,
    direct_edges: Sequence[JsonObject],
    linked_edges: Sequence[JsonObject],
    membership_edges: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
) -> list[str]:
    """Order root, direct responses, linked responses, then General Responses."""
    direct = {str(edge["target_unit_id"]) for edge in direct_edges}
    linked_responses = {
        str(edge["target_unit_id"])
        for edge in linked_edges
        if units[str(edge["target_unit_id"])]["unit_kind"] == "response"
    }
    general_responses = {
        str(edge["target_unit_id"])
        for edge in linked_edges
        if units[str(edge["target_unit_id"])]["unit_kind"] == "general_response"
    }
    general_responses.update(str(edge["source_unit_id"]) for edge in membership_edges)

    def ordered(values: set[str]) -> list[str]:
        return sorted(values, key=lambda unit_id: (str(units[unit_id]["official_label"]), unit_id))

    result = [
        str(comment["unit_id"]),
        *ordered(direct),
        *ordered(linked_responses),
        *ordered(general_responses),
    ]
    return list(dict.fromkeys(result))


def _attach_edge_ids(outcomes: Sequence[JsonObject], edge_ids: Mapping[EdgeKey, str]) -> None:
    """Replace report-only edge keys with stable IDs after evidence aggregation."""
    for outcome in outcomes:
        raw_key = outcome.pop("edge_key", None)
        if raw_key is not None:
            outcome["edge_id"] = edge_ids[cast(EdgeKey, tuple(raw_key))]


def _census_report(
    spec: ResponseRelationshipRunSpecV3 | ResponseRelationshipReviewRunSpecV4,
    activity: JsonObject,
    acceptance: JsonObject,
    upstream: Sequence[JsonObject],
    edges: Sequence[JsonObject],
    diagnostics: Sequence[JsonObject],
    views: Sequence[JsonObject],
    mention_outcomes: Sequence[JsonObject],
    membership_outcomes: Sequence[JsonObject],
    direct_outcomes: Sequence[JsonObject],
) -> JsonObject:
    """Preserve complete individual outcomes plus compact failure summaries."""
    source_units = [record for record in upstream if record.get("record_type") == "source_unit"]
    all_mentions = [
        record for record in upstream if record.get("record_type") == "reference_mention"
    ]
    mention_failure_categories = Counter(
        str(outcome["reason"]) for outcome in mention_outcomes if outcome["outcome"] != "resolved"
    )
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "status": "exact_baseline_complete_review_required",
        "activity_id": activity["activity_id"],
        "accepted_task05d": {
            "acceptance_id": acceptance["acceptance_id"],
            "completion_id": spec.accepted_task05d.completion_id,
            "inventory_id": spec.accepted_task05d.inventory_id,
            "semantic_digest": spec.accepted_task05d.semantic_digest,
        },
        "policy": {
            "direct_pair_rule": EXACT_DIRECT_PAIR_RULE,
            "mention_rule": EXACT_MENTION_RULE,
            "membership_rule": EXACT_MEMBERSHIP_RULE,
            "whitespace_normalization": False,
            "punctuation_normalization": False,
            "case_normalization": False,
            "letter_suffix_inference": False,
            "fuzzy_or_semantic_matching": False,
        },
        "counts": {
            "source_units": len(source_units),
            "comment_units": sum(record["unit_kind"] == "comment" for record in source_units),
            "response_units": sum(record["unit_kind"] == "response" for record in source_units),
            "general_response_units": sum(
                record["unit_kind"] == "general_response" for record in source_units
            ),
            "reference_mentions": len(all_mentions),
            "intra_volume_mentions": len(mention_outcomes),
            "out_of_scope_mentions": len(all_mentions) - len(mention_outcomes),
            "membership_claims": len(membership_outcomes),
            "resolved_mentions": sum(item["outcome"] == "resolved" for item in mention_outcomes),
            "terminal_unresolved_mentions": sum(
                item["outcome"] != "resolved" for item in mention_outcomes
            ),
            "resolved_memberships": sum(
                item["outcome"] == "resolved" for item in membership_outcomes
            ),
            "terminal_unresolved_memberships": sum(
                item["outcome"] != "resolved" for item in membership_outcomes
            ),
            "direct_pair_unit_outcomes": len(direct_outcomes),
            "direct_pair_resolved_units": sum(
                item["outcome"] == "resolved" for item in direct_outcomes
            ),
            "direct_pair_unresolved_units": sum(
                item["outcome"] != "resolved" for item in direct_outcomes
            ),
            "semantic_edges": len(edges),
            "diagnostics": len(diagnostics),
            "review_views": len(views),
        },
        "edge_counts_by_relation": dict(
            sorted(Counter(str(edge["relation_type"]) for edge in edges).items())
        ),
        "diagnostic_counts_by_code": dict(
            sorted(Counter(str(item["code"]) for item in diagnostics).items())
        ),
        "mention_failure_categories": dict(sorted(mention_failure_categories.items())),
        "membership_failure_categories": dict(
            sorted(
                Counter(
                    str(outcome["reason"])
                    for outcome in membership_outcomes
                    if outcome["outcome"] != "resolved"
                ).items()
            )
        ),
        "direct_pair_failure_labels": sorted(
            str(outcome["official_label"])
            for outcome in direct_outcomes
            if outcome["outcome"] != "resolved"
        ),
        "mention_outcomes": list(mention_outcomes),
        "membership_outcomes": list(membership_outcomes),
        "direct_pair_outcomes": list(direct_outcomes),
        "gate2_authorized": False,
        "source_pdf_accessed": False,
    }


def _baseline_receipt(
    activity: JsonObject,
    census: JsonObject,
    derived_records: Sequence[JsonObject],
    payloads: Mapping[str, bytes],
) -> JsonObject:
    """Describe exact nonterminal baseline bytes without publishing completion."""
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "status": "exact_baseline_complete_review_required",
        "activity_id": activity["activity_id"],
        "semantic_digest": semantic_bundle_digest(derived_records),
        "census_digest": canonical_json_sha256(census),
        "files": [
            {
                "path": path,
                "byte_size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for path, content in sorted(payloads.items())
        ],
        "completion_written": False,
        "gate2_authorized": False,
        "source_pdf_accessed": False,
    }


def _review_receipt(
    activity: JsonObject,
    census: JsonObject,
    derived_records: Sequence[JsonObject],
    payloads: Mapping[str, bytes],
) -> JsonObject:
    """Describe bounded review bytes without impersonating terminal Gate 2 completion."""
    return {
        "schema_version": REVIEW_PASS_SCHEMA_VERSION,
        "status": "bounded_review_complete_review_required",
        "activity_id": activity["activity_id"],
        "semantic_digest": semantic_bundle_digest(derived_records),
        "census_digest": canonical_json_sha256(census),
        "files": [
            {
                "path": path,
                "byte_size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for path, content in sorted(payloads.items())
        ],
        "completion_written": False,
        "gate2_authorized": True,
        "source_pdf_accessed": False,
    }


def _verify_published_baseline(
    baseline_root: Path, payloads: Mapping[str, bytes], receipt: JsonObject
) -> None:
    """Verify every published baseline file and the absence of completion state."""
    for relative_path, expected in payloads.items():
        observed = (baseline_root / relative_path).read_bytes()
        if observed != expected:
            raise ValueError(f"published Task 05E baseline differs: {relative_path}")
    if (baseline_root / "records/stage_completion.json").exists():
        raise ValueError("Gate 1 baseline must not publish a stage completion")
    observed_receipt = read_json_object(baseline_root / "records/baseline_receipt.json")
    if observed_receipt != receipt:
        raise ValueError("published Task 05E baseline receipt differs")


def _verify_published_review(
    review_root: Path, payloads: Mapping[str, bytes], receipt: JsonObject
) -> None:
    """Verify every review-pass byte and absence of terminal completion state."""
    for relative_path, expected in payloads.items():
        if (review_root / relative_path).read_bytes() != expected:
            raise ValueError(f"published Task 05E review pass differs: {relative_path}")
    if (review_root / "records/stage_completion.json").exists():
        raise ValueError("bounded review pass must not publish a stage completion")
    if read_json_object(review_root / "records/review_receipt.json") != receipt:
        raise ValueError("published Task 05E review-pass receipt differs")


def _binding_path(
    spec: ResponseRelationshipRunSpecV3 | ResponseRelationshipReviewRunSpecV4,
    role: str,
) -> Path:
    """Return one uniquely validated repository binding path."""
    return next(binding.path for binding in spec.repository_bindings if binding.role == role)


__all__ = ["build_bounded_relationship_review", "build_exact_relationship_baseline"]
