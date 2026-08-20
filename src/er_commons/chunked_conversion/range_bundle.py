"""Completion-last publication and reuse of source-free range shards."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
    write_json_atomic_streaming,
)
from er_commons.chunked_conversion.range_contract import (
    RangeCompletion,
    RangePlan,
    canonicalize_completions,
    validate_range_completion,
)
from er_commons.chunked_conversion.range_recomposition import (
    OverlapEvidence,
    RangeItem,
    RangeShard,
    validate_range_shard,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


class RangeBundleError(ValueError):
    """An immutable range bundle is missing, corrupt, or differently identified."""


def publish_range_bundle(root: Path, plan: RangePlan, shard: RangeShard) -> Path:
    """Publish one range through unique staging with the completion record last."""
    planned = next((item for item in plan.ranges if item.range_id == shard.range_id), None)
    if planned is None or shard.plan_id != plan.plan_id:
        raise RangeBundleError(
            f"plan={plan.plan_id} range={shard.range_id} path=manifest invariant=planned_range"
        )
    validate_range_shard(plan, shard, require_projections=True)
    final = root / shard.range_id
    if final.exists():
        existing = verify_range_bundle(final, plan, shard.range_id)
        if existing != shard:
            raise RangeBundleError(
                f"plan={plan.plan_id} range={shard.range_id} path={final / 'shard.json'} "
                "invariant=existing_bundle_collision expected=proposed_shard actual=sealed_shard"
            )
        return final
    staging = root / ".tmp" / f"{shard.range_id}.{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    records = staging / "records"
    records.mkdir()
    try:
        write_json_atomic(
            staging / "manifest.json",
            {
                "schema_version": "er_commons.docling_range_manifest.v1",
                "plan_id": plan.plan_id,
                "range_id": shard.range_id,
                "source": plan.inputs.source.model_dump(mode="json"),
                "core": planned.core.model_dump(mode="json"),
                "read": planned.read.model_dump(mode="json"),
                "range_conversion_identity": plan.inputs.range_conversion_identity,
            },
        )
        write_json_atomic_streaming(staging / "shard.json", _shard_to_json(shard))
        inventory_path = records / "artifact_inventory.json"
        inventory = artifact_inventory(
            staging,
            excluded={"records/artifact_inventory.json", "records/completion_record.json"},
        )
        write_json_atomic(inventory_path, inventory)
        verify_inventory(staging, inventory)
        completion = RangeCompletion(
            plan_id=plan.plan_id,
            range_id=shard.range_id,
            source=plan.inputs.source,
            core=planned.core,
            read=planned.read,
            overlap_owners=planned.overlap_owners,
            range_conversion_identity=plan.inputs.range_conversion_identity,
            expected_pages=planned.read.pages,
            converted_pages=planned.read.pages,
            successful_pages=planned.read.pages,
            overlap_pages=tuple(
                page for page in planned.read.pages if page not in planned.core.pages
            ),
            core_owned_pages=planned.core.pages,
            artifact_inventory_path="records/artifact_inventory.json",
            artifact_inventory_sha256=sha256_file(inventory_path),
        )
        write_json_atomic(records / "completion_record.json", completion)
        root.mkdir(parents=True, exist_ok=True)
        staging.rename(final)
        _fsync_directory(final.parent)
    except BaseException:
        # Retain incomplete evidence without making it discoverable as a final child.
        raise
    return final


def verify_range_bundle(root: Path, plan: RangePlan, range_id: str) -> RangeShard:
    """Deep-audit a completed child and deserialize its source-free shard."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    try:
        completion = RangeCompletion.model_validate_json(completion_path.read_bytes())
        validate_range_completion(plan, completion, path=completion_path.as_posix())
        if completion.range_id != range_id:
            raise RangeBundleError(
                f"plan={plan.plan_id} range={range_id} path={completion_path} "
                f"invariant=range_identity actual={completion.range_id}"
            )
        if sha256_file(inventory_path) != completion.artifact_inventory_sha256:
            raise RangeBundleError(
                f"plan={plan.plan_id} range={range_id} path={inventory_path} "
                "invariant=inventory_checksum"
            )
        inventory = read_json_object(inventory_path)
        verify_inventory(root, inventory)
        planned = next(item for item in plan.ranges if item.range_id == range_id)
        manifest = read_json_object(root / "manifest.json")
        expected_manifest = {
            "schema_version": "er_commons.docling_range_manifest.v1",
            "plan_id": plan.plan_id,
            "range_id": range_id,
            "source": plan.inputs.source.model_dump(mode="json"),
            "core": planned.core.model_dump(mode="json"),
            "read": planned.read.model_dump(mode="json"),
            "range_conversion_identity": plan.inputs.range_conversion_identity,
        }
        if manifest != expected_manifest:
            raise RangeBundleError(
                f"plan={plan.plan_id} range={range_id} path={root / 'manifest.json'} "
                "invariant=manifest_identity"
            )
        with (root / "shard.json").open(encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict):
            raise RangeBundleError(
                f"plan={plan.plan_id} range={range_id} path={root / 'shard.json'} "
                "invariant=shard_shape"
            )
        shard = _shard_from_json(payload)
        if shard.plan_id != plan.plan_id or shard.range_id != range_id:
            raise RangeBundleError(
                f"plan={plan.plan_id} range={range_id} path={root / 'shard.json'} "
                "invariant=shard_identity"
            )
        validate_range_shard(plan, shard, require_projections=True)
        return shard
    except RangeBundleError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise RangeBundleError(
            f"plan={plan.plan_id} range={range_id} path={root} invariant=completed_bundle: {error}"
        ) from error


