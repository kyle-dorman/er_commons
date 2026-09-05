"""Resolve, identify, validate, and publish document relinking runs.

The relinking module owns in-memory record construction.  This module owns the
stage boundary: resolving sealed inputs, deriving the candidate identity,
validating every output family, and publishing completion-last without
clobbering an existing candidate.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256
from er_commons.document_publication.config import DocumentRunSpec, load_document_run_spec
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_publication.records import SourceIdentity
from er_commons.document_publication.storage import verify_candidate as verify_document_candidate
from er_commons.document_records.document_references.construction import (
    CROSS_REFERENCE_PATH,
    TARGET_ALIAS_PATH,
    CandidateSource,
)
from er_commons.document_records.document_references.indexing import NamespaceRemapper
from er_commons.document_records.document_references.linking_core import LinkedSourceProducts
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.document_records.document_references.policy import default_mention_policy
from er_commons.document_records.document_references.relink_preflight import (
    validate_base_collection_selection,
)
from er_commons.document_records.document_references.relinking import (
    DocumentRelinkBuilder,
    NavigationInputs,
    RelinkBuild,
)
from er_commons.document_records.document_references.relinking_config import (
    OUTPUT_SCHEMA_ROLES,
    DocumentLinkRunSpec,
    ExternalArtifactRef,
    load_document_link_run_spec,
)
from er_commons.document_records.document_references.reviewed_navigation import (
    ArtifactRoots,
    load_reviewed_navigation_bundle,
)
from er_commons.document_records.document_references.storage import (
    read_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)
from er_commons.document_records.document_references.types import JsonObject
from er_commons.document_records.record_mapping.publication import (
    build_inventory,
    write_inventory,
)
from er_commons.source_family_catalog import SourceFamilyCatalog

_NAVIGATION_PATHS = {
    "entries": "navigation/entries.jsonl",
    "relations": "navigation/parent_relations.jsonl",
    "decisions": "navigation/decisions.jsonl",
    "links": "navigation/links.jsonl",
}
_SUPPORT_PATHS = {
    "target_index": "support/document_link_target_index.json",
    "accounting": "support/document_link_accounting.json",
    "preservation": "support/document_link_preservation.json",
}
_OUTPUT_SCHEMA_ROLE_SET = frozenset(OUTPUT_SCHEMA_ROLES)
_OUTPUT_ROW_PATHS = {
    "alias": TARGET_ALIAS_PATH,
    "ordinary_reference": CROSS_REFERENCE_PATH,
    "navigation_entry": _NAVIGATION_PATHS["entries"],
    "navigation_relation": _NAVIGATION_PATHS["relations"],
    "navigation_decision": _NAVIGATION_PATHS["decisions"],
    "navigation_link": _NAVIGATION_PATHS["links"],
}


@dataclass(frozen=True)
class RelinkIdentityInputs:
    """Sealed inputs that determine one per-source linked-product identity."""

    source_id: str
    source_document_id: str
    structured_candidate_id: str
    source_document_completion_sha256: str
    source_document_inventory_sha256: str
    structured_completion_sha256: str
    structured_inventory_sha256: str
    link_run_spec_sha256: str
    linking_policy_sha256: str
    source_family_catalog_sha256: str
    reviewed_navigation_bundle_id: str | None
    reviewed_navigation_completion_sha256: str | None
    output_schema_bundle_sha256: str
    owned_code_bundle_sha256: str


@dataclass(frozen=True)
class RelinkExecutionRequest:
    """Resolved, seal-bearing request used by the package CLI adapter."""

    structured_root: Path
    source_document_completion_path: Path
    source_document_inventory_path: Path
    linking_policy_path: Path
    linking_policy_schema_path: Path
    source_family_catalog_path: Path
    output_parent: Path
    identity_inputs: RelinkIdentityInputs
    output_schema_paths: Mapping[str, Path]
    reviewed_navigation_root: Path | None = None
    reviewed_navigation_completion_path: Path | None = None


@dataclass(frozen=True)
class RelinkExecutionResult:
    """Deterministic identity, build, and completion from one relink request."""

    identity: JsonObject
    build: RelinkBuild
    root: Path
    completion_path: Path


@dataclass(frozen=True)
class PreparedRelinkRun:
    """One globally verified, immutable-in-memory relink execution plan."""

    spec: DocumentLinkRunSpec
    spec_path: Path
    spec_sha256: str
    repository_root: Path
    artifact_root: Path
    base_production_id: str
    replacement_production_id: str
    document_spec_path: Path
    document_spec: DocumentRunSpec
    collection_spec_path: Path
    policy_path: Path
    policy_schema_path: Path
    catalog_path: Path
    output_schema_paths: Mapping[str, Path]
    owned_code_bundle_sha256: str


def prepare_document_relink_run(
    *, data_root: Path, link_spec: Path, repository_root: Path | None = None
) -> PreparedRelinkRun:
    """Load and globally preflight a relink specification exactly once."""
    spec_path = link_spec.resolve()
    spec, spec_sha256 = load_document_link_run_spec(spec_path)
    repo_root = (repository_root or Path(__file__).resolve().parents[4]).resolve()
    artifact_root = data_root.resolve()

    def resolve(reference: ExternalArtifactRef) -> Path:
        return reference.resolve(repository_root=repo_root, artifact_root=artifact_root)

    handoff = _read_object(resolve(spec.base_collection.handoff_ref))
    contract_bundle = _read_object(resolve(spec.base_collection.contract_bundle_ref))
    base_identity = _read_object(resolve(spec.base_production_identity_ref))
    replacement_identity = _read_object(resolve(spec.replacement_production_identity_recipe_ref))
    base = validate_production_identity(base_identity)
    replacement = validate_production_identity(
        replacement_identity,
        expected_source_ids=list(spec.selected_source_ids),
        project_root=repo_root,
    )
    validate_base_collection_selection(
        spec=spec,
        base_production_identity=base_identity,
        handoff=handoff,
        contract_bundle=contract_bundle,
    )
    document_spec_path = resolve(spec.document_publication_spec_ref)
    document_spec, _ = load_document_run_spec(document_spec_path)
    document_source_ids = tuple(item.source_id for item in document_spec.document_processes)
    if (
        document_spec.production_extraction_id != replacement.value
        or document_source_ids != spec.selected_source_ids
    ):
        raise ValueError("relink and replacement document specifications differ")
    output_schema_paths = {
        field_name: resolve(getattr(spec.output_schema_refs, field_name))
        for field_name in spec.output_schema_refs.__class__.model_fields
    }
    return PreparedRelinkRun(
        spec=spec,
        spec_path=spec_path,
        spec_sha256=spec_sha256,
        repository_root=repo_root,
        artifact_root=artifact_root,
        base_production_id=base.value,
        replacement_production_id=replacement.value,
        document_spec_path=document_spec_path,
        document_spec=document_spec,
        collection_spec_path=resolve(spec.collection_run_spec_ref),
        policy_path=resolve(spec.linking_policy_ref),
        policy_schema_path=resolve(spec.linking_policy_schema_ref),
        catalog_path=resolve(spec.source_family_catalog_ref),
        output_schema_paths=output_schema_paths,
        owned_code_bundle_sha256=_owned_code_bundle_sha256(),
    )


def verify_prepared_link_spec(prepared: PreparedRelinkRun) -> None:
    """Fail if the small run specification changes during a collection run."""
    _verify_digest(prepared.spec_path, prepared.spec_sha256, "prepared link specification")


def execute_document_relink_from_spec(
    *,
    data_root: Path,
    link_spec: Path,
    source_id: str,
    repository_root: Path | None = None,
) -> RelinkExecutionResult:
    """Resolve and verify a portable run spec before relinking one named source."""
    prepared = prepare_document_relink_run(
        data_root=data_root, link_spec=link_spec, repository_root=repository_root
    )
    return execute_prepared_document_relink(prepared, source_id=source_id)


def execute_prepared_document_relink(
    prepared: PreparedRelinkRun, *, source_id: str
) -> RelinkExecutionResult:
    """Relink one source from a globally verified, fixed execution plan."""
    verify_prepared_link_spec(prepared)
    spec = prepared.spec
    spec_sha256 = prepared.spec_sha256
    repo_root = prepared.repository_root
    artifact_root = prepared.artifact_root
    selection = spec.document(source_id)

    def resolve(reference: ExternalArtifactRef) -> Path:
        return reference.resolve(repository_root=repo_root, artifact_root=artifact_root)

    policy_path = prepared.policy_path
    policy_schema_path = prepared.policy_schema_path
    catalog_path = prepared.catalog_path
    source_completion = resolve(selection.source_document.completion_ref)
    source_inventory = resolve(selection.source_document.inventory_ref)
    source_document_root = source_completion.parent.parent
    if (
        source_inventory.parent.parent != source_document_root
        or source_document_root.name != selection.source_document.candidate_id
    ):
        raise ValueError("source document completion, inventory, or identity differs")
    source_document_completion = _read_object(source_completion)
    verify_document_candidate(
        source_document_root,
        selection.source_document.candidate_id,
        SourceIdentity.model_validate(source_document_completion.get("source")),
    )
    structured_completion = resolve(selection.structured_document.completion_ref)
    structured_inventory = resolve(selection.structured_document.inventory_ref)
    structured_root = structured_completion.parent.parent
    if structured_inventory.parent.parent != structured_root:
        raise ValueError("structured completion and inventory have different roots")
    _verify_source_document_reuse_boundary(
        source_document_root=source_document_root,
        artifact_root=artifact_root,
        expected_source_id=source_id,
        expected_production_id=prepared.base_production_id,
        selected_structured_completion=selection.structured_document.completion_ref,
    )

    schema_refs = spec.output_schema_refs.model_dump()
    output_schema_paths = prepared.output_schema_paths
    reviewed_root, reviewed_completion, reviewed_id, reviewed_completion_sha256 = (
        _resolve_reviewed_navigation(
            spec=spec,
            source_id=source_id,
            resolve=resolve,
            repository_root=repo_root,
            artifact_root=artifact_root,
        )
    )
    identity_inputs = RelinkIdentityInputs(
        source_id=source_id,
        source_document_id=selection.source_document.candidate_id,
        structured_candidate_id=selection.structured_document.candidate_id,
        source_document_completion_sha256=selection.source_document.completion_ref.sha256,
        source_document_inventory_sha256=selection.source_document.inventory_ref.sha256,
        structured_completion_sha256=selection.structured_document.completion_ref.sha256,
        structured_inventory_sha256=selection.structured_document.inventory_ref.sha256,
        link_run_spec_sha256=spec_sha256,
        linking_policy_sha256=spec.linking_policy_ref.sha256,
        source_family_catalog_sha256=spec.source_family_catalog_ref.sha256,
        reviewed_navigation_bundle_id=reviewed_id,
        reviewed_navigation_completion_sha256=reviewed_completion_sha256,
        output_schema_bundle_sha256=canonical_json_sha256(schema_refs),
        owned_code_bundle_sha256=prepared.owned_code_bundle_sha256,
    )
    return execute_document_relink(
        RelinkExecutionRequest(
            structured_root=structured_root,
            source_document_completion_path=source_completion,
            source_document_inventory_path=source_inventory,
            linking_policy_path=policy_path,
            linking_policy_schema_path=policy_schema_path,
            source_family_catalog_path=catalog_path,
            output_parent=(
                artifact_root / spec.artifact_relative_root / "linked_candidates" / source_id
            ),
            identity_inputs=identity_inputs,
            output_schema_paths=output_schema_paths,
            reviewed_navigation_root=reviewed_root,
            reviewed_navigation_completion_path=reviewed_completion,
        )
    )


def _resolve_reviewed_navigation(
    *,
    spec: DocumentLinkRunSpec,
    source_id: str,
    resolve: Callable[[ExternalArtifactRef], Path],
    repository_root: Path,
    artifact_root: Path,
) -> tuple[Path | None, Path | None, str | None, str | None]:
    """Verify an optional reviewed-navigation bundle and its selected references."""
    # Kept behind this small adapter so the main spec executor remains readable.
    reviewed = spec.reviewed_navigation
    if reviewed is None or source_id not in reviewed.source_ids:
        return None, None, None, None
    descriptor_path = resolve(reviewed.bundle_ref)
    schema_path = resolve(reviewed.schema_ref)
    published = load_reviewed_navigation_bundle(
        descriptor_path,
        roots=ArtifactRoots(repository_root, artifact_root),
        schema_path=schema_path,
        selected_source_ids=spec.selected_source_ids,
    )
    if published.descriptor["bundle_id"] != reviewed.bundle_id:
        raise ValueError("reviewed bundle selection differs from verified descriptor")
    descriptor = published.descriptor
    expected_refs = {
        "review_decisions_ref": descriptor["identity_preimage"]["review_decisions_ref"],
        "semantic_view_ref": descriptor["identity_preimage"]["semantic_view_ref"],
        "disposition_ref": descriptor["payloads"]["dispositions_ref"],
        "text_entries_ref": descriptor["payloads"]["text_entries_ref"],
        "parent_relations_ref": descriptor["payloads"]["parent_relations_ref"],
        "inventory_ref": descriptor["inventory_ref"],
        "completion_ref": descriptor["completion_ref"],
    }
    for field_name, expected in expected_refs.items():
        selected = getattr(reviewed, field_name)
        if selected.model_dump() != expected:
            raise ValueError(f"reviewed bundle reference differs: {field_name}")
        selected.resolve(
            repository_root=repository_root,
            artifact_root=artifact_root,
            bundle_root=published.root,
        )
    identity_path = resolve(reviewed.identity_ref)
    if identity_path != published.root / "records/identity_preimage.json":
        raise ValueError("reviewed bundle identity reference differs")
    completion = resolve(reviewed.completion_ref)
    return published.root, completion, reviewed.bundle_id, reviewed.completion_ref.sha256


def _verify_source_document_reuse_boundary(
    *,
    source_document_root: Path,
    artifact_root: Path,
    expected_source_id: str,
    expected_production_id: str,
    selected_structured_completion: ExternalArtifactRef,
) -> None:
    """Verify all five frozen upstream products named by the source document."""
    identity = _read_object(source_document_root / "records/document_identity.json")
    source = identity.get("source")
    if (
        identity.get("candidate_id") != source_document_root.name
        or identity.get("production_extraction_id") != expected_production_id
        or not isinstance(source, dict)
        or source.get("source_id") != expected_source_id
    ):
        raise ValueError("source document identity, production, or source differs")
    stages = identity.get("stage_completions")
    if not isinstance(stages, dict):
        raise ValueError("source document identity lacks stage completions")
    reused = (
        "stable_content_evidence",
        "heading_evidence",
        "mapped_records",
        "hierarchy_decisions",
        "structured_document",
    )
    for stage_name in reused:
        reference = stages.get(stage_name)
        if not isinstance(reference, dict):
            raise ValueError(f"source document lacks reused stage: {stage_name}")
        relative = reference.get("path")
        digest = reference.get("sha256")
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise ValueError(f"source document has invalid reused stage: {stage_name}")
        path = (artifact_root / relative).resolve()
        if not path.is_relative_to(artifact_root) or not path.is_file():
            raise ValueError(f"reused stage is absent or escapes artifact root: {stage_name}")
        _verify_digest(path, digest, f"reused {stage_name}")
    structured = stages["structured_document"]
    if (
        structured.get("path") != selected_structured_completion.path
        or structured.get("sha256") != selected_structured_completion.sha256
    ):
        raise ValueError("selected structured document differs from source identity")


def build_relink_identity(inputs: RelinkIdentityInputs) -> JsonObject:
    """Derive an acyclic identity from sealed inputs, never from output bytes."""
    preimage: JsonObject = {
        "schema_version": "er_commons.document_link_identity.v1",
        **inputs.__dict__,
    }
    digest = canonical_json_sha256(preimage)
    return {
        "schema_version": "er_commons.extraction_identity.v3",
        "extraction_version_name": "document_linking_v1",
        "extraction_id": f"exv1-{digest}",
        "identity_sha256": digest,
        "document_link_contract": preimage,
    }


def execute_document_relink(request: RelinkExecutionRequest) -> RelinkExecutionResult:
    """Verify sealed inputs, build one source, and no-clobber publish its result."""
    inputs = request.identity_inputs
    _verify_execution_inputs(request)
    source = CandidateSource.load(request.structured_root)
    if inputs.reviewed_navigation_bundle_id is None:
        if request.reviewed_navigation_root or request.reviewed_navigation_completion_path:
            raise ValueError("machine-only identity cannot consume reviewed navigation")
        navigation = NavigationInputs.from_machine_records(
            source.record_files, source_id=inputs.source_id
        )
    else:
        navigation = _load_reviewed_navigation(request, source)
        source_document_root = request.source_document_completion_path.parent.parent
        prior_linked_manifest = _read_object(source_document_root / "content/records/manifest.json")
        prior_linked_id = prior_linked_manifest.get("extraction_id")
        if not isinstance(prior_linked_id, str) or not prior_linked_id:
            raise ValueError("source document content lacks its linked extraction identity")
        navigation = navigation.remap_namespace(prior_linked_id, inputs.structured_candidate_id)
    documents = source.record_files.get("canonical/documents.jsonl", [])
    if (
        request.structured_root.name != inputs.structured_candidate_id
        or len(documents) != 1
        or documents[0].get("source_id") != inputs.source_id
    ):
        raise ValueError("structured candidate identity or source differs")
    identity = build_relink_identity(inputs)
    candidate_id = str(identity["extraction_id"])
    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=inputs.structured_candidate_id,
        candidate_id=candidate_id,
        source_id=inputs.source_id,
        mention_policy=default_mention_policy(),
        linking_policy=load_document_linking_policy(
            request.linking_policy_path, schema_path=request.linking_policy_schema_path
        ),
        source_family_catalog=SourceFamilyCatalog.load(request.source_family_catalog_path),
        source_family_catalog_sha256=inputs.source_family_catalog_sha256,
        navigation=navigation,
    ).build()
    root = request.output_parent / candidate_id
    completion = publish_relink_candidate(
        root=root,
        source=source,
        build=build,
        identity=identity,
        schema_paths=request.output_schema_paths,
    )
    return RelinkExecutionResult(identity, build, root, completion)


def _verify_execution_inputs(request: RelinkExecutionRequest) -> None:
    inputs = request.identity_inputs
    pairs = (
        (
            request.source_document_completion_path,
            inputs.source_document_completion_sha256,
            "source document completion",
        ),
        (
            request.source_document_inventory_path,
            inputs.source_document_inventory_sha256,
            "source document inventory",
        ),
        (
            request.structured_root / "records/completion_record.json",
            inputs.structured_completion_sha256,
            "structured completion",
        ),
        (
            request.structured_root / "records/artifact_inventory.json",
            inputs.structured_inventory_sha256,
            "structured inventory",
        ),
        (request.linking_policy_path, inputs.linking_policy_sha256, "linking policy"),
        (
            request.source_family_catalog_path,
            inputs.source_family_catalog_sha256,
            "source-family catalog",
        ),
    )
    for path, digest, label in pairs:
        _verify_digest(path, digest, label)
    _verify_completion_inventory(
        request.structured_root / "records/completion_record.json",
        request.structured_root / "records/artifact_inventory.json",
        label="structured candidate",
    )


def _load_reviewed_navigation(
    request: RelinkExecutionRequest, source: CandidateSource
) -> NavigationInputs:
    inputs = request.identity_inputs
    if (
        request.reviewed_navigation_root is None
        or request.reviewed_navigation_completion_path is None
        or inputs.reviewed_navigation_completion_sha256 is None
    ):
        raise ValueError("reviewed identity requires its verified bundle paths")
    if request.reviewed_navigation_root.name != inputs.reviewed_navigation_bundle_id:
        raise ValueError("reviewed navigation bundle identity differs")
    _verify_digest(
        request.reviewed_navigation_completion_path,
        inputs.reviewed_navigation_completion_sha256,
        "reviewed navigation completion",
    )
    _verify_completion_inventory(
        request.reviewed_navigation_completion_path,
        request.reviewed_navigation_root / "records/artifact_inventory.json",
        label="reviewed navigation",
    )
    return NavigationInputs.from_bundle_root(
        request.reviewed_navigation_root, source_id=inputs.source_id
    )


def publish_relink_candidate(
    *,
    root: Path,
    source: CandidateSource,
    build: RelinkBuild,
    identity: JsonObject,
    schema_paths: Mapping[str, Path],
) -> Path:
    """Atomically publish an absent candidate and validate exact inventory closure."""
    candidate_id = str(identity["extraction_id"])
    if root.exists():
        return verify_relink_candidate(
            root,
            candidate_id,
            schema_paths=schema_paths,
            expected_identity=identity,
            expected_build=build,
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{candidate_id}.", dir=root.parent))
    try:
        _write_candidate(staging, source, build, identity, schema_paths)
        os.rename(staging, root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return verify_relink_candidate(
        root,
        candidate_id,
        schema_paths=schema_paths,
        expected_identity=identity,
        expected_build=build,
    )


def verify_relink_candidate(
    root: Path,
    candidate_id: str,
    *,
    schema_paths: Mapping[str, Path],
    expected_identity: JsonObject | None = None,
    expected_build: RelinkBuild | None = None,
) -> Path:
    """Reject incomplete, changed, or non-closed linked-product candidates."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    identity_path = root / "records/extraction_identity.json"
    manifest_path = root / "records/manifest.json"
    for path in (completion_path, inventory_path, identity_path, manifest_path):
        if not path.is_file():
            raise ValueError(f"relink candidate lacks terminal record: {path.name}")
    identity = _read_object(identity_path)
    if identity.get("extraction_id") != candidate_id:
        raise ValueError("relink identity differs from candidate namespace")
    preimage = identity.get("document_link_contract")
    if not isinstance(preimage, dict) or canonical_json_sha256(
        preimage
    ) != candidate_id.removeprefix("exv1-"):
        raise ValueError("relink identity preimage differs")
    if expected_identity is not None and identity != expected_identity:
        raise ValueError("existing relink identity differs from the requested build")
    completion = _read_object(completion_path)
    if completion != {
        "schema_version": "er_commons.document_link_completion.v1",
        "extraction_id": candidate_id,
        "status": "complete_with_warnings",
        "completion_last": True,
        "artifact_inventory_sha256": sha256_file(inventory_path),
        "preservation_status": "passed",
        "undeclared_difference_count": 0,
    }:
        raise ValueError("relink completion fields differ")
    if _read_object(inventory_path) != build_inventory(root):
        raise ValueError("relink inventory differs from managed files")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("relink candidate contains a managed symlink")
    _validate_published_outputs(root, schema_paths)
    if expected_build is not None:
        _verify_expected_linking_outputs(root, expected_build)
    return completion_path


