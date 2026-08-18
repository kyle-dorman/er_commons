"""Focused tests for owner inputs, authorization, and warning handoffs."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from document_publication_test_support import _workspace

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_publication.config import HierarchyDisposition, load_document_run_spec
from er_commons.document_publication.fresh_lineage import FreshLineageBinder
from er_commons.document_publication.lineage_preflight import (
    ProducerLineage,
    validate_lineage_bindings,
)
from er_commons.document_publication.lineage_validation import (
    validate_current_hierarchy_identity,
)
from er_commons.document_publication.process_diagnostics import run_process_stage
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_process_resources,
)
from er_commons.document_publication.process_observations import collect_process_warnings
from er_commons.document_publication.process_validation import (
    ProcessCompletions,
    validate_hierarchy_authorization,
)


def test_hierarchy_authorization_joins_config_semantic_and_evidence(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    config = tmp_path / "correction.json"
    config.write_text('{"publication_authorization":"bounded_acceptance"}')
    relative = Path("authorization.json")
    write_json_atomic(
        data_root / relative,
        {
            "status": "accepted_with_known_limitations",
            "scope": {"source_id": "alpha", "corpus_wide_acceptance": False},
            "candidate": {
                "identity": {
                    "candidate_id": "hcorv1-test",
                    "config_sha256": sha256_file(config),
                }
            },
        },
    )
    validate_hierarchy_authorization(
        data_root=data_root,
        source_id="alpha",
        disposition={
            "authority": "bounded_acceptance",
            "authorization_relative_path": relative.as_posix(),
        },
        correction_config={"publication_authorization": "bounded_acceptance"},
        semantic_config={"bounded_acceptance_relative_path": relative.as_posix()},
        correction_id="hcorv1-test",
        correction_config_path=config,
    )
    with pytest.raises(ValueError, match="differs from correction authorization"):
        validate_hierarchy_authorization(
            data_root=data_root,
            source_id="alpha",
            disposition={"authority": "machine_validation"},
            correction_config={"publication_authorization": "bounded_acceptance"},
            semantic_config={"bounded_acceptance_relative_path": relative.as_posix()},
            correction_id="hcorv1-test",
            correction_config_path=config,
        )


def test_resource_preflight_rejects_effective_producer_drift(tmp_path: Path) -> None:
    _data_root, spec_path = _workspace(tmp_path)
    spec, _digest = load_document_run_spec(spec_path)
    drifted = spec.model_copy(
        update={
            "resource_policy": spec.resource_policy.model_copy(
                update={"cpu_threads_per_document": 5}
            )
        }
    )
    configured = ProcessConfigs(
        content_parsing=Path("configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json"),
        heading_evidence_parsing=Path(
            "configs/brisbane_baylands_2025_deir_task03e_appendix_p_v1.json"
        ),
        record_mapping=Path("configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json"),
        hierarchy_inference=Path(
            "configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json"
        ),
        document_structure=Path("configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json"),
        document_reference_linking=Path(
            "configs/brisbane_baylands_2025_deir_task03e5_cross_references_human_v2.json"
        ),
    )
    with pytest.raises(ValueError, match="effective config"):
        verify_process_resources(configured, drifted, data_root=tmp_path)


def test_warning_aggregation_includes_hierarchy_summary_and_stream(
    tmp_path: Path,
) -> None:
    root = tmp_path / "hierarchy"
    completion = root / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    write_json_atomic(completion, {"status": "complete_with_ambiguities"})
    write_json_atomic(root / "records/summary.json", {"warning_count": 1})
    stream = root / "artifacts/warnings.jsonl"
    stream.parent.mkdir()
    stream.write_text('{"code":"TOC_WARNING","detail":"retained ambiguity"}\n')
    repeated = ProcessCompletions(
        content_parsing=completion,
        heading_evidence_parsing=completion,
        record_mapping=completion,
        hierarchy_inference=completion,
        document_structure=completion,
        document_reference_linking=completion,
    )

    warnings = collect_process_warnings(repeated)

    assert "hierarchy_decisions warning_count: 1" in warnings
    assert "hierarchy_decisions TOC_WARNING: retained ambiguity" in warnings


def test_owner_failure_persists_stage_qualified_diagnostics(tmp_path: Path) -> None:
    def fail() -> Path:
        raise RuntimeError("owner broke")

    with pytest.raises(RuntimeError, match="owner broke"):
        run_process_stage(
            "document_structure",
            {},
            fail,
            diagnostics_root=tmp_path,
            ordinal=5,
            data_root=tmp_path,
        )

    started = json.loads(
        (tmp_path / "document_process_events/05_document_structure_started.json").read_text()
    )
    failed = json.loads(
        (tmp_path / "document_process_events/05_document_structure_failed.json").read_text()
    )
    assert started["state"] == "started"
    assert failed["state"] == "failed"
    assert failed["error_class"] == "RuntimeError"


def test_lineage_preflight_rejects_predicted_producer_drift_before_pdf(
    tmp_path: Path,
) -> None:
    configs, disposition = _lineage_fixture(tmp_path)

    with pytest.raises(ValueError, match="before PDF work.*record_mapping baseline producer"):
        validate_lineage_bindings(
            configs=configs,
            source_id="alpha",
            disposition=disposition,
            lineage=ProducerLineage(
                baseline="prv1-" + "1" * 64,
                hierarchy="prv1-" + "2" * 64,
            ),
            data_root=tmp_path / "data",
        )


def test_lineage_preflight_rejects_stale_candidate_authorization(
    tmp_path: Path,
) -> None:
    configs, disposition = _lineage_fixture(tmp_path)
    correction_sha = sha256_file(configs.hierarchy_inference)
    evidence_path = tmp_path / "data" / disposition.authorization_relative_path
    evidence = json.loads(evidence_path.read_text())
    evidence["candidate"]["identity"]["config_sha256"] = correction_sha
    write_json_atomic(evidence_path, evidence)
    configs.hierarchy_inference.write_text(
        '{"producer_run_id":"prv1-'
        + "2" * 64
        + '","publication_authorization":"bounded_acceptance","changed":true}'
    )

    with pytest.raises(ValueError, match="bounded authorization correction config is stale"):
        validate_lineage_bindings(
            configs=configs,
            source_id="alpha",
            disposition=disposition,
            lineage=ProducerLineage(
                baseline="prv1-" + "1" * 64,
                hierarchy="prv1-" + "2" * 64,
            ),
            data_root=tmp_path / "data",
        )


def test_lineage_preflight_compares_semantic_id_to_current_hierarchy_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = "hcorv1-" + "1" * 64
    derived = "hcorv1-" + "2" * 64
    monkeypatch.setattr(
        "er_commons.hierarchy_inference.preflight.prepare_run",
        lambda *_args: SimpleNamespace(candidate_id=derived),
    )
    mismatches: list[str] = []

    validate_current_hierarchy_identity(
        tmp_path,
        tmp_path / "hierarchy.json",
        {"hierarchy_candidate_id": configured},
        mismatches,
    )

    assert mismatches == [
        "document_structure hierarchy candidate is stale for current code/config: "
        f"configured={configured}, derived={derived}"
    ]


def test_fresh_lineage_preflight_does_not_require_downstream_candidates(
    tmp_path: Path,
) -> None:
    configs = _fresh_templates(tmp_path)
    validate_lineage_bindings(
        configs=configs,
        source_id="deir_appendix_p",
        disposition=HierarchyDisposition(
            source_id="deir_appendix_p", authority="machine_validation"
        ),
        lineage=ProducerLineage(
            baseline="prv1-" + "1" * 64,
            hierarchy="prv1-" + "2" * 64,
        ),
        data_root=tmp_path / "data",
        lineage_mode="fresh_build",
    )


def test_fresh_lineage_preflight_rejects_historical_pins_and_bounded_authority(
    tmp_path: Path,
) -> None:
    configs = _fresh_templates(tmp_path)
    document_structure = json.loads(configs.document_structure.read_text())
    document_structure["baseline_candidate_id"] = "exv1-" + "9" * 64
    configs.document_structure.write_text(json.dumps(document_structure))
    with pytest.raises(ValueError, match="machine hierarchy validation.*non-placeholder"):
        validate_lineage_bindings(
            configs=configs,
            source_id="deir_appendix_p",
            disposition=HierarchyDisposition(
                source_id="deir_appendix_p",
                authority="bounded_acceptance",
                authorization_relative_path=Path("historical/authorization.json"),
            ),
            lineage=ProducerLineage(
                baseline="prv1-" + "1" * 64,
                hierarchy="prv1-" + "2" * 64,
            ),
            data_root=tmp_path / "data",
            lineage_mode="fresh_build",
        )


def test_fresh_binder_persists_exact_effective_lineage(tmp_path: Path) -> None:
    configs = _fresh_templates(tmp_path)
    data_root = tmp_path / "data"
    attempt = data_root / "pipelines/task_03g2_document/attempts/one"
    binder = FreshLineageBinder(
        data_root=data_root,
        project_root=tmp_path,
        source_id="deir_appendix_p",
        templates=configs,
        attempt_root=attempt,
    )
    binder.initial_configs()
    baseline = _completion(data_root, "producer", "prv1-" + "1" * 64)
    hierarchy = _completion(data_root, "producer", "prv1-" + "2" * 64)
    record_mapping = _completion(data_root, "record_mapping", "exv1-" + "3" * 64)
    correction = _completion(data_root, "correction", "hcorv1-" + "4" * 64)
    document_structure = _completion(data_root, "document_structure", "exv1-" + "5" * 64)

    canonical_config = binder.canonical_config(baseline)
    binder.correction_config(hierarchy)
    semantic_config = binder.semantic_config(
        baseline_completion=baseline,
        hierarchy_completion=hierarchy,
        canonical_completion=record_mapping,
        correction_completion=correction,
    )
    cross_config = binder.cross_reference_config(document_structure)

    assert json.loads(canonical_config.read_text())["producer_run_id"] == baseline.parents[1].name
    assert json.loads(semantic_config.read_text())["hierarchy_candidate_id"] == (
        correction.parents[1].name
    )
    assert json.loads(cross_config.read_text())["upstream_completion_sha256"] == sha256_file(
        document_structure
    )
    manifest = json.loads(
        (attempt / "effective_document_process_configs/binding_manifest.json").read_text()
    )
    assert set(manifest["bindings"]) == set(configs.as_dict())
    assert manifest["bindings"]["document_structure"]["upstreams"]["record_mapping"]["sha256"] == (
        sha256_file(record_mapping)
    )


def _lineage_fixture(tmp_path: Path) -> tuple[ProcessConfigs, HierarchyDisposition]:
    baseline = "prv1-" + "0" * 64
    hierarchy = "prv1-" + "2" * 64
    candidate = "hcorv1-" + "3" * 64
    record_mapping = tmp_path / "record_mapping.json"
    correction = tmp_path / "correction.json"
    document_structure = tmp_path / "document_structure.json"
    other = tmp_path / "other.json"
    record_mapping.write_text('{"producer_run_id":"' + baseline + '"}')
    correction.write_text(
        '{"producer_run_id":"' + hierarchy + '","publication_authorization":"bounded_acceptance"}'
    )
    authorization = Path("review") / candidate / "bounded_acceptance.json"
    document_structure.write_text(
        json.dumps(
            {
                "baseline_producer_run_id": baseline,
                "hierarchy_producer_run_id": hierarchy,
                "baseline_candidate_id": "exv1-" + "4" * 64,
                "baseline_candidate_relative_root": ("pipelines/record_mapping/exv1-" + "4" * 64),
                "hierarchy_candidate_id": candidate,
                "hierarchy_candidate_relative_root": f"pipelines/hierarchy/{candidate}",
                "bounded_acceptance_relative_path": authorization.as_posix(),
            }
        )
    )
    other.write_text("{}")
    data_root = tmp_path / "data"
    write_json_atomic(
        data_root / authorization,
        {
            "status": "accepted_with_known_limitations",
            "scope": {"source_id": "alpha", "corpus_wide_acceptance": False},
            "candidate": {
                "identity": {
                    "candidate_id": candidate,
                    "config_sha256": sha256_file(correction),
                }
            },
        },
    )
    configs = ProcessConfigs(
        content_parsing=other,
        heading_evidence_parsing=other,
        record_mapping=record_mapping,
        hierarchy_inference=correction,
        document_structure=document_structure,
        document_reference_linking=other,
    )
    disposition = HierarchyDisposition(
        source_id="alpha",
        authority="bounded_acceptance",
        authorization_relative_path=authorization,
    )
    return configs, disposition


def _fresh_templates(tmp_path: Path) -> ProcessConfigs:
    zero = "0" * 64
    config_root = tmp_path / "configs"
    config_root.mkdir()
    source_root = Path(__file__).parents[1] / "configs"
    source_files = {
        "content_parsing": "brisbane_baylands_2025_deir_task03c_appendix_p_v2.json",
        "heading_evidence_parsing": "brisbane_baylands_2025_deir_task03e_appendix_p_v1.json",
        "record_mapping": "brisbane_baylands_2025_deir_task03d_appendix_p_v1.json",
        "hierarchy_inference": (
            "brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json"
        ),
        "document_structure": "brisbane_baylands_2025_deir_task03e4_semantic_v1.json",
        "document_reference_linking": (
            "brisbane_baylands_2025_deir_task03e5_cross_references_human_v2.json"
        ),
    }
    values = {
        role: json.loads((source_root / name).read_text()) for role, name in source_files.items()
    }
    producer_root = "pipelines/brisbane_baylands/task_03g2_owner_candidates/producers"
    canonical_root = "pipelines/brisbane_baylands/task_03g2_owner_candidates/record_mapping"
    correction_root = "pipelines/brisbane_baylands/task_03g2_owner_candidates/correction"
    for role in ("content_parsing", "heading_evidence_parsing"):
        values[role]["artifact_relative_root"] = producer_root
    values["record_mapping"].update(
        producer_artifact_relative_root=producer_root,
        producer_run_id="prv1-" + zero,
        artifact_relative_root=canonical_root,
    )
    values["hierarchy_inference"].update(
        publication_authorization="machine_validation",
        producer_artifact_relative_root=producer_root,
        producer_run_id="prv1-" + zero,
        artifact_relative_root=correction_root,
        bounded_acceptance_artifact_relative_root=None,
        bounded_acceptance_config_relative_path=None,
    )
    values["document_structure"].update(
        control_profile="strict_quality_gate",
        baseline_candidate_relative_root=canonical_root + "/exv1-" + zero,
        baseline_candidate_id="exv1-" + zero,
        baseline_producer_relative_root=producer_root,
        baseline_producer_run_id="prv1-" + zero,
        hierarchy_producer_relative_root=producer_root,
        hierarchy_producer_run_id="prv1-" + zero,
        hierarchy_candidate_relative_root=correction_root + "/hcorv1-" + zero,
        hierarchy_candidate_id="hcorv1-" + zero,
        bounded_acceptance_relative_path=None,
        bounded_acceptance_policy_relative_path=None,
        producer_comparison_relative_path=None,
        artifact_relative_root=canonical_root,
        expectations=None,
    )
    values["document_reference_linking"].update(
        upstream_candidate_id="exv1-" + zero,
        upstream_completion_sha256=zero,
        upstream_inventory_sha256=zero,
        artifact_relative_root=canonical_root,
    )
    data_root = tmp_path / "data"
    manifest_path = (
        data_root / values["document_reference_linking"]["source_manifest_relative_path"]
    )
    write_json_atomic(manifest_path, {"fixture": "sealed"})
    values["document_reference_linking"]["source_manifest_sha256"] = sha256_file(manifest_path)
    paths = {}
    for role, value in values.items():
        path = config_root / f"{role}.json"
        write_json_atomic(path, value)
        paths[role] = path
    return ProcessConfigs(**paths)


def _completion(data_root: Path, family: str, candidate_id: str) -> Path:
    root = (
        data_root / "pipelines/brisbane_baylands/task_03g2_owner_candidates" / family / candidate_id
    )
    completion = root / "records/completion_record.json"
    write_json_atomic(completion, {"candidate_id": candidate_id})
    write_json_atomic(root / "records/artifact_inventory.json", {"files": []})
    return completion
