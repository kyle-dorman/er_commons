"""Seal and verify optional human-reviewed navigation evidence.

The materializer deliberately does not interpret navigation or perform links.  It
copies already prepared evidence into one checksum-closed namespace so both the
machine-only and reviewed linking paths can share the same downstream linker.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import (
    canonical_json_sha256,
    json_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    sha256_bytes,
    sha256_file,
)
from er_commons.document_records.document_references.relinking_config import (
    ExternalArtifactRef,
)
from er_commons.document_records.record_mapping.publication import build_inventory

JsonObject = dict[str, Any]
_SOURCE_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_BUNDLE_PREFIX = "navreviewv1-"
_BUNDLE_SCHEMA_VERSION = "er_commons.reviewed_navigation_bundle.v1"
_IDENTITY_SCHEMA_VERSION = "er_commons.reviewed_navigation_bundle_identity.v1"
_COMPLETION_SCHEMA_VERSION = "er_commons.reviewed_navigation_bundle_completion.v1"
_SEAL_POLICY = (
    "verify_identity_digest_source_coverage_upstream_refs_payload_ref_equality_"
    "inventory_closure_and_completion_last"
)
_PAYLOAD_PATHS = {
    "text_entries_ref": "navigation/text_entries.jsonl",
    "dispositions_ref": "navigation/dispositions.jsonl",
    "parent_relations_ref": "navigation/parent_relations.jsonl",
}
_ENTRY_ID_FIELDS = ("navigation_entry_id", "toc_text_entry_id", "entry_id")
_DISPOSITION_ID_FIELDS = ("disposition_id", "semantic_disposition_id")
_RELATION_CHILD_FIELDS = ("child_entry_id", "navigation_entry_id", "toc_text_entry_id")
_RELATION_PARENT_FIELDS = ("parent_entry_id", "parent_navigation_entry_id")
_MATERIALIZER_CODE_PATHS = (
    "src/er_commons/artifact_io.py",
    "src/er_commons/document_records/document_references/relinking_config.py",
    "src/er_commons/document_records/document_references/reviewed_navigation.py",
    "src/er_commons/document_records/record_mapping/publication.py",
)


@dataclass(frozen=True)
class ArtifactRoots:
    """The two roots named by external artifact-reference authorities."""

    repository: Path
    artifact_root: Path

    def resolved(self) -> ArtifactRoots:
        """Return normalized roots used for all containment checks."""
        return ArtifactRoots(self.repository.resolve(), self.artifact_root.resolve())


@dataclass(frozen=True)
class ReviewedNavigationMaterializationRequest:
    """Inputs required to seal one source-free reviewed-navigation bundle."""

    roots: ArtifactRoots
    output_parent: Path
    schema_path: Path
    source_ids: tuple[str, ...]
    review_decisions_ref: JsonObject
    semantic_view_ref: JsonObject
    text_entries_ref: JsonObject
    dispositions_ref: JsonObject
    parent_relations_ref: JsonObject


@dataclass(frozen=True)
class PublishedReviewedNavigation:
    """Paths and validated descriptor for one published bundle."""

    root: Path
    descriptor_path: Path
    descriptor: JsonObject


class ReviewedNavigationRequestSpec(BaseModel):
    """Portable JSON input for the maintained materialization command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = Field(pattern=r"^er_commons\.reviewed_navigation_request\.v1$")
    artifact_relative_root: str = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)
    bundle_schema_ref: ExternalArtifactRef
    review_decisions_ref: ExternalArtifactRef
    semantic_view_ref: ExternalArtifactRef
    text_entries_ref: ExternalArtifactRef
    dispositions_ref: ExternalArtifactRef
    parent_relations_ref: ExternalArtifactRef

    @model_validator(mode="after")
    def require_safe_output_and_sources(self) -> ReviewedNavigationRequestSpec:
        """Reject output traversal and duplicate source coverage before I/O."""
        relative = Path(self.artifact_relative_root)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("reviewed-navigation artifact root must be contained and relative")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("reviewed-navigation source IDs must be unique")
        return self


