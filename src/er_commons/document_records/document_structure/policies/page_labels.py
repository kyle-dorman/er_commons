"""Physical-page coverage and printed-label resolution policies."""

from __future__ import annotations

from dataclasses import dataclass

from er_commons.document_records.document_structure.bundle import (
    DocumentStructureBundleView,
    JsonObject,
)
from er_commons.document_records.document_structure.errors import StructureContractError


@dataclass(frozen=True)
class ExpectedResolution:
    """The only valid canonical outcome for one page's source evidence."""

    state: str
    value: str | None
    basis: str | None


def validate_page_labels(view: DocumentStructureBundleView) -> None:
    """Require one evidence-consistent label outcome for every accepted page."""
    accepted_page_count = view.bundle["control_provenance"]["physical_page_count"]
    if view.bundle["expected_page_count"] != accepted_page_count:
        raise StructureContractError(
            "page-label coverage differs from the accepted control: "
            f"expected {accepted_page_count}, got {view.bundle['expected_page_count']}"
        )

    expected_pages = list(range(1, accepted_page_count + 1))
    actual_pages = [item["physical_page_number"] for item in view.page_labels]
    if actual_pages != expected_pages:
        raise StructureContractError(
            "page-label outcomes are not a complete physical-page sequence"
        )

    for observation in view.page_labels:
        _validate_evidence_states(observation)
        _validate_resolution(observation)


def _validate_evidence_states(observation: JsonObject) -> None:
    """Keep evidence state, value, and source anchors internally coherent."""
    physical_page = observation["physical_page_number"]
    explicit = observation["explicit_pdf_label"]
    visible = observation["visible_label"]

    _validate_evidence_value(physical_page, "explicit", explicit)
    _validate_evidence_value(physical_page, "visible", visible)
    if explicit["state"] == "absent" and explicit["value"] is not None:
        raise StructureContractError(
            f"absent explicit page label has a value on physical page {physical_page}"
        )
    if visible["state"] == "absent" and (visible["value"] is not None or visible["evidence_refs"]):
        raise StructureContractError(
            f"absent visible page label has evidence on physical page {physical_page}"
        )
    if observation["synthesized_default_rejected"] is not True:
        raise StructureContractError(
            f"library-synthesized page default was not rejected on physical page {physical_page}"
        )


def _validate_evidence_value(
    physical_page: int,
    source: str,
    evidence: JsonObject,
) -> None:
    """Require present or conflicting evidence to retain source anchors."""
    if evidence["state"] != "absent" and not evidence["evidence_refs"]:
        raise StructureContractError(
            f"{source} page-label evidence has no source anchors on physical page {physical_page}"
        )
    if evidence["state"] == "present" and evidence["value"] is None:
        raise StructureContractError(
            f"present {source} page-label evidence has no value on physical page {physical_page}"
        )


def _validate_resolution(observation: JsonObject) -> None:
    """Derive the sole valid state, value, and basis from source evidence."""
    expected = _expected_resolution(
        observation["explicit_pdf_label"],
        observation["visible_label"],
    )
    actual = ExpectedResolution(
        state=observation["resolved_state"],
        value=observation["resolved_label"],
        basis=observation["resolution_basis"],
    )
    if actual != expected:
        physical_page = observation["physical_page_number"]
        raise StructureContractError(
            f"page-label resolution differs on physical page {physical_page}: "
            f"expected {expected}, got {actual}"
        )


def _expected_resolution(explicit: JsonObject, visible: JsonObject) -> ExpectedResolution:
    """Apply conflict, explicit-metadata, visible-consensus, then unknown precedence."""
    if _has_conflicting_evidence(explicit, visible):
        return ExpectedResolution(state="conflict", value=None, basis=None)
    if explicit["state"] == "present":
        return ExpectedResolution(
            state="resolved",
            value=explicit["value"],
            basis="explicit_pdf_page_labels",
        )
    if visible["state"] == "present":
        return ExpectedResolution(
            state="resolved",
            value=visible["value"],
            basis="visible_footer_consensus",
        )
    return ExpectedResolution(state="unknown", value=None, basis=None)


def _has_conflicting_evidence(explicit: JsonObject, visible: JsonObject) -> bool:
    """Return whether either source is conflicted or the two sources disagree."""
    return bool(
        explicit["state"] == "conflict"
        or visible["state"] == "conflict"
        or (
            explicit["state"] == "present"
            and visible["state"] == "present"
            and explicit["value"] != visible["value"]
        )
    )
