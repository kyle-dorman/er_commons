"""Prepare sealed evidence-only inputs; no retrieval, generation or scoring."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from er_commons.artifact_io import (
    file_reference,
    json_bytes,
    jsonl_bytes,
    publish_bytes_no_clobber,
    sha256_bytes,
    stable_json_sha256,
)
from er_commons.automatic_metric_inputs import source_unit
from er_commons.judge_packets import StrictModel, Table, _project_source
from er_commons.synthetic_intake import verify_binding, verify_split

SCHEMA = "task10.evidence_only.v1"


class Passage(StrictModel):
    """Complete source content with neutral local IDs and readable locations only."""

    citation_id: str
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    heading_path: list[str]
    edition: str | None = None
    full_source_text: str = Field(min_length=1)
    tables: list[Table]
    physical_pages: list[int]
    printed_labels: list[str]


class Payload(StrictModel):
    """The only object that may be projected into a target request."""

    question: str = Field(min_length=1)
    passages: list[Passage] = Field(min_length=1)


def build_case(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Deduplicate exact source views and isolate approved roles from target text."""
    sources = case["sources"]
    support: set[tuple[str, str, str, str]] = set()
    context: set[tuple[str, str, str, str]] = set()
    for source in sources:
        unit = source_unit(source)
        role = source.get("reference_role")
        if role not in {"support", "context"}:
            raise ValueError("Unknown reference role")
        if source.get("reference_role_basis") not in {
            "sealed_citation_index",
            "sealed_optional_context_occurrence",
        }:
            raise ValueError("Unknown reference role basis")
        if not isinstance(source.get("approved_roles"), list):
            raise ValueError("Missing approved role provenance")
        (support if role == "support" else context).add(unit)
    grouped: dict[tuple[tuple[str, str, str, str], str], dict[str, Any]] = {}
    for source in sources:
        unit = source_unit(source)
        if unit not in support | context:
            raise ValueError(f"Source lacks approved role for {case['case_id']}")
        content = _project_source(source)
        target = content.get("canonical_target", {})
        passage = {
            "source_id": content["source_id"],
            "title": content.get("title"),
            **({"edition": content["edition"]} if "edition" in content else {}),
            "heading_path": [h["heading_text"] for h in target.get("breadcrumb", [])],
            "full_source_text": content["full_source_text"],
            "tables": content["tables"],
            "physical_pages": content.get("physical_pages", target.get("pages", [])),
            "printed_labels": content.get("printed_labels", []),
        }
        anchors = source.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            raise ValueError(f"Missing canonical anchors for {case['case_id']}")
        view_hash = stable_json_sha256(
            [{"record_id": a["record_id"], "locators": a.get("locators", [])} for a in anchors]
        )
        key = (unit, view_hash)
        if key in grouped:
            previous = grouped[key]
            if previous["passage"] != passage or previous["anchors"] != anchors:
                raise ValueError(f"Conflicting duplicate source for {case['case_id']}")
            previous["occurrence_ids"].add(source["occurrence_id"])
            previous["approved_roles"].update(source["approved_roles"])
            previous["role_bases"].add(source["reference_role_basis"])
        else:
            grouped[key] = {
                "passage": passage,
                "anchors": copy.deepcopy(anchors),
                "occurrence_ids": {source["occurrence_id"]},
                "approved_roles": set(source["approved_roles"]),
                "role_bases": {source["reference_role_basis"]},
            }
    passages, mappings = [], []
    for index, ((unit, view_hash), row) in enumerate(sorted(grouped.items()), 1):
        identifier = f"P{index}"
        passages.append({"citation_id": identifier, **row["passage"]})
        mappings.append(
            {
                "citation_id": identifier,
                "canonical_unit": list(unit),
                "source_view_sha256": view_hash,
                "anchors": row["anchors"],
                "occurrence_ids": sorted(row["occurrence_ids"]),
                "approved_roles": sorted(row["approved_roles"]),
                "reference_role_bases": sorted(row["role_bases"]),
                "reference_role": "support" if unit in support else "context",
            }
        )
    payload = {"question": case["question"], "passages": passages}
    Payload.model_validate(payload)
    record = {"schema_version": SCHEMA, "case_id": case["case_id"], "payload": payload}
    mapping = {
        "schema_version": SCHEMA,
        "case_id": case["case_id"],
        "split": case["split"],
        "payload_sha256": stable_json_sha256(payload),
        "passages": mappings,
    }
    return record, mapping


