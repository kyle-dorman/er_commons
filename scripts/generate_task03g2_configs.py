"""Generate the reviewed, source-specialized Task 03G.2 config set."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "configs"
MANIFEST_RELATIVE = (
    "datasets/ceqa/raw/brisbane_baylands/"
    "brisbane_baylands_2025_deir_sources_v1/records/source_manifest.json"
)
MANIFEST_SHA256 = "fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38"
PRODUCER_ROOT = "pipelines/brisbane_baylands/task_03g2_document_producers"
CANONICAL_ROOT = "pipelines/brisbane_baylands/task_03g2_canonical_records"
CORRECTION_ROOT = "pipelines/brisbane_baylands/task_03g2_hierarchy_correction"
PILOT_ROOT = "pipelines/brisbane_baylands/task_03g2_representative_pilot"
ZERO_EXV1 = f"exv1-{'0' * 64}"
ZERO_PRV1 = f"prv1-{'0' * 64}"
ZERO_HCORV1 = f"hcorv1-{'0' * 64}"
ZERO_SHA256 = "0" * 64
IDENTITY_RELATIVE = (
    "benchmarks/er_bench/fixtures/corpus_extraction/v1_1/production_identity_preimage.json"
)
SOURCE_FAMILY_CATALOG_NAME = "brisbane_baylands_2025_deir_task03g2_source_family_catalog_v1.json"

SOURCES: tuple[dict[str, Any], ...] = (
    {
        "slug": "main",
        "source_id": "deir_main",
        "official_title": "Complete 2025 Baylands Specific Plan DEIR (PDF)",
        "sha256": "0b81e84176c86205c07d9ae6b2a9994fcd45405e516546bcfc7ab9b1f88cf83f",
        "byte_size": 65_818_524,
        "pdf_page_count": 2_092,
        "lookup_keys": [
            "complete 2025 baylands specific plan deir",
            "baylands specific plan draft eir",
            "draft eir",
            "deir",
        ],
    },
    {
        "slug": "appendix_d",
        "source_id": "deir_appendix_d",
        "official_title": "Appendix D - Biological Resources Technical Report (PDF)",
        "sha256": "0e0d0dc3d5c9d75ca52ec698f3943da59e560e69dde8dfa4763c9afd6673e1c3",
        "byte_size": 62_423_471,
        "pdf_page_count": 356,
        "lookup_keys": ["appendix d", "biological resources technical report"],
    },
    {
        "slug": "appendix_p",
        "source_id": "deir_appendix_p",
        "official_title": "Appendix P - Water Supply Assessment (PDF)",
        "sha256": "2dfceac46931a946bc343d52b09104b7b58ed8831bc4f49a03f0b8655e4e6ea1",
        "byte_size": 6_528_561,
        "pdf_page_count": 222,
        "lookup_keys": ["appendix p", "water supply assessment"],
    },
)


def main() -> None:
    """Write stable JSON bytes for every Task 03G.2 static input."""
    baseline_base = _read("brisbane_baylands_2025_deir_task03c_appendix_p_v2.json")
    hierarchy_base = _read("brisbane_baylands_2025_deir_task03e_appendix_p_v1.json")
    canonical_base = _read("brisbane_baylands_2025_deir_task03d_appendix_p_v1.json")
    correction_base = _read("brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json")
    semantic_base = _read("brisbane_baylands_2025_deir_task03e4_semantic_v1.json")
    cross_reference_base = _read(
        "brisbane_baylands_2025_deir_task03e5_cross_references_human_v2.json"
    )

    source_family_catalog_path = CONFIG_ROOT / SOURCE_FAMILY_CATALOG_NAME
    _write(source_family_catalog_path, _source_family_catalog())

    owner_paths: dict[str, dict[str, str]] = {}
    for source in SOURCES:
        owner_paths[str(source["source_id"])] = _write_owner_templates(
            source,
            baseline_base=baseline_base,
            hierarchy_base=hierarchy_base,
            canonical_base=canonical_base,
            correction_base=correction_base,
            semantic_base=semantic_base,
            cross_reference_base=cross_reference_base,
        )

    target_policy_path = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_target_policy_v1.json"
    resolution_policy_path = (
        CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json"
    )
    _write(
        target_policy_path,
        {
            "schema_version": "er_commons.corpus_target_policy.v1",
            "policy_version": "task03g2-corpus-target-policy-v1",
            "eligible_candidates": "verified_successful_document_candidates",
            "input_roles": ["target_aliases", "target_records", "document_targets"],
            "deduplication_key": ["alias_id", "target_id"],
            "collision_policy": "retain_cross_target_collisions",
            "ordering": [
                "normalized_lookup_key",
                "target_type",
                "manifest_source_ordinal",
                "target_id",
                "alias_id",
            ],
        },
    )
    _write(
        resolution_policy_path,
        {
            "schema_version": "er_commons.corpus_resolution_policy.v1",
            "policy_version": "task03g2-corpus-resolution-policy-v1",
            "eligible_resolution_status": "unresolved",
            "eligible_unresolved_reason": "deferred_cross_document",
            "target_type": "document",
            "catalog_join": "reviewed_alias_to_source_ids_to_sealed_document_targets",
            "match_fields": ["target_type", "intended_target_source_ids"],
            "dispositions": {
                "one_match": "resolved",
                "multiple_matches": "ambiguous",
                "successful_source_without_match": "target_unavailable",
                "failed_source": "target_source_failed",
                "source_outside_scope": "target_not_in_scope",
            },
            "stage_one_mutation": "forbidden",
        },
    )

    document_name = "brisbane_baylands_2025_deir_task03g2_document_v1.json"
    _write(
        CONFIG_ROOT / document_name,
        {
            "schema_version": "er_commons.document_run_spec.v1",
            "production_extraction_id": _pilot_identity_id(),
            "production_identity_relative_path": IDENTITY_RELATIVE,
            "scope_kind": "representative_pilot",
            "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
            "source_manifest_relative_path": MANIFEST_RELATIVE,
            "artifact_relative_root": PILOT_ROOT,
            "document_owners": [
                {
                    "source_id": source["source_id"],
                    "lineage_mode": "fresh_build",
                    "configs": owner_paths[str(source["source_id"])],
                }
                for source in SOURCES
            ],
            "hierarchy_dispositions": [
                {"source_id": source["source_id"], "authority": "machine_validation"}
                for source in SOURCES
            ],
            "resource_policy": {
                "document_concurrency": 1,
                "page_batch_size": 4,
                "stage_batch_size": 4,
                "queue_capacity": 100,
                "cpu_threads_per_document": 4,
                "device": "cpu",
                "memory_estimate_bytes": 17_179_869_184,
                "storage_estimate_bytes": 107_374_182_400,
                "docling_timeout_seconds": None,
                "outer_process_deadline_seconds": 86_400,
                "cancellation_grace_seconds": 15,
                "retry_limit": 1,
            },
        },
    )
    _write(
        CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_scope_v1.json",
        {
            "schema_version": "er_commons.scope_run_spec.v1",
            "document_run_spec": document_name,
            "source_ids": [source["source_id"] for source in SOURCES],
            "corpus_catalog_relative_path": (f"{PILOT_ROOT}/inputs/{SOURCE_FAMILY_CATALOG_NAME}"),
            "blocking_policy": "all_sources_successful",
            "document_evidence_mode": "downstream_replay_only",
            "target_policy_sha256": _sha256(target_policy_path),
            "resolution_policy_sha256": _sha256(resolution_policy_path),
            "ordering_policy_version": "corpus_target_order_v1",
        },
    )


def _write_owner_templates(
    source: dict[str, Any],
    *,
    baseline_base: dict[str, Any],
    hierarchy_base: dict[str, Any],
    canonical_base: dict[str, Any],
    correction_base: dict[str, Any],
    semantic_base: dict[str, Any],
    cross_reference_base: dict[str, Any],
) -> dict[str, str]:
    slug = str(source["slug"])
    source_id = str(source["source_id"])
    paths = {
        role: f"configs/brisbane_baylands_2025_deir_task03g2_{slug}_{role}_v1.json"
        for role in (
            "baseline_producer",
            "hierarchy_producer",
            "canonical",
            "hierarchy_correction",
            "semantic",
            "cross_references",
        )
    }
    producer_source = {
        "source_id": source_id,
        "official_title": source["official_title"],
        "expected_sha256": source["sha256"],
        "expected_byte_size": source["byte_size"],
        "expected_pdf_page_count": source["pdf_page_count"],
    }
    baseline = copy.deepcopy(baseline_base)
    baseline.update(
        {
            "pipeline_id": f"brisbane_baylands_2025_deir_task03g2_{slug}_baseline_v1",
            "source": producer_source,
            "artifact_relative_root": PRODUCER_ROOT,
        }
    )
    hierarchy = copy.deepcopy(hierarchy_base)
    hierarchy.update(
        {
            "pipeline_id": f"brisbane_baylands_2025_deir_task03g2_{slug}_hierarchy_v1",
            "source": producer_source,
            "artifact_relative_root": PRODUCER_ROOT,
        }
    )
    canonical = copy.deepcopy(canonical_base)
    canonical.update(
        {
            "mapping_policy_version": "task03g2-source-neutral-mapping-v1",
            "candidate_version_name": f"{source_id}_task03g2_core_candidate_v1",
            "ordered_materialization_scope": [
                {
                    "source_id": source_id,
                    "source_sha256": source["sha256"],
                    "pdf_page_count": source["pdf_page_count"],
                }
            ],
            "producer_artifact_relative_root": PRODUCER_ROOT,
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": CANONICAL_ROOT,
        }
    )
    correction = copy.deepcopy(correction_base)
    correction.update(
        {
            "pipeline_id": f"brisbane_baylands_2025_deir_task03g2_{slug}_correction_v1",
            "publication_authorization": "machine_validation",
            "source": producer_source,
            "producer_artifact_relative_root": PRODUCER_ROOT,
            "producer_run_id": ZERO_PRV1,
            "artifact_relative_root": CORRECTION_ROOT,
        }
    )
    correction.pop("bounded_acceptance_artifact_relative_root", None)
    # The maintained loader has a historical Appendix P path as this field's
    # default, so machine validation must override it explicitly with null.
    correction["bounded_acceptance_config_relative_path"] = None

    semantic = copy.deepcopy(semantic_base)
    semantic.update(
        {
            "candidate_version_name": f"{source_id}_task03g2_semantic_candidate_v2",
            "control_profile": "strict_quality_gate",
            "source": {
                "source_id": source_id,
                "source_sha256": source["sha256"],
                "physical_page_count": source["pdf_page_count"],
            },
            "baseline_candidate_relative_root": f"{CANONICAL_ROOT}/{ZERO_EXV1}",
            "baseline_candidate_id": ZERO_EXV1,
            "baseline_producer_relative_root": PRODUCER_ROOT,
            "baseline_producer_run_id": ZERO_PRV1,
            "hierarchy_producer_relative_root": PRODUCER_ROOT,
            "hierarchy_producer_run_id": ZERO_PRV1,
            "hierarchy_candidate_relative_root": f"{CORRECTION_ROOT}/{ZERO_HCORV1}",
            "hierarchy_candidate_id": ZERO_HCORV1,
            "artifact_relative_root": CANONICAL_ROOT,
        }
    )
    for field in (
        "bounded_acceptance_relative_path",
        "bounded_acceptance_policy_relative_path",
        "producer_comparison_relative_path",
        "expectations",
    ):
        semantic.pop(field, None)

    cross_references = copy.deepcopy(cross_reference_base)
    cross_references.update(
        {
            "upstream_candidate_id": ZERO_EXV1,
            "upstream_completion_sha256": ZERO_SHA256,
            "upstream_inventory_sha256": ZERO_SHA256,
            "source_id": source_id,
            "candidate_version_name": f"{source_id}_task03g2_cross_references_v3",
            "artifact_relative_root": CANONICAL_ROOT,
            "source_manifest_relative_path": MANIFEST_RELATIVE,
            "source_manifest_sha256": MANIFEST_SHA256,
            "source_family_catalog_relative_path": (
                f"{PILOT_ROOT}/inputs/{SOURCE_FAMILY_CATALOG_NAME}"
            ),
            "source_family_catalog_sha256": _sha256(CONFIG_ROOT / SOURCE_FAMILY_CATALOG_NAME),
        }
    )
    values = {
        "baseline_producer": baseline,
        "hierarchy_producer": hierarchy,
        "canonical": canonical,
        "hierarchy_correction": correction,
        "semantic": semantic,
        "cross_references": cross_references,
    }
    for role, value in values.items():
        _write(ROOT / paths[role], value)
    return paths


def _source_family_catalog() -> dict[str, Any]:
    """Build the shared reviewed source-family catalog used by both stages."""
    sources = []
    for source in SOURCES:
        aliases = list(source["lookup_keys"])
        aliases.append(str(source["official_title"]).casefold())
        sources.append(
            {
                "source": {
                    "source_id": source["source_id"],
                    "sha256": source["sha256"],
                    "byte_size": source["byte_size"],
                    "pdf_page_count": source["pdf_page_count"],
                },
                "family_root_source_id": "deir_main",
                "document_role": (
                    "root_report" if source["source_id"] == "deir_main" else "top_level_appendix"
                ),
                "parent_source_id": (None if source["source_id"] == "deir_main" else "deir_main"),
                "reference_aliases": aliases,
            }
        )
    return {
        "schema_version": "er_commons.source_family_catalog.v1",
        "catalog_version": "brisbane_baylands_2025_deir_task03g2_source_family_v1",
        "source_family_id": "brisbane_baylands_2025_deir",
        "sources": sources,
    }


def _read(name: str) -> dict[str, Any]:
    value = json.loads((CONFIG_ROOT / name).read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"config is not an object: {name}")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pilot_identity_id() -> str:
    """Reuse the generated pilot ID while retaining a zero sentinel before refresh."""
    identity_path = ROOT / IDENTITY_RELATIVE
    if not identity_path.is_file():
        return ZERO_EXV1
    record = json.loads(identity_path.read_bytes())
    preimage = record.get("preimage", {})
    if preimage.get("contract_revision") != "task_03g2_representative_pilot_v1":
        return ZERO_EXV1
    extraction_id = record.get("extraction_id")
    return extraction_id if isinstance(extraction_id, str) else ZERO_EXV1


if __name__ == "__main__":
    main()
