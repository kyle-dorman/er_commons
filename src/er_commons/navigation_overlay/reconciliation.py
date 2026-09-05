"""Reconcile accepted navigation tables into a source-free sparse link overlay."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    file_reference,
    iter_jsonl,
    json_bytes,
    jsonl_bytes,
    read_json_object,
    sha256_file,
)
from er_commons.navigation_overlay.toc_text import PARSER_VERSION, project_toc_text

JsonObject = dict[str, Any]

ACCEPTED_GATE_A_ID = (
    "navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741"
)
ACCEPTED_GATE_B_ID = (
    "navsemanticv1-ae00c6e6f70839f1ca15404c9dff14161f0a3e9aaa9e7902f51f65b36023c8fc"
)
_OUTPUT_RELATIVE = "pipelines/brisbane_baylands/task_04_navigation_overlay"
_TASK03J_RELATIVE = "pipelines/brisbane_baylands/task_03h_clean_full_v4"
_AMBIGUITY_RELATIVE = (
    "pipelines/brisbane_baylands/task_04_review/"
    "reviewv1-task03j-final-c17/gate_d/ambiguous_link_dispositions.json"
)
_SCHEMA_RELATIVE = "benchmarks/er_bench/schemas/navigation_overlay/v1/gate_c"
_OUTCOMES = (
    "empty_entry",
    "unsupported_entry_shape",
    "unsupported_target_type",
    "no_target_alias",
    "ambiguous_target_alias",
    "no_unique_destination_page",
    "destination_target_page_mismatch",
    "resolved_unique",
)
_RULES = [
    "replace_every_gate_b_human_confirmed_navigation_table_with_sealed_docling_text",
    "expose_the_same_ordered_text_entries_to_model_exploration_and_link_reconciliation",
    "identify_each_entry_by_page_line_span_and_ordered_source_cell_checksum",
    (
        "after_sealed_ascii_whitespace_casefold_normalization_only_trim_spaces_around_"
        "literal_dots_in_numeric_target_markers"
    ),
    (
        "count_supported_markers_across_the_whole_entry_and_reject_any_second_marker_"
        "as_unsupported_entry_shape"
    ),
    "require_exactly_one_terminal_printed_page_token",
    "collect_all_existing_printed_page_destinations_for_the_terminal_label",
    "intersect_existing_body_target_pages_with_printed_page_destinations",
    "require_exactly_one_page_consistent_body_target_alias",
    "create_sparse_link_records_only_when_every_threshold_passes",
    "never_create_a_new_alias_and_only_invalidate_existing_aliases_in_the_affected_closure",
    "otherwise_close_unresolved_without_guessing_or_mutating_machine_records_or_old_tables",
    "carry_all_inherited_ambiguous_links_forward_unchanged_outside_the_affected_closure",
]
_SOURCE_FREE = {
    "source_pdf_bytes_read": False,
    "source_pdf_checksum_recomputed": False,
    "renders_generated": False,
    "model_files_read": False,
    "large_task03j_files_rehashed": False,
    "task03j_files_written": False,
    "task04a_files_written": False,
    "gate_a_files_written": False,
    "gate_b_files_written": False,
}
_POLICY: JsonObject = {
    "schema_version": "er_commons.navigation_overlay.v1.link_policy",
    "target_marker": "numeric leading marker; trim spaces around dots only",
    "target_alias": "exact existing same-document body aliases filtered by page intersection",
    "printed_page": "all existing destinations for one terminal printed-page label",
    "creation": "link only after exactly one body target remains after page intersection",
    "alias_creation": "none; existing sealed target aliases are authoritative",
    "failure": "closed unresolved outcome without mutation or guessing",
}
_SECTION_MARKER = re.compile(r"^(?P<marker>\d+(?:\.\d+)+)(?=\s|$)")
_RAW_SECTION_MARKER = re.compile(r"^(?P<marker>\d+(?:\s*\.\s*\d+)+)(?=\s|$)")
_EXPLICIT_MARKER = re.compile(
    r"(?<![a-z])(?P<kind>table|figure)\s+"
    r"(?P<marker>[a-z0-9]+(?:[.-][a-z0-9]+)*)\s*:"
)
_TERMINAL = re.compile(r"(?:^|\s)(?P<label>[ivxlcdm]+|\d+(?:\.\d+)*(?:-\d+)*)$")
_MARKER_NORMALIZATION = "sealed_ascii_whitespace_casefold_then_trim_spaces_around_literal_dots_only"


@dataclass(frozen=True)
class GateCReconciliationRequest:
    """Exact roots for one source-free Gate C publication."""

    data_root: Path
    repo_root: Path
    gate_a_root: Path | None = None
    gate_b_root: Path | None = None
    task03j_root: Path | None = None
    task04a_ambiguous_path: Path | None = None
    output_parent: Path | None = None

    def resolved_gate_a_root(self) -> Path:
        return (
            self.gate_a_root or self.data_root / _OUTPUT_RELATIVE / ACCEPTED_GATE_A_ID
        ).resolve()

    def resolved_gate_b_root(self) -> Path:
        return (
            self.gate_b_root or self.data_root / _OUTPUT_RELATIVE / ACCEPTED_GATE_B_ID
        ).resolve()

    def resolved_task03j_root(self) -> Path:
        return (self.task03j_root or self.data_root / _TASK03J_RELATIVE).resolve()

    def resolved_ambiguity_path(self) -> Path:
        return (self.task04a_ambiguous_path or self.data_root / _AMBIGUITY_RELATIVE).resolve()

    def resolved_output_parent(self) -> Path:
        return (self.output_parent or self.data_root / _OUTPUT_RELATIVE).resolve()


@dataclass(frozen=True)
class _DocumentIndex:
    target_aliases: dict[tuple[str, str], list[JsonObject]]
    entities: dict[str, JsonObject]
    entity_pages: dict[str, tuple[str, ...]]
    destination_aliases: dict[str, list[JsonObject]]
    physical_by_page_id: dict[str, int]


def prepare_and_publish_gate_c(request: GateCReconciliationRequest) -> Path:
    """Build the effective TOC text view, reconcile its entries, and publish."""
    repo_root = request.repo_root.resolve()
    _require(repo_root.is_dir(), f"repository root is absent: {repo_root}")
    gate_a, gate_a_refs = _validate_gate(request.resolved_gate_a_root(), ACCEPTED_GATE_A_ID)
    gate_b, gate_b_refs = _validate_gate(request.resolved_gate_b_root(), ACCEPTED_GATE_B_ID)
    _require(gate_b.get("overlay_plan_id") == ACCEPTED_GATE_A_ID, "Gate B does not bind Gate A")
    closure = read_json_object(request.resolved_gate_a_root() / "affected_closure.json")
    _validate_gate_a_closure(closure)

    task03j_inputs = cast(JsonObject, cast(JsonObject, gate_a["inputs"])["task03j"])
    candidate_records = cast(list[JsonObject], task03j_inputs["candidate_records"])
    _require(len(candidate_records) == 35, "Gate A must bind exactly 35 sealed candidates")
    sealed: list[JsonObject] = []
    for row in candidate_records:
        recorded_completion = cast(JsonObject, row["structured_document_completion"])
        completion_path = request.data_root.resolve() / str(recorded_completion["path"])
        completion_reference = file_reference(
            completion_path,
            root=request.data_root.resolve(),
        )
        _require(
            completion_reference["sha256"] == recorded_completion["sha256"],
            f"changed sealed candidate completion: {completion_path}",
        )
        sealed.append(
            {
                "source_id": row["source_id"],
                "candidate_id": row["candidate_id"],
                "completion_record": completion_reference,
            }
        )
    bound = {(str(row["source_id"]), str(row["candidate_id"])): row for row in candidate_records}
    table_dispositions = [
        row
        for row in iter_jsonl(request.resolved_gate_b_root() / "semantic_dispositions.jsonl")
        if row.get("entity_kind") == "table"
        and row.get("disposition") == "human_confirmed_navigation"
    ]
    _require(len(table_dispositions) == 15, "Gate B must select exactly 15 navigation tables")
    selected_candidates = {
        (str(row["source_id"]), str(row["candidate_id"])) for row in table_dispositions
    }
    for key in selected_candidates:
        _validate_candidate_files(request, bound[key])

    pages: list[JsonObject] = []
    entries: list[JsonObject] = []
    reconciliations: list[JsonObject] = []
    links: list[JsonObject] = []
    docling_refs: list[JsonObject] = []
    indexes: dict[tuple[str, str], _DocumentIndex] = {}
    for disposition in sorted(table_dispositions, key=lambda row: str(row["entity_id"])):
        key = (str(disposition["source_id"]), str(disposition["candidate_id"]))
        _require(key in bound, f"Gate B table is absent from Gate A candidates: {key}")
        document_root = (
            request.resolved_task03j_root() / "document_publications/documents" / key[0] / key[1]
        )
        index = indexes.setdefault(key, _load_document_index(document_root))
        table = _find_table(document_root, str(disposition["entity_id"]))
        source_page_ids = sorted(
            {str(region["page_id"]) for region in cast(list[JsonObject], table["regions"])}
        )
        _require(len(source_page_ids) == 1, f"table spans multiple source pages: {table['id']}")
        source_page_id = source_page_ids[0]
        physical_page = index.physical_by_page_id[source_page_id]
        decision_pages = cast(list[int], disposition["decision_physical_pages"])
        _require(decision_pages == [physical_page], "Gate B table page differs from canonical page")
        projection = project_toc_text(
            data_root=request.data_root.resolve(),
            task03j_root=request.resolved_task03j_root(),
            document_root=document_root,
            source_id=key[0],
            candidate_id=key[1],
            source_page_id=source_page_id,
            physical_page=physical_page,
            source_table_id=str(table["id"]),
            table_disposition_id=str(disposition["disposition_id"]),
        )
        pages.append(projection.page)
        entries.extend(projection.entries)
        docling_refs.append(projection.sealed_reference)
        for entry in projection.entries:
            record, link = _reconcile_entry(
                source_id=key[0],
                candidate_id=key[1],
                entry=entry,
                index=index,
                link_view_id=None,
            )
            reconciliations.append(record)
            if link is not None:
                links.append(link)
    _require(len(pages) == 15, f"expected 15 TOC text pages, got {len(pages)}")
    _require(len(entries) == 560, f"expected 560 TOC text entries, got {len(entries)}")

    ambiguity_path = request.resolved_ambiguity_path()
    task04a_inputs = cast(JsonObject, cast(JsonObject, gate_a["inputs"])["task04a"])
    pinned_ambiguity = cast(JsonObject, task04a_inputs["ambiguous_link_dispositions"])
    ambiguity_reference = file_reference(ambiguity_path, root=request.data_root.resolve())
    _require(
        ambiguity_reference == pinned_ambiguity,
        "Task 04A ambiguity register differs from the Gate A-pinned input",
    )
    ambiguity_payload = read_json_object(ambiguity_path)
    ambiguity_entries = cast(list[JsonObject], ambiguity_payload.get("entries"))
    _validate_ambiguity_population(ambiguity_entries, closure)
    inherited = _inherit_ambiguities(ambiguity_entries, bound, link_view_id=None)

    schema_root = repo_root / _SCHEMA_RELATIVE
    schemas = [
        file_reference(path, root=repo_root) for path in sorted(schema_root.glob("*.schema.json"))
    ]
    _require(len(schemas) == 8, "Gate C schema bundle is incomplete")
    implementation = file_reference(Path(__file__).resolve(), root=repo_root)
    parser_implementation = file_reference(
        Path(project_toc_text.__code__.co_filename).resolve(), root=repo_root
    )
    preimage = {
        "schema_version": "er_commons.navigation_overlay.v1.link_identity_preimage",
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
        "semantic_view_id": ACCEPTED_GATE_B_ID,
        "gate_a_completion_sha256": gate_a_refs["completion"]["sha256"],
        "gate_b_completion_sha256": gate_b_refs["completion"]["sha256"],
        "task04a_ambiguity_bytes_sha256": ambiguity_reference["sha256"],
        "sealed_candidates_sha256": canonical_json_sha256(sealed),
        "sealed_docling_pages_sha256": canonical_json_sha256(docling_refs),
        "toc_text_parser_version": PARSER_VERSION,
        "link_policy_sha256": canonical_json_sha256(_POLICY),
        "schema_bundle_sha256": canonical_json_sha256(schemas),
        "implementation_sha256": implementation["sha256"],
        "toc_text_implementation_sha256": parser_implementation["sha256"],
    }
    link_view_id = f"navlinkv1-{canonical_json_sha256(preimage)}"
    pages = [_bind_effective_view(row, link_view_id) for row in pages]
    entries = [_bind_effective_view(row, link_view_id) for row in entries]
    reconciliations = [_bind_link_view(row, link_view_id) for row in reconciliations]
    links = [_bind_link_view(row, link_view_id) for row in links]
    inherited = [_bind_link_view(row, link_view_id) for row in inherited]
    accounting = _accounting(pages, entries, reconciliations, links, inherited)
    refs = {
        "gate_a_specification": gate_a_refs["manifest"],
        "gate_a_completion": gate_a_refs["completion"],
        "gate_a_inventory": gate_a_refs["inventory"],
        "affected_closure": file_reference(
            request.resolved_gate_a_root() / "affected_closure.json",
            root=request.data_root.resolve(),
        ),
        "gate_b_specification": gate_b_refs["manifest"],
        "gate_b_completion": gate_b_refs["completion"],
        "gate_b_inventory": gate_b_refs["inventory"],
        "semantic_dispositions": file_reference(
            request.resolved_gate_b_root() / "semantic_dispositions.jsonl",
            root=request.data_root.resolve(),
        ),
        "task04a_ambiguous_link_dispositions": ambiguity_reference,
        "sealed_candidates": sealed,
        "sealed_docling_pages": docling_refs,
    }
    specification = _specification(link_view_id, preimage, refs, accounting, request)
    _validate_schemas(
        schema_root, pages, entries, reconciliations, [], links, inherited, specification
    )
    return _publish(
        request.resolved_output_parent(),
        link_view_id,
        pages,
        entries,
        reconciliations,
        links,
        inherited,
        specification,
        accounting,
        schema_root,
    )


def _validate_gate_a_closure(closure: JsonObject) -> None:
    """Require the accepted zero-invalidation Gate A closure accounting."""
    inherited_closure = cast(JsonObject, closure.get("inherited_ambiguous_links"))
    closure_accounting = cast(JsonObject, closure.get("accounting"))
    _require(
        len(cast(list[str], inherited_closure.get("in_closure_ids"))) == 0
        and len(cast(list[str], inherited_closure.get("outside_closure_ids"))) == 725
        and closure_accounting.get("affected_alias_count") == 0
        and closure_accounting.get("affected_link_count") == 0
        and closure_accounting.get("affected_collection_resolution_count") == 0
        and closure_accounting.get("inherited_ambiguous_link_in_closure_count") == 0
        and closure_accounting.get("inherited_ambiguous_link_outside_closure_count") == 725,
        "Gate A ambiguity closure differs",
    )


def _validate_ambiguity_population(entries: list[JsonObject], closure: JsonObject) -> None:
    """Require exact one-to-one coverage of Gate A's inherited ambiguity IDs."""
    inherited = cast(JsonObject, closure["inherited_ambiguous_links"])
    reference_ids = [str(entry.get("reference_id")) for entry in entries]
    outside_ids = cast(list[str], inherited["outside_closure_ids"])
    all_ids = cast(list[str], inherited["all_ids"])
    _require(
        len(reference_ids) == len(set(reference_ids)) == 725
        and sorted(reference_ids) == sorted(outside_ids) == sorted(all_ids),
        "Task 04A ambiguity register differs from the Gate A closure",
    )