def _write_candidate(
    root: Path,
    source: CandidateSource,
    build: RelinkBuild,
    identity: JsonObject,
    schema_paths: Mapping[str, Path],
) -> None:
    write_json(root / "records/extraction_identity.json", identity)
    record_files: list[JsonObject] = []
    for item in source.manifest["record_files"]:
        path = str(item["path"])
        rows = _record_rows(path, build)
        write_jsonl(root / path, rows)
        record_files.append({**item, "sha256": sha256_file(root / path), "record_count": len(rows)})
    for role, path in _NAVIGATION_PATHS.items():
        rows = list(getattr(build.products, f"navigation_{role}"))
        write_jsonl(root / path, rows)
        record_files.append(
            {
                "record_type": f"navigation_{role}",
                "path": path,
                "sha256": sha256_file(root / path),
                "record_count": len(rows),
            }
        )
    support_files: list[JsonObject] = []
    for item in source.manifest.get("support_files", []):
        relative = str(item["path"])
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source.root / relative, destination)
        support_files.append(
            {**item, "sha256": sha256_file(destination), "reused_from_structured_candidate": True}
        )
    for role, path in _SUPPORT_PATHS.items():
        write_json(root / path, build.support[role])
        support_files.append(
            {
                "role": role,
                "path": path,
                "sha256": sha256_file(root / path),
                "schema_version": "1.0.0",
            }
        )
    remapper = NamespaceRemapper(
        str(source.manifest["extraction_id"]), str(identity["extraction_id"])
    )
    manifest = {
        **remapper.value(source.manifest),
        "schema_version": "er_commons.document_link_manifest.v1",
        "extraction_id": identity["extraction_id"],
        "identity_sha256": identity["identity_sha256"],
        "record_files": record_files,
        "support_files": support_files,
        "target_alias_count": len(build.products.target_aliases),
        "cross_reference_count": len(build.products.ordinary_references),
        "navigation_entry_count": len(build.products.navigation_entries),
        "navigation_link_count": len(build.products.navigation_links),
    }
    write_json(root / "records/manifest.json", manifest)
    upstream_summary = source.root / "records/canonicalization_summary.json"
    if upstream_summary.is_file():
        summary = remapper.value(_read_object(upstream_summary))
        summary["schema_version"] = "er_commons.document_link_summary.v1"
        summary["candidate_id"] = identity["extraction_id"]
        summary["document_link_accounting"] = build.support["accounting"]
        write_json(root / "records/canonicalization_summary.json", summary)
    validators = _output_validators(schema_paths)
    _validate_pre_completion_outputs(
        validators=validators, identity=identity, manifest=manifest, build=build
    )
    inventory_path = write_inventory(root)
    _validate_schema_value(validators["inventory"], _read_object(inventory_path), "inventory")
    completion = {
        "schema_version": "er_commons.document_link_completion.v1",
        "extraction_id": identity["extraction_id"],
        "status": "complete_with_warnings",
        "completion_last": True,
        "artifact_inventory_sha256": sha256_file(inventory_path),
        "preservation_status": "passed",
        "undeclared_difference_count": 0,
    }
    _validate_schema_value(validators["completion"], completion, "completion")
    write_json(root / "records/completion_record.json", completion)


