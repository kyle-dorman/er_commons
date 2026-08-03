"""Responsibility-owned validation for the human-readable candidate build."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.cross_reference_enrichment.construction import CandidateBuild
from er_commons.cross_reference_enrichment.indexing import NamespaceRemapper
from er_commons.cross_reference_enrichment.storage import read_jsonl
from er_commons.cross_reference_enrichment.types import JsonObject


def validate_candidate_build(
    *,
    build: CandidateBuild,
    upstream_root: Path,
    upstream_candidate_id: str,
    candidate_id: str,
    schema_path: Path,
    identity_extension: JsonObject,
) -> None:
    """Sequence shape, provenance, graph-closure, and preservation policies."""
    schema = json.loads(schema_path.read_bytes())
    _validate_shapes(build, schema, identity_extension)
    _validate_mentions(build)
    _validate_alias_correspondence(build, upstream_root)
    _validate_preserved_records(
        build,
        upstream_root=upstream_root,
        remapper=NamespaceRemapper(upstream_candidate_id, candidate_id),
    )


def validate_serialized_terminal_records(root: Path, schema_path: Path) -> None:
    """Validate manifest extension and completion after completion-last writing."""
    schema = json.loads(schema_path.read_bytes())
    manifest = json.loads((root / "records" / "manifest.json").read_bytes())
    completion = json.loads((root / "records" / "completion_record.json").read_bytes())
    _definition_validator(schema, "manifest_extension").validate(
        manifest["cross_reference_extension"]
    )
    _definition_validator(schema, "completion").validate(completion)


def _validate_shapes(
    build: CandidateBuild, schema: JsonObject, identity_extension: JsonObject
) -> None:
    for alias in build.target_aliases:
        _definition_validator(schema, "canonical_target_alias").validate(alias)
    for mention in build.cross_references:
        _definition_validator(schema, "cross_reference").validate(mention)
    support_definitions = {
        "cross_reference_target_index": "target_index_support",
        "cross_reference_summary": "summary_support",
        "cross_reference_preservation": "preservation_support",
    }
    for role, definition in support_definitions.items():
        _definition_validator(schema, definition).validate(build.support[role])
    _definition_validator(schema, "identity_extension").validate(identity_extension)


def _validate_mentions(build: CandidateBuild) -> None:
    blocks = {
        block["id"]: block for block in build.preserved_record_files["canonical/blocks.jsonl"]
    }
    local_alias_ids = {alias["id"] for alias in build.target_aliases}
    local_target_ids = {
        record["id"]
        for path in (
            "canonical/documents.jsonl",
            "canonical/pages.jsonl",
            "canonical/sections.jsonl",
            "canonical/tables.jsonl",
            "canonical/figures.jsonl",
        )
        for record in build.preserved_record_files[path]
    }
    previous_order: tuple[int, int, int] | None = None
    for mention in build.cross_references:
        source = blocks[mention["source_record_id"]]
        start, end = mention["source_charspan"]
        _require(
            source["canonical_text"][start:end] == mention["raw_text"],
            "mention span reproduces canonical text",
        )
        _require(mention["regions"] == source["regions"], "mention inherits all regions")
        _require(mention["raw_links"] == source["raw_links"], "mention inherits raw links")
        order = (source["sequence"], start, end)
        _require(
            previous_order is None or previous_order < order,
            "mention order follows source order",
        )
        previous_order = order
        for candidate in mention["candidates"]:
            _require(
                candidate["target_record_id"] in local_target_ids,
                "candidate target remains in the v3 namespace",
            )
            _require(
                all(alias_id in local_alias_ids for alias_id in candidate["alias_record_ids"]),
                "candidate aliases remain in the v3 namespace",
            )


def _validate_alias_correspondence(build: CandidateBuild, upstream_root: Path) -> None:
    upstream_aliases = read_jsonl(upstream_root / "canonical" / "target_aliases.jsonl")
    preserved = [alias for alias in build.target_aliases if alias["alias_origin"] == "upstream_v2"]
    _require(len(upstream_aliases) == len(preserved) == 323, "all upstream aliases survive")
    _require(
        {alias["id"] for alias in upstream_aliases}
        == {alias["upstream_alias_id"] for alias in preserved},
        "alias correspondence is exact and bidirectional",
    )


def _validate_preserved_records(
    build: CandidateBuild, *, upstream_root: Path, remapper: NamespaceRemapper
) -> None:
    for path, observed in build.preserved_record_files.items():
        expected = [remapper.value(record) for record in read_jsonl(upstream_root / path)]
        _require(observed == expected, f"preserved semantics differ for {path}")


def _definition_validator(schema: JsonObject, name: str) -> Draft202012Validator:
    return Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{name}"})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