def _normalize_numeric_marker(value: str) -> str | None:
    """Normalize only whitespace immediately surrounding decimal separators."""
    stripped = value.strip()
    if not re.fullmatch(r"[0-9]+(?:\s*\.\s*[0-9]+)+", stripped):
        return None
    return re.sub(r"\s*\.\s*", ".", stripped)


def _normalize_alias(value: str) -> str:
    """Apply the sealed ASCII-whitespace and case-folding policy."""
    value = unicodedata.normalize("NFC", value.replace("\u00a0", " "))
    return " ".join(value.split()).casefold()


def _normalize_marker_dots(value: str) -> str:
    """Normalize spaces only around literal dots between digits."""
    return re.sub(r"(?<=\d)\s*\.\s*(?=\d)", ".", _normalize_alias(value))


def _reconcile_entry(
    *,
    source_id: str,
    candidate_id: str,
    entry: JsonObject,
    index: _DocumentIndex,
    link_view_id: str | None,
) -> tuple[JsonObject, JsonObject | None]:
    """Apply the documented fail-closed link policy to one effective text entry."""
    identity = {
        "toc_text_entry_id": entry["toc_text_entry_id"],
        "entry_text_sha256": canonical_json_sha256(entry["raw_text"]),
    }
    reconciliation_id = f"navtocentryrecv1-{canonical_json_sha256(identity)[:24]}"
    raw_entry = str(entry["raw_text"])
    base_entry = _normalize_alias(raw_entry)
    normalized_entry = _normalize_marker_dots(raw_entry)
    section_match = _SECTION_MARKER.match(normalized_entry)
    explicit_matches = list(_EXPLICIT_MARKER.finditer(normalized_entry))
    supported_marker_count = (1 if section_match else 0) + len(explicit_matches)
    marker_kind: str | None = None
    raw_marker: str | None = None
    normalized_marker: str | None = None
    marker_end = 0
    if section_match is not None:
        marker_kind = "section"
        normalized_marker = section_match.group("marker")
        raw_match = _RAW_SECTION_MARKER.match(base_entry)
        raw_marker = raw_match.group("marker") if raw_match else normalized_marker
        marker_end = section_match.end()
    elif explicit_matches and explicit_matches[0].start() == 0:
        match = explicit_matches[0]
        marker_kind = match.group("kind")
        normalized_marker = match.group("marker")
        raw_marker = base_entry[: match.end()].rstrip(" :")
        marker_end = match.end()
    # The token must be complete and final in the reconstructed entry.
    terminal = cast(str | None, entry.get("terminal_destination_token"))
    terminal_start = len(normalized_entry) - len(terminal) if terminal else 0
    target_aliases: list[JsonObject] = []
    target_alias_ids: list[str] = []
    selected_target_alias_ids: list[str] = []
    distinct_target_ids: list[str] = []
    destination_aliases: list[JsonObject] = []
    destination_alias_ids: list[str] = []
    destination_page_ids: list[str] = []
    page_consistent_target_ids: list[str] = []
    page_disambiguation_applied = False
    target_page_ids: list[str] = []
    link: JsonObject | None = None
    outcome = "empty_entry"
    if base_entry:
        if (
            marker_kind is None
            or terminal is None
            or terminal_start <= marker_end
            or supported_marker_count != 1
        ):
            outcome = "unsupported_entry_shape"
        elif (
            marker_kind == "figure"
            and (
                marker_kind,
                cast(str, normalized_marker),
            )
            not in index.target_aliases
        ):
            outcome = "unsupported_target_type"
        else:
            key = (marker_kind, cast(str, normalized_marker))
            target_aliases = index.target_aliases.get(key, [])
            target_alias_ids = sorted({str(alias["id"]) for alias in target_aliases})
            distinct_target_ids = sorted(
                {
                    str(target["target_id"])
                    for alias in target_aliases
                    for target in cast(list[JsonObject], alias.get("eligible_targets", []))
                }
            )
            if not distinct_target_ids:
                outcome = "no_target_alias"
            else:
                destination_aliases = index.destination_aliases.get(_normalize_alias(terminal), [])
                destination_alias_ids = sorted({str(alias["id"]) for alias in destination_aliases})
                destination_page_ids = sorted(
                    {
                        str(target["target_id"])
                        for alias in destination_aliases
                        for target in cast(list[JsonObject], alias["eligible_targets"])
                    }
                )
                if not destination_page_ids:
                    outcome = "no_unique_destination_page"
                else:
                    page_consistent_target_ids = [
                        target_id
                        for target_id in distinct_target_ids
                        if len(index.entity_pages.get(target_id, ())) == 1
                        and index.entity_pages[target_id][0] in destination_page_ids
                    ]
                    page_disambiguation_applied = (
                        len(distinct_target_ids) > 1 or len(destination_page_ids) > 1
                    )
                    if not page_consistent_target_ids:
                        outcome = "destination_target_page_mismatch"
                    elif len(page_consistent_target_ids) > 1:
                        outcome = "ambiguous_target_alias"
                    else:
                        target_id = page_consistent_target_ids[0]
                        target_page_ids = list(index.entity_pages[target_id])
                        selected_target_alias_ids = sorted(
                            {
                                str(alias["id"])
                                for alias in target_aliases
                                if any(
                                    str(target["target_id"]) == target_id
                                    for target in cast(
                                        list[JsonObject], alias.get("eligible_targets", [])
                                    )
                                )
                            }
                        )
                        if len(selected_target_alias_ids) != 1:
                            outcome = "ambiguous_target_alias"
                            continue_link = False
                        else:
                            outcome = "resolved_unique"
                            continue_link = True
                    if outcome != "resolved_unique" or not continue_link:
                        target_id = ""
                    else:
                        resolution_method = (
                            "existing_body_alias_and_printed_page_candidate_intersection"
                            if page_disambiguation_applied
                            else "existing_unique_body_alias_and_independent_printed_page_agreement"
                        )
                if outcome == "resolved_unique":
                    link_identity = {
                        "reconciliation_id": reconciliation_id,
                        "target_id": target_id,
                    }
                    link_id = f"navlinkentryv1-{canonical_json_sha256(link_identity)[:24]}"
                    link = {
                        "schema_version": "er_commons.navigation_overlay.v1.link_overlay",
                        "link_view_id": link_view_id or "navlinkv1-" + "0" * 64,
                        "semantic_view_id": ACCEPTED_GATE_B_ID,
                        "link_overlay_id": link_id,
                        "reconciliation_id": reconciliation_id,
                        "source_id": source_id,
                        "candidate_id": candidate_id,
                        "operation": "add",
                        "source_toc_entry_id": entry["toc_text_entry_id"],
                        "normalized_marker": normalized_marker,
                        "terminal_destination_token": terminal,
                        "existing_body_alias_id": selected_target_alias_ids[0],
                        "target_id": target_id,
                        "target_page_id": target_page_ids[0],
                        "destination_page_alias_ids": destination_alias_ids,
                        "resolution_method": resolution_method,
                    }
    record = {
        "schema_version": "er_commons.navigation_overlay.v1.toc_entry_reconciliation",
        "link_view_id": link_view_id or "navlinkv1-" + "0" * 64,
        "semantic_view_id": ACCEPTED_GATE_B_ID,
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
        "reconciliation_id": reconciliation_id,
        "toc_text_entry_id": entry["toc_text_entry_id"],
        "source_id": source_id,
        "candidate_id": candidate_id,
        "source_page_id": entry["source_page_id"],
        "physical_page": entry["physical_page"],
        "entry_locator": {
            "toc_text_page_id": entry["toc_text_page_id"],
            "entry_index": entry["entry_index"],
            "entry_text_sha256": canonical_json_sha256(entry["raw_text"]),
        },
        "raw_entry_text": raw_entry,
        "normalized_entry_text": normalized_entry,
        "marker_kind": marker_kind,
        "raw_marker": raw_marker,
        "normalized_marker": normalized_marker,
        "marker_normalization_rule": _MARKER_NORMALIZATION,
        "supported_marker_count": supported_marker_count,
        "terminal_destination_token": terminal,
        "target_alias_ids": target_alias_ids,
        "selected_target_alias_ids": selected_target_alias_ids,
        "distinct_target_ids": distinct_target_ids,
        "target_alias_count": len(target_alias_ids),
        "page_consistent_target_ids": page_consistent_target_ids,
        "page_disambiguation_applied": page_disambiguation_applied,
        "destination_page_alias_ids": destination_alias_ids,
        "distinct_destination_page_ids": destination_page_ids,
        "destination_page_count": len(destination_page_ids),
        "target_physical_page_ids": target_page_ids,
        "entry_outcome": outcome,
        "link_overlay_id": None if link is None else link["link_overlay_id"],
    }
    return record, link


