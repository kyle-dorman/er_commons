"""Seal and lineage validation for downstream-only document candidates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from er_commons.document_publication.candidates import CandidateIdentity
    from er_commons.document_publication.downstream_replay import ReplayInputs
    from er_commons.document_publication.preflight import DocumentRun

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.records import (
    ArtifactRef,
    DocumentIdentityRecord,
    DownstreamReplayRecord,
)


def verify_downstream_replay(
    candidate_root: Path, *, data_root: Path, budget: VerificationBudget | None = None
) -> Path:
    """Verify replay lineage, replacement product, and all reused upstream seals."""
    replay_path = candidate_root / "records/downstream_replay.json"
    if budget is not None:
        budget.reserve_read(
            replay_path, role="input_binding", source_id="replay", root=candidate_root
        )
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
        _verify_reference(reference, data_root, budget=budget)
    _verify_identity_stages(candidate_root, replay, budget=budget)
    return replay_path


def artifact_ref(
    path: Path,
    data_root: Path,
    *,
    budget: VerificationBudget | None = None,
    role: str = "completion",
) -> ArtifactRef:
    """Build a sealed relative reference after containment validation."""
    resolved = path.resolve()
    root = data_root.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"downstream replay input escapes data root or is absent: {path}")
    return ArtifactRef(
        path=resolved.relative_to(root).as_posix(),
        sha256=(
            budget.hash_file(resolved, role=role, source_id="replay", root=root)
            if budget is not None
            else sha256_file(resolved)
        ),
    )


def verify_cross_reference_completion(root: Path, completion: Path) -> None:
    """Require completion-last and inventory seals owned by one candidate."""
    expected = root / "records/completion_record.json"
    inventory = root / "records/artifact_inventory.json"
    if completion != expected or not inventory.is_file() or not completion.is_file():
        raise ValueError(
            "cross-reference completion lacks candidate-owned terminal seals: "
            f"completion={completion} inventory={inventory}"
        )


def _verify_identity_stages(
    candidate_root: Path,
    replay: DownstreamReplayRecord,
    *,
    budget: VerificationBudget | None = None,
) -> None:
    """Compare the descendant identity to exact recorded replay stage bindings."""
    if budget is not None:
        budget.reserve_read(
            candidate_root / "records/document_identity.json",
            role="identity_preimage",
            source_id=replay.source.source_id,
            root=candidate_root,
        )
    identity = DocumentIdentityRecord.model_validate_json(
        (candidate_root / "records/document_identity.json").read_bytes()
    )
    expected = {
        **replay.reused_stage_completions,
        "linked_document": replay.replacement_linked_document_completion_ref,
    }
    if identity.stage_completions != expected:
        raise ValueError(f"downstream replay stage completions differ: {candidate_root}")


def _verify_reference(
    reference: ArtifactRef, data_root: Path, *, budget: VerificationBudget | None = None
) -> None:
    path = (data_root / reference.path).resolve()
    root = data_root.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(
            f"downstream replay input is absent or escapes data root: {reference.path}"
        )
    role = "managed_inventory" if path.name == "artifact_inventory.json" else "completion"
    if (
        budget is not None
        and role == "managed_inventory"
        and path.stat().st_size > budget.hash_file_limit
    ):
        budget.check_metadata(path, role=role, source_id="replay", root=root)
        return
    observed = (
        budget.hash_file(path, role=role, source_id="replay", root=root)
        if budget is not None
        else sha256_file(path)
    )
    if observed != reference.sha256:
        raise ValueError(
            f"downstream replay input seal differs: path={reference.path} "
            f"expected={reference.sha256} observed={observed}"
        )


def build_replay_record(
    run: DocumentRun,
    inputs: ReplayInputs,
    identity: CandidateIdentity,
    *,
    budget: VerificationBudget,
) -> DownstreamReplayRecord:
    replay_id = f"replayv1-{canonical_digest(_replay_preimage(inputs, identity))}"
    return DownstreamReplayRecord(
        replay_id=replay_id,
        source=run.source,
        source_candidate_id=inputs.source_root.name,
        source_completion_ref=artifact_ref(inputs.source_completion, run.data_root, budget=budget),
        source_inventory_ref=ArtifactRef(
            path=inputs.source_inventory.resolve().relative_to(run.data_root.resolve()).as_posix(),
            sha256=inputs.source_inventory_sha256,
        ),
        reused_stage_completions={
            role: reference
            for role, reference in inputs.stage_completions.items()
            if role != "linked_document"
        },
        replacement_linked_document_completion_ref=inputs.stage_completions["linked_document"],
        candidate_id=identity.candidate_id,
    )


def _replay_preimage(inputs: ReplayInputs, identity: CandidateIdentity) -> dict[str, object]:
    return {
        "schema_version": "er_commons.downstream_document_replay_identity.v2",
        "source_candidate_id": inputs.source_identity.candidate_id,
        "source_control_digest": inputs.source_identity.control_digest,
        "candidate_id": identity.candidate_id,
        "candidate_control_digest": identity.control_digest,
    }
