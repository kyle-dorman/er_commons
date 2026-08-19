"""Content-bound Appendix P publication acceptance with known limitations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from er_commons.hierarchy_inference.candidate_storage import stable_json_bytes
from er_commons.hierarchy_inference.config import StrictConfigModel
from er_commons.hierarchy_inference.digests import canonical_json_sha256
from er_commons.hierarchy_inference.publication_authorization import (
    SEMANTIC_PATHS,
    VerifiedPublicationAuthorization,
    _mark_verified_authorization,
    candidate_semantic_sha256,
)

HISTORICAL_CANDIDATE_ID = "hcorv1-97ffded53a26803052be6a6b6451d2f38587a604923c41b6f2402185105c2c1a"
LIMITATIONS = (
    "historical_development_and_held_out_quality_rejection",
    "two_observed_false_table_boundaries",
    "frozen_r04_r05_attribution_disagreements",
    "existing_ssf_district_level_disagreement",
    "page_2000_r06_content_ambiguity",
    "remaining_payload_ambiguities_and_warnings",
    "task_03e2a_has_no_new_held_out_evaluation",
)
AUTHORIZED_USES = (
    "task_03e3_semantic_contract_input",
    "task_03e4_semantic_materialization_input",
    "task_03g_representative_pilot_hypothesis",
)
EXPECTED_SEMANTIC_SHA256 = "c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8"
EXPECTED_COUNTS = {
    "features": 6931,
    "toc_entries": 140,
    "reconciliations": 140,
    "regimes": 2,
    "decisions": 6931,
    "roots": 12,
    "edges": 234,
    "direct_membership": 4571,
    "unassigned_content": 2,
    "ambiguities": 17,
    "warnings": 148,
}


class EvidenceBinding(StrictConfigModel):
    """One immutable external input to the bounded policy decision."""

    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_contained_path(self) -> EvidenceBinding:
        """Keep every evidence reference below the configured data root."""
        if self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("bounded-acceptance evidence paths must be contained")
        return self


class AcceptanceEvidence(StrictConfigModel):
    """Exact historical, corrected-MVP, and human-rewrite evidence set."""

    historical_held_out_seal: EvidenceBinding
    historical_quality_report_manifest: EvidenceBinding
    historical_failed_attempt: EvidenceBinding
    post_03e2a_reference_manifest: EvidenceBinding
    post_03e2a_reference_semantic: EvidenceBinding
    task_03e2b_equivalence_report: EvidenceBinding
    task_03e2b_reference_semantic: EvidenceBinding
    task_03e2b_rewritten_semantic: EvidenceBinding
    task_03e2b_offline_candidate_report: EvidenceBinding


class AcceptanceScope(StrictConfigModel):
    """The only downstream purposes authorized by the Appendix P decision."""

    source_id: Literal["deir_appendix_p"]
    physical_page_count: Literal[222]
    authorized_uses: tuple[
        Literal[
            "task_03e3_semantic_contract_input",
            "task_03e4_semantic_materialization_input",
            "task_03g_representative_pilot_hypothesis",
        ],
        ...,
    ]
    corpus_wide_acceptance: Literal[False]

    @model_validator(mode="after")
    def require_exact_uses(self) -> AcceptanceScope:
        """Prevent this document-bounded decision from expanding silently."""
        if self.authorized_uses != AUTHORIZED_USES:
            raise ValueError("bounded-acceptance authorized uses differ")
        return self


class SemanticCounts(StrictConfigModel):
    """Frozen ordered payload counts reproduced by the human-owned code."""

    features: int = Field(ge=0)
    toc_entries: int = Field(ge=0)
    reconciliations: int = Field(ge=0)
    regimes: int = Field(ge=0)
    decisions: int = Field(ge=0)
    roots: int = Field(ge=0)
    edges: int = Field(ge=0)
    direct_membership: int = Field(ge=0)
    unassigned_content: int = Field(ge=0)
    ambiguities: int = Field(ge=0)
    warnings: int = Field(ge=0)


class BoundedAcceptanceConfig(StrictConfigModel):
    """Checked-in policy for one explicit, known-limitation authorization."""

    schema_version: Literal["1.0.0"]
    authorization_id: Literal["brisbane_baylands_2025_deir_task03e2d_bounded_acceptance_v1"]
    status: Literal["accepted_with_known_limitations"]
    scope: AcceptanceScope
    limitations: tuple[str, ...]
    expected_semantic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_counts: SemanticCounts
    evidence: AcceptanceEvidence

    @model_validator(mode="after")
    def require_exact_limitations(self) -> BoundedAcceptanceConfig:
        """Make the approved limitation vocabulary complete and order-stable."""
        if self.limitations != LIMITATIONS:
            raise ValueError("bounded-acceptance limitation inventory differs")
        if self.expected_semantic_sha256 != EXPECTED_SEMANTIC_SHA256:
            raise ValueError("bounded-acceptance semantic checksum differs")
        if self.expected_counts.model_dump() != EXPECTED_COUNTS:
            raise ValueError("bounded-acceptance semantic counts differ")
        semantic_bindings = (
            self.evidence.post_03e2a_reference_semantic,
            self.evidence.task_03e2b_reference_semantic,
            self.evidence.task_03e2b_rewritten_semantic,
        )
        if any(item.sha256 != self.expected_semantic_sha256 for item in semantic_bindings):
            raise ValueError("bounded-acceptance semantic evidence differs")
        return self


class CandidateIdentityBinding(StrictConfigModel):
    """The complete candidate-producing identity copied into authorization."""

    candidate_id: str = Field(pattern=r"^hcorv1-[0-9a-f]{64}$")
    producer_run_id: str = Field(pattern=r"^prv1-[0-9a-f]{64}$")
    source_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_]*$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    producer_completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    producer_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    conversion_completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    conversion_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_version: Literal["1.0.0"]
    policy_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CandidateBinding(StrictConfigModel):
    """Exact candidate semantics and all identity inputs accepted by policy."""

    identity: CandidateIdentityBinding
    identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_semantic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frozen_semantic_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    counts: SemanticCounts


class BoundedAcceptance(StrictConfigModel):
    """External publication authorization; not hierarchy semantic evidence."""

    record_type: Literal["hierarchy_bounded_acceptance"]
    schema_version: Literal["1.0.0"]
    authorization_id: Literal["brisbane_baylands_2025_deir_task03e2d_bounded_acceptance_v1"]
    acceptance_config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate: CandidateBinding
    evidence: AcceptanceEvidence
    limitations: tuple[str, ...]
    scope: AcceptanceScope
    status: Literal["accepted_with_known_limitations"]

    @model_validator(mode="after")
    def require_exact_limitations(self) -> BoundedAcceptance:
        """Reject missing, reordered, duplicated, or expanded limitations."""
        if self.limitations != LIMITATIONS:
            raise ValueError("bounded-acceptance limitation inventory differs")
        return self


@dataclass(frozen=True)
class VerifiedBoundedAcceptancePolicy:
    """Checked policy and frozen evidence verified before mutable work."""

    path: Path
    config: BoundedAcceptanceConfig
    sha256: str


@dataclass(frozen=True)
class VerifiedBoundedAcceptance(VerifiedPublicationAuthorization):
    """Opaque candidate-bound proof accepted by the publication seam."""

    path: Path
    candidate_id: str
    candidate_semantic_sha256: str
    frozen_semantic_sha256: str


def load_bounded_acceptance_config(
    path: Path,
) -> tuple[BoundedAcceptanceConfig, str]:
    """Load the exact checked-in acceptance policy and hash its bytes."""
    raw = path.read_bytes()
    return BoundedAcceptanceConfig.model_validate_json(raw), hashlib.sha256(raw).hexdigest()


def verify_bounded_acceptance_policy(
    config_path: Path,
    data_root: Path,
) -> VerifiedBoundedAcceptancePolicy:
    """Fail closed unless every frozen decision input retains exact bytes."""
    config, digest = load_bounded_acceptance_config(config_path)
    _verify_bounded_acceptance_evidence(config, data_root)
    return VerifiedBoundedAcceptancePolicy(config_path, config, digest)


def _verify_bounded_acceptance_evidence(
    config: BoundedAcceptanceConfig,
    data_root: Path,
) -> None:
    """Verify every referenced evidence byte and its terminal disposition."""
    records: dict[str, dict[str, Any]] = {}
    for name, binding in config.evidence:
        raw = (data_root / binding.path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != binding.sha256:
            raise ValueError(f"bounded-acceptance evidence checksum differs: {name}")
        records[name] = json.loads(raw)
    manifest = records["historical_quality_report_manifest"]
    statuses = {item["name"]: item["status"] for item in manifest.get("reports", [])}
    rejected_reports = (
        statuses.get("development") == "reject" and statuses.get("held_out") == "reject"
    )
    if manifest.get("status") != "reject" or not rejected_reports:
        raise ValueError("historical quality rejection evidence differs")
    manifest_root = data_root / config.evidence.historical_quality_report_manifest.path.parent
    for item in manifest.get("reports", []):
        report_raw = (manifest_root / item["path"]).read_bytes()
        if (
            hashlib.sha256(report_raw).hexdigest() != item["sha256"]
            or json.loads(report_raw).get("status") != item["status"]
        ):
            raise ValueError(f"historical quality report differs: {item['name']}")
    seal = records["historical_held_out_seal"]
    seal_root = data_root / config.evidence.historical_held_out_seal.path.parent
    annotation_raw = (seal_root / seal["annotations_path"]).read_bytes()
    render_raw = (seal_root / seal["render_manifest_path"]).read_bytes()
    if (
        seal.get("candidate_id") != HISTORICAL_CANDIDATE_ID
        or seal.get("status") != "sealed"
        or hashlib.sha256(annotation_raw).hexdigest() != seal.get("annotations_file_sha256")
        or canonical_json_sha256(json.loads(annotation_raw)) != seal.get("annotation_bundle_sha256")
        or hashlib.sha256(render_raw).hexdigest() != seal.get("render_manifest_sha256")
    ):
        raise ValueError("historical held-out annotation seal differs")
    attempt = records["historical_failed_attempt"]
    if attempt.get("candidate_id") != HISTORICAL_CANDIDATE_ID or attempt.get("status") != "failed":
        raise ValueError("historical failed-attempt evidence differs")
    reference = records["post_03e2a_reference_manifest"]
    if (
        reference.get("semantic_sha256") != config.expected_semantic_sha256
        or reference.get("counts") != config.expected_counts.model_dump()
    ):
        raise ValueError("post-03E.2a reference evidence differs")
    equivalence = records["task_03e2b_equivalence_report"]
    if (
        equivalence.get("status") != "pass"
        or equivalence.get("reference_semantic_sha256") != config.expected_semantic_sha256
        or equivalence.get("rewritten_semantic_sha256") != config.expected_semantic_sha256
        or equivalence.get("counts") != config.expected_counts.model_dump()
    ):
        raise ValueError("Task 03E.2b equivalence evidence differs")
    if records["task_03e2b_offline_candidate_report"].get("status") != "pass":
        raise ValueError("Task 03E.2b offline candidate evidence differs")


def semantic_payload(candidate_root: Path) -> dict[str, Any]:
    """Reconstruct the existing v1 semantic aggregate in frozen key order."""

    def load(relative: str) -> Any:
        path = candidate_root / relative
        if relative.endswith(".jsonl"):
            return [json.loads(line) for line in path.read_text().splitlines()]
        return json.loads(path.read_bytes())

    return {
        "features": load(SEMANTIC_PATHS[0]),
        "toc_entries": load(SEMANTIC_PATHS[1]),
        "reconciliations": load(SEMANTIC_PATHS[2]),
        "regimes": load(SEMANTIC_PATHS[3]),
        "decisions": load(SEMANTIC_PATHS[4]),
        "hierarchy": load(SEMANTIC_PATHS[5]),
        "ambiguities": load(SEMANTIC_PATHS[6]),
        "warnings": load(SEMANTIC_PATHS[7]),
    }


def semantic_counts(payload: dict[str, Any]) -> dict[str, int]:
    """Count all frozen semantic collections and hierarchy relationships."""
    hierarchy = payload["hierarchy"]
    return {
        "features": len(payload["features"]),
        "toc_entries": len(payload["toc_entries"]),
        "reconciliations": len(payload["reconciliations"]),
        "regimes": len(payload["regimes"]),
        "decisions": len(payload["decisions"]),
        "roots": len(hierarchy["roots"]),
        "edges": len(hierarchy["edges"]),
        "direct_membership": len(hierarchy["direct_membership"]),
        "unassigned_content": len(hierarchy["unassigned_content"]),
        "ambiguities": len(payload["ambiguities"]),
        "warnings": len(payload["warnings"]),
    }


def assemble_bounded_acceptance(
    *,
    path: Path,
    policy: VerifiedBoundedAcceptancePolicy,
    candidate_root: Path,
    candidate_id: str,
    data_root: Path,
) -> VerifiedBoundedAcceptance:
    """Write one no-clobber authorization and independently verify it."""
    identity = CandidateIdentityBinding.model_validate_json(
        (candidate_root / "records/identity.json").read_bytes()
    )
    payload = semantic_payload(candidate_root)
    frozen_digest = hashlib.sha256(stable_json_bytes(payload)).hexdigest()
    if frozen_digest != policy.config.expected_semantic_sha256:
        raise ValueError("candidate differs from frozen post-Task 03E.2a semantic")
    record = BoundedAcceptance(
        record_type="hierarchy_bounded_acceptance",
        schema_version="1.0.0",
        authorization_id=policy.config.authorization_id,
        acceptance_config_sha256=policy.sha256,
        candidate=CandidateBinding(
            identity=identity,
            identity_sha256=canonical_json_sha256(identity.model_dump()),
            candidate_semantic_sha256=candidate_semantic_sha256(candidate_root),
            frozen_semantic_sha256=policy.config.expected_semantic_sha256,
            counts=SemanticCounts.model_validate(semantic_counts(payload)),
        ),
        evidence=policy.config.evidence,
        limitations=policy.config.limitations,
        scope=policy.config.scope,
        status=policy.config.status,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(stable_json_bytes(record.model_dump(mode="json")))
    return verify_bounded_acceptance(
        path=path,
        policy=policy,
        candidate_root=candidate_root,
        candidate_id=candidate_id,
        data_root=data_root,
    )


def verify_bounded_acceptance(
    *,
    path: Path,
    policy: VerifiedBoundedAcceptancePolicy,
    candidate_root: Path,
    candidate_id: str,
    data_root: Path,
) -> VerifiedBoundedAcceptance:
    """Verify policy, evidence, exact semantic behavior, scope, and identity."""
    refreshed = verify_bounded_acceptance_policy(policy.path, data_root)
    if refreshed.sha256 != policy.sha256:
        raise ValueError("bounded-acceptance policy changed after preflight")
    if path.name != "bounded_acceptance.json" or path.parent.name != candidate_id:
        raise ValueError("bounded-acceptance path differs from candidate authorization root")
    record = BoundedAcceptance.model_validate_json(path.read_bytes())
    if (
        record.authorization_id != policy.config.authorization_id
        or record.acceptance_config_sha256 != policy.sha256
        or record.evidence != policy.config.evidence
        or record.limitations != policy.config.limitations
        or record.scope != policy.config.scope
        or record.status != policy.config.status
    ):
        raise ValueError("bounded-acceptance policy binding differs")
    identity = CandidateIdentityBinding.model_validate_json(
        (candidate_root / "records/identity.json").read_bytes()
    )
    payload = semantic_payload(candidate_root)
    frozen_digest = hashlib.sha256(stable_json_bytes(payload)).hexdigest()
    counts = SemanticCounts.model_validate(semantic_counts(payload))
    semantic_digest = candidate_semantic_sha256(candidate_root)
    if (
        identity.candidate_id != candidate_id
        or record.candidate.identity != identity
        or record.candidate.identity_sha256 != canonical_json_sha256(identity.model_dump())
        or record.candidate.candidate_semantic_sha256 != semantic_digest
        or record.candidate.frozen_semantic_sha256 != frozen_digest
        or frozen_digest != policy.config.expected_semantic_sha256
        or record.candidate.counts != counts
        or counts != policy.config.expected_counts
    ):
        raise ValueError("bounded-acceptance candidate binding differs")
    authorization = VerifiedBoundedAcceptance(path, candidate_id, semantic_digest, frozen_digest)
    _mark_verified_authorization(authorization)
    return authorization
