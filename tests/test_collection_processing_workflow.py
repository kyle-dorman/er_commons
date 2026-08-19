"""Synthetic end-to-end gates for Task 03F.3 stage-two runtime."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from collection_processing_test_support import write_collection_spec, write_cross_reference_inputs
from document_publication_test_support import _result, _workspace

from er_commons.collection_processing.handoff_validation import validate_collection_handoff
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.collection_processing.publication import StageHooks
from er_commons.collection_processing.workflow import CollectionHooks, assemble_collection_handoff
from er_commons.document_publication.process import ProcessOutcome
from er_commons.document_publication.workflow import publish_document


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_source", "catalog differs from the exact collection scope"),
        ("wrong_byte_size", "catalog source identity differs from manifest"),
    ],
)
def test_collection_preflight_rejects_incomplete_or_byte_mismatched_catalog(
    tmp_path: Path, mutation: str, message: str
) -> None:
    data_root, _document_spec = _workspace(tmp_path)
    collection_spec = write_collection_spec(tmp_path, data_root)
    catalog_path = data_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text())
    if mutation == "missing_source":
        catalog["sources"].pop()
    else:
        catalog["sources"][0]["source"]["byte_size"] += 1
    catalog_path.write_text(json.dumps(catalog))

    with pytest.raises(ValueError, match=message):
        prepare_collection_run(data_root, collection_spec)


def test_run_scope_continues_terminal_failure_and_reuses_exact_outputs(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="er_commons.collection_processing.document_evidence")
    data_root, document_spec = _workspace(tmp_path)
    collection_spec = write_collection_spec(tmp_path, data_root)

    def runner(root: Path, spec: Path, source_id: str) -> Path:
        if source_id == "beta":

            def fail(*_args: object) -> ProcessOutcome:
                raise RuntimeError("synthetic terminal source failure")

            return publish_document(root, spec, source_id, executor=fail)
        result = _result(tmp_path, "alpha")
        write_cross_reference_inputs(Path(result.final_candidate_root), source_id)
        return publish_document(
            root,
            spec,
            source_id,
            executor=lambda *_args: ProcessOutcome(result, False, 0, ""),
        )

    first = assemble_collection_handoff(data_root, collection_spec, document_runner=runner)
    first_bytes = first.read_bytes()
    second = assemble_collection_handoff(data_root, collection_spec, document_runner=runner)

    assert any(
        "Document execution failed before terminal observation source=beta" in record.getMessage()
        for record in caplog.records
    )
    assert any(
        "Retained terminal evidence allowed collection continuation source=beta"
        in record.getMessage()
        for record in caplog.records
    )

    assert second == first
    assert second.read_bytes() == first_bytes
    handoff = json.loads(second.read_bytes())
    assert handoff["status"] == "blocked"
    assert handoff["task04_status"] == "not_evaluated"
    bundle = json.loads((second.parents[3] / "contract_bundle.json").read_bytes())
    assert bundle["accounting"]["counts"]["failed_terminal"] == 1
    assert bundle["resolution_completion"]["counts"] == {
        "total": 1,
        "resolved": 0,
        "ambiguous": 0,
        "unresolved": 1,
    }
    assert (
        bundle["resolution_completion"]["resolutions"][0]["unresolved_reason"]
        == "target_source_failed"
    )
    assert (
        bundle["resolution_completion"]["candidate_inventories_before"]
        == bundle["resolution_completion"]["candidate_inventories_after"]
    )
    bundle["resolution_completion"]["counts"]["total"] += 1
    bundle_path = second.parents[3] / "contract_bundle.json"
    bundle_path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError, match="link counts differ"):
        validate_collection_handoff(
            data_root=data_root,
            extraction_root=data_root / "pipelines/test/task_03f",
            scope_id=second.parents[3].name,
            schema_path=Path(
                "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
            ),
        )


def test_publication_after_rename_is_reconciled_without_clobber(tmp_path: Path) -> None:
    data_root, document_spec = _workspace(tmp_path)
    collection_spec = write_collection_spec(tmp_path, data_root)
    raised = False

    def runner(root: Path, spec: Path, source_id: str) -> Path:
        result = _result(tmp_path, source_id, pages=2 if source_id == "alpha" else 3)
        write_cross_reference_inputs(Path(result.final_candidate_root), source_id)
        return publish_document(
            root,
            spec,
            source_id,
            executor=lambda *_args: ProcessOutcome(result, False, 0, ""),
        )

    def interrupt(_path: Path) -> None:
        nonlocal raised
        if not raised:
            raised = True
            raise RuntimeError("synthetic post-publication interruption")

    with pytest.raises(RuntimeError, match="post-publication"):
        assemble_collection_handoff(
            data_root,
            collection_spec,
            document_runner=runner,
            hooks=CollectionHooks(target_index=StageHooks(after_publish=interrupt)),
        )

    completion = assemble_collection_handoff(data_root, collection_spec, document_runner=runner)
    assert json.loads(completion.read_bytes())["status"] == "ready"
    bundle = json.loads((completion.parents[3] / "contract_bundle.json").read_bytes())
    assert bundle["resolution_completion"]["resolutions"][0]["status"] == "resolved"
    assert bundle["resolution_completion"]["resolutions"][0]["lookup_key"] == "report beta"
    assert bundle["target_index"]["document_targets"][1]["source_id"] == "beta"
    assert {row["target_type"] for row in bundle["target_index"]["entries"]} == {
        "document",
        "section",
        "table",
        "figure",
        "page",
    }
    assert [
        Path(reference["path"]).name
        for reference in bundle["target_index"]["eligible_candidates"][0]["target_records_ref"]
    ] == [
        "documents.jsonl",
        "sections.jsonl",
        "tables.jsonl",
        "figures.jsonl",
        "pages.jsonl",
    ]
    verified = validate_collection_handoff(
        data_root=data_root,
        extraction_root=data_root / "pipelines/test/task_03f",
        scope_id=completion.parents[3].name,
        schema_path=Path(
            "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
        ),
    )
    assert verified.status == "ready"
    assert verified.verified_document_count == 2
    assert verified.task04_status == "not_evaluated"

    (data_root / "owner-alpha/records/completion_record.json").write_text('{"status":"changed"}\n')
    with pytest.raises(ValueError, match="upstream seal differs"):
        validate_collection_handoff(
            data_root=data_root,
            extraction_root=data_root / "pipelines/test/task_03f",
            scope_id=completion.parents[3].name,
            schema_path=Path(
                "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
            ),
        )


def test_target_index_rejects_alias_absent_from_all_sealed_target_streams(
    tmp_path: Path,
) -> None:
    data_root, document_spec = _workspace(tmp_path)
    collection_spec = write_collection_spec(tmp_path, data_root)

    def runner(root: Path, spec: Path, source_id: str) -> Path:
        result = _result(tmp_path, source_id, pages=2 if source_id == "alpha" else 3)
        candidate_root = Path(result.final_candidate_root)
        write_cross_reference_inputs(candidate_root, source_id)
        if source_id == "beta":
            aliases_path = candidate_root / "canonical/target_aliases.jsonl"
            aliases = [json.loads(line) for line in aliases_path.read_text().splitlines()]
            aliases[1]["targets"][0]["target_id"] = "fixture-beta-missing"
            aliases_path.write_text("".join(json.dumps(row) + "\n" for row in aliases))
        return publish_document(
            root,
            spec,
            source_id,
            executor=lambda *_args: ProcessOutcome(result, False, 0, ""),
        )

    with pytest.raises(ValueError, match="alias target is absent"):
        assemble_collection_handoff(data_root, collection_spec, document_runner=runner)


def test_interrupted_staging_is_cancelled_before_retry(tmp_path: Path) -> None:
    data_root, document_spec = _workspace(tmp_path)
    collection_spec = write_collection_spec(tmp_path, data_root)
    raised = False

    def runner(root: Path, spec: Path, source_id: str) -> Path:
        result = _result(tmp_path, source_id, pages=2 if source_id == "alpha" else 3)
        write_cross_reference_inputs(Path(result.final_candidate_root), source_id)
        return publish_document(
            root,
            spec,
            source_id,
            executor=lambda *_args: ProcessOutcome(result, False, 0, ""),
        )

    def interrupt(_path: Path) -> None:
        nonlocal raised
        if not raised:
            raised = True
            raise RuntimeError("synthetic pre-publication interruption")

    with pytest.raises(RuntimeError, match="pre-publication"):
        assemble_collection_handoff(
            data_root,
            collection_spec,
            document_runner=runner,
            hooks=CollectionHooks(accounting=StageHooks(before_publish=interrupt)),
        )

    completion = assemble_collection_handoff(data_root, collection_spec, document_runner=runner)
    bundle = json.loads((completion.parents[3] / "contract_bundle.json").read_bytes())
    accounting_attempts = [
        row for row in bundle["collection_stage_attempts"] if row["stage_type"] == "accounting"
    ]
    assert [row["disposition"] for row in accounting_attempts] == ["cancelled", "complete"]
