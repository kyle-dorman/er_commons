"""Seal and lineage validation for downstream-only document candidates."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.records import (
    ArtifactRef,
    DocumentIdentityRecord,
    DownstreamReplayRecord,
)


def verify_downstream_replay(candidate_root: Path, *, data_root: Path) -> Path:
    """Verify replay lineage, replacement product, and all reused upstream seals."""
    replay_path = candidate_root / "records/downstream_replay.json"
    replay = DownstreamReplayRecord.model_validate_json(replay_path.read_bytes())
    if replay.candidate_id != candidate_root.name:
        raise ValueError(
            f"downstream replay candidate ID differs: expected={candidate_root.name} "
            f"observed={replay.candidate_id}"
        )
    references = (
        replay.source_completion_ref,
        replay.source_inventory_ref,
        *replay.reused_stage_completions.values(),
        replay.replacement_linked_document_completion_ref,
    )
    for reference in references:
        _verify_reference(reference, data_root)
    _verify_identity_stages(candidate_root, replay)
    return replay_path


def artifact_ref(path: Path, data_root: Path) -> ArtifactRef:
    """Build a sealed relative reference after containment validation."""
    resolved = path.resolve()
    root = data_root.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"downstream replay input escapes data root or is absent: {path}")
    return ArtifactRef(path=resolved.relative_to(root).as_posix(), sha256=sha256_file(resolved))


def verify_cross_reference_completion(root: Path, completion: Path) -> None:
    """Require completion-last and inventory seals owned by one candidate."""
    expected = root / "records/completion_record.json"
    inventory = root / "records/artifact_inventory.json"
    if completion != expected or not inventory.is_file() or not completion.is_file():
        raise ValueError(
            "cross-reference completion lacks candidate-owned terminal seals: "
            f"completion={completion} inventory={inventory}"
        )


def _verify_identity_stages(candidate_root: Path, replay: DownstreamReplayRecord) -> None:
    identity = DocumentIdentityRecord.model_validate_json(
        (candidate_root / "records/document_identity.json").read_bytes()
    )
    expected = {
        **replay.reused_stage_completions,
        "linked_document": replay.replacement_linked_document_completion_ref,
    }
    if identity.stage_completions != expected:
        raise ValueError(f"downstream replay stage completions differ: {candidate_root}")


def _verify_reference(reference: ArtifactRef, data_root: Path) -> None:
    path = (data_root / reference.path).resolve()
    root = data_root.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(
            f"downstream replay input is absent or escapes data root: {reference.path}"
        )
    observed = sha256_file(path)
    if observed != reference.sha256:
        raise ValueError(
            f"downstream replay input seal differs: path={reference.path} "
            f"expected={reference.sha256} observed={observed}"
        )
