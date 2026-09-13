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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256
from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import reference_for_path
from er_commons.document_publication.accepted_inputs import (
    PreparedPublicationInputs,
    capture_verified_stamps,
    file_stamp,
    prepare_publication_inputs,
)
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_publication.records import SourceIdentity
from er_commons.document_publication.storage import (
    verify_candidate_metadata as verify_document_candidate,
)
from er_commons.document_publication.storage import verify_inventory_metadata
from er_commons.document_records.document_references.construction import (
    CROSS_REFERENCE_PATH,
    TARGET_ALIAS_PATH,
    CandidateSource,
)
from er_commons.document_records.document_references.fc1_equivalence import (
    AcceptedFc1Packet,
    build_fc1_rebuilt_equivalence,
    load_accepted_fc1_packet,
)
from er_commons.document_records.document_references.figure_aliases import (
    FigureAliasValidationInputs,
    validate_caption_figure_alias_evidence,
)
from er_commons.document_records.document_references.indexing import NamespaceRemapper
from er_commons.document_records.document_references.linking_core import LinkedSourceProducts
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.document_records.document_references.policy import default_mention_policy
from er_commons.document_records.document_references.relink_preflight import (
    task06g_base_membership_from_source_slots,
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
    RelinkDocumentSelection,
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

RELINK_READ_FILE_LIMIT = 2_147_483_648
RELINK_READ_TOTAL_LIMIT = 8_589_934_592


def _relink_verification_budget() -> VerificationBudget:
    """Bound accepted canonical-record reads for one collection-wide relink."""
    return VerificationBudget(
        read_file_limit=RELINK_READ_FILE_LIMIT,
        read_total_limit=RELINK_READ_TOTAL_LIMIT,
    )


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
    "figure_qualification": "support/figure_caption_alias_qualification.json",
    "fc1_rebuilt_equivalence": "support/fc1_rebuilt_equivalence.json",
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
    resolved_spec_ref: JsonObject | None = None
    accepted_fc1_evidence: JsonObject | None = None
    fc1_rebuilt_equivalence_sha256: str | None = None


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
    prepared_navigation: NavigationInputs | None = None
    budget: VerificationBudget | None = None
    figure_aliases_enabled: bool | None = None
    accepted_fc1_packet: AcceptedFc1Packet | None = None
    base_structured_candidate_id: str | None = None
    fc1_correspondence_ref: JsonObject | None = None


@dataclass(frozen=True)
class RelinkExecutionResult:
    """Deterministic identity, build, and completion from one relink request."""

    identity: JsonObject
    build: RelinkBuild
    root: Path
    completion_path: Path


@dataclass(frozen=True)
class PreparedReviewedNavigation:
    """One validated shared bundle with source-local navigation projections."""

    root: Path
    completion_path: Path
    bundle_id: str
    completion_sha256: str
    inputs_by_source: Mapping[str, NavigationInputs]


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
    budget: VerificationBudget
    reviewed_navigation: PreparedReviewedNavigation | None
    shared_refs: tuple[ExternalArtifactRef, ...]
    accepted_fc1_packet: AcceptedFc1Packet | None = None
    publication_inputs: PreparedPublicationInputs | None = None
    input_stamps: Mapping[Path, tuple[int, int, int, int]] | None = None


def prepare_document_relink_run(
    *,
    data_root: Path,
    link_spec: Path,
    repository_root: Path | None = None,
    prepare_publication: bool = False,
) -> PreparedRelinkRun:
    """Load and globally preflight a relink specification exactly once."""
    spec_path = link_spec.resolve()
    repo_root = (repository_root or Path(__file__).resolve().parents[4]).resolve()
    artifact_root = data_root.resolve()
    spec_root = (
        artifact_root
        if spec_path.is_relative_to(artifact_root)
        else repo_root
        if spec_path.is_relative_to(repo_root)
        else None
    )
    if spec_root is None:
        raise ValueError("link specification is outside repository and artifact roots")
    budget = _relink_verification_budget()
    spec_sha256 = budget.hash_file(
        spec_path, role="run_descriptor", source_id="shared", root=spec_root
    )
    spec = DocumentLinkRunSpec.model_validate(
        budget.read_json(spec_path, role="run_descriptor", source_id="shared", root=spec_root)
    )
    if spec.base_membership_ref is not None and spec.resolution_status != "resolved":
        raise ValueError("mixed-lineage relink execution requires a resolved spec")

    def resolve(reference: ExternalArtifactRef) -> Path:
        return reference.resolve(
            repository_root=repo_root, artifact_root=artifact_root, budget=budget
        )

    handoff = _read_object(resolve(spec.base_collection.handoff_ref), budget=budget)
    contract_bundle = _read_object(resolve(spec.base_collection.contract_bundle_ref), budget=budget)
    base_identity = _read_object(resolve(spec.base_production_identity_ref), budget=budget)
    replacement_identity = _read_object(
        resolve(spec.replacement_production_identity_recipe_ref), budget=budget
    )
    base = validate_production_identity(base_identity)
    replacement = validate_production_identity(
        replacement_identity,
        expected_source_ids=list(spec.selected_source_ids),
        project_root=repo_root,
        artifact_root=artifact_root,
        budget=budget,
    )
    base_membership_spec: DocumentLinkRunSpec | tuple[RelinkDocumentSelection, ...] | None = None
    if spec.base_membership_ref is not None:
        base_membership_path = resolve(spec.base_membership_ref)
        base_membership_value = budget.read_json(
            base_membership_path,
            role="input_binding",
            source_id="shared",
            root=(
                artifact_root
                if spec.base_membership_ref.authority == "artifact_root"
                else repo_root
            ),
        )
        if spec.base_membership_ref is not None:
            contract_path = Path(spec.base_collection.contract_bundle_ref.path)
            if contract_path.name != "contract_bundle.json" or len(contract_path.parents) < 3:
                raise ValueError("mixed-lineage base collection contract path is invalid")
            base_membership_spec = task06g_base_membership_from_source_slots(
                cast(dict[str, object], base_membership_value),
                artifact_root=artifact_root,
                publication_root=artifact_root / contract_path.parents[2],
                production_extraction_id=base.value,
                budget=budget,
            )
        else:
            base_membership_spec = DocumentLinkRunSpec.model_validate(base_membership_value)
    validate_base_collection_selection(
        spec=spec,
        base_production_identity=base_identity,
        handoff=handoff,
        contract_bundle=contract_bundle,
        base_membership_spec=base_membership_spec,
    )
    for selection in spec.documents:
        for evidence_ref in (
            *(selection.evidence_refs or ()),
            *(selection.correspondence_refs or ()),
        ):
            resolve(evidence_ref)
    accepted_fc1_packet = None
    if spec.accepted_fc1_evidence is not None:
        fc1 = spec.accepted_fc1_evidence
        accepted_fc1_packet = load_accepted_fc1_packet(
            fc1,
            resolved_paths={
                "completion": resolve(fc1.completion_ref),
                "inventory": resolve(fc1.inventory_ref),
                "identity": resolve(fc1.identity_ref),
                "qualification": resolve(fc1.qualification_ref),
                "figure_aliases": resolve(fc1.figure_aliases_ref),
                "target_index_entries": resolve(fc1.target_index_entries_ref),
            },
        )
    document_spec_path = resolve(spec.document_publication_spec_ref)
    document_spec_root = (
        artifact_root
        if spec.document_publication_spec_ref.authority == "artifact_root"
        else repo_root
    )
    document_spec = DocumentRunSpec.model_validate(
        budget.read_json(
            document_spec_path,
            role="run_descriptor",
            source_id="shared",
            root=document_spec_root,
        )
    )
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
    prepared = PreparedRelinkRun(
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
        owned_code_bundle_sha256=_owned_code_bundle_sha256(budget),
        budget=budget,
        reviewed_navigation=_resolve_reviewed_navigation(
            spec=spec,
            source_id=(
                spec.reviewed_navigation.source_ids[0]
                if spec.reviewed_navigation
                else spec.selected_source_ids[0]
            ),
            resolve=resolve,
            repository_root=repo_root,
            artifact_root=artifact_root,
            budget=budget,
        ),
        shared_refs=(
            spec.document_publication_spec_ref,
            spec.collection_run_spec_ref,
            spec.linking_policy_ref,
            spec.linking_policy_schema_ref,
            spec.source_family_catalog_ref,
            *tuple(getattr(spec.output_schema_refs, role) for role in OUTPUT_SCHEMA_ROLES),
        ),
        accepted_fc1_packet=accepted_fc1_packet,
    )

    publication_inputs = (
        prepare_publication_inputs(
            artifact_root, document_spec_path, repository_root=repo_root, budget=budget
        )
        if prepare_publication
        else None
    )
    stamps = capture_verified_stamps(budget)
    return replace(prepared, publication_inputs=publication_inputs, input_stamps=stamps)


def verify_prepared_link_spec(prepared: PreparedRelinkRun) -> None:
    """Fail if the small run specification changes during a collection run."""
    artifact_root = getattr(prepared, "artifact_root", prepared.repository_root)
    digest = prepared.budget.hash_file(
        prepared.spec_path,
        role="run_descriptor",
        source_id="shared",
        root=(
            artifact_root
            if prepared.spec_path.is_relative_to(artifact_root)
            else prepared.repository_root
        ),
    )
    if digest != prepared.spec_sha256:
        raise ValueError("prepared link specification changed")
    for path, expected in (prepared.input_stamps or {}).items():
        if file_stamp(path) != expected:
            raise ValueError(f"prepared link input changed: {path}")


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
        return reference.resolve(
            repository_root=repo_root, artifact_root=artifact_root, budget=prepared.budget
        )

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
    source_document_completion = _read_object(
        source_completion, budget=prepared.budget, role="completion"
    )
    verify_document_candidate(
        source_document_root,
        selection.source_document.candidate_id,
        SourceIdentity.model_validate(source_document_completion.get("source")),
        budget=prepared.budget,
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
        expected_production_id=(
            prepared.replacement_production_id
            if selection.change_class != "preserved_semantic"
            else prepared.base_production_id
        ),
        selected_structured_completion=selection.structured_document.completion_ref,
        budget=prepared.budget,
    )

    schema_refs = spec.output_schema_refs.model_dump()
    output_schema_paths = prepared.output_schema_paths
    reviewed = prepared.reviewed_navigation
    if reviewed is not None and source_id not in reviewed.inputs_by_source:
        reviewed = None
    reviewed_root = reviewed.root if reviewed is not None else None
    reviewed_completion = reviewed.completion_path if reviewed is not None else None
    reviewed_id = reviewed.bundle_id if reviewed is not None else None
    reviewed_completion_sha256 = reviewed.completion_sha256 if reviewed is not None else None
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
        resolved_spec_ref=(
            reference_for_path(
                prepared.spec_path,
                repository_root=repo_root,
                artifact_root=artifact_root,
                sha256=spec_sha256,
            ).model_dump(mode="json")
            if spec.base_membership_ref is not None
            else None
        ),
        accepted_fc1_evidence=(
            spec.accepted_fc1_evidence.model_dump(mode="json")
            if source_id == "deir_main" and spec.accepted_fc1_evidence is not None
            else None
        ),
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
            prepared_navigation=(reviewed.inputs_by_source[source_id] if reviewed else None),
            budget=prepared.budget,
            figure_aliases_enabled=(
                source_id in spec.figure_alias_source_ids
                if spec.figure_alias_source_ids is not None
                else None
            ),
            accepted_fc1_packet=(
                prepared.accepted_fc1_packet if source_id == "deir_main" else None
            ),
            base_structured_candidate_id=(
                selection.base_structured_document.candidate_id
                if source_id == "deir_main" and selection.base_structured_document is not None
                else None
            ),
            fc1_correspondence_ref=(
                selection.correspondence_refs[0].model_dump(mode="json")
                if source_id == "deir_main" and selection.correspondence_refs
                else None
            ),
        )
    )


