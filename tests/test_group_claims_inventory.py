"""Source-free checks against silently losing response assertions or qualifications."""

import copy

import pytest

from er_commons.group_claims_inventory import validate_inventory
from er_commons.group_ranking import digest, encoded


def fixture():
    """Invent one assertion whose meaning depends on two exact passages."""
    packet = {
        "cases": [
            {
                "case_id": "S",
                "passages": [
                    {"passage_id": "P1", "text": "It opens."},
                    {"passage_id": "P2", "text": "Only after inspection."},
                ],
            }
        ]
    }
    inventory = {
        "schema_version": "task08d.inventory.v1",
        "model": "gpt-6-astra",
        "packet_sha256": digest(encoded(packet)),
        "cases": [
            {
                "case_id": "S",
                "assertions": [
                    {
                        "assertion_id": "I1",
                        "text": "It opens after inspection.",
                        "passage_ids": ["P1", "P2"],
                    }
                ],
                "passage_coverage": [
                    {"passage_id": p, "assertion_ids": ["I1"], "note": "Qualification retained."}
                    for p in ("P1", "P2")
                ],
            }
        ],
    }
    proposal = {
        "schema_version": "task08d.proposal.v1",
        "model": "gpt-6-astra",
        "packet_sha256": digest(encoded(packet)),
        "inventory_sha256": digest(encoded(inventory)),
        "cases": [
            {
                "case_id": "S",
                "claims": [
                    {
                        "claim_id": "A001",
                        "text": "It opens after inspection.",
                        "assertion_ids": ["I1"],
                        "passage_ids": ["P1", "P2"],
                        "relationship": "direct",
                        "targets": ["Q1"],
                        "rationale": "States the condition.",
                    }
                ],
                "question_parts": [],
            }
        ],
    }
    return packet, inventory, proposal


def test_accounting_does_not_assert_semantic_truth():
    result = validate_inventory(*fixture())
    assert result["valid"]
    assert result["semantic_coverage"] == "requires independent review"


@pytest.mark.parametrize(
    "failure",
    [
        "missing_assertion",
        "dropped_qualification",
        "inventory_hash",
        "missing_passage",
        "coverage_disagrees",
    ],
)
def test_incomplete_two_pass_accounting_fails(failure):
    packet, inventory, proposal = copy.deepcopy(fixture())
    if failure == "missing_assertion":
        proposal["cases"][0]["claims"] = []
    elif failure == "dropped_qualification":
        proposal["cases"][0]["claims"][0]["passage_ids"] = ["P1"]
    elif failure == "inventory_hash":
        proposal["inventory_sha256"] = "0" * 64
    elif failure == "missing_passage":
        inventory["cases"][0]["passage_coverage"].pop()
        proposal["inventory_sha256"] = digest(encoded(inventory))
    else:
        inventory["cases"][0]["passage_coverage"][0]["assertion_ids"] = []
        proposal["inventory_sha256"] = digest(encoded(inventory))
    with pytest.raises(ValueError):
        validate_inventory(packet, inventory, proposal)
