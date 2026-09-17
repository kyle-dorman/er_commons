"""Closed population, deterministic output and sealed-target comparison for Task 05G."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256, read_json_object
from er_commons.response_inventory.reference_baseline import _indexes
from er_commons.response_inventory.reference_replay_resolver import DEPENDENCY_ROLES, keyed

type JsonObject = dict[str, Any]


def validate_population(baseline: list[JsonObject], population: JsonObject) -> None:
    """Require exact frozen IDs, baseline partition, reconciliation and collision membership."""
    rows = keyed(baseline, "mention_id")
    frozen = keyed(population["baseline_outcomes"], "mention_id")
    if set(rows) != set(frozen):
        raise ValueError("frozen baseline mention population differs")
    for mention_id, projection in frozen.items():
        if any(rows[mention_id].get(key) != value for key, value in projection.items()):
            raise ValueError(f"frozen baseline outcome differs: {mention_id}")
    counts = {
        "total": len(rows),
        "links": sum(row["outcome"] == "resolved" for row in rows.values()),
        "explicit_nonlinks": sum(row["outcome"] == "terminal_nonlink" for row in rows.values()),
    }
    if counts != population["baseline_counts"]:
        raise ValueError("frozen baseline partition differs")
    for group, members in population["reconciliation"].items():
        if len(members) != len(set(members)) or not set(members) <= set(rows):
            raise ValueError(f"invalid reconciliation membership: {group}")
    reason_groups = {
        "f1_mentions": "upstream_source_identity_repair_required",
        "figure_mentions": "exact_figure_target_absent",
        "chapter_8_9_mentions": "exact_alias_only_outside_routed_source",
        "collision_sets": "exact_target_collision",
        "comment_authored_exclusions": "comment_authored_reference_no_official_response_link",
        "appendix_q_outcomes": "appendix_q_verification_required",
    }
    for group, reason in reason_groups.items():
        if group in population["reconciliation"] and set(population["reconciliation"][group]) != {
            key for key, row in rows.items() if row["terminal_reason"] == reason
        }:
            raise ValueError(f"reconciliation membership differs: {group}")
    groups = population["reconciliation"]
    if "draft_response_mentions" in groups and set(groups["draft_response_mentions"]) != {
        key for key, row in rows.items() if row["reference_domain"] == "draft_eir"
    }:
        raise ValueError("Draft EIR reconciliation membership differs")
    if "appendix_a_impacts" in groups and set(groups["appendix_a_impacts"]) != {
        key
        for key, row in rows.items()
        if row["routed_source_ids"] == ["deir_appendix_a"]
        and row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
    }:
        raise ValueError("Appendix A reconciliation membership differs")
    if "specific_target_protection" in population and set(
        population["specific_target_protection"]
    ) != {
        key
        for key, row in rows.items()
        if row["requested_target_type"] != "document"
        or row["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
    }:
        raise ValueError("specific-target protection membership differs")
    for mention_id, candidates in population["collision_candidates"].items():
        if rows[mention_id]["compatible_target_ids"] != candidates:
            raise ValueError(f"baseline collision options differ: {mention_id}")


def validate_result(
    result: JsonObject,
    baseline_outcomes: list[JsonObject],
    population: JsonObject,
    *,
    expected_result: JsonObject | None = None,
) -> None:
    """Validate independent loaded output closure against fresh deterministic pure resolution."""
    validate_population(baseline_outcomes, population)
    schema_root = (
        Path(__file__).resolve().parents[3] / "benchmarks/er_bench/schemas/response_inventory/v6"
    )
    outcome_schema = Draft202012Validator(
        read_json_object(schema_root / "reference_outcome.schema.json")
    )
    record_schema = Draft202012Validator(read_json_object(schema_root / "records.schema.json"))
    outcomes = keyed(result["outcomes"], "mention_id")
    baseline_ids = set(keyed(baseline_outcomes, "mention_id"))
    if set(outcomes) != baseline_ids:
        raise ValueError("replay outcomes do not close baseline population")
    links = keyed(result["links"], "mention_id")
    diagnostics = keyed(result["diagnostics"], "mention_id")
    if set(links) & set(diagnostics) or set(links) | set(diagnostics) != baseline_ids:
        raise ValueError("link/nonlink partition is conflicting or incomplete")
    f1_ids = set(population["reconciliation"].get("f1_mentions", []))
    for row in result["outcomes"]:
        outcome_schema.validate(row)
        if row["mention_id"] in f1_ids:
            warning = row["final_f1_warning"]
            binding = population["final_f1_warning_binding"]
            if warning is None or warning["binding"] != binding:
                raise ValueError("Final F1 warning binding differs")
            specific = [
                entry
                for entry in binding["response_specific"]
                if row["mention_id"] in entry["mention_ids"]
            ]
            if warning["response_specific"] != specific or any(
                entry["unit_id"] != row["source_unit_id"] for entry in specific
            ):
                raise ValueError("Final F1 response-specific warning differs")
        elif (
            population.get("final_f1_warning_binding") is not None
            and row["final_f1_warning"] is not None
        ):
            raise ValueError("Final F1 warning attached outside frozen population")
        _validate_identity(row, "outcome_id", "outcomev2-")
        mention_id = row["mention_id"]
        if [item["role"] for item in row["input_refs"]] != list(DEPENDENCY_ROLES):
            raise ValueError("outcome dependency roles differ")
        annotations = keyed(row["target_annotations"], "target_id")
        if sorted(annotations) != row["compatible_target_ids"]:
            raise ValueError("candidate annotation coverage differs")
        for annotation in annotations.values():
            if annotation["target_type"] != row["requested_target_type"]:
                raise ValueError("target annotation type differs")
            if annotation["source_id"] not in row["routed_source_ids"]:
                raise ValueError("target annotation source differs")
            if annotation["target_type"] == "figure" and (
                annotation["text_only_model_eligibility"] is not False
                or annotation["target_limitation"] is None
            ):
                raise ValueError("figure cannot become text-only evidence")
        if row["outcome"] == "resolved":
            link = links.get(mention_id)
            if (
                link is None
                or row["terminal_reason"] is not None
                or row["link_id"] != link["link_id"]
                or row["compatible_target_ids"] != [link["target_id"]]
            ):
                raise ValueError("resolved outcome/link is inconsistent")
            if (
                link["target_annotation"] != annotations[link["target_id"]]
                or link["final_f1_warning"] != row["final_f1_warning"]
                or link["input_refs"] != row["input_refs"]
                or link["resolver_rule"] != row["resolver_rule"]
                or link["source_unit_id"] != row["source_unit_id"]
            ):
                raise ValueError("link annotation or dependency differs")
            if row["source_kind"] == "comment" or row["reference_domain"] == "appendix_q":
                raise ValueError("excluded reference became a link")
        elif (
            not row["terminal_reason"]
            or row["link_id"] is not None
            or mention_id not in diagnostics
        ):
            raise ValueError("nonlink lacks terminal diagnostic")
        else:
            diagnostic = diagnostics[mention_id]
            if (
                diagnostic["terminal_reason"] != row["terminal_reason"]
                or diagnostic["mention_span_id"] != row["mention_span_id"]
                or diagnostic["input_refs"] != row["input_refs"]
            ):
                raise ValueError("terminal diagnostic differs")
    expected_census = {
        "total": len(outcomes),
        "links": len(links),
        "explicit_nonlinks": len(diagnostics),
        "terminal_reasons": dict(
            sorted(
                Counter(
                    row["terminal_reason"]
                    for row in outcomes.values()
                    if row["terminal_reason"] is not None
                ).items()
            )
        ),
    }
    if result["census"] != expected_census:
        raise ValueError("outcome census differs")
    for collection, identity, prefix in (
        (result["links"], "link_id", "linkv2-"),
        (result["diagnostics"], "diagnostic_id", "diagnosticv2-"),
    ):
        keyed(collection, identity)
        for row in collection:
            record_schema.validate(row)
            _validate_identity(row, identity, prefix)
    forward, reverse = _indexes(result["outcomes"], result["links"])
    if result["forward"] != forward or result["reverse"] != reverse:
        raise ValueError("forward/reverse index closure differs")
    if expected_result is not None and result != expected_result:
        raise ValueError(
            "replay differs from deterministic resolution or warning/limitation coverage"
        )


def _validate_identity(row: JsonObject, field: str, prefix: str) -> None:
    """Reject modified records even when their path and cardinality still match."""
    content = {key: value for key, value in row.items() if key != field}
    if row.get(field) != prefix + canonical_json_sha256(content):
        raise ValueError(f"record content identity differs: {field}")


def _added_target_ids(correspondence: JsonObject) -> set[str]:
    """Return only new target IDs explicitly authorized by the sealed target comparison."""
    return set(correspondence.get("authorized_added_target_ids", []))


def compare_outcomes(
    baseline: list[JsonObject],
    current: list[JsonObject],
    *,
    population: JsonObject,
    correspondence: JsonObject,
    approved_inner_rules: bool = False,
    approved_header_rules: bool = False,
) -> JsonObject:
    """Retain full before/after rows and fail closed on an unexplained semantic delta."""
    validate_population(baseline, population)
    before, after = keyed(baseline, "mention_id"), keyed(current, "mention_id")
    if set(before) != set(after):
        raise ValueError("comparison population differs")
    mapping_rows = keyed(correspondence["target_mapping"], "baseline_target_id")
    mapping = {key: row["selected_target_id"] for key, row in mapping_rows.items()}
    added = _added_target_ids(correspondence)
    rows = []
    for mention_id, old in sorted(before.items()):
        new = after[mention_id]
        for field in (
            "mention_span_id",
            "source_unit_id",
            "raw_text_sha256",
            "reference_domain",
            "source_kind",
        ):
            if old[field] != new[field]:
                raise ValueError(f"immutable comparison field differs: {field}")
        inner_change = (
            approved_inner_rules
            and old["requested_target_type"] == "document"
            and new["resolver_rule"] == "task05g_general_inner_reference_v1"
            and new.get("inner_reference_evidence")
            and new["requested_target_type"] in {"section", "table", "page"}
            and new["outcome"] == "resolved"
        )
        old_ids = old["compatible_target_ids"]
        new_ids = new["compatible_target_ids"]
        mapped = [mapping.get(value, value) for value in old_ids]
        same = (
            old["outcome"] == new["outcome"]
            and old["terminal_reason"] == new["terminal_reason"]
            and sorted(mapped) == new_ids
            and old["routed_source_ids"] == new["routed_source_ids"]
            and old["requested_target_type"] == new["requested_target_type"]
        )
        for candidate_field in ("global_candidate_target_ids", "source_candidate_target_ids"):
            old_options = set(mapping.get(value, value) for value in old.get(candidate_field, []))
            new_options = set(new.get(candidate_field, []))
            # F1 had no queried options before its separately verified substitution.
            if not inner_change and mention_id not in population["reconciliation"].get(
                "f1_mentions", []
            ):
                if old_options - new_options or not new_options - old_options <= added:
                    raise ValueError(f"unexplained candidate-option delta: {mention_id}")
        header_change = (
            approved_header_rules
            and old["terminal_reason"] == "exact_target_collision"
            and old["requested_target_type"] == new["requested_target_type"] == "section"
            and old["routed_source_ids"] == new["routed_source_ids"]
            and new["resolver_rule"] == "task05g_header_qualified_section_v1"
            and new["outcome"] == "resolved"
            and len(new_ids) == 1
            and set(new_ids) < set(mapped)
            and set(new.get("header_qualification_evidence", {}).get("excluded_targets", {}))
            == set(mapped) - set(new_ids)
        )
        classification = None
        if inner_change:
            classification = "approved_general_inner_reference"
        elif header_change:
            classification = "approved_header_qualification"
        elif same:
            classification = "namespace_only" if old_ids != new_ids else "review_annotation"
        elif (
            mention_id in population["reconciliation"].get("f1_mentions", [])
            and old["terminal_reason"] == "upstream_source_identity_repair_required"
            and new["final_f1_warning"] is not None
            and new["routed_source_ids"] == ["feir_appendix_f1"]
        ):
            classification = "accepted_source_substitution"
        elif (
            old["outcome"] == "terminal_nonlink"
            and old["terminal_reason"]
            in {
                "exact_target_absent",
                "exact_alias_only_outside_routed_source",
                "exact_figure_target_absent",
            }
            and old["requested_target_type"] == new["requested_target_type"]
            and old["routed_source_ids"] == new["routed_source_ids"]
            and new_ids
            and set(new_ids) <= added
        ):
            classification = (
                "accepted_figure_target_availability"
                if new["requested_target_type"] == "figure"
                else "accepted_structural_repair"
            )
        if classification is None:
            raise ValueError(f"unexplained replay delta: {mention_id}")
        if old["outcome"] == "resolved" and new["outcome"] != "resolved":
            raise ValueError(f"historical link lost: {mention_id}")
        if (
            old["requested_target_type"] not in {None, "document"}
            and new["requested_target_type"] == "document"
        ):
            raise ValueError("specific target downgraded to document")
        if (
            old["terminal_reason"] == "more_specific_appendix_target_requires_resolution"
            and new["outcome"] == "resolved"
            and new["requested_target_type"] == "document"
        ):
            raise ValueError("attached specific appendix target downgraded")
        rows.append(
            {
                "mention_id": mention_id,
                "changed": True,
                "classification": classification,
                "before": old,
                "after": new,
                "baseline_collision_options": population["collision_candidates"].get(
                    mention_id, []
                ),
                "selected_collision_options": new_ids,
                "baseline_target_correspondence": [mapping_rows.get(value) for value in old_ids],
                "populations": [
                    name for name, ids in population["reconciliation"].items() if mention_id in ids
                ],
            }
        )
    return {
        "census": {
            "total": len(rows),
            "links": sum(row["outcome"] == "resolved" for row in current),
            "explicit_nonlinks": sum(row["outcome"] == "terminal_nonlink" for row in current),
        },
        "schema_version": "er_commons.task05g.comparison.v1",
        "rows": rows,
        "baseline_counts": population["baseline_counts"],
        "classifications": dict(sorted(Counter(row["classification"] for row in rows).items())),
        "link_gains": sum(
            old["outcome"] != "resolved" and after[key]["outcome"] == "resolved"
            for key, old in before.items()
        ),
        "link_losses": sum(
            old["outcome"] == "resolved" and after[key]["outcome"] != "resolved"
            for key, old in before.items()
        ),
        "residual_census": dict(
            sorted(
                Counter(
                    row["terminal_reason"] for row in current if row["terminal_reason"] is not None
                ).items()
            )
        ),
    }


def validate_activity(
    activity: JsonObject,
    result: JsonObject,
    *,
    expected_input_refs: list[JsonObject],
    expected_activity_id: str,
) -> None:
    """Verify v6 activity and exact provenance parity across every derived record."""
    schema_root = (
        Path(__file__).resolve().parents[3] / "benchmarks/er_bench/schemas/response_inventory/v6"
    )
    Draft202012Validator(read_json_object(schema_root / "records.schema.json")).validate(activity)
    if activity["record_type"] != "activity" or activity["activity_id"] != expected_activity_id:
        raise ValueError("Task 05G activity identity differs")
    if activity["input_refs"] != expected_input_refs or [
        entry["role"] for entry in expected_input_refs
    ] != list(DEPENDENCY_ROLES):
        raise ValueError("Task 05G activity dependency binding differs")
    for name in ("outcomes", "links", "diagnostics"):
        for row in result[name]:
            if row["input_refs"] != expected_input_refs:
                raise ValueError("Task 05G output dependency differs from activity")
            if name != "outcomes" and row["activity_id"] != expected_activity_id:
                raise ValueError("Task 05G output activity identity differs")