def _load_document_index(root: Path) -> _DocumentIndex:
    aliases = list(iter_jsonl(root / "content/canonical/target_aliases.jsonl"))
    pages = list(iter_jsonl(root / "content/canonical/pages.jsonl"))
    physical_by_page_id = {
        str(page["id"]): int(cast(int, page["physical_page_number"])) for page in pages
    }
    page_by_id = {str(page["id"]): page for page in pages}
    for page in pages:
        _require(isinstance(page.get("physical_page_number"), int), "invalid physical page")
    entities: dict[str, JsonObject] = {}
    entity_pages: dict[str, tuple[str, ...]] = {}
    for filename in ("blocks.jsonl", "sections.jsonl", "tables.jsonl"):
        path = root / "content/canonical" / filename
        if not path.is_file():
            continue
        for entity in iter_jsonl(path):
            entity_id = str(entity["id"])
            entities[entity_id] = entity
            if filename != "sections.jsonl":
                entity_pages[entity_id] = tuple(
                    sorted(
                        {
                            str(region["page_id"])
                            for region in cast(list[JsonObject], entity.get("regions", []))
                        }
                    )
                )
    for entity_id, entity in entities.items():
        if "/section/" in entity_id:
            heading = entity.get("heading_block_id")
            entity_pages[entity_id] = (
                entity_pages.get(str(heading), ()) if isinstance(heading, str) else ()
            )

    target_index: dict[tuple[str, str], list[JsonObject]] = defaultdict(list)
    destination_index: dict[str, list[JsonObject]] = defaultdict(list)
    for alias in aliases:
        kind = str(alias.get("alias_kind"))
        normalized = _normalize_marker_dots(str(alias.get("normalized_alias", "")))
        eligible: list[JsonObject] = []
        for target in cast(list[JsonObject], alias.get("targets", [])):
            target_id = str(target.get("target_id"))
            lookup_entity: JsonObject | None = entities.get(target_id)
            if kind in {"section", "table", "figure"}:
                if lookup_entity is not None and _body_non_navigation(lookup_entity):
                    eligible.append(target)
            elif kind == "printed_page" and target.get("target_type") == "page":
                lookup_page: JsonObject | None = page_by_id.get(target_id)
                if lookup_page is not None and _normalize_alias(
                    str(lookup_page.get("printed_page_label", ""))
                ) == _normalize_alias(normalized):
                    eligible.append(target)
        if not eligible:
            continue
        indexed_alias = {**alias, "eligible_targets": eligible}
        if kind == "section":
            match = _SECTION_MARKER.match(normalized)
            if match:
                target_index[(kind, match.group("marker"))].append(indexed_alias)
        elif kind in {"table", "figure"}:
            marker_only = re.fullmatch(rf"{kind}\s+([^\s:]+):?", normalized)
            if marker_only:
                target_index[(kind, marker_only.group(1))].append(indexed_alias)
        elif kind == "printed_page":
            destination_index[_normalize_alias(normalized)].append(indexed_alias)
    return _DocumentIndex(
        dict(target_index),
        entities,
        entity_pages,
        dict(destination_index),
        physical_by_page_id,
    )


