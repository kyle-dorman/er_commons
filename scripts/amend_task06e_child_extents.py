#!/usr/bin/env python3
"""Publish a no-clobber 06E packet with complete compact child extents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from er_commons.document_records.document_structure.missing_chapter_extent_amendment import (
    amend_child_subtree_extents,
)
from er_commons.document_records.document_structure.missing_chapter_policy import (
    MissingChapterDecision,
)
from er_commons.document_records.document_structure.missing_chapter_qualification import (
    publish_missing_chapter_qualification,
    verify_compact_qualification_packet,
)

JsonObject = dict[str, Any]


def main() -> None:
    """Validate frozen inputs, require exact corrections, and publish completion last."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    data_root_value = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not data_root_value:
        raise ValueError("ER_COMMONS_DATA_ROOT is required")
    data_root = Path(data_root_value).resolve()
    config = _read_json(args.config)
    _verify_file(Path(__file__), config["generator_ref"]["sha256"])
    base_root = data_root / config["base_qualification"]["relative_root"]
    candidate_root = data_root / config["candidate"]["relative_root"]
    verify_compact_qualification_packet(
        base_root,
        expected_completion_sha256=config["base_qualification"]["completion_sha256"],
    )
    _verify_file(
        candidate_root / "records/completion_record.json",
        config["candidate"]["completion_sha256"],
    )
    module_ref = config["candidate"]["amendment_module_ref"]
    _verify_file(repo_root / module_ref["path"], module_ref["sha256"])
    publication_module_ref = config["publication_module_ref"]
    _verify_file(
        repo_root / publication_module_ref["path"],
        publication_module_ref["sha256"],
    )
    decision_module_ref = config["decision_module_ref"]
    _verify_file(repo_root / decision_module_ref["path"], decision_module_ref["sha256"])
    for item in config["candidate"]["compact_inputs"]:
        _verify_file(candidate_root / item["path"], item["sha256"])
    policy_path = repo_root / config["policy_ref"]["path"]
    schema_path = repo_root / config["decision_schema_ref"]["path"]
    _verify_file(policy_path, config["policy_ref"]["sha256"])
    _verify_file(schema_path, config["decision_schema_ref"]["sha256"])
    decisions = tuple(
        MissingChapterDecision.from_record(row)
        for row in _read_jsonl(base_root / "all_decisions.jsonl")
    )
    compact = {
        item["path"]: _read_jsonl(candidate_root / item["path"])
        for item in config["candidate"]["compact_inputs"]
    }
    amended, corrections = amend_child_subtree_extents(
        decisions,
        sections=compact["canonical/sections.jsonl"],
        content=(
            *compact["canonical/blocks.jsonl"],
            *compact["canonical/tables.jsonl"],
            *compact["canonical/figures.jsonl"],
        ),
    )
    if list(corrections) != config["expected_corrections"]:
        raise ValueError("observed Task 06E extent corrections differ from frozen allowlist")
    amendment_ref = {
        "schema_version": config["schema_version"],
        "config_ref": {
            "path": args.config.resolve().relative_to(repo_root).as_posix(),
            "sha256": _sha256(args.config),
        },
        "base_qualification": config["base_qualification"],
        "candidate": config["candidate"],
        "publication_module_ref": publication_module_ref,
        "decision_module_ref": decision_module_ref,
        "generator_ref": config["generator_ref"],
        "expected_corrections": config["expected_corrections"],
    }
    publish_missing_chapter_qualification(
        args.output_root,
        decisions=amended,
        source_ref=_read_json(base_root / "qualification.json")["source_ref"],
        policy_ref=config["policy_ref"],
        schema_ref=config["decision_schema_ref"],
        decision_schema=_read_json(schema_path),
        amendment_ref=amendment_ref,
    )


def _read_json(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> tuple[JsonObject, ...]:
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())


def _verify_file(path: Path, expected_sha256: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = _sha256(path)
    if observed != expected_sha256:
        raise ValueError(f"checksum mismatch: {path}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
