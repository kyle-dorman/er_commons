"""Source-free substantive correspondence proofs for Task 06H."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from er_commons.human_review_support.extraction_review.task06h_visual_correspondence import (
    normalized_records,
    page_visual_evidence,
)

JsonObject = dict[str, Any]
_BASE_KINDS = {"blocks": "block", "sections": "section", "tables": "table"}
_KINDS = {**_BASE_KINDS, "figures": "figure", "images": "image", "assets": "asset"}


def stable_entity_suffix(entity_id: str) -> str:
    """Remove only the producer namespace from a canonical entity ID."""
    namespace, separator, suffix = entity_id.partition("/")
    if not namespace or not separator or "/" not in suffix:
        raise ValueError(f"canonical entity ID has no stable suffix: {entity_id}")
    return suffix


def prove_task04_reuse(
    review_rows: list[JsonObject],
    source_rows: list[JsonObject],
    *,
    baseline_publications_root: Path,
    selected_publications_root: Path,
    accepted_policy_digest: str,
    current_policy_digest: str,
    expected_unchanged: int = 706,
) -> tuple[JsonObject, ...]:
    """Prove Task 04 reuse from candidate metadata and substantive page evidence."""
    unchanged = [row for row in review_rows if row.get("classification") == "unchanged"]
    if len(unchanged) != expected_unchanged:
        raise ValueError(
            f"Task 06H unchanged population differs: expected={expected_unchanged} "
            f"observed={len(unchanged)}"
        )
    sources = _unique_by(source_rows, "logical_source_id", "source correspondence")
    candidate_cache: dict[tuple[str, str], Path] = {}
    evidence_cache: dict[tuple[str, str], dict[str, dict[str, list[JsonObject]]]] = {}
    requirements = _review_requirements(unchanged)
    output: list[JsonObject] = []
    for row in sorted(unchanged, key=lambda item: str(item["entry_id"])):
        source_id = _text(row, "source_id")
        source = sources.get(source_id)
        if source is None:
            raise ValueError(f"Task 06H source correspondence is absent: {source_id}")
        baseline = _object(row, "baseline_evidence")
        baseline_id = _text(baseline, "candidate_id")
        selected_id = _text(source, "replacement_candidate_id")
        baseline_root = _candidate_root(baseline_publications_root, source_id, baseline_id)
        selected_root = _candidate_root(selected_publications_root, source_id, selected_id)
        for label, root, candidate_id, completion_ref in (
            ("Task 03J", baseline_root, baseline_id, None),
            ("Task 06G", selected_root, selected_id, source.get("replacement_completion_ref")),
        ):
            cache_key = (label, candidate_id)
            if cache_key not in candidate_cache:
                _verify_candidate(root, candidate_id, source_id, completion_ref)
                candidate_cache[cache_key] = root
                evidence_cache[cache_key] = _load_requested_evidence(root, requirements[source_id])
        try:
            proof = _prove_review_row(
                row,
                baseline_root,
                selected_root,
                evidence_cache[("Task 03J", baseline_id)],
                evidence_cache[("Task 06G", selected_id)],
                policy_compatible=accepted_policy_digest == current_policy_digest,
            )
        except EvidenceMappingError as error:
            proof = {
                "entry_id": _text(row, "entry_id"),
                "source_id": source_id,
                "physical_page": _integer(baseline, "physical_page"),
                "baseline_disposition": _text(baseline, "disposition"),
                "baseline_candidate_id": baseline_id,
                "selected_candidate_id": selected_id,
                "page_mapping": None,
                "entity_mappings": {},
                "substantive_evidence_equal": False,
                "policy_compatible": accepted_policy_digest == current_policy_digest,
                "correspondence_result": "rejected_ambiguous",
                "result_status": "finite_result",
                "reason": str(error),
            }
        output.append(proof)
    if len({str(row["entry_id"]) for row in output}) != expected_unchanged:
        raise ValueError("Task 06H unchanged entry IDs are not unique")
    return tuple(output)


def map_eligible_figures(
    qualification: JsonObject,
    *,
    selected_candidate_root: Path,
    expected_candidate_id: str,
    expected_count: int = 178,
) -> tuple[JsonObject, ...]:
    """Map eligible 06F targets to exact 06G figure, caption, image, and page rows."""
    _verify_candidate(selected_candidate_root, expected_candidate_id, "deir_main", None)
    decisions = _objects(qualification.get("decisions"), "Task 06F decisions")
    eligible = [row for row in decisions if row.get("eligibility") == "eligible"]
    if len(eligible) != expected_count:
        raise ValueError(
            f"Task 06F eligible population differs: expected={expected_count} "
            f"observed={len(eligible)}"
        )
    canonical = selected_candidate_root / "content/canonical"
    figures = _records_by_suffix(canonical / "figures.jsonl")
    blocks = _records_by_suffix(canonical / "blocks.jsonl")
    images = _records_by_suffix(canonical / "images.jsonl")
    pages = _records_by_suffix(canonical / "pages.jsonl")
    mapped = [
        _map_figure(decision, figures=figures, blocks=blocks, images=images, pages=pages)
        for decision in sorted(eligible, key=lambda item: str(item["figure_id"]))
    ]
    if len({str(row["qualification_figure_id"]) for row in mapped}) != expected_count:
        raise ValueError("Task 06F eligible figure IDs are not unique")
    return tuple(mapped)


def _prove_review_row(
    row: JsonObject,
    baseline_root: Path,
    selected_root: Path,
    baseline_index: dict[str, dict[str, list[JsonObject]]],
    selected_index: dict[str, dict[str, list[JsonObject]]],
    *,
    policy_compatible: bool,
) -> JsonObject:
    baseline = _object(row, "baseline_evidence")
    source_id = _text(row, "source_id")
    physical_page = _integer(baseline, "physical_page")
    old_entities, old_page = _review_evidence(baseline_index, baseline, source_id, physical_page)
    new_entities, new_page = _review_evidence(selected_index, baseline, source_id, physical_page)
    mappings: dict[str, list[JsonObject]] = {}
    ambiguous = False
    for kind in _KINDS:
        old_by_suffix = _group_by_suffix(old_entities[kind])
        new_by_suffix = _group_by_suffix(new_entities[kind])
        ambiguous = ambiguous or any(
            len(values) != 1 for values in (*old_by_suffix.values(), *new_by_suffix.values())
        )
        mappings[kind] = [
            {
                "stable_suffix": suffix,
                "baseline_id": values[0]["id"],
                "selected_id": new_by_suffix[suffix][0]["id"],
            }
            for suffix, values in sorted(old_by_suffix.items())
            if len(values) == 1 and len(new_by_suffix.get(suffix, ())) == 1
        ]
        if set(old_by_suffix) != set(new_by_suffix):
            ambiguous = True
    equal = normalized_records([old_page], "pages") == normalized_records(
        [new_page], "pages"
    ) and all(
        normalized_records(old_entities[kind], kind) == normalized_records(new_entities[kind], kind)
        for kind in _KINDS
    )
    raw_ids_equal = _text(old_page, "id") == _text(new_page, "id") and all(
        mapping["baseline_id"] == mapping["selected_id"]
        for values in mappings.values()
        for mapping in values
    )
    if ambiguous:
        result = "rejected_ambiguous"
    elif not policy_compatible or not equal:
        result = "new_review_required"
    else:
        result = "reused_unchanged" if raw_ids_equal else "reused_remapped_equivalent"
    return {
        "entry_id": _text(row, "entry_id"),
        "source_id": source_id,
        "physical_page": physical_page,
        "baseline_disposition": _text(baseline, "disposition"),
        "baseline_candidate_id": baseline_root.name,
        "selected_candidate_id": selected_root.name,
        "page_mapping": {
            "stable_suffix": stable_entity_suffix(_text(old_page, "id")),
            "baseline_id": _text(old_page, "id"),
            "selected_id": _text(new_page, "id"),
        },
        "entity_mappings": mappings,
        "substantive_evidence_equal": equal,
        "policy_compatible": policy_compatible,
        "correspondence_result": result,
        "result_status": "proposed" if result == "new_review_required" else "finite_result",
    }


def _review_evidence(
    index: dict[str, dict[str, list[JsonObject]]],
    baseline: JsonObject,
    source_id: str,
    physical_page: int,
) -> tuple[dict[str, list[JsonObject]], JsonObject]:
    page_suffix = f"page/{source_id}/p{physical_page:06d}"
    page = _one(index["pages"].get(page_suffix, ()), f"page {page_suffix}")
    selected: dict[str, list[JsonObject]] = {}
    entity_ids = _object(baseline, "entity_ids_by_kind")
    for plural, singular in _BASE_KINDS.items():
        requested = entity_ids.get(plural)
        if not isinstance(requested, list) or any(
            not isinstance(value, str) for value in requested
        ):
            raise ValueError(f"Task 04 {plural} entity IDs are invalid")
        selected[plural] = [
            _one(index[plural].get(stable_entity_suffix(value), ()), f"{singular} {value}")
            for value in requested
        ]
    selected.update(page_visual_evidence(index, page))
    return selected, page


def _review_requirements(rows: list[JsonObject]) -> dict[str, dict[str, set[str]]]:
    requirements: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        source_id = _text(row, "source_id")
        baseline = _object(row, "baseline_evidence")
        wanted = requirements.setdefault(
            source_id,
            {"pages": set(), "blocks": set(), "sections": set(), "tables": set()},
        )
        page = _integer(baseline, "physical_page")
        wanted["pages"].add(f"page/{source_id}/p{page:06d}")
        entity_ids = _object(baseline, "entity_ids_by_kind")
        for plural in _BASE_KINDS:
            wanted[plural].update(
                stable_entity_suffix(value) for value in _string_list(entity_ids, plural)
            )
    return requirements


def _load_requested_evidence(
    root: Path, requirements: dict[str, set[str]]
) -> dict[str, dict[str, list[JsonObject]]]:
    canonical = root / "content/canonical"
    output = {
        name: _records_by_suffix(canonical / f"{name}.jsonl", wanted_suffixes=wanted)
        for name, wanted in requirements.items()
    }
    for name in ("figures", "images", "assets"):
        output[name] = _records_by_suffix(canonical / f"{name}.jsonl")
    return output


def _map_figure(
    decision: JsonObject,
    *,
    figures: Mapping[str, list[JsonObject]],
    blocks: Mapping[str, list[JsonObject]],
    images: Mapping[str, list[JsonObject]],
    pages: Mapping[str, list[JsonObject]],
) -> JsonObject:
    figure_suffix = stable_entity_suffix(_text(decision, "upstream_figure_id"))
    figure = _one(figures.get(figure_suffix, ()), f"figure {figure_suffix}")
    caption_ids = _string_list(decision, "caption_block_ids")
    image_ids = _string_list(decision, "image_ids")
    mapped_captions = [
        _one(blocks.get(stable_entity_suffix(value), ()), value) for value in caption_ids
    ]
    mapped_images = [
        _one(images.get(stable_entity_suffix(value), ()), value) for value in image_ids
    ]
    expected_page = stable_entity_suffix(_text(decision, "page_id"))
    page = _one(pages.get(expected_page, ()), f"page {expected_page}")
    attachment_ok = sorted(
        stable_entity_suffix(value) for value in _string_list(figure, "caption_block_ids")
    ) == sorted(stable_entity_suffix(value) for value in caption_ids) and sorted(
        stable_entity_suffix(value) for value in _string_list(figure, "image_ids")
    ) == sorted(stable_entity_suffix(value) for value in image_ids)
    caption_text = _text(decision, "caption_text")
    marker = _text(decision, "raw_marker")
    caption_ok = (
        len(mapped_captions) == 1
        and mapped_captions[0].get("canonical_text") == caption_text
        and (caption_text == marker or caption_text.startswith(marker + ":"))
        and mapped_captions[0].get("block_type") == "caption"
    )
    page_ok = page.get("physical_page_number") == _integer(
        decision, "physical_page_number"
    ) and all(
        _record_has_page(record, expected_page)
        for record in [figure, *mapped_captions, *mapped_images]
    )
    classification = _object(decision, "classification")
    classification_ok = (
        figure.get("content_layer") == classification.get("figure_content_layer") == "body"
        and figure.get("is_toc_row") is classification.get("figure_is_toc_row") is False
        and mapped_captions[0].get("content_layer")
        == classification.get("caption_content_layer")
        == "body"
        and mapped_captions[0].get("is_toc_row")
        is classification.get("caption_is_toc_row")
        is False
    )
    if not (attachment_ok and caption_ok and page_ok and classification_ok):
        raise ValueError(f"Task 06F figure attachment proof failed: {decision.get('figure_id')}")
    return {
        "qualification_figure_id": _text(decision, "figure_id"),
        "upstream_figure_id": _text(decision, "upstream_figure_id"),
        "selected_figure_id": _text(figure, "id"),
        "stable_figure_suffix": figure_suffix,
        "raw_marker": marker,
        "caption_text": caption_text,
        "physical_page_number": _integer(decision, "physical_page_number"),
        "selected_page_id": _text(page, "id"),
        "caption_mappings": _id_mappings(caption_ids, mapped_captions),
        "image_mappings": _id_mappings(image_ids, mapped_images),
        "attachment_status": "verified",
    }


def _verify_candidate(
    root: Path, candidate_id: str, source_id: str, completion_ref: object
) -> None:
    completion_path = root / "records/completion_record.json"
    completion = _read_object(completion_path)
    if (
        completion.get("candidate_id") != candidate_id
        or completion.get("completion_last") is not True
        or completion.get("raw_docling_status") != "SUCCESS"
        or _object(completion, "source").get("source_id") != source_id
    ):
        raise ValueError(f"candidate completion is invalid: {candidate_id}")
    if completion_ref is not None:
        reference = completion_ref if isinstance(completion_ref, dict) else {}
        if reference.get("sha256") != _sha256(completion_path):
            raise ValueError(f"candidate completion reference differs: {candidate_id}")
    inventory_path = root / "records/artifact_inventory.json"
    inventory_ref = _object(completion, "candidate_inventory")
    if inventory_ref.get("sha256") != _sha256(inventory_path):
        raise ValueError(f"candidate inventory reference differs: {candidate_id}")
    inventory = _read_object(inventory_path)
    files = inventory.get("files")
    if not isinstance(files, list) or any(not isinstance(row, dict) for row in files):
        raise ValueError(f"candidate inventory is invalid: {candidate_id}")
    _verify_evidence_files(root, files, candidate_id)


def _verify_evidence_files(root: Path, files: list[JsonObject], candidate_id: str) -> None:
    """Verify every canonical payload this module may use against the sealed inventory."""
    by_path = {row.get("path"): row for row in files}
    names = ("pages", "blocks", "sections", "tables", "figures", "images", "assets")
    for name in names:
        relative = f"content/canonical/{name}.jsonl"
        reference = by_path.get(relative)
        path = root / relative
        if (
            not isinstance(reference, dict)
            or reference.get("byte_size") != path.stat().st_size
            or reference.get("sha256") != _sha256(path)
        ):
            raise ValueError(f"candidate evidence file differs: {candidate_id}:{relative}")


def _records_by_suffix(
    path: Path, *, wanted_suffixes: set[str] | None = None
) -> dict[str, list[JsonObject]]:
    output: dict[str, list[JsonObject]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            suffix = stable_entity_suffix(_text(value, "id"))
            if wanted_suffixes is None or suffix in wanted_suffixes:
                output.setdefault(suffix, []).append(value)
    return output


def _record_has_page(record: JsonObject, expected_suffix: str) -> bool:
    regions = record.get("regions")
    return isinstance(regions, list) and any(
        isinstance(region, dict)
        and isinstance(region.get("page_id"), str)
        and stable_entity_suffix(region["page_id"]) == expected_suffix
        for region in regions
    )


def _id_mappings(old_ids: list[str], selected: list[JsonObject]) -> list[JsonObject]:
    return [
        {
            "stable_suffix": stable_entity_suffix(old_id),
            "qualification_id": old_id,
            "selected_id": _text(new, "id"),
        }
        for old_id, new in zip(old_ids, selected, strict=True)
    ]


def _candidate_root(publications: Path, source_id: str, candidate_id: str) -> Path:
    return publications / "documents" / source_id / candidate_id


def _group_by_suffix(records: Iterable[JsonObject]) -> dict[str, list[JsonObject]]:
    result: dict[str, list[JsonObject]] = {}
    for record in records:
        result.setdefault(stable_entity_suffix(_text(record, "id")), []).append(record)
    return result


def _unique_by(rows: list[JsonObject], field: str, label: str) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for row in rows:
        key = _text(row, field)
        if key in result:
            raise ValueError(f"{label} has duplicate {field}: {key}")
        result[key] = row
    return result


def _one(values: Iterable[JsonObject], label: str) -> JsonObject:
    items = list(values)
    if len(items) != 1:
        raise EvidenceMappingError(f"Task 06H mapping is not one-to-one: {label}")
    return items[0]


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be a list of objects")
    return value


def _object(value: Mapping[str, Any], field: str) -> JsonObject:
    result = value.get(field)
    if not isinstance(result, dict):
        raise ValueError(f"Task 06H field must be an object: {field}")
    return result


def _text(value: Mapping[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise ValueError(f"Task 06H field must be non-empty text: {field}")
    return result


def _integer(value: Mapping[str, Any], field: str) -> int:
    result = value.get(field)
    if not isinstance(result, int) or isinstance(result, bool):
        raise ValueError(f"Task 06H field must be an integer: {field}")
    return result


def _string_list(value: Mapping[str, Any], field: str) -> list[str]:
    result = value.get(field)
    if not isinstance(result, list) or any(not isinstance(item, str) for item in result):
        raise ValueError(f"Task 06H field must be a string list: {field}")
    return result


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON record is not an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class EvidenceMappingError(ValueError):
    """A finite missing or non-unique stable-suffix mapping result."""


__all__ = ["map_eligible_figures", "prove_task04_reuse", "stable_entity_suffix"]