def _output_validators(schema_paths: Mapping[str, Path]) -> dict[str, Draft202012Validator]:
    """Load the exact role-keyed schema bundle bound into the relink identity."""
    if set(schema_paths) != _OUTPUT_SCHEMA_ROLE_SET:
        missing = sorted(_OUTPUT_SCHEMA_ROLE_SET - set(schema_paths))
        extra = sorted(set(schema_paths) - _OUTPUT_SCHEMA_ROLE_SET)
        raise ValueError(f"relink output schema roles differ: missing={missing}, extra={extra}")
    validators: dict[str, Draft202012Validator] = {}
    for role in OUTPUT_SCHEMA_ROLES:
        schema = _read_object(schema_paths[role])
        Draft202012Validator.check_schema(schema)
        validators[role] = Draft202012Validator(schema)
    return validators


def _validate_pre_completion_outputs(
    *,
    validators: Mapping[str, Draft202012Validator],
    identity: JsonObject,
    manifest: JsonObject,
    build: RelinkBuild,
) -> None:
    """Validate every generated family before a completion record can exist."""
    _validate_schema_value(validators["identity"], identity, "identity")
    _validate_schema_value(validators["manifest"], manifest, "manifest")
    _require_manifest_counts(manifest, build.products)
    _validate_relink_build_products(build, validators)