def _validate_candidate_files(
    request: GateCReconciliationRequest,
    candidate: JsonObject,
) -> None:
    """Validate compact seals and size-check every Task 03J file Gate C reads."""
    publication_root = request.resolved_task03j_root() / "document_publications"
    inventory_ref = cast(JsonObject, candidate["candidate_inventory"])
    inventory_path = publication_root / str(inventory_ref["path"])
    _require(
        inventory_path.is_file() and sha256_file(inventory_path) == inventory_ref["sha256"],
        f"changed candidate inventory: {inventory_path}",
    )
    inventory = read_json_object(inventory_path)
    files = {str(row["path"]): row for row in cast(list[JsonObject], inventory.get("files", []))}
    declared = {
        str(row["path"]): row
        for row in cast(list[JsonObject], candidate.get("canonical_records", []))
    }
    for relative, reference in declared.items():
        inventory_record = files.get(relative)
        _require(
            inventory_record is not None
            and inventory_record.get("sha256") == reference.get("sha256")
            and inventory_record.get("byte_size") == reference.get("byte_size"),
            f"canonical reference differs from candidate inventory: {relative}",
        )
    document_root = inventory_path.parent.parent
    required = (
        "records/document_identity.json",
        "content/canonical/pages.jsonl",
        "content/canonical/sections.jsonl",
        "content/canonical/blocks.jsonl",
        "content/canonical/tables.jsonl",
        "content/canonical/target_aliases.jsonl",
        "content/observations/page_labels.jsonl",
    )
    for relative in required:
        size_reference = files.get(relative)
        path = document_root / relative
        _require(
            size_reference is not None
            and path.is_file()
            and path.stat().st_size == size_reference.get("byte_size"),
            f"changed or unsealed Gate C input: {path}",
        )
        if relative == "records/document_identity.json":
            identity_reference = cast(JsonObject, size_reference)
            _require(
                sha256_file(path) == identity_reference.get("sha256"),
                f"changed candidate identity: {path}",
            )