def materialize_reviewed_navigation_from_spec(
    *, data_root: Path, review_spec: Path, repository_root: Path | None = None
) -> PublishedReviewedNavigation:
    """Load one strict JSON request and publish its checksum-closed bundle."""
    spec = ReviewedNavigationRequestSpec.model_validate_json(review_spec.read_bytes())
    repo_root = (repository_root or Path(__file__).resolve().parents[4]).resolve()
    artifact_root = data_root.resolve()
    roots = ArtifactRoots(repository=repo_root, artifact_root=artifact_root)

    def resolve(reference: ExternalArtifactRef) -> Path:
        return reference.resolve(repository_root=repo_root, artifact_root=artifact_root)

    request = ReviewedNavigationMaterializationRequest(
        roots=roots,
        output_parent=artifact_root / spec.artifact_relative_root,
        schema_path=resolve(spec.bundle_schema_ref),
        source_ids=spec.source_ids,
        review_decisions_ref=spec.review_decisions_ref.model_dump(),
        semantic_view_ref=spec.semantic_view_ref.model_dump(),
        text_entries_ref=spec.text_entries_ref.model_dump(),
        dispositions_ref=spec.dispositions_ref.model_dump(),
        parent_relations_ref=spec.parent_relations_ref.model_dump(),
    )
    return materialize_reviewed_navigation(request)


def materialize_reviewed_navigation(
    request: ReviewedNavigationMaterializationRequest,
) -> PublishedReviewedNavigation:
    """Verify prepared inputs and completion-last publish an immutable bundle."""
    roots = request.roots.resolved()
    output_parent = request.output_parent.resolve()
    _require(
        output_parent.is_relative_to(roots.artifact_root),
        "output parent escapes artifact root",
    )
    source_ids = _validate_source_ids(request.source_ids)
    input_refs = {
        "review_decisions_ref": _validate_external_ref(request.review_decisions_ref, roots),
        "semantic_view_ref": _validate_external_ref(request.semantic_view_ref, roots),
        "text_entries_ref": _validate_external_ref(request.text_entries_ref, roots),
        "dispositions_ref": _validate_external_ref(request.dispositions_ref, roots),
        "parent_relations_ref": _validate_external_ref(request.parent_relations_ref, roots),
    }
    schema = _load_schema(request.schema_path)
    payload_bytes = {
        key: _resolve_ref(input_refs[key], roots).read_bytes() for key in _PAYLOAD_PATHS
    }
    _validate_navigation_records(payload_bytes, source_ids)
    payload_refs = {
        key: _bundle_ref(_PAYLOAD_PATHS[key], payload_bytes[key]) for key in _PAYLOAD_PATHS
    }
    preimage: JsonObject = {
        "schema_version": _IDENTITY_SCHEMA_VERSION,
        "source_ids_sha256": canonical_json_sha256(list(source_ids)),
        "review_decisions_ref": input_refs["review_decisions_ref"],
        "semantic_view_ref": input_refs["semantic_view_ref"],
        **payload_refs,
        "schema_sha256": sha256_file(request.schema_path),
        "materializer_code_sha256": _materializer_code_sha256(),
    }
    bundle_id = f"{_BUNDLE_PREFIX}{canonical_json_sha256(preimage)}"
    root = output_parent / bundle_id
    owned = {
        **{_PAYLOAD_PATHS[key]: payload_bytes[key] for key in _PAYLOAD_PATHS},
        "records/identity_preimage.json": json_bytes(preimage),
    }
    _publish_candidate(root, bundle_id, source_ids, owned, payload_refs)
    descriptor = _descriptor(
        roots=roots,
        root=root,
        bundle_id=bundle_id,
        source_ids=source_ids,
        preimage=preimage,
        payload_refs=payload_refs,
    )
    _validate_schema(schema, descriptor, request.schema_path)
    descriptor_path = output_parent / f"{bundle_id}.json"
    publish_bytes_no_clobber(descriptor_path, json_bytes(descriptor))
    return load_reviewed_navigation_bundle(
        descriptor_path,
        roots=roots,
        schema_path=request.schema_path,
    )


