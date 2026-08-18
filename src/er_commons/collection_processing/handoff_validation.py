"""Read-only validation of a published collection handoff."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.semantic_validation import (
    CollectionArtifactReader,
    validate_collection_bundle,
)
from er_commons.document_publication.candidates import verify_identity_and_upstreams
from er_commons.document_publication.records import (
    DocumentCompletion,
    DocumentIdentityRecord,
    SourceIdentity,
)
from er_commons.document_publication.storage import verify_candidate


@dataclass(frozen=True)
class VerifiedHandoff:
    """Compact result from validation that never rebuilds or mutates a candidate."""

    scope_id: str
    handoff_id: str
    status: str
    verified_document_count: int
    unavailable_source_count: int
    task04_status: str


def validate_collection_handoff(
    *,
    extraction_root: Path,
    scope_id: str,
    schema_path: Path,
    data_root: Path | None = None,
) -> VerifiedHandoff:
    """Verify the v2 bundle and every successful document candidate in place."""
    root = extraction_root.resolve()
    bundle = _json_object(root / "scopes" / scope_id / "contract_bundle.json")
    checked_data_root = (
        data_root.resolve() if data_root is not None else _infer_data_root(root, bundle)
    )
    if not root.is_relative_to(checked_data_root):
        raise ValueError("extraction root must be contained by the data root")
    schema = _json_object(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(bundle)
    validate_collection_bundle(bundle, CollectionArtifactReader(root))

    accounting = _object(bundle, "accounting")
    handoff = _object(bundle, "handoff")
    if accounting.get("scope_id") != scope_id:
        raise ValueError("handoff scope differs from its published directory")
    if handoff.get("task04_status") != "not_evaluated":
        raise ValueError("Task 03 handoff may not claim Task 04 evaluation")

    completions = cast(list[JsonObject], bundle["document_completions"])
    for completion in completions:
        _verify_document_candidate(checked_data_root, root, bundle, completion)
    unavailable = cast(list[JsonObject], _object(bundle, "target_index")["unavailable_sources"])
    return VerifiedHandoff(
        scope_id=scope_id,
        handoff_id=str(handoff["handoff_id"]),
        status=str(handoff["status"]),
        verified_document_count=len(completions),
        unavailable_source_count=len(unavailable),
        task04_status="not_evaluated",
    )


def _verify_document_candidate(
    data_root: Path,
    root: Path,
    bundle: JsonObject,
    completion_record: JsonObject,
) -> None:
    completion = DocumentCompletion.model_validate(completion_record)
    candidate_root = (
        root / "documents" / completion.source.source_id / completion.candidate_id
    ).resolve()
    if not candidate_root.is_relative_to(root):
        raise ValueError("document candidate path escapes extraction root")
    expected_inventory = (
        f"documents/{completion.source.source_id}/{completion.candidate_id}/"
        "records/artifact_inventory.json"
    )
    if str(completion.candidate_inventory.path) != expected_inventory:
        raise ValueError("document completion inventory path differs from candidate identity")
    completion_path = verify_candidate(
        candidate_root,
        completion.candidate_id,
        SourceIdentity.model_validate(completion.source),
    )
    if _json_object(completion_path) != completion_record:
        raise ValueError("embedded document completion differs from published candidate")
    identity = DocumentIdentityRecord.model_validate_json(
        (candidate_root / "records" / "document_identity.json").read_bytes()
    )
    if (
        identity.production_extraction_id != bundle.get("production_extraction_id")
        or identity.candidate_id != completion.candidate_id
        or identity.source != completion.source
    ):
        raise ValueError("document identity differs from collection handoff")
    verify_identity_and_upstreams(
        candidate_root,
        identity=identity.model_dump(mode="json"),
        data_root=data_root,
    )


def _json_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _object(value: JsonObject, field: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        raise ValueError(f"handoff field must be an object: {field}")
    return observed


def _infer_data_root(extraction_root: Path, bundle: JsonObject) -> Path:
    """Find the unique ancestor that resolves every sealed product completion."""
    references: list[JsonObject] = []
    for completion_record in cast(list[JsonObject], bundle["document_completions"]):
        completion = DocumentCompletion.model_validate(completion_record)
        identity_path = (
            extraction_root
            / "documents"
            / completion.source.source_id
            / completion.candidate_id
            / "records/document_identity.json"
        )
        identity = DocumentIdentityRecord.model_validate_json(identity_path.read_bytes())
        references.extend(
            value.model_dump(mode="json") for value in identity.stage_completions.values()
        )
    if not references:
        return extraction_root
    matches = [
        ancestor
        for ancestor in (extraction_root, *extraction_root.parents)
        if all(_reference_matches(ancestor, reference) for reference in references)
    ]
    if len(matches) != 1:
        raise ValueError("could not infer one data root from upstream completion seals")
    return matches[0]


def _reference_matches(root: Path, reference: JsonObject) -> bool:
    path = (root / str(reference["path"])).resolve()
    return bool(
        path.is_relative_to(root)
        and path.is_file()
        and hashlib.sha256(path.read_bytes()).hexdigest() == reference["sha256"]
    )
