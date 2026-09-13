"""Source-free correspondence and comparison closure for Task 06G."""

from __future__ import annotations

import copy
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from er_commons.collection_processing.authority_refs import CollectionArtifactResolver
from er_commons.document_records.document_structure.constants import (
    MISSING_CHAPTER_CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
    REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH,
)
from er_commons.document_records.document_structure.publication import (
    verify_completed_document_structure,
)
from er_commons.document_records.document_structure.support import (
    MISSING_CHAPTER_CORRESPONDENCE_PATH,
    REPEATED_HEADING_CORRESPONDENCE_PATH,
)
from er_commons.task06g.comparison_links import (
    compare_link_populations,
    load_collection_link_evidence,
    load_task04c_inherited_targets,
)
from er_commons.task06g.core import (
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    publish_directory_no_clobber,
    reference,
    verify_reference,
)

BASELINE_SCOPE_ID = "scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da"
BASELINE_HANDOFF_ID = "handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1"
BASELINE_COLLECTION_ROOT = Path(
    "pipelines/brisbane_baylands/task_04d_relinked_v1/document_publications"
)
SOURCE_SLOTS_PATH = Path("pipelines/brisbane_baylands/task_06_recovery_v1/06a/source_slots.json")
REVIEW_CORRESPONDENCE_PATH = Path(
    "pipelines/brisbane_baylands/task_06_recovery_v1/06a/review_correspondence_candidates.v1.json"
)
MENTION_POPULATIONS_PATH = Path(
    "pipelines/brisbane_baylands/task_06_recovery_v1/06a/mention_populations.v1.json"
)
REPAIR_ROOTS = {
    "task06d": Path("pipelines/brisbane_baylands/task_06_recovery_v1/06d/qualification_v8"),
    "task06e": Path("pipelines/brisbane_baylands/task_06_recovery_v1/06e/qualification_v17"),
    "task06f": Path("pipelines/brisbane_baylands/task_06_recovery_v1/06f/qualification_v10"),
}
GATE_C_PATH = Path("pipelines/brisbane_baylands/task_04d_gate_c_final_pass1/gate_c_validation.json")
GATE_C_SHA256 = "f64e4b36b647b1fac795a37fc23d0e04d509d1a31f56d60c9f3752e1b16c4526"
REPAIRED_SOURCES = frozenset({"feir_appendix_f1", "deir_appendix_a", "deir_main"})
EXPECTED_CHECKS = {
    "appendix_a_chapter_06_many_to_one",
    "appendix_a_chapter_07_many_to_one",
    "appendix_a_chapter_08_many_to_one",
    "appendix_a_chapter_09_many_to_one",
    "main_chapter_8_addition",
    "main_chapter_9_addition",
    "main_fc1_274_178_96_zero_collision",
    "figure_4_8_absent",
    "preserved_32_semantic_equality_after_mapping",
}
EXPECTED_FIXED_ACCOUNTING = {
    "document_count": 35,
    "page_count": 49_022,
    "task04a_decision_count": 757,
    "task05_mention_count": 511,
    "task05_link_count": 295,
    "task05_nonlink_count": 216,
    "ordinary_reference_count": 5_088,
    "navigation_claim_count": 560,
    "inherited_navigation_link_count": 28,
    "baseline_resolution_decision_count": 72,
}


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be an array of objects")
    return cast(list[JsonObject], value)


