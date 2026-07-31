"""Immutable Task 03E.2d bindings used by the semantic contract."""

EXPECTED_CANDIDATE_ID = "hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1"
EXPECTED_INVENTORY_DIGEST = "8242a22aab347b17964562081e3a4f1f38b2efec23480aed07b770c2ada35c3a"
EXPECTED_SEMANTIC_FILE_SET_DIGEST = (
    "75a0e36c7e5814d5135763a09c7374643fdd5e0edafd30de360bb954345dd3d2"
)
EXPECTED_AGGREGATE_DIGEST = "c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8"
EXPECTED_ACCEPTANCE_SHA256 = "5335737128fcbac2b1f2d41c42712af0534e2d15141ccf1150c37ffbf70f328c"
EXPECTED_AUTHORIZATION_ID = "brisbane_baylands_2025_deir_task03e2d_bounded_acceptance_v1"
EXPECTED_PRODUCER_COMPARISON_SHA256 = (
    "33574f6b15dc128a7bf58d6e2ab1a35c867ce1df493fe317a46bed1b8e8bf364"
)
PRODUCER_COMPARISON_RELATIVE_PATH = (
    "pipelines/brisbane_baylands/task_03e_hierarchy_review/"
    "cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/"
    "producer_comparison_report.json"
)

EXPECTED_LIMITATIONS = (
    "historical_development_and_held_out_quality_rejection",
    "two_observed_false_table_boundaries",
    "frozen_r04_r05_attribution_disagreements",
    "existing_ssf_district_level_disagreement",
    "page_2000_r06_content_ambiguity",
    "remaining_payload_ambiguities_and_warnings",
    "task_03e2a_has_no_new_held_out_evaluation",
)

EXPECTED_AUTHORIZED_USES = (
    "task_03e3_semantic_contract_input",
    "task_03e4_semantic_materialization_input",
    "task_03g_representative_pilot_hypothesis",
)

EXPECTED_SEMANTIC_COUNTS = {
    "features": 6931,
    "toc_entries": 140,
    "reconciliations": 140,
    "regimes": 2,
    "decisions": 6931,
    "roots": 12,
    "edges": 234,
    "direct_membership": 4571,
    "unassigned_content": 2,
    "ambiguities": 17,
    "warnings": 148,
}

EXPECTED_CONTROL_FIELDS = {
    "candidate_id": EXPECTED_CANDIDATE_ID,
    "completion_status": "complete_with_ambiguities",
    "artifact_inventory_sha256": EXPECTED_INVENTORY_DIGEST,
    "semantic_file_set_sha256": EXPECTED_SEMANTIC_FILE_SET_DIGEST,
    "aggregate_semantic_sha256": EXPECTED_AGGREGATE_DIGEST,
    "bounded_acceptance_sha256": EXPECTED_ACCEPTANCE_SHA256,
    "authorization_id": EXPECTED_AUTHORIZATION_ID,
    "acceptance_status": "accepted_with_known_limitations",
    "source_id": "deir_appendix_p",
    "physical_page_count": 222,
    "corpus_wide_acceptance": False,
    "producer_comparison_sha256": EXPECTED_PRODUCER_COMPARISON_SHA256,
}

PERMITTED_BRIDGE_DISPOSITIONS = frozenset(
    {
        "canonical_table_replacement_descendant",
        "canonical_figure_suppressed_descendant",
    }
)

ALLOWED_DIFFERENCE_CATEGORIES = (
    "identity_and_schema",
    "semantic_sections_and_membership",
    "page_label_resolution_and_observations",
    "target_aliases",
    "semantic_support_and_completion",
)

ALIAS_TARGET_TYPES = frozenset({"document", "page", "section", "table", "figure"})