def load_reviewed_navigation_bundle(
    descriptor_path: Path,
    *,
    roots: ArtifactRoots,
    schema_path: Path,
    selected_source_ids: Sequence[str] | None = None,
) -> PublishedReviewedNavigation:
    """Load a bundle only after revalidating identity, evidence, and every seal."""
    resolved_roots = roots.resolved()
    descriptor = cast(JsonObject, read_json_object(descriptor_path))
    schema = _load_schema(schema_path)
    _validate_schema(schema, descriptor, schema_path)
    source_ids = _validate_source_ids(cast(Sequence[str], descriptor["source_ids"]))
    if selected_source_ids is not None:
        selected = set(_validate_source_ids(selected_source_ids))
        _require(set(source_ids) <= selected, "reviewed coverage exceeds selected sources")

    preimage = _object(descriptor.get("identity_preimage"), "identity_preimage")
    bundle_id = _string(descriptor.get("bundle_id"), "bundle_id")
    _require(
        bundle_id == f"{_BUNDLE_PREFIX}{canonical_json_sha256(preimage)}",
        "bundle identity differs from identity preimage",
    )
    _require(
        preimage.get("source_ids_sha256") == canonical_json_sha256(list(source_ids)),
        "source coverage digest differs",
    )
    _require(preimage.get("schema_sha256") == sha256_file(schema_path), "schema digest differs")
    _require(
        preimage.get("materializer_code_sha256") == _materializer_code_sha256(),
        "materializer code digest differs",
    )
    for name in ("review_decisions_ref", "semantic_view_ref"):
        _validate_external_ref(_object(preimage.get(name), name), resolved_roots)

    inventory_ref = _validate_external_ref(
        _object(descriptor.get("inventory_ref"), "inventory_ref"), resolved_roots
    )
    completion_ref = _validate_external_ref(
        _object(descriptor.get("completion_ref"), "completion_ref"), resolved_roots
    )
    inventory_path = _resolve_ref(inventory_ref, resolved_roots)
    completion_path = _resolve_ref(completion_ref, resolved_roots)
    root = completion_path.parent.parent
    _require(root == inventory_path.parent.parent, "terminal records have different roots")
    _require(root.name == bundle_id, "bundle path identity differs")
    payloads = _object(descriptor.get("payloads"), "payloads")
    payload_bytes: dict[str, bytes] = {}
    for name, relative in _PAYLOAD_PATHS.items():
        ref = _validate_bundle_ref(_object(payloads.get(name), name), relative)
        _require(ref == preimage.get(name), f"{name} differs from identity preimage")
        path = _resolve_bundle_ref(ref, root)
        _verify_file_ref(path, ref)
        payload_bytes[name] = path.read_bytes()

    _require(
        not any(path.is_symlink() for path in root.rglob("*")),
        "bundle contains a managed symlink",
    )
    inventory = read_json_object(inventory_path)
    _require(inventory == build_inventory(root), "bundle inventory closure differs")
    completion = read_json_object(completion_path)
    _validate_completion(completion, root, bundle_id, source_ids, inventory_path, payloads)
    _validate_navigation_records(payload_bytes, source_ids)
    return PublishedReviewedNavigation(root, descriptor_path.resolve(), descriptor)