def validate_relink_build_products(
    build: RelinkBuild,
    *,
    schema_paths: Mapping[str, Path],
) -> None:
    """Validate every generated row and support payload before publication."""
    _validate_relink_build_products(build, _output_validators(schema_paths))


def _validate_relink_build_products(
    build: RelinkBuild, validators: Mapping[str, Draft202012Validator]
) -> None:
    """Apply already-loaded validators to each generated record family."""
    for role, rows in _product_rows(build.products).items():
        for index, row in enumerate(rows):
            _validate_schema_value(validators[role], row, f"{role}[{index}]")
    for role, payload in sorted(build.support.items()):
        _validate_schema_value(validators["support"], payload, f"support.{role}")


def _validate_published_outputs(root: Path, schema_paths: Mapping[str, Path]) -> None:
    validators = _output_validators(schema_paths)
    _validate_schema_value(
        validators["identity"], _read_object(root / "records/extraction_identity.json"), "identity"
    )
    manifest = _read_object(root / "records/manifest.json")
    _validate_schema_value(validators["manifest"], manifest, "manifest")
    _validate_schema_value(
        validators["inventory"], _read_object(root / "records/artifact_inventory.json"), "inventory"
    )
    _validate_schema_value(
        validators["completion"],
        _read_object(root / "records/completion_record.json"),
        "completion",
    )
    row_counts: dict[str, int] = {}
    for role, relative in _OUTPUT_ROW_PATHS.items():
        rows = read_jsonl(root / relative)
        row_counts[role] = len(rows)
        for index, row in enumerate(rows):
            _validate_schema_value(validators[role], row, f"{role}[{index}]")
    expected = {
        "target_alias_count": row_counts["alias"],
        "cross_reference_count": row_counts["ordinary_reference"],
        "navigation_entry_count": row_counts["navigation_entry"],
        "navigation_link_count": row_counts["navigation_link"],
    }
    if any(manifest.get(name) != count for name, count in expected.items()):
        raise ValueError("relink manifest output counts differ")
    for role, relative in _SUPPORT_PATHS.items():
        _validate_schema_value(
            validators["support"], _read_object(root / relative), f"support.{role}"
        )