def _object(value: object, label: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return cast(JsonObject, value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be nonempty text")
    return value


def _index(rows: list[JsonObject], key: str, label: str) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for row in rows:
        identity = _text(row.get(key), f"{label}.{key}")
        if identity in result:
            raise ValueError(f"duplicate {label} {key}: {identity}")
        result[identity] = row
    return result


def _semantic_target_entry(row: JsonObject) -> JsonObject:
    """Remove namespace-only prefixes while retaining source-local target identity."""
    normalized = copy.deepcopy(row)
    normalized["target_id"] = _collection_target_local_id(
        normalized.get("target_id"), "target entry target_id"
    )
    # Alias record IDs are sequence-bearing publication identities, not semantic
    # entities.  Repairs can insert aliases and deterministically renumber later
    # records without changing their lookup-to-target edge.
    normalized.pop("alias_id", None)
    normalized.pop("source_ordinal", None)
    return normalized


def _target_rows_by_source(bundle: JsonObject) -> dict[str, list[JsonObject]]:
    index = _object(bundle.get("target_index"), "target_index")
    rows = _objects(index.get("entries"), "target_index.entries")
    grouped: dict[str, list[JsonObject]] = {}
    for row in rows:
        grouped.setdefault(_text(row.get("source_id"), "target source_id"), []).append(
            _semantic_target_entry(row)
        )
    return {key: sorted(value, key=_sort_key) for key, value in grouped.items()}


def _sort_key(value: JsonObject) -> tuple[str, ...]:
    return tuple(str(value.get(key, "")) for key in sorted(value))


def _identity_relative(value: object, label: str) -> str:
    text = _text(value, label)
    _, separator, relative = text.partition("/")
    if not separator or not relative:
        raise ValueError(f"{label} lacks an extraction namespace")
    return relative


def _collection_target_local_id(value: object, label: str) -> str:
    """Normalize namespaced or already-local collection target IDs idempotently."""
    text = _text(value, label)
    first, separator, relative = text.partition("/")
    if not separator or not relative:
        raise ValueError(f"{label} lacks a record-type namespace")
    if first in {"document", "page", "section", "table", "figure"}:
        return text
    return relative


def _repair_authorizations(
    *,
    repairs: Mapping[str, JsonObject],
    appendix_a_correspondence: JsonObject,
    main_correspondence: JsonObject,
    baseline: JsonObject,
    replacement: JsonObject,
) -> JsonObject:
    """Derive exact target/entity authorities from sealed repair evidence."""
    if (
        appendix_a_correspondence.get("schema_version")
        != "er_commons.recovery.repeated_heading_correspondence.v1"
    ):
        raise ValueError("Task 06D sealed repeated-heading correspondence schema differs")
    target_authorities: dict[str, list[JsonObject]] = {}
    lookup_authorities: dict[str, list[JsonObject]] = {}

    def authorize_target(
        target: object,
        *,
        owner: str,
        reason: str,
        evidence: JsonObject,
        source_id: str,
        directions: list[str],
        lookup_keys: list[str] | None = None,
        target_type: str | None = None,
        collection_target: bool = False,
    ) -> None:
        relative = (
            _collection_target_local_id(target, "authorized collection target")
            if collection_target
            else _identity_relative(target, "authorized target")
        )
        target_authorities.setdefault(relative, []).append(
            {
                "owner": owner,
                "reason": reason,
                "evidence": evidence,
                "source_id": source_id,
                "directions": directions,
                "lookup_keys": sorted(key.lower() for key in lookup_keys or []),
                "target_type": target_type,
            }
        )

    def authorize_lookup(
        lookup_key: str, *, owner: str, reason: str, evidence: JsonObject, source_id: str
    ) -> None:
        lookup_authorities.setdefault(lookup_key.lower(), []).append(
            {
                "owner": owner,
                "reason": reason,
                "evidence": evidence,
                "source_id": source_id,
            }
        )

    for record in _objects(
        appendix_a_correspondence.get("records"), "Appendix A correspondence records"
    ):
        for target in _objects(record.get("old_targets"), "Appendix A old targets"):
            authorize_target(
                target.get("section_id"),
                owner="task06d",
                reason="sealed_appendix_a_repeated_heading_old_target",
                evidence={
                    "correspondence_candidate_id": appendix_a_correspondence.get("candidate_id"),
                    "chapter_marker": record.get("chapter_marker"),
                },
                source_id="deir_appendix_a",
                directions=["removed", "resolution"],
            )
        new_target = _object(record.get("new_target"), "Appendix A new target")
        authorize_target(
            new_target.get("section_id"),
            owner="task06d",
            reason="sealed_appendix_a_repeated_heading_new_target",
            evidence={
                "correspondence_candidate_id": appendix_a_correspondence.get("candidate_id"),
                "chapter_marker": record.get("chapter_marker"),
            },
            source_id="deir_appendix_a",
            directions=["added", "resolution"],
        )
    task06e_titles: dict[str, str] = {}
    for row in _objects(
        repairs["task06e"].get("eligible_decisions"), "Task 06E eligible decisions"
    ):
        marker = _text(row.get("chapter_marker"), "Task 06E chapter marker")
        chapter_title = _text(row.get("chapter_title"), "Task 06E chapter title")
        if marker in task06e_titles:
            raise ValueError(f"duplicate Task 06E chapter marker: {marker}")
        task06e_titles[marker] = chapter_title
        evidence = {
            "chapter_marker": marker,
            "chapter_title": chapter_title,
            "decision_kind": row.get("decision_kind"),
        }
        for lookup in (f"chapter {marker}", marker, chapter_title):
            authorize_lookup(
                lookup,
                owner="task06e",
                reason="sealed_main_missing_chapter_lookup",
                evidence=evidence,
                source_id="deir_main",
            )
    main_records = _objects(
        main_correspondence.get("records"), "main missing-chapter correspondence records"
    )
    if len(main_records) != 2:
        raise ValueError("main missing-chapter correspondence must contain two records")
    for row in main_records:
        target = _object(row.get("new_target"), "main missing-chapter new target")
        marker = _text(row.get("chapter_marker"), "main correspondence chapter marker")
        matched_chapter_title = task06e_titles.get(marker)
        if matched_chapter_title is None:
            raise ValueError(
                f"main correspondence chapter marker lacks an eligible decision: {marker}"
            )
        authorize_target(
            target.get("section_id"),
            owner="task06e",
            reason="sealed_main_missing_chapter_target",
            evidence={
                "chapter_marker": marker,
                "chapter_title": matched_chapter_title,
                "decision_ref": row.get("decision_ref"),
            },
            source_id="deir_main",
            directions=["added", "resolution"],
            lookup_keys=[marker, f"chapter {marker}", matched_chapter_title],
            target_type="section",
        )
    for row in _objects(repairs["task06f"].get("decisions"), "Task 06F decisions"):
        if row.get("eligibility") == "eligible":
            alias = _text(row.get("normalized_alias"), "Task 06F eligible alias")
            evidence = {
                "normalized_alias": alias,
                "upstream_figure_id": row.get("upstream_figure_id"),
                "reason": row.get("reason"),
            }
            authorize_lookup(
                alias,
                owner="task06f",
                reason="sealed_fc1_eligible_alias",
                evidence=evidence,
                source_id="deir_main",
            )
            authorize_target(
                row.get("upstream_figure_id"),
                owner="task06f",
                reason="sealed_fc1_eligible_figure_target",
                evidence=evidence,
                source_id="deir_main",
                directions=["added", "resolution"],
                lookup_keys=[alias],
                target_type="figure",
            )
    # Task 06C explicitly establishes a new, non-equivalent physical source.  Bind
    # that authority to the exact target entities observed on each side rather
    # than granting a source-wide owner during comparison.
    for bundle, source_id, direction in (
        (baseline, "deir_appendix_f1", "removed"),
        (replacement, "feir_appendix_f1", "added"),
    ):
        rows = _objects(
            _object(bundle.get("target_index"), "Final F1 target index").get("entries"),
            "Final F1 target entries",
        )
        for row in rows:
            if row.get("source_id") != source_id:
                continue
            authorize_target(
                row.get("target_id"),
                owner="task06c",
                reason="sealed_final_f1_no_equivalence_boundary",
                evidence={
                    "physical_source_id": source_id,
                    "boundary": "accepted_source_substitution_without_semantic_equivalence",
                },
                source_id=source_id,
                directions=[direction, "resolution"],
                lookup_keys=[_text(row.get("lookup_key"), "Final F1 lookup_key")],
                target_type=_text(row.get("target_type"), "Final F1 target_type"),
                collection_target=True,
            )
    return {
        "targets": {key: value for key, value in sorted(target_authorities.items())},
        "lookups": {key: value for key, value in sorted(lookup_authorities.items())},
        "final_f1_resolution_sources": {
            "deir_appendix_f1": {
                "owner": "task06c",
                "reason": "sealed_final_f1_no_equivalence_boundary",
            },
            "feir_appendix_f1": {
                "owner": "task06c",
                "reason": "sealed_final_f1_no_equivalence_boundary",
            },
        },
    }


def _resolution_key(row: JsonObject) -> tuple[str, int, str, str]:
    sequence = row.get("candidate_local_sequence")
    if not isinstance(sequence, int):
        raise ValueError("resolution candidate_local_sequence must be an integer")
    mention_id = _text(row.get("mention_id"), "resolution mention_id")
    parts = mention_id.split("/")
    if "cross-reference" not in parts:
        raise ValueError("resolution mention_id lacks a cross-reference source segment")
    marker = parts.index("cross-reference")
    if marker + 1 >= len(parts):
        raise ValueError("resolution mention_id lacks its source ID")
    return (
        parts[marker + 1],
        sequence,
        _text(row.get("mention_class"), "resolution mention_class"),
        _text(row.get("lookup_key"), "resolution lookup_key"),
    )


def _resolution_outcome(row: JsonObject) -> JsonObject:
    targets = []
    for target in _objects(row.get("candidate_targets"), "candidate_targets"):
        target_id = _text(target.get("target_id"), "candidate target_id")
        targets.append(
            {
                "target_source_id": target.get("target_source_id"),
                "target_type": target.get("target_type"),
                "target_local_id": _collection_target_local_id(target_id, "candidate target_id"),
            }
        )
    cross_document = row.get("cross_document_evidence")
    source_family = None
    if isinstance(cross_document, dict):
        source_family = {
            "source_family_id": cross_document.get("source_family_id"),
            "intended_target_source_ids": cross_document.get("intended_target_source_ids"),
            "traversal_rule": cross_document.get("traversal_rule"),
        }
    return {
        "status": row.get("status"),
        "unresolved_reason": row.get("unresolved_reason"),
        "source_family_evidence": source_family,
        "targets": sorted(targets, key=_sort_key),
    }


def _catalog_ref(bundle: JsonObject, label: str) -> JsonObject:
    completion = _object(bundle.get("resolution_completion"), f"{label} resolution")
    manifest = _object(completion.get("mention_input_manifest"), f"{label} mention manifest")
    return _object(manifest.get("source_family_catalog_ref"), f"{label} catalog ref")


def _catalog_rebinding(
    *,
    baseline: JsonObject,
    replacement: JsonObject,
    baseline_catalog: JsonObject,
    replacement_catalog: JsonObject,
) -> JsonObject:
    """Qualify the exact source-family identity change as the accepted F1 substitution."""
    old_ref = _catalog_ref(baseline, "baseline")
    new_ref = _catalog_ref(replacement, "replacement")
    if old_ref.get("sha256") == new_ref.get("sha256"):
        raise ValueError("source-family catalogs did not rebind for Final F1")
    for key in ("schema_version", "catalog_version", "source_family_id"):
        if baseline_catalog.get(key) != replacement_catalog.get(key):
            raise ValueError(f"source-family catalog {key} changed")
    old_sources = _objects(baseline_catalog.get("sources"), "baseline catalog sources")
    new_sources = _objects(replacement_catalog.get("sources"), "replacement catalog sources")
    if len(old_sources) != 35 or len(new_sources) != 35:
        raise ValueError("source-family catalogs must contain exactly 35 sources")
    changed = [
        index
        for index, pair in enumerate(zip(old_sources, new_sources, strict=True))
        if pair[0] != pair[1]
    ]
    if changed != [9]:
        raise ValueError(f"source-family catalog delta differs from Final F1 slot: {changed}")
    old_row = copy.deepcopy(old_sources[9])
    new_row = copy.deepcopy(new_sources[9])
    old_source = _object(old_row.pop("source", None), "baseline catalog Final F1 source")
    new_source = _object(new_row.pop("source", None), "replacement catalog Final F1 source")
    if old_row != new_row:
        raise ValueError("source-family Final F1 routing metadata changed")
    if old_source.get("source_id") != "deir_appendix_f1":
        raise ValueError("baseline source-family catalog lacks Draft F1 at slot 10")
    if new_source.get("source_id") != "feir_appendix_f1":
        raise ValueError("replacement source-family catalog lacks Final F1 at slot 10")
    for bundle, source, label in (
        (baseline, old_source, "baseline"),
        (replacement, new_source, "replacement"),
    ):
        ordered = _objects(
            _object(bundle.get("accounting"), f"{label} accounting").get("ordered_sources"),
            f"{label} ordered sources",
        )
        if any(
            source.get(key) != ordered[9].get(key)
            for key in ("source_id", "sha256", "pdf_page_count")
        ):
            raise ValueError(f"{label} catalog F1 source differs from accounting")
    return {
        "classification": "catalog_rebound",
        "owner": "task06c",
        "reason": "accepted_final_f1_source_substitution",
        "baseline_catalog_ref": old_ref,
        "replacement_catalog_ref": new_ref,
        "changed_slot": 10,
        "baseline_source": old_source,
        "replacement_source": new_source,
        "preserved_routing": old_row,
    }


def _matching_authorities(
    authorizations: JsonObject,
    *,
    target_local_id: str | None,
    source_id: str,
    lookup_key: str,
    target_type: object,
    direction: str,
) -> list[JsonObject]:
    """Return only authorities matching the exact changed entity and operation."""
    matches: list[JsonObject] = []
    targets = _object(authorizations.get("targets"), "target authorizations")
    if target_local_id is not None:
        raw = targets.get(target_local_id, [])
        for authority in _objects(raw, f"authorities for {target_local_id}"):
            allowed_lookups = authority.get("lookup_keys")
            directions = authority.get("directions")
            if (
                authority.get("source_id") == source_id
                and isinstance(directions, list)
                and direction in directions
                and authority.get("target_type") in {None, target_type}
                and (
                    not allowed_lookups
                    or isinstance(allowed_lookups, list)
                    and lookup_key.lower() in allowed_lookups
                )
            ):
                matches.append(authority)
    return matches


def _authorize_target_delta(
    row: JsonObject, *, source_id: str, direction: str, authorizations: JsonObject
) -> list[JsonObject]:
    target_id = _text(row.get("target_id"), "target delta target_id")
    target_local_id = _collection_target_local_id(target_id, "target delta target_id")
    matches = _matching_authorities(
        authorizations,
        target_local_id=target_local_id,
        source_id=source_id,
        lookup_key=_text(row.get("lookup_key"), "target delta lookup_key"),
        target_type=row.get("target_type"),
        direction=direction,
    )
    if not matches:
        raise ValueError(f"unowned target-index {direction}: {source_id}/{target_local_id}")
    return [
        {
            "owner": authority.get("owner"),
            "reason": authority.get("reason"),
            "evidence": authority.get("evidence"),
        }
        for authority in matches
    ]


def _lookup_authorities(
    authorizations: JsonObject, *, source_id: str, lookup_key: str
) -> list[JsonObject]:
    lookups = _object(authorizations.get("lookups"), "lookup authorizations")
    return [
        row
        for row in _objects(lookups.get(lookup_key.lower(), []), "lookup authority rows")
        if row.get("source_id") == source_id
    ]


def _resolution_authorities(
    *, row: JsonObject, authorizations: JsonObject, direction: str
) -> list[JsonObject]:
    key = _resolution_key(row)
    source_id, _, _, lookup_key = key
    candidates = _objects(row.get("candidate_targets"), "resolution candidate targets")
    matches: list[JsonObject] = []
    for candidate in candidates:
        target_id = _text(candidate.get("target_id"), "resolution target_id")
        target_local_id = _collection_target_local_id(target_id, "resolution target_id")
        target_source_id = _text(candidate.get("target_source_id"), "resolution target_source_id")
        matches.extend(
            _matching_authorities(
                authorizations,
                target_local_id=target_local_id,
                source_id=target_source_id,
                lookup_key=lookup_key,
                target_type=candidate.get("target_type"),
                direction="resolution",
            )
        )
    if not candidates:
        matches.extend(
            _lookup_authorities(authorizations, source_id=source_id, lookup_key=lookup_key)
        )
    final_f1 = _object(
        authorizations.get("final_f1_resolution_sources"),
        "Final F1 resolution source boundaries",
    )
    boundary = final_f1.get(source_id)
    if isinstance(boundary, dict):
        matches.append(boundary)
    return [
        {**row, "direction": direction}
        for row in sorted(
            matches,
            key=lambda item: (
                str(item.get("owner")),
                str(item.get("reason")),
                str(item.get("evidence")),
            ),
        )
    ]


def _compare_resolutions(
    baseline: JsonObject,
    replacement: JsonObject,
    *,
    authorizations: JsonObject,
    catalog_rebinding: JsonObject,
) -> JsonObject:
    old_rows = _objects(
        _object(baseline.get("resolution_completion"), "baseline resolution").get("resolutions"),
        "baseline resolutions",
    )
    new_rows = _objects(
        _object(replacement.get("resolution_completion"), "replacement resolution").get(
            "resolutions"
        ),
        "replacement resolutions",
    )
    if len(old_rows) != 72:
        raise ValueError("Task 04D resolution comparison population must contain 72 rows")
    old = {_resolution_key(row): row for row in old_rows}
    new = {_resolution_key(row): row for row in new_rows}
    if len(old) != len(old_rows) or len(new) != len(new_rows):
        raise ValueError("resolution comparison keys are not unique")
    old_catalog_sha = _text(
        _object(catalog_rebinding.get("baseline_catalog_ref"), "baseline catalog ref").get(
            "sha256"
        ),
        "baseline catalog digest",
    )
    new_catalog_sha = _text(
        _object(catalog_rebinding.get("replacement_catalog_ref"), "replacement catalog ref").get(
            "sha256"
        ),
        "replacement catalog digest",
    )
    comparisons: list[JsonObject] = []
    for key in sorted(set(old) | set(new)):
        old_row = old.get(key)
        new_row = new.get(key)
        for row, expected_sha, label in (
            (old_row, old_catalog_sha, "baseline"),
            (new_row, new_catalog_sha, "replacement"),
        ):
            if row is None:
                continue
            cross_document = _object(
                row.get("cross_document_evidence"), f"{label} cross-document evidence"
            )
            if cross_document.get("catalog_sha256") != expected_sha:
                raise ValueError(f"{label} resolution catalog binding differs")
        old_outcome = _resolution_outcome(old_row) if old_row is not None else None
        new_outcome = _resolution_outcome(new_row) if new_row is not None else None
        classification = (
            "unchanged"
            if old_outcome == new_outcome
            else "removed"
            if new_row is None
            else "added"
            if old_row is None
            else "changed"
        )
        authorities: list[JsonObject] = []
        if classification != "unchanged":
            if old_row is not None:
                authorities.extend(
                    _resolution_authorities(
                        row=old_row,
                        authorizations=authorizations,
                        direction="baseline_outcome",
                    )
                )
            if new_row is not None:
                authorities.extend(
                    _resolution_authorities(
                        row=new_row,
                        authorizations=authorizations,
                        direction="replacement_outcome",
                    )
                )
            if not authorities:
                raise ValueError("unowned collection-resolution delta: " + "/".join(map(str, key)))
        comparisons.append(
            {
                "comparison_key": list(key),
                "classification": classification,
                "baseline": old_outcome,
                "replacement": new_outcome,
                "authorizations": (
                    authorities
                    if authorities
                    else [
                        {
                            "owner": "task06g_no_change",
                            "reason": "baseline_and_replacement_outcomes_equal",
                        }
                    ]
                ),
            }
        )
    missing = [row for row in comparisons if row["classification"] == "removed"]
    added = [row for row in comparisons if row["classification"] == "added"]
    return {
        "schema_version": "er_commons.task06g.resolution_comparison.v1",
        "source_family_catalog_rebinding": {
            **catalog_rebinding,
            "affected_resolution_count": len(comparisons),
        },
        "baseline_population_count": 72,
        "replacement_population_count": len(new_rows),
        "matched_count": len(comparisons),
        "missing": missing,
        "added": added,
        "comparisons": comparisons,
        "complete_baseline_reconciliation": all(
            row.get("classification") != "removed" or bool(row.get("authorizations"))
            for row in comparisons
        ),
    }


def _repair_checks(
    repairs: Mapping[str, JsonObject],
    appendix_a_correspondence: JsonObject,
    *,
    replacement: JsonObject,
    replacement_links: JsonObject,
) -> JsonObject:
    d = repairs["task06d"]
    e = repairs["task06e"]
    f = repairs["task06f"]
    d_rows = _objects(d.get("eligible_decisions"), "Task 06D eligible decisions")
    e_rows = _objects(e.get("eligible_decisions"), "Task 06E eligible decisions")
    by_marker_d = {_text(row.get("chapter_marker"), "06D chapter_marker"): row for row in d_rows}
    by_marker_e = {_text(row.get("chapter_marker"), "06E chapter_marker"): row for row in e_rows}
    expected_d = {
        "06": {
            "heading_physical_pages": [311, 312],
            "extent": [311, 451],
            "children": 6,
            "boundary": ["07 INFRASTRUCTURE", 451, 5571],
        },
        "07": {
            "heading_physical_pages": [451, 452],
            "extent": [451, 479],
            "children": 10,
            "boundary": ["08 PUBLIC FACILITIES FINANCING", 479, 5964],
        },
        "08": {
            "heading_physical_pages": [479, 480],
            "extent": [479, 491],
            "children": 4,
            "boundary": ["09 IMPLEMENTATION", 491, 6179],
        },
        "09": {
            "heading_physical_pages": [491, 492],
            "extent": [491, 501],
            "children": 5,
            "boundary": ["APPENDICES", 501, 6274],
        },
    }
    if (
        appendix_a_correspondence.get("schema_version")
        != "er_commons.recovery.repeated_heading_correspondence.v1"
    ):
        raise ValueError("Task 06D sealed repeated-heading correspondence schema differs")
    correspondence = _objects(
        appendix_a_correspondence.get("records"),
        "Task 06D sealed repeated-heading correspondence",
    )
    if len(correspondence) != 4:
        raise ValueError("Task 06D must seal exactly four repeated-heading correspondences")
    correspondence_extents = sorted(
        cast(list[int], row.get("logical_content_page_extent")) for row in correspondence
    )
    if correspondence_extents != [[311, 451], [451, 479], [479, 491], [491, 501]]:
        raise ValueError("Task 06D repeated-heading correspondence extents differ")
    for correspondence_row in correspondence:
        if (
            correspondence_row.get("change_class") != "many_to_one_repeated_heading_repair"
            or correspondence_row.get("policy_version") != "repeated_chapter_divider_opening_v2"
            or correspondence_row.get("extent_basis")
            != "record_order_before_immediate_same_level_sibling"
            or len(_objects(correspondence_row.get("old_targets"), "Task 06D old targets")) != 2
            or not isinstance(correspondence_row.get("new_target"), dict)
            or correspondence_row.get("content_record_ids_unique") is not True
        ):
            raise ValueError("Task 06D repeated-heading correspondence is incomplete")
    for marker, expected in expected_d.items():
        row = by_marker_d.get(marker)
        if row is None:
            raise ValueError(f"Task 06D lacks accepted Chapter {marker} decision")
        extents = row.get("source_page_extents")
        child_groups = row.get("ordered_child_refs")
        if not isinstance(extents, list) or not all(isinstance(item, list) for item in extents):
            raise ValueError("06D source_page_extents must be an array of arrays")
        if not isinstance(child_groups, list) or not all(
            isinstance(item, list) for item in child_groups
        ):
            raise ValueError("06D ordered_child_refs must be an array of arrays")
        flattened = [page for extent in extents for page in extent]
        if not flattened or not all(isinstance(page, int) for page in flattened):
            raise ValueError("06D source_page_extents must contain integer bounds")
        children = sum(len(group) - 1 for group in child_groups)
        observed = {
            "heading_physical_pages": row.get("heading_physical_pages"),
            "extent": [min(flattened), max(flattened)],
            "children": children,
            "boundary": [
                row.get("following_boundary_raw_text"),
                row.get("following_boundary_page"),
                row.get("following_boundary_content_order"),
            ],
        }
        if observed != expected:
            raise ValueError(f"Task 06D Chapter {marker} invariant differs: {observed}")
    for marker, extent in {"8": [1855, 2014], "9": [2015, 2084]}.items():
        row = by_marker_e.get(marker)
        if row is None or [row.get("extent_start_page"), row.get("extent_end_page")] != extent:
            raise ValueError(f"Task 06E Chapter {marker} extent differs")
    chapter_nine = by_marker_e["9"]
    if chapter_nine.get("following_boundary_page") != 2085:
        raise ValueError("Task 06E Chapter 9 is not bounded by Chapter 10 at page 2085")
    f_counts = {
        "candidate": f.get("candidate_figure_count"),
        "eligible": f.get("eligible_figure_count"),
        "rejected": f.get("rejected_figure_count"),
        "unique_aliases": f.get("unique_alias_count"),
        "target_edges": f.get("target_edge_count"),
        "ambiguous": f.get("ambiguous_alias_count"),
        "collisions": f.get("collision_group_count"),
        "review_required": f.get("review_required_figure_count"),
    }
    expected_f = {
        "candidate": 274,
        "eligible": 178,
        "rejected": 96,
        "unique_aliases": 178,
        "target_edges": 178,
        "ambiguous": 0,
        "collisions": 0,
        "review_required": 0,
    }
    if f_counts != expected_f:
        raise ValueError(f"Task 06F FC1 invariant differs: {f_counts}")
    figure_48 = [
        row
        for row in _objects(f.get("decisions"), "Task 06F decisions")
        if row.get("normalized_alias") == "figure 4.8"
    ]
    if figure_48:
        raise ValueError("Figure 4.8 unexpectedly appears in accepted FC1 evidence")
    eligible = [
        row
        for row in _objects(f.get("decisions"), "Task 06F decisions")
        if row.get("eligibility") == "eligible"
    ]
    accepted_edges = {
        (
            _text(row.get("normalized_alias"), "Task 06F eligible alias").lower(),
            _identity_relative(row.get("upstream_figure_id"), "Task 06F figure target"),
        )
        for row in eligible
    }
    if len(eligible) != 178 or len(accepted_edges) != 178:
        raise ValueError("Task 06F must authorize exactly 178 unique FC1 alias/target edges")
    accepted_target_entries = _objects(
        f.get("accepted_target_index_entries"), "Task 06F accepted target-index entries"
    )
    accepted_entry_edges = {
        (
            _text(row.get("lookup_key"), "Task 06F target-index lookup").lower(),
            _identity_relative(
                row.get("upstream_target_record_id"), "Task 06F target-index target"
            ),
        )
        for row in accepted_target_entries
    }
    accepted_aliases = _objects(
        f.get("accepted_figure_aliases"), "Task 06F accepted figure aliases"
    )
    accepted_alias_edges = {
        (
            _text(row.get("normalized_alias"), "Task 06F figure alias").lower(),
            _identity_relative(
                _object(
                    _objects(row.get("targets"), "Task 06F figure alias targets")[0],
                    "Task 06F figure alias target",
                ).get("upstream_target_id"),
                "Task 06F figure alias upstream target",
            ),
        )
        for row in accepted_aliases
        if len(_objects(row.get("targets"), "Task 06F figure alias targets")) == 1
    }
    if (
        len(accepted_target_entries) != 178
        or len(accepted_aliases) != 178
        or accepted_entry_edges != accepted_edges
        or accepted_alias_edges != accepted_edges
    ):
        raise ValueError("Task 06F sealed alias/target evidence differs at entity level")
    replacement_target_rows = _objects(
        _object(replacement.get("target_index"), "replacement target index").get("entries"),
        "replacement target entries",
    )
    rebuilt_main_figures = {
        (
            _text(row.get("lookup_key"), "rebuilt main figure lookup").lower(),
            _identity_relative(row.get("target_id"), "rebuilt main figure target"),
        )
        for row in replacement_target_rows
        if row.get("source_id") == "deir_main" and row.get("target_type") == "figure"
    }
    rebuilt_main_figure_rows = [
        row
        for row in replacement_target_rows
        if row.get("source_id") == "deir_main" and row.get("target_type") == "figure"
    ]
    if len(rebuilt_main_figure_rows) != 178 or rebuilt_main_figures != accepted_edges:
        missing = sorted(accepted_edges - rebuilt_main_figures)
        added = sorted(rebuilt_main_figures - accepted_edges)
        raise ValueError(
            "rebuilt main FC1 alias/target edges differ from accepted Task 06F: "
            f"missing={missing[:3]} added={added[:3]}"
        )
    actual_figure_48_targets = [
        row
        for row in replacement_target_rows
        if row.get("source_id") == "deir_main"
        and isinstance(row.get("lookup_key"), str)
        and str(row["lookup_key"]).lower() == "figure 4.8"
    ]
    actual_figure_48_links = [
        row
        for row in _objects(replacement_links.get("ordinary"), "replacement ordinary references")
        if row.get("source_id") == "deir_main"
        and isinstance(row.get("lookup_key"), str)
        and str(row["lookup_key"]).lower() == "figure 4.8"
        and (
            row.get("resolution_status") == "resolved"
            or bool(_objects(row.get("candidates"), "Figure 4.8 candidates"))
        )
    ]
    replacement_resolution_rows = _objects(
        _object(replacement.get("resolution_completion"), "replacement resolution").get(
            "resolutions"
        ),
        "replacement resolutions",
    )
    actual_figure_48_resolutions = [
        row
        for row in replacement_resolution_rows
        if isinstance(row.get("lookup_key"), str)
        and str(row["lookup_key"]).lower() == "figure 4.8"
        and (row.get("status") == "resolved" or bool(row.get("candidate_targets")))
    ]
    if actual_figure_48_targets or actual_figure_48_links or actual_figure_48_resolutions:
        raise ValueError("Figure 4.8 appears in actual replacement target/link evidence")
    return {
        "schema_version": "er_commons.task06g.repair_checks.v1",
        "appendix_a": {
            "expected_groups": expected_d,
            "correspondence_candidate_id": appendix_a_correspondence.get("candidate_id"),
            "decision_ref": appendix_a_correspondence.get("decision_ref"),
            "correspondence_count": len(correspondence),
            "correspondence_records": correspondence,
        },
        "main_chapters": {"8": [1855, 2014], "9": [2015, 2084], "chapter_10": 2085},
        "main_fc1": {
            **f_counts,
            "accepted_edge_count": len(accepted_edges),
            "rebuilt_edge_count": len(rebuilt_main_figures),
            "entity_level_equivalence": True,
        },
        "figure_4_8": "absent_from_qualification_targets_and_resolved_links",
        "status": "passed",
    }


def build_task06g_closure(
    *,
    spec: JsonObject,
    baseline: JsonObject,
    replacement: JsonObject,
    source_slots: JsonObject,
    reviews: JsonObject,
    mentions: JsonObject,
    repairs: Mapping[str, JsonObject],
    appendix_a_correspondence: JsonObject,
    main_correspondence: JsonObject,
    gate_c: JsonObject,
    link_evidence: JsonObject,
    replacement_document_support: Mapping[str, JsonObject],
    source_family_catalogs: Mapping[str, JsonObject],
) -> tuple[dict[str, JsonObject], dict[str, JsonObject]]:
    """Build deterministic closure records from compact sealed JSON evidence."""
    expected = _object(spec.get("expected_fixed_accounting"), "expected_fixed_accounting")
    if expected != EXPECTED_FIXED_ACCOUNTING:
        raise ValueError("Task 06G fixed accounting differs from the accepted contract")
    required_checks = set(cast(list[str], spec.get("required_repair_checks", [])))
    if required_checks != EXPECTED_CHECKS:
        raise ValueError("Task 06G required repair checks differ from the accepted set")
    old_accounting = _object(baseline.get("accounting"), "baseline accounting")
    new_accounting = _object(replacement.get("accounting"), "replacement accounting")
    old_sources = _objects(old_accounting.get("ordered_sources"), "baseline ordered_sources")
    new_sources = _objects(new_accounting.get("ordered_sources"), "replacement ordered_sources")
    slots = _objects(source_slots.get("sources"), "Task 06A source slots")
    if len(slots) != 35 or len(old_sources) != 35 or len(new_sources) != 35:
        raise ValueError("source/accounting closure must contain exactly 35 rows")
    slot_ids = [_text(row.get("source_id"), "source slot ID") for row in slots]
    if len(set(slot_ids)) != 35:
        raise ValueError("Task 06A source slots must contain 35 unique source IDs")
    expected_new_ids = [
        "feir_appendix_f1" if row.get("source_id") == "deir_appendix_f1" else row.get("source_id")
        for row in slots
    ]
    if [row.get("source_id") for row in old_sources] != slot_ids:
        raise ValueError("baseline source order differs from Task 06A")
    if [row.get("source_id") for row in new_sources] != expected_new_ids:
        raise ValueError("replacement source order or Final F1 substitution differs")
    old_page_count = sum(cast(int, row.get("pdf_page_count")) for row in old_sources)
    if old_page_count != 48_341:
        raise ValueError(f"baseline page accounting differs: {old_page_count}")
    page_count = sum(cast(int, row.get("pdf_page_count")) for row in new_sources)
    if page_count != expected.get("page_count") or page_count != 49_022:
        raise ValueError(f"replacement page accounting differs: {page_count}")

    old_rows = _index(_objects(old_accounting.get("rows"), "baseline rows"), "source_id", "row")
    new_rows = _index(_objects(new_accounting.get("rows"), "replacement rows"), "source_id", "row")
    old_targets = _target_rows_by_source(baseline)
    new_targets = _target_rows_by_source(replacement)
    authorizations = _repair_authorizations(
        repairs=repairs,
        appendix_a_correspondence=appendix_a_correspondence,
        main_correspondence=main_correspondence,
        baseline=baseline,
        replacement=replacement,
    )
    final_f1_mentions: JsonObject = {}
    for evidence_label, physical_source in (
        ("baseline", "deir_appendix_f1"),
        ("replacement", "feir_appendix_f1"),
    ):
        evidence = _object(link_evidence.get(evidence_label), f"{evidence_label} link evidence")
        for row in _objects(evidence.get("ordinary"), f"{evidence_label} ordinary references"):
            mention_key = _identity_relative(row.get("id"), "Final F1 mention ID")
            parts = mention_key.split("/")
            if len(parts) < 3 or parts[0] != "cross-reference":
                raise ValueError("Final F1 mention ID lacks its source-local identity")
            identity_source = parts[1]
            if identity_source != physical_source:
                continue
            row_source = row.get("source_id", identity_source)
            if row_source != identity_source:
                raise ValueError("Final F1 mention source field differs from its identity")
            document_key = _identity_relative(row.get("document_id"), "Final F1 document ID")
            if document_key != f"document/{identity_source}":
                raise ValueError("Final F1 mention document differs from its identity")
            final_f1_mentions[mention_key] = {
                "owner": "task06c",
                "reason": "sealed_final_f1_no_equivalence_boundary",
                "evidence": {
                    "physical_source_id": physical_source,
                    "evidence_side": evidence_label,
                },
            }
    authorizations["final_f1_mentions"] = final_f1_mentions
    source_correspondence: list[JsonObject] = []
    target_deltas: list[JsonObject] = []
    preserved_count = 0
    for ordinal, (slot, old_source, new_source) in enumerate(
        zip(slots, old_sources, new_sources, strict=True), start=1
    ):
        logical = _text(slot.get("source_id"), "source slot ID")
        selected = _text(new_source.get("source_id"), "selected source ID")
        change_class = (
            "substituted_new_source"
            if logical == "deir_appendix_f1"
            else "repaired_structure"
            if logical in {"deir_appendix_a", "deir_main"}
            else "preserved_semantic"
        )
        old_row = old_rows[logical]
        new_row = new_rows[selected]
        old_target_rows = old_targets.get(logical, [])
        new_target_rows = new_targets.get(selected, [])
        if change_class == "preserved_semantic":
            support = replacement_document_support.get(selected)
            if support is None:
                raise ValueError(f"missing preserved-document replay support: {selected}")
            if support.get("source_candidate_id") != old_row.get("candidate_id"):
                raise ValueError(
                    f"preserved document did not reuse its sealed candidate: {selected}"
                )
            if old_target_rows != new_target_rows:
                raise ValueError(f"preserved document target semantics changed: {selected}")
            preserved_count += 1
        source_correspondence.append(
            {
                "ordinal": ordinal,
                "logical_source_id": logical,
                "baseline_physical_source_id": old_source.get("source_id"),
                "selected_physical_source_id": selected,
                "baseline_source": old_source,
                "selected_source": new_source,
                "baseline_candidate_id": old_row.get("candidate_id"),
                "replacement_candidate_id": new_row.get("candidate_id"),
                "baseline_completion_ref": old_row.get("document_completion_ref"),
                "replacement_completion_ref": new_row.get("document_completion_ref"),
                "change_class": change_class,
                "semantic_equivalence": change_class == "preserved_semantic",
                "owner": (
                    "task06g"
                    if change_class == "preserved_semantic"
                    else "task06c"
                    if logical == "deir_appendix_f1"
                    else "task06d"
                    if logical == "deir_appendix_a"
                    else "task06e_task06f"
                ),
            }
        )
        if change_class != "preserved_semantic":
            old_set = {_sort_key(row): row for row in old_target_rows}
            new_set = {_sort_key(row): row for row in new_target_rows}
            if len(old_set) != len(old_target_rows) or len(new_set) != len(new_target_rows):
                raise ValueError(f"duplicate semantic target entries for {logical}")
            removed = []
            for key in sorted(set(old_set) - set(new_set)):
                row = old_set[key]
                removed.append(
                    {
                        "target": row,
                        "authorizations": _authorize_target_delta(
                            row,
                            source_id=logical,
                            direction="removed",
                            authorizations=authorizations,
                        ),
                    }
                )
            added = []
            for key in sorted(set(new_set) - set(old_set)):
                row = new_set[key]
                added.append(
                    {
                        "target": row,
                        "authorizations": _authorize_target_delta(
                            row,
                            source_id=selected,
                            direction="added",
                            authorizations=authorizations,
                        ),
                    }
                )
            target_deltas.append(
                {
                    "logical_source_id": logical,
                    "selected_source_id": selected,
                    "change_class": change_class,
                    "owner": (
                        "task06c"
                        if logical == "deir_appendix_f1"
                        else "task06d"
                        if logical == "deir_appendix_a"
                        else "task06e_task06f"
                    ),
                    "baseline_count": len(old_target_rows),
                    "replacement_count": len(new_target_rows),
                    "removed": removed,
                    "added": added,
                }
            )
    if preserved_count != 32:
        raise ValueError(f"preserved semantic population differs: {preserved_count}")

    historical = _objects(reviews.get("historical_correspondence"), "historical review rows")
    if len(historical) != expected.get("task04a_decision_count") or len(historical) != 757:
        raise ValueError("Task 04A review correspondence must contain 757 rows")
    review_rows: list[JsonObject] = []
    review_ids: set[str] = set()
    for row in historical:
        source_id = _text(row.get("source_id"), "review source_id")
        entry_id = _text(row.get("decision_entry_id"), "review decision_entry_id")
        if entry_id in review_ids:
            raise ValueError(f"duplicate Task 04A review decision: {entry_id}")
        review_ids.add(entry_id)
        classification = (
            "unproven"
            if source_id in {"deir_appendix_f1", "deir_appendix_a", "deir_main"}
            else "unchanged"
        )
        review_rows.append(
            {
                "entry_id": entry_id,
                "source_id": source_id,
                "classification": classification,
                "baseline_evidence": row,
                "task04_status": "not_evaluated",
            }
        )
    review_counts = dict(sorted(Counter(row["classification"] for row in review_rows).items()))
    mention_rows = _objects(mentions.get("mentions"), "Task 06A mentions")
    mention_counts = _object(mentions.get("population_counts"), "mention population_counts")
    if len(mention_rows) != 511 or len(mention_rows) != expected.get("task05_mention_count"):
        raise ValueError("Task 05 comparison population must contain 511 mentions")
    accepted_populations = {
        "f1_wrong_source": 66,
        "figure_missing_target": 79,
        "chapter_8_9": 19,
        "appendix_a_duplicate_heading_reference": 2,
    }
    if any(mention_counts.get(key) != value for key, value in accepted_populations.items()):
        raise ValueError("Task 06 planning populations differ from accepted counts")

    replacement_link_evidence = _object(
        link_evidence.get("replacement"), "replacement link evidence"
    )
    repair_checks = _repair_checks(
        repairs,
        appendix_a_correspondence,
        replacement=replacement,
        replacement_links=replacement_link_evidence,
    )
    catalog_rebinding = _catalog_rebinding(
        baseline=baseline,
        replacement=replacement,
        baseline_catalog=source_family_catalogs["baseline"],
        replacement_catalog=source_family_catalogs["replacement"],
    )
    resolution = _compare_resolutions(
        baseline,
        replacement,
        authorizations=authorizations,
        catalog_rebinding=catalog_rebinding,
    )
    if not resolution["complete_baseline_reconciliation"]:
        raise ValueError("not all 72 baseline resolutions were reconciled")
    old_index_count = _object(baseline.get("target_index"), "baseline index").get("entry_count")
    new_index_count = _object(replacement.get("target_index"), "replacement index").get(
        "entry_count"
    )
    if old_index_count != 99_172:
        raise ValueError("Task 04D target index must contain 99,172 entries")
    accounting = {
        "schema_version": "er_commons.task06g.accounting_comparison.v1",
        "baseline": {
            "document_count": 35,
            "page_count": 48_341,
            "target_index_count": old_index_count,
        },
        "replacement": {
            "document_count": len(new_rows),
            "page_count": page_count,
            "target_index_count": new_index_count,
        },
        "target_index_delta": cast(int, new_index_count) - cast(int, old_index_count),
        "target_delta_owners": [row["owner"] for row in target_deltas],
        "status": "passed",
    }
    navigation = _object(gate_c.get("navigation"), "Gate C navigation")
    ordinary = _object(gate_c.get("ordinary_machine"), "Gate C ordinary-machine")
    observed_gate_c = {
        "ordinary_references": ordinary.get("population_count"),
        "navigation_claims": navigation.get("population_count"),
        "navigation_linked": navigation.get("resolved_count"),
        "navigation_unresolved": navigation.get("unresolved_count"),
        "inherited_task04c_links": _object(
            navigation.get("control_population_counts"), "Gate C control populations"
        ).get("existing_task04c_link"),
        "inherited_task04c_invalidations": navigation.get("existing_link_invalidation_count"),
    }
    expected_gate_c = {
        "ordinary_references": expected.get("ordinary_reference_count"),
        "navigation_claims": expected.get("navigation_claim_count"),
        "navigation_linked": 410,
        "navigation_unresolved": 150,
        "inherited_task04c_links": expected.get("inherited_navigation_link_count"),
        "inherited_task04c_invalidations": 0,
    }
    if observed_gate_c != expected_gate_c:
        raise ValueError(f"accepted Task 04D Gate C control differs: {observed_gate_c}")
    references = {
        "schema_version": "er_commons.task06g.reference_population_comparison.v1",
        "task05": {
            "mentions": 511,
            "links": 295,
            "nonlinks": 216,
            "status": "preserved_not_replayed",
        },
        "task04d_controls": observed_gate_c,
        "planning_populations": accepted_populations,
        "replacement_result_policy": "dynamic_itemized_by_source_and_resolution_comparison",
    }
    links = compare_link_populations(
        baseline=_object(link_evidence.get("baseline"), "baseline link evidence"),
        replacement=replacement_link_evidence,
        authorizations=authorizations,
    )
    replacement_navigation = _object(links.get("navigation"), "navigation comparison")
    references["replacement_controls"] = {
        "ordinary_references": _object(links.get("ordinary"), "ordinary comparison").get(
            "replacement_population_count"
        ),
        "navigation_claims": replacement_navigation.get("replacement_population_count"),
        "navigation_linked": replacement_navigation.get("replacement_resolved_count"),
        "navigation_unresolved": replacement_navigation.get("replacement_unresolved_count"),
    }
    correspondence: dict[str, JsonObject] = {
        "source_correspondence.json": {
            "schema_version": "er_commons.task06g.source_correspondence.v1",
            "rows": source_correspondence,
            "counts": {"total": 35, "preserved": 32, "repaired": 2, "substituted": 1},
        },
        "target_correspondence.json": {
            "schema_version": "er_commons.task06g.target_correspondence.v1",
            "changed_sources": target_deltas,
            "preserved_source_count": 32,
            "appendix_a_many_to_one": appendix_a_correspondence,
            "main_missing_chapters": main_correspondence,
        },
        "review_correspondence.json": {
            "schema_version": "er_commons.task06g.review_correspondence.v1",
            "rows": review_rows,
            "counts": review_counts,
            "task04_status": "not_evaluated",
        },
    }
    comparison = {
        "accounting_comparison.json": accounting,
        "resolution_comparison.json": resolution,
        "reference_comparison.json": references,
        "link_population_comparison.json": links,
        "repair_checks.json": repair_checks,
    }
    return correspondence, comparison


def _publication_files(records: Mapping[str, JsonObject], kind: str) -> dict[str, bytes]:
    files = {name: canonical_bytes(value) for name, value in records.items()}
    inventory = {
        "schema_version": f"er_commons.task06g.{kind}_inventory.v1",
        "files": [content_reference(name, content) for name, content in sorted(files.items())],
    }
    files["artifact_inventory.json"] = canonical_bytes(inventory)
    completion = {
        "schema_version": f"er_commons.task06g.{kind}_completion.v1",
        "status": "complete",
        "task04_status": "not_evaluated",
        "artifact_inventory": content_reference(
            "artifact_inventory.json", files["artifact_inventory.json"]
        ),
        "completion_last": True,
    }
    files["completion.json"] = canonical_bytes(completion)
    return files


def _verify_or_publish(root: Path, files: dict[str, bytes]) -> None:
    if not root.exists():
        publish_directory_no_clobber(root, files)
        return
    if not root.is_dir():
        raise FileExistsError(f"Task 06G closure path is not a directory: {root}")
    observed = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    if observed != files:
        raise FileExistsError(f"refusing to overwrite changed Task 06G closure: {root}")


def _scope_id_from_checkpoint(checkpoint: JsonObject) -> str:
    if checkpoint.get("verified") is not True:
        raise ValueError("collection handoff checkpoint is not verified")
    derived = checkpoint.get("derived_id")
    if not isinstance(derived, str) or derived != checkpoint.get("recomputed_id"):
        raise ValueError("collection handoff checkpoint identity recomputation differs")
    outputs = _object(checkpoint.get("outputs"), "checkpoint outputs")
    scope_id = outputs.get("scope_id")
    if not isinstance(scope_id, str) or not scope_id.startswith("scopev1-"):
        raise ValueError("collection handoff checkpoint does not expose its outputs.scope_id")
    return scope_id


def _inventory_entry(inventory: JsonObject, relative_path: str, label: str) -> JsonObject:
    rows = _objects(inventory.get("files"), f"{label} inventory files")
    matches = [row for row in rows if row.get("path") == relative_path]
    if len(matches) != 1:
        raise ValueError(f"{label} inventory must name {relative_path} exactly once")
    return matches[0]


def _verify_sha_reference(value: object, *, root: Path, label: str) -> Path:
    artifact = _object(value, label)
    raw_path = _text(artifact.get("path"), f"{label}.path")
    expected_sha = _text(artifact.get("sha256"), f"{label}.sha256")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} must be a contained relative path")
    path = root / relative
    observed = reference(path, root=root)
    if observed["sha256"] != expected_sha:
        raise ValueError(f"{label} checksum differs")
    return path.resolve()


def _authority_reference(path: Path, *, root: Path, authority: str) -> JsonObject:
    """Describe one compact input under an explicit path authority."""
    return {"authority": authority, **reference(path, root=root)}


def _appendix_a_structure_correspondence(
    *,
    data_root: Path,
    collection_root: Path,
    bundle: JsonObject,
    document_input_root: Path | None = None,
) -> tuple[JsonObject, JsonObject]:
    """Load Appendix A correspondence through its document and structure seals."""
    accounting = _object(bundle.get("accounting"), "replacement accounting")
    rows = _objects(accounting.get("rows"), "replacement accounting rows")
    matches = [row for row in rows if row.get("source_id") == "deir_appendix_a"]
    if len(matches) != 1:
        raise ValueError("replacement accounting must name Appendix A exactly once")
    row = matches[0]
    _resolve_candidate_ref(
        _object(row.get("document_completion_ref"), "Appendix A document completion ref"),
        collection_root=collection_root,
        document_input_root=document_input_root,
    )
    inventory_path = _resolve_candidate_ref(
        _object(row.get("candidate_inventory_ref"), "Appendix A candidate inventory ref"),
        collection_root=collection_root,
        document_input_root=document_input_root,
    )
    candidate_root = inventory_path.parent.parent
    candidate_inventory = load_object(inventory_path)
    identity_relative = "records/document_identity.json"
    identity_entry = _inventory_entry(
        candidate_inventory, identity_relative, "Appendix A candidate"
    )
    identity_path = candidate_root / identity_relative
    identity_observed = reference(identity_path, root=candidate_root)
    if identity_observed["sha256"] != identity_entry.get("sha256") or identity_observed[
        "byte_size"
    ] != identity_entry.get("byte_size"):
        raise ValueError("Appendix A document identity differs from its candidate inventory")
    identity = load_object(identity_path)
    if (
        identity.get("candidate_id") != row.get("candidate_id")
        or _object(identity.get("source"), "Appendix A identity source").get("source_id")
        != "deir_appendix_a"
    ):
        raise ValueError("Appendix A document identity differs from replacement accounting")
    stages = _object(identity.get("stage_completions"), "Appendix A stage completions")
    structure_completion_path = _verify_sha_reference(
        stages.get("structured_document"),
        root=data_root,
        label="Appendix A structured-document completion",
    )
    structure_root = structure_completion_path.parent.parent
    structure_completion = load_object(structure_completion_path)
    structure_id = _text(
        structure_completion.get("extraction_id"), "Appendix A structure extraction_id"
    )
    if structure_root.name != structure_id:
        raise ValueError("Appendix A structure completion path and identity differ")
    verify_completed_document_structure(structure_root, structure_id)
    structure_inventory_path = structure_root / "records/artifact_inventory.json"
    structure_manifest_path = structure_root / "records/manifest.json"
    structure_inventory = load_object(structure_inventory_path)
    structure_manifest = load_object(structure_manifest_path)
    support_rows = _objects(
        structure_manifest.get("support_files"), "Appendix A structure support files"
    )
    support_matches = [
        support
        for support in support_rows
        if support.get("role") == "repeated_heading_correspondence"
    ]
    if len(support_matches) != 1:
        raise ValueError("Appendix A structure must own one repeated-heading support file")
    support = support_matches[0]
    if (
        support.get("path") != REPEATED_HEADING_CORRESPONDENCE_PATH
        or support.get("schema_version") != "1.0.0"
    ):
        raise ValueError("Appendix A repeated-heading support declaration differs")
    correspondence_path = structure_root / REPEATED_HEADING_CORRESPONDENCE_PATH
    correspondence_ref = reference(correspondence_path, root=data_root)
    if correspondence_ref["sha256"] != support.get("sha256"):
        raise ValueError("Appendix A repeated-heading support checksum differs")
    correspondence_entry = _inventory_entry(
        structure_inventory,
        REPEATED_HEADING_CORRESPONDENCE_PATH,
        "Appendix A structure",
    )
    if (
        correspondence_entry.get("sha256") != correspondence_ref["sha256"]
        or correspondence_entry.get("byte_size") != correspondence_ref["byte_size"]
    ):
        raise ValueError("Appendix A repeated-heading support differs from structure inventory")
    correspondence = load_object(correspondence_path)
    records = _objects(correspondence.get("records"), "Appendix A correspondence records")
    if (
        correspondence.get("candidate_id") != structure_id
        or structure_completion.get("repeated_heading_correspondence_count") != len(records)
        or len(records) != 4
    ):
        raise ValueError("Appendix A correspondence identity or count differs")
    schema_path = (
        Path(__file__).resolve().parents[3] / REPEATED_HEADING_CORRESPONDENCE_SCHEMA_RELATIVE_PATH
    )
    provenance = {
        "appendix_a_document_identity": _authority_reference(
            identity_path, root=data_root, authority="artifact_root"
        ),
        "appendix_a_structure_completion": _authority_reference(
            structure_completion_path, root=data_root, authority="artifact_root"
        ),
        "appendix_a_structure_inventory": _authority_reference(
            structure_inventory_path, root=data_root, authority="artifact_root"
        ),
        "appendix_a_structure_manifest": _authority_reference(
            structure_manifest_path, root=data_root, authority="artifact_root"
        ),
        "appendix_a_repeated_heading_correspondence": {
            "authority": "artifact_root",
            **correspondence_ref,
        },
        "repeated_heading_correspondence_schema": _authority_reference(
            schema_path,
            root=Path(__file__).resolve().parents[3],
            authority="repository",
        ),
    }
    return correspondence, provenance


def _main_structure_correspondence(
    *,
    data_root: Path,
    collection_root: Path,
    bundle: JsonObject,
    document_input_root: Path | None = None,
) -> tuple[JsonObject, JsonObject]:
    """Load main missing-chapter correspondence through its published seals."""
    rows = _objects(
        _object(bundle.get("accounting"), "replacement accounting").get("rows"),
        "replacement accounting rows",
    )
    matches = [row for row in rows if row.get("source_id") == "deir_main"]
    if len(matches) != 1:
        raise ValueError("replacement accounting must name main exactly once")
    row = matches[0]
    inventory_path = _resolve_candidate_ref(
        _object(row.get("candidate_inventory_ref"), "main candidate inventory ref"),
        collection_root=collection_root,
        document_input_root=document_input_root,
    )
    candidate_root = inventory_path.parent.parent
    candidate_inventory = load_object(inventory_path)
    identity_relative = "records/document_identity.json"
    identity_entry = _inventory_entry(candidate_inventory, identity_relative, "main candidate")
    identity_path = candidate_root / identity_relative
    identity_ref = reference(identity_path, root=candidate_root)
    if identity_ref["sha256"] != identity_entry.get("sha256") or identity_ref[
        "byte_size"
    ] != identity_entry.get("byte_size"):
        raise ValueError("main document identity differs from candidate inventory")
    identity = load_object(identity_path)
    if (
        identity.get("candidate_id") != row.get("candidate_id")
        or _object(identity.get("source"), "main identity source").get("source_id") != "deir_main"
    ):
        raise ValueError("main document identity differs from replacement accounting")
    stages = _object(identity.get("stage_completions"), "main stage completions")
    completion_path = _verify_sha_reference(
        stages.get("structured_document"),
        root=data_root,
        label="main structured-document completion",
    )
    structure_root = completion_path.parent.parent
    completion = load_object(completion_path)
    structure_id = _text(completion.get("extraction_id"), "main structure extraction_id")
    if structure_root.name != structure_id:
        raise ValueError("main structure completion path and identity differ")
    verify_completed_document_structure(structure_root, structure_id)
    manifest_path = structure_root / "records/manifest.json"
    structure_inventory_path = structure_root / "records/artifact_inventory.json"
    manifest = load_object(manifest_path)
    structure_inventory = load_object(structure_inventory_path)
    support = [
        item
        for item in _objects(manifest.get("support_files"), "main structure support files")
        if item.get("role") == "missing_chapter_correspondence"
    ]
    if (
        len(support) != 1
        or support[0].get("path") != MISSING_CHAPTER_CORRESPONDENCE_PATH
        or support[0].get("schema_version") != "1.0.0"
    ):
        raise ValueError("main structure must own one missing-chapter support file")
    path = structure_root / MISSING_CHAPTER_CORRESPONDENCE_PATH
    path_ref = reference(path, root=data_root)
    entry = _inventory_entry(
        structure_inventory, MISSING_CHAPTER_CORRESPONDENCE_PATH, "main structure"
    )
    if (
        path_ref["sha256"] != support[0].get("sha256")
        or path_ref["sha256"] != entry.get("sha256")
        or path_ref["byte_size"] != entry.get("byte_size")
    ):
        raise ValueError("main missing-chapter support seal differs")
    payload = load_object(path)
    records = _objects(payload.get("records"), "main missing-chapter records")
    if len(records) != 2 or completion.get("missing_chapter_correspondence_count") != 2:
        raise ValueError("main missing-chapter correspondence count differs")
    repository_root = Path(__file__).resolve().parents[3]
    schema_path = repository_root / MISSING_CHAPTER_CORRESPONDENCE_SCHEMA_RELATIVE_PATH
    return payload, {
        "main_document_identity": _authority_reference(
            identity_path, root=data_root, authority="artifact_root"
        ),
        "main_structure_completion": _authority_reference(
            completion_path, root=data_root, authority="artifact_root"
        ),
        "main_structure_inventory": _authority_reference(
            structure_inventory_path, root=data_root, authority="artifact_root"
        ),
        "main_structure_manifest": _authority_reference(
            manifest_path, root=data_root, authority="artifact_root"
        ),
        "main_missing_chapter_correspondence": {
            "authority": "artifact_root",
            **path_ref,
        },
        "missing_chapter_correspondence_schema": _authority_reference(
            schema_path, root=repository_root, authority="repository"
        ),
    }


def _load_inventory_jsonl(
    *, root: Path, inventory: JsonObject, relative: str, label: str
) -> list[JsonObject]:
    entry = _inventory_entry(inventory, relative, label)
    path = root / relative
    observed = reference(path, root=root)
    if observed["sha256"] != entry.get("sha256") or observed["byte_size"] != entry.get("byte_size"):
        raise ValueError(f"{label} compact evidence differs: {relative}")
    return [
        _object(json.loads(line), f"{label} {relative} row")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_repairs(data_root: Path) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for name, relative_root in REPAIR_ROOTS.items():
        root = data_root / relative_root
        inventory_path = root / "inventory.json"
        completion_path = root / "completion.json"
        inventory = load_object(inventory_path)
        completion = load_object(completion_path)
        inventory_ref = reference(inventory_path)
        if (
            completion.get("status") != "complete"
            or completion.get("inventory_sha256") != inventory_ref["sha256"]
        ):
            raise ValueError(f"accepted {name} completion or inventory binding differs")

        qualification_entry = _inventory_entry(inventory, "qualification.json", f"accepted {name}")
        qualification_path = root / "qualification.json"
        qualification_ref = reference(qualification_path, root=root)
        if qualification_ref["sha256"] != qualification_entry.get("sha256") or qualification_ref[
            "byte_size"
        ] != qualification_entry.get("byte_size"):
            raise ValueError(f"accepted {name} qualification differs from inventory")
        qualification = load_object(root / "qualification.json")
        if name in {"task06d", "task06e"}:
            qualification["eligible_decisions"] = _load_inventory_jsonl(
                root=root,
                inventory=inventory,
                relative="eligible_decisions.jsonl",
                label=f"accepted {name}",
            )
        if name == "task06f":
            qualification["accepted_target_index_entries"] = _load_inventory_jsonl(
                root=root,
                inventory=inventory,
                relative="target_index_entries.jsonl",
                label=f"accepted {name}",
            )
            qualification["accepted_figure_aliases"] = _load_inventory_jsonl(
                root=root,
                inventory=inventory,
                relative="figure_aliases.jsonl",
                label=f"accepted {name}",
            )
        result[name] = qualification
    return result


def _repair_provenance(data_root: Path) -> JsonObject:
    """Bind every compact Task 06D--06F record consumed by comparison."""
    result: JsonObject = {}
    for name, relative_root in REPAIR_ROOTS.items():
        root = data_root / relative_root
        relatives = ["completion.json", "inventory.json", "qualification.json"]
        if name in {"task06d", "task06e"}:
            relatives.append("eligible_decisions.jsonl")
        if name == "task06f":
            relatives.extend(["figure_aliases.jsonl", "target_index_entries.jsonl"])
        result[name] = [
            {
                "authority": "artifact_root",
                "role": relative,
                **reference(root / relative, root=data_root),
            }
            for relative in relatives
        ]
    return result


def _resolve_candidate_ref(
    reference_value: JsonObject,
    *,
    collection_root: Path,
    document_input_root: Path | None,
) -> Path:
    """Resolve a historical local ref or a v3 imported-document ref."""
    if document_input_root is None:
        return verify_reference(reference_value, root=collection_root)
    return CollectionArtifactResolver(
        document_input_root=document_input_root,
        collection_output_root=collection_root,
    ).resolve(reference_value, expected_authority="document_input_root")


def _replacement_document_root(data_root: Path, bundle: JsonObject) -> Path | None:
    """Return the explicit v32 authority for a collection-only bundle."""
    imported = bundle.get("imported_document_evidence")
    if imported is None:
        return None
    value = _object(imported, "replacement imported document evidence")
    relative = _text(
        value.get("document_input_root_relative_path"),
        "replacement document input root",
    )
    root = (data_root / relative).resolve()
    if not root.is_relative_to(data_root.resolve()) or not root.is_dir():
        raise ValueError("replacement document input root escapes or is absent")
    return root


def _replacement_support(
    collection_root: Path,
    document_input_root: Path | None,
    bundle: JsonObject,
) -> dict[str, JsonObject]:
    accounting = _object(bundle.get("accounting"), "replacement accounting")
    result: dict[str, JsonObject] = {}
    for row in _objects(accounting.get("rows"), "replacement accounting rows"):
        source_id = _text(row.get("source_id"), "replacement source_id")
        if source_id in REPAIRED_SOURCES:
            continue
        if document_input_root is None:
            candidate_id = _text(row.get("candidate_id"), "replacement candidate_id")
            path = (
                collection_root
                / "documents"
                / source_id
                / candidate_id
                / "records/downstream_replay.json"
            )
        else:
            path = _resolve_candidate_ref(
                _object(row.get("downstream_replay_ref"), "downstream replay ref"),
                collection_root=collection_root,
                document_input_root=document_input_root,
            )
        result[source_id] = load_object(path)
    return result


def publish_task06g_comparison(*, data_root: Path, comparison_spec: Path) -> tuple[Path, Path]:
    """Validate and atomically publish Task 06G correspondence/comparison evidence."""
    spec = load_object(comparison_spec)
    if spec.get("schema_version") != "er_commons.task06g.comparison_template.v1":
        raise ValueError("Task 06G comparison spec schema differs")
    if spec.get("baseline_handoff_id") != BASELINE_HANDOFF_ID:
        raise ValueError("Task 06G comparison spec selects a different baseline handoff")
    artifact_relative_root = _text(spec.get("artifact_relative_root"), "artifact_relative_root")
    comparison_root = (data_root / artifact_relative_root).resolve()
    if not comparison_root.is_relative_to(data_root.resolve()):
        raise ValueError("Task 06G comparison output escapes ER_COMMONS_DATA_ROOT")
    replay_root = comparison_root.parent
    correspondence_root = replay_root / "correspondence_v1"
    checkpoint_path = replay_root / "identity_checkpoints_v1/stages/collection_handoff.json"
    checkpoint = load_object(checkpoint_path)
    replacement_handoff_id = _text(spec.get("replacement_handoff_id"), "replacement handoff ID")
    if (
        checkpoint.get("verified") is not True
        or checkpoint.get("derived_id") != replacement_handoff_id
    ):
        raise ValueError("replacement handoff checkpoint is not verified or selects another ID")
    if checkpoint.get("recomputed_id") != replacement_handoff_id:
        raise ValueError("replacement handoff checkpoint recomputation differs")
    scope_id = _scope_id_from_checkpoint(checkpoint)
    baseline_root = data_root / BASELINE_COLLECTION_ROOT
    replacement_root = replay_root / "document_publications"
    baseline_path = baseline_root / f"scopes/{BASELINE_SCOPE_ID}/contract_bundle.json"
    replacement_path = replacement_root / f"scopes/{scope_id}/contract_bundle.json"
    baseline = load_object(baseline_path)
    replacement = load_object(replacement_path)
    replacement_document_root = _replacement_document_root(data_root, replacement)
    replacement_handoff = _object(replacement.get("handoff"), "replacement handoff")
    if replacement_handoff.get("handoff_id") != replacement_handoff_id:
        raise ValueError("replacement contract bundle names a different handoff")
    if replacement_handoff.get("task04_status") != "not_evaluated":
        raise ValueError("replacement handoff must retain task04_status not_evaluated")
    stage_completion = checkpoint.get("stage_completion")
    if isinstance(stage_completion, dict):
        verify_reference(cast(Mapping[str, object], stage_completion), root=data_root)
    appendix_a_correspondence, appendix_a_provenance = _appendix_a_structure_correspondence(
        data_root=data_root,
        collection_root=replacement_root,
        document_input_root=replacement_document_root,
        bundle=replacement,
    )
    main_correspondence, main_provenance = _main_structure_correspondence(
        data_root=data_root,
        collection_root=replacement_root,
        document_input_root=replacement_document_root,
        bundle=replacement,
    )
    baseline_link_evidence, baseline_link_provenance = load_collection_link_evidence(
        data_root=data_root,
        collection_root=baseline_root,
        bundle=baseline,
        label="baseline",
    )
    replacement_link_evidence, replacement_link_provenance = load_collection_link_evidence(
        data_root=data_root,
        collection_root=replacement_root,
        bundle=replacement,
        label="replacement",
        document_input_root=replacement_document_root,
    )
    task04c_targets, task04c_provenance = load_task04c_inherited_targets(data_root=data_root)
    baseline_link_evidence["task04c_baseline_targets"] = task04c_targets
    baseline_catalog_path = verify_reference(_catalog_ref(baseline, "baseline"), root=baseline_root)
    replacement_catalog_path = verify_reference(
        _catalog_ref(replacement, "replacement"), root=replacement_root
    )
    records = build_task06g_closure(
        spec=spec,
        baseline=baseline,
        replacement=replacement,
        source_slots=load_object(data_root / SOURCE_SLOTS_PATH),
        reviews=load_object(data_root / REVIEW_CORRESPONDENCE_PATH),
        mentions=load_object(data_root / MENTION_POPULATIONS_PATH),
        repairs=_load_repairs(data_root),
        appendix_a_correspondence=appendix_a_correspondence,
        main_correspondence=main_correspondence,
        gate_c=load_object(data_root / GATE_C_PATH),
        link_evidence={
            "baseline": baseline_link_evidence,
            "replacement": replacement_link_evidence,
        },
        replacement_document_support=_replacement_support(
            replacement_root, replacement_document_root, replacement
        ),
        source_family_catalogs={
            "baseline": load_object(baseline_catalog_path),
            "replacement": load_object(replacement_catalog_path),
        },
    )
    repository_root = Path(__file__).resolve().parents[3]
    provenance = {
        "comparison_spec": _authority_reference(
            comparison_spec, root=data_root, authority="artifact_root"
        ),
        "baseline_contract": _authority_reference(
            baseline_path, root=data_root, authority="artifact_root"
        ),
        "replacement_contract": _authority_reference(
            replacement_path, root=data_root, authority="artifact_root"
        ),
        "replacement_handoff_checkpoint": _authority_reference(
            checkpoint_path, root=data_root, authority="artifact_root"
        ),
        "source_slots": _authority_reference(
            data_root / SOURCE_SLOTS_PATH, root=data_root, authority="artifact_root"
        ),
        "review_correspondence": _authority_reference(
            data_root / REVIEW_CORRESPONDENCE_PATH,
            root=data_root,
            authority="artifact_root",
        ),
        "mention_populations": _authority_reference(
            data_root / MENTION_POPULATIONS_PATH,
            root=data_root,
            authority="artifact_root",
        ),
        "task04d_gate_c": _authority_reference(
            data_root / GATE_C_PATH, root=data_root, authority="artifact_root"
        ),
        "comparison_implementation": _authority_reference(
            Path(__file__), root=repository_root, authority="repository"
        ),
        "link_comparison_implementation": _authority_reference(
            Path(__file__).with_name("comparison_links.py"),
            root=repository_root,
            authority="repository",
        ),
        "baseline_link_evidence": baseline_link_provenance,
        "replacement_link_evidence": replacement_link_provenance,
        "task04c_inherited_navigation": task04c_provenance,
        "accepted_repair_evidence": _repair_provenance(data_root),
        **appendix_a_provenance,
        **main_provenance,
    }
    if provenance["task04d_gate_c"]["sha256"] != GATE_C_SHA256:
        raise ValueError("accepted Task 04D Gate C compact record differs")
    correspondence, comparison = records
    correspondence["provenance.json"] = {
        "schema_version": "er_commons.task06g.correspondence_provenance.v1",
        **provenance,
    }
    comparison["provenance.json"] = {
        "schema_version": "er_commons.task06g.comparison_provenance.v1",
        **provenance,
    }
    _verify_or_publish(correspondence_root, _publication_files(correspondence, "correspondence"))
    _verify_or_publish(comparison_root, _publication_files(comparison, "comparison"))
    return correspondence_root / "completion.json", comparison_root / "completion.json"


__all__ = ["build_task06g_closure", "publish_task06g_comparison"]
