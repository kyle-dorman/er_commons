"""Construct one evidence-based printed-label outcome per physical page."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from er_commons.semantic_structure.errors import SemanticContractError

JsonObject = dict[str, Any]


def build_page_label_observations(
    *,
    page_count: int,
    item_features: list[JsonObject],
    visible_evidence_ref: JsonObject,
    explicit_labels: Mapping[int, tuple[str, ...]] | None = None,
    explicit_evidence_ref: JsonObject | None = None,
) -> list[JsonObject]:
    """Aggregate all page evidence before resolving labels by accepted precedence."""
    if page_count < 1:
        raise SemanticContractError("page-label construction requires at least one page")
    explicit_labels = explicit_labels or {}
    invalid_pages = sorted(set(explicit_labels) - set(range(1, page_count + 1)))
    if invalid_pages:
        raise SemanticContractError(
            f"explicit page-label evidence is out of range: {invalid_pages}"
        )

    visible_by_page: dict[int, list[str]] = defaultdict(list)
    for feature in item_features:
        page = int(feature["physical_page"])
        if page < 1 or page > page_count:
            raise SemanticContractError(f"visible page-label evidence is out of range: {page}")
        label = feature.get("printed_page_label")
        if label is not None:
            visible_by_page[page].append(str(label))

    observations = []
    for page in range(1, page_count + 1):
        explicit = _evidence(tuple(explicit_labels.get(page, ())), explicit_evidence_ref)
        visible = _evidence(tuple(visible_by_page.get(page, ())), visible_evidence_ref)
        state, value, basis = _resolve(explicit, visible)
        observations.append(
            {
                "physical_page_number": page,
                "explicit_pdf_label": explicit,
                "visible_label": visible,
                "resolved_state": state,
                "resolved_label": value,
                "resolution_basis": basis,
                "synthesized_default_rejected": True,
            }
        )
    return observations


def _evidence(values: tuple[str, ...], evidence_ref: JsonObject | None) -> JsonObject:
    distinct = tuple(dict.fromkeys(values))
    if not distinct:
        return {"state": "absent", "value": None, "evidence_refs": []}
    if evidence_ref is None:
        raise SemanticContractError("present page-label evidence requires a checksum reference")
    if len(distinct) == 1:
        return {"state": "present", "value": distinct[0], "evidence_refs": [evidence_ref]}
    return {"state": "conflict", "value": None, "evidence_refs": [evidence_ref]}


def _resolve(explicit: JsonObject, visible: JsonObject) -> tuple[str, str | None, str | None]:
    if (
        explicit["state"] == "conflict"
        or visible["state"] == "conflict"
        or (
            explicit["state"] == "present"
            and visible["state"] == "present"
            and explicit["value"] != visible["value"]
        )
    ):
        return "conflict", None, None
    if explicit["state"] == "present":
        return "resolved", str(explicit["value"]), "explicit_pdf_page_labels"
    if visible["state"] == "present":
        return "resolved", str(visible["value"]), "visible_footer_consensus"
    return "unknown", None, None
