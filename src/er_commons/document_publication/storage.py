"""Candidate inventory, completion-last publication, and exact reuse."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    artifact_inventory,
    directory_bytes,
    sha256_file,
    write_json_atomic,
)
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.identity import build_candidate_id, canonical_digest
from er_commons.document_publication.records import (
    ArtifactRef,
    DocumentCompletion,
    DocumentIdentityRecord,
    SourceIdentity,
)


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
    """Copy one verified linked document into the publication transaction."""
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    target = staging_root / "content"
    shutil.copytree(source_root, target)
    return target


def content_digest(root: Path) -> str:
    """Digest relative paths and bytes before candidate identity/control records."""
    inventory = artifact_inventory(root, excluded=set())
    return canonical_digest(inventory)


def write_inventory(root: Path, *, recorded_files: dict[str, dict[str, Any]] | None = None) -> Path:
    """Seal every managed file except self-referential inventory/completion records."""
    records = root / "records"
    records.mkdir(parents=True, exist_ok=True)
    path = records / "artifact_inventory.json"
    excluded = {"records/artifact_inventory.json", "records/completion_record.json"}
    files = []
    for item in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = item.relative_to(root).as_posix()
        if relative in excluded:
            continue
        inherited = (recorded_files or {}).get(relative)
        if inherited is not None:
            if item.stat().st_size != inherited["byte_size"]:
                raise ValueError(f"inherited publication payload size differs: {relative}")
            files.append(dict(inherited))
        else:
            files.append(
                {"path": relative, "sha256": sha256_file(item), "byte_size": item.stat().st_size}
            )
    payload = {
        "files": files,
        "file_count": len(files),
        "byte_count": sum(item["byte_size"] for item in files),
    }
    write_json_atomic(path, payload)
    return path


def publish_candidate(
    workspace: CandidateWorkspace,
    *,
    transaction_id: str,
    candidate_id: str,
    source: SourceIdentity,
    processed_pages: list[int],
    recorded_files: dict[str, dict[str, Any]] | None = None,
) -> Path:
    """Write completion last and atomically publish into an absent candidate directory."""
    inventory_path = write_inventory(workspace.staging_root, recorded_files=recorded_files)
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


def verify_inventory_metadata(
    root: Path, inventory: dict[str, Any], *, budget: VerificationBudget, source_id: str
) -> None:
    """Check exact managed membership and sizes without reading payload bytes."""
    if inventory.get("schema_version") not in {None, "er_commons.candidate_artifact_inventory.v1"}:
        raise ValueError(f"source={source_id} incompatible managed inventory schema")
    files = inventory.get("files")
    if not isinstance(files, list):
        raise ValueError(f"source={source_id} inventory files must be a list")
    excluded = {"records/artifact_inventory.json", "records/completion_record.json"}
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "byte_size"}:
            raise ValueError(f"source={source_id} malformed managed inventory row")
        relative = item["path"]
        if (
            not isinstance(relative, str)
            or not isinstance(item["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        ):
            raise ValueError(f"source={source_id} invalid managed path or digest")
        if (
            not isinstance(item["byte_size"], int)
            or isinstance(item["byte_size"], bool)
            or item["byte_size"] < 0
        ):
            raise ValueError(f"source={source_id} invalid managed byte size")
        if relative in seen or relative in excluded:
            raise ValueError(
                f"source={source_id} duplicate/self-referential managed path: {relative}"
            )
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"source={source_id} unsafe managed path: {relative}")
        seen.add(relative)
        budget.check_metadata(
            root / relative,
            root=root,
            role="preserved_payload",
            source_id=source_id,
            byte_size=item["byte_size"],
        )
    if "file_count" in inventory and inventory["file_count"] != len(files):
        raise ValueError(f"source={source_id} inventory file count differs")
    if "byte_count" in inventory and inventory["byte_count"] != sum(
        item["byte_size"] for item in files
    ):
        raise ValueError(f"source={source_id} inventory byte count differs")
    if "byte_size" in inventory and inventory["byte_size"] != sum(
        item["byte_size"] for item in files
    ):
        raise ValueError(f"source={source_id} inventory byte size differs")
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    } - excluded
    if observed != seen:
        raise ValueError(
            f"source={source_id} managed-file closure differs: "
            f"missing={sorted(seen - observed)[:5]} extra={sorted(observed - seen)[:5]}"
        )


def verify_candidate_metadata(
    root: Path, candidate_id: str, source: SourceIdentity, *, budget: VerificationBudget
) -> Path:
    """Consume recorded identities and exact metadata closure, never payload equality."""
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    completion = DocumentCompletion.model_validate(
        budget.read_json(completion_path, role="completion", source_id=source.source_id, root=root)
    )
    budget.hash_file(completion_path, role="completion", source_id=source.source_id, root=root)
    if completion.candidate_id != candidate_id or completion.source != source:
        raise ValueError("candidate completion identity differs")
    if completion.processed_pages != list(range(1, source.pdf_page_count + 1)):
        raise ValueError("candidate completion is not a complete PDF")
    if inventory_path.stat().st_size <= budget.hash_file_limit:
        digest = budget.hash_file(
            inventory_path, role="managed_inventory", source_id=source.source_id, root=root
        )
        if digest != completion.candidate_inventory.sha256:
            raise ValueError("candidate completion does not seal inventory")
    inventory = budget.read_json(
        inventory_path, role="managed_inventory", source_id=source.source_id, root=root
    )
    if not isinstance(inventory, dict):
        raise ValueError("candidate inventory must be an object")
    verify_inventory_metadata(root, inventory, budget=budget, source_id=source.source_id)
    return _verify_recorded_candidate_identity(root, candidate_id, source, inventory, budget)


def _verify_recorded_candidate_identity(
    root: Path,
    candidate_id: str,
    source: SourceIdentity,
    inventory: dict[str, Any],
    budget: VerificationBudget,
) -> Path:
    """Recompute the historical candidate preimage from sealed record digests."""
    identity_path = root / "records/document_identity.json"
    identity = DocumentIdentityRecord.model_validate(
        budget.read_json(
            identity_path, role="identity_preimage", source_id=source.source_id, root=root
        )
    )
    if identity.source != source or identity.candidate_id != candidate_id:
        raise ValueError("candidate identity source or candidate differs")
    identity_digest = budget.hash_file(
        identity_path, role="identity_preimage", source_id=source.source_id, root=root
    )
    sealed = [row for row in inventory["files"] if row["path"] == "records/document_identity.json"]
    if len(sealed) != 1 or sealed[0]["sha256"] != identity_digest:
        raise ValueError("candidate identity inventory binding differs")
    control = canonical_digest(
        {
            "hierarchy_disposition": identity.hierarchy_disposition,
            "run_spec_sha256": identity.run_spec_sha256,
            "stage_completions": {
                role: ref.model_dump(mode="json")
                for role, ref in identity.stage_completions.items()
            },
            "terminal_state": identity.terminal_state,
        }
    )
    if identity.control_digest != control or candidate_id != build_candidate_id(
        production_extraction_id=identity.production_extraction_id,
        source_id=source.source_id,
        content_digest=identity.content_digest,
        control_digest=control,
    ):
        raise ValueError("candidate identity does not derive from recorded preimage")
    content_files = [
        {**row, "path": row["path"][len("content/") :]}
        for row in inventory["files"]
        if row["path"].startswith("content/")
    ]
    recorded_content = {
        "files": content_files,
        "file_count": len(content_files),
        "byte_count": sum(row["byte_size"] for row in content_files),
    }
    if identity.content_digest != canonical_digest(recorded_content):
        raise ValueError("candidate recorded content inventory digest differs")
    return root / "records/completion_record.json"


def sealed_content_inventory(
    root: Path, *, budget: VerificationBudget, source_id: str
) -> dict[str, Any]:
    """Compose content identity using sealed payload digests and compact terminal hashes."""
    inventory_path = root / "records/artifact_inventory.json"
    completion_path = root / "records/completion_record.json"
    inventory = budget.read_json(
        inventory_path, role="managed_inventory", source_id=source_id, root=root
    )
    completion = budget.read_json(
        completion_path, role="completion", source_id=source_id, root=root
    )
    if not isinstance(inventory, dict) or not isinstance(completion, dict):
        raise ValueError("linked terminal seals must be objects")
    inventory_digest = budget.hash_file(
        inventory_path, role="managed_inventory", source_id=source_id, root=root
    )
    if completion.get("artifact_inventory_sha256") != inventory_digest:
        raise ValueError("linked completion inventory binding differs")
    if completion.get("completion_last") is not True or completion.get("status") not in {
        "complete",
        "complete_with_warnings",
    }:
        raise ValueError("linked completion is not terminal")
    verify_inventory_metadata(root, inventory, budget=budget, source_id=source_id)
    files = list(cast(list[dict[str, Any]], inventory["files"]))
    for path, role in ((inventory_path, "managed_inventory"), (completion_path, "completion")):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "byte_size": path.stat().st_size,
                "sha256": budget.hash_file(path, role=role, source_id=source_id, root=root),
            }
        )
    files.sort(key=lambda row: row["path"])
    return {
        "files": files,
        "file_count": len(files),
        "byte_count": sum(row["byte_size"] for row in files),
    }