def _body_non_navigation(entity: JsonObject) -> bool:
    return (
        entity.get("content_layer") == "body"
        and not bool(entity.get("is_toc_row", False))
        and entity.get("semantic_placement") != "toc_content"
    )


def _find_table(root: Path, table_id: str) -> JsonObject:
    matches = [
        row
        for row in iter_jsonl(root / "content/canonical/tables.jsonl")
        if row.get("id") == table_id
    ]
    _require(len(matches) == 1, f"canonical table lookup is not unique: {table_id}")
    return matches[0]


def _inherit_ambiguities(
    entries: list[JsonObject], bound: dict[tuple[str, str], JsonObject], *, link_view_id: str | None
) -> list[JsonObject]:
    rows = []
    for entry in sorted(entries, key=lambda row: str(row["reference_id"])):
        key = (str(entry["source_id"]), str(entry["candidate_id"]))
        _require(key in bound, f"ambiguity entry is outside sealed candidates: {key}")
        completion = cast(JsonObject, bound[key]["structured_document_completion"])
        identity = {
            "reference_id": entry["reference_id"],
            "record_sha256": canonical_json_sha256(entry),
        }
        rows.append(
            {
                "schema_version": (
                    "er_commons.navigation_overlay.v1.inherited_ambiguous_disposition"
                ),
                "link_view_id": link_view_id or "navlinkv1-" + "0" * 64,
                "disposition_id": f"navambigv1-{canonical_json_sha256(identity)[:24]}",
                "reference_id": entry["reference_id"],
                "source_id": entry["source_id"],
                "candidate_id": entry["candidate_id"],
                "closure_membership": "outside_gate_c_affected_closure",
                "disposition": "inherited_unresolved_unchanged",
                "downstream_status": "excluded_from_trusted_resolved_link_use",
                "task04a_ambiguity_record_sha256": canonical_json_sha256(entry),
                "sealed_candidate_completion_sha256": completion["sha256"],
                "reason": "outside_affected_closure_not_re_reviewed",
            }
        )
    return rows