def _verify_expected_linking_outputs(root: Path, build: RelinkBuild) -> None:
    """Compare reuse against regenerated linking-owned records, never large source payloads."""
    expected_rows = _product_rows(build.products)
    for role, relative in _OUTPUT_ROW_PATHS.items():
        if tuple(read_jsonl(root / relative)) != expected_rows[role]:
            raise ValueError(f"existing relink {role} rows differ from requested build")
    for role, relative in _SUPPORT_PATHS.items():
        if _read_object(root / relative) != build.support[role]:
            raise ValueError(f"existing relink support differs from requested build: {role}")
    summary_path = root / "records/canonicalization_summary.json"
    if (
        summary_path.is_file()
        and _read_object(summary_path).get("document_link_accounting")
        != build.support["accounting"]
    ):
        raise ValueError("existing relink summary differs from requested build")


def _validate_schema_value(validator: Draft202012Validator, value: JsonObject, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path)
        suffix = f" at {location}" if location else ""
        raise ValueError(f"invalid relink {label}{suffix}: {error.message}")


def _require_manifest_counts(manifest: JsonObject, products: LinkedSourceProducts) -> None:
    expected = {
        "target_alias_count": len(products.target_aliases),
        "cross_reference_count": len(products.ordinary_references),
        "navigation_entry_count": len(products.navigation_entries),
        "navigation_link_count": len(products.navigation_links),
    }
    if any(manifest.get(name) != count for name, count in expected.items()):
        raise ValueError("relink manifest output counts differ")


