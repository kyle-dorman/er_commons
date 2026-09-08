"""Deterministic identities and source-free validation for inventory records."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from jsonschema import (  # type: ignore[import-untyped]
    Draft202012Validator,
    FormatChecker,
    ValidationError,
)

from er_commons.artifact_io import canonical_json_sha256

type JsonObject = dict[str, Any]

SCHEMA_VERSION: Final = "er_commons.response_inventory.v1"

# These projections are the complete semantic ID policy. Runtime timestamps,
# working paths, review dispositions, and normalized display text are excluded.
ID_RULES: Final[dict[str, tuple[str, str, tuple[str, ...]]]] = {
    "activity": (
        "activity_id",
        "activityv1",
        (
            "stage",
            "source_id",
            "page_ranges",
            "config_sha256",
            "schema_sha256",
            "code_sha256",
            "tool_versions",
            "input_refs",
        ),
    ),
    "page": ("page_id", "pagev1", ("source_id", "physical_page")),
    "page_continuation": (
        "continuation_id",
        "continuationv1",
        ("from_page_id", "to_page_id", "continuation_kind"),
    ),
    "marker_candidate": (
        "marker_id",
        "markerv1",
        ("page_id", "marker_kind", "observed_label", "text_start"),
    ),
    "source_span": ("span_id", "spanv1", ("source_id", "fragments")),
    "commenter": (
        "commenter_id",
        "commenterv1",
        ("source_id", "source_label", "opener_span_id"),
    ),
    "submission": (
        "submission_id",
        "submissionv1",
        ("source_id", "submission_kind", "official_code", "opener_span_id"),
    ),
    "source_unit": (
        "unit_id",
        "unitv1",
        ("source_id", "unit_kind", "official_label", "start_marker_id", "span_ids"),
    ),
    "membership_claim": (
        "membership_id",
        "membershipv1",
        ("general_response_unit_id", "mention_span_id", "target_label"),
    ),
    "reference_mention": (
        "mention_id",
        "mentionv1",
        ("source_unit_id", "mention_span_id", "raw_text_sha256"),
    ),
    "semantic_edge": (
        "edge_id",
        "edgev1",
        ("relation_type", "source_unit_id", "target_unit_id"),
    ),
    "draft_eir_link": (
        "link_id",
        "deirlinkv1",
        ("source_unit_id", "mention_id", "target_id"),
    ),
    "diagnostic": (
        "diagnostic_id",
        "diagnosticv1",
        ("stage", "code", "severity", "terminal", "subject_ids", "evidence_ids"),
    ),
    "source_placement_exception": (
        "exception_id",
        "placementv1",
        ("source_id", "exception_code", "advertised_label"),
    ),
    "correction": (
        "correction_id",
        "correctionv1",
        (
            "correction_kind",
            "target_ids",
            "replacement_ids",
            "evidence_ids",
            "replacement_text",
            "disposition",
            "transcription_method",
        ),
    ),
    "review_view": (
        "view_id",
        "reviewviewv1",
        ("root_unit_id", "ordered_unit_ids", "edge_ids", "anchor_span_ids"),
    ),
    "managed_file_inventory": (
        "inventory_id",
        "fileinventoryv1",
        ("stage", "activity_id", "dependencies", "files"),
    ),
    "stage_completion": (
        "completion_id",
        "completionv1",
        ("stage", "status", "activity_id", "inventory_id", "counts"),
    ),
}


def build_record_id(record: Mapping[str, Any]) -> str:
    """Derive a typed stable ID from the record's closed semantic projection."""
    record_type = record.get("record_type")
    if not isinstance(record_type, str) or record_type not in ID_RULES:
        raise ValueError(f"unsupported record_type for identity: {record_type!r}")
    _id_field, prefix, fields = ID_RULES[record_type]
    missing = [field for field in fields if field not in record]
    if missing:
        raise ValueError(f"identity preimage is missing fields: {missing}")
    preimage = {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        **{field: _identity_value(record_type, field, record[field]) for field in fields},
    }
    return f"{prefix}-{canonical_json_sha256(preimage)}"


def semantic_bundle_digest(records: Iterable[Mapping[str, Any]]) -> str:
    """Hash semantic records after canonical ID ordering, independent of discovery order."""
    ordered = sorted(
        (_semantic_record(record) for record in records),
        key=lambda record: (str(record["record_type"]), _record_id(record)),
    )
    return canonical_json_sha256(ordered)