def resume_range_bundles(
    plan: RangePlan,
    root: Path,
    execute: Callable[[str], RangeShard],
) -> tuple[RangeShard, ...]:
    """Reuse deep-verified children and execute only missing or invalid ranges."""
    shards: list[RangeShard] = []
    completions: list[RangeCompletion] = []
    for planned in plan.ranges:
        child_root = root / planned.range_id
        try:
            shard = verify_range_bundle(child_root, plan, planned.range_id)
        except RangeBundleError:
            if child_root.exists():
                raise
            shard = execute(planned.range_id)
            publish_range_bundle(root, plan, shard)
        shards.append(shard)
        completions.append(
            RangeCompletion.model_validate_json(
                (root / planned.range_id / "records" / "completion_record.json").read_bytes()
            )
        )
    canonicalize_completions(plan, tuple(completions))
    return tuple(shards)


def _shard_to_json(shard: RangeShard) -> dict[str, Any]:
    return {
        "schema_version": "er_commons.docling_range_shard.v1",
        "plan_id": shard.plan_id,
        "range_id": shard.range_id,
        "core_pages": list(shard.core_pages),
        "read_pages": list(shard.read_pages),
        "pages": [[page, value] for page, value in shard.pages],
        "items": [
            {
                "collection": item.collection,
                "source_index": item.source_index,
                "local_ref": item.local_ref,
                "source_ref": item.source_ref,
                "pages": list(item.pages),
                "value": item.value,
            }
            for item in shard.items
        ],
        "overlap_evidence": [
            {
                "page": evidence.page,
                "page_digest": evidence.page_digest,
                "record_digests": [list(item) for item in evidence.record_digests],
                "heading_overlay": list(evidence.heading_overlay),
                "alignment_page": evidence.alignment_page,
                "assets": list(evidence.assets),
            }
            for evidence in shard.overlap_evidence
        ],
        "heading_overlay": list(shard.heading_overlay),
        "alignment_pages": list(shard.alignment_pages),
        "assets": list(shard.assets),
    }


def _shard_from_json(payload: dict[str, Any]) -> RangeShard:
    if payload.get("schema_version") != "er_commons.docling_range_shard.v1":
        raise ValueError("range shard schema differs")
    raw_items = payload["items"]
    raw_pages = payload["pages"]
    raw_overlap = payload["overlap_evidence"]
    if not isinstance(raw_items, list) or not isinstance(raw_pages, list):
        raise ValueError("range shard collections are invalid")
    return RangeShard(
        plan_id=str(payload["plan_id"]),
        range_id=str(payload["range_id"]),
        core_pages=tuple(int(value) for value in payload["core_pages"]),
        read_pages=tuple(int(value) for value in payload["read_pages"]),
        pages=tuple((int(page), value) for page, value in raw_pages),
        items=tuple(
            RangeItem(
                collection=str(item["collection"]),
                source_index=int(item["source_index"]),
                local_ref=str(item["local_ref"]),
                source_ref=str(item["source_ref"]),
                pages=tuple(int(value) for value in item["pages"]),
                value=item["value"],
            )
            for item in raw_items
        ),
        overlap_evidence=tuple(
            OverlapEvidence(
                page=int(evidence["page"]),
                page_digest=str(evidence["page_digest"]),
                record_digests=tuple(
                    (str(reference), str(digest))
                    for reference, digest in evidence["record_digests"]
                ),
                heading_overlay=tuple(evidence.get("heading_overlay", [])),
                alignment_page=evidence.get("alignment_page"),
                assets=tuple(evidence.get("assets", [])),
            )
            for evidence in raw_overlap
        ),
        heading_overlay=tuple(payload.get("heading_overlay", [])),
        alignment_pages=tuple(payload.get("alignment_pages", [])),
        assets=tuple(payload.get("assets", [])),
    )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "RangeBundleError",
    "publish_range_bundle",
    "resume_range_bundles",
    "verify_range_bundle",
]