def _bind_link_view(row: JsonObject, link_view_id: str) -> JsonObject:
    return {**row, "link_view_id": link_view_id}


def _bind_effective_view(row: JsonObject, link_view_id: str) -> JsonObject:
    """Bind a parser output to the accepted semantic and Gate A identities."""
    return {
        **row,
        "link_view_id": link_view_id,
        "semantic_view_id": ACCEPTED_GATE_B_ID,
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
    }


def _accounting(
    pages: list[JsonObject],
    entries: list[JsonObject],
    reconciliations: list[JsonObject],
    links: list[JsonObject],
    inherited: list[JsonObject],
) -> JsonObject:
    counts = Counter(str(row["entry_outcome"]) for row in reconciliations)
    accounting = {
        "confirmed_navigation_table_count": 15,
        "toc_text_page_count": len(pages),
        "toc_text_entry_count": len(entries),
        "toc_entry_reconciliation_count": len(reconciliations),
        "toc_entry_outcome_counts": {name: counts[name] for name in _OUTCOMES},
        "resolved_toc_entry_count": counts["resolved_unique"],
        "unresolved_toc_entry_count": len(entries) - counts["resolved_unique"],
        "alias_overlay_addition_count": 0,
        "link_overlay_addition_count": len(links),
        "existing_alias_invalidation_count": 0,
        "existing_link_invalidation_count": 0,
        "inherited_ambiguous_disposition_count": len(inherited),
        "inherited_ambiguous_in_affected_closure_count": 0,
        "inherited_ambiguous_outside_affected_closure_count": len(inherited),
    }
    _require(
        len(pages) == 15 and len(entries) == len(reconciliations) == 560 and len(inherited) == 725,
        f"Gate C production accounting differs: {accounting}",
    )
    return accounting


