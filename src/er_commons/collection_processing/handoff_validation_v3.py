"""Read-only validation for collection-only v3 handoffs."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.authority_reference import AuthorityReference
from er_commons.collection_processing.artifact_reader import CollectionArtifactReader
from er_commons.collection_processing.authority_refs import CollectionArtifactResolver
from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.handoff_validation import (
    VerifiedHandoff,
    _json_object,
    _object,
)
from er_commons.collection_processing.imported_selection import (
    ImportedDocumentSelection,
    load_imported_document_selection,
)
from er_commons.collection_processing.production_identity import (
    validate_collection_production_identity,
)
from er_commons.collection_processing.semantic_validation import validate_collection_bundle


def validate_v3_collection_handoff(
    *,
    root: Path,
    scope_id: str,
    schema_path: Path,
    bundle: JsonObject,
    data_root: Path | None,
    document_input_root: Path | None,
) -> VerifiedHandoff:
    """Verify fresh collection products and exact retained document inputs."""
    data, documents = _authority_roots(root, data_root, document_input_root)
    resolver = CollectionArtifactResolver(
        document_input_root=documents, collection_output_root=root
    )
    schema = _json_object(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(bundle)
    validate_collection_bundle(bundle, CollectionArtifactReader(root))
    _reject_legacy_document_execution(bundle)
    accounting, handoff = _object(bundle, "accounting"), _object(bundle, "handoff")
    if accounting.get("scope_id") != scope_id:
        raise ValueError("handoff scope differs from its published directory")
    if handoff.get("task04_status") != "not_evaluated":
        raise ValueError("collection handoff may not claim Task 04 evaluation")
    selection, selection_ref = _validate_imported_documents(
        bundle, data_root=data, resolver=resolver
    )
    _validate_collection_identity(bundle, root=root, data_root=data, selection_ref=selection_ref)
    _validate_fresh_collection_attempts(bundle, root=root, scope_id=scope_id)
    unavailable = cast(list[JsonObject], _object(bundle, "target_index")["unavailable_sources"])
    return VerifiedHandoff(
        scope_id=scope_id,
        handoff_id=str(handoff["handoff_id"]),
        status=str(handoff["status"]),
        verified_document_count=len(selection.candidates),
        unavailable_source_count=len(unavailable),
        task04_status="not_evaluated",
    )


def _authority_roots(
    root: Path, data_root: Path | None, document_input_root: Path | None
) -> tuple[Path, Path]:
    if data_root is None or document_input_root is None:
        raise ValueError("v3 handoff requires explicit data and document input roots")
    data, documents = data_root.resolve(), document_input_root.resolve()
    if not root.is_relative_to(data):
        raise ValueError("extraction root must be contained by the data root")
    if not documents.is_relative_to(data):
        raise ValueError("document input root must be contained by the data root")
    return data, documents


def _reject_legacy_document_execution(bundle: JsonObject) -> None:
    fields = {
        "production_extraction_id",
        "state_events",
        "document_attempts",
        "document_completions",
        "downstream_replays",
    }
    if fields.intersection(bundle):
        raise ValueError("v3 handoff contains legacy document execution evidence")


def _validate_imported_documents(
    bundle: JsonObject,
    *,
    data_root: Path,
    resolver: CollectionArtifactResolver,
) -> tuple[ImportedDocumentSelection, AuthorityReference]:
    imported = _object(bundle, "imported_document_evidence")
    selection_ref = AuthorityReference.model_validate(bundle.get("imported_selection_ref"))
    if selection_ref.authority != "artifact_root":
        raise ValueError("v3 imported selection must use artifact-root authority")
    if imported.get("selection_ref") != selection_ref.model_dump(mode="json"):
        raise ValueError("imported document evidence names another selection reference")
    repository_root = Path(__file__).resolve().parents[3]
    path = selection_ref.resolve(repository_root=repository_root, artifact_root=data_root)
    selections = cast(list[JsonObject], imported.get("selections"))
    if len(selections) != 35:
        raise ValueError("v3 handoff requires exactly 35 imported document candidates")
    selection = load_imported_document_selection(
        path,
        expected_source_order=tuple(str(row.get("physical_source_id")) for row in selections),
        expected_sha256=str(bundle.get("imported_selection_sha256")),
        expected_byte_size=selection_ref.byte_size,
        resolver=resolver,
    )
    if not _selection_envelope_matches(selection, imported, selections):
        raise ValueError("imported document evidence differs from its frozen selection")
    return selection, selection_ref


def _selection_envelope_matches(
    selection: ImportedDocumentSelection,
    imported: JsonObject,
    selections: list[JsonObject],
) -> bool:
    return bool(
        selection.document_production_identity_ref.model_dump(mode="json")
        == imported.get("document_production_identity_ref")
        and selection.document_run_spec_ref.model_dump(mode="json")
        == imported.get("document_run_spec_ref")
        and [item.model_dump(mode="json") for item in selection.candidates] == selections
    )


def _validate_collection_identity(
    bundle: JsonObject,
    *,
    root: Path,
    data_root: Path,
    selection_ref: AuthorityReference,
) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    identity_ref = AuthorityReference.model_validate(
        bundle.get("collection_production_identity_ref")
    )
    if identity_ref.authority != "artifact_root":
        raise ValueError("v3 collection production identity must use artifact-root authority")
    identity_path = identity_ref.resolve(repository_root=repository_root, artifact_root=data_root)
    identity = validate_collection_production_identity(
        _json_object(identity_path),
        repository_root=repository_root,
        artifact_root=data_root,
        expected_imported_selection_ref=selection_ref,
        expected_output_namespace=root.relative_to(data_root).as_posix(),
    )
    if identity.collection_production_id != bundle.get("collection_production_id"):
        raise ValueError("collection production identity differs from handoff")


def _validate_fresh_collection_attempts(bundle: JsonObject, *, root: Path, scope_id: str) -> None:
    expected = _expected_stages(bundle, scope_id)
    grouped: dict[str, list[JsonObject]] = {stage: [] for stage in expected}
    attempts = bundle.get("collection_stage_attempts")
    if not isinstance(attempts, list):
        raise ValueError("v3 handoff lacks collection stage attempts")
    for value in attempts:
        if not isinstance(value, dict) or value.get("stage_type") not in grouped:
            raise ValueError("v3 handoff contains an unknown collection stage attempt")
        grouped[str(value["stage_type"])].append(cast(JsonObject, value))
    reader = CollectionArtifactReader(root)
    for stage, (stage_id, completion, directory) in expected.items():
        _validate_stage_chain(
            grouped[stage], stage, stage_id, completion, directory, scope_id, reader
        )


def _expected_stages(bundle: JsonObject, scope_id: str) -> dict[str, tuple[str, JsonObject, str]]:
    accounting, index = _object(bundle, "accounting"), _object(bundle, "target_index")
    links, handoff = _object(bundle, "resolution_completion"), _object(bundle, "handoff")
    return {
        "accounting": (scope_id, accounting, "accounting"),
        "target_index": (str(index.get("index_id")), index, "target_indexes"),
        "resolution": (str(links.get("resolution_id")), links, "resolutions"),
        "handoff": (str(handoff.get("handoff_id")), handoff, "handoffs"),
    }


def _validate_stage_chain(
    rows: list[JsonObject],
    stage: str,
    stage_id: str,
    completion: JsonObject,
    directory: str,
    scope_id: str,
    reader: CollectionArtifactReader,
) -> None:
    if not rows or [row.get("attempt") for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError(f"v3 {stage} attempts are absent or non-contiguous")
    if any(row.get("stage_id") != stage_id for row in rows):
        raise ValueError(f"v3 {stage} attempt names another stage identity")
    terminal, expected_path = (
        rows[-1],
        (f"scopes/{scope_id}/{directory}/{stage_id}/records/completion_record.json"),
    )
    if terminal.get("disposition") != "complete" or terminal.get("failure_class") is not None:
        raise ValueError(f"v3 {stage} stage did not finish successfully")
    reference = terminal.get("completion_ref")
    if not isinstance(reference, dict) or reference.get("path") != expected_path:
        raise ValueError(f"v3 {stage} completion is outside its fresh stage namespace")
    if reader.read_json(cast(JsonObject, reference)) != completion:
        raise ValueError(f"v3 {stage} attempt completion differs from its bundle record")
