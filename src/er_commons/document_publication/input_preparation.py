"""Qualify explicit current run controls without reading source PDFs or models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import assert_contained, write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import authority_root_for_path
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.collection_processing.preflight import prepare_collection_run
from er_commons.document_publication.accepted_inputs import (
    PreparedPublicationInputs,
    _production_identity_path,
    capture_verified_stamps,
    prepare_publication_inputs,
)
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.process_inputs import (
    ProcessConfigs,
    verify_process_resource_contract,
    verify_reused_completion_inputs,
)
from er_commons.source_family_catalog import SourceFamilyCatalog


@dataclass(frozen=True)
class InputPreparationRequest:
    """Explicit controls and output namespace for one source-free readiness check."""

    document_spec: Path
    collection_spec: Path
    output_root: Path
    data_root: Path
    repository_root: Path
    resume_existing: bool = False


def prepare_document_inputs(request: InputPreparationRequest) -> Path:
    """Validate all declared source/config/resource controls before staging readiness."""
    root = request.data_root.resolve()
    output = request.output_root.resolve()
    if not output.is_relative_to(root) or output == root:
        raise ValueError("preparation output root must be a child of the data root")
    existing = output.exists()
    if request.resume_existing != existing:
        raise ValueError("preparation namespace existence differs from explicit resume request")
    budget = VerificationBudget()
    prepared = prepare_publication_inputs(
        root, request.document_spec, repository_root=request.repository_root, budget=budget
    )
    expected_root = root / prepared.spec.artifact_relative_root.parent
    if output != expected_root.resolve():
        raise ValueError("preparation output root differs from document namespace")
    collection_authority = _authority_root(
        request.collection_spec, repository_root=request.repository_root, data_root=root
    )
    collection = CollectionRunSpec.model_validate(
        budget.read_json(
            request.collection_spec,
            root=collection_authority,
            role="config",
            source_id="preparation",
        )
    )
    collection_digest = budget.hash_file(
        request.collection_spec,
        root=collection_authority,
        role="config",
        source_id="preparation",
    )
    document_run_spec = collection.document_run_spec
    if document_run_spec is None:
        raise ValueError("document input preparation requires a document run specification")
    selected_document_spec = (request.collection_spec.parent / document_run_spec).resolve()
    if selected_document_spec != request.document_spec.resolve():
        raise ValueError("collection selects another document specification")
    if list(collection.source_ids) != list(prepared.sources):
        raise ValueError("document and collection source scopes differ")
    markers = completed_candidate_markers(output)
    if markers:
        raise ValueError("preparation namespace already contains completed candidates")
    configs = _validate_process_configs(prepared, output.relative_to(root), budget)
    catalog, raw = _catalog_input(prepared, collection.source_family_catalog_relative_path, budget)
    destination = assert_contained(root, collection.source_family_catalog_relative_path.as_posix())
    if not destination.is_relative_to(output):
        raise ValueError("catalog staging path is outside preparation output root")
    _stage_catalog(destination, raw, budget=budget, root=root)
    prepare_collection_run(root, request.collection_spec, budget=budget)
    report = _readiness(
        prepared, request, configs, catalog, collection_digest, budget, collection=collection
    )
    capture_verified_stamps(budget)
    report_path = destination.parent / "task03h_preparation_readiness.json"
    if report_path.exists():
        if (
            budget.read_json(report_path, root=root, role="run_descriptor", source_id="preparation")
            != report
        ):
            raise ValueError("existing readiness belongs to different controls")
    else:
        write_json_atomic(report_path, report)
    return report_path


def _authority_root(path: Path, *, repository_root: Path, data_root: Path) -> Path:
    """Select one of the two declared spec authorities without external discovery."""
    resolved = path.resolve()
    for root in (data_root.resolve(), repository_root.resolve()):
        if resolved.is_relative_to(root):
            return root
    raise ValueError(f"run specification is outside repository and artifact roots: {path}")


def _validate_process_configs(
    prepared: PreparedPublicationInputs, run_root: Path, budget: VerificationBudget
) -> list[dict[str, Any]]:
    """Retain unique six-config, source, fresh-lineage and resource validation."""
    refs: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for selection in prepared.spec.document_processes:
        verify_reused_completion_inputs(prepared, selection.source_id, budget)
        paths = {
            role: assert_contained(prepared.repository_root, path.as_posix())
            for role, path in selection.configs.model_dump().items()
        }
        if seen.intersection(paths.values()):
            raise ValueError("process config is reused across source selections")
        seen.update(paths.values())
        configs = ProcessConfigs(**paths)
        source_digest = prepared.sources[selection.source_id].sha256
        parsed_values: dict[str, dict[str, Any]] = {}
        for role, path in paths.items():
            value = budget.read_json(
                path, root=prepared.repository_root, role="config", source_id=selection.source_id
            )
            _require_source_config(value, selection.source_id, source_digest, role)
            assert isinstance(value, dict)
            parsed_values[role] = value
        fresh_build = selection.lineage_mode == "fresh_build"
        validate_fresh_build_templates(
            configs=configs,
            source_id=selection.source_id,
            disposition=prepared.spec.hierarchy_disposition(selection.source_id),
            data_root=prepared.data_root,
            declared_artifact_root=run_root if fresh_build else None,
            recorded_manifest_digest=_manifest_digest(prepared, selection.source_id, budget),
            parsed_values=parsed_values,
            reused_roles=(
                set(selection.reused_completions.selected())
                if fresh_build and selection.reused_completions is not None
                else None
            ),
        )
        verify_process_resource_contract(configs, prepared.spec, parsed_values=parsed_values)
        refs.extend(
            {
                "source_id": selection.source_id,
                "process": role,
                "path": path.relative_to(prepared.repository_root).as_posix(),
                "sha256": budget.hash_file(
                    path,
                    root=prepared.repository_root,
                    role="config",
                    source_id=selection.source_id,
                ),
                "byte_size": path.stat().st_size,
            }
            for role, path in paths.items()
        )
    if len(refs) != len(prepared.sources) * 6:
        raise ValueError("preparation must seal exactly six process configs per selected source")
    return refs


def _require_source_config(value: Any, source_id: str, digest: str, role: str) -> None:
    """Reject transplanted template source selections before any execution."""
    if not isinstance(value, dict):
        raise ValueError("process config must be an object")
    declared = value.get("source_id", value.get("source", {}).get("source_id"))
    if declared is not None and declared != source_id:
        raise ValueError(f"process config selects another source: {role}")
    scope = value.get("ordered_materialization_scope")
    if scope is not None and (
        not isinstance(scope, list)
        or len(scope) != 1
        or not isinstance(scope[0], dict)
        or scope[0].get("source_id") != source_id
        or scope[0].get("source_sha256") != digest
    ):
        raise ValueError(f"process config materialization source differs: {role}")
    source = value.get("source", {})
    observed = source.get("expected_sha256", source.get("source_sha256"))
    if observed is not None and observed != digest:
        raise ValueError(f"process config source digest differs: {role}")


def _manifest_digest(
    prepared: PreparedPublicationInputs, source_id: str, budget: VerificationBudget
) -> tuple[Path, str]:
    """Use the recorded source manifest seal rather than hashing accepted metadata again."""
    from er_commons.document_publication.sources import manifest_selection_for

    selected = manifest_selection_for(prepared.spec, source_id)
    path = prepared.data_root / selected.source_manifest_path.parent / "completion_record.json"
    completion = budget.read_json(
        path, root=prepared.data_root, role="completion", source_id=source_id
    )
    assert isinstance(completion, dict) and isinstance(completion["manifest"], dict)
    return selected.source_manifest_path, str(completion["manifest"]["sha256"])


def _catalog_input(
    prepared: PreparedPublicationInputs, relative: Path, budget: VerificationBudget
) -> tuple[Path, bytes]:
    """Locate the declared catalog among already-verified recipe artifacts."""
    identity_path = _production_identity_path(
        prepared.spec,
        repository_root=prepared.repository_root,
        data_root=prepared.data_root,
        budget=budget,
    )
    identity_root = authority_root_for_path(
        identity_path,
        repository_root=prepared.repository_root,
        artifact_root=prepared.data_root,
    )
    identity = budget.read_json(
        identity_path,
        root=identity_root,
        role="identity_preimage",
        source_id="preparation",
    )
    assert isinstance(identity, dict)
    references = cast(dict[str, Any], identity)["preimage"]["collection_process_contract"][
        "artifacts"
    ]
    matches = [
        Path(item["path"]) for item in references if Path(item["path"]).name == relative.name
    ]
    if len(matches) != 1:
        raise ValueError("current recipe must declare one catalog matching the staging filename")
    path = assert_contained(prepared.repository_root, matches[0].as_posix())
    budget.reserve_read(
        path, root=prepared.repository_root, role="catalog", source_id="preparation"
    )
    catalog = SourceFamilyCatalog.load(path)
    return path, catalog.raw_bytes


def _stage_catalog(
    destination: Path, raw: bytes, *, budget: VerificationBudget, root: Path
) -> None:
    """Preserve existing bytes and never overwrite a different staged catalog."""
    if destination.exists():
        budget.reserve_read(destination, root=root, role="catalog", source_id="preparation")
        if destination.read_bytes() != raw:
            raise FileExistsError("staged catalog differs from checked current controls")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(raw)


def completed_candidate_markers(run_root: Path) -> list[str]:
    """Inspect only the explicitly selected namespace for completed candidates."""
    return (
        sorted(str(path.relative_to(run_root)) for path in run_root.rglob("completion_record.json"))
        if run_root.exists()
        else []
    )


def _readiness(
    prepared: PreparedPublicationInputs,
    request: InputPreparationRequest,
    configs: list[dict[str, Any]],
    catalog: Path,
    collection_digest: str,
    budget: VerificationBudget,
    *,
    collection: CollectionRunSpec,
) -> dict[str, Any]:
    """Keep historical readiness readers compatible while binding explicit current controls."""
    sizes = {
        row["source_id"]: row["byte_size"]
        for row in budget.observations
        if row["role"] == "source_pdf"
    }
    return {
        "schema_version": "er_commons.task03h_preparation_readiness.v1",
        "status": "ready_for_user_authorized_clean_run",
        "production_extraction_id": prepared.spec.production_extraction_id,
        "production_identity_sha256": _production_identity_digest(prepared, budget),
        "document_run_spec_sha256": prepared.spec_sha256,
        "collection_run_spec_sha256": collection_digest,
        "source_scope": {
            "source_count": len(prepared.sources),
            "page_count": sum(source.pdf_page_count for source in prepared.sources.values()),
            "byte_count": sum(sizes.values()),
            "ordered_source_ids": list(prepared.sources),
        },
        "catalog": {
            "checked_in_path": str(catalog.relative_to(prepared.repository_root)),
            "staged_path": collection.source_family_catalog_relative_path.as_posix(),
            "sha256": budget.hash_file(
                catalog, root=prepared.repository_root, role="config", source_id="preparation"
            ),
            "byte_size": catalog.stat().st_size,
        },
        "owner_configs": configs,
        "resource_policy": prepared.spec.resource_policy.model_dump(mode="json"),
        "freshness": {
            "task_root": request.output_root.resolve().relative_to(prepared.data_root).as_posix(),
            "completed_candidate_markers": [],
            "historical_lineage_pins": [],
        },
        "source_pdf_bytes_read": False,
        "model_files_read": False,
        "producer_identity_derivation_run": False,
        "execution_boundary": "source/model execution not run",
    }


def _production_identity_digest(
    prepared: PreparedPublicationInputs, budget: VerificationBudget
) -> str:
    """Hash a production identity beneath its declared repository or artifact authority."""
    path = _production_identity_path(
        prepared.spec,
        repository_root=prepared.repository_root,
        data_root=prepared.data_root,
        budget=budget,
    )
    root = authority_root_for_path(
        path, repository_root=prepared.repository_root, artifact_root=prepared.data_root
    )
    return budget.hash_file(path, root=root, role="identity_preimage", source_id="preparation")
