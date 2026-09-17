"""Synthetic guards on existing owners; these do not implement Task 05G replay."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256
from er_commons.human_review_support.extraction_review.task06h_contract import final_f1_warnings
from er_commons.human_review_support.extraction_review.task06h_correspondence import (
    correspondence_result,
)
from er_commons.response_inventory.reference_baseline import (
    _fallback_candidates,
    _MentionContext,
    _publish_candidate,
    _query_plan,
    _target_indexes,
    _validate_acceptance,
    _validate_outcomes,
)


def _outcomes() -> list[dict[str, Any]]:
    """Create schema-valid terminal outcomes without reading source artifacts."""
    return [
        {
            "schema_version": "er_commons.task05f.reference_outcome.v1",
            "outcome_id": f"outcomev1-{index:064x}",
            "mention_id": f"mention-{index}",
            "mention_span_id": f"span-{index}",
            "source_unit_id": "unit-synthetic",
            "source_kind": "response",
            "raw_text_sha256": "a" * 64,
            "reference_domain": "draft_eir" if index < 509 else "appendix_q",
            "raw_target_label": "synthetic label",
            "qualifier": None,
            "projected_target": None,
            "canonical_target": None,
            "requested_target_type": None,
            "routed_source_ids": [],
            "global_candidate_target_ids": [],
            "source_candidate_target_ids": [],
            "compatible_target_ids": [],
            "outcome": "terminal_nonlink",
            "terminal_reason": "unsupported_reference_form",
            "link_id": None,
            "task04a_registry_entry_id": None,
            "task04a_usability": "not_applicable",
            "visual_evidence_usability": "not_applicable",
        }
        for index in range(511)
    ]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "conflicting", "incomplete"])
def test_existing_outcome_owner_rejects_broken_closure(mutation: str) -> None:
    """Require 511 distinct schema-valid outcomes and coherent link status."""
    schema_path = (
        Path(__file__).resolve().parents[1]
        / "benchmarks/er_bench/schemas/response_inventory/v5/reference_outcome.schema.json"
    )
    schema = json.loads(schema_path.read_text())
    outcomes = _outcomes()
    _validate_outcomes(outcomes, schema)
    if mutation == "missing":
        outcomes.pop()
    elif mutation == "duplicate":
        outcomes[-1] = copy.deepcopy(outcomes[0])
    elif mutation == "conflicting":
        outcomes[0]["link_id"] = "link-for-a-nonlink"
    else:
        del outcomes[0]["terminal_reason"]
    with pytest.raises((ValueError, ValidationError)):
        _validate_outcomes(outcomes, schema)


@pytest.mark.parametrize("mutation", ["general", "specific", "equivalence", "limitations"])
def test_existing_acceptance_digest_detects_warning_loss(mutation: str) -> None:
    """Exercise content binding with the actual warning record shape, in memory."""
    record: dict[str, Any] = {"status": "accepted", "warnings": final_f1_warnings()}
    record["acceptance_id"] = f"acceptancev1-{canonical_json_sha256(record)}"
    _validate_acceptance(record, expected={"status": "accepted"})
    warnings = record["warnings"]
    field = {
        "general": "general_warning",
        "specific": "response_specific",
        "equivalence": "other_mentions_not_proven_draft_final_equivalent",
        "limitations": "accepted_limitations",
    }[mutation]
    del warnings[field]
    with pytest.raises(ValueError, match="content"):
        _validate_acceptance(record, expected={"status": "accepted"})


def test_existing_acceptance_requires_expected_identity_even_when_rehashed() -> None:
    """A valid digest cannot replace an explicitly selected upstream identity."""
    record = {"status": "accepted", "handoff_id": "synthetic-replacement"}
    record["acceptance_id"] = f"acceptancev1-{canonical_json_sha256(record)}"
    with pytest.raises(ValueError, match="mismatch"):
        _validate_acceptance(record, expected={"handoff_id": "synthetic-selected"})


def test_existing_publication_restarts_only_with_exact_complete_bytes(tmp_path: Path) -> None:
    """An identical retry preserves bytes; drift and incomplete roots fail closed."""
    root = tmp_path / "candidate"
    payloads = {"outcomes/test.json": b'{"synthetic":true}\n'}
    receipt = {"synthetic": True}
    _publish_candidate(root, payloads, receipt)
    original = (root / "outcomes/test.json").stat().st_mtime_ns
    _publish_candidate(root, payloads, receipt)
    assert (root / "outcomes/test.json").stat().st_mtime_ns == original
    with pytest.raises(ValueError, match="differs"):
        _publish_candidate(root, {"outcomes/test.json": b"changed"}, receipt)
    (root / "records/rule_receipt.json").unlink()
    with pytest.raises(ValueError, match="partial"):
        _publish_candidate(root, payloads, receipt)


@pytest.mark.parametrize("kind", ["chapter", "section", "table", "figure", "page"])
def test_existing_appendix_fallback_preserves_attached_specificity(kind: str) -> None:
    """An absent inner target cannot turn into an available outer document link."""
    plan = _query_plan("Draft EIR Appendix D", "draft_eir", {"appendix d": {"deir_appendix_d"}}, {})
    indexes = _target_indexes(
        [
            {
                "lookup_key": "report",
                "source_id": "deir_appendix_d",
                "target_type": "document",
                "target_id": "doc",
            }
        ],
        {},
    )
    outer, _, reason = _fallback_candidates(plan, indexes, _MentionContext())
    assert len(outer) == 1 and reason is None
    rows, _, reason = _fallback_candidates(plan, indexes, _MentionContext(before=f"{kind} 3 in "))
    assert rows == []
    assert reason == "more_specific_appendix_target_requires_resolution"


def test_sample_confirmation_does_not_prove_unproven_substantive_reuse() -> None:
    """The historical correspondence owner keeps sampled and proven reuse apart."""
    evidence: dict[str, Any] = {
        "text": [],
        "tables": [],
        "image_attachments": [],
        "placement": [],
        "context": [],
    }
    common: dict[str, Any] = {
        "source_change_class": "repaired",
        "mapping_cardinality": "one_to_one",
        "old_evidence": evidence,
        "new_evidence": evidence,
        "policy_compatible": True,
    }
    assert correspondence_result(classification="unchanged", **common) == "reused_unchanged"
    assert (
        correspondence_result(classification="unproven", sample_result="confirmed", **common)
        == "new_review_required"
    )
    assert (
        correspondence_result(
            classification="unchanged", sample_result="mismatch_invalidate_stratum", **common
        )
        == "new_review_required"
    )