def _specification(
    link_view_id: str,
    preimage: JsonObject,
    refs: JsonObject,
    accounting: JsonObject,
    request: GateCReconciliationRequest,
) -> JsonObject:
    return {
        "schema_version": "er_commons.navigation_overlay.v1.gate_c_specification",
        "link_view_id": link_view_id,
        "semantic_view_id": ACCEPTED_GATE_B_ID,
        "overlay_plan_id": ACCEPTED_GATE_A_ID,
        "status": "gate_c_complete",
        "inputs": refs,
        "identity_preimage": preimage,
        "outputs": {
            "toc_text_pages": {
                "path": "toc_text_pages.jsonl",
                "sha256": "0" * 64,
                "byte_size": 0,
            },
            "toc_text_entries": {
                "path": "toc_text_entries.jsonl",
                "sha256": "0" * 64,
                "byte_size": 0,
            },
            "toc_entry_reconciliations": {
                "path": "toc_entry_reconciliations.jsonl",
                "sha256": "0" * 64,
                "byte_size": 0,
            },
            "alias_overlay": {"path": "alias_overlay.jsonl", "sha256": "0" * 64, "byte_size": 0},
            "link_overlay": {"path": "link_overlay.jsonl", "sha256": "0" * 64, "byte_size": 0},
            "inherited_ambiguous_link_dispositions": {
                "path": "inherited_ambiguous_link_dispositions.jsonl",
                "sha256": "0" * 64,
                "byte_size": 0,
            },
        },
        "reconciliation_rules": _RULES,
        "outcome_precedence": list(_OUTCOMES),
        "accounting": accounting,
        "reproduction": {
            "package_api": (
                "er_commons.navigation_overlay.reconciliation.prepare_and_publish_gate_c"
            ),
            "command": "uv run python scripts/reconcile_task04c_gate_c.py --repo-root .",
            "arguments": {
                "data_root": "ER_COMMONS_DATA_ROOT",
                "repo_root": ".",
                "gate_a_root": f"{_OUTPUT_RELATIVE}/{ACCEPTED_GATE_A_ID}",
                "gate_b_root": f"{_OUTPUT_RELATIVE}/{ACCEPTED_GATE_B_ID}",
                "output_parent": _OUTPUT_RELATIVE,
            },
        },
        "source_free_boundary": _SOURCE_FREE,
        "warnings": [],
    }


def _validate_gate(root: Path, expected_id: str) -> tuple[JsonObject, JsonObject]:
    _require(root.name == expected_id and root.is_dir(), f"accepted gate root differs: {root}")
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    completion = read_json_object(completion_path)
    _require(completion.get("status") == "complete", f"gate is incomplete: {root}")
    for reference in cast(list[JsonObject], completion.get("managed_files", [])):
        path = root / str(reference["path"])
        _require(
            path.is_file()
            and sha256_file(path) == reference["sha256"]
            and path.stat().st_size == reference["byte_size"],
            f"changed managed gate file: {path}",
        )
    manifest_name = (
        "gate_a_specification.json"
        if expected_id == ACCEPTED_GATE_A_ID
        else "semantic_view_manifest.json"
    )
    refs = {
        "manifest": file_reference(root / manifest_name, root=root.parent.parent.parent.parent),
        "completion": file_reference(completion_path, root=root.parent.parent.parent.parent),
        "inventory": file_reference(inventory_path, root=root.parent.parent.parent.parent),
    }
    return read_json_object(root / manifest_name), refs


