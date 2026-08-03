"""Cross-record validation for the schema-v3 cross-reference contract.

This module validates persisted shapes against independently supplied upstream
alias, label-block, and table/figure evidence. It does not detect mentions,
construct indexes, resolve candidates, or publish artifacts.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, cast

from er_commons.cross_reference_contract.errors import CrossReferenceContractError

type JsonObject = dict[str, Any]

ELIGIBLE_TYPES = {"caption", "footnote", "list_item", "paragraph"}
TARGET_TYPES_BY_MENTION = {
    "section": {"section"},
    "appendix": {"section"},
    "table": {"table"},
    "figure": {"figure"},
    "printed_page": {"page"},
    "document": {"document"},
}
SUPPORT_PATH_BY_ROLE = {
    "cross_reference_target_index": "support/cross_reference_target_index.json",
    "cross_reference_summary": "support/cross_reference_summary.json",
    "cross_reference_preservation": "support/cross_reference_preservation.json",
}
TABLE_LABEL_PATTERN = re.compile(r"table [1-9][0-9]*(?:[.-][a-z0-9]+)*")
QUALIFIED_EXTERNAL_TABLE_PATTERN = re.compile(
    r"^\s+(?:in|from|of)\s+reference\s+[1-9][0-9]*\b", re.IGNORECASE
)
TABLE_PAGE_WINDOW = 5


def _as_objects(value: Any, field: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise CrossReferenceContractError(f"{field} is not an object list")
    return cast(list[JsonObject], value)


def _object_index(records: Sequence[JsonObject], field: str, label: str) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for record in records:
        key = record.get(field)
        if not isinstance(key, str) or key in result:
            raise CrossReferenceContractError(f"{label} has a missing or duplicate {field}")
        result[key] = record
    return result


def _eligible_source(record: Mapping[str, Any]) -> bool:
    return (
        record.get("content_layer") == "body"
        and record.get("is_toc_row") is False
        and record.get("block_type") in ELIGIBLE_TYPES
    )


def _validate_source_checksums(records: Sequence[JsonObject], label: str) -> None:
    for record in records:
        text = record.get("canonical_text")
        expected = record.get("canonical_text_sha256")
        if not isinstance(text, str) or hashlib.sha256(text.encode()).hexdigest() != expected:
            raise CrossReferenceContractError(f"{label} source checksum drifted")


def _alias_evidence_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("lookup_key"),
        record.get("alias_record_id"),
        record.get("target_record_id"),
        record.get("target_type"),
    )


def _index_upstream_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("lookup_key"),
        record.get("upstream_alias_record_id"),
        record.get("upstream_target_record_id"),
        record.get("target_type"),
    )


def validate_cross_reference_contract(
    bundle: JsonObject,
    *,
    upstream_alias_evidence: Sequence[JsonObject],
    target_evidence_blocks: Sequence[JsonObject],
    target_records: Sequence[JsonObject],
    physical_page_numbers: Mapping[str, int],
) -> None:
    """Validate a v3 contract bundle against independent accepted evidence."""
    persisted_upstream = _as_objects(bundle.get("upstream_alias_evidence"), "upstream aliases")
    persisted_target_blocks = _as_objects(
        bundle.get("target_evidence_blocks"), "target evidence blocks"
    )
    persisted_target_records = _as_objects(bundle.get("target_records"), "target records")
    if persisted_upstream != list(upstream_alias_evidence):
        raise CrossReferenceContractError(
            "persisted upstream aliases differ from external evidence"
        )
    if persisted_target_blocks != list(target_evidence_blocks):
        raise CrossReferenceContractError("persisted target blocks differ from external evidence")
    if persisted_target_records != list(target_records):
        raise CrossReferenceContractError("persisted target records differ from external evidence")

    sources = _object_index(
        _as_objects(bundle.get("source_blocks"), "source blocks"), "id", "source"
    )
    evidence_blocks = _object_index(target_evidence_blocks, "id", "target evidence")
    targets = _object_index(target_records, "id", "target record")
    _validate_source_checksums(list(sources.values()), "mention")
    _validate_source_checksums(list(evidence_blocks.values()), "target")

    index_entries = _as_objects(bundle.get("target_index"), "target index")
    index_keys = {
        (entry["lookup_key"], entry["alias_record_id"], entry["target_record_id"])
        for entry in index_entries
    }
    index_by_alias = _object_index(index_entries, "alias_record_id", "target index")
    expected_upstream = {_alias_evidence_key(item) for item in upstream_alias_evidence}
    actual_upstream = {
        _index_upstream_key(item)
        for item in index_entries
        if item.get("alias_origin") == "upstream_v2"
    }
    if actual_upstream != expected_upstream:
        raise CrossReferenceContractError("target index differs from external upstream aliases")

    canonical_aliases = _as_objects(bundle.get("canonical_target_aliases"), "canonical aliases")
    canonical_by_id = _object_index(canonical_aliases, "id", "canonical alias")
    if set(canonical_by_id) != set(index_by_alias):
        raise CrossReferenceContractError("canonical aliases and target index differ")
    for alias_id, entry in index_by_alias.items():
        alias = canonical_by_id[alias_id]
        if alias.get("alias_origin") != entry.get("alias_origin") or alias.get(
            "upstream_alias_id"
        ) != entry.get("upstream_alias_record_id"):
            raise CrossReferenceContractError("canonical alias differs from target index")
        alias_targets = _as_objects(alias.get("targets"), "canonical alias targets")
        if len(alias_targets) != 1 or (
            alias_targets[0].get("target_id") != entry.get("target_record_id")
            or alias_targets[0].get("upstream_target_id") != entry.get("upstream_target_record_id")
        ):
            raise CrossReferenceContractError("canonical alias target differs from target index")
        if entry.get("alias_origin") == "v3_verified_table_label" and alias.get(
            "normalized_alias"
        ) != entry.get("lookup_key"):
            raise CrossReferenceContractError("derived canonical alias differs from target index")

    order: list[tuple[int, int, int]] = []
    cross_references = _as_objects(bundle.get("cross_references"), "cross references")
    for expected_sequence, mention in enumerate(cross_references, start=1):
        if mention.get("sequence") != expected_sequence:
            raise CrossReferenceContractError("mention sequence is not contiguous")
        source_id = mention.get("source_record_id")
        source = sources.get(source_id) if isinstance(source_id, str) else None
        if source is None:
            raise CrossReferenceContractError("mention source is absent from external evidence")
        if not _eligible_source(source):
            raise CrossReferenceContractError("mention escaped source eligibility")

        span = mention.get("source_charspan")
        if not isinstance(span, list) or len(span) != 2:
            raise CrossReferenceContractError("mention span is malformed")
        start, end = span
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or start >= end
            or source["canonical_text"][start:end] != mention.get("raw_text")
        ):
            raise CrossReferenceContractError("mention span does not reproduce source text")
        if mention.get("regions") != source.get("regions"):
            raise CrossReferenceContractError("mention regions are not complete inherited evidence")
        if mention.get("raw_links") != source.get("raw_links"):
            raise CrossReferenceContractError(
                "mention raw links are not complete inherited evidence"
            )

        order.append((cast(int, source["sequence"]), start, end))
        candidates = _as_objects(mention.get("candidates"), "mention candidates")
        expected_status = (
            "unresolved" if not candidates else "resolved" if len(candidates) == 1 else "ambiguous"
        )
        if mention.get("resolution_status") != expected_status:
            raise CrossReferenceContractError("mention status disagrees with candidate count")
        if (expected_status == "unresolved") != (mention.get("unresolved_reason") is not None):
            raise CrossReferenceContractError("mention unresolved reason disagrees with status")

        candidate_target_ids = [candidate.get("target_record_id") for candidate in candidates]
        if len(candidate_target_ids) != len(set(candidate_target_ids)):
            raise CrossReferenceContractError("candidate targets were not deduplicated")
        for candidate in candidates:
            mention_class = mention.get("mention_class")
            if (
                mention_class not in TARGET_TYPES_BY_MENTION
                or candidate.get("target_type") not in TARGET_TYPES_BY_MENTION[mention_class]
            ):
                raise CrossReferenceContractError(
                    "candidate target type disagrees with mention class"
                )
            alias_ids = candidate.get("alias_record_ids")
            if not isinstance(alias_ids, list) or not alias_ids:
                raise CrossReferenceContractError("candidate has no alias evidence")
            for alias_id in alias_ids:
                key = (mention.get("lookup_key"), alias_id, candidate.get("target_record_id"))
                if key not in index_keys:
                    raise CrossReferenceContractError(
                        "candidate is absent from external target index"
                    )
            evidence_entries = [index_by_alias[alias_id] for alias_id in alias_ids]
            if any(
                entry.get("alias_origin") != candidate.get("alias_origin")
                or entry.get("upstream_target_record_id")
                != candidate.get("upstream_target_record_id")
                for entry in evidence_entries
            ):
                raise CrossReferenceContractError(
                    "candidate correspondence differs from target index"
                )
            upstream_aliases = [
                entry["upstream_alias_record_id"]
                for entry in evidence_entries
                if entry.get("upstream_alias_record_id") is not None
            ]
            if candidate.get("upstream_alias_record_ids") != upstream_aliases:
                raise CrossReferenceContractError(
                    "candidate upstream aliases differ from target index"
                )

        if mention.get("mention_class") == "table":
            source_page_ids = {
                region.get("page_id")
                for region in _as_objects(source.get("regions"), "source regions")
            }
            try:
                source_pages = [
                    physical_page_numbers[cast(str, page_id)] for page_id in source_page_ids
                ]
            except KeyError as error:
                raise CrossReferenceContractError(
                    "table mention page is absent from external page evidence"
                ) from error

            is_qualified_external = bool(
                QUALIFIED_EXTERNAL_TABLE_PATTERN.match(source["canonical_text"][end:])
            )
            eligible_distances: dict[str, int] = {}
            matching_alias_exists = False
            for entry in index_entries:
                if (
                    entry.get("lookup_key") != mention.get("lookup_key")
                    or entry.get("target_type") != "table"
                ):
                    continue
                matching_alias_exists = True
                target_id = entry.get("target_record_id")
                target = targets.get(target_id) if isinstance(target_id, str) else None
                if target is None:
                    raise CrossReferenceContractError(
                        "table alias target is absent from external target evidence"
                    )
                try:
                    target_pages = [
                        physical_page_numbers[page_id] for page_id in target.get("page_ids", [])
                    ]
                except KeyError as error:
                    raise CrossReferenceContractError(
                        "table target page is absent from external page evidence"
                    ) from error
                distance = min(
                    abs(source_page - target_page)
                    for source_page in source_pages
                    for target_page in target_pages
                )
                if distance <= TABLE_PAGE_WINDOW:
                    eligible_distances[cast(str, target_id)] = distance

            expected_target_ids = set() if is_qualified_external else set(eligible_distances)
            if set(candidate_target_ids) != expected_target_ids:
                raise CrossReferenceContractError(
                    "table candidates disagree with the five-page target window"
                )
            for candidate in candidates:
                if candidate.get("page_distance") != eligible_distances.get(
                    cast(str, candidate.get("target_record_id"))
                ):
                    raise CrossReferenceContractError("table candidate page distance disagrees")
            if not candidates:
                expected_reason = (
                    "qualified_external_table_reference"
                    if is_qualified_external
                    else "outside_table_page_window"
                    if matching_alias_exists
                    else "accepted_target_type_unavailable"
                )
                if mention.get("unresolved_reason") != expected_reason:
                    raise CrossReferenceContractError(
                        "table unresolved reason disagrees with window outcome"
                    )

    if order != sorted(order):
        raise CrossReferenceContractError("mentions are not in deterministic source order")

    derived_tables = [
        entry for entry in index_entries if entry.get("alias_origin") != "upstream_v2"
    ]
    for entry in derived_tables:
        evidence_id = entry.get("evidence_source_record_id")
        target_id = entry.get("target_record_id")
        evidence_block = evidence_blocks.get(evidence_id) if isinstance(evidence_id, str) else None
        target = targets.get(target_id) if isinstance(target_id, str) else None
        same_page_table_count = (
            sum(
                record.get("target_type") == "table"
                and record.get("document_id") == target.get("document_id")
                and entry.get("evidence_page_id") in record.get("page_ids", [])
                for record in targets.values()
            )
            if target is not None
            else 0
        )
        labels_for_target = [
            candidate
            for candidate in derived_tables
            if candidate.get("target_record_id") == entry.get("target_record_id")
        ]
        numbered_labels_on_page = (
            [
                record
                for record in evidence_blocks.values()
                if _eligible_source(record)
                and TABLE_LABEL_PATTERN.fullmatch(record.get("canonical_text", "").casefold())
                and record.get("document_id") == target.get("document_id")
                and {region["page_id"] for region in record.get("regions", [])}
                == {entry.get("evidence_page_id")}
            ]
            if target is not None
            else []
        )
        if not (
            entry.get("target_type") == "table"
            and entry.get("evidence_kind") == "verified_same_page_table_label"
            and entry.get("upstream_alias_record_id") is None
            and evidence_block is not None
            and target is not None
            and _eligible_source(evidence_block)
            and TABLE_LABEL_PATTERN.fullmatch(evidence_block.get("canonical_text", "").casefold())
            and evidence_block.get("canonical_text", "").casefold() == entry.get("lookup_key")
            and evidence_block.get("document_id") == target.get("document_id")
            and {region["page_id"] for region in evidence_block.get("regions", [])}
            == {entry.get("evidence_page_id")}
            and entry.get("evidence_page_id") in target.get("page_ids", [])
            and target.get("upstream_target_record_id") == entry.get("upstream_target_record_id")
            and same_page_table_count == 1
            and len(labels_for_target) == 1
            and [record.get("id") for record in numbered_labels_on_page]
            == [evidence_block.get("id")]
        ):
            raise CrossReferenceContractError(
                "derived table alias lacks exact target-side evidence"
            )

    support_files = _as_objects(bundle.get("support_files"), "support files")
    support_roles = [item.get("role") for item in support_files]
    if set(support_roles) != set(SUPPORT_PATH_BY_ROLE) or len(support_roles) != 3:
        raise CrossReferenceContractError("support roles are not exact")
    for item in support_files:
        if item.get("path") != SUPPORT_PATH_BY_ROLE[item["role"]]:
            raise CrossReferenceContractError("support role has the wrong canonical path")

    target_support = cast(JsonObject, bundle["target_index_support"])
    if target_support.get("entries") != index_entries:
        raise CrossReferenceContractError("target-index support differs from external index")
    if target_support.get("upstream_alias_count") != len(upstream_alias_evidence):
        raise CrossReferenceContractError("upstream alias count disagrees with evidence")
    if target_support.get("derived_table_alias_count") != len(derived_tables):
        raise CrossReferenceContractError("derived table-alias count disagrees with index")
    if target_support.get("derived_figure_alias_count") != 0:
        raise CrossReferenceContractError("derived figure aliases are forbidden in v3")

    summary = cast(JsonObject, bundle["summary_support"])
    if summary.get("eligible_source_count") != len(sources):
        raise CrossReferenceContractError("summary eligible-source count disagrees")
    if summary.get("mention_counts") != dict(
        Counter(mention["mention_class"] for mention in cross_references)
    ):
        raise CrossReferenceContractError("summary mention counts disagree")
    if summary.get("status_counts") != dict(
        Counter(mention["resolution_status"] for mention in cross_references)
    ):
        raise CrossReferenceContractError("summary status counts disagree")
    if summary.get("unresolved_reason_counts") != dict(
        Counter(
            mention["unresolved_reason"]
            for mention in cross_references
            if mention.get("unresolved_reason") is not None
        )
    ):
        raise CrossReferenceContractError("summary unresolved-reason counts disagree")

    preservation = cast(JsonObject, bundle["preservation_support"])
    if (
        preservation.get("upstream_alias_count") != len(upstream_alias_evidence)
        or preservation.get("derived_table_alias_count") != len(derived_tables)
        or preservation.get("derived_figure_alias_count") != 0
    ):
        raise CrossReferenceContractError("preservation counts disagree with evidence")

    manifest = cast(JsonObject, bundle["manifest_extension"])
    if (
        manifest.get("cross_reference_count") != len(cross_references)
        or manifest.get("preserved_alias_count") != len(upstream_alias_evidence)
        or manifest.get("derived_table_alias_count") != len(derived_tables)
        or manifest.get("derived_figure_alias_count") != 0
        or manifest.get("support_files") != support_files
    ):
        raise CrossReferenceContractError("manifest extension counts or support files disagree")

    identity = cast(JsonObject, bundle["identity_extension"])
    completion = cast(JsonObject, bundle["completion"])
    extraction_ids = {mention.get("extraction_id") for mention in cross_references}
    if len(extraction_ids) != 1 or completion.get("extraction_id") not in extraction_ids:
        raise CrossReferenceContractError("completion extraction identity disagrees with mentions")
    if identity.get("upstream_candidate_id") != preservation.get("upstream_candidate_id"):
        raise CrossReferenceContractError("identity upstream candidate disagrees with preservation")

    if bundle.get("fixture_scope") == "full_candidate" and len(upstream_alias_evidence) != 323:
        raise CrossReferenceContractError(
            "full candidate does not preserve all 323 upstream aliases"
        )
