"""Reconstruct and compare accepted Task 06F FC1 semantics before relinking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.document_records.document_references.figure_aliases import (
    ALIAS_ORIGIN,
    FigureAliasValidationInputs,
    build_caption_figure_aliases,
    require_equal,
)
from er_commons.document_records.document_references.relinking_config import (
    AcceptedFc1Evidence,
)
from er_commons.document_records.document_references.storage import read_jsonl
from er_commons.document_records.document_references.types import JsonObject

EXPECTED_COUNTS = {
    "candidate_figure_count": 274,
    "eligible_figure_count": 178,
    "rejected_figure_count": 96,
    "review_required_figure_count": 0,
    "alias_count": 178,
    "target_edge_count": 178,
    "one_target_alias_count": 178,
    "multiple_target_alias_count": 0,
    "unique_alias_count": 178,
    "ambiguous_alias_count": 0,
    "collision_group_count": 0,
}


@dataclass(frozen=True)
class AcceptedFc1Packet:
    """Verified small Task 06F evidence retained for prelink comparison."""

    selection: AcceptedFc1Evidence
    identity: JsonObject
    qualification: JsonObject
    aliases: tuple[JsonObject, ...]
    entries: tuple[JsonObject, ...]


def load_accepted_fc1_packet(
    selection: AcceptedFc1Evidence, *, resolved_paths: dict[str, Path]
) -> AcceptedFc1Packet:
    """Verify accepted packet closure after authority refs resolved their seals."""
    required = {
        "completion",
        "inventory",
        "identity",
        "qualification",
        "figure_aliases",
        "target_index_entries",
    }
    if set(resolved_paths) != required:
        raise ValueError("accepted FC1 resolved path roles differ")
    completion = _object(resolved_paths["completion"])
    inventory = _object(resolved_paths["inventory"])
    identity = _object(resolved_paths["identity"])
    qualification = _object(resolved_paths["qualification"])
    aliases = tuple(read_jsonl(resolved_paths["figure_aliases"]))
    entries = tuple(read_jsonl(resolved_paths["target_index_entries"]))
    if completion != {
        "completion_last": True,
        "inventory_sha256": selection.inventory_ref.sha256,
        "pdf_or_image_payload_hashed": False,
        "qualification_id": selection.qualification_id,
        "schema_version": "er_commons.figure_caption_qualification_completion.v1",
        "source_pdf_accessed": False,
        "status": "complete",
    }:
        raise ValueError("accepted FC1 completion differs")
    expected_inventory = {
        "identity.json": selection.identity_ref,
        "qualification.json": selection.qualification_ref,
        "figure_aliases.jsonl": selection.figure_aliases_ref,
        "target_index_entries.jsonl": selection.target_index_entries_ref,
    }
    rows = inventory.get("files")
    if (
        inventory.get("schema_version") != "er_commons.figure_caption_qualification_inventory.v1"
        or inventory.get("qualification_id") != selection.qualification_id
        or not isinstance(rows, list)
        or len(rows) != len(expected_inventory)
    ):
        raise ValueError("accepted FC1 inventory closure differs")
    observed = {str(row.get("path")): row for row in rows if isinstance(row, dict)}
    if set(observed) != set(expected_inventory):
        raise ValueError("accepted FC1 inventory managed files differ")
    for name, reference in expected_inventory.items():
        row = observed[name]
        if row.get("sha256") != reference.sha256 or row.get("byte_size") != reference.byte_size:
            raise ValueError(f"accepted FC1 inventory seal differs: {name}")
    if (
        identity.get("qualification_id") != selection.qualification_id
        or identity.get("source_id") != selection.source_id
        or qualification.get("source_id") != selection.source_id
    ):
        raise ValueError("accepted FC1 identity/source binding differs")
    _require_frozen_counts(qualification, aliases=aliases, entries=entries)
    return AcceptedFc1Packet(selection, identity, qualification, aliases, entries)


def build_fc1_rebuilt_equivalence(
    *,
    packet: AcceptedFc1Packet,
    inputs: FigureAliasValidationInputs,
    base_structured_candidate_id: str,
    correspondence_ref: JsonObject,
) -> JsonObject:
    """Require exact accepted/rebuilt FC1 meaning under declared namespace mapping."""
    if inputs.source_id != "deir_main" or packet.selection.source_id != "deir_main":
        raise ValueError("FC1 rebuilt equivalence is main-only")
    old_upstream = packet.identity.get("upstream_candidate_id")
    old_qualified = packet.selection.qualification_id
    if not isinstance(old_upstream, str) or not old_upstream.startswith("exv1-"):
        raise ValueError("accepted FC1 upstream namespace differs")
    if correspondence_ref.get("path", "").split("/")[-1] != "missing_chapter_correspondence.json":
        raise ValueError("FC1 rebuilt equivalence lacks accepted main correspondence")

    rebuilt = build_caption_figure_aliases(inputs=inputs, first_sequence=1)
    rebuilt_aliases = list(rebuilt.aliases)
    rebuilt_entries = [row.as_json() for row in rebuilt.entries]
    _require_frozen_counts(
        rebuilt.qualification, aliases=tuple(rebuilt_aliases), entries=tuple(rebuilt_entries)
    )
    prefixes = (old_qualified, old_upstream)
    accepted_qualification = _map_namespaces(packet.qualification, prefixes, inputs.candidate_id)
    accepted_aliases = _map_namespaces(list(packet.aliases), prefixes, inputs.candidate_id)
    accepted_entries = _map_namespaces(list(packet.entries), prefixes, inputs.candidate_id)
    require_equal(
        label="FC1 rebuilt qualification",
        observed=rebuilt.qualification,
        expected=accepted_qualification,
    )
    require_equal(label="FC1 rebuilt aliases", observed=rebuilt_aliases, expected=accepted_aliases)
    require_equal(
        label="FC1 rebuilt target-index entries",
        observed=rebuilt_entries,
        expected=accepted_entries,
    )
    if any(str(row.get("lookup_key")) == "figure 4.8" for row in rebuilt_entries):
        raise ValueError("FC1 rebuilt evidence unexpectedly contains Figure 4.8")

    accepted_digest = canonical_json_sha256(
        {
            "qualification": accepted_qualification,
            "aliases": accepted_aliases,
            "entries": accepted_entries,
        }
    )
    rebuilt_digest = canonical_json_sha256(
        {
            "qualification": rebuilt.qualification,
            "aliases": rebuilt_aliases,
            "entries": rebuilt_entries,
        }
    )
    preimage: JsonObject = {
        "schema_version": "er_commons.fc1_rebuilt_equivalence.v1",
        "status": "passed",
        "source_id": "deir_main",
        "accepted_qualification_id": packet.selection.qualification_id,
        "accepted_packet_refs": packet.selection.model_dump(mode="json"),
        "accepted_upstream_candidate_id": old_upstream,
        "base_structured_candidate_id": base_structured_candidate_id,
        "rebuilt_structured_candidate_id": inputs.candidate_id,
        "correspondence_ref": correspondence_ref,
        "namespace_mapping_policy": "declared_main_correspondence_entity_tail_v1",
        "accepted_semantic_sha256": accepted_digest,
        "rebuilt_semantic_sha256": rebuilt_digest,
        "candidate_figure_count": 274,
        "eligible_figure_count": 178,
        "rejected_figure_count": 96,
        "review_required_figure_count": 0,
        "alias_count": 178,
        "target_edge_count": 178,
        "figure_4_8_absent": True,
    }
    return {**preimage, "equivalence_sha256": canonical_json_sha256(preimage)}


def _require_frozen_counts(
    qualification: JsonObject,
    *,
    aliases: tuple[JsonObject, ...],
    entries: tuple[JsonObject, ...],
) -> None:
    """Reject count drift before semantic comparison can claim equivalence."""
    for field, expected in EXPECTED_COUNTS.items():
        if qualification.get(field) != expected:
            raise ValueError(
                f"FC1 {field} differs: expected={expected}; observed={qualification.get(field)!r}"
            )
    if len(aliases) != 178 or len(entries) != 178:
        raise ValueError("FC1 alias/target row counts differ")
    if any(row.get("alias_origin") != ALIAS_ORIGIN for row in (*aliases, *entries)):
        raise ValueError("FC1 packet contains a non-FC1 row")


def _map_namespaces(value: Any, prefixes: tuple[str, str], target: str) -> Any:
    """Map extraction-qualified IDs only, preserving every semantic scalar."""
    if isinstance(value, str):
        for prefix in prefixes:
            if value == prefix or value.startswith(f"{prefix}/"):
                return f"{target}{value[len(prefix) :]}"
        return value
    if isinstance(value, list):
        return [_map_namespaces(item, prefixes, target) for item in value]
    if isinstance(value, dict):
        return {key: _map_namespaces(item, prefixes, target) for key, item in value.items()}
    return value


def _object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


__all__ = [
    "AcceptedFc1Packet",
    "build_fc1_rebuilt_equivalence",
    "load_accepted_fc1_packet",
]
