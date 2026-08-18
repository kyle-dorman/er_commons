"""Readable completion-last writer and checksum-closed candidate verifier."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_records.document_references.construction import (
    CROSS_REFERENCE_PATH,
    TARGET_ALIAS_PATH,
    CandidateBuild,
    CandidateSource,
)
from er_commons.document_records.document_references.storage import write_json, write_jsonl
from er_commons.document_records.document_references.types import JsonObject
from er_commons.document_records.record_mapping.publication import (
    build_inventory,
    sha256_file,
    write_inventory,
)

NEW_SUPPORT_PATHS = {
    "cross_reference_target_index": "support/cross_reference_target_index.json",
    "cross_reference_summary": "support/cross_reference_summary.json",
    "cross_reference_preservation": "support/cross_reference_preservation.json",
}


@dataclass(frozen=True)
class CandidateWriter:
    """Serialize one validated build and write completion last."""

    upstream: CandidateSource

    def write(self, root: Path, build: CandidateBuild, identity: JsonObject) -> None:
        """Write records, support, manifest, inventory, then completion."""
        candidate_id = identity["extraction_id"]
        write_json(root / "records" / "extraction_identity.json", identity)
        record_files = self._write_record_files(root, build)
        support_files = self._write_support_files(root, build, identity)
        manifest = self._manifest(
            build=build,
            identity=identity,
            record_files=record_files,
            support_files=support_files,
        )
        write_json(root / "records" / "manifest.json", manifest)
        write_json(
            root / "records" / "canonicalization_summary.json",
            self._summary(build, identity),
        )
        inventory_path = write_inventory(root)
        write_json(
            root / "records" / "completion_record.json",
            {
                "schema_version": "er_commons.canonical_extraction_completion.v3",
                "extraction_id": candidate_id,
                "status": "complete_with_warnings",
                "artifact_inventory_sha256": sha256_file(inventory_path),
                "support_files_verified": True,
                "preservation_status": "passed",
                "undeclared_difference_count": 0,
            },
        )

    def _write_record_files(self, root: Path, build: CandidateBuild) -> list[JsonObject]:
        record_files: list[JsonObject] = []
        for upstream_item in self.upstream.manifest["record_files"]:
            path = upstream_item["path"]
            records = _records_for_path(build, path)
            write_jsonl(root / path, records)
            record_files.append(
                {
                    "record_type": upstream_item["record_type"],
                    "path": path,
                    "sha256": sha256_file(root / path),
                    "record_count": len(records),
                }
            )
        return record_files

    def _write_support_files(
        self, root: Path, build: CandidateBuild, identity: JsonObject
    ) -> list[JsonObject]:
        files: list[JsonObject] = []
        for upstream_item in self.upstream.manifest["support_files"]:
            source = self.upstream.root / upstream_item["path"]
            destination = root / upstream_item["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            files.append(
                {
                    **upstream_item,
                    "upstream_candidate_id": identity["upstream_candidate_id"],
                }
            )
        for role, path in NEW_SUPPORT_PATHS.items():
            write_json(root / path, build.support[role])
            files.append(
                {
                    "role": role,
                    "path": path,
                    "sha256": sha256_file(root / path),
                    "schema_version": "3.0.0",
                }
            )
        return files

    def _manifest(
        self,
        *,
        build: CandidateBuild,
        identity: JsonObject,
        record_files: list[JsonObject],
        support_files: list[JsonObject],
    ) -> JsonObject:
        new_support = [item for item in support_files if item["role"] in NEW_SUPPORT_PATHS]
        extension = {
            "schema_version": "er_commons.canonical_extraction_manifest.v3",
            "cross_reference_count": len(build.cross_references),
            "preserved_alias_count": build.support["cross_reference_preservation"][
                "upstream_alias_count"
            ],
            "derived_table_alias_count": build.support["cross_reference_preservation"][
                "derived_table_alias_count"
            ],
            "derived_figure_alias_count": 0,
            "support_files": new_support,
        }
        document_id = build.preserved_record_files["canonical/documents.jsonl"][0]["id"]
        return {
            **self.upstream.manifest,
            "schema_version": "er_commons.canonical_extraction_manifest.v3",
            "extraction_id": identity["extraction_id"],
            "identity_sha256": identity["identity_sha256"],
            "ordered_document_ids": [document_id],
            "record_files": record_files,
            "target_alias_count": len(build.target_aliases),
            "cross_reference_count": len(build.cross_references),
            "support_files": support_files,
            "cross_reference_extension": extension,
        }

    def _summary(self, build: CandidateBuild, identity: JsonObject) -> JsonObject:
        upstream_summary = json.loads(
            (self.upstream.root / "records" / "canonicalization_summary.json").read_bytes()
        )
        return {
            **upstream_summary,
            "schema_version": "er_commons.cross_reference_materialization_summary.v3",
            "candidate_id": identity["extraction_id"],
            "counts": {
                **upstream_summary["counts"],
                "target_aliases": len(build.target_aliases),
                "cross_references": len(build.cross_references),
            },
            "cross_reference_summary": build.support["cross_reference_summary"],
        }


def verify_completed_candidate(root: Path, candidate_id: str) -> Path:
    """Verify terminal records, inventory closure, and every new support checksum."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    manifest_path = root / "records" / "manifest.json"
    if not all(path.is_file() for path in (completion_path, inventory_path, manifest_path)):
        raise ValueError("candidate terminal records are incomplete")
    completion = json.loads(completion_path.read_bytes())
    inventory = json.loads(inventory_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    expected_completion = {
        "schema_version": "er_commons.canonical_extraction_completion.v3",
        "extraction_id": candidate_id,
        "status": "complete_with_warnings",
        "support_files_verified": True,
        "preservation_status": "passed",
        "undeclared_difference_count": 0,
    }
    if any(completion.get(key) != value for key, value in expected_completion.items()):
        raise ValueError("candidate completion fields differ")
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise ValueError("candidate completion does not seal its inventory")
    if inventory != build_inventory(root):
        raise ValueError("candidate inventory differs from its managed files")
    support_by_role = {item["role"]: item for item in manifest["support_files"]}
    for role, path in NEW_SUPPORT_PATHS.items():
        item = support_by_role.get(role)
        if item is None or item["path"] != path:
            raise ValueError(f"candidate support role differs: {role}")
        if item["sha256"] != sha256_file(root / path):
            raise ValueError(f"candidate support checksum differs: {role}")
    return completion_path


def preserve_failed_attempt(task_root: Path, staging_root: Path) -> Path:
    """Retain a failed workspace but remove any misleading completion record."""
    destination = task_root / "attempts" / staging_root.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_root.rename(destination)
    (destination / "records" / "completion_record.json").unlink(missing_ok=True)
    return destination


def write_failed_build_snapshot(
    root: Path,
    *,
    build: CandidateBuild,
    identity: JsonObject,
    error: Exception,
) -> None:
    """Persist the rejected build and error context before retaining an attempt."""
    diagnostic_root = root / "diagnostics" / "validation_build"
    write_json(
        diagnostic_root / "context.json",
        {
            "candidate_id": identity.get("extraction_id"),
            "error_type": type(error).__name__,
            "error_message": str(error),
        },
    )
    write_jsonl(diagnostic_root / "target_aliases.jsonl", build.target_aliases)
    write_jsonl(diagnostic_root / "cross_references.jsonl", build.cross_references)
    for role, payload in build.support.items():
        write_json(diagnostic_root / f"{role}.json", payload)


def _records_for_path(build: CandidateBuild, path: str) -> list[JsonObject]:
    if path == TARGET_ALIAS_PATH:
        return build.target_aliases
    if path == CROSS_REFERENCE_PATH:
        return build.cross_references
    return build.preserved_record_files[path]