def _binding(path: Path) -> dict[str, Any]:
    """Bind source and implementation bytes without putting them in target payloads."""
    return {**file_reference(path, root=path.parent), "path": str(path.resolve())}


def _implementation() -> list[dict[str, Any]]:
    """Bind owned code, reused projection/identity helpers and dependency versions."""
    repo = Path(__file__).resolve().parents[2]
    names = (
        "evidence_only.py",
        "evidence_only_sources.py",
        "judge_packets.py",
        "judge_qualification_packets.py",
        "automatic_metric_inputs.py",
        "synthetic_intake.py",
        "artifact_io.py",
        "pilot_citation_records.py",
        "group_answer_intake.py",
    )
    return [_binding(Path(__file__).with_name(name)) for name in names] + [
        _binding(repo / "uv.lock"),
        _binding(repo / "pyproject.toml"),
    ]


def publication_files(intake: dict[str, Any]) -> dict[str, bytes]:
    """Construct every output before publication, requiring exact frozen membership."""
    dev, test = verify_split(
        {"status": "approved", "dev": intake["dev_case_ids"], "test": intake["test_case_ids"]}
    )
    cases = {row["case_id"]: row for row in intake["cases"]}
    if len(cases) != len(intake["cases"]) or set(cases) != set(dev + test):
        raise ValueError("Case membership differs from the frozen split")
    files: dict[str, bytes] = {}
    diagnostics = []
    for split, ids in (("dev", dev), ("test", test)):
        records, mappings = [], []
        for case_id in ids:
            case = cases[case_id]
            if case["split"] != split:
                raise ValueError("Case split differs from frozen membership")
            record, mapping = build_case(case)
            records.append(record)
            mappings.append(mapping)
            diagnostics.append(
                {
                    "case_id": case_id,
                    "split": split,
                    "passage_count": len(record["payload"]["passages"]),
                    "payload_bytes": len(json_bytes(record["payload"])),
                    "source_characters": sum(
                        len(p["full_source_text"]) for p in record["payload"]["passages"]
                    ),
                }
            )
        files[f"target/{split}.jsonl"] = jsonl_bytes(records)
        files[f"evaluator/{split}_mappings.jsonl"] = jsonl_bytes(mappings)
    files["split.json"] = json_bytes({"status": "approved", "dev": dev, "test": test})
    files["payload.schema.json"] = json_bytes(Payload.model_json_schema())
    files["validation.json"] = json_bytes(
        {
            "schema_version": SCHEMA,
            "status": "passed",
            "case_count": 49,
            "development_count": 19,
            "test_count": 30,
            "cases": diagnostics,
            "inference_calls": 0,
            "retrieval": "not_applicable",
            "context_fit": "unverified_until_task11_rendered_request",
            "source_verification": intake["verification"],
        }
    )
    files["manifest.json"] = json_bytes(
        {
            "schema_version": SCHEMA,
            "release_id": intake["release_id"],
            "data_root": intake["data_root"],
            "source_bindings": intake["source_bindings"],
            "implementation": _implementation(),
            "policy": {
                "evidence": "all_approved_support_and_context_units",
                "ordering": "canonical_tuple_then_anchor_scope_digest_ascending",
                "deduplication": (
                    "exact_views_within_canonical_identity_distinct_approved_scopes_preserved"
                ),
                "payload": "question_and_allowlisted_complete_source_passages",
                "default_split": "dev",
                "truncation": False,
                "inference_calls": 0,
            },
        }
    )
    inventory = [
        {"path": name, "sha256": sha256_bytes(content), "byte_size": len(content)}
        for name, content in sorted(files.items())
    ]
    files["completion.json"] = json_bytes(
        {"schema_version": SCHEMA, "status": "complete", "inventory": inventory}
    )
    return files


