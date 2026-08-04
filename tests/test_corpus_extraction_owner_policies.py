"""Focused tests for owner inputs, authorization, and warning handoffs."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from corpus_extraction_test_support import _workspace

from er_commons.corpus_extraction.config import HierarchyDisposition, load_run_spec
from er_commons.corpus_extraction.content_owners import _timed
from er_commons.corpus_extraction.lineage_preflight import (
    ProducerLineage,
    validate_lineage_bindings,
)
from er_commons.corpus_extraction.lineage_validation import (
    _validate_current_hierarchy_identity,
)
from er_commons.corpus_extraction.owner_inputs import (
    OwnerConfigs,
    verify_owner_resources,
)
from er_commons.corpus_extraction.owner_observations import collect_owner_warnings
from er_commons.corpus_extraction.owner_validation import (
    OwnerCompletions,
    validate_hierarchy_authorization,
)
from er_commons.source_freeze import sha256_file, write_json_atomic


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
    spec, _digest = load_run_spec(spec_path)
    drifted = spec.model_copy(
        update={
            "resource_policy": spec.resource_policy.model_copy(
                update={"cpu_threads_per_document": 5}
            )
        }
    )
    configured = OwnerConfigs(
        baseline_producer=Path("configs/brisbane_baylands_2025_deir_task03c_appendix_p_v2.json"),
        hierarchy_producer=Path("configs/brisbane_baylands_2025_deir_task03e_appendix_p_v1.json"),
        canonical=Path("configs/brisbane_baylands_2025_deir_task03d_appendix_p_v1.json"),
        hierarchy_correction=Path(
            "configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json"
        ),
        semantic=Path("configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json"),
        cross_references=Path(
            "configs/brisbane_baylands_2025_deir_task03e5_cross_references_human_v2.json"
        ),
    )
    with pytest.raises(ValueError, match="effective config"):
        verify_owner_resources(configured, drifted, data_root=tmp_path)


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
    repeated = OwnerCompletions(
        baseline_producer=completion,
        hierarchy_producer=completion,
        canonical=completion,
        hierarchy_correction=completion,
        semantic=completion,
        cross_references=completion,
    )

    warnings = collect_owner_warnings(repeated)

    assert "hierarchy_correction warning_count: 1" in warnings
    assert "hierarchy_correction TOC_WARNING: retained ambiguity" in warnings


def test_owner_failure_persists_stage_qualified_diagnostics(tmp_path: Path) -> None:
    def fail() -> Path:
        raise RuntimeError("owner broke")

    with pytest.raises(RuntimeError, match="owner broke"):
        _timed(
            "semantic",
            {},
            fail,
            diagnostics_root=tmp_path,
            ordinal=5,
            data_root=tmp_path,
        )

    started = json.loads((tmp_path / "owner_stage_events/05_semantic_started.json").read_text())
    failed = json.loads((tmp_path / "owner_stage_events/05_semantic_failed.json").read_text())
    assert started["state"] == "started"
    assert failed["state"] == "failed"
    assert failed["error_class"] == "RuntimeError"


def test_lineage_preflight_rejects_predicted_producer_drift_before_pdf(
    tmp_path: Path,
) -> None:
    configs, disposition = _lineage_fixture(tmp_path)

    with pytest.raises(ValueError, match="before PDF work.*canonical baseline producer"):
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
    correction_sha = sha256_file(configs.hierarchy_correction)
    evidence_path = tmp_path / "data" / disposition.authorization_relative_path
    evidence = json.loads(evidence_path.read_text())
    evidence["candidate"]["identity"]["config_sha256"] = correction_sha
    write_json_atomic(evidence_path, evidence)
    configs.hierarchy_correction.write_text(
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
        "er_commons.hierarchy_correction.preflight.prepare_run",
        lambda *_args: SimpleNamespace(candidate_id=derived),
    )
    mismatches: list[str] = []

    _validate_current_hierarchy_identity(
        tmp_path,
        tmp_path / "hierarchy.json",
        {"hierarchy_candidate_id": configured},
        mismatches,
    )

    assert mismatches == [
        "semantic hierarchy candidate is stale for current code/config: "
        f"configured={configured}, derived={derived}"
    ]


def _lineage_fixture(tmp_path: Path) -> tuple[OwnerConfigs, HierarchyDisposition]:
    baseline = "prv1-" + "0" * 64
    hierarchy = "prv1-" + "2" * 64
    candidate = "hcorv1-" + "3" * 64
    canonical = tmp_path / "canonical.json"
    correction = tmp_path / "correction.json"
    semantic = tmp_path / "semantic.json"
    other = tmp_path / "other.json"
    canonical.write_text('{"producer_run_id":"' + baseline + '"}')
    correction.write_text(
        '{"producer_run_id":"' + hierarchy + '","publication_authorization":"bounded_acceptance"}'
    )
    authorization = Path("review") / candidate / "bounded_acceptance.json"
    semantic.write_text(
        json.dumps(
            {
                "baseline_producer_run_id": baseline,
                "hierarchy_producer_run_id": hierarchy,
                "baseline_candidate_id": "exv1-" + "4" * 64,
                "baseline_candidate_relative_root": ("pipelines/canonical/exv1-" + "4" * 64),
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
    configs = OwnerConfigs(
        baseline_producer=other,
        hierarchy_producer=other,
        canonical=canonical,
        hierarchy_correction=correction,
        semantic=semantic,
        cross_references=other,
    )
    disposition = HierarchyDisposition(
        source_id="alpha",
        authority="bounded_acceptance",
        authorization_relative_path=authorization,
    )
    return configs, disposition