def _publish_candidate(
    root: Path,
    bundle_id: str,
    source_ids: tuple[str, ...],
    owned: Mapping[str, bytes],
    payload_refs: Mapping[str, JsonObject],
) -> None:
    """Atomically publish an absent namespace or exactly reuse an existing one."""
    if root.exists():
        for relative, expected in owned.items():
            path = root / relative
            _require(path.is_file() and path.read_bytes() == expected, f"changed file: {relative}")
        return
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{bundle_id}.", dir=root.parent))
    try:
        for relative, content in owned.items():
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        inventory = build_inventory(staging)
        inventory_path = staging / "records/artifact_inventory.json"
        inventory_path.write_bytes(json_bytes(inventory))
        completion = {
            "schema_version": _COMPLETION_SCHEMA_VERSION,
            "bundle_id": bundle_id,
            "source_ids": list(source_ids),
            "status": "complete",
            "completion_last": True,
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "payloads": dict(payload_refs),
        }
        completion_path = staging / "records/completion_record.json"
        completion_path.write_bytes(json_bytes(completion))
        os.rename(staging, root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _descriptor(
    *,
    roots: ArtifactRoots,
    root: Path,
    bundle_id: str,
    source_ids: tuple[str, ...],
    preimage: JsonObject,
    payload_refs: Mapping[str, JsonObject],
) -> JsonObject:
    return {
        "schema_version": _BUNDLE_SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "source_ids": list(source_ids),
        "identity_preimage": preimage,
        "payloads": dict(payload_refs),
        "inventory_ref": _external_file_ref(
            root / "records/artifact_inventory.json", roots.artifact_root, "artifact_root"
        ),
        "completion_ref": _external_file_ref(
            root / "records/completion_record.json", roots.artifact_root, "artifact_root"
        ),
        "seal_policy": _SEAL_POLICY,
    }


def _validate_navigation_records(
    payload_bytes: Mapping[str, bytes], source_ids: tuple[str, ...]
) -> None:
    """Require exact declared coverage and valid entry/disposition relations."""
    rows = {name: _jsonl_objects(content, name) for name, content in payload_bytes.items()}
    allowed = set(source_ids)
    for name, records in rows.items():
        for index, record in enumerate(records):
            source_id = _string(record.get("source_id"), f"{name}[{index}].source_id")
            _require(source_id in allowed, f"{name} contains undeclared source: {source_id}")

    entries: dict[str, str] = {}
    entry_records: dict[str, JsonObject] = {}
    for index, record in enumerate(rows["text_entries_ref"]):
        entry_id = _identifier(record, _ENTRY_ID_FIELDS, f"text entry {index}")
        _require(entry_id not in entries, f"duplicate text entry: {entry_id}")
        entries[entry_id] = cast(str, record["source_id"])
        entry_records[entry_id] = record
    _require(set(entries.values()) == allowed, "text-entry source coverage differs")

    dispositions: dict[str, str] = {}
    for index, record in enumerate(rows["dispositions_ref"]):
        disposition_id = _identifier(record, _DISPOSITION_ID_FIELDS, f"disposition {index}")
        _require(disposition_id not in dispositions, f"duplicate disposition: {disposition_id}")
        dispositions[disposition_id] = cast(str, record["source_id"])
    for entry_id, source_id in entries.items():
        raw_disposition_id = entry_records[entry_id].get("table_disposition_id")
        if raw_disposition_id is not None:
            _require(
                dispositions.get(_string(raw_disposition_id, "table_disposition_id")) == source_id,
                f"text entry disposition differs: {entry_id}",
            )

    relations: set[str] = set()
    parent_by_child: dict[str, str] = {}
    for index, record in enumerate(rows["parent_relations_ref"]):
        relation_id = _identifier(
            record,
            ("relation_id", "parent_relation_id"),
            f"parent relation {index}",
        )
        _require(relation_id not in relations, f"duplicate parent relation: {relation_id}")
        relations.add(relation_id)
        child = _identifier(record, _RELATION_CHILD_FIELDS, f"parent relation {relation_id}")
        parent = _identifier(record, _RELATION_PARENT_FIELDS, f"parent relation {relation_id}")
        source_id = cast(str, record["source_id"])
        _require(child != parent, f"self-parent relation: {relation_id}")
        _require(entries.get(child) == source_id, f"parent relation child differs: {relation_id}")
        _require(entries.get(parent) == source_id, f"parent relation parent differs: {relation_id}")
        _require(child not in parent_by_child, f"multiple parent relations for entry: {child}")
        parent_by_child[child] = parent
    for child in parent_by_child:
        visited: set[str] = set()
        current: str | None = child
        while current is not None:
            _require(current not in visited, f"parent relation cycle contains entry: {current}")
            visited.add(current)
            current = parent_by_child.get(current)


def _validate_completion(
    completion: JsonObject,
    root: Path,
    bundle_id: str,
    source_ids: tuple[str, ...],
    inventory_path: Path,
    payloads: JsonObject,
) -> None:
    expected = {
        "schema_version": _COMPLETION_SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "source_ids": list(source_ids),
        "status": "complete",
        "completion_last": True,
        "artifact_inventory_sha256": sha256_file(inventory_path),
        "payloads": payloads,
    }
    _require(completion == expected, "completion record differs")
    _require(not any(root.rglob("*.part")), "bundle contains incomplete atomic writes")


def _load_schema(path: Path) -> JsonObject:
    schema = cast(JsonObject, read_json_object(path))
    Draft202012Validator.check_schema(schema)
    return schema


def _validate_schema(schema: JsonObject, value: JsonObject, path: Path) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(f"reviewed-navigation schema violation in {path}: {errors[0].message}")


def _validate_source_ids(values: Sequence[str]) -> tuple[str, ...]:
    source_ids = tuple(values)
    _require(bool(source_ids), "source coverage is empty")
    _require(len(source_ids) == len(set(source_ids)), "source coverage contains duplicates")
    for source_id in source_ids:
        _require(
            isinstance(source_id, str) and _SOURCE_ID.fullmatch(source_id) is not None,
            "invalid source ID",
        )
    return source_ids


def _validate_external_ref(ref: JsonObject, roots: ArtifactRoots) -> JsonObject:
    _require(ref.get("authority") in {"repository", "artifact_root"}, "invalid external authority")
    _require(set(ref) == {"authority", "path", "sha256", "byte_size"}, "artifact ref shape differs")
    path = _resolve_ref(ref, roots)
    _verify_file_ref(path, ref)
    return dict(ref)


def _resolve_ref(ref: Mapping[str, Any], roots: ArtifactRoots) -> Path:
    authority = ref.get("authority")
    root = roots.repository if authority == "repository" else roots.artifact_root
    relative = Path(_string(ref.get("path"), "artifact path"))
    _require(not relative.is_absolute() and ".." not in relative.parts, "unsafe artifact path")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root), "artifact path escapes authority root")
    return path


