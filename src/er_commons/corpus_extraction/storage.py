"""Candidate inventory, completion-last publication, and exact reuse."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.identity import canonical_digest
from er_commons.corpus_extraction.records import ArtifactRef, DocumentCompletion, SourceIdentity
from er_commons.document_extraction.artifacts import artifact_inventory, directory_bytes
from er_commons.source_freeze import sha256_file, write_json_atomic


@dataclass(frozen=True)
class CandidateWorkspace:
    """Unique attempt staging and deterministic final parent."""

    staging_root: Path
    final_parent: Path


def reserve_candidate_workspace(attempt_root: Path, final_parent: Path) -> CandidateWorkspace:
    """Create a transaction-local candidate tree."""
    staging = attempt_root / "candidate"
    staging.mkdir(parents=True, exist_ok=False)
    return CandidateWorkspace(staging_root=staging, final_parent=final_parent)


def import_content(source_root: Path, staging_root: Path) -> Path:
    """Copy one verified owner candidate into the stage-one transaction."""
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    target = staging_root / "content"
    shutil.copytree(source_root, target)
    return target


def content_digest(root: Path) -> str:
    """Digest relative paths and bytes before candidate identity/control records."""
    inventory = artifact_inventory(root, excluded=set())
    return canonical_digest(inventory)


def write_inventory(root: Path) -> Path:
    """Seal every managed file except self-referential inventory/completion records."""
    records = root / "records"
    records.mkdir(parents=True, exist_ok=True)
    path = records / "artifact_inventory.json"
    payload = artifact_inventory(
        root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    write_json_atomic(path, payload)
    return path


def publish_candidate(
    workspace: CandidateWorkspace,
    *,
    transaction_id: str,
    candidate_id: str,
    source: SourceIdentity,
    processed_pages: list[int],
) -> Path:
    """Write completion last and atomically publish into an absent candidate directory."""
    inventory_path = write_inventory(workspace.staging_root)
    completion = DocumentCompletion(
        transaction_id=transaction_id,
        source=source,
        processed_pages=processed_pages,
        candidate_id=candidate_id,
        candidate_inventory=ArtifactRef(
            path=(f"documents/{source.source_id}/{candidate_id}/records/artifact_inventory.json"),
            sha256=sha256_file(inventory_path),
        ),
    )
    completion_path = workspace.staging_root / "records" / "completion_record.json"
    write_json_atomic(completion_path, completion.model_dump(mode="json"))
    final_root = workspace.final_parent / candidate_id
    workspace.final_parent.mkdir(parents=True, exist_ok=True)
    if final_root.exists():
        raise FileExistsError(f"document candidate destination exists: {final_root}")
    workspace.staging_root.rename(final_root)
    return final_root / "records" / "completion_record.json"


def verify_candidate(root: Path, candidate_id: str, source: SourceIdentity) -> Path:
    """Require identity, completion, checksum, and exact managed-file closure."""
    completion_path = root / "records" / "completion_record.json"
    inventory_path = root / "records" / "artifact_inventory.json"
    if not completion_path.is_file() or not inventory_path.is_file():
        raise ValueError("candidate lacks completion or inventory")
    completion = DocumentCompletion.model_validate_json(completion_path.read_bytes())
    if completion.candidate_id != candidate_id or completion.source != source:
        raise ValueError("candidate completion identity differs")
    if completion.processed_pages != list(range(1, source.pdf_page_count + 1)):
        raise ValueError("candidate completion is not a complete PDF")
    if completion.candidate_inventory.sha256 != sha256_file(inventory_path):
        raise ValueError("candidate completion does not seal inventory")
    expected = json.loads(inventory_path.read_text())
    for item in expected.get("files", []):
        path = root / item["path"]
        if (
            not path.is_file()
            or path.stat().st_size != item["byte_size"]
            or sha256_file(path) != item["sha256"]
        ):
            raise ValueError(f"candidate managed file differs: {item['path']}")
    actual = artifact_inventory(
        root,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    if actual != expected:
        raise ValueError("candidate managed-file closure differs")
    return completion_path


def candidate_output_bytes(root: Path) -> int:
    """Return total candidate bytes for non-identity observability."""
    return directory_bytes(root)