def build_publication_id(completion: Mapping[str, Any], inventory: Mapping[str, Any]) -> str:
    """Derive the sole successful 05G release ID from validated record identities."""
    if (
        completion.get("record_type") != "stage_completion"
        or inventory.get("record_type") != "managed_file_inventory"
    ):
        raise ValueError("publication identity requires completion and inventory records")
    if completion.get("stage") != "05g" or inventory.get("stage") != "05g":
        raise ValueError("only Task 05G may derive an inventoryv1 publication")
    if completion.get("status") not in {"complete", "complete_with_warnings"}:
        raise ValueError("failed completion cannot derive an inventoryv1 publication")
    completion_id = _record_id(completion)
    inventory_id = _record_id(inventory)
    if completion_id != build_record_id(completion) or inventory_id != build_record_id(inventory):
        raise ValueError("publication inputs do not derive from their identity preimages")
    if completion.get("inventory_id") != inventory_id:
        raise ValueError("publication completion does not reference its managed inventory")
    preimage = {
        "schema_version": SCHEMA_VERSION,
        "stage": "05g",
        "stage_completion_id": completion_id,
        "managed_file_inventory_id": inventory_id,
    }
    return f"inventoryv1-{canonical_json_sha256(preimage)}"


def validate_record_bundle(records: Sequence[JsonObject], schema: JsonObject) -> str:
    """Validate record shapes, identities, references, and MVP semantic invariants."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for index, record in enumerate(records):
        try:
            validator.validate(record)
        except ValidationError as error:
            raise ValueError(f"record {index} fails JSON Schema: {error.message}") from error

    by_id: dict[str, JsonObject] = {}
    for record in records:
        record_id = _record_id(record)
        if record_id in by_id:
            raise ValueError(f"duplicate record ID: {record_id}")
        expected = build_record_id(record)
        if record_id != expected:
            raise ValueError(f"record ID does not derive from its preimage: {record_id}")
        by_id[record_id] = record

    pages = _records_of_type(records, "page")
    spans = _records_of_type(records, "source_span")
    units = _records_of_type(records, "source_unit")
    mentions = _records_of_type(records, "reference_mention")
    memberships = _records_of_type(records, "membership_claim")
    inventories = _records_of_type(records, "managed_file_inventory")
    activities = _records_of_type(records, "activity")

    page_keys = [(page["source_id"], page["physical_page"]) for page in pages.values()]
    if len(page_keys) != len(set(page_keys)):
        raise ValueError("physical pages must be unique within a source")

    for page in pages.values():
        digest = hashlib.sha256(page["raw_text"].encode("utf-8")).hexdigest()
        if page["raw_text_sha256"] != digest:
            raise ValueError(f"page raw-text digest mismatch: {page['page_id']}")
        _require_ref(page["activity_id"], activities, expected_type="activity")
        _validate_page_box(page)
        if page.get("geometry_ref") is not None:
            _validate_artifact_reference(page["geometry_ref"], require_digest=False)

    for record in _records_of_type(records, "page_continuation").values():
        _require_refs(record, ("from_page_id", "to_page_id"), pages)
        for evidence_id in record["evidence_ids"]:
            if evidence_id not in by_id:
                raise ValueError(f"continuation references missing evidence: {evidence_id}")
        if (
            pages[record["from_page_id"]]["physical_page"]
            >= pages[record["to_page_id"]]["physical_page"]
        ):
            raise ValueError("page continuation must point forward")
        if pages[record["from_page_id"]]["source_id"] != pages[record["to_page_id"]]["source_id"]:
            raise ValueError("page continuation cannot cross source identities")

    for marker in _records_of_type(records, "marker_candidate").values():
        _require_refs(marker, ("page_id",), pages)
        _require_text_interval(marker, pages[marker["page_id"]]["raw_text"])
        _validate_bbox(marker["bbox"], pages[marker["page_id"]])
        if marker["disposition"] == "unit_start":
            style = marker["style_evidence"]
            expected_style = (
                marker["marker_kind"] == "comment" and style["bold"] and style["solid_rule"]
            ) or (marker["marker_kind"] == "response" and style["italic"] and style["dotted_rule"])
            if not marker["line_initial"]:
                raise ValueError("unit-start marker must be line-initial")
            if marker["marker_kind"] in {"comment", "response"} and not expected_style:
                raise ValueError("unit-start marker lacks required style and rule evidence")

    for span in spans.values():
        previous: tuple[int, int] | None = None
        for fragment in span["fragments"]:
            page_id = fragment["page_id"]
            if page_id not in pages:
                raise ValueError(f"source span references missing page: {page_id}")
            if span["source_id"] != pages[page_id]["source_id"]:
                raise ValueError(f"source span crosses source identities: {span['span_id']}")
            _require_text_interval(fragment, pages[page_id]["raw_text"])
            if fragment["bbox"] is not None:
                _validate_bbox(fragment["bbox"], pages[page_id])
            if (
                fragment["character_slot_end"] is not None
                and fragment["character_slot_end"] > pages[page_id]["character_slot_count"]
            ):
                raise ValueError("PDFium character-slot interval exceeds page slot count")
            current = (pages[page_id]["physical_page"], fragment["text_start"])
            if previous is not None and current < previous:
                raise ValueError(f"source span fragments are not ordered: {span['span_id']}")
            previous = current

    for commenter in _records_of_type(records, "commenter").values():
        _require_refs(commenter, ("opener_span_id",), spans)
        if spans[commenter["opener_span_id"]]["source_id"] != commenter["source_id"]:
            raise ValueError("commenter opener span crosses source identities")
    for submission in _records_of_type(records, "submission").values():
        _require_refs(submission, ("opener_span_id",), spans)
        if spans[submission["opener_span_id"]]["source_id"] != submission["source_id"]:
            raise ValueError("submission opener span crosses source identities")
        _require_list_refs(submission, "commenter_ids", by_id, expected_type="commenter")
        if any(
            by_id[item]["source_id"] != submission["source_id"]
            for item in submission["commenter_ids"]
        ):
            raise ValueError("submission commenter crosses source identities")
    for unit in units.values():
        _require_list_refs(unit, "span_ids", spans)
        _require_ref(unit["activity_id"], activities, expected_type="activity")
        if any(spans[span_id]["source_id"] != unit["source_id"] for span_id in unit["span_ids"]):
            raise ValueError(f"source unit crosses source identities: {unit['unit_id']}")
        if unit["submission_id"] is not None:
            _require_ref(unit["submission_id"], by_id, expected_type="submission")
            if by_id[unit["submission_id"]]["source_id"] != unit["source_id"]:
                raise ValueError(
                    f"source unit references another source's submission: {unit['unit_id']}"
                )
        if unit["unit_kind"] in {"comment", "response"}:
            if unit["start_marker_id"] is None:
                raise ValueError("comment and response units require an accepted start marker")
            start_marker = by_id.get(unit["start_marker_id"])
            if (
                start_marker is None
                or start_marker["record_type"] != "marker_candidate"
                or start_marker["disposition"] != "unit_start"
                or start_marker["marker_kind"] != unit["unit_kind"]
            ):
                raise ValueError("source unit start marker is missing or incompatible")
            first_fragment = spans[unit["span_ids"][0]]["fragments"][0]
            if (
                start_marker["page_id"] != first_fragment["page_id"]
                or start_marker["text_start"] != first_fragment["text_start"]
            ):
                raise ValueError("source unit start marker differs from its first span anchor")
        elif unit["start_marker_id"] is not None:
            _require_ref(unit["start_marker_id"], by_id, expected_type="marker_candidate")
        if unit["unit_kind"] == "general_response" and _is_general_response_nine(
            unit["official_label"]
        ):
            raise ValueError("General Response 9 cannot be a Volume 4 source unit")

    for membership in memberships.values():
        _require_ref(membership["general_response_unit_id"], units, expected_type="source_unit")
        if units[membership["general_response_unit_id"]]["unit_kind"] != "general_response":
            raise ValueError("membership owner must be a general response")
        _require_ref(membership["mention_span_id"], spans, expected_type="source_span")

    for mention in mentions.values():
        _require_ref(mention["source_unit_id"], units, expected_type="source_unit")
        _require_ref(mention["mention_span_id"], spans, expected_type="source_span")
        _validate_mention_text(mention, units, spans, pages)

    for edge in _records_of_type(records, "semantic_edge").values():
        _require_refs(edge, ("source_unit_id", "target_unit_id"), units)
        source_kind = units[edge["source_unit_id"]]["unit_kind"]
        target_kind = units[edge["target_unit_id"]]["unit_kind"]
        expected_kinds = {
            "comment_response": ("comment", "response"),
            "response_response": ("response", "response"),
            "response_general_response": ("response", "general_response"),
            "general_response_membership": ("general_response", "comment"),
        }
        if (source_kind, target_kind) != expected_kinds[edge["relation_type"]]:
            raise ValueError("semantic edge endpoint kinds contradict relation type")
        for evidence_id in edge["evidence_ids"]:
            if (
                evidence_id not in mentions
                and evidence_id not in memberships
                and by_id.get(evidence_id, {}).get("record_type") != "marker_candidate"
            ):
                raise ValueError(f"semantic edge has missing evidence: {evidence_id}")
        _validate_edge_evidence(edge, units, mentions, memberships, by_id)

    for link in _records_of_type(records, "draft_eir_link").values():
        _require_ref(link["source_unit_id"], units, expected_type="source_unit")
        _require_ref(link["mention_id"], mentions, expected_type="reference_mention")
        if mentions[link["mention_id"]]["source_unit_id"] != link["source_unit_id"]:
            raise ValueError("Draft EIR link source differs from its mention source")
        if mentions[link["mention_id"]]["reference_domain"] != "draft_eir":
            raise ValueError("Draft EIR link must use a draft_eir mention")
        activity = activities[link["activity_id"]]
        input_identities = {item["role"]: item["identity"] for item in activity["input_refs"]}
        if link["task04d_handoff_id"] != input_identities.get("task04d_handoff"):
            raise ValueError("Draft EIR link differs from its Task 04D handoff input")
        if link["task04a_registry_id"] != input_identities.get("task04a_registry"):
            raise ValueError("Draft EIR link differs from its Task 04A registry input")

    closed_stages = {
        completion["stage"]
        for completion in _records_of_type(records, "stage_completion").values()
        if completion["status"] != "failed"
    }
    _validate_diagnostics(records, by_id, mentions, closed_stages)
    _validate_placement(records, units)
    _validate_corrections(records, by_id)
    _validate_views(records, units, spans, by_id)

    for completion in _records_of_type(records, "stage_completion").values():
        _require_ref(completion["activity_id"], activities, expected_type="activity")
        _require_ref(
            completion["inventory_id"], inventories, expected_type="managed_file_inventory"
        )
        if activities[completion["activity_id"]]["stage"] != completion["stage"]:
            raise ValueError("completion stage differs from its activity")
        if inventories[completion["inventory_id"]]["stage"] != completion["stage"]:
            raise ValueError("completion stage differs from its inventory")
        if completion["stage"] in {"05d", "05g"} and completion["status"] != "failed":
            general_responses = [
                unit for unit in units.values() if unit["unit_kind"] == "general_response"
            ]
            placement_exceptions = _records_of_type(records, "source_placement_exception")
            if completion["counts"].get("general_responses") != len(general_responses):
                raise ValueError("completion General Response count differs from records")
            if len(general_responses) != 8:
                raise ValueError("complete source inventory must account for 8 General Responses")
            if completion["counts"].get("placement_exceptions") != len(placement_exceptions):
                raise ValueError("completion placement-exception count differs from records")
            if len(placement_exceptions) != 1:
                raise ValueError("complete source inventory must account for the GR9 exception")
            labels = {unit["official_label"].strip().lower() for unit in general_responses}
            if labels != {f"general response {number}" for number in range(1, 9)}:
                raise ValueError("complete source inventory must contain General Responses 1-8")

    _validate_inventories(inventories, activities)
    _validate_activity_scopes(activities, pages)
    _validate_derived_activities(records, activities)

    return semantic_bundle_digest(records)


def validate_contract_fixtures(schema_path: Path, fixture_root: Path) -> int:
    """Validate checked-in positive and negative source-free contract fixtures."""
    schema = _load_object(schema_path)
    valid_paths = sorted(fixture_root.glob("valid_*.json"))
    if not valid_paths:
        raise ValueError(
            f"response-inventory fixture directory has no valid bundles: {fixture_root}"
        )
    count = 0
    for path in valid_paths:
        fixture = _load_object(path)
        records = _materialize_fixture_records(_record_list(fixture, path))
        digest = validate_record_bundle(records, schema)
        reversed_digest = validate_record_bundle(list(reversed(records)), schema)
        if digest != reversed_digest:
            raise ValueError(f"fixture is not discovery-order deterministic: {path}")
        count += 1

    invalid_path = fixture_root / "invalid_cases.json"
    invalid = _load_object(invalid_path)
    cases = invalid.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"invalid fixture cases are absent: {invalid_path}")
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("expected_error"), str):
            raise ValueError(f"invalid fixture case is malformed: {invalid_path}")
        record_templates = case.get("records")
        if not isinstance(record_templates, list) or not all(
            isinstance(item, dict) for item in record_templates
        ):
            raise ValueError(f"invalid fixture records are malformed: {invalid_path}")
        try:
            records = _materialize_fixture_records(record_templates)
            validate_record_bundle(records, schema)
        except ValueError as error:
            if case["expected_error"] not in str(error):
                raise ValueError(
                    f"invalid fixture {case.get('case_id')} raised unexpected error: {error}"
                ) from error
        else:
            raise ValueError(f"invalid fixture unexpectedly passed: {case.get('case_id')}")
        count += 1
    return count


def validate_managed_files(
    inventory: Mapping[str, Any], root: Path, *, excluded_paths: Iterable[str] = ()
) -> int:
    """Verify one managed inventory against an exact contained file set."""
    resolved_root = root.resolve()
    excluded = set(excluded_paths)
    expected = {item["path"]: item for item in inventory["files"]}
    observed = {
        path.relative_to(resolved_root).as_posix(): path
        for path in resolved_root.rglob("*")
        if path.is_file() and path.relative_to(resolved_root).as_posix() not in excluded
    }
    if set(expected) != set(observed):
        raise ValueError("managed-file inventory does not close the exact file set")
    require_digest = inventory["stage"] == "05g"
    for relative_path, reference in expected.items():
        _validate_artifact_reference(reference, require_digest=require_digest)
        path = observed[relative_path]
        if path.stat().st_size != reference["byte_size"]:
            raise ValueError(f"managed file size differs from inventory: {relative_path}")
        if reference["sha256"] is not None:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != reference["sha256"]:
                raise ValueError(f"managed file digest differs from inventory: {relative_path}")
    return len(observed)


def _validate_diagnostics(
    records: Sequence[JsonObject],
    by_id: Mapping[str, JsonObject],
    mentions: Mapping[str, JsonObject],
    closed_stages: set[str],
) -> None:
    terminal_subjects: set[str] = set()
    for diagnostic in _records_of_type(records, "diagnostic").values():
        if diagnostic["subject_ids"] != sorted(set(diagnostic["subject_ids"])):
            raise ValueError("diagnostic subject_ids must be sorted and unique")
        if diagnostic["evidence_ids"] != sorted(set(diagnostic["evidence_ids"])):
            raise ValueError("diagnostic evidence_ids must be sorted and unique")
        for record_id in diagnostic["subject_ids"] + diagnostic["evidence_ids"]:
            if record_id not in by_id:
                raise ValueError(f"diagnostic references missing record: {record_id}")
        if diagnostic["terminal"]:
            terminal_subjects.update(diagnostic["subject_ids"])

    resolved_mentions = {
        evidence_id
        for edge in _records_of_type(records, "semantic_edge").values()
        for evidence_id in edge["evidence_ids"]
        if evidence_id in mentions
    }
    resolved_mentions.update(
        link["mention_id"] for link in _records_of_type(records, "draft_eir_link").values()
    )
    required_domains: set[str] = set()
    if closed_stages & {"05e", "05f", "05g"}:
        required_domains.add("intra_volume")
    if closed_stages & {"05f", "05g"}:
        required_domains.update({"draft_eir", "final_eir", "appendix_q", "external", "unknown"})
    for mention_id, mention in mentions.items():
        if (
            mention["reference_domain"] in required_domains
            and mention_id not in resolved_mentions
            and mention_id not in terminal_subjects
        ):
            raise ValueError(f"reference mention lacks resolved or terminal outcome: {mention_id}")


def _validate_placement(records: Sequence[JsonObject], units: Mapping[str, JsonObject]) -> None:
    exceptions = _records_of_type(records, "source_placement_exception")
    general_numbers = {
        unit["official_label"].strip().lower()
        for unit in units.values()
        if unit["unit_kind"] == "general_response"
    }
    allowed = {f"general response {number}" for number in range(1, 9)}
    if not general_numbers.issubset(allowed):
        raise ValueError("Volume 4 General Response labels are limited to 1-8")
    for exception in exceptions.values():
        if exception["exception_code"] != "general_response_9_not_in_volume_4":
            raise ValueError("unsupported source-placement exception")


def _validate_corrections(records: Sequence[JsonObject], by_id: Mapping[str, JsonObject]) -> None:
    for correction in _records_of_type(records, "correction").values():
        for target_id in correction["target_ids"]:
            if target_id not in by_id:
                raise ValueError(f"correction target is missing: {target_id}")
        for replacement_id in correction["replacement_ids"]:
            if replacement_id not in by_id:
                raise ValueError(f"correction replacement is missing: {replacement_id}")
        structural = correction["correction_kind"] in {"resegment", "reanchor", "relink"}
        if correction["requires_replay"] != structural:
            raise ValueError("correction replay flag contradicts correction kind")
        if correction["correction_kind"] == "text_overlay" and not correction["replacement_text"]:
            raise ValueError("text overlay correction requires replacement_text")
        if (
            correction["correction_kind"] == "text_overlay"
            and not correction["transcription_method"]
        ):
            raise ValueError("text overlay correction requires a transcription method")
        if correction["correction_kind"] != "text_overlay" and correction["transcription_method"]:
            raise ValueError("only text overlays may carry a transcription method")
        if (
            correction["correction_kind"] == "metadata_disposition"
            and not correction["disposition"]
        ):
            raise ValueError("metadata correction requires a disposition")
        if correction["correction_kind"] != "metadata_disposition" and correction["disposition"]:
            raise ValueError("only metadata corrections may carry a disposition")
        if structural and not correction["replacement_ids"]:
            raise ValueError("structural correction requires replacement IDs")


def _validate_mention_text(
    mention: JsonObject,
    units: Mapping[str, JsonObject],
    spans: Mapping[str, JsonObject],
    pages: Mapping[str, JsonObject],
) -> None:
    mention_span = spans[mention["mention_span_id"]]
    unit = units[mention["source_unit_id"]]
    unit_fragments = [
        fragment for span_id in unit["span_ids"] for fragment in spans[span_id]["fragments"]
    ]
    text_parts: list[str] = []
    for fragment in mention_span["fragments"]:
        if not any(
            container["page_id"] == fragment["page_id"]
            and container["text_start"] <= fragment["text_start"]
            and container["text_end"] >= fragment["text_end"]
            for container in unit_fragments
        ):
            raise ValueError("reference mention span is outside its source unit")
        page_text = pages[fragment["page_id"]]["raw_text"]
        text_parts.append(page_text[fragment["text_start"] : fragment["text_end"]])
    digest = hashlib.sha256("".join(text_parts).encode("utf-8")).hexdigest()
    if digest != mention["raw_text_sha256"]:
        raise ValueError("reference mention digest differs from its raw source span")


def _validate_edge_evidence(
    edge: JsonObject,
    units: Mapping[str, JsonObject],
    mentions: Mapping[str, JsonObject],
    memberships: Mapping[str, JsonObject],
    by_id: Mapping[str, JsonObject],
) -> None:
    source = units[edge["source_unit_id"]]
    target = units[edge["target_unit_id"]]
    marker_evidence: set[str] = set()
    for evidence_id in edge["evidence_ids"]:
        if evidence_id in mentions:
            mention = mentions[evidence_id]
            if mention["reference_domain"] != "intra_volume":
                raise ValueError("semantic edge mention evidence must be intra_volume")
            forward = (
                mention["source_unit_id"] == source["unit_id"]
                and target["official_label"] in mention["target_labels"]
            )
            if not forward:
                raise ValueError("semantic edge mention evidence does not name an endpoint")
        elif evidence_id in memberships:
            membership = memberships[evidence_id]
            if (
                edge["relation_type"] != "general_response_membership"
                or membership["general_response_unit_id"] != source["unit_id"]
                or membership["target_label"] != target["official_label"]
            ):
                raise ValueError("membership evidence does not support the semantic edge")
        else:
            marker = by_id[evidence_id]
            marker_evidence.add(evidence_id)
            if edge["relation_type"] != "comment_response" or marker["disposition"] != "unit_start":
                raise ValueError("marker evidence does not support the semantic edge")
    if marker_evidence and marker_evidence != {
        source["start_marker_id"],
        target["start_marker_id"],
    }:
        raise ValueError("direct-pair edge must retain both endpoint markers")


def _validate_inventories(
    inventories: Mapping[str, JsonObject], activities: Mapping[str, JsonObject]
) -> None:
    for inventory in inventories.values():
        _require_ref(inventory["activity_id"], activities, expected_type="activity")
        if activities[inventory["activity_id"]]["stage"] != inventory["stage"]:
            raise ValueError("managed inventory stage differs from its activity")
        dependency_keys = [
            (item["role"], item["identity"], item["path"]) for item in inventory["dependencies"]
        ]
        if dependency_keys != sorted(dependency_keys) or len(dependency_keys) != len(
            set(dependency_keys)
        ):
            raise ValueError("managed inventory dependencies must be sorted and unique")
        dependency_roles = [item["role"] for item in inventory["dependencies"]]
        if len(dependency_roles) != len(set(dependency_roles)):
            raise ValueError("managed inventory dependency roles must be unique")
        for dependency in inventory["dependencies"]:
            _validate_dependency_reference(dependency)
        paths = [item["path"] for item in inventory["files"]]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("managed inventory files must have sorted unique paths")
        for reference in inventory["files"]:
            _validate_artifact_reference(reference, require_digest=False)
        if inventory["stage"] == "05g" and any(
            item["sha256"] is None for item in inventory["files"]
        ):
            raise ValueError("05G managed files require publication-time SHA-256 digests")


def _validate_activity_scopes(
    activities: Mapping[str, JsonObject], pages: Mapping[str, JsonObject]
) -> None:
    for activity_id, activity in activities.items():
        input_keys = [
            (item["role"], item["identity"], item["path"]) for item in activity["input_refs"]
        ]
        if input_keys != sorted(input_keys) or len(input_keys) != len(set(input_keys)):
            raise ValueError("activity input references must have sorted unique paths")
        input_roles = [item["role"] for item in activity["input_refs"]]
        if len(input_roles) != len(set(input_roles)):
            raise ValueError("activity input dependency roles must be unique")
        for item in activity["input_refs"]:
            _validate_dependency_reference(item)
        required_roles = {
            "05c": {"source_record", "task05a_completion"},
            "05d": {"source_record", "task05c_completion"},
            "05e": {"task05d_completion"},
            "05f": {
                "task04a_registry",
                "task04d_handoff",
                "task05d_completion",
                "task05e_completion",
            },
            "05g": {"task05d_completion", "task05e_completion", "task05f_completion"},
        }[activity["stage"]]
        if not required_roles.issubset({item["role"] for item in activity["input_refs"]}):
            raise ValueError("activity is missing a required stage dependency role")
        ranges = activity["page_ranges"]
        if activity["stage"] in {"05c", "05d"}:
            if not activity["source_id"] or not ranges:
                raise ValueError("05C/05D activity requires an explicit source and page ranges")
            expected_pages: list[int] = []
            for start, end in ranges:
                if end < start:
                    raise ValueError("activity page range ends before it starts")
                expected_pages.extend(range(start, end + 1))
            if expected_pages != sorted(set(expected_pages)):
                raise ValueError("activity page ranges must be ordered and non-overlapping")
            observed_pages = sorted(
                page["physical_page"]
                for page in pages.values()
                if page["activity_id"] == activity_id
            )
            if observed_pages != expected_pages:
                raise ValueError("activity page records do not close the declared page ranges")
            if any(
                page["source_id"] != activity["source_id"]
                for page in pages.values()
                if page["activity_id"] == activity_id
            ):
                raise ValueError("activity page records cross source identities")
        elif activity["source_id"] is not None or ranges:
            raise ValueError("non-source activity cannot declare source page ranges")


def _validate_derived_activities(
    records: Sequence[JsonObject], activities: Mapping[str, JsonObject]
) -> None:
    allowed_stages = {
        "semantic_edge": {"05e"},
        "draft_eir_link": {"05f"},
        "diagnostic": {"05c", "05d", "05e", "05f", "05g"},
        "source_placement_exception": {"05c", "05d"},
        "correction": {"05g"},
        "review_view": {"05e", "05g"},
    }
    for record_type, stages in allowed_stages.items():
        for record in _records_of_type(records, record_type).values():
            activity_id = record["activity_id"]
            _require_ref(activity_id, activities, expected_type="activity")
            if activities[activity_id]["stage"] not in stages:
                raise ValueError(f"{record_type} has an activity from the wrong stage")
            if record_type == "diagnostic" and activities[activity_id]["stage"] != record["stage"]:
                raise ValueError("diagnostic stage differs from its activity")
    for record_type in ("page", "source_unit"):
        for record in _records_of_type(records, record_type).values():
            activity = activities[record["activity_id"]]
            if activity["stage"] not in {"05c", "05d"}:
                raise ValueError(f"{record_type} has an activity from the wrong stage")
            if activity["source_id"] != record["source_id"]:
                raise ValueError(f"{record_type} source differs from its activity")


def _validate_views(
    records: Sequence[JsonObject],
    units: Mapping[str, JsonObject],
    spans: Mapping[str, JsonObject],
    by_id: Mapping[str, JsonObject],
) -> None:
    for view in _records_of_type(records, "review_view").values():
        _require_ref(view["root_unit_id"], units, expected_type="source_unit")
        _require_list_refs(view, "ordered_unit_ids", units)
        _require_list_refs(view, "anchor_span_ids", spans)
        _require_list_refs(view, "edge_ids", by_id, expected_type="semantic_edge")


def _require_text_interval(record: Mapping[str, Any], text: str) -> None:
    start = record["text_start"]
    end = record["text_end"]
    if start < 0 or end <= start or end > len(text):
        raise ValueError(f"invalid half-open raw-text interval: {start}:{end}")
    slot_start = record.get("character_slot_start")
    slot_end = record.get("character_slot_end")
    if (slot_start is None) != (slot_end is None):
        raise ValueError("PDFium character-slot interval must be wholly present or null")
    if slot_start is not None and (slot_start < 0 or slot_end <= slot_start):
        raise ValueError("invalid PDFium character-slot interval")


def _validate_page_box(page: Mapping[str, Any]) -> None:
    box = page["page_box"]
    if not math.isfinite(box["width_points"]) or not math.isfinite(box["height_points"]):
        raise ValueError("page box dimensions must be finite")


def _validate_artifact_reference(reference: Mapping[str, Any], *, require_digest: bool) -> None:
    path = Path(reference["path"])
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"artifact path is not portable: {reference['path']}")
    if require_digest and reference["sha256"] is None:
        raise ValueError("sealed artifact reference requires a SHA-256 digest")


def _validate_dependency_reference(reference: Mapping[str, Any]) -> None:
    path = Path(reference["path"])
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"dependency path is not portable: {reference['path']}")


def _validate_bbox(bbox: Sequence[float], page: Mapping[str, Any]) -> None:
    left, bottom, right, top = bbox
    if not all(math.isfinite(value) for value in bbox):
        raise ValueError("PDF geometry must be finite")
    tolerance = 1.0
    if (
        right < left
        or top < bottom
        or left < -tolerance
        or bottom < -tolerance
        or right > page["page_box"]["width_points"] + tolerance
        or top > page["page_box"]["height_points"] + tolerance
    ):
        raise ValueError("PDF geometry falls outside the displayed page box")


def _require_refs(
    record: Mapping[str, Any], fields: Iterable[str], records: Mapping[str, Any]
) -> None:
    for field in fields:
        _require_ref(record[field], records)


def _require_ref(
    record_id: str, records: Mapping[str, Any], expected_type: str | None = None
) -> None:
    if record_id not in records:
        raise ValueError(f"missing referenced record: {record_id}")
    if expected_type is not None and records[record_id]["record_type"] != expected_type:
        raise ValueError(f"referenced record has wrong type: {record_id}")


def _require_list_refs(
    record: Mapping[str, Any],
    field: str,
    records: Mapping[str, Any],
    expected_type: str | None = None,
) -> None:
    for record_id in record[field]:
        _require_ref(record_id, records, expected_type=expected_type)


def _records_of_type(records: Sequence[JsonObject], record_type: str) -> dict[str, JsonObject]:
    return {
        _record_id(record): record for record in records if record["record_type"] == record_type
    }


def _record_id(record: Mapping[str, Any]) -> str:
    record_type = record.get("record_type")
    if not isinstance(record_type, str) or record_type not in ID_RULES:
        raise ValueError(f"unknown record_type: {record_type!r}")
    id_field = ID_RULES[record_type][0]
    record_id = record.get(id_field)
    if not isinstance(record_id, str):
        raise ValueError(f"record is missing {id_field}")
    return record_id


def _is_general_response_nine(label: str) -> bool:
    return label.strip().lower() in {"general response 9", "general response no. 9"}


def _identity_value(record_type: str, field: str, value: Any) -> Any:
    """Keep spatial and visual evidence outside stable text-span identity."""
    if record_type == "source_span" and field == "fragments":
        return [
            {
                "page_id": fragment["page_id"],
                "text_start": fragment["text_start"],
                "text_end": fragment["text_end"],
            }
            for fragment in value
        ]
    return value


def _semantic_record(record: Mapping[str, Any]) -> JsonObject:
    """Remove runtime-only timestamps before hashing semantic bundle content."""
    return {
        key: value for key, value in record.items() if key not in {"recorded_at", "completed_at"}
    }


def _load_object(path: Path) -> JsonObject:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _record_list(fixture: JsonObject, path: Path) -> list[JsonObject]:
    records = fixture.get("records")
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"fixture records must be JSON objects: {path}")
    return records


def _materialize_fixture_records(templates: Sequence[JsonObject]) -> list[JsonObject]:
    """Resolve readable ``@key`` fixture references and derive their stable IDs."""
    remaining = [dict(template) for template in templates]
    materialized: list[JsonObject] = []
    aliases: dict[str, str] = {}
    while remaining:
        progressed = False
        deferred: list[JsonObject] = []
        for template in remaining:
            key = template.get("fixture_key")
            if not isinstance(key, str) or not key:
                raise ValueError("fixture record requires a non-empty fixture_key")
            record = {
                field: _replace_fixture_aliases(value, aliases)
                for field, value in template.items()
                if field != "fixture_key"
            }
            if _contains_fixture_alias(record):
                deferred.append(template)
                continue
            record_type = record.get("record_type")
            if not isinstance(record_type, str) or record_type not in ID_RULES:
                raise ValueError(f"fixture has unknown record_type: {record_type!r}")
            id_field = ID_RULES[record_type][0]
            record.setdefault(id_field, build_record_id(record))
            aliases[key] = str(record[id_field])
            materialized.append(record)
            progressed = True
        if not progressed:
            keys = [str(record.get("fixture_key")) for record in deferred]
            raise ValueError(f"fixture aliases are unresolved or cyclic: {keys}")
        remaining = deferred
    return materialized


def _replace_fixture_aliases(value: Any, aliases: Mapping[str, str]) -> Any:
    if isinstance(value, str) and value.startswith("@"):
        return aliases.get(value[1:], value)
    if isinstance(value, list):
        return [_replace_fixture_aliases(item, aliases) for item in value]
    if isinstance(value, dict):
        return {key: _replace_fixture_aliases(item, aliases) for key, item in value.items()}
    return value


def _contains_fixture_alias(value: Any) -> bool:
    if isinstance(value, str):
        return value.startswith("@")
    if isinstance(value, list):
        return any(_contains_fixture_alias(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_fixture_alias(item) for item in value.values())
    return False


__all__ = [
    "ID_RULES",
    "SCHEMA_VERSION",
    "build_record_id",
    "build_publication_id",
    "semantic_bundle_digest",
    "validate_contract_fixtures",
    "validate_managed_files",
    "validate_record_bundle",
]