def publish_files(output: Path, files: dict[str, bytes]) -> None:
    """Preflight all paths and resume exact partial writes; publish completion last."""
    expected = set(files)
    if output.is_symlink():
        raise ValueError("Output must not be a symbolic link")
    if output.exists():
        for path in output.rglob("*"):
            relative = path.relative_to(output).as_posix()
            if path.is_symlink() or (path.is_file() and relative not in expected):
                raise FileExistsError("Unexpected or linked output entry")
            if path.is_dir() and not any(name.startswith(relative + "/") for name in expected):
                raise FileExistsError("Unexpected output directory")
        for name, content in files.items():
            path = output / name
            if path.exists() and (not path.is_file() or path.read_bytes() != content):
                raise FileExistsError(f"Refusing changed output: {name}")
    for name in sorted(expected - {"completion.json"}):
        publish_bytes_no_clobber(output / name, files[name])
    publish_bytes_no_clobber(output / "completion.json", files["completion.json"])


def prepare(pointer: Path, data_root: Path, output: Path) -> dict[str, Any]:
    """Verify inputs and prepare all cases under an existing external artifact root."""
    from er_commons.evidence_only_sources import load_evidence_sources

    if not data_root.is_dir() or not output.resolve().is_relative_to(data_root.resolve()):
        raise ValueError("Output requires an existing configured external data root")
    intake = load_evidence_sources(pointer, data_root)
    files = publication_files(intake)
    publish_files(output, files)
    value: dict[str, Any] = json.loads(files["validation.json"])
    return value


def validate_publication(output: Path) -> dict[str, Any]:
    """Rebuild from verified release/code bindings and compare every published byte."""
    completion = json.loads((output / "completion.json").read_text())
    if completion.get("status") != "complete" or completion.get("schema_version") != SCHEMA:
        raise ValueError("Publication is not complete")
    inventory = completion["inventory"]
    paths = [row["path"] for row in inventory]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate output inventory path")
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != set(paths) | {"completion.json"} or any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("Published inventory differs")
    for row in inventory:
        verify_binding(row, output)
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest["implementation"] != _implementation():
        raise ValueError("Implementation changed; use the bound implementation for replay")
    from er_commons.evidence_only_sources import load_evidence_sources

    pointer = Path(manifest["source_bindings"]["pointer"]["path"])
    for binding in manifest["source_bindings"].values():
        verify_binding(binding, Path(binding["path"]).parent)
    expected = publication_files(load_evidence_sources(pointer, Path(manifest["data_root"])))
    if actual != set(expected):
        raise ValueError("Publication file set differs from rebuilt inputs")
    for name, content in expected.items():
        if (output / name).read_bytes() != content:
            raise ValueError(f"Publication differs from rebuilt inputs: {name}")
    value: dict[str, Any] = json.loads((output / "validation.json").read_text())
    return value


def load_records(output: Path, *, split: Literal["dev", "test"] = "dev") -> list[dict[str, Any]]:
    """Load only the requested sealed split; test selection must be explicit."""
    if split not in {"dev", "test"}:
        raise ValueError("Unknown split")
    completion = json.loads((output / "completion.json").read_text())
    if completion.get("status") != "complete" or completion.get("schema_version") != SCHEMA:
        raise ValueError("Publication is not complete")
    inventory = {row["path"]: row for row in completion["inventory"]}
    if len(inventory) != len(completion["inventory"]):
        raise ValueError("Duplicate output inventory path")
    split_path = verify_binding(inventory["split.json"], output)
    dev, test = verify_split(json.loads(split_path.read_text()))
    path = verify_binding(inventory[f"target/{split}.jsonl"], output)
    records = [json.loads(line) for line in path.read_text().splitlines()]
    if [row["case_id"] for row in records] != (dev if split == "dev" else test):
        raise ValueError("Loaded IDs differ from frozen split")
    for row in records:
        if row["schema_version"] != SCHEMA or set(row) != {"schema_version", "case_id", "payload"}:
            raise ValueError("Unexpected target record fields")
        Payload.model_validate(row["payload"])
    return records


def main() -> None:
    """Expose explicit preparation and offline validation without provider imports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "validate"])
    parser.add_argument("--release", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "prepare":
        if args.release is None or not os.environ.get("ER_COMMONS_DATA_ROOT"):
            parser.error("prepare requires --release and ER_COMMONS_DATA_ROOT")
        result = prepare(args.release, Path(os.environ["ER_COMMONS_DATA_ROOT"]), args.output)
    else:
        result = validate_publication(args.output)
    logging.info(
        "Evidence-only %s: cases=%s output=%s", args.command, result["case_count"], args.output
    )


if __name__ == "__main__":
    main()
