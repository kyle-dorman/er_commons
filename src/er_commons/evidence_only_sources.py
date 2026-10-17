"""Read all frozen evidence inventories without returning reference-answer prose."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import sha256_file
from er_commons.automatic_metric_inputs import source_unit
from er_commons.group_answer_intake import _compact_anchors
from er_commons.pilot_citation_records import index_records
from er_commons.synthetic_intake import SOURCE_FIELDS, verify_binding, verify_split


def _object(path: Path) -> dict[str, Any]:
    """Decode one verified object without printing its potentially restricted text."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Expected release object")
    return value


def _rows(path: Path) -> list[dict[str, Any]]:
    """Read a verified JSONL inventory, preserving its frozen ordering."""
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def _binding(path: Path) -> dict[str, Any]:
    """Bind an existing file without copying any content into diagnostics."""
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _linked_source(
    source: dict[str, Any],
    document: dict[str, Any],
    data_root: Path,
    records: dict[str, dict[str, Any]],
    bindings: dict[str, Any],
    dependencies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Recover omitted anchors and headings from checksum-bound upstream records."""
    source = copy.deepcopy(source)
    linked_files: dict[str, Any] = {}

    def canonical(kind: str) -> tuple[str, dict[str, Any]]:
        """Load only canonical files already bound by the approved corpus."""
        binding = (
            document.get("canonical_files", document.get("files", {})).get(kind)
            or linked_files[kind]
        )
        path = verify_binding(binding, data_root)
        key = str(path)
        if key not in dependencies:
            dependencies[key] = {**binding, "path": key}
        if key not in records:
            records[key] = index_records(path.read_bytes())
            bindings[key] = _binding(path)
        return key, records[key]

    target = source["canonical_target"]
    if not source.get("anchors"):
        ref = source.get("full_source_ref", {})
        path = verify_binding(ref.get("binding", ref), data_root)
        bindings[f"linked_source:{path}"] = _binding(path)
        linked = _object(path)
        linked_files = linked.get("source_binding", {}).get("files", {})
        if linked.get("anchors"):
            if (
                linked.get("source_id") != source["source_id"]
                or linked.get("extraction_id") != source["extraction_id"]
            ):
                raise ValueError("Linked source identity differs")
            if linked.get("quote") != source["full_source_text"]:
                raise ValueError("Linked source text differs")
            source["anchors"] = _compact_anchors(linked["anchors"])
        else:
            members = target.get("member_record_ids")
            if not members:
                raise ValueError("Linked source lacks frozen member inventory")
            source["anchors"] = []
            for member in members:
                kind = member.split("/")[-3]
                path_key, indexed = canonical(
                    {"block": "blocks", "table": "tables", "figure": "figures"}[kind]
                )
                record = indexed[member]
                if kind == "figure":
                    # The approved text-only unit retains these IDs but supplies no pixels.
                    continue
                fields = (
                    [
                        (f"cells.{i}.text", c["text"])
                        for i, c in enumerate(record["cells"])
                        if c["text"]
                    ]
                    if kind == "table"
                    else [("canonical_text", record["canonical_text"])]
                )
                source["anchors"].append(
                    {
                        "path": path_key,
                        "record_id": member,
                        "locators": [
                            {"text_field": f, "start": 0, "end": len(t)} for f, t in fields
                        ],
                    }
                )
    if source.get("anchors") and all("text_field" in a for a in source["anchors"]):
        source["anchors"] = _compact_anchors(source["anchors"])
    if not target.get("breadcrumb") and "sections" in document.get(
        "canonical_files", document.get("files", {})
    ):
        _, sections = canonical("sections")
        _, blocks = canonical("blocks")
        section = sections[target.get("section_id", target["unit_id"])]
        target["breadcrumb"] = [
            {"heading_text": blocks[sections[sid]["heading_block_id"]]["canonical_text"]}
            for sid in section["section_path_ids"]
            if sections[sid].get("heading_block_id")
        ]
    if not source.get("title"):
        source["title"] = source.get("document_title") or document.get("title")
    return source


def _verify_source(
    source: dict[str, Any],
    allowed: dict[str, dict[str, Any]],
    data_root: Path,
    records: dict[str, dict[str, Any]],
    bindings: dict[str, Any],
    dependencies: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Replay complete block/cell spans and tables against live canonical records."""
    unit = source_unit(source)
    document = allowed.get(unit[0])
    if document is None or document["extraction_id"] != unit[1]:
        raise ValueError("Citation is outside frozen corpus")
    source = _linked_source(source, document, data_root, records, bindings, dependencies)
    roles = source.get("approved_roles")
    if not isinstance(roles, list) or set(roles) - {
        "required",
        "required_support",
        "optional_context",
        "context_only",
        "context",
        "required_direct",
        "required_qualification",
    }:
        raise ValueError("Citation lacks recognized approved roles")
    if not source.get("occurrence_id") or not source.get("anchors"):
        raise ValueError("Citation occurrence and complete anchors required")
    texts: list[str] = []
    tables: dict[str, Any] = {}
    structured_texts: list[str] = []
    for anchor in source["anchors"]:
        path = (data_root / anchor["path"]).resolve()
        if not path.is_relative_to(data_root.resolve()) or not path.is_file():
            raise ValueError("Missing or escaping canonical anchor file")
        key = str(path)
        if key not in dependencies:
            raise ValueError("Canonical anchor lacks frozen dependency binding")
        if key not in records:
            verify_binding(dependencies[key], data_root)
            records[key] = index_records(path.read_bytes())
            bindings[key] = _binding(path)
        record = records[key].get(anchor["record_id"])
        if record is None or record.get("extraction_id") != unit[1]:
            raise ValueError("Canonical anchor identity differs")
        if record.get("document_id") != f"{unit[1]}/document/{unit[0]}":
            raise ValueError("Canonical anchor document differs")
        locators = anchor.get("locators")
        if not locators:
            raise ValueError("Canonical anchor has no spans")
        expected = (
            [
                (f"cells.{i}.text", cell["text"])
                for i, cell in enumerate(record["cells"])
                if cell["text"]
            ]
            if "cells" in record
            else [("canonical_text", record["canonical_text"])]
        )
        if locators != [
            {"text_field": field, "start": 0, "end": len(text)} for field, text in expected
        ]:
            raise ValueError("Citation spans omit or alter complete canonical text")
        texts.extend(text for _, text in expected)
        structured_texts.append(
            json.dumps(
                {
                    "table_id": record["id"],
                    "cells": [
                        {k: cell[k] for k in ("column_index", "row_index", "text")}
                        for cell in record["cells"]
                    ],
                },
                ensure_ascii=False,
            )
            if "cells" in record
            else record["canonical_text"]
        )
        if "cells" in record:
            tables[record["id"]] = record
    if (
        source.get("full_source_text") not in {"\n\n".join(texts), "\n\n".join(structured_texts)}
        or not texts
    ):
        raise ValueError(
            f"Full source text differs from canonical assembly: {source['occurrence_id']}"
        )
    projected_tables = source.get("tables", [])
    if len(projected_tables) != len(tables) or {t["id"] for t in projected_tables} != set(tables):
        raise ValueError("Canonical table inventory differs")
    for table in projected_tables:
        if any(tables[table["id"]].get(key) != value for key, value in table.items()):
            raise ValueError("Canonical table content differs")
        if table.get("cells") != tables[table["id"]]["cells"]:
            raise ValueError("Complete canonical cells required")
    source["tables"] = projected_tables
    return {key: copy.deepcopy(source[key]) for key in SOURCE_FIELDS if key in source}


def load_evidence_sources(pointer: Path, data_root: Path) -> dict[str, Any]:
    """Verify 49 approved cases and return exact questions plus source-only fields.

    Both splits are read mechanically. This interface never returns answers,
    authoring history or display snippets; consumers still explicitly project
    source fields to separate model payloads from evaluator-only identities.
    """
    result = _object(pointer)
    if result.get("status") != "complete":
        raise ValueError("Release pointer is incomplete")
    completion_path = verify_binding(result["completion"], data_root)
    root = completion_path.parent
    completion = _object(completion_path)
    if completion.get("status") != "complete":
        raise ValueError("Release completion is incomplete")
    inventory = {row["path"]: row for row in completion["inventory"]}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if len(inventory) != len(completion["inventory"]) or actual != set(inventory) | {
        "completion.json"
    }:
        raise ValueError("Release managed inventory differs")
    bindings = {"pointer": _binding(pointer), "completion": _binding(completion_path)}
    for relative, binding in inventory.items():
        bindings[f"release:{relative}"] = _binding(verify_binding(binding, root))

    def release_file(binding: dict[str, Any]) -> Path:
        """Require pointer and sealed inventory to designate the same file."""
        path = verify_binding(binding, data_root)
        relative = path.relative_to(root).as_posix()
        if relative not in inventory or inventory[relative]["sha256"] != binding["sha256"]:
            raise ValueError("Pointer differs from sealed inventory")
        return path

    handoff = _object(release_file(result["handoff"]))
    if handoff["release_id"] != result["release_id"]:
        raise ValueError("Release identity differs")
    dev, test = verify_split(_object(release_file(result["approved_split"])))
    corpus = _object(release_file(handoff["artifacts"]["corpus"]))
    allowed = {row["source_id"]: row for row in corpus["documents"]}
    if len(allowed) != len(corpus["documents"]):
        raise ValueError("Duplicate corpus source")
    dependencies: dict[str, dict[str, Any]] = {}

    def collect(value: Any) -> None:
        """Verify declared external bindings, retaining expected canonical hashes."""
        if isinstance(value, dict):
            if {"path", "sha256"} <= value.keys():
                path = verify_binding(value, data_root)
                key = str(path)
                previous = dependencies.get(key)
                if previous is not None and previous["sha256"] != value["sha256"]:
                    raise ValueError("Conflicting frozen dependency bindings")
                dependencies[key] = {**value, "path": key}
                bindings[f"dependency:{key}"] = _binding(path)
            else:
                for member in value.values():
                    collect(member)
        elif isinstance(value, list):
            for member in value:
                collect(member)

    collect(corpus)
    for relative in inventory:
        path = root / relative
        if "dependenc" in path.name and path.suffix in {".json", ".jsonl"}:
            collect(_rows(path) if path.suffix == ".jsonl" else json.loads(path.read_bytes()))
    index = _rows(release_file(handoff["artifacts"]["reference_index"]))
    indexed = {row["case_id"]: row for row in index}
    if len(index) != 49 or set(indexed) != set(dev + test):
        raise ValueError("Reference membership differs")
    cases: list[dict[str, Any]] = []
    records: dict[str, dict[str, Any]] = {}
    for split, ids in (("dev", dev), ("test", test)):
        targets = _rows(release_file(result[f"target_{split}"]))
        if [row["case_id"] for row in targets] != ids:
            raise ValueError("Target IDs differ from frozen split")
        for target in targets:
            case_id = target["case_id"]
            row = indexed[case_id]
            binding = inventory.get(row["reference_record"])
            if (
                row["split"] != split
                or binding is None
                or binding["sha256"] != row["reference_sha256"]
            ):
                raise ValueError(f"Reference binding or split differs: {case_id}")
            reference = _object(verify_binding(binding, root))
            if reference["case_id"] != case_id or reference["question"] != target["question"]:
                raise ValueError(f"Reference question differs: {case_id}")
            if reference.get("final_disposition") != "approved":
                raise ValueError(f"Reference is not approved: {case_id}")
            sources = [
                _verify_source(s, allowed, data_root, records, bindings, dependencies)
                for s in reference["citation_occurrences"]
            ]
            if not sources:
                raise ValueError(f"Case has no approved citations: {case_id}")
            indexed_occurrences = {}
            for citation_unit in row["citation_units"]:
                for occurrence in citation_unit["occurrence_ids"]:
                    if occurrence in indexed_occurrences:
                        raise ValueError("Duplicate indexed citation occurrence")
                    indexed_occurrences[occurrence] = citation_unit
            if not set(indexed_occurrences) <= {s["occurrence_id"] for s in sources}:
                raise ValueError("Indexed citation membership differs")
            for source in sources:
                authority = indexed_occurrences.get(source["occurrence_id"])
                if authority is None:
                    if source.get("role") != "optional_context":
                        raise ValueError("Required citation absent from index")
                    source["reference_role"] = "context"
                    source["reference_role_basis"] = "sealed_optional_context_occurrence"
                    continue
                unit = source_unit(source)
                if (
                    authority["document_id"] != f"{unit[1]}/document/{unit[0]}"
                    or authority["unit_id"] != unit[3]
                ):
                    raise ValueError("Indexed citation identity differs")
                source["reference_role_basis"] = "sealed_citation_index"
                source["reference_role"] = {"required": "support", "optional_context": "context"}[
                    authority["role"]
                ]
            cases.append(
                {
                    "case_id": case_id,
                    "split": split,
                    "question": target["question"],
                    "sources": sources,
                }
            )
    return {
        "release_id": result["release_id"],
        "data_root": str(data_root.resolve()),
        "dev_case_ids": dev,
        "test_case_ids": test,
        "cases": cases,
        "source_bindings": bindings,
        "verification": {
            "release_inventory_sha256_verified": True,
            "canonical_anchor_text_and_tables_verified": True,
            "canonical_file_frozen_hashes_verified": True,
            "development_count": len(dev),
            "test_count": len(test),
            "source_text_basis": "Frozen approved complete units replayed from canonical anchors",
            "semantic_source_support_verified": False,
            "figure_policy": (
                "Approved text-only units preserve member IDs; "
                "figure pixels are not supplied or interpreted"
            ),
            "unit_boundary_basis": "inherited_from_verified_approved_release_not_recomputed",
        },
    }
