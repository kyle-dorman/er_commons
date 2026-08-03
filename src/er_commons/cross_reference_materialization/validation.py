"""Independent production-bundle invariants for Task 03E.5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.cross_reference_materialization.construction import CrossReferenceBuild
from er_commons.cross_reference_materialization.errors import CrossReferenceMaterializationError
from er_commons.cross_reference_materialization.targets import remap_value

JsonObject = dict[str, Any]


def validate_build(
    *,
    build: CrossReferenceBuild,
    upstream_root: Path,
    upstream_id: str,
    candidate_id: str,
    schema_path: Path,
    identity_extension: JsonObject,
) -> None:
    """Validate shape, spans, closure, alias correspondence, and preservation."""
    schema = json.loads(schema_path.read_bytes())
    for definition, records in (
        ("canonical_target_alias", build.target_aliases),
        ("cross_reference", build.cross_references),
    ):
        validator = Draft202012Validator(
            {"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
        )
        for record in records:
            validator.validate(record)
    for definition, payload in (
        ("target_index_support", build.support["cross_reference_target_index"]),
        ("summary_support", build.support["cross_reference_summary"]),
        ("preservation_support", build.support["cross_reference_preservation"]),
        ("identity_extension", identity_extension),
    ):
        Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}).validate(
            payload
        )

    blocks = {item["id"]: item for item in build.record_files["canonical/blocks.jsonl"]}
    aliases = {item["id"]: item for item in build.target_aliases}
    targets = {
        item["id"]
        for path in (
            "canonical/documents.jsonl",
            "canonical/pages.jsonl",
            "canonical/sections.jsonl",
            "canonical/tables.jsonl",
            "canonical/figures.jsonl",
        )
        for item in build.record_files[path]
    }
    previous: tuple[int, int, int] | None = None
    for mention in build.cross_references:
        source = blocks[mention["source_record_id"]]
        start, end = mention["source_charspan"]
        _require(
            source["canonical_text"][start:end] == mention["raw_text"],
            "mention span reproduces canonical text",
        )
        _require(mention["regions"] == source["regions"], "mention inherits complete regions")
        _require(mention["raw_links"] == source["raw_links"], "mention inherits raw links")
        order = (source["sequence"], start, end)
        _require(previous is None or previous < order, "mentions have deterministic source order")
        previous = order
        for candidate in mention["candidates"]:
            _require(candidate["target_record_id"] in targets, "candidate target is v3-local")
            _require(
                all(alias_id in aliases for alias_id in candidate["alias_record_ids"]),
                "candidate aliases are v3-local",
            )

    upstream_manifest = json.loads((upstream_root / "records" / "manifest.json").read_bytes())
    upstream_alias_count = next(
        item["record_count"]
        for item in upstream_manifest["record_files"]
        if item["path"] == "canonical/target_aliases.jsonl"
    )
    preserved = [item for item in build.target_aliases if item["alias_origin"] == "upstream_v2"]
    _require(
        len(preserved) == upstream_alias_count == 323, "all 323 upstream aliases are preserved"
    )
    _require(
        {item["upstream_alias_id"] for item in preserved}
        == {
            item["id"] for item in _read_jsonl(upstream_root / "canonical" / "target_aliases.jsonl")
        },
        "alias correspondence is bidirectional",
    )

    for path, candidate_records in build.record_files.items():
        upstream_records = _read_jsonl(upstream_root / path)
        expected = [remap_value(item, upstream_id, candidate_id) for item in upstream_records]
        _require(candidate_records == expected, f"upstream record semantics preserved for {path}")


def validate_serialized_candidate(root: Path, schema_path: Path) -> None:
    """Validate terminal v3 extension and completion shapes after serialization."""
    schema = json.loads(schema_path.read_bytes())
    manifest = json.loads((root / "records" / "manifest.json").read_bytes())
    completion = json.loads((root / "records" / "completion_record.json").read_bytes())
    for definition, payload in (
        ("manifest_extension", manifest["cross_reference_extension"]),
        ("completion", completion),
    ):
        Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}).validate(
            payload
        )


def _read_jsonl(path: Path) -> list[JsonObject]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _require(condition: bool, invariant: str) -> None:
    if not condition:
        raise CrossReferenceMaterializationError(invariant)
