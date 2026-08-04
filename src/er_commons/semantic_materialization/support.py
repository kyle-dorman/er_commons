"""Build the four semantic support payloads and validator projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.semantic_materialization.baseline import load_baseline_candidate
from er_commons.semantic_materialization.comparison import compare_baseline_collections
from er_commons.semantic_materialization.config import SemanticExpectations
from er_commons.semantic_materialization.construction import SemanticBuild
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError

JsonObject = dict[str, Any]

SUPPORT_PATHS = {
    "cross_producer_bridge": "support/cross_producer_bridge.json",
    "candidate_correspondence": "support/candidate_correspondence.json",
    "baseline_preservation": "support/baseline_preservation.json",
    "bounded_control_verification": "support/bounded_control_verification.json",
}


@dataclass(frozen=True)
class CandidateSupport:
    """The exact noncanonical support files and their correspondence summary."""

    payloads: dict[str, JsonObject]
    correspondence: JsonObject


def semantic_validation_bundle(
    *,
    build: SemanticBuild,
    control: JsonObject,
    correspondence: JsonObject,
    baseline_producer_run_id: str,
    hierarchy_producer_run_id: str,
) -> JsonObject:
    """Project persisted records into the accepted executable v2 contract."""
    global_order = list(
        dict.fromkeys(
            record_id
            for page in build.collections["pages"]
            for record_id in page["ordered_content_ids"]
        )
    )
    return {
        "document_id": build.collections["documents"][0]["id"],
        "expected_page_count": len(build.collections["pages"]),
        "global_content_order_ids": global_order,
        "sections": build.collections["sections"],
        "content": _compact_content(build),
        "page_label_observations": build.page_label_observations,
        "target_aliases": build.target_aliases,
        "baseline_producer_run_id": baseline_producer_run_id,
        "hierarchy_producer_run_id": hierarchy_producer_run_id,
        "bridge_entries": build.bridge_entries,
        "control_provenance": control,
        "correspondence_report": correspondence,
        "cross_references": build.collections["cross_references"],
    }


def build_candidate_support(
    *,
    baseline_root: Path,
    build: SemanticBuild,
    baseline_candidate_id: str,
    candidate_id: str,
    control: JsonObject,
    expectations: SemanticExpectations,
) -> CandidateSupport:
    """Build preservation, bridge, correspondence, and control evidence."""
    baseline = load_baseline_candidate(baseline_root)
    preservation = compare_baseline_collections(
        baseline.collections,
        build.collections,
        baseline_candidate_id=baseline_candidate_id,
        new_candidate_id=candidate_id,
    )
    if preservation["undeclared_difference_count"]:
        raise SemanticMaterializationInvariantError(
            stage="baseline preservation",
            invariant="Task 03D.1 differences are declared semantic extensions",
            expected=0,
            observed=preservation["undeclared_difference_count"],
            subject="candidate collections",
        )
    correspondence = {
        key: preservation[key]
        for key in (
            "baseline_candidate_id",
            "new_candidate_id",
            "allowed_difference_categories",
            "undeclared_difference_count",
            "status",
        )
    }
    payloads = {
        "cross_producer_bridge": _bridge_payload(build, control, expectations),
        "candidate_correspondence": correspondence,
        "baseline_preservation": {
            "schema_version": "er_commons.baseline_preservation.v2",
            **preservation,
        },
        "bounded_control_verification": {
            "schema_version": "er_commons.bounded_control_verification.v2",
            "status": "verified",
            "source_semantic_disposition": (
                "strict_quality_gate"
                if control.get("control_kind") == "strict_quality_gate"
                else "accepted_with_known_limitations"
            ),
            "control_provenance": control,
        },
    }
    return CandidateSupport(payloads=payloads, correspondence=correspondence)


def _compact_content(build: SemanticBuild) -> list[JsonObject]:
    records: list[JsonObject] = []
    for record_type, family in (("block", "blocks"), ("table", "tables"), ("figure", "figures")):
        for record in build.collections[family]:
            records.append(
                {
                    "id": record["id"],
                    "record_type": record_type,
                    "content_layer": record["content_layer"],
                    "section_id": record["section_id"],
                    "sequence": record["sequence"],
                    "semantic_placement": record["semantic_placement"],
                    "is_toc_row": record["is_toc_row"],
                    "stable_item_key": record["stable_item_key"],
                }
            )
    order = {
        record_id: index
        for index, record_id in enumerate(
            dict.fromkeys(
                record_id
                for page in build.collections["pages"]
                for record_id in page["ordered_content_ids"]
            )
        )
    }
    return sorted(records, key=lambda item: order[item["id"]])


def _bridge_payload(
    build: SemanticBuild, control: JsonObject, expectations: SemanticExpectations
) -> JsonObject:
    table_replacements = sum(
        item["disposition"] == "canonical_table_replacement_descendant"
        for item in build.bridge_entries
    )
    figure_suppressions = sum(
        item["disposition"] == "canonical_figure_suppressed_descendant"
        for item in build.bridge_entries
    )
    return {
        "schema_version": "2.0.0",
        "producer_comparison_sha256": control["producer_comparison_sha256"],
        "heading_count": expectations.heading_count,
        "direct_membership_count": expectations.direct_membership_count,
        "mapped_block_count": expectations.mapped_block_count,
        "table_replacement_count": table_replacements,
        "figure_suppression_count": figure_suppressions,
        "entries": build.bridge_entries,
        "status": "complete",
    }
