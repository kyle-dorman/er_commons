"""Profile-level tests proving stage-one owners accept non-pilot documents."""

from __future__ import annotations

import json
from pathlib import Path

from er_commons.canonical_extraction.config import CanonicalizationConfig
from er_commons.cross_reference_enrichment.config import CrossReferenceEnrichmentConfig
from er_commons.hierarchy_correction.configuration import HierarchyCorrectionConfig
from er_commons.semantic_materialization.config import SemanticMaterializationConfig

ROOT = Path(__file__).resolve().parents[1]


def _payload(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_bytes())


def test_canonical_owner_accepts_generic_complete_document_profile() -> None:
    payload = _payload("configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json")
    payload.update(
        acceptance_profile="generic_complete_document",
        candidate_version_name="alternate_document_v1",
        producer_run_id="prv1-" + "1" * 64,
    )
    payload["ordered_materialization_scope"] = [
        {"source_id": "alternate", "source_sha256": "2" * 64, "pdf_page_count": 7}
    ]

    config = CanonicalizationConfig.model_validate(payload)

    assert config.selected_source_id == "alternate"


def test_hierarchy_owner_accepts_strict_generic_document_profile() -> None:
    payload = _payload("configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json")
    payload.update(
        publication_authorization="machine_validation",
        pipeline_id="alternate_hierarchy_v1",
        producer_run_id="prv1-" + "3" * 64,
        bounded_acceptance_artifact_relative_root=None,
        bounded_acceptance_config_relative_path=None,
    )
    payload["source"] = {
        "source_id": "alternate",
        "official_title": "Alternate document",
        "expected_sha256": "4" * 64,
        "expected_byte_size": 123,
        "expected_pdf_page_count": 7,
    }

    config = HierarchyCorrectionConfig.model_validate(payload)

    assert config.source.source_id == "alternate"


def test_semantic_owner_accepts_strict_independent_document_profile() -> None:
    payload = _payload("configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json")
    payload.update(
        candidate_version_name="alternate_semantic_v2",
        control_profile="strict_quality_gate",
        baseline_candidate_id="exv1-" + "5" * 64,
        baseline_producer_run_id="prv1-" + "6" * 64,
        hierarchy_producer_run_id="prv1-" + "7" * 64,
        hierarchy_candidate_id="hcorv1-" + "8" * 64,
        hierarchy_candidate_relative_root=("pipelines/alternate/hcorv1-" + "8" * 64),
        bounded_acceptance_relative_path=None,
        bounded_acceptance_policy_relative_path=None,
        producer_comparison_relative_path=None,
    )
    payload["source"] = {
        "source_id": "alternate",
        "source_sha256": "9" * 64,
        "physical_page_count": 7,
    }
    payload["expectations"] = {
        "section_count": 3,
        "bridge_entry_count": 8,
        "canonical_block_count": 5,
        "heading_count": 2,
        "direct_membership_count": 5,
        "mapped_block_count": 5,
        "table_replacement_count": 0,
        "figure_suppression_count": 0,
    }

    config = SemanticMaterializationConfig.model_validate(payload)

    assert config.source.source_id == "alternate"
    assert config.expectations.section_count == 3


def test_cross_reference_owner_accepts_independent_document_profile(
    tmp_path: Path,
) -> None:
    payload = _payload(
        "configs/brisbane_baylands_2025_deir_task03e5_cross_references_human_v2.json"
    )
    payload.update(
        source_id="alternate",
        candidate_version_name="alternate_cross_references_v3",
    )
    path = tmp_path / "cross_reference.json"
    path.write_text(json.dumps(payload))

    config = CrossReferenceEnrichmentConfig.load(path)

    assert config.source_id == "alternate"
    assert config.source_id == "alternate"
