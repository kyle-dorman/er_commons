"""Recorded document identity and upstream-seal validation boundaries."""

from __future__ import annotations

from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import AuthorityReference
from er_commons.document_publication.identity import build_candidate_id, canonical_digest
from er_commons.document_publication.records import (
    DOCUMENT_PROCESS_NAME_SET,
    ArtifactRef,
    SourceIdentity,
)
from er_commons.document_publication.storage import content_digest


def verify_identity_and_upstreams(
    root: Path,
    *,
    identity: dict[str, object],
    data_root: Path,
    budget: VerificationBudget | None = None,
) -> None:
    """Recompute the candidate ID and every document-product completion seal."""
    controls = {
        "hierarchy_disposition": identity.get("hierarchy_disposition"),
        "run_spec_sha256": identity.get("run_spec_sha256"),
        "stage_completions": identity.get("stage_completions"),
        "terminal_state": identity.get("terminal_state"),
    }
    if identity.get("resolved_spec_ref") is not None:
        controls["resolved_spec_ref"] = identity["resolved_spec_ref"]
    if identity.get("resolved_process_config_refs") is not None:
        controls["resolved_process_config_refs"] = identity["resolved_process_config_refs"]
    control_digest = canonical_digest(controls)
    if identity.get("control_digest") != control_digest:
        raise ValueError("document candidate control digest differs")
    source = SourceIdentity.model_validate(identity["source"])
    resolved_spec = identity.get("resolved_spec_ref")
    if resolved_spec is not None:
        spec_reference = AuthorityReference.model_validate(resolved_spec)
        path = spec_reference.resolve(
            repository_root=Path(__file__).resolve().parents[3],
            artifact_root=data_root,
            budget=budget,
            role="run_descriptor",
        )
        if spec_reference.sha256 != identity.get("run_spec_sha256") or not path.is_file():
            raise ValueError("document candidate resolved spec binding differs")
    process_specs = identity.get("resolved_process_config_refs")
    if process_specs is not None:
        if not isinstance(process_specs, dict) or set(process_specs) != DOCUMENT_PROCESS_NAME_SET:
            raise ValueError("document candidate process-config closure differs")
        for role, value in process_specs.items():
            process_reference = AuthorityReference.model_validate(value)
            process_path = process_reference.resolve(
                repository_root=Path(__file__).resolve().parents[3],
                artifact_root=data_root,
                budget=budget,
                role="config",
                source_id=source.source_id,
            )
            if not process_path.is_file():
                raise ValueError(f"document candidate process config is absent: {role}")
    candidate_id = build_candidate_id(
        production_extraction_id=str(identity["production_extraction_id"]),
        source_id=source.source_id,
        content_digest=(
            str(identity["content_digest"])
            if budget is not None
            else content_digest(root / "content")
        ),
        control_digest=control_digest,
    )
    if identity.get("candidate_id") != candidate_id or root.name != candidate_id:
        raise ValueError("document candidate identity does not derive from managed inputs")
    completions = identity.get("stage_completions")
    if not isinstance(completions, dict):
        raise ValueError("document candidate lacks typed stage completions")
    for role, value in completions.items():
        reference = ArtifactRef.model_validate(value)
        path = (data_root / reference.path).resolve()
        if (
            not path.is_relative_to(data_root.resolve())
            or not path.is_file()
            or (
                budget.hash_file(
                    path, role="completion", source_id=source.source_id, root=data_root
                )
                if budget is not None
                else sha256_file(path)
            )
            != reference.sha256
        ):
            raise ValueError(f"document candidate upstream seal differs: {role}")
