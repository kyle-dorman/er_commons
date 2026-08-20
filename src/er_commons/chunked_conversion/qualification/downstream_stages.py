"""Producer and record-stage execution for Gate C downstream qualification."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import read_json_object, sha256_file, write_json_atomic
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.downstream_configuration import (
    prepared_for_aggregate,
    qualification_templates,
)
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    AGGREGATE_ID,
    QUALIFICATION_PRODUCER_ID,
    QUALIFICATION_STAGE_IDS,
    SOURCE_ID,
    DownstreamPaths,
)
from er_commons.document_parsing.content_parsing.conversion_seal import (
    deep_audit_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.derived_publication import (
    DerivedPublicationProgress,
    build_and_publish_derived,
)
from er_commons.document_parsing.content_parsing.evidence import verify_completed_run
from er_commons.document_parsing.content_parsing.services import ContentParsingServices
from er_commons.document_publication.fresh_lineage import FreshLineageBinder
from er_commons.document_publication.process_validation import (
    ProcessCompletions,
    validate_process_lineage,
)
from er_commons.document_records import (
    link_document_references,
    map_document_records,
    map_document_structure,
)
from er_commons.hierarchy_inference import infer_document_hierarchy


def qualify_producer(paths: DownstreamPaths) -> Path:
    """Reuse or build routing and clean tables from the verified aggregate only."""
    sealed = deep_audit_conversion_bundle(paths.aggregate, AGGREGATE_ID)
    prepared = prepared_for_aggregate(paths)
    _require_equal(
        "producer_identity",
        prepared.identity.run_id,
        QUALIFICATION_PRODUCER_ID,
        paths.downstream,
    )
    task_root = paths.downstream / "document_parse_evidence"
    final_root = task_root / QUALIFICATION_PRODUCER_ID
    if final_root.exists():
        return verify_completed_run(final_root, QUALIFICATION_PRODUCER_ID)
    services = ContentParsingServices()
    completion = build_and_publish_derived(
        data_root=paths.data_root,
        task_root=task_root,
        config_path=paths.config("content_parsing"),
        prepared=prepared,
        sealed_conversion=sealed,
        services=services,
        started=services.monotonic(),
        progress=DerivedPublicationProgress(),
    )
    return verify_completed_run(completion.parents[1], QUALIFICATION_PRODUCER_ID)


def qualify_records(paths: DownstreamPaths) -> ProcessCompletions:
    """Build the four descendants, validate lineage, and record exact completions."""
    producer_completion = qualify_producer(paths)
    binder = _lineage_binder(paths)
    binder.initial_configs()
    record_completion = map_document_records(
        paths.data_root,
        binder.canonical_config(producer_completion),
        config_identity_path=paths.config("record_mapping"),
    )
    hierarchy_completion = infer_document_hierarchy(
        paths.data_root,
        binder.correction_config(producer_completion),
        config_identity_path=paths.config("hierarchy_inference"),
    )
    semantic_config = binder.semantic_config(
        baseline_completion=producer_completion,
        hierarchy_completion=producer_completion,
        canonical_completion=record_completion,
        correction_completion=hierarchy_completion,
    )
    structure_completion = map_document_structure(
        paths.data_root,
        semantic_config,
        config_identity_path=paths.config("document_structure"),
    )
    reference_completion = link_document_references(
        paths.data_root,
        binder.cross_reference_config(structure_completion),
        config_identity_path=paths.config("document_reference_linking"),
    )
    completions = ProcessCompletions(
        content_parsing=producer_completion,
        heading_evidence_parsing=producer_completion,
        record_mapping=record_completion,
        hierarchy_inference=hierarchy_completion,
        document_structure=structure_completion,
        document_reference_linking=reference_completion,
    )
    validate_expected_stage_completions(completions)
    _validate_lineage(paths, binder, completions)
    _write_completion_refs(paths, completions)
    return completions


def validate_expected_stage_completions(completions: ProcessCompletions) -> None:
    """Reject a transplanted or corrupt completion set before publication."""
    expected = {
        "stable_content_evidence": QUALIFICATION_PRODUCER_ID,
        "heading_evidence": QUALIFICATION_PRODUCER_ID,
        **QUALIFICATION_STAGE_IDS,
    }
    for role, completion in completions.as_dict().items():
        if not completion.is_file():
            _fail("completion_exists", completion, "file", "missing", role=role)
        observed = completion.parents[1].name
        _require_equal("completion_identity", observed, expected[role], completion, role=role)
        payload = read_json_object(completion)
        if payload.get("status") not in {"complete", "complete_with_warnings"}:
            _fail(
                "completion_status",
                completion,
                ["complete", "complete_with_warnings"],
                payload.get("status"),
                role=role,
            )


def _lineage_binder(paths: DownstreamPaths) -> FreshLineageBinder:
    return FreshLineageBinder(
        data_root=paths.data_root,
        project_root=paths.project_root,
        source_id=SOURCE_ID,
        templates=qualification_templates(paths),
        attempt_root=paths.downstream / "document_process_attempt",
    )


def _validate_lineage(
    paths: DownstreamPaths, binder: FreshLineageBinder, completions: ProcessCompletions
) -> None:
    try:
        validate_process_lineage(
            data_root=paths.data_root,
            source_id=SOURCE_ID,
            hierarchy_disposition={
                "source_id": SOURCE_ID,
                "authority": "machine_validation",
                "authorization_relative_path": None,
            },
            configs=binder.effective_configs(),
            completions=completions,
        )
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise QualificationError(
            "stage_lineage",
            stage="downstream_records",
            path=paths.downstream.as_posix(),
            expected="fresh aggregate descendant chain",
            actual=str(error),
            context={"source_id": SOURCE_ID},
        ) from error


def _write_completion_refs(paths: DownstreamPaths, completions: ProcessCompletions) -> None:
    write_json_atomic(
        paths.downstream / "record_stage_completions.json",
        {
            role: {
                "path": path.relative_to(paths.data_root).as_posix(),
                "sha256": sha256_file(path),
            }
            for role, path in completions.as_dict().items()
        },
    )


def _require_equal(
    code: str, actual: object, expected: object, path: Path, *, role: str | None = None
) -> None:
    if actual != expected:
        _fail(code, path, expected, actual, role=role)


def _fail(
    code: str, path: Path, expected: object, actual: object, *, role: str | None = None
) -> None:
    raise QualificationError(
        code,
        stage="downstream_records",
        path=path.as_posix(),
        expected=expected,
        actual=actual,
        context={"role": role, "source_id": SOURCE_ID},
    )


__all__ = ["qualify_producer", "qualify_records", "validate_expected_stage_completions"]
