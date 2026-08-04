"""Responsibility-owned validation for the human-readable candidate build."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.cross_reference_enrichment.construction import CandidateBuild
from er_commons.cross_reference_enrichment.indexing import NamespaceRemapper
from er_commons.cross_reference_enrichment.policy import (
    ELIGIBLE_BLOCK_TYPES,
    TABLE_LABEL_PATTERN,
    TABLE_PAGE_WINDOW,
    is_qualified_external_table_reference,
)
from er_commons.cross_reference_enrichment.resolution import TARGET_TYPE_FOR_MENTION
from er_commons.cross_reference_enrichment.storage import read_jsonl
from er_commons.cross_reference_enrichment.types import JsonObject, MentionKind


def validate_candidate_build(
    *,
    build: CandidateBuild,
    upstream_root: Path,
    upstream_candidate_id: str,
    candidate_id: str,
    schema_path: Path,
    identity_extension: JsonObject,
) -> None:
    """Sequence shape, provenance, graph-closure, and preservation policies."""
    schema = json.loads(schema_path.read_bytes())
    _validate_shapes(build, schema, identity_extension)
    _validate_cross_reference_policy(build)
    _validate_alias_correspondence(build, upstream_root)
    _validate_target_index(build, upstream_root, upstream_candidate_id, candidate_id)
    _validate_support(build, upstream_root, upstream_candidate_id, candidate_id)
    _validate_preserved_records(
        build,
        upstream_root=upstream_root,
        remapper=NamespaceRemapper(upstream_candidate_id, candidate_id),
    )


def validate_serialized_terminal_records(root: Path, schema_path: Path) -> None:
    """Validate manifest extension and completion after completion-last writing."""
    schema = json.loads(schema_path.read_bytes())
    manifest = json.loads((root / "records" / "manifest.json").read_bytes())
    completion = json.loads((root / "records" / "completion_record.json").read_bytes())
    _definition_validator(schema, "manifest_extension").validate(
        manifest["cross_reference_extension"]
    )
    _definition_validator(schema, "completion").validate(completion)


def _validate_shapes(
    build: CandidateBuild, schema: JsonObject, identity_extension: JsonObject
) -> None:
    for alias in build.target_aliases:
        _definition_validator(schema, "canonical_target_alias").validate(alias)
    for mention in build.cross_references:
        _definition_validator(schema, "cross_reference").validate(mention)
    support_definitions = {
        "cross_reference_target_index": "target_index_support",
        "cross_reference_summary": "summary_support",
        "cross_reference_preservation": "preservation_support",
    }
    for role, definition in support_definitions.items():
        _definition_validator(schema, definition).validate(build.support[role])
    _definition_validator(schema, "identity_extension").validate(identity_extension)


def _validate_cross_reference_policy(build: CandidateBuild) -> None:
    """Validate source, resolution, target, and evidence policy cross-record."""
    blocks = {
        block["id"]: block for block in build.preserved_record_files["canonical/blocks.jsonl"]
    }
    aliases = {alias["id"]: alias for alias in build.target_aliases}
    entries = build.support["cross_reference_target_index"]["entries"]
    index_by_alias: dict[str, list[JsonObject]] = {}
    for entry in entries:
        index_by_alias.setdefault(entry["alias_record_id"], []).append(entry)
    indexed_alias_targets = {
        (entry["alias_record_id"], entry["target_record_id"]) for entry in entries
    }
    targets = {
        record["id"]: record
        for path in (
            "canonical/documents.jsonl",
            "canonical/pages.jsonl",
            "canonical/sections.jsonl",
            "canonical/tables.jsonl",
            "canonical/figures.jsonl",
        )
        for record in build.preserved_record_files[path]
    }
    pages = {
        page["id"]: page["physical_page_number"]
        for page in build.preserved_record_files["canonical/pages.jsonl"]
    }
    previous_order: tuple[int, int, int] | None = None
    for expected_sequence, mention in enumerate(build.cross_references, start=1):
        _require(mention["sequence"] == expected_sequence, "mention sequence is contiguous")
        source = blocks.get(mention["source_record_id"])
        _require(source is not None, "mention source exists")
        assert source is not None
        _require(_eligible_source(source), "mention source is eligible")
        expected_checksum = source.get("canonical_text_sha256")
        if expected_checksum is not None:
            _require(
                hashlib.sha256(source["canonical_text"].encode()).hexdigest() == expected_checksum,
                "mention source checksum is stable",
            )
        start, end = mention["source_charspan"]
        _require(
            source["canonical_text"][start:end] == mention["raw_text"],
            "mention span reproduces canonical text",
        )
        _require(mention["regions"] == source["regions"], "mention inherits all regions")
        _require(mention["raw_links"] == source["raw_links"], "mention inherits raw links")
        order = (source["sequence"], start, end)
        _require(
            previous_order is None or previous_order < order,
            "mention order follows source order",
        )
        previous_order = order
        candidates = mention["candidates"]
        expected_status = (
            "unresolved" if not candidates else "resolved" if len(candidates) == 1 else "ambiguous"
        )
        _require(
            mention["resolution_status"] == expected_status,
            "mention status matches candidates",
        )
        _require(
            (expected_status == "unresolved") == (mention["unresolved_reason"] is not None),
            "mention unresolved reason matches status",
        )
        target_ids = [candidate["target_record_id"] for candidate in candidates]
        _require(len(target_ids) == len(set(target_ids)), "candidate targets are deduplicated")
        for candidate in candidates:
            _require(
                candidate["target_record_id"] in targets,
                "candidate target remains in the v3 namespace",
            )
            _require(
                candidate["target_type"]
                == TARGET_TYPE_FOR_MENTION[MentionKind(mention["mention_class"])],
                "candidate target type matches mention class",
            )
            alias_ids = candidate["alias_record_ids"]
            _require(bool(alias_ids), "candidate has alias evidence")
            _require(
                all(alias_id in aliases and alias_id in index_by_alias for alias_id in alias_ids),
                "candidate aliases remain in the v3 namespace",
            )
            for alias_id in alias_ids:
                _require(
                    (alias_id, candidate["target_record_id"]) in indexed_alias_targets,
                    "candidate is present in target index",
                )
            evidence_entries = [
                matching[0]
                for alias_id in alias_ids
                if (
                    matching := [
                        entry
                        for entry in index_by_alias[alias_id]
                        if entry["target_record_id"] == candidate["target_record_id"]
                    ]
                )
            ]
            _require(
                len(evidence_entries) == len(alias_ids),
                "candidate has one target-index row per alias",
            )
            _require(
                all(
                    entry["alias_origin"] == candidate["alias_origin"]
                    and entry["upstream_target_record_id"] == candidate["upstream_target_record_id"]
                    for entry in evidence_entries
                ),
                "candidate correspondence matches target index",
            )
            _require(
                candidate["upstream_alias_record_ids"]
                == [
                    entry["upstream_alias_record_id"]
                    for entry in evidence_entries
                    if entry["upstream_alias_record_id"] is not None
                ],
                "candidate upstream aliases match target index",
            )
        if mention["mention_class"] == "table":
            _validate_table_resolution(mention, source, entries, pages)

    _validate_derived_table_aliases(build, blocks, targets)


def _validate_table_resolution(
    mention: JsonObject,
    source: JsonObject,
    entries: list[JsonObject],
    pages: dict[str, int],
) -> None:
    start, end = mention["source_charspan"]
    source_page = pages[source["regions"][0]["page_id"]]
    qualified = is_qualified_external_table_reference(source["canonical_text"][end:])
    matching = [
        entry
        for entry in entries
        if entry["lookup_key"] == mention["lookup_key"] and entry["target_type"] == "table"
    ]
    eligible_distances: dict[str, int] = {}
    for entry in matching:
        evidence_page_id = entry.get("evidence_page_id")
        if evidence_page_id is None:
            continue
        distance = abs(source_page - pages[evidence_page_id])
        if distance <= TABLE_PAGE_WINDOW:
            eligible_distances[entry["target_record_id"]] = distance
    candidates = mention["candidates"]
    expected_targets = set() if qualified else set(eligible_distances)
    _require(
        {candidate["target_record_id"] for candidate in candidates} == expected_targets,
        "table candidates match the verified five-page target window",
    )
    for candidate in candidates:
        _require(
            candidate.get("page_distance") == eligible_distances[candidate["target_record_id"]],
            "table candidate page distance matches evidence",
        )
    if not candidates:
        expected_reason = (
            "qualified_external_table_reference"
            if qualified
            else "outside_table_page_window"
            if matching
            else "no_local_alias"
        )
        _require(
            mention["unresolved_reason"] == expected_reason,
            "table unresolved reason matches target evidence",
        )


def _validate_derived_table_aliases(
    build: CandidateBuild,
    blocks: dict[str, JsonObject],
    targets: dict[str, JsonObject],
) -> None:
    entries = build.support["cross_reference_target_index"]["entries"]
    derived = [entry for entry in entries if entry["alias_origin"] != "upstream_v2"]
    for entry in derived:
        block = blocks.get(entry["evidence_source_record_id"])
        target = targets.get(entry["target_record_id"])
        _require(block is not None and target is not None, "derived table evidence exists")
        assert block is not None and target is not None
        page_id = entry["evidence_page_id"]
        same_page_tables = [
            record
            for record in build.preserved_record_files["canonical/tables.jsonl"]
            if record["document_id"] == target["document_id"]
            and page_id in _record_page_ids(record)
        ]
        labels = [
            candidate
            for candidate in blocks.values()
            if _eligible_source(candidate)
            and TABLE_LABEL_PATTERN.fullmatch(candidate["canonical_text"].casefold())
            and candidate["document_id"] == target["document_id"]
            and set(_record_page_ids(candidate)) == {page_id}
        ]
        _require(
            entry["target_type"] == "table"
            and entry["evidence_kind"] == "verified_same_page_table_label"
            and entry["upstream_alias_record_id"] is None
            and block["canonical_text"].casefold() == entry["lookup_key"]
            and len(same_page_tables) == 1
            and same_page_tables[0]["id"] == target["id"]
            and [label["id"] for label in labels] == [block["id"]],
            "derived table alias has exact same-page single-table evidence",
        )


def _validate_alias_correspondence(build: CandidateBuild, upstream_root: Path) -> None:
    upstream_aliases = read_jsonl(upstream_root / "canonical" / "target_aliases.jsonl")
    preserved = [alias for alias in build.target_aliases if alias["alias_origin"] == "upstream_v2"]
    _require(len(upstream_aliases) == len(preserved), "all upstream aliases survive")
    _require(
        {alias["id"] for alias in upstream_aliases}
        == {alias["upstream_alias_id"] for alias in preserved},
        "alias correspondence is exact and bidirectional",
    )


def _validate_target_index(
    build: CandidateBuild,
    upstream_root: Path,
    upstream_candidate_id: str,
    candidate_id: str,
) -> None:
    """Require the support index to exactly represent canonical alias evidence."""
    entries = build.support["cross_reference_target_index"]["entries"]
    serialized_rows = [
        json.dumps(entry, sort_keys=True, separators=(",", ":")) for entry in entries
    ]
    _require(
        len(serialized_rows) == len(set(serialized_rows)),
        "target index contains duplicate exact alias-target rows",
    )
    aliases = _unique_index(build.target_aliases, "id", "canonical aliases")
    indexed_alias_ids = [entry["alias_record_id"] for entry in entries]
    _require(set(indexed_alias_ids) == set(aliases), "canonical aliases and target index match")

    upstream_aliases = read_jsonl(upstream_root / "canonical/target_aliases.jsonl")
    expected_upstream_rows = {
        (
            alias["normalized_alias"],
            alias["id"],
            target["target_id"],
            target["target_type"],
        )
        for alias in upstream_aliases
        for target in alias["targets"]
    }
    observed_upstream_rows = {
        (
            entry["lookup_key"],
            entry["upstream_alias_record_id"],
            entry["upstream_target_record_id"],
            entry["target_type"],
        )
        for entry in entries
        if entry["alias_origin"] == "upstream_v2"
    }
    _require(
        observed_upstream_rows == expected_upstream_rows,
        "target index matches all upstream alias evidence",
    )

    remapper = NamespaceRemapper(upstream_candidate_id, candidate_id)
    for entry in entries:
        alias = aliases[entry["alias_record_id"]]
        _require(alias["alias_origin"] == entry["alias_origin"], "alias origin matches index")
        _require(
            alias["upstream_alias_id"] == entry["upstream_alias_record_id"],
            "alias correspondence matches index",
        )
        matching_targets = [
            target
            for target in alias["targets"]
            if target["target_id"] == entry["target_record_id"]
            and target["target_type"] == entry["target_type"]
            and target["upstream_target_id"] == entry["upstream_target_record_id"]
        ]
        _require(
            len(matching_targets) == 1,
            "canonical alias target matches index",
        )
        if entry["alias_origin"] == "upstream_v2":
            _require(
                alias["id"] == remapper.record_id(entry["upstream_alias_record_id"]),
                "upstream alias ID is namespace-remapped exactly",
            )
            _require(
                entry["target_record_id"] == remapper.record_id(entry["upstream_target_record_id"]),
                "upstream alias target is namespace-remapped exactly",
            )
        else:
            _require(
                alias["normalized_alias"] == entry["lookup_key"],
                "derived alias lookup key matches index",
            )


def _validate_support(
    build: CandidateBuild,
    upstream_root: Path,
    upstream_candidate_id: str,
    candidate_id: str,
) -> None:
    _require(
        set(build.support)
        == {
            "cross_reference_target_index",
            "cross_reference_summary",
            "cross_reference_preservation",
        },
        "support roles are exact",
    )
    index = build.support["cross_reference_target_index"]
    summary = build.support["cross_reference_summary"]
    preservation = build.support["cross_reference_preservation"]
    upstream_count = len(read_jsonl(upstream_root / "canonical/target_aliases.jsonl"))
    derived_count = sum(alias["alias_origin"] != "upstream_v2" for alias in build.target_aliases)
    _require(index["upstream_alias_count"] == upstream_count, "target-index upstream count matches")
    _require(index["derived_table_alias_count"] == derived_count, "derived table count matches")
    _require(index["derived_figure_alias_count"] == 0, "derived figure aliases are forbidden")
    eligible_count = sum(
        _eligible_source(block) for block in build.preserved_record_files["canonical/blocks.jsonl"]
    )
    _require(summary["eligible_source_count"] == eligible_count, "eligible-source count matches")
    _require(
        summary["mention_counts"]
        == dict(sorted(Counter(item["mention_class"] for item in build.cross_references).items())),
        "mention counts match",
    )
    _require(
        summary["status_counts"]
        == dict(
            sorted(Counter(item["resolution_status"] for item in build.cross_references).items())
        ),
        "status counts match",
    )
    _require(
        summary["unresolved_reason_counts"]
        == dict(
            sorted(
                Counter(
                    item["unresolved_reason"]
                    for item in build.cross_references
                    if item["unresolved_reason"] is not None
                ).items()
            )
        ),
        "unresolved-reason counts match",
    )
    _require(
        preservation["upstream_candidate_id"] == upstream_candidate_id
        and preservation["upstream_alias_count"] == upstream_count
        and preservation["derived_table_alias_count"] == derived_count
        and preservation["derived_figure_alias_count"] == 0
        and preservation["bidirectional_alias_correspondence_complete"] is True
        and preservation["undeclared_difference_count"] == 0
        and preservation["status"] == "passed",
        "preservation support matches validated evidence",
    )
    _require(
        all(mention["extraction_id"] == candidate_id for mention in build.cross_references),
        "mention extraction identities match candidate",
    )


def _validate_preserved_records(
    build: CandidateBuild, *, upstream_root: Path, remapper: NamespaceRemapper
) -> None:
    for path, observed in build.preserved_record_files.items():
        expected = [remapper.value(record) for record in read_jsonl(upstream_root / path)]
        _require(observed == expected, f"preserved semantics differ for {path}")


def _definition_validator(schema: JsonObject, name: str) -> Draft202012Validator:
    return Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{name}"})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _eligible_source(record: JsonObject) -> bool:
    return (
        record.get("content_layer") == "body"
        and record.get("is_toc_row") is False
        and record.get("block_type") in ELIGIBLE_BLOCK_TYPES
    )


def _record_page_ids(record: JsonObject) -> list[str]:
    if "page_ids" in record:
        return list(record["page_ids"])
    return [region["page_id"] for region in record.get("regions", [])]


def _unique_index(records: list[JsonObject], field: str, label: str) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for record in records:
        key = record.get(field)
        _require(isinstance(key, str) and key not in result, f"{label} {field} is unique")
        assert isinstance(key, str)
        result[key] = record
    return result
