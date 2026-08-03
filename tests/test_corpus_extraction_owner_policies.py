"""Focused tests for owner inputs, authorization, and warning handoffs."""

from __future__ import annotations

from pathlib import Path

import pytest

from er_commons.corpus_extraction.config import load_run_spec
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
            disposition={"authority": "strict_quality_gate"},
            correction_config={"publication_authorization": "bounded_acceptance"},
            semantic_config={"bounded_acceptance_relative_path": relative.as_posix()},
            correction_id="hcorv1-test",
            correction_config_path=config,
        )


def test_resource_preflight_rejects_effective_producer_drift(tmp_path: Path) -> None:
    spec, _digest = load_run_spec(
        Path("configs/brisbane_baylands_2025_deir_task03f2_document_stage_v1.json")
    )
    drifted = spec.model_copy(
        update={
            "resource_policy": spec.resource_policy.model_copy(
                update={"cpu_threads_per_document": 5}
            )
        }
    )
    configured = OwnerConfigs(**spec.content_owners("deir_appendix_p").model_dump())
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
