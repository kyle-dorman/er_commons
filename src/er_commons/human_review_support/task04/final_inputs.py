"""Resolve Task 03J review inputs without rehashing large artifacts."""

from __future__ import annotations

from pathlib import Path

from er_commons.human_review_support.task04.discovery import DiscoveredInputs
from er_commons.human_review_support.task04.final_pass import SOURCE_RELEASE_RELATIVE
from er_commons.human_review_support.task04.json_io import (
    optional_string,
    read_json_object,
    require_integer,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonObject, SourceEvidence

TASK03J_RELATIVE = "pipelines/brisbane_baylands/task_03h_clean_full_v4"
SCOPE_ID = "scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893"


def discover_task03j_inputs(data_root: Path) -> DiscoveredInputs:
    """Build typed final-pass inputs from the sealed Task 03J handoff."""
    task_root = data_root / TASK03J_RELATIVE
    plan_path = task_root / "inputs/task03j_activation_plan.json"
    readiness_path = task_root / "inputs/task03j_preparation_readiness.json"
    catalog_paths = sorted((task_root / "inputs").glob("*source_family_catalog*.json"))
    if len(catalog_paths) != 1:
        raise ValueError(f"expected one Task 03J source catalog; found {len(catalog_paths)}")
    catalog_path = catalog_paths[0]
    plan = read_json_object(plan_path)
    readiness = read_json_object(readiness_path)
    catalog = read_json_object(catalog_path)
    bundle = _contract_bundle(task_root)
    completions = _completion_index(bundle, task_root)
    metadata = _catalog_metadata(catalog)
    sources = tuple(
        _source_evidence(data_root, task_root, order, completions, metadata)
        for order in _object_list(plan, "source_order", plan_path)
    )
    if len(sources) != 35:
        raise ValueError(f"expected 35 Task 03J sources; found {len(sources)}")
    return DiscoveredInputs(catalog_path, readiness_path, catalog, readiness, sources)


def _contract_bundle(task_root: Path) -> JsonObject:
    """Load the final scope bundle containing document completions."""
    path = task_root / f"document_publications/scopes/{SCOPE_ID}/contract_bundle.json"
    return read_json_object(path)


def _catalog_metadata(catalog: JsonObject) -> dict[str, JsonObject]:
    """Index optional role and family fields by source identity."""
    result: dict[str, JsonObject] = {}
    sources = catalog.get("sources")
    for entry in sources if isinstance(sources, list) else []:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source")
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        if not isinstance(source_id, str):
            continue
        result[source_id] = entry
    return result


def _completion_index(bundle: JsonObject, task_root: Path) -> dict[str, JsonObject]:
    """Index validated document completions with useful duplicate diagnostics."""
    path = task_root / "document_publications/scopes" / SCOPE_ID / "contract_bundle.json"
    completions = _object_list(bundle, "document_completions", path)
    indexed: dict[str, JsonObject] = {}
    for index, completion in enumerate(completions):
        source = require_mapping(
            completion.get("source"), path=f"{path}:$.document_completions[{index}].source"
        )
        source_id = require_string(
            source.get("source_id"),
            path=f"{path}:$.document_completions[{index}].source.source_id",
        )
        if source_id in indexed:
            raise ValueError(f"duplicate document completion for source {source_id!r} in {path}")
        indexed[source_id] = completion
    return indexed


def _source_evidence(
    data_root: Path,
    task_root: Path,
    order: JsonObject,
    completions: dict[str, JsonObject],
    metadata: dict[str, JsonObject],
) -> SourceEvidence:
    """Resolve one selected candidate and its source PDF path."""
    source_id = require_string(
        order.get("source_id"), path="activation_plan.source_order[].source_id"
    )
    completion = completions.get(source_id)
    if completion is None:
        raise ValueError(f"Task 03J activation source has no document completion: {source_id}")
    source = require_mapping(completion.get("source"), path=f"completion[{source_id}].source")
    candidate_id = require_string(
        completion.get("candidate_id"), path=f"completion[{source_id}].candidate_id"
    )
    source_pdf = data_root / SOURCE_RELEASE_RELATIVE / f"{source_id}.pdf"
    candidate = task_root / "document_publications/documents" / source_id / candidate_id
    if not source_pdf.is_file() or not candidate.is_dir():
        raise FileNotFoundError(source_pdf if not source_pdf.is_file() else candidate)
    entry = metadata.get(source_id, {})
    inventory = require_mapping(
        completion.get("candidate_inventory"),
        path=f"completion[{source_id}].candidate_inventory",
    )
    return SourceEvidence(
        source_id=source_id,
        document_role=optional_string(
            entry.get("document_role"), path=f"catalog[{source_id}].document_role"
        ),
        parent_source_id=optional_string(
            entry.get("parent_source_id"), path=f"catalog[{source_id}].parent_source_id"
        ),
        sha256=require_string(source.get("sha256"), path=f"completion[{source_id}].source.sha256"),
        byte_size=require_integer(
            order.get("byte_size"), path=f"source_order[{source_id}].byte_size"
        ),
        pdf_page_count=require_integer(
            order.get("pdf_page_count"), path=f"source_order[{source_id}].pdf_page_count", minimum=1
        ),
        source_relative_path=source_pdf.relative_to(data_root).as_posix(),
        source_pdf=source_pdf,
        source_pdf_sha256=require_string(
            source.get("sha256"), path=f"completion[{source_id}].source.sha256"
        ),
        candidate_ids=(candidate_id,),
        selected_candidate=candidate,
        selected_completion_sha256=None,
        selected_inventory_sha256=require_string(
            inventory.get("sha256"), path=f"completion[{source_id}].candidate_inventory.sha256"
        ),
    )


def _object_list(record: JsonObject, field: str, path: Path) -> list[JsonObject]:
    """Read a JSON object array with a path that identifies malformed rows."""
    values = require_list(record.get(field), path=f"{path}:$.{field}")
    return [
        require_mapping(value, path=f"{path}:$.{field}[{index}]")
        for index, value in enumerate(values)
    ]


__all__ = ["TASK03J_RELATIVE", "discover_task03j_inputs"]
