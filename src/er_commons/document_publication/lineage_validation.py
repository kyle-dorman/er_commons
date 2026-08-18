"""Validate config joins and already-sealed document-process artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.config import HierarchyDisposition
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.document_publication.published_document import ProducerLineage
from er_commons.document_publication.records import ArtifactRef

JsonObject = dict[str, Any]


def validate_lineage_bindings(
    *,
    configs: ProcessConfigs,
    source_id: str,
    disposition: HierarchyDisposition,
    lineage: ProducerLineage,
    data_root: Path,
    project_root: Path | None = None,
    lineage_mode: Literal["sealed_inputs", "fresh_build"] = "sealed_inputs",
) -> tuple[Path, ArtifactRef | None]:
    """Validate every derivable config and sealed-artifact lineage join."""
    root = project_root or Path(__file__).resolve().parents[3]
    verify_seals = project_root is not None
    record_mapping = _json(configs.record_mapping)
    correction = _json(configs.hierarchy_inference)
    document_structure = _json(configs.document_structure)
    cross_reference = _json(configs.document_reference_linking)
    if lineage_mode == "fresh_build":
        return validate_fresh_build_templates(
            configs=configs,
            source_id=source_id,
            disposition=disposition,
            data_root=data_root,
        )
    mismatches = _producer_mismatches(record_mapping, correction, document_structure, lineage)
    _validate_candidate_paths(document_structure, mismatches)
    final_root = Path(".")
    if verify_seals:
        validate_current_hierarchy_identity(
            data_root,
            configs.hierarchy_inference,
            document_structure,
            mismatches,
        )
        final_root = _validate_cross_reference_config(
            data_root, source_id, cross_reference, mismatches
        )
    authorization = None
    if disposition.authority == "bounded_acceptance":
        authorization = _validate_bounded_binding(
            data_root, configs, source_id, disposition, correction, document_structure, mismatches
        )
    if verify_seals:
        _validate_existing_candidates(
            data_root, root, document_structure, cross_reference, disposition, mismatches
        )
    if mismatches:
        raise ValueError(
            "document-process lineage preflight failed before PDF work: " + "; ".join(mismatches)
        )
    return final_root, authorization


def validate_current_hierarchy_identity(
    data_root: Path,
    config_path: Path,
    document_structure: JsonObject,
    mismatches: list[str],
) -> None:
    """Report whether a downstream config names the currently derived hierarchy ID."""
    # Keep the generic lineage helpers importable by synthetic tests without loading
    # the document-specific hierarchy package. Production preflight takes this branch.
    from er_commons.hierarchy_inference.preflight import prepare_run

    try:
        current_candidate_id = prepare_run(data_root, config_path).candidate_id
    except (OSError, ValueError) as error:
        mismatches.append(f"current hierarchy identity cannot be derived: {error}")
        return
    configured_candidate_id = document_structure.get("hierarchy_candidate_id")
    if configured_candidate_id != current_candidate_id:
        mismatches.append(
            "document_structure hierarchy candidate is stale for current code/config: "
            f"configured={configured_candidate_id}, derived={current_candidate_id}"
        )


def _producer_mismatches(
    record_mapping: JsonObject,
    correction: JsonObject,
    document_structure: JsonObject,
    lineage: ProducerLineage,
) -> list[str]:
    expected = {
        "record_mapping baseline producer": (
            record_mapping.get("producer_run_id"),
            lineage.baseline,
        ),
        "correction hierarchy producer": (correction.get("producer_run_id"), lineage.hierarchy),
        "document_structure baseline producer": (
            document_structure.get("baseline_producer_run_id"),
            lineage.baseline,
        ),
        "document_structure hierarchy producer": (
            document_structure.get("hierarchy_producer_run_id"),
            lineage.hierarchy,
        ),
    }
    return [
        f"{label}: configured={configured}, predicted={predicted}"
        for label, (configured, predicted) in expected.items()
        if configured != predicted
    ]


def _validate_candidate_paths(document_structure: JsonObject, mismatches: list[str]) -> None:
    pairs = (
        (
            "document_structure baseline candidate",
            "baseline_candidate_id",
            "baseline_candidate_relative_root",
        ),
        (
            "document_structure hierarchy candidate",
            "hierarchy_candidate_id",
            "hierarchy_candidate_relative_root",
        ),
    )
    for label, id_field, path_field in pairs:
        configured_id = document_structure.get(id_field)
        configured_path = document_structure.get(path_field)
        path_id = Path(configured_path).name if isinstance(configured_path, str) else None
        if configured_id != path_id:
            mismatches.append(f"{label} path: configured={configured_id}, path_candidate={path_id}")


def _validate_cross_reference_config(
    data_root: Path,
    source_id: str,
    config: JsonObject,
    mismatches: list[str],
) -> Path:
    upstream_id = config.get("upstream_candidate_id")
    artifact_value = config.get("artifact_relative_root")
    artifact_root = Path(artifact_value) if isinstance(artifact_value, str) else Path(".")
    if (
        not isinstance(artifact_value, str)
        or artifact_root.is_absolute()
        or ".." in artifact_root.parts
    ):
        mismatches.append("cross-reference artifact root is missing or not contained")
    if config.get("source_id") != source_id:
        mismatches.append("cross-reference source differs from selected source")
    manifest_value = config.get("source_manifest_relative_path")
    manifest_path = (
        (data_root / manifest_value).resolve() if isinstance(manifest_value, str) else None
    )
    if (
        manifest_path is None
        or not manifest_path.is_relative_to(data_root.resolve())
        or not manifest_path.is_file()
        or sha256_file(manifest_path) != config.get("source_manifest_sha256")
    ):
        mismatches.append("cross-reference source manifest seal differs")
    if not isinstance(upstream_id, str):
        mismatches.append("cross-reference upstream candidate ID is missing")
        return artifact_root
    upstream_root = data_root / artifact_root / upstream_id
    completion = upstream_root / "records/completion_record.json"
    inventory = upstream_root / "records/artifact_inventory.json"
    if not completion.is_file() or not inventory.is_file():
        mismatches.append(f"cross-reference document_structure input is missing: {upstream_root}")
    else:
        if sha256_file(completion) != config.get("upstream_completion_sha256"):
            mismatches.append("cross-reference upstream completion checksum differs")
        if sha256_file(inventory) != config.get("upstream_inventory_sha256"):
            mismatches.append("cross-reference upstream inventory checksum differs")
    return artifact_root


def _validate_bounded_binding(
    data_root: Path,
    configs: ProcessConfigs,
    source_id: str,
    disposition: HierarchyDisposition,
    correction: JsonObject,
    document_structure: JsonObject,
    mismatches: list[str],
) -> ArtifactRef | None:
    relative = disposition.authorization_relative_path
    if relative is None:
        mismatches.append("bounded hierarchy disposition has no authorization path")
        return None
    if document_structure.get("bounded_acceptance_relative_path") != relative.as_posix():
        mismatches.append("document_structure bounded-authorization path differs from run spec")
    path = (data_root / relative).resolve()
    if not path.is_relative_to(data_root.resolve()) or not path.is_file():
        mismatches.append(f"bounded authorization is missing: {path}")
        return None
    evidence = _json(path)
    candidate = evidence.get("candidate")
    identity = candidate.get("identity") if isinstance(candidate, dict) else None
    scope = evidence.get("scope")
    if not isinstance(identity, dict) or not isinstance(scope, dict):
        mismatches.append("bounded authorization lacks candidate identity or scope")
        return None
    if identity.get("candidate_id") != document_structure.get("hierarchy_candidate_id"):
        mismatches.append(
            "document_structure hierarchy candidate differs from bounded authorization"
        )
    if identity.get("config_sha256") != sha256_file(configs.hierarchy_inference):
        mismatches.append("bounded authorization correction config is stale")
    if (
        evidence.get("status") != "accepted_with_known_limitations"
        or scope.get("source_id") != source_id
        or scope.get("corpus_wide_acceptance") is not False
        or correction.get("publication_authorization") != "bounded_acceptance"
    ):
        mismatches.append("bounded authorization status, scope, or correction policy differs")
    return ArtifactRef(path=path.relative_to(data_root).as_posix(), sha256=sha256_file(path))


def _validate_existing_candidates(
    data_root: Path,
    project_root: Path,
    document_structure: JsonObject,
    cross_reference: JsonObject,
    disposition: HierarchyDisposition,
    mismatches: list[str],
) -> None:
    baseline_id = document_structure.get("baseline_candidate_id")
    baseline_path = document_structure.get("baseline_candidate_relative_root")
    if isinstance(baseline_id, str) and isinstance(baseline_path, str):
        _capture(
            "document_structure baseline candidate",
            lambda: _verify_sealed_candidate((data_root / baseline_path).resolve(), baseline_id),
            mismatches,
        )
    hierarchy_id = document_structure.get("hierarchy_candidate_id")
    hierarchy_path = document_structure.get("hierarchy_candidate_relative_root")
    if isinstance(hierarchy_id, str) and isinstance(hierarchy_path, str):
        hierarchy_root = (data_root / hierarchy_path).resolve()
        _capture(
            "document_structure hierarchy candidate",
            lambda: _verify_sealed_candidate(hierarchy_root, hierarchy_id),
            mismatches,
        )
    upstream_id = cross_reference.get("upstream_candidate_id")
    artifact_root = cross_reference.get("artifact_relative_root")
    if isinstance(upstream_id, str) and isinstance(artifact_root, str):
        _capture(
            "cross-reference document_structure candidate",
            lambda: _verify_sealed_candidate(
                (data_root / artifact_root / upstream_id).resolve(), upstream_id
            ),
            mismatches,
        )


def _verify_sealed_candidate(root: Path, candidate_id: str) -> None:
    """Verify completion and inventory seals without importing a transformation."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    completion = _json(completion_path)
    inventory = _json(inventory_path)
    observed_id = completion.get("candidate_id") or completion.get("extraction_id")
    if observed_id != candidate_id or root.name != candidate_id:
        raise ValueError("candidate ID differs from its completion or path")
    expected_inventory = completion.get("artifact_inventory_sha256")
    if expected_inventory not in {sha256_file(inventory_path), canonical_digest(inventory)}:
        raise ValueError("candidate completion does not seal its inventory")
    files = inventory.get("files")
    if not isinstance(files, list):
        raise ValueError("candidate inventory lacks files")
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("candidate inventory contains an invalid entry")
        path = root / item["path"]
        if (
            not path.is_file()
            or path.stat().st_size != item.get("byte_size")
            or sha256_file(path) != item.get("sha256")
        ):
            raise ValueError(f"candidate managed file differs: {item['path']}")


def _capture(label: str, operation: Any, mismatches: list[str]) -> None:
    try:
        operation()
    except (FileNotFoundError, ValueError) as error:
        mismatches.append(f"{label} is not sealed: {error}")


def _json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
