"""Derive exact figure aliases from canonical attachment evidence only."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from er_commons.document_records.document_references.exact_resolution import (
    normalize_exact_text,
)
from er_commons.document_records.document_references.indexing import NamespaceRemapper
from er_commons.document_records.document_references.types import JsonObject, TargetIndexEntry

POLICY_ID = "figure_caption_alias_v1"
ALIAS_ORIGIN = "linking_v2_fc1_body_figure_caption"
EVIDENCE_KIND = "attached_body_figure_caption"
TEXT_ONLY_STATUS = "not_evaluated_pending_task06h"

# The lookahead requires at least one digit. Greedy dot/hyphen components consume
# the complete identifier before the delimiter assertion is evaluated.
_LEADING_MARKER = re.compile(
    r"^(?P<marker>figure[\t ]+(?P<identifier>(?=[a-z0-9.-]*\d)[a-z0-9]+(?:[.-][a-z0-9]+)*))"
    r"[\t ]*:",
    re.IGNORECASE | re.ASCII,
)
_FIGURE_TOKEN = re.compile(r"figure[\t ]+", re.IGNORECASE | re.ASCII)


@dataclass(frozen=True)
class FigureAliasBuild:
    """Aliases, index entries, and closed qualification evidence for all figures."""

    aliases: tuple[JsonObject, ...]
    entries: tuple[TargetIndexEntry, ...]
    qualification: JsonObject


@dataclass(frozen=True)
class FigureAliasValidationInputs:
    """Canonical inputs needed to revalidate FC1 without source payload access."""

    upstream_candidate_id: str
    candidate_id: str
    source_id: str
    source_document_id: str
    upstream_figures: Sequence[JsonObject]
    upstream_images: Sequence[JsonObject]
    upstream_blocks: Sequence[JsonObject]
    upstream_pages: Sequence[JsonObject]


@dataclass(frozen=True)
class _EligibleFigure:
    figure: JsonObject
    image: JsonObject
    caption: JsonObject
    marker: str
    normalized_marker: str
    page_id: str
    physical_page_number: int
    repeated_caption_reference_count: int
    repeated_image_reference_count: int


def build_caption_figure_aliases(
    *,
    inputs: FigureAliasValidationInputs,
    first_sequence: int,
) -> FigureAliasBuild:
    """Qualify every canonical figure and publish grouped exact marker aliases."""
    upstream_candidate_id = inputs.upstream_candidate_id
    candidate_id = inputs.candidate_id
    source_id = inputs.source_id
    source_document_id = inputs.source_document_id
    remapper = NamespaceRemapper(upstream_candidate_id, candidate_id)
    expected_document_id = f"{upstream_candidate_id}/document/{source_id}"
    if source_document_id != expected_document_id:
        raise ValueError("FC1 source document does not match candidate/source namespace")
    images = _unique_records(inputs.upstream_images, family="image")
    blocks = _unique_records(inputs.upstream_blocks, family="block")
    figures = _unique_records(inputs.upstream_figures, family="figure")
    pages = _unique_records(inputs.upstream_pages, family="page")
    caption_owner_counts = Counter(
        str(caption_id)
        for figure in figures.values()
        for caption_id in set(figure.get("caption_block_ids", []))
    )
    image_owner_counts = Counter(
        str(image_id)
        for figure in figures.values()
        for image_id in set(figure.get("image_ids", []))
    )
    decisions: list[JsonObject] = []
    eligible: list[_EligibleFigure] = []
    for figure in sorted(figures.values(), key=_record_order):
        result, decision = _qualify_figure(
            figure=figure,
            images=images,
            blocks=blocks,
            remapper=remapper,
            caption_owner_counts=caption_owner_counts,
            image_owner_counts=image_owner_counts,
            pages=pages,
            upstream_candidate_id=upstream_candidate_id,
            source_id=source_id,
            source_document_id=source_document_id,
        )
        decisions.append(decision)
        if result is not None:
            eligible.append(result)

    grouped: dict[str, list[_EligibleFigure]] = defaultdict(list)
    for item in eligible:
        grouped[item.normalized_marker].append(item)

    aliases: list[JsonObject] = []
    entries: list[TargetIndexEntry] = []
    for normalized_marker, group in sorted(grouped.items()):
        by_target = {str(item.figure["id"]): item for item in group}
        ordered = sorted(by_target.values(), key=lambda item: _record_order(item.figure))
        alias_id = (
            f"{candidate_id}/target-alias/{source_id}/alias{first_sequence + len(aliases):06d}"
        )
        targets = [_target_provenance(item=item, remapper=remapper) for item in ordered]
        alias: JsonObject = {
            "id": alias_id,
            "document_id": remapper.record_id(str(ordered[0].figure["document_id"])),
            "sequence": first_sequence + len(aliases),
            "alias_kind": "figure",
            "raw_values": sorted(
                {item.marker for item in ordered}, key=lambda value: (value.casefold(), value)
            ),
            "normalized_alias": normalized_marker,
            "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
            "resolution_status": "unique" if len(targets) == 1 else "ambiguous",
            "alias_origin": ALIAS_ORIGIN,
            "upstream_alias_id": None,
            "targets": targets,
        }
        aliases.append(alias)
        for item, target in zip(ordered, targets, strict=True):
            entries.append(
                TargetIndexEntry(
                    lookup_key=normalized_marker,
                    target_type="figure",
                    alias_origin=ALIAS_ORIGIN,
                    alias_record_id=alias_id,
                    target_record_id=str(target["target_id"]),
                    upstream_alias_record_id=None,
                    upstream_target_record_id=str(target["upstream_target_id"]),
                    evidence_kind=EVIDENCE_KIND,
                    evidence_source_record_id=remapper.record_id(str(item.caption["id"])),
                    evidence_page_id=remapper.record_id(item.page_id),
                )
            )

    reason_counts = Counter(
        str(decision["reason"]) for decision in decisions if decision["eligibility"] != "eligible"
    )
    qualification: JsonObject = {
        "schema_version": "er_commons.figure_caption_alias_qualification.v1",
        "policy_id": POLICY_ID,
        "source_id": source_id,
        "candidate_figure_count": len(decisions),
        "eligible_figure_count": len(eligible),
        "rejected_figure_count": sum(
            decision["eligibility"] == "rejected" for decision in decisions
        ),
        "review_required_figure_count": sum(
            decision["eligibility"] == "review_required" for decision in decisions
        ),
        "alias_count": len(aliases),
        "zero_target_figure_count": len(decisions) - len(eligible),
        "rejection_reason_counts": dict(sorted(reason_counts.items())),
        "structural_target_status": "evaluated",
        "text_only_evidence_status": TEXT_ONLY_STATUS,
        "decisions": decisions,
    }
    qualification = with_effective_figure_accounting(
        qualification,
        entries=[entry.as_json() for entry in entries],
        fc1_entries=[entry.as_json() for entry in entries],
    )
    return FigureAliasBuild(tuple(aliases), tuple(entries), qualification)


def parse_leading_figure_marker(value: str) -> tuple[str, str] | None:
    """Return the complete leading marker and normalized exact lookup key."""
    match = _LEADING_MARKER.match(value.strip())
    if match is None:
        return None
    marker = match.group("marker")
    return marker, normalize_exact_text(marker)


def validate_caption_figure_alias_evidence(
    *,
    aliases: list[JsonObject] | tuple[JsonObject, ...],
    entries: list[JsonObject] | tuple[JsonObject, ...],
    qualification: JsonObject,
    inputs: FigureAliasValidationInputs,
) -> None:
    """Reconstruct FC1 evidence and reject provenance or accounting drift."""
    fc1_aliases = [row for row in aliases if row.get("alias_origin") == ALIAS_ORIGIN]
    first_sequence = min((int(row["sequence"]) for row in fc1_aliases), default=1)
    expected = build_caption_figure_aliases(
        inputs=inputs,
        first_sequence=first_sequence,
    )
    require_equal(
        label="FC1 aliases",
        observed=fc1_aliases,
        expected=list(expected.aliases),
    )
    fc1_entries = [row for row in entries if row.get("alias_origin") == ALIAS_ORIGIN]
    expected_entries = [row.as_json() for row in expected.entries]
    require_equal(
        label="FC1 target-index entries",
        observed=fc1_entries,
        expected=expected_entries,
    )
    expected_qualification = with_effective_figure_accounting(
        expected.qualification,
        entries=entries,
        fc1_entries=expected_entries,
    )
    require_equal(
        label="FC1 qualification",
        observed=qualification,
        expected=expected_qualification,
    )


def with_effective_figure_accounting(
    qualification: JsonObject,
    *,
    entries: Sequence[JsonObject],
    fc1_entries: Sequence[JsonObject],
) -> JsonObject:
    """Overlay FC1 counts after unioning existing and derived figure targets."""
    fc1_keys = {str(row.get("lookup_key", "")) for row in fc1_entries}
    targets_by_key: dict[str, set[str]] = {key: set() for key in fc1_keys}
    for row in entries:
        key = str(row.get("lookup_key", ""))
        if row.get("target_type") == "figure" and key in targets_by_key:
            targets_by_key[key].add(str(row.get("target_record_id", "")))
    one = sum(len(targets) == 1 for targets in targets_by_key.values())
    multiple = sum(len(targets) > 1 for targets in targets_by_key.values())
    return {
        **qualification,
        "target_edge_count": sum(len(targets) for targets in targets_by_key.values()),
        "one_target_alias_count": one,
        "multiple_target_alias_count": multiple,
        "collision_group_count": multiple,
        "unique_alias_count": one,
        "ambiguous_alias_count": multiple,
    }


def require_equal(*, label: str, observed: object, expected: object) -> None:
    """Raise one bounded diagnostic for the first semantic difference."""
    difference = _first_difference(expected, observed)
    if difference is None:
        return
    path, expected_value, observed_value = difference
    raise ValueError(
        f"{label} differs at {path}: expected={_bounded_repr(expected_value)}; "
        f"observed={_bounded_repr(observed_value)}"
    )


def _first_difference(
    expected: object, observed: object, *, path: str = "$"
) -> tuple[str, object, object] | None:
    """Find one deterministic field or sequence difference."""
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        expected_keys = set(expected)
        observed_keys = set(observed)
        if missing := sorted(expected_keys - observed_keys, key=str):
            key = missing[0]
            return f"{path}.{key}", expected[key], "<missing>"
        if extra := sorted(observed_keys - expected_keys, key=str):
            key = extra[0]
            return f"{path}.{key}", "<missing>", observed[key]
        for key in sorted(expected_keys, key=str):
            difference = _first_difference(expected[key], observed[key], path=f"{path}.{key}")
            if difference is not None:
                return difference
        return None
    if (
        isinstance(expected, Sequence)
        and not isinstance(expected, (str, bytes))
        and isinstance(observed, Sequence)
        and not isinstance(observed, (str, bytes))
    ):
        shared_length = min(len(expected), len(observed))
        for index in range(shared_length):
            record_id = _diagnostic_record_id(expected[index], observed[index])
            suffix = f"[{index}]" + (f"(record={record_id})" if record_id else "")
            difference = _first_difference(expected[index], observed[index], path=f"{path}{suffix}")
            if difference is not None:
                return difference
        if len(expected) != len(observed):
            index = shared_length
            expected_value = expected[index] if index < len(expected) else "<missing>"
            observed_value = observed[index] if index < len(observed) else "<missing>"
            record_id = _diagnostic_record_id(expected_value, observed_value)
            suffix = f"[{index}]" + (f"(record={record_id})" if record_id else "")
            return f"{path}{suffix}", expected_value, observed_value
        return None
    if expected != observed:
        return path, expected, observed
    return None


def _diagnostic_record_id(expected: object, observed: object) -> str | None:
    """Choose a useful stable identity for one compared record."""
    for value in (expected, observed):
        if not isinstance(value, Mapping):
            continue
        for key in ("id", "alias_record_id", "figure_id", "lookup_key"):
            candidate = value.get(key)
            if candidate not in (None, ""):
                return str(candidate)
    return None


def _bounded_repr(value: object, *, limit: int = 240) -> str:
    """Keep verification failures readable even when values are large."""
    rendered = repr(value)
    return rendered if len(rendered) <= limit else f"{rendered[: limit - 3]}..."


def _qualify_figure(
    *,
    figure: JsonObject,
    images: dict[str, JsonObject],
    blocks: dict[str, JsonObject],
    remapper: NamespaceRemapper,
    caption_owner_counts: Counter[str],
    image_owner_counts: Counter[str],
    pages: dict[str, JsonObject],
    upstream_candidate_id: str,
    source_id: str,
    source_document_id: str,
) -> tuple[_EligibleFigure | None, JsonObject]:
    """Apply closed attachment, classification, page, and marker checks."""
    figure_id = str(figure["id"])
    caption_refs = [str(value) for value in figure.get("caption_block_ids", [])]
    image_refs = [str(value) for value in figure.get("image_ids", [])]
    distinct_captions = tuple(dict.fromkeys(caption_refs))
    distinct_images = tuple(dict.fromkeys(image_refs))
    base: JsonObject = {
        "figure_id": remapper.record_id(figure_id),
        "upstream_figure_id": figure_id,
        "eligibility": "rejected",
        "reason": None,
        "caption_block_ids": [remapper.record_id(value) for value in distinct_captions],
        "image_ids": [remapper.record_id(value) for value in distinct_images],
        "repeated_caption_reference_count": len(caption_refs) - len(distinct_captions),
        "repeated_image_reference_count": len(image_refs) - len(distinct_images),
        "structural_target_status": "rejected",
        "text_only_evidence_status": TEXT_ONLY_STATUS,
    }
    if not _belongs_to_namespace(figure_id, upstream_candidate_id, "figure", source_id):
        return None, _rejected(base, "wrong_figure_record_family")
    if figure.get("document_id") != source_document_id:
        return None, _rejected(base, "figure_document_identity_mismatch")
    if figure.get("extraction_id") != upstream_candidate_id:
        return None, _rejected(base, "figure_extraction_identity_mismatch")
    if figure.get("content_layer") != "body":
        return None, _rejected(base, "figure_not_body")
    if figure.get("is_toc_row") is not False:
        return None, _rejected(base, "figure_toc_or_unclassified")
    if figure.get("semantic_placement") != "inherited_nontext":
        return None, _rejected(base, "figure_semantic_placement_unqualified")
    if len(distinct_captions) != 1:
        if distinct_captions:
            return None, _rejected(base, "multiple_captions", review_required=True)
        return None, _rejected(base, "missing_caption")
    if len(distinct_images) != 1:
        if distinct_images:
            return None, _rejected(base, "multiple_images", review_required=True)
        return None, _rejected(base, "missing_image")
    if not _belongs_to_namespace(distinct_captions[0], upstream_candidate_id, "block", source_id):
        return None, _rejected(base, "caption_attachment_wrong_record_family")
    if not _belongs_to_namespace(distinct_images[0], upstream_candidate_id, "image", source_id):
        return None, _rejected(base, "image_attachment_wrong_record_family")
    if caption_owner_counts[distinct_captions[0]] != 1:
        return None, _rejected(base, "caption_attached_to_multiple_figures")
    if image_owner_counts[distinct_images[0]] != 1:
        return None, _rejected(base, "image_attached_to_multiple_figures")
    caption = blocks.get(distinct_captions[0])
    image = images.get(distinct_images[0])
    if caption is None:
        return None, _rejected(base, "dangling_caption_attachment")
    if image is None:
        return None, _rejected(base, "dangling_image_attachment")
    document_id = figure.get("document_id")
    scoped_records = (figure, caption, image)
    if any(record.get("extraction_id") != upstream_candidate_id for record in scoped_records):
        return None, _rejected(base, "attachment_extraction_identity_mismatch")
    if caption.get("document_id") != document_id or image.get("document_id") != document_id:
        return None, _rejected(base, "cross_document_attachment")
    if caption.get("section_id") != figure.get("section_id"):
        return None, _rejected(base, "cross_section_attachment")
    if caption.get("block_type") != "caption":
        return None, _rejected(base, "attached_block_not_caption")
    if caption.get("content_layer") != "body":
        return None, _rejected(base, "caption_not_body")
    if caption.get("is_toc_row") is not False:
        return None, _rejected(base, "caption_toc_or_unclassified")
    page_ids = (
        _page_ids(figure),
        _page_ids(image),
        _page_ids(caption),
    )
    if any(len(value) != 1 for value in page_ids):
        return None, _rejected(base, "attachment_page_cardinality_unqualified")
    if len(set(page_ids)) != 1:
        return None, _rejected(base, "attachment_page_mismatch")
    page = pages.get(page_ids[0][0])
    if page is None:
        return None, _rejected(base, "dangling_page_attachment")
    if not _belongs_to_namespace(str(page.get("id", "")), upstream_candidate_id, "page", source_id):
        return None, _rejected(base, "page_record_namespace_mismatch")
    if page.get("document_id") != document_id or document_id != source_document_id:
        return None, _rejected(base, "cross_document_page_attachment")
    if page.get("extraction_id") != upstream_candidate_id:
        return None, _rejected(base, "page_extraction_identity_mismatch")
    parsed = parse_leading_figure_marker(str(caption.get("canonical_text", "")))
    if parsed is None:
        caption_text = str(caption.get("canonical_text", "")).strip()
        later_marker = _FIGURE_TOKEN.search(caption_text)
        reason = (
            "figure_marker_not_leading"
            if later_marker is not None and later_marker.start() > 0
            else "leading_figure_marker_absent_or_invalid"
        )
        return None, _rejected(base, reason)
    marker, normalized_marker = parsed
    base.update(
        {
            "eligibility": "eligible",
            "reason": "eligible_attached_body_caption",
            "page_id": remapper.record_id(page_ids[0][0]),
            "physical_page_number": int(page["physical_page_number"]),
            "raw_marker": marker,
            "normalized_alias": normalized_marker,
            "caption_text": str(caption["canonical_text"]),
            "classification": {
                "figure_content_layer": "body",
                "figure_is_toc_row": False,
                "figure_semantic_placement": "inherited_nontext",
                "caption_block_type": "caption",
                "caption_content_layer": "body",
                "caption_is_toc_row": False,
                "same_section": True,
            },
            "structural_target_status": "eligible",
        }
    )
    return (
        _EligibleFigure(
            figure=figure,
            image=image,
            caption=caption,
            marker=marker,
            normalized_marker=normalized_marker,
            page_id=page_ids[0][0],
            physical_page_number=int(page["physical_page_number"]),
            repeated_caption_reference_count=len(caption_refs) - len(distinct_captions),
            repeated_image_reference_count=len(image_refs) - len(distinct_images),
        ),
        base,
    )


def _target_provenance(*, item: _EligibleFigure, remapper: NamespaceRemapper) -> JsonObject:
    """Serialize the complete canonical attachment evidence for one target."""
    return {
        "target_id": remapper.record_id(str(item.figure["id"])),
        "target_type": "figure",
        "upstream_target_id": item.figure["id"],
        "evidence_kind": EVIDENCE_KIND,
        "evidence_source_record_id": remapper.record_id(str(item.caption["id"])),
        "evidence_page_id": remapper.record_id(item.page_id),
        "evidence_physical_page_number": item.physical_page_number,
        "evidence_image_record_ids": [remapper.record_id(str(item.image["id"]))],
        "attachment_provenance": {
            "caption_block_ids": [remapper.record_id(str(item.caption["id"]))],
            "image_ids": [remapper.record_id(str(item.image["id"]))],
            "repeated_caption_reference_count": item.repeated_caption_reference_count,
            "repeated_image_reference_count": item.repeated_image_reference_count,
        },
        "classification_provenance": {
            "figure_content_layer": "body",
            "figure_is_toc_row": False,
            "figure_semantic_placement": "inherited_nontext",
            "figure_section_id": remapper.record_id(str(item.figure["section_id"])),
            "caption_section_id": remapper.record_id(str(item.caption["section_id"])),
            "caption_block_type": "caption",
            "caption_content_layer": "body",
            "caption_is_toc_row": False,
        },
        "structural_target_status": "eligible",
        "text_only_evidence_status": TEXT_ONLY_STATUS,
    }


def _unique_records(records: Sequence[JsonObject], *, family: str) -> dict[str, JsonObject]:
    """Index canonical records and reject contradictory duplicate identities."""
    indexed: dict[str, JsonObject] = {}
    for record in records:
        record_id = str(record.get("id", ""))
        if not record_id:
            raise ValueError(f"{family} record lacks an ID")
        previous = indexed.setdefault(record_id, record)
        if previous != record:
            raise ValueError(f"contradictory duplicate {family} record: {record_id}")
    return indexed


def _record_order(record: JsonObject) -> tuple[int, str]:
    """Use canonical sequence with record ID as a deterministic tie breaker."""
    return int(record.get("sequence", 0)), str(record["id"])


def _page_ids(record: JsonObject) -> tuple[str, ...]:
    """Return distinct attached pages without interpreting geometry."""
    return tuple(
        dict.fromkeys(str(region.get("page_id", "")) for region in record.get("regions", []))
    )


def _belongs_to_namespace(record_id: str, candidate_id: str, family: str, source_id: str) -> bool:
    """Require the exact candidate, family, and source namespace."""
    return record_id.startswith(f"{candidate_id}/{family}/{source_id}/")


def _rejected(base: JsonObject, reason: str, *, review_required: bool = False) -> JsonObject:
    if review_required:
        base["eligibility"] = "review_required"
        base["structural_target_status"] = "review_required"
    base["reason"] = reason
    return base


__all__ = [
    "ALIAS_ORIGIN",
    "EVIDENCE_KIND",
    "POLICY_ID",
    "FigureAliasBuild",
    "FigureAliasValidationInputs",
    "build_caption_figure_aliases",
    "parse_leading_figure_marker",
    "require_equal",
    "validate_caption_figure_alias_evidence",
    "with_effective_figure_accounting",
]
