"""Configuration transplant and aggregate identity binding for downstream qualification."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object, write_json_atomic
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    AGGREGATE_ID,
    SOURCE_ID,
    DownstreamPaths,
    JsonObject,
)
from er_commons.document_parsing.content_parsing.config import load_content_parsing_config
from er_commons.document_parsing.content_parsing.identity import (
    ContentParsingIdentity,
    build_content_parsing_identity,
    code_identity,
    parsing_code_paths,
)
from er_commons.document_parsing.content_parsing.preparation import prepare_content_parsing
from er_commons.document_parsing.table_reconstruction.pipeline import installed_table_environment
from er_commons.document_publication.process_inputs import ProcessConfigs

PROCESS_ROLES = (
    "content_parsing",
    "heading_evidence_parsing",
    "record_mapping",
    "hierarchy_inference",
    "document_structure",
    "document_reference_linking",
)


def transplant_process_config(
    role: str, payload: JsonObject, downstream_relative: Path
) -> JsonObject:
    """Move one copied process config into the isolated qualification namespace."""
    if role not in PROCESS_ROLES:
        _fail("known_process_role", role, PROCESS_ROLES, role)
    roots = {
        "content_parsing": "document_parse_evidence",
        "heading_evidence_parsing": "document_parse_evidence",
        "record_mapping": "document_records",
        "hierarchy_inference": "hierarchy_inference",
        "document_structure": "document_records",
        "document_reference_linking": "document_records",
    }
    transplanted = dict(payload)
    transplanted["artifact_relative_root"] = (downstream_relative / roots[role]).as_posix()
    if role in {"record_mapping", "hierarchy_inference"}:
        transplanted["producer_artifact_relative_root"] = (
            downstream_relative / "document_parse_evidence"
        ).as_posix()
    return transplanted


def qualification_templates(paths: DownstreamPaths) -> ProcessConfigs:
    """Materialize no-clobber process templates under a qualification-only root."""
    downstream_relative = _relative(paths.downstream, paths.data_root)
    configured: dict[str, Path] = {}
    for role in PROCESS_ROLES:
        source = paths.config(role)
        payload = transplant_process_config(role, read_json_object(source), downstream_relative)
        target = paths.template_root / f"{role}.json"
        _write_once(target, payload, role)
        configured[role] = target
    return ProcessConfigs(**configured)


def qualification_document_spec(paths: DownstreamPaths) -> Path:
    """Copy the production-full document contract into the isolated namespace."""
    payload = read_json_object(paths.config("document_spec"))
    payload["artifact_relative_root"] = (
        _relative(paths.downstream, paths.data_root) / "document_publications"
    ).as_posix()
    target = paths.template_root / "document_spec.json"
    _write_once(target, payload, "document_spec")
    return target


def prepared_for_aggregate(paths: DownstreamPaths) -> Any:
    """Bind routing/table identity to the exact verified chunked aggregate."""
    config_path = paths.config("content_parsing")
    config, config_sha256 = load_content_parsing_config(config_path)
    prepared = prepare_content_parsing(
        paths.data_root,
        config=config,
        config_sha256=config_sha256,
    )
    identity_record = read_json_object(paths.aggregate / "records/conversion_identity.json")
    aggregate_identity = identity_record.get("identity")
    if not isinstance(aggregate_identity, dict):
        _fail(
            "aggregate_identity_payload",
            paths.aggregate / "records/conversion_identity.json",
            "object",
            aggregate_identity,
        )
    typed_identity = cast(dict[str, Any], aggregate_identity)
    producer_identity = build_content_parsing_identity(
        config=config,
        source=prepared.source,
        source_manifest_path=prepared.source_manifest_path,
        source_completion_path=prepared.source_manifest_path.parent / "completion_record.json",
        table_environment=installed_table_environment(),
        project_code=code_identity(
            parsing_code_paths(paths.project_root), repo_root=paths.project_root
        ),
        conversion_id=AGGREGATE_ID,
    )
    return replace(
        prepared,
        identity=producer_identity,
        conversion_identity=ContentParsingIdentity(
            run_id=AGGREGATE_ID,
            payload=typed_identity,
        ),
    )


def _write_once(path: Path, payload: JsonObject, role: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        existing = read_json_object(path)
        if existing != payload:
            _fail("template_collision", path, payload, existing)
        return
    write_json_atomic(path, payload)


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise QualificationError(
            "contained_qualification_path",
            stage="downstream_configuration",
            path=path.as_posix(),
            expected=f"under {root.resolve()}",
            actual=path.resolve().as_posix(),
        ) from error


def _fail(code: str, path: object, expected: object, actual: object) -> None:
    raise QualificationError(
        code,
        stage="downstream_configuration",
        path=str(path),
        expected=expected,
        actual=actual,
        context={"source_id": SOURCE_ID},
    )


__all__ = [
    "PROCESS_ROLES",
    "prepared_for_aggregate",
    "qualification_document_spec",
    "qualification_templates",
    "transplant_process_config",
]
