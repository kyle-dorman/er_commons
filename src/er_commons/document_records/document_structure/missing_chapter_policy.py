"""Pure source-free classification for missing whole-chapter targets."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Any, Literal

JsonObject = dict[str, Any]
DecisionStatus = Literal["eligible", "already_present", "rejected", "review_required"]
ChapterRepresentation = Literal["recovered_composite", "toc_children_fallback"]
StartOrderBasis = Literal["family_record_sequence", "global_mixed_content_index"]

_SPACE = re.compile(r"[ \t\n\r\f\v]+")
_MARKER = re.compile(r"^(?:chapter[ \t]+)?(?P<marker>[0-9]{1,2})(?=$|[ \t])", re.I)
_CHILD_MARKER = re.compile(r"^(?P<marker>[0-9]{1,2})\.[0-9]+(?=$|[. \t])")


def normalize_chapter_text(value: str) -> str:
    """Apply the canonical alias normalization subset used by this policy."""
    normalized = unicodedata.normalize("NFC", value).replace("\N{NO-BREAK SPACE}", " ")
    return _SPACE.sub(" ", normalized).strip().casefold()


@dataclass(frozen=True)
class ChapterHeadingComponent:
    """One retained source block that contributes to an observed chapter heading."""

    block_id: str
    stable_item_key: str
    raw_text: str
    physical_page: int
    sequence: int
    block_type: str = "page_header"
    content_layer: str = "furniture"
    is_toc_row: bool = False
    source_id: str = ""
    corrected_role: Literal["heading", "heading_component"] = "heading_component"
    reclassification_authorized: bool = False
    reclassification_authority: str | None = None


@dataclass(frozen=True)
class ChapterTocEvidence:
    """Accepted TOC title and any independently accepted destination pages."""

    evidence_ids: tuple[str, ...]
    raw_title: str
    accepted: bool = True
    destination_physical_pages: tuple[int, ...] = ()
    source_id: str = ""


@dataclass(frozen=True)
class ChapterBoundaryEvidence:
    """Observed next structural boundary closing a chapter extent."""

    record_id: str
    stable_item_key: str | None
    raw_text: str
    physical_page: int
    source_id: str = ""
    content_order: int | None = None
    boundary_kind: Literal["following_heading", "document_end"] = "following_heading"
    scope_start_record_id: str | None = None
    scope_start_stable_key: str | None = None
    scope_start_content_order: int | None = None


@dataclass(frozen=True)
class ChapterChildEvidence:
    """Verified source-order topology for one frozen child-section anchor."""

    section_ref: str
    source_id: str
    content_order: int
    parent_ref: str
    semantic_level: int
    extent_start_page: int
    extent_end_page: int
    heading_raw_text: str


@dataclass(frozen=True)
class EnclosingSectionEvidence:
    """Frozen facts proving an allowed intervening ancestor is unnumbered."""

    section_ref: str
    source_id: str
    stable_item_key: str
    heading_block_ref: str
    heading_raw_text: str
    content_order: int
    parent_ref: str
    semantic_level: int


@dataclass(frozen=True)
class DirectContentEvidence:
    """One in-boundary body record not owned by a selected child subtree."""

    record_id: str
    stable_item_key: str | None
    record_type: Literal["block", "table", "figure"]
    source_id: str
    content_order: int
    physical_pages: tuple[int, ...]
    original_owner_ref: str


@dataclass(frozen=True)
class _StartAnchorCandidate:
    """One permitted logical start and the meaning of its published order value."""

    record_refs: frozenset[str]
    published_content_order: int
    order_basis: StartOrderBasis


@dataclass(frozen=True)
class MissingChapterEvidence:
    """Compact accepted-record evidence for one missing whole chapter."""

    source_id: str
    chapter_marker: str
    heading_components: tuple[ChapterHeadingComponent, ...]
    toc_evidence: tuple[ChapterTocEvidence, ...]
    ordered_child_refs: tuple[str, ...]
    parent_ref: str
    semantic_level: int
    start_record_ref: str
    extent_start_page: int
    extent_end_page: int
    following_boundary: ChapterBoundaryEvidence | None
    existing_target_id: str | None = None
    unsupported_gap: bool = False
    child_topology: tuple[ChapterChildEvidence, ...] = ()
    enclosing_section_refs: tuple[str, ...] = ()
    enclosing_topology: tuple[EnclosingSectionEvidence, ...] = ()
    direct_content_topology: tuple[DirectContentEvidence, ...] = ()
    start_content_order: int | None = None


@dataclass(frozen=True)
class MissingChapterDecision:
    """One versioned classification and deterministic projection recipe."""

    status: DecisionStatus
    reason_codes: tuple[str, ...]
    source_id: str
    chapter_marker: str | None
    chapter_title: str | None
    representation: ChapterRepresentation | None
    heading_stable_keys: tuple[str, ...]
    heading_block_ids: tuple[str, ...]
    heading_raw_texts: tuple[str, ...]
    heading_physical_pages: tuple[int, ...]
    heading_components: tuple[ChapterHeadingComponent, ...]
    toc_evidence_ids: tuple[str, ...]
    destination_physical_pages: tuple[int, ...]
    ordered_child_refs: tuple[str, ...]
    child_topology: tuple[ChapterChildEvidence, ...]
    enclosing_section_refs: tuple[str, ...]
    enclosing_topology: tuple[EnclosingSectionEvidence, ...]
    direct_content_topology: tuple[DirectContentEvidence, ...]
    parent_ref: str | None
    semantic_level: int | None
    start_record_ref: str | None
    start_content_order: int | None
    extent_start_page: int | None
    extent_end_page: int | None
    following_boundary_ref: str | None
    following_boundary_stable_key: str | None
    following_boundary_raw_text: str | None
    following_boundary_page: int | None
    following_boundary_content_order: int | None
    following_boundary_kind: Literal["following_heading", "document_end"] | None = None
    following_scope_start_ref: str | None = None
    following_scope_start_stable_key: str | None = None
    following_scope_start_content_order: int | None = None

    @classmethod
    def from_record(cls, record: JsonObject) -> MissingChapterDecision:
        """Load the policy fields needed by projection from a validated record."""
        return cls(
            status=record["status"],
            reason_codes=tuple(record["reason_codes"]),
            source_id=record["source_id"],
            chapter_marker=record["chapter_marker"],
            chapter_title=record["chapter_title"],
            representation=record["representation"],
            heading_stable_keys=tuple(record["heading_stable_keys"]),
            heading_block_ids=tuple(record["heading_block_ids"]),
            heading_raw_texts=tuple(record["heading_raw_texts"]),
            heading_physical_pages=tuple(record["heading_physical_pages"]),
            heading_components=tuple(
                ChapterHeadingComponent(
                    block_id=item["block_id"],
                    stable_item_key=item["stable_item_key"],
                    raw_text=item["raw_text"],
                    physical_page=item["physical_page"],
                    sequence=item["sequence"],
                    block_type=item["block_type"],
                    content_layer=item["content_layer"],
                    is_toc_row=item["is_toc_row"],
                    source_id=item["source_id"],
                    corrected_role=item["corrected_role"],
                    reclassification_authorized=item["reclassification_authorized"],
                    reclassification_authority=item["reclassification_authority"],
                )
                for item in record["heading_components"]
            ),
            toc_evidence_ids=tuple(record["toc_evidence_ids"]),
            destination_physical_pages=tuple(record["destination_physical_pages"]),
            ordered_child_refs=tuple(record["ordered_child_refs"]),
            child_topology=tuple(
                ChapterChildEvidence(
                    section_ref=item["section_ref"],
                    source_id=item["source_id"],
                    content_order=item["content_order"],
                    parent_ref=item["parent_ref"],
                    semantic_level=item["semantic_level"],
                    extent_start_page=item["extent_start_page"],
                    extent_end_page=item["extent_end_page"],
                    heading_raw_text=item["heading_raw_text"],
                )
                for item in record["child_topology"]
            ),
            enclosing_section_refs=tuple(record["enclosing_section_refs"]),
            enclosing_topology=tuple(
                EnclosingSectionEvidence(**item) for item in record["enclosing_topology"]
            ),
            direct_content_topology=tuple(
                DirectContentEvidence(
                    record_id=item["record_id"],
                    stable_item_key=item["stable_item_key"],
                    record_type=item["record_type"],
                    source_id=item["source_id"],
                    content_order=item["content_order"],
                    physical_pages=tuple(item["physical_pages"]),
                    original_owner_ref=item["original_owner_ref"],
                )
                for item in record["direct_content_topology"]
            ),
            parent_ref=record["parent_ref"],
            semantic_level=record["semantic_level"],
            start_record_ref=record["start_record_ref"],
            start_content_order=record["start_content_order"],
            extent_start_page=record["extent_start_page"],
            extent_end_page=record["extent_end_page"],
            following_boundary_ref=record["following_boundary_ref"],
            following_boundary_stable_key=record["following_boundary_stable_key"],
            following_boundary_raw_text=record["following_boundary_raw_text"],
            following_boundary_page=record["following_boundary_page"],
            following_boundary_content_order=record["following_boundary_content_order"],
            following_boundary_kind=record.get("following_boundary_kind"),
            following_scope_start_ref=record["following_scope_start_ref"],
            following_scope_start_stable_key=record["following_scope_start_stable_key"],
            following_scope_start_content_order=record["following_scope_start_content_order"],
        )

    def as_record(
        self,
        *,
        source_ref: JsonObject,
        new_target_ref: JsonObject | None,
        human_decision_ref: JsonObject | None = None,
    ) -> JsonObject:
        """Return the closed decision and correspondence-input record."""
        inference_method = (
            None
            if self.representation is None
            else {
                "recovered_composite": "accepted_composite_heading_recovery",
                "toc_children_fallback": "accepted_toc_children_derivation",
            }[self.representation]
        )
        return {
            "schema_version": "er_commons.recovery.missing_chapter_decision.v1",
            "rule_version": "missing_whole_chapter_v1",
            "decision_kind": "missing_whole_chapter",
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "source_id": self.source_id,
            "chapter_marker": self.chapter_marker,
            "chapter_title": self.chapter_title,
            "representation": self.representation,
            "heading_stable_keys": list(self.heading_stable_keys),
            "heading_block_ids": list(self.heading_block_ids),
            "heading_raw_texts": list(self.heading_raw_texts),
            "heading_physical_pages": list(self.heading_physical_pages),
            "heading_components": [
                {
                    "block_id": item.block_id,
                    "stable_item_key": item.stable_item_key,
                    "raw_text": item.raw_text,
                    "physical_page": item.physical_page,
                    "sequence": item.sequence,
                    "block_type": item.block_type,
                    "content_layer": item.content_layer,
                    "is_toc_row": item.is_toc_row,
                    "source_id": item.source_id,
                    "corrected_role": item.corrected_role,
                    "reclassification_authorized": item.reclassification_authorized,
                    "reclassification_authority": item.reclassification_authority,
                }
                for item in self.heading_components
            ],
            "toc_evidence_ids": list(self.toc_evidence_ids),
            "destination_physical_pages": list(self.destination_physical_pages),
            "ordered_child_refs": list(self.ordered_child_refs),
            "child_topology": [
                {
                    "section_ref": item.section_ref,
                    "source_id": item.source_id,
                    "content_order": item.content_order,
                    "parent_ref": item.parent_ref,
                    "semantic_level": item.semantic_level,
                    "extent_start_page": item.extent_start_page,
                    "extent_end_page": item.extent_end_page,
                    "heading_raw_text": item.heading_raw_text,
                }
                for item in self.child_topology
            ],
            "enclosing_section_refs": list(self.enclosing_section_refs),
            "enclosing_topology": [item.__dict__ for item in self.enclosing_topology],
            "direct_content_topology": [
                {**item.__dict__, "physical_pages": list(item.physical_pages)}
                for item in self.direct_content_topology
            ],
            "parent_ref": self.parent_ref,
            "semantic_level": self.semantic_level,
            "start_record_ref": self.start_record_ref,
            "start_content_order": self.start_content_order,
            "extent_start_page": self.extent_start_page,
            "extent_end_page": self.extent_end_page,
            "following_boundary_ref": self.following_boundary_ref,
            "following_boundary_stable_key": self.following_boundary_stable_key,
            "following_boundary_raw_text": self.following_boundary_raw_text,
            "following_boundary_page": self.following_boundary_page,
            "following_boundary_content_order": self.following_boundary_content_order,
            "following_boundary_kind": self.following_boundary_kind,
            "following_scope_start_ref": self.following_scope_start_ref,
            "following_scope_start_stable_key": self.following_scope_start_stable_key,
            "following_scope_start_content_order": self.following_scope_start_content_order,
            "extent_basis": (
                "start_through_document_end"
                if self.following_boundary_kind == "document_end"
                else "start_through_before_following_boundary"
            ),
            "inference_method": inference_method,
            "source_ref": source_ref,
            "new_target_ref": new_target_ref,
            "human_decision_ref": human_decision_ref,
        }


def classify_missing_chapter(evidence: MissingChapterEvidence) -> MissingChapterDecision:
    """Classify recovered-composite or TOC-plus-children evidence without mutation."""
    base = _decision_base(evidence)
    if evidence.existing_target_id is not None:
        return replace(base, status="already_present", reason_codes=("whole_chapter_exists",))

    rejected = _common_rejections(evidence)
    if rejected:
        return replace(base, status="rejected", reason_codes=tuple(rejected))

    accepted_toc = tuple(item for item in evidence.toc_evidence if item.accepted)
    if any(item.source_id != evidence.source_id for item in accepted_toc):
        return replace(base, status="rejected", reason_codes=("cross_source_toc_evidence",))
    titles = {normalize_chapter_text(item.raw_title) for item in accepted_toc}
    if len(titles) > 1:
        return replace(base, status="review_required", reason_codes=("conflicting_toc_titles",))
    if not accepted_toc:
        return replace(base, status="rejected", reason_codes=("missing_accepted_toc_title",))
    title = accepted_toc[0].raw_title.strip()
    expected_marker = _title_marker(title)
    if expected_marker != evidence.chapter_marker:
        return replace(base, status="review_required", reason_codes=("toc_marker_conflict",))

    destinations = tuple(
        sorted({page for item in accepted_toc for page in item.destination_physical_pages})
    )
    if evidence.heading_components:
        recovery_reasons = _composite_rejections(evidence, title)
        if recovery_reasons:
            return replace(
                base,
                status="review_required",
                reason_codes=tuple(recovery_reasons),
                chapter_title=title,
                toc_evidence_ids=tuple(
                    evidence_id for item in accepted_toc for evidence_id in item.evidence_ids
                ),
                destination_physical_pages=destinations,
            )
        return replace(
            base,
            status="eligible",
            reason_codes=("observed_composite_heading_recovered",),
            chapter_title=title,
            representation="recovered_composite",
            toc_evidence_ids=tuple(
                evidence_id for item in accepted_toc for evidence_id in item.evidence_ids
            ),
            destination_physical_pages=destinations,
        )

    if destinations != (evidence.extent_start_page,):
        reason = (
            "missing_toc_body_destination" if not destinations else "conflicting_toc_destination"
        )
        status: DecisionStatus = "rejected" if not destinations else "review_required"
        return replace(
            base,
            status=status,
            reason_codes=(reason,),
            chapter_title=title,
            toc_evidence_ids=tuple(
                evidence_id for item in accepted_toc for evidence_id in item.evidence_ids
            ),
            destination_physical_pages=destinations,
        )
    return replace(
        base,
        status="eligible",
        reason_codes=("accepted_toc_and_contiguous_children_fallback",),
        chapter_title=title,
        representation="toc_children_fallback",
        toc_evidence_ids=tuple(
            evidence_id for item in accepted_toc for evidence_id in item.evidence_ids
        ),
        destination_physical_pages=destinations,
    )


def _decision_base(evidence: MissingChapterEvidence) -> MissingChapterDecision:
    boundary = evidence.following_boundary
    return MissingChapterDecision(
        status="rejected",
        reason_codes=("unclassified",),
        source_id=evidence.source_id,
        chapter_marker=evidence.chapter_marker,
        chapter_title=None,
        representation=None,
        heading_stable_keys=tuple(item.stable_item_key for item in evidence.heading_components),
        heading_block_ids=tuple(item.block_id for item in evidence.heading_components),
        heading_raw_texts=tuple(item.raw_text for item in evidence.heading_components),
        heading_physical_pages=tuple(item.physical_page for item in evidence.heading_components),
        heading_components=evidence.heading_components,
        toc_evidence_ids=tuple(
            evidence_id for item in evidence.toc_evidence for evidence_id in item.evidence_ids
        ),
        destination_physical_pages=tuple(
            sorted(
                {page for item in evidence.toc_evidence for page in item.destination_physical_pages}
            )
        ),
        ordered_child_refs=evidence.ordered_child_refs,
        child_topology=evidence.child_topology,
        enclosing_section_refs=evidence.enclosing_section_refs,
        enclosing_topology=evidence.enclosing_topology,
        direct_content_topology=evidence.direct_content_topology,
        parent_ref=evidence.parent_ref,
        semantic_level=evidence.semantic_level,
        start_record_ref=evidence.start_record_ref,
        start_content_order=evidence.start_content_order,
        extent_start_page=evidence.extent_start_page,
        extent_end_page=evidence.extent_end_page,
        following_boundary_ref=boundary.record_id if boundary else None,
        following_boundary_stable_key=boundary.stable_item_key if boundary else None,
        following_boundary_raw_text=boundary.raw_text if boundary else None,
        following_boundary_page=boundary.physical_page if boundary else None,
        following_boundary_content_order=boundary.content_order if boundary else None,
        following_boundary_kind=boundary.boundary_kind if boundary else None,
        following_scope_start_ref=boundary.scope_start_record_id if boundary else None,
        following_scope_start_stable_key=(boundary.scope_start_stable_key if boundary else None),
        following_scope_start_content_order=(
            boundary.scope_start_content_order if boundary else None
        ),
    )


def _common_rejections(evidence: MissingChapterEvidence) -> list[str]:
    reasons: list[str] = []
    if not re.fullmatch(r"[0-9]{1,2}", evidence.chapter_marker):
        reasons.append("invalid_chapter_marker")
    if not evidence.ordered_child_refs:
        reasons.append("missing_child_run")
    if len(set(evidence.ordered_child_refs)) != len(evidence.ordered_child_refs):
        reasons.append("duplicate_child_reference")
    if len(set(evidence.enclosing_section_refs)) != len(evidence.enclosing_section_refs):
        reasons.append("duplicate_enclosing_section_reference")
    if tuple(item.section_ref for item in evidence.enclosing_topology) != (
        evidence.enclosing_section_refs
    ):
        reasons.append("enclosing_topology_reference_mismatch")
    if any(item.source_id != evidence.source_id for item in evidence.enclosing_topology):
        reasons.append("cross_source_enclosing_evidence")
    if any(
        _title_marker(item.heading_raw_text) is not None
        or _child_chapter_marker(item.heading_raw_text) is not None
        for item in evidence.enclosing_topology
    ):
        reasons.append("numbered_enclosing_section")
    direct_keys = tuple(
        item.stable_item_key
        for item in evidence.direct_content_topology
        if item.stable_item_key is not None
    )
    direct_ids = tuple(item.record_id for item in evidence.direct_content_topology)
    direct_orders = tuple(item.content_order for item in evidence.direct_content_topology)
    if len(set(direct_keys)) != len(direct_keys) or len(set(direct_ids)) != len(direct_ids):
        reasons.append("duplicate_direct_content_evidence")
    if direct_orders != tuple(sorted(direct_orders)) or len(set(direct_orders)) != len(
        direct_orders
    ):
        reasons.append("direct_content_order_invalid")
    if any(
        item.source_id != evidence.source_id
        or not item.physical_pages
        or item.physical_pages != tuple(sorted(set(item.physical_pages)))
        or min(item.physical_pages) < evidence.extent_start_page
        or max(item.physical_pages) > evidence.extent_end_page
        for item in evidence.direct_content_topology
    ):
        reasons.append("direct_content_scope_invalid")
    if not evidence.child_topology:
        reasons.append("missing_verified_child_topology")
    else:
        child_refs = tuple(item.section_ref for item in evidence.child_topology)
        if child_refs != evidence.ordered_child_refs:
            reasons.append("child_topology_reference_mismatch")
        if any(item.source_id != evidence.source_id for item in evidence.child_topology):
            reasons.append("cross_source_child_evidence")
        orders = tuple(item.content_order for item in evidence.child_topology)
        if orders != tuple(sorted(orders)) or len(set(orders)) != len(orders):
            reasons.append("noncontiguous_children")
        if any(item.semantic_level <= evidence.semantic_level for item in evidence.child_topology):
            reasons.append("invalid_child_level")
        if any(
            _child_chapter_marker(item.heading_raw_text) != evidence.chapter_marker
            for item in evidence.child_topology
        ):
            reasons.append("child_chapter_marker_mismatch")
        if (
            min(item.extent_start_page for item in evidence.child_topology)
            < evidence.extent_start_page
        ):
            reasons.append("child_extent_before_chapter")
        if max(item.extent_end_page for item in evidence.child_topology) > evidence.extent_end_page:
            reasons.append("child_extent_after_chapter")
    if evidence.unsupported_gap:
        reasons.append("unsupported_gap")
    if evidence.extent_start_page > evidence.extent_end_page:
        reasons.append("invalid_extent")
    boundary = evidence.following_boundary
    if boundary is None:
        reasons.append("missing_following_boundary")
    elif boundary.source_id != evidence.source_id:
        reasons.append("cross_source_boundary_evidence")
    elif boundary.boundary_kind == "following_heading" and (
        any(
            item is not None
            for item in (
                boundary.scope_start_record_id,
                boundary.scope_start_stable_key,
                boundary.scope_start_content_order,
            )
        )
        and (boundary.scope_start_record_id is None or boundary.scope_start_content_order is None)
    ):
        reasons.append("incomplete_scope_boundary_evidence")
    elif (
        boundary.boundary_kind == "following_heading"
        and boundary.physical_page < evidence.extent_end_page
    ):
        reasons.append("boundary_before_extent_end")
    elif (
        boundary.boundary_kind == "following_heading"
        and boundary.physical_page == evidence.extent_end_page
        and (
            boundary.content_order is None
            or boundary.content_order
            <= max(
                (
                    *(item.content_order for item in evidence.child_topology),
                    *(item.sequence for item in evidence.heading_components),
                ),
                default=-1,
            )
        )
    ):
        reasons.append("boundary_not_after_chapter_anchors")
    elif boundary.boundary_kind == "document_end" and (
        boundary.stable_item_key is not None
        or boundary.raw_text != "document end"
        or boundary.physical_page != evidence.extent_end_page
        or boundary.content_order is None
        or boundary.content_order
        <= max(
            (
                *(item.content_order for item in evidence.child_topology),
                *(item.sequence for item in evidence.heading_components),
            ),
            default=-1,
        )
        or boundary.scope_start_record_id is not None
        or boundary.scope_start_stable_key is not None
        or boundary.scope_start_content_order is not None
    ):
        reasons.append("invalid_document_end_boundary")
    if evidence.semantic_level <= 0 or evidence.semantic_level > 6:
        reasons.append("invalid_semantic_level")
    if not evidence.parent_ref or not evidence.start_record_ref:
        reasons.append("missing_parent_or_start")
    start_candidates = _start_anchor_candidates(evidence)
    matching_starts = [
        item for item in start_candidates if evidence.start_record_ref in item.record_refs
    ]
    if len(matching_starts) != 1 or (
        matching_starts
        and evidence.start_content_order != matching_starts[0].published_content_order
    ):
        reasons.append("start_anchor_mismatch")
    return reasons


def _start_anchor_candidates(evidence: MissingChapterEvidence) -> tuple[_StartAnchorCandidate, ...]:
    """Name whether each permitted start order is a family sequence or mixed index."""
    candidates: list[_StartAnchorCandidate] = []
    if evidence.heading_components:
        first_heading = evidence.heading_components[0]
        candidates.append(
            _StartAnchorCandidate(
                frozenset({first_heading.stable_item_key}),
                first_heading.sequence,
                "family_record_sequence",
            )
        )
    if evidence.child_topology:
        first_child = evidence.child_topology[0]
        candidates.append(
            _StartAnchorCandidate(
                frozenset({first_child.section_ref}),
                first_child.content_order,
                "family_record_sequence",
            )
        )
    if evidence.heading_components and evidence.direct_content_topology:
        first_direct = evidence.direct_content_topology[0]
        refs = {first_direct.record_id}
        if first_direct.stable_item_key is not None:
            refs.add(first_direct.stable_item_key)
        candidates.append(
            _StartAnchorCandidate(
                frozenset(refs),
                first_direct.content_order,
                "global_mixed_content_index",
            )
        )
    return tuple(candidates)


def _composite_rejections(evidence: MissingChapterEvidence, toc_title: str) -> list[str]:
    components = evidence.heading_components
    reasons: list[str] = []
    if any(item.source_id != evidence.source_id for item in components):
        reasons.append("cross_source_heading_evidence")
    if any(item.corrected_role not in {"heading", "heading_component"} for item in components):
        reasons.append("heading_component_role_not_accepted")
    if components[0].corrected_role != "heading" or any(
        item.corrected_role != "heading_component" for item in components[1:]
    ):
        reasons.append("heading_component_roles_not_ordered")

    def requires_reclassification(item: ChapterHeadingComponent) -> bool:
        return item.content_layer == "furniture" or item.block_type == "page_header"

    if any(
        requires_reclassification(item) and not item.reclassification_authorized
        for item in components
    ):
        reasons.append("furniture_reclassification_not_authorized")
    if any(
        requires_reclassification(item)
        and item.reclassification_authority
        != "missing_whole_chapter_v1_observed_heading_reclassification"
        for item in components
    ):
        reasons.append("reclassification_authority_missing")
    if any(item.is_toc_row for item in components):
        reasons.append("toc_block_cannot_be_body_heading")
    if len({item.physical_page for item in components}) != 1:
        reasons.append("composite_components_cross_pages")
    if components[0].physical_page != evidence.extent_start_page:
        reasons.append("composite_heading_not_at_start")
    sequences = [item.sequence for item in components]
    if len(components) > 1 and sequences != list(
        range(sequences[0], sequences[0] + len(sequences))
    ):
        reasons.append("nonadjacent_composite_components")
    observed_title = normalize_chapter_text(" ".join(item.raw_text for item in components))
    if observed_title != normalize_chapter_text(toc_title):
        reasons.append("composite_title_disagrees_with_toc")
    if _title_marker(observed_title) != evidence.chapter_marker:
        reasons.append("composite_marker_conflict")
    return reasons


def _title_marker(value: str) -> str | None:
    match = _MARKER.match(normalize_chapter_text(value))
    return match.group("marker") if match is not None else None


def _child_chapter_marker(value: str) -> str | None:
    match = _CHILD_MARKER.match(normalize_chapter_text(value))
    return match.group("marker") if match is not None else None