def _resolve_reviewed_navigation(
    *,
    spec: DocumentLinkRunSpec,
    source_id: str,
    resolve: Callable[[ExternalArtifactRef], Path],
    repository_root: Path,
    artifact_root: Path,
    budget: VerificationBudget,
) -> PreparedReviewedNavigation | None:
    """Verify an optional reviewed-navigation bundle and its selected references."""
    # Kept behind this small adapter so the main spec executor remains readable.
    reviewed = spec.reviewed_navigation
    if reviewed is None or source_id not in reviewed.source_ids:
        return None
    descriptor_path = resolve(reviewed.bundle_ref)
    schema_path = resolve(reviewed.schema_ref)
    published = load_reviewed_navigation_bundle(
        descriptor_path,
        roots=ArtifactRoots(repository_root, artifact_root),
        schema_path=schema_path,
        selected_source_ids=spec.selected_source_ids,
        budget=budget,
    )
    if published.descriptor["bundle_id"] != reviewed.bundle_id:
        raise ValueError("reviewed bundle selection differs from verified descriptor")
    if tuple(published.descriptor["source_ids"]) != reviewed.source_ids:
        raise ValueError("reviewed source coverage differs from verified descriptor")
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
    identity_path = resolve(reviewed.identity_ref)
    if identity_path != published.root / "records/identity_preimage.json":
        raise ValueError("reviewed bundle identity reference differs")
    completion = resolve(reviewed.completion_ref)
    return PreparedReviewedNavigation(
        published.root,
        completion,
        reviewed.bundle_id,
        reviewed.completion_ref.sha256,
        {
            source: NavigationInputs.from_records(published.payload_records, source_id=source)
            for source in reviewed.source_ids
        },
    )