def _validate_bundle_ref(ref: JsonObject, expected_path: str) -> JsonObject:
    _require(set(ref) == {"authority", "path", "sha256", "byte_size"}, "bundle ref shape differs")
    _require(ref.get("authority") == "bundle", "owned payload authority differs")
    _require(ref.get("path") == expected_path, "owned payload path differs")
    return ref


def _resolve_bundle_ref(ref: Mapping[str, Any], root: Path) -> Path:
    relative = Path(_string(ref.get("path"), "bundle artifact path"))
    _require(not relative.is_absolute() and ".." not in relative.parts, "unsafe bundle path")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root), "bundle path escapes candidate root")
    return path


def _verify_file_ref(path: Path, ref: Mapping[str, Any]) -> None:
    _require(path.is_file(), f"referenced artifact is absent: {path}")
    byte_size = ref.get("byte_size")
    digest = ref.get("sha256")
    _require(isinstance(byte_size, int) and not isinstance(byte_size, bool), "invalid byte size")
    _require(path.stat().st_size == byte_size, f"artifact byte size differs: {path}")
    _require(
        isinstance(digest, str) and digest == sha256_file(path),
        f"artifact digest differs: {path}",
    )


def _external_file_ref(path: Path, root: Path, authority: str) -> JsonObject:
    resolved = path.resolve()
    _require(resolved.is_relative_to(root), "published artifact escapes declared root")
    return {
        "authority": authority,
        "path": resolved.relative_to(root).as_posix(),
        "sha256": sha256_file(resolved),
        "byte_size": resolved.stat().st_size,
    }


def _bundle_ref(path: str, content: bytes) -> JsonObject:
    return {
        "authority": "bundle",
        "path": path,
        "sha256": sha256_bytes(content),
        "byte_size": len(content),
    }


def _materializer_code_sha256() -> str:
    """Bind the complete, small code closure that shapes reviewed bundles."""
    repo_root = Path(__file__).resolve().parents[4]
    return canonical_json_sha256(
        [
            {"path": relative, "sha256": sha256_file(repo_root / relative)}
            for relative in _MATERIALIZER_CODE_PATHS
        ]
    )


def _jsonl_objects(content: bytes, label: str) -> list[JsonObject]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(
            f"reviewed-navigation contract violation: invalid UTF-8 in {label}: byte {error.start}"
        ) from error
    records: list[JsonObject] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                "reviewed-navigation contract violation: "
                f"invalid JSONL in {label}:{line_number}: {error.msg}"
            ) from error
        _require(isinstance(value, dict), f"non-object JSONL row in {label}:{line_number}")
        records.append(cast(JsonObject, value))
    return records


def _identifier(record: Mapping[str, Any], fields: Sequence[str], label: str) -> str:
    present = [field for field in fields if field in record]
    _require(len(present) == 1, f"{label} must have one identifier field")
    return _string(record[present[0]], f"{label} identifier")


def _object(value: Any, label: str) -> JsonObject:
    _require(isinstance(value, dict), f"{label} is not an object")
    return cast(JsonObject, value)


def _string(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{label} is not a non-empty string")
    return cast(str, value)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"reviewed-navigation contract violation: {message}")


__all__ = [
    "ArtifactRoots",
    "PublishedReviewedNavigation",
    "ReviewedNavigationMaterializationRequest",
    "ReviewedNavigationRequestSpec",
    "load_reviewed_navigation_bundle",
    "materialize_reviewed_navigation",
    "materialize_reviewed_navigation_from_spec",
]
