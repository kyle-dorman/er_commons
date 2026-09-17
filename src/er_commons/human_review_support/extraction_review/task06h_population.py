"""Metadata-only population builders for the Task 06H review plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.human_review_support.extraction_review.task06h_evidence import (
    stable_entity_suffix,
)
from er_commons.human_review_support.extraction_review.task06h_selection import SelectedPage

JsonObject = dict[str, Any]


def build_source_registry(
    source_rows: list[JsonObject],
    manifests: tuple[JsonObject, JsonObject],
    old_registry: JsonObject,
) -> tuple[JsonObject, ...]:
    """Bind all 35 selected sources to accepted manifest metadata."""
    manifest_rows = {
        str(row["source_id"]): row
        for manifest in manifests
        for row in _objects(manifest.get("sources"), "source manifest")
    }
    old = {
        str(row["source_id"]): row
        for row in _objects(old_registry.get("entries"), "Task 04 registry")
    }
    output = []
    for row in sorted(source_rows, key=lambda value: str(value["logical_source_id"])):
        logical = _text(row, "logical_source_id")
        physical = _text(row, "selected_physical_source_id")
        selected = _object(row, "selected_source")
        manifest = manifest_rows.get(physical)
        if manifest is None or (manifest.get("sha256"), manifest.get("pdf_page_count")) != (
            selected.get("sha256"),
            selected.get("pdf_page_count"),
        ):
            raise ValueError(f"selected source manifest differs: {physical}")
        output.append(
            {
                "source_id": physical,
                "logical_source_id": logical,
                "selected_candidate_id": _text(row, "replacement_candidate_id"),
                "change_class": _text(row, "change_class"),
                "source_sha256": _text(selected, "sha256"),
                "pdf_page_count": _integer(selected, "pdf_page_count"),
                "source_relative_path": _text(manifest, "local_path"),
                "byte_size": _integer(manifest, "byte_size"),
                "old_registry_status": (
                    "not_reusable_source_substitution"
                    if logical == "deir_appendix_f1"
                    else _text(old[logical], "status")
                ),
                "task06h_registry_status": "pending_human_review",
            }
        )
    if len(output) != 35 or len({row["source_id"] for row in output}) != 35:
        raise ValueError("Task 06H source registry must contain 35 unique sources")
    return tuple(output)


def build_fresh_navigation_rows(
    review_rows: list[JsonObject],
    source_rows: list[JsonObject],
    selected_publications_root: Path,
) -> tuple[JsonObject, ...]:
    """Bind all 51 non-reusable Task 04 rows to exact selected page identities."""
    sources = {str(row["logical_source_id"]): row for row in source_rows}
    selected = [row for row in review_rows if row.get("classification") == "unproven"]
    candidate_pages: dict[tuple[str, str], dict[str, JsonObject]] = {}
    output = []
    for row in sorted(selected, key=lambda value: str(value["entry_id"])):
        source_id = _text(row, "source_id")
        source = sources[source_id]
        candidate_id = _text(source, "replacement_candidate_id")
        key = (source_id, candidate_id)
        if key not in candidate_pages:
            candidate_pages[key] = _verified_pages(
                selected_publications_root / "documents" / source_id / candidate_id,
                candidate_id,
                source_id,
                _object(source, "replacement_completion_ref"),
            )
        baseline = _object(row, "baseline_evidence")
        page = _integer(baseline, "physical_page")
        suffix = f"page/{source_id}/p{page:06d}"
        current = candidate_pages[key].get(suffix)
        if current is None:
            raise ValueError(f"selected review page is absent: {source_id}:{page}")
        output.append(
            {
                "entry_id": _text(row, "entry_id"),
                "source_id": source_id,
                "physical_page": page,
                "baseline_disposition": _text(baseline, "disposition"),
                "baseline_candidate_id": _text(baseline, "candidate_id"),
                "selected_candidate_id": candidate_id,
                "selected_page_id": _text(current, "id"),
                "baseline_entity_ids_by_kind": _object(baseline, "entity_ids_by_kind"),
                "correspondence_result": "new_review_required",
                "result_status": "finite_result",
                "reason": "Task 06G classified repaired-source correspondence as unproven",
            }
        )
    if len(output) != 51:
        raise ValueError(f"fresh navigation population differs: {len(output)}")
    return tuple(output)


def selection_records(
    selections: tuple[SelectedPage, ...], registry: tuple[JsonObject, ...]
) -> tuple[JsonObject, ...]:
    """Attach each selected page to its exact selected candidate."""
    sources = {str(row["source_id"]): row for row in registry}
    return tuple(
        {
            "source_id": row.source_id,
            "selected_candidate_id": sources[row.source_id]["selected_candidate_id"],
            "physical_page": row.physical_page,
            "evidence_kinds": list(row.evidence_kinds),
            "render_action": row.render_action,
            "sample_entry_id": row.entry_id,
        }
        for row in selections
    )


def target_population(
    repairs: JsonObject,
    figure_mappings: tuple[JsonObject, ...],
    *,
    source_rows: list[JsonObject],
    selected_publications_root: Path,
) -> tuple[JsonObject, ...]:
    """Freeze the exact 185 document, structural, and caption-backed targets."""
    output: list[JsonObject] = [
        {
            "target_id": "docv1-55e5ed5711ba804130fd4729efd8fac56a97cec2e19b07321a2621bc30835050",
            "source_id": "feir_appendix_f1",
            "target_kind": "document",
        }
    ]
    structure = _selected_structures(source_rows, selected_publications_root)
    appendix = _object(repairs, "appendix_a")
    for row in _objects(appendix.get("correspondence_records"), "Appendix A repairs"):
        upstream = _text(_object(row, "new_target"), "section_id")
        selected, aliases = _mapped_section(structure["deir_appendix_a"], upstream)
        output.append(
            {
                "target_id": _text(selected, "id"),
                "upstream_structure_target_id": upstream,
                "authoritative_alias_ids": aliases,
                "source_id": "deir_appendix_a",
                "target_kind": "repaired_section",
                "extent": row["logical_content_page_extent"],
                "retained_heading_mappings": [
                    {
                        "upstream_structure_id": block_id,
                        "selected_id": _text(
                            _mapped_one(structure["deir_appendix_a"]["blocks"], block_id),
                            "id",
                        ),
                    }
                    for block_id in row["retained_heading_block_ids"]
                ],
            }
        )
    for chapter, target_id in (
        (
            "8",
            "exv1-997e9c433e8e5ec030a15ca0b34f48eb772b3e54d98ed0c15082b2580c8b0529/section/deir_main/sec003489",
        ),
        (
            "9",
            "exv1-997e9c433e8e5ec030a15ca0b34f48eb772b3e54d98ed0c15082b2580c8b0529/section/deir_main/sec003490",
        ),
    ):
        selected, aliases = _mapped_section(structure["deir_main"], target_id)
        output.append(
            {
                "target_id": _text(selected, "id"),
                "upstream_structure_target_id": target_id,
                "authoritative_alias_ids": aliases,
                "source_id": "deir_main",
                "target_kind": "repaired_chapter",
                "extent": _object(repairs, "main_chapters")[chapter],
            }
        )
    for row in figure_mappings:
        output.append(
            {
                "target_id": row["selected_figure_id"],
                "source_id": "deir_main",
                "target_kind": "caption_backed_figure",
                "physical_page": row["physical_page_number"],
                "marker": row["raw_marker"],
                "selected_page_id": row["selected_page_id"],
                "caption_mappings": row["caption_mappings"],
                "image_mappings": row["image_mappings"],
                "text_only_model_eligibility": "pending_independent_human_disposition",
            }
        )
    ordered = tuple(sorted(output, key=lambda row: str(row["target_id"])))
    if len(ordered) != 185 or len({row["target_id"] for row in ordered}) != 185:
        raise ValueError("Task 06H target population differs from 185 unique targets")
    return ordered


def task03i_record(old: JsonObject, source_rows: list[JsonObject]) -> JsonObject:
    """Rebind the accepted fixed page range without widening its meaning."""
    source_id = _text(old, "source_id")
    selected = next(row for row in source_rows if row["logical_source_id"] == source_id)
    if old.get("status") != "fixed_confirmed" or old.get("physical_pages") != list(range(974, 984)):
        raise ValueError("Task 03I recheck differs from accepted evidence")
    return {
        "source_id": source_id,
        "selected_candidate_id": selected["replacement_candidate_id"],
        "physical_pages": old["physical_pages"],
        "historical_status": "fixed_confirmed",
        "mapping_status": "mapped_explicitly_pending_registry_closure",
    }


def _verified_pages(
    root: Path, candidate_id: str, source_id: str, completion_ref: JsonObject
) -> dict[str, JsonObject]:
    return _verified_records(root, candidate_id, source_id, completion_ref, ("pages",))["pages"]


def _selected_structure(
    source_id: str, source_rows: list[JsonObject], publications: Path
) -> dict[str, dict[str, JsonObject]]:
    source = next(row for row in source_rows if row.get("logical_source_id") == source_id)
    candidate_id = _text(source, "replacement_candidate_id")
    return _verified_records(
        publications / "documents" / source_id / candidate_id,
        candidate_id,
        source_id,
        _object(source, "replacement_completion_ref"),
        ("sections", "blocks", "target_aliases"),
    )


def _selected_structures(
    source_rows: list[JsonObject], publications: Path
) -> dict[str, dict[str, dict[str, JsonObject]]]:
    return {
        source: _selected_structure(source, source_rows, publications)
        for source in ("deir_appendix_a", "deir_main")
    }


def _verified_records(
    root: Path,
    candidate_id: str,
    source_id: str,
    completion_ref: JsonObject,
    names: tuple[str, ...],
) -> dict[str, dict[str, JsonObject]]:
    completion_path = root / "records/completion_record.json"
    if completion_ref.get("sha256") != _sha256(completion_path):
        raise ValueError(f"selected completion reference differs: {candidate_id}")
    completion = _read_object(completion_path)
    if (
        completion.get("candidate_id") != candidate_id
        or _object(completion, "source").get("source_id") != source_id
    ):
        raise ValueError(f"selected candidate identity differs: {candidate_id}")
    inventory_path = root / "records/artifact_inventory.json"
    if _object(completion, "candidate_inventory").get("sha256") != _sha256(inventory_path):
        raise ValueError(f"selected candidate inventory differs: {candidate_id}")
    inventory = _read_object(inventory_path)
    references = {
        str(row.get("path")): row for row in _objects(inventory.get("files"), "candidate inventory")
    }
    output = {}
    for name in names:
        relative = f"content/canonical/{name}.jsonl"
        path = root / relative
        reference = references.get(relative)
        if reference is None or (reference.get("sha256"), reference.get("byte_size")) != (
            _sha256(path),
            path.stat().st_size,
        ):
            raise ValueError(f"selected {name} evidence differs: {candidate_id}")
        output[name] = {stable_entity_suffix(_text(row, "id")): row for row in _read_jsonl(path)}
    return output


def _mapped_one(records: dict[str, JsonObject], upstream_id: str) -> JsonObject:
    result = records.get(stable_entity_suffix(upstream_id))
    if result is None:
        raise ValueError(f"selected structural target is absent: {upstream_id}")
    return result


def _mapped_section(
    records: dict[str, dict[str, JsonObject]], upstream_id: str
) -> tuple[JsonObject, list[str]]:
    matches = []
    for alias in records["target_aliases"].values():
        targets = alias.get("targets")
        if not isinstance(targets, list):
            continue
        for target in targets:
            if isinstance(target, dict) and target.get("upstream_target_id") == upstream_id:
                matches.append((_text(alias, "id"), _text(target, "target_id")))
    target_ids = {target_id for _, target_id in matches}
    if len(target_ids) != 1:
        raise ValueError(f"authoritative structural alias is not unique: {upstream_id}")
    target_id = target_ids.pop()
    selected = _mapped_one(records["sections"], target_id)
    if _text(selected, "id") != target_id:
        raise ValueError(f"authoritative structural alias target differs: {upstream_id}")
    return selected, sorted(alias_id for alias_id, _ in matches)


def _read_jsonl(path: Path) -> list[JsonObject]:
    with path.open(encoding="utf-8") as handle:
        values = [json.loads(line) for line in handle if line.strip()]
    return _objects(values, str(path))


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    return _object({"value": value}, "value")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be a list of objects")
    return value


def _object(value: dict[str, Any], field: str) -> JsonObject:
    result = value.get(field)
    if not isinstance(result, dict):
        raise ValueError(f"Task 06H field must be an object: {field}")
    return result


def _text(value: dict[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise ValueError(f"Task 06H field must be non-empty text: {field}")
    return result


def _integer(value: dict[str, Any], field: str) -> int:
    result = value.get(field)
    if not isinstance(result, int) or isinstance(result, bool):
        raise ValueError(f"Task 06H field must be an integer: {field}")
    return result


__all__ = [
    "build_fresh_navigation_rows",
    "build_source_registry",
    "selection_records",
    "target_population",
    "task03i_record",
]
