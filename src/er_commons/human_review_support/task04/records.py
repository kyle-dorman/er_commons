"""Identity, schema validation, record writing, and atomic Task 04 publication."""

from __future__ import annotations

import json
import shutil
import uuid
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

import er_commons.artifact_io as artifact_io_module
import er_commons.document_parsing.content_parsing.routing_geometry as routing_geometry_module
import er_commons.document_publication.records as publication_records_module
import er_commons.document_publication.storage as publication_storage_module
from er_commons.artifact_io import canonical_json_sha256, sha256_file, write_json_atomic
from er_commons.human_review_support.task04.config import REVIEW_PASS, SCHEMA_VERSION
from er_commons.human_review_support.task04.discovery import DiscoveredInputs
from er_commons.human_review_support.task04.models import (
    BuildIdentity,
    IdentityDependency,
    JsonValue,
    ReviewCard,
)
from er_commons.human_review_support.task04.retained_evidence import retained_exact_evidence
from er_commons.human_review_support.task04.selection import SelectionResult


@dataclass(frozen=True)
class PublicationWorkspace:
    """One unique staging tree and its deterministic final destination."""

    staging_root: Path
    final_root: Path


class RecordValidator:
    """Validate Task 04 records with concise record and JSON-path diagnostics."""

    def __init__(self, schema_root: Path) -> None:
        self.schema_root = schema_root

    def validate(self, name: str, record: dict[str, JsonValue]) -> None:
        """Validate one named record and report every failing instance path."""
        schema_path = self.schema_root / f"{name}.schema.json"
        if not schema_path.is_file():
            raise ValueError(f"Task 04 schema is missing for {name}: {schema_path}")
        try:
            schema = json.loads(schema_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot load Task 04 schema {schema_path}: {error}") from error
        if not isinstance(schema, dict):
            raise ValueError(f"Task 04 schema must be an object: {schema_path}")
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(record),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            details = "; ".join(
                f"{_json_path(error.absolute_path)}: {error.message}" for error in errors
            )
            raise ValueError(f"invalid Task 04 {name} record: {details}")


def create_identity(
    inputs: DiscoveredInputs,
    policy: dict[str, JsonValue],
    implementation_root: Path,
    schema_root: Path,
    renderer_name: str,
    renderer_version: str,
    renderer_scale: float,
    dependencies: tuple[IdentityDependency, ...] | None = None,
) -> BuildIdentity:
    """Bind exact inputs, policy, maintained code, assets, and schemas."""
    policy_sha256 = canonical_json_sha256(policy)
    active_dependencies = dependencies or _identity_dependencies(
        implementation_root, schema_root, renderer_name, renderer_version
    )
    implementation_sha256 = canonical_json_sha256(
        [dependency.to_record() for dependency in active_dependencies]
    )
    input_payload: dict[str, JsonValue] = {
        "catalog_sha256": sha256_file(inputs.catalog_path),
        "readiness_sha256": sha256_file(inputs.readiness_path),
        "upstream": inputs.readiness.get("production_extraction_id"),
        "sources": [
            {
                "source_id": source.source_id,
                "source_sha256": source.sha256,
                "candidate_ids": list(source.candidate_ids),
                "selected_candidate_id": source.selected_candidate_id,
                "selected_completion_sha256": source.selected_completion_sha256,
                "selected_inventory_sha256": source.selected_inventory_sha256,
                "source_pdf_sha256": source.source_pdf_sha256,
            }
            for source in inputs.sources
        ],
        "dependencies": [dependency.to_record() for dependency in active_dependencies],
        "render_scale": renderer_scale,
    }
    input_sha256 = canonical_json_sha256(input_payload)
    identity_payload: dict[str, JsonValue] = {
        "pass": REVIEW_PASS,
        "policy_sha256": policy_sha256,
        "implementation_sha256": implementation_sha256,
        "input_sha256": input_sha256,
    }
    run_id = f"reviewv1-task03h-first-{canonical_json_sha256(identity_payload)[:16]}"
    return BuildIdentity(
        run_id,
        policy,
        policy_sha256,
        implementation_sha256,
        input_sha256,
        active_dependencies,
    )


def reserve_publication(output_root: Path, review_run_id: str) -> PublicationWorkspace:
    """Reserve unique staging without creating or mutating the final run path."""
    final_root = output_root / review_run_id
    if final_root.exists():
        raise FileExistsError(f"review run already exists: {final_root}")
    staging_parent = output_root / ".tmp"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = staging_parent / f"{review_run_id}.{uuid.uuid4().hex}"
    staging.mkdir()
    return PublicationWorkspace(staging, final_root)


def abandon_publication(workspace: PublicationWorkspace) -> None:
    """Remove only the unique unpublished staging tree after a failed build."""
    if workspace.staging_root.exists():
        shutil.rmtree(workspace.staging_root)


def publish(workspace: PublicationWorkspace) -> Path:
    """Atomically rename a completion-sealed staging tree to its final identity."""
    completion = workspace.staging_root / "records" / "review_bundle_manifest.json"
    handoff = workspace.staging_root / "records" / "task03i_handoff.json"
    if not completion.is_file():
        raise ValueError(f"Task 04 staging tree lacks completion manifest: {completion}")
    if not handoff.is_file():
        raise ValueError(f"Task 04 staging tree lacks initial finding handoff: {handoff}")
    if workspace.final_root.exists():
        raise FileExistsError(f"review run appeared during build: {workspace.final_root}")
    workspace.staging_root.rename(workspace.final_root)
    return workspace.final_root


def write_records(
    workspace: PublicationWorkspace,
    inputs: DiscoveredInputs,
    identity: BuildIdentity,
    selection: SelectionResult,
    cards: tuple[ReviewCard, ...],
    generated_files: tuple[Path, ...],
    validator: RecordValidator,
    data_root: Path,
    renderer_name: str,
    renderer_version: str,
    renderer_scale: float,
) -> None:
    """Write and validate durable records, then seal the disposable bundle last."""
    records_root = workspace.staging_root / "records"
    records_root.mkdir(parents=True, exist_ok=True)
    inventory = _input_inventory(inputs, identity, selection, data_root)
    selection_record = _selection_manifest(identity, cards)
    finding_register = _empty_finding_register(identity.review_run_id)
    _validate_write(records_root, "input_inventory", inventory, validator)
    _validate_write(records_root, "selection_manifest", selection_record, validator)
    _validate_write(records_root, "finding_register", finding_register, validator)
    manifest = _bundle_manifest(
        workspace,
        inputs,
        identity,
        cards,
        generated_files,
        records_root,
        renderer_name,
        renderer_version,
        renderer_scale,
    )
    _validate_write(records_root, "review_bundle_manifest", manifest, validator)
    handoff = _empty_task03i_handoff(identity.review_run_id, records_root)
    _validate_write(records_root, "task03i_handoff", handoff, validator)


def _input_inventory(
    inputs: DiscoveredInputs,
    identity: BuildIdentity,
    selection: SelectionResult,
    data_root: Path,
) -> dict[str, JsonValue]:
    """Build the strict all-source review-input inventory."""
    scope_value = inputs.readiness.get("source_scope")
    if not isinstance(scope_value, dict):
        raise ValueError(f"readiness source_scope is not an object: {inputs.readiness_path}")
    return {
        "schema_version": f"{SCHEMA_VERSION}.input_inventory",
        "review_run_id": identity.review_run_id,
        "pass": REVIEW_PASS,
        "input_sha256": identity.input_sha256,
        "upstream": {
            "retained_root_relative_path": inputs.catalog_path.parents[1]
            .relative_to(data_root)
            .as_posix(),
            "readiness_relative_path": inputs.readiness_path.relative_to(
                inputs.catalog_path.parents[1]
            ).as_posix(),
            "readiness_sha256": sha256_file(inputs.readiness_path),
            "catalog_relative_path": inputs.catalog_path.relative_to(
                inputs.catalog_path.parents[1]
            ).as_posix(),
            "catalog_sha256": sha256_file(inputs.catalog_path),
        },
        "scope": scope_value,
        "sources": [source.inventory_record() for source in inputs.sources],
        "populations": {key: value for key, value in selection.populations.items()},
    }


def _selection_manifest(
    identity: BuildIdentity, cards: tuple[ReviewCard, ...]
) -> dict[str, JsonValue]:
    """Serialize selection anchors plus compact exact IDs, never UI payloads."""
    items: list[JsonValue] = []
    for card in cards:
        record = card.item.to_record()
        record["exact_evidence"] = retained_exact_evidence(card)
        items.append(record)
    return {
        "schema_version": f"{SCHEMA_VERSION}.selection_manifest",
        "review_run_id": identity.review_run_id,
        "pass": REVIEW_PASS,
        "selection_policy": dict(identity.policy),
        "selection_policy_sha256": identity.policy_sha256,
        "items": items,
        "queue_counts": dict(Counter(card.item.queue.value for card in cards)),
    }


def _empty_finding_register(review_run_id: str) -> dict[str, JsonValue]:
    """Initialize the first-pass finding workflow without fabricating decisions."""
    return {
        "schema_version": f"{SCHEMA_VERSION}.finding_register",
        "review_run_id": review_run_id,
        "pass": REVIEW_PASS,
        "status": "open_empty",
        "findings": [],
    }


def _empty_task03i_handoff(review_run_id: str, records_root: Path) -> dict[str, JsonValue]:
    """Initialize the checksum-linked Task 03I handoff pending user findings."""
    return {
        "schema_version": f"{SCHEMA_VERSION}.task03i_handoff",
        "review_run_id": review_run_id,
        "pass": REVIEW_PASS,
        "status": "empty_pending_review",
        "finding_register_sha256": sha256_file(records_root / "finding_register.json"),
        "input_inventory_sha256": sha256_file(records_root / "input_inventory.json"),
        "selection_manifest_sha256": sha256_file(records_root / "selection_manifest.json"),
        "review_bundle_manifest_sha256": sha256_file(records_root / "review_bundle_manifest.json"),
        "extraction_findings": [],
    }


def _bundle_manifest(
    workspace: PublicationWorkspace,
    inputs: DiscoveredInputs,
    identity: BuildIdentity,
    cards: tuple[ReviewCard, ...],
    generated_files: tuple[Path, ...],
    records_root: Path,
    renderer_name: str,
    renderer_version: str,
    renderer_scale: float,
) -> dict[str, JsonValue]:
    """Seal durable records and disposable outputs with explicit render bindings."""
    immutable_records = tuple(
        path
        for path in records_root.iterdir()
        if path.name in {"input_inventory.json", "selection_manifest.json"}
    )
    managed = tuple(sorted((*immutable_records, *generated_files)))
    return {
        "schema_version": f"{SCHEMA_VERSION}.review_bundle_manifest",
        "review_run_id": identity.review_run_id,
        "pass": REVIEW_PASS,
        "status": "generated_disposable_bundle",
        "selection_manifest_sha256": sha256_file(records_root / "selection_manifest.json"),
        "identity": {
            "input_sha256": identity.input_sha256,
            "policy_sha256": identity.policy_sha256,
            "implementation_sha256": identity.implementation_sha256,
            "dependencies": [dependency.to_record() for dependency in identity.dependencies],
            "selected_sources": [
                {
                    "source_id": source.source_id,
                    "source_pdf_sha256": source.source_pdf_sha256,
                    "candidate_id": source.selected_candidate_id,
                    "completion_sha256": source.selected_completion_sha256,
                    "inventory_sha256": source.selected_inventory_sha256,
                }
                for source in inputs.sources
                if source.selected_candidate is not None
            ],
        },
        "render": {
            "renderer": renderer_name,
            "renderer_version": renderer_version,
            "scale": renderer_scale,
            "rendered_page_count": sum(len(card.rendered_pages) for card in cards),
        },
        "package_versions": _package_versions(renderer_name, renderer_version),
        "mutable_records": [
            "records/finding_register.json",
            "records/task03i_handoff.json",
        ],
        "render_bindings": [
            {
                "review_item_id": card.item.review_item_id,
                "pages": [
                    {"physical_page": page.physical_page, "path": page.relative_path}
                    for page in card.rendered_pages
                ],
            }
            for card in cards
        ],
        "files": [_file_record(path, workspace.staging_root) for path in managed],
    }


def _validate_write(
    root: Path,
    name: str,
    record: dict[str, JsonValue],
    validator: RecordValidator,
) -> None:
    """Validate before atomically writing one authoritative record."""
    validator.validate(name, record)
    write_json_atomic(root / f"{name}.json", record)


def _file_record(path: Path, root: Path) -> dict[str, JsonValue]:
    """Build one checksummed managed-file entry."""
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _package_versions(renderer_name: str, renderer_version: str) -> dict[str, JsonValue]:
    """Record application and renderer package versions in identity and manifest."""
    return {
        name: package_version
        for name, package_version in _resolved_package_versions(
            renderer_name, renderer_version
        ).items()
    }


def _identity_dependencies(
    implementation_root: Path,
    schema_root: Path,
    renderer_name: str,
    renderer_version: str,
) -> tuple[IdentityDependency, ...]:
    """Resolve every maintained code and package input that can change Task 04 behavior."""
    repo_root = implementation_root.parents[3]
    assets_root = implementation_root / "assets"
    code_paths = (
        ("artifact_io_canonical_hashing", Path(artifact_io_module.__file__)),
        ("routing_displayed_page_transform", Path(routing_geometry_module.__file__)),
        ("document_publication_records", Path(publication_records_module.__file__)),
        ("document_publication_verification", Path(publication_storage_module.__file__)),
    )
    dependencies = [
        IdentityDependency(
            "task04_package",
            "maintained_code_tree",
            implementation_root.relative_to(repo_root).as_posix(),
            _tree_digest(implementation_root),
            None,
        ),
        IdentityDependency(
            "task04_assets",
            "asset_tree",
            assets_root.relative_to(repo_root).as_posix(),
            _tree_digest(assets_root),
            None,
        ),
        IdentityDependency(
            "task04_schemas",
            "schema_tree",
            schema_root.relative_to(repo_root).as_posix(),
            _tree_digest(schema_root),
            None,
        ),
        *[
            IdentityDependency(
                name,
                "maintained_code_file",
                path.relative_to(repo_root).as_posix(),
                sha256_file(path),
                None,
            )
            for name, path in code_paths
        ],
    ]
    package_versions = _resolved_package_versions(renderer_name, renderer_version)
    dependencies.extend(
        IdentityDependency(name, "package", None, None, package_version)
        for name, package_version in sorted(package_versions.items())
    )
    return tuple(sorted(dependencies, key=lambda dependency: dependency.name))


def _resolved_package_versions(renderer_name: str, renderer_version: str) -> dict[str, str]:
    """Resolve runtime packages with behavior in hashing, schemas, geometry, and rendering."""
    return {
        "er-commons": version("er-commons"),
        "jsonschema": version("jsonschema"),
        "pypdf": version("pypdf"),
        "pypdfium2": version("pypdfium2"),
        "Pillow": version("Pillow"),
        "rfc8785": version("rfc8785"),
        renderer_name: renderer_version,
    }


def _tree_digest(root: Path) -> str:
    """Content-bind every maintained file under one implementation root."""
    if not root.is_dir():
        raise ValueError(f"identity input directory is missing: {root}")
    entries: list[dict[str, JsonValue]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts:
            continue
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)})
    if not entries:
        raise ValueError(f"identity input directory contains no files: {root}")
    return canonical_json_sha256(entries)


def _json_path(parts: Iterable[object]) -> str:
    """Format a jsonschema path as a concise JSONPath expression."""
    path = "$"
    for part in parts:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


__all__ = [
    "PublicationWorkspace",
    "RecordValidator",
    "abandon_publication",
    "create_identity",
    "publish",
    "reserve_publication",
    "write_records",
]