def _record_rows(path: str, build: RelinkBuild) -> list[JsonObject]:
    """Select the one generated or preserved row family for a manifest path."""
    if path == TARGET_ALIAS_PATH:
        return list(build.products.target_aliases)
    if path == CROSS_REFERENCE_PATH:
        return list(build.products.ordinary_references)
    return list(build.preserved_record_files[path])


def _product_rows(products: LinkedSourceProducts) -> dict[str, tuple[JsonObject, ...]]:
    """Name each generated row family by its output-schema role."""
    return {
        "alias": products.target_aliases,
        "ordinary_reference": products.ordinary_references,
        "navigation_entry": products.navigation_entries,
        "navigation_relation": products.navigation_relations,
        "navigation_decision": products.navigation_decisions,
        "navigation_link": products.navigation_links,
    }


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _verify_digest(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} is absent: {path}")
    if sha256_file(path) != expected:
        raise ValueError(f"{label} seal differs (SHA-256): {path}")


def _verify_completion_inventory(
    completion_path: Path, inventory_path: Path, *, label: str
) -> None:
    completion = _read_object(completion_path)
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise ValueError(f"{label} completion does not seal its inventory")
    root = completion_path.parent.parent
    if inventory_path.parent.parent != root or _read_object(inventory_path) != build_inventory(
        root
    ):
        raise ValueError(f"{label} inventory differs from managed files")


def _owned_code_bundle_sha256() -> str:
    """Bind every output-affecting linking module in stable repository order."""
    repo_root = Path(__file__).resolve().parents[4]
    package_root = repo_root / "src/er_commons/document_records/document_references"
    relative_paths = sorted(
        {path.relative_to(repo_root).as_posix() for path in package_root.glob("*.py")}
        | {
            "src/er_commons/artifact_io.py",
            "src/er_commons/cli.py",
            "src/er_commons/document_records/record_mapping/publication.py",
            "src/er_commons/source_family_catalog.py",
        }
    )
    return canonical_json_sha256(
        [
            {"path": relative, "sha256": sha256_file(repo_root / relative)}
            for relative in relative_paths
        ]
    )


__all__ = [
    "PreparedRelinkRun",
    "RelinkExecutionRequest",
    "RelinkExecutionResult",
    "RelinkIdentityInputs",
    "build_relink_identity",
    "execute_document_relink",
    "execute_document_relink_from_spec",
    "execute_prepared_document_relink",
    "prepare_document_relink_run",
    "publish_relink_candidate",
    "validate_relink_build_products",
    "verify_relink_candidate",
    "verify_prepared_link_spec",
]