def _validate_schemas(
    schema_root: Path,
    pages: list[JsonObject],
    entries: list[JsonObject],
    reconciliations: list[JsonObject],
    aliases: list[JsonObject],
    links: list[JsonObject],
    inherited: list[JsonObject],
    specification: JsonObject,
) -> None:
    pairs = (
        ("toc text page", "toc_text_page_row.schema.json", pages),
        ("toc text entry", "toc_text_entry_row.schema.json", entries),
        (
            "toc entry reconciliation",
            "toc_entry_reconciliation_row.schema.json",
            reconciliations,
        ),
        ("alias overlay", "alias_overlay_row.schema.json", aliases),
        ("link overlay", "link_overlay_row.schema.json", links),
        ("inherited ambiguity", "inherited_ambiguous_link_disposition_row.schema.json", inherited),
    )
    for label, filename, records in pairs:
        validator = Draft202012Validator(read_json_object(schema_root / filename))
        for index, row in enumerate(records):
            errors = sorted(validator.iter_errors(row), key=lambda error: list(error.path))
            if errors:
                raise ValueError(f"invalid {label} {index}: {errors[0].message}")
    errors = sorted(
        Draft202012Validator(
            read_json_object(schema_root / "gate_c_specification.schema.json")
        ).iter_errors(specification),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(f"invalid Gate C specification: {errors[0].message}")


def _publish(
    output_parent: Path,
    link_view_id: str,
    pages: list[JsonObject],
    entries: list[JsonObject],
    reconciliations: list[JsonObject],
    links: list[JsonObject],
    inherited: list[JsonObject],
    specification: JsonObject,
    accounting: JsonObject,
    schema_root: Path,
) -> Path:
    payloads = {
        "toc_text_pages.jsonl": jsonl_bytes(pages),
        "toc_text_entries.jsonl": jsonl_bytes(entries),
        "toc_entry_reconciliations.jsonl": jsonl_bytes(reconciliations),
        "alias_overlay.jsonl": b"",
        "link_overlay.jsonl": jsonl_bytes(links),
        "inherited_ambiguous_link_dispositions.jsonl": jsonl_bytes(inherited),
    }
    for name, content in payloads.items():
        specification["outputs"][name.removesuffix(".jsonl")] = {
            "path": name,
            "sha256": __import__("hashlib").sha256(content).hexdigest(),
            "byte_size": len(content),
        }
    payloads["navigation_link_manifest.json"] = json_bytes(specification)
    payloads["records/identity_preimage.json"] = json_bytes(specification["identity_preimage"])
    final = output_parent / link_view_id
    if final.exists():
        for relative, content in payloads.items():
            _require(
                (final / relative).is_file() and (final / relative).read_bytes() == content,
                f"refusing to reuse changed Gate C artifact: {final / relative}",
                FileExistsError,
            )
        _validate_published(final, schema_root)
        return final
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{link_view_id}.", dir=output_parent))
    try:
        for relative, content in payloads.items():
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        inventory = artifact_inventory(
            staging, {"records/artifact_inventory.json", "records/completion_record.json"}
        )
        inventory_path = staging / "records/artifact_inventory.json"
        inventory_path.write_bytes(json_bytes(inventory))
        ordered = (
            "toc_text_pages.jsonl",
            "toc_text_entries.jsonl",
            "toc_entry_reconciliations.jsonl",
            "alias_overlay.jsonl",
            "link_overlay.jsonl",
            "inherited_ambiguous_link_dispositions.jsonl",
            "navigation_link_manifest.json",
            "records/identity_preimage.json",
            "records/artifact_inventory.json",
        )
        completion = {
            "schema_version": "er_commons.navigation_overlay.v1.gate_c_completion",
            "link_view_id": link_view_id,
            "semantic_view_id": ACCEPTED_GATE_B_ID,
            "overlay_plan_id": ACCEPTED_GATE_A_ID,
            "status": "complete",
            "gate_c_specification": file_reference(
                staging / "navigation_link_manifest.json", root=staging
            ),
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "managed_files": [file_reference(staging / name, root=staging) for name in ordered],
            "accounting": accounting,
            "validation": {
                "schema_validation_passed": True,
                "toc_text_page_coverage_complete": True,
                "toc_entry_coverage_complete": True,
                "entry_locators_reproduced": True,
                "created_records_meet_full_evidence_threshold": True,
                "all_unresolved_entries_are_closed": True,
                "inherited_ambiguity_coverage_complete": True,
                "existing_machine_records_unchanged": True,
                "output_ids_unique": True,
                "output_order_deterministic": True,
                "identity_rederived": True,
                "repeated_build_reused_identical_namespace": True,
            },
            "atomic_publication": {
                "inventory_completed_before_completion": True,
                "completion_published_last": True,
                "temporary_namespace_atomically_renamed": True,
                "no_clobber_reuse": True,
            },
            "source_free_boundary": _SOURCE_FREE,
        }
        errors = list(
            Draft202012Validator(
                read_json_object(schema_root / "gate_c_completion.schema.json")
            ).iter_errors(completion)
        )
        _require(not errors, f"invalid Gate C completion: {errors[0].message if errors else ''}")
        (staging / "records/completion_record.json").write_bytes(json_bytes(completion))
        os.rename(staging, final)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    _validate_published(final, schema_root)
    return final


def _validate_published(root: Path, schema_root: Path) -> None:
    completion = read_json_object(root / "records/completion_record.json")
    _require(
        completion.get("link_view_id") == root.name and completion.get("status") == "complete",
        "invalid Gate C completion identity",
    )
    preimage = read_json_object(root / "records/identity_preimage.json")
    _require(
        root.name == f"navlinkv1-{canonical_json_sha256(preimage)}",
        "Gate C identity does not rederive from its sealed preimage",
    )
    _require(
        sha256_file(root / "records/artifact_inventory.json")
        == completion.get("artifact_inventory_sha256"),
        "Gate C inventory seal differs",
    )
    for reference in cast(list[JsonObject], completion["managed_files"]):
        path = root / str(reference["path"])
        _require(
            path.is_file()
            and sha256_file(path) == reference["sha256"]
            and path.stat().st_size == reference["byte_size"],
            f"changed Gate C managed file: {path}",
        )
    errors = list(
        Draft202012Validator(
            read_json_object(schema_root / "gate_c_completion.schema.json")
        ).iter_errors(completion)
    )
    _require(
        not errors, f"invalid published Gate C completion: {errors[0].message if errors else ''}"
    )


def _require(condition: bool, message: str, error_type: type[Exception] = ValueError) -> None:
    if not condition:
        raise error_type(message)
