"""Completion-last document publication from verified qualification descendants."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from er_commons.artifact_io import sha256_file
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.downstream_configuration import (
    qualification_document_spec,
)
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    QUALIFICATION_DOCUMENT_ID,
    SOURCE_ID,
    DownstreamPaths,
)
from er_commons.chunked_conversion.qualification.downstream_stages import qualify_records
from er_commons.document_publication.attempts import AttemptSession, next_attempt_number
from er_commons.document_publication.candidates import find_reusable_candidate
from er_commons.document_publication.hooks import WorkflowHooks
from er_commons.document_publication.observability import record_resource_enforcement
from er_commons.document_publication.preflight import prepare_document_run
from er_commons.document_publication.process import ProcessOutcome
from er_commons.document_publication.process_observations import (
    collect_process_warnings,
    content_parse_observations,
    content_parse_page_count,
)
from er_commons.document_publication.process_validation import ProcessCompletions
from er_commons.document_publication.publication import complete_attempt
from er_commons.document_publication.records import (
    ArtifactRef,
    DocumentCompletion,
    PipelineResult,
)


def qualify_publication(paths: DownstreamPaths) -> Path:
    """Reuse or publish the exact expected qualification document candidate."""
    completions = qualify_records(paths)
    run = prepare_document_run(
        paths.data_root,
        qualification_document_spec(paths),
        SOURCE_ID,
    )
    reusable = find_reusable_candidate(run)
    if reusable is not None:
        return validate_publication_completion(reusable)
    result = _pipeline_result(paths, completions)
    attempt = AttemptSession.start(run, next_attempt_number(run))
    record_resource_enforcement(
        attempt.root,
        transaction_id=attempt.transaction_id,
        enforcement=result.resource_enforcement,
    )
    completion = complete_attempt(
        run,
        attempt,
        ProcessOutcome(result=result, timed_out=False, return_code=0, stderr=""),
        hooks=WorkflowHooks(),
    )
    if completion is None:
        _fail(
            "publication_gate",
            attempt.root,
            "completed document candidate",
            "publication rejected",
        )
    return validate_publication_completion(completion)


def validate_publication_completion(completion: Path) -> Path:
    """Require the expected document ID and strict native-v2 completion record."""
    if not completion.is_file():
        _fail("publication_completion_exists", completion, "file", "missing")
    try:
        record = DocumentCompletion.model_validate_json(completion.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise QualificationError(
            "publication_completion_record",
            stage="downstream_publication",
            path=completion.as_posix(),
            expected="strict native-v2 document completion",
            actual=str(error),
        ) from error
    observed = completion.parents[1].name
    if record.candidate_id != QUALIFICATION_DOCUMENT_ID or observed != QUALIFICATION_DOCUMENT_ID:
        _fail(
            "publication_identity",
            completion,
            QUALIFICATION_DOCUMENT_ID,
            {"record": record.candidate_id, "directory": observed},
        )
    return completion


def _pipeline_result(paths: DownstreamPaths, completions: ProcessCompletions) -> PipelineResult:
    raw_status, errors = content_parse_observations(completions.content_parsing)
    return PipelineResult(
        source_id=SOURCE_ID,
        raw_docling_status=raw_status,
        processed_pages=list(range(1, content_parse_page_count(completions.content_parsing) + 1)),
        structured_errors=errors,
        warnings=collect_process_warnings(completions),
        final_candidate_root=str(completions.document_reference_linking.parents[1]),
        stage_completions={
            role: ArtifactRef(
                path=path.relative_to(paths.data_root).as_posix(),
                sha256=sha256_file(path),
            )
            for role, path in completions.as_dict().items()
        },
        stage_timings={role: 0.0 for role in _stage_roles()},
        resource_enforcement="validated_before_document_processes",
    )


def _stage_roles() -> tuple[str, ...]:
    return (
        "content_parsing",
        "heading_evidence_parsing",
        "record_mapping",
        "hierarchy_inference",
        "document_structure",
        "document_reference_linking",
    )


def _fail(code: str, path: Path, expected: object, actual: object) -> NoReturn:
    raise QualificationError(
        code,
        stage="downstream_publication",
        path=path.as_posix(),
        expected=expected,
        actual=actual,
        context={"source_id": SOURCE_ID},
    )


__all__ = ["qualify_publication", "validate_publication_completion"]
