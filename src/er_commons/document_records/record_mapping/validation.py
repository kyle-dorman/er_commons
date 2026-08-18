"""Cross-record validation for a schema-valid extraction bundle.

JSON Schema validates each record's shape. The policy functions below validate
relationships that only become meaningful when the complete bundle is
considered together.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from er_commons.document_records.record_mapping.bundle import BundleView
from er_commons.document_records.record_mapping.policies.bundle import (
    document_pages_are_complete,
    human_review_fields_are_absent,
    identity_matches_manifest,
    manifest_matches_serialized_records,
    record_ids_are_unique_and_well_formed,
    records_are_canonically_ordered,
    references_exist_and_have_expected_types,
    source_edition_overrides_propagate,
    source_release_matches_documents,
)
from er_commons.document_records.record_mapping.policies.content import (
    canonical_text_is_explainable,
    page_content_lists_are_complete,
    regions_match_their_pages,
    section_hierarchy_is_consistent,
    table_families_are_consistent,
    table_shapes_are_complete,
    table_stage_mappings_are_consistent,
)
from er_commons.document_records.record_mapping.policies.lineage import (
    caption_links_target_captions,
    cross_reference_statuses_are_consistent,
    raw_link_producers_are_compatible,
    raw_mapping_coverage_is_complete,
    relationships_stay_within_documents,
)

PolicyCheck = Callable[[BundleView], None]

# Order matters: early checks establish the indexes and relationships that
# later, more specific checks rely on.
BUNDLE_POLICY_CHECKS: tuple[PolicyCheck, ...] = (
    identity_matches_manifest,
    record_ids_are_unique_and_well_formed,
    human_review_fields_are_absent,
    references_exist_and_have_expected_types,
    manifest_matches_serialized_records,
    source_release_matches_documents,
    document_pages_are_complete,
    source_edition_overrides_propagate,
    regions_match_their_pages,
    records_are_canonically_ordered,
    section_hierarchy_is_consistent,
    table_families_are_consistent,
    table_shapes_are_complete,
    table_stage_mappings_are_consistent,
    canonical_text_is_explainable,
    relationships_stay_within_documents,
    page_content_lists_are_complete,
    raw_mapping_coverage_is_complete,
    raw_link_producers_are_compatible,
    cross_reference_statuses_are_consistent,
    caption_links_target_captions,
)


def validate_bundle_integrity(bundle: dict[str, Any]) -> None:
    """Validate cross-record policy for one schema-valid extraction bundle.

    Callers must validate individual record shapes with the published JSON
    Schema first. Keeping those layers separate makes it clear whether a failure
    concerns JSON structure or a relationship across records.
    """
    view = BundleView(bundle)
    for check in BUNDLE_POLICY_CHECKS:
        check(view)
