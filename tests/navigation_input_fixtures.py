"""Historical test inputs kept separate from runtime defaults."""

from er_commons.navigation_overlay.input_specs import (
    MaterializationBindings,
    PreparationBindings,
    ReconciliationBindings,
)

PREPARATION = PreparationBindings(
    **{
        "production_extraction_id": (
            "exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773"
        ),
        "scope_id": ("scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893"),
        "handoff_id": (
            "handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325"
        ),
        "task04a_review_id": "reviewv1-task03j-final-c17",
        "task04a_gate_a_id": "reviewv1-task03j-final-b19a7a36b04bda89",
        "expected_source_count": 35,
        "expected_census_page_count": 5624,
        "expected_decision_count": 757,
        "expected_decision_counts": {"toc": 60, "not_toc": 697},
        "expected_ambiguous_link_count": 725,
    }
)
MATERIALIZATION = MaterializationBindings(
    **{
        "accepted_gate_a_id": (
            "navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741"
        ),
        "expected_decision_count": 757,
        "expected_accounting": {
            "decision_count": 757,
            "machine_toc_human_toc_count": 45,
            "machine_not_toc_human_not_toc_count": 303,
            "human_confirmed_navigation_decision_count": 15,
            "human_rejected_machine_navigation_decision_count": 391,
            "fail_closed_decision_count": 3,
            "changed_content_entity_count": 5800,
            "human_confirmed_navigation_entity_count": 72,
            "human_rejected_machine_navigation_entity_count": 5728,
            "changed_block_count": 5785,
            "changed_table_count": 15,
            "preserved_section_association_count": 23,
        },
    }
)
RECONCILIATION = ReconciliationBindings(
    **{
        "accepted_gate_a_id": (
            "navoverlayplanv1-72af852ffe39c272ce958147c74974008269b6e72db2c0c7b03e0f66ba366741"
        ),
        "accepted_gate_b_id": (
            "navsemanticv1-ae00c6e6f70839f1ca15404c9dff14161f0a3e9aaa9e7902f51f65b36023c8fc"
        ),
        "expected_source_count": 35,
        "expected_ambiguity_count": 725,
        "expected_table_count": 15,
        "expected_entry_count": 560,
    }
)