def _verify_source_document_reuse_boundary(
    *,
    source_document_root: Path,
    artifact_root: Path,
    expected_source_id: str,
    expected_production_id: str,
    selected_structured_completion: ExternalArtifactRef,
    budget: VerificationBudget | None = None,
) -> None:
    """Verify all five frozen upstream products named by the source document."""
    identity = _read_object(
        source_document_root / "records/document_identity.json",
        budget=budget,
        role="identity_preimage",
    )
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
        _verify_digest(path, digest, f"reused {stage_name}", budget=budget, role="completion")
    structured = stages["structured_document"]
    if (
        structured.get("path") != selected_structured_completion.path
        or structured.get("sha256") != selected_structured_completion.sha256
    ):
        raise ValueError("selected structured document differs from source identity")


def build_relink_identity(inputs: RelinkIdentityInputs) -> JsonObject:
    """Derive an acyclic identity from sealed inputs, never from output bytes."""
    values = dict(inputs.__dict__)
    resolved_spec_ref = values.pop("resolved_spec_ref")
    accepted_fc1_evidence = values.pop("accepted_fc1_evidence")
    fc1_equivalence_sha256 = values.pop("fc1_rebuilt_equivalence_sha256")
    preimage: JsonObject = {
        "schema_version": (
            "er_commons.document_link_identity.v2"
            if resolved_spec_ref is not None
            else "er_commons.document_link_identity.v1"
        ),
        **values,
    }
    if resolved_spec_ref is not None:
        preimage["resolved_spec_ref"] = resolved_spec_ref
    if accepted_fc1_evidence is not None:
        preimage["accepted_fc1_evidence"] = accepted_fc1_evidence
        preimage["fc1_rebuilt_equivalence_sha256"] = fc1_equivalence_sha256
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
    if request.budget is not None:
        manifest = request.budget.read_json(
            request.structured_root / "records/manifest.json",
            role="input_binding",
            source_id=inputs.source_id,
            root=request.structured_root,
        )
        manifest_record = cast(JsonObject, manifest)
        for item in manifest_record["record_files"]:
            request.budget.reserve_read(
                request.structured_root / item["path"],
                role="canonical_records",
                source_id=inputs.source_id,
                root=request.structured_root,
            )
    if request.budget is not None:
        for path, role in (
            (request.structured_root / "records/manifest.json", "input_binding"),
            (request.linking_policy_path, "config"),
            (request.linking_policy_schema_path, "schema"),
            (request.source_family_catalog_path, "input_binding"),
        ):
            request.budget.reserve_read(
                path, role=role, source_id=inputs.source_id, root=path.parent
            )
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
        prior_linked_manifest = _read_object(
            source_document_root / "content/records/manifest.json", budget=request.budget
        )
        prior_linked_id = prior_linked_manifest.get("extraction_id")
        if not isinstance(prior_linked_id, str) or not prior_linked_id:
            raise ValueError("source document content lacks its linked extraction identity")
        navigation = navigation.remap_namespace(prior_linked_id, inputs.structured_candidate_id)
        navigation = navigation.remap_source_record_namespaces(
            inputs.source_id, inputs.structured_candidate_id
        )
    documents = source.record_files.get("canonical/documents.jsonl", [])
    if (
        request.structured_root.name != inputs.structured_candidate_id
        or len(documents) != 1
        or documents[0].get("source_id") != inputs.source_id
    ):
        raise ValueError("structured candidate identity or source differs")
    equivalence = None
    if request.accepted_fc1_packet is not None:
        if (
            inputs.source_id != "deir_main"
            or request.base_structured_candidate_id is None
            or request.fc1_correspondence_ref is None
        ):
            raise ValueError("accepted FC1 evidence lacks main correspondence context")
        equivalence = build_fc1_rebuilt_equivalence(
            packet=request.accepted_fc1_packet,
            inputs=FigureAliasValidationInputs(
                upstream_candidate_id=inputs.structured_candidate_id,
                candidate_id=inputs.structured_candidate_id,
                source_id=inputs.source_id,
                source_document_id=(
                    f"{inputs.structured_candidate_id}/document/{inputs.source_id}"
                ),
                upstream_figures=tuple(source.record_files.get("canonical/figures.jsonl", [])),
                upstream_images=tuple(source.record_files.get("canonical/images.jsonl", [])),
                upstream_blocks=tuple(source.record_files["canonical/blocks.jsonl"]),
                upstream_pages=tuple(source.record_files["canonical/pages.jsonl"]),
            ),
            base_structured_candidate_id=request.base_structured_candidate_id,
            correspondence_ref=request.fc1_correspondence_ref,
        )
        inputs = replace(
            inputs,
            fc1_rebuilt_equivalence_sha256=str(equivalence["equivalence_sha256"]),
        )
    elif inputs.accepted_fc1_evidence is not None:
        raise ValueError("FC1 identity evidence lacks a verified accepted packet")
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
        figure_aliases_enabled=request.figure_aliases_enabled,
    ).build()
    if equivalence is not None:
        build = replace(
            build,
            support={**build.support, "fc1_rebuilt_equivalence": equivalence},
        )
    # Publication uses the sealed manifest and support paths, while ``build``
    # owns the remapped record rows. Drop the duplicate upstream row graph
    # before writing and verifying a large candidate.
    source = replace(source, record_files={})
    root = request.output_parent / candidate_id
    completion = publish_relink_candidate(
        root=root,
        source=source,
        build=build,
        identity=identity,
        schema_paths=request.output_schema_paths,
        budget=request.budget,
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
        _verify_digest(
            path,
            digest,
            label,
            budget=request.budget,
            role="managed_inventory" if label.endswith("inventory") else "input_binding",
        )
    _verify_completion_inventory(
        request.structured_root / "records/completion_record.json",
        request.structured_root / "records/artifact_inventory.json",
        label="structured candidate",
        budget=request.budget,
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
    if request.prepared_navigation is not None:
        navigation = request.prepared_navigation
        for row in (*navigation.entries, *navigation.relations):
            if row.get("source_id") != inputs.source_id:
                raise ValueError("prepared reviewed navigation source coverage differs")
        return navigation
    _verify_digest(
        request.reviewed_navigation_completion_path,
        inputs.reviewed_navigation_completion_sha256,
        "reviewed navigation completion",
        budget=request.budget,
        role="completion",
    )
    _verify_completion_inventory(
        request.reviewed_navigation_completion_path,
        request.reviewed_navigation_root / "records/artifact_inventory.json",
        label="reviewed navigation",
        budget=request.budget,
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
    budget: VerificationBudget | None = None,
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
            budget=budget,
        )
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{candidate_id}.", dir=root.parent))
    try:
        _write_candidate(staging, source, build, identity, schema_paths, budget=budget)
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
        budget=budget,
    )


def verify_relink_candidate(
    root: Path,
    candidate_id: str,
    *,
    schema_paths: Mapping[str, Path],
    expected_identity: JsonObject | None = None,
    expected_build: RelinkBuild | None = None,
    budget: VerificationBudget | None = None,
) -> Path:
    """Reject incomplete, changed, or non-closed linked-product candidates."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    identity_path = root / "records/extraction_identity.json"
    manifest_path = root / "records/manifest.json"
    for path in (completion_path, inventory_path, identity_path, manifest_path):
        if not path.is_file():
            raise ValueError(f"relink candidate lacks terminal record: {path.name}")
    identity = _read_object(identity_path, budget=budget, role="identity_preimage")
    if identity.get("extraction_id") != candidate_id:
        raise ValueError("relink identity differs from candidate namespace")
    preimage = identity.get("document_link_contract")
    if not isinstance(preimage, dict) or canonical_json_sha256(
        preimage
    ) != candidate_id.removeprefix("exv1-"):
        raise ValueError("relink identity preimage differs")
    if expected_identity is not None and identity != expected_identity:
        raise ValueError("existing relink identity differs from the requested build")
    completion = _read_object(completion_path, budget=budget, role="completion")
    expected_completion: JsonObject = {
        "schema_version": "er_commons.document_link_completion.v1",
        "extraction_id": candidate_id,
        "status": "complete_with_warnings",
        "completion_last": True,
        "artifact_inventory_sha256": (
            budget.hash_file(
                inventory_path, role="managed_inventory", source_id=candidate_id, root=root
            )
            if budget is not None
            else sha256_file(inventory_path)
        ),
        "preservation_status": "passed",
        "undeclared_difference_count": 0,
    }
    equivalence = root / _SUPPORT_PATHS["fc1_rebuilt_equivalence"]
    if equivalence.is_file():
        expected_completion.update(
            schema_version="er_commons.document_link_completion.v2",
            fc1_rebuilt_equivalence_sha256=str(
                _read_object(equivalence, budget=budget)["equivalence_sha256"]
            ),
        )
    if completion != expected_completion:
        raise ValueError("relink completion fields differ")
    if budget is not None:
        verify_inventory_metadata(
            root,
            _read_object(inventory_path, budget=budget, role="managed_inventory"),
            budget=budget,
            source_id=candidate_id,
        )
    elif _read_object(inventory_path, budget=budget, role="managed_inventory") != build_inventory(
        root
    ):
        raise ValueError("relink inventory differs from managed files")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("relink candidate contains a managed symlink")
    _validate_published_outputs(root, schema_paths, budget=budget)
    if expected_build is not None:
        _validate_fc1_build_semantics(expected_build)
        _verify_expected_linking_outputs(root, expected_build, budget=budget)
    return completion_path


def _write_candidate(
    root: Path,
    source: CandidateSource,
    build: RelinkBuild,
    identity: JsonObject,
    schema_paths: Mapping[str, Path],
    *,
    budget: VerificationBudget | None = None,
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
    support_files, inherited_files = _copy_preserved_support(source, root, budget)
    for role, path in _SUPPORT_PATHS.items():
        if role not in build.support:
            continue
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
        summary = remapper.value(_read_object(upstream_summary, budget=budget))
        summary["schema_version"] = "er_commons.document_link_summary.v1"
        summary["candidate_id"] = identity["extraction_id"]
        summary["document_link_accounting"] = build.support["accounting"]
        write_json(root / "records/canonicalization_summary.json", summary)
    if budget is not None:
        for schema_path in schema_paths.values():
            budget.reserve_read(
                schema_path, role="schema", source_id="linking", root=schema_path.parent
            )
    validators = _output_validators(schema_paths)
    _validate_pre_completion_outputs(
        validators=validators, identity=identity, manifest=manifest, build=build
    )
    inventory_path = write_inventory(root, recorded_files=inherited_files)
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
    if "fc1_rebuilt_equivalence" in build.support:
        completion.update(
            schema_version="er_commons.document_link_completion.v2",
            fc1_rebuilt_equivalence_sha256=build.support["fc1_rebuilt_equivalence"][
                "equivalence_sha256"
            ],
        )
    _validate_schema_value(validators["completion"], completion, "completion")
    write_json(root / "records/completion_record.json", completion)


def _copy_preserved_support(
    source: CandidateSource,
    root: Path,
    budget: VerificationBudget | None,
) -> tuple[list[JsonObject], dict[str, JsonObject]]:
    """Copy only explicitly inventoried support and propagate its recorded digest."""
    support_files: list[JsonObject] = []
    inherited_files: dict[str, JsonObject] = {}
    source_inventory_path = source.root / "records/artifact_inventory.json"
    source_rows = (
        _read_object(source_inventory_path, budget=budget, role="managed_inventory")["files"]
        if source_inventory_path.is_file()
        else []
    )
    source_inventory = {row["path"]: row for row in source_rows}
    for item in source.manifest.get("support_files", []):
        relative = str(item["path"])
        if relative not in source_inventory:
            raise ValueError(f"inherited support lacks sealed inventory binding: {relative}")
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"inherited support path escapes candidate: {relative}")
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source.root / relative, destination)
        inherited_files[relative] = source_inventory[relative]
        support_files.append(
            {
                **item,
                "sha256": source_inventory[relative]["sha256"],
                "reused_from_structured_candidate": True,
            }
        )
    return support_files, inherited_files


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
    _validate_fc1_build_semantics(build)


def _validate_fc1_build_semantics(build: RelinkBuild) -> None:
    """Reconstruct FC1 provenance and accounting for publication and reuse."""
    context = build.figure_validation_inputs
    if context is not None:
        validate_caption_figure_alias_evidence(
            aliases=list(build.products.target_aliases),
            entries=list(build.support["target_index"]["entries"]),
            qualification=build.support["figure_qualification"],
            inputs=context,
        )


def _validate_published_outputs(
    root: Path, schema_paths: Mapping[str, Path], *, budget: VerificationBudget | None = None
) -> None:
    def read(path: Path) -> JsonObject:
        return _read_object(path, budget=budget)

    if budget is not None:
        for schema_path in schema_paths.values():
            budget.reserve_read(
                schema_path, role="schema", source_id="linking", root=schema_path.parent
            )
    validators = _output_validators(schema_paths)
    _validate_schema_value(
        validators["identity"], read(root / "records/extraction_identity.json"), "identity"
    )
    manifest = read(root / "records/manifest.json")
    _validate_schema_value(validators["manifest"], manifest, "manifest")
    _validate_schema_value(
        validators["inventory"], read(root / "records/artifact_inventory.json"), "inventory"
    )
    _validate_schema_value(
        validators["completion"],
        read(root / "records/completion_record.json"),
        "completion",
    )
    row_counts: dict[str, int] = {}
    for role, relative in _OUTPUT_ROW_PATHS.items():
        if budget is not None:
            budget.reserve_read(
                root / relative, role="linking_records", source_id="linking", root=root
            )
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
        if not (root / relative).is_file():
            continue
        _validate_schema_value(validators["support"], read(root / relative), f"support.{role}")
    target_index = read(root / _SUPPORT_PATHS["target_index"])
    figure_support = root / _SUPPORT_PATHS["figure_qualification"]
    if (
        target_index.get("schema_version") == "er_commons.cross_reference_target_index.v4"
        and not figure_support.is_file()
    ):
        raise ValueError("v4 target index lacks figure qualification support")


def _verify_expected_linking_outputs(
    root: Path, build: RelinkBuild, *, budget: VerificationBudget | None = None
) -> None:
    """Compare reuse against regenerated linking-owned records, never large source payloads."""

    def read(path: Path) -> JsonObject:
        return _read_object(path, budget=budget)

    expected_rows = _product_rows(build.products)
    for role, relative in _OUTPUT_ROW_PATHS.items():
        if budget is not None:
            budget.reserve_read(
                root / relative, role="linking_records", source_id="linking", root=root
            )
        if tuple(read_jsonl(root / relative)) != expected_rows[role]:
            raise ValueError(f"existing relink {role} rows differ from requested build")
    for role, relative in _SUPPORT_PATHS.items():
        if role not in build.support:
            continue
        if read(root / relative) != build.support[role]:
            raise ValueError(f"existing relink support differs from requested build: {role}")
    summary_path = root / "records/canonicalization_summary.json"
    if (
        summary_path.is_file()
        and read(summary_path).get("document_link_accounting") != build.support["accounting"]
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


def _read_object(
    path: Path, *, budget: VerificationBudget | None = None, role: str = "input_binding"
) -> JsonObject:
    """Read one selected record, reserving accepted-input bytes when requested."""
    if budget is not None:
        budget.reserve_read(path, role=role, source_id="linking", root=path.parent)
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _verify_digest(
    path: Path,
    expected: str,
    label: str,
    *,
    budget: VerificationBudget | None = None,
    role: str = "input_binding",
) -> None:
    if not path.is_file():
        raise ValueError(f"{label} is absent: {path}")
    if (
        budget is not None
        and role == "managed_inventory"
        and path.stat().st_size > budget.hash_file_limit
    ):
        budget.check_metadata(path, role=role, source_id=label, root=path.parent)
        return
    digest = (
        budget.hash_file(path, role=role, source_id=label, root=path.parent)
        if budget is not None
        else sha256_file(path)
    )
    if digest != expected:
        raise ValueError(f"{label} seal differs (SHA-256): {path}")


def _verify_completion_inventory(
    completion_path: Path,
    inventory_path: Path,
    *,
    label: str,
    budget: VerificationBudget | None = None,
) -> None:
    """Validate terminal seals and choose explicit deep or compact managed closure."""
    root = completion_path.parent.parent
    if inventory_path.parent.parent != root:
        raise ValueError(f"{label} terminal records have different roots")
    if budget is not None:
        budget.reserve_read(completion_path, role="completion", source_id=label, root=root)
        budget.reserve_read(inventory_path, role="managed_inventory", source_id=label, root=root)
    completion = _read_object(completion_path)
    if completion.get("status") not in {"complete", "complete_with_warnings"}:
        raise ValueError(f"{label} completion is not terminal")
    recorded_digest = completion.get("artifact_inventory_sha256")
    if budget is not None and inventory_path.stat().st_size > budget.hash_file_limit:
        inventory_digest = recorded_digest
    else:
        inventory_digest = (
            budget.hash_file(inventory_path, role="managed_inventory", source_id=label, root=root)
            if budget is not None
            else sha256_file(inventory_path)
        )
    if not isinstance(recorded_digest, str) or recorded_digest != inventory_digest:
        raise ValueError(f"{label} completion does not seal its inventory")
    inventory = _read_object(inventory_path)
    if budget is not None:
        verify_inventory_metadata(root, inventory, budget=budget, source_id=label)
    elif inventory != build_inventory(root):
        raise ValueError(f"{label} inventory differs from managed files")


def _owned_code_bundle_sha256(budget: VerificationBudget | None = None) -> str:
    """Bind every output-affecting linking module in stable repository order."""
    repo_root = Path(__file__).resolve().parents[4]
    modules = (
        "construction",
        "detection",
        "errors",
        "exact_resolution",
        "fc1_equivalence",
        "figure_aliases",
        "indexing",
        "linking_core",
        "linking_policy",
        "machine_link_resolution",
        "policy",
        "relink_preflight",
        "relink_publication",
        "relinking",
        "relinking_config",
        "resolution",
        "reviewed_navigation",
        "source_scope",
        "storage",
        "table_aliases",
        "types",
    )
    relative_paths = sorted(
        [f"src/er_commons/document_records/document_references/{name}.py" for name in modules]
        + [
            "src/er_commons/artifact_io.py",
            "src/er_commons/artifact_verification.py",
            "src/er_commons/document_publication/accepted_inputs.py",
            "src/er_commons/document_publication/candidate_identity_validation.py",
            "src/er_commons/document_parsing/content_parsing/sources.py",
            "src/er_commons/document_publication/sources.py",
            "src/er_commons/document_records/record_mapping/publication.py",
            "src/er_commons/document_records/record_mapping/errors.py",
            "src/er_commons/source_family_catalog.py",
            "src/er_commons/source_release/models.py",
            "src/er_commons/document_publication/config.py",
            "src/er_commons/document_publication/production_identity.py",
            "src/er_commons/document_publication/identity.py",
            "src/er_commons/document_publication/records.py",
            "src/er_commons/document_publication/storage.py",
            "src/er_commons/collection_processing/contract.py",
        ]
    )
    return canonical_json_sha256(
        [
            {
                "path": relative,
                "sha256": (
                    budget.hash_file(
                        repo_root / relative, role="code", source_id="linking", root=repo_root
                    )
                    if budget is not None
                    else sha256_file(repo_root / relative)
                ),
            }
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
