"""Portable, source-free run specifications for Task 05 source stages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.response_inventory.code_inventory import owned_code_digest
from er_commons.response_inventory.pilot_policy import TASK05C_PILOT_RANGES
from er_commons.response_inventory.task05d_policy import (
    TASK05D_ALLOWED_WARNING_CODES,
    TASK05D_PAGE_COUNT,
    TASK05D_RANGE,
)


class StrictModel(BaseModel):
    """Reject undeclared fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class PageRange(StrictModel):
    """One inclusive physical-page range and operational restart unit."""

    range_id: str = Field(pattern=r"^p[0-9]{4}-p[0-9]{4}$")
    first_page: int = Field(ge=1)
    last_page: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> PageRange:
        """Require a forward range whose label agrees with its bounds."""
        if self.last_page < self.first_page:
            raise ValueError("page range must end at or after its first page")
        expected = f"p{self.first_page:04d}-p{self.last_page:04d}"
        if self.range_id != expected:
            raise ValueError(f"page range ID must be {expected}")
        return self

    @property
    def page_count(self) -> int:
        """Return the inclusive number of pages in the range."""
        return self.last_page - self.first_page + 1


class ArtifactReference(StrictModel):
    """Compact accepted-artifact binding without copying its payload."""

    role: Literal["task05a_completion", "source_release_completion", "source_manifest"]
    authority: Literal["artifact_root"]
    path: Path
    byte_size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> ArtifactReference:
        """Keep artifact references relative to the configured data root."""
        _require_contained_path(self.path, "artifact reference")
        return self


class RepositoryBinding(StrictModel):
    """Digest-bound checked-in schema or producer module."""

    role: Literal[
        "response_record_schema",
        "producer_run_spec_code",
        "relationship_run_spec_schema",
        "reference_outcome_schema",
        "reference_run_spec_schema",
        "task04d_collection_spec",
    ]
    authority: Literal["repository"]
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> RepositoryBinding:
        """Keep repository bindings portable and contained."""
        _require_contained_path(self.path, "repository binding")
        return self


class ArtifactReferenceV2(StrictModel):
    """Exact source-free evidence binding used by the complete 05D run."""

    role: Literal[
        "task05a_structural_profile",
        "task05c_build_summary",
        "task05c_completion",
        "task05c_managed_inventory",
        "task05c_qualification",
        "task05c_source_records",
        "source_release_completion",
        "source_manifest",
    ]
    authority: Literal["artifact_root"]
    path: Path
    byte_size: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> ArtifactReferenceV2:
        """Keep evidence references relative to the configured data root."""
        _require_contained_path(self.path, "artifact reference")
        return self


class AcceptedTask05C(StrictModel):
    """Accepted pilot identities that the complete source run must inherit."""

    activity_id: Literal[
        "activityv1-5ef86aaad50e772cf07b9153e333e36672c503b3ab1c922a0290be9fb8a6df85"
    ]
    completion_id: Literal[
        "completionv1-5853fa56753aa6e032687cdd727c72bac1c8cec0abf34cc6d2fac1e9b358e571"
    ]
    inventory_id: Literal[
        "fileinventoryv1-58b8910295f4f3adf9675fb8ec98170e2977ed3d5026f3f02cf3b9c8a15620a6"
    ]
    semantic_digest: Literal["ac874b8671ea40a07d76602d35c404dc641bb2fd7338178eb838b5ff2af145d3"]


class SourceBinding(StrictModel):
    """Frozen source facts that preflight can verify without opening the PDF."""

    source_id: Literal["feir_volume_4"]
    source_role: Literal["curator_only_response_source"]
    source_release_version: Literal["brisbane_baylands_2025_deir_sources_v1"]
    path: Path
    recorded_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recorded_byte_size: int = Field(gt=0)
    recorded_page_count: int = Field(gt=0)
    retrieval_status: Literal["downloaded"]
    validation_status: Literal["valid"]
    member_of_model_corpus: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> SourceBinding:
        """Require an artifact-root-relative PDF path without reading it."""
        _require_contained_path(self.path, "source")
        if self.path.suffix.lower() != ".pdf":
            raise ValueError("response source path must name a PDF")
        return self


class OutputPolicy(StrictModel):
    """Contained, activity-derived pilot publication namespace."""

    artifact_relative_root: Path
    pilot_namespace_template: Literal["pilots/pilotv1-{activity_hash}"]
    completion_written_last: Literal[True]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> OutputPolicy:
        """Keep Task 05 outputs below a portable artifact-root path."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class CachePolicy(StrictModel):
    """Replaceable cache boundary for selected-page diagnostics."""

    relative_path_template: Path
    replaceable: Literal[True]
    selected_pages_only: Literal[True]
    retain_range_receipts: Literal[True]

    @model_validator(mode="after")
    def validate_path(self) -> CachePolicy:
        """Keep cache paths below the artifact root."""
        _require_contained_path(self.relative_path_template, "cache")
        return self


class CompleteOutputPolicy(StrictModel):
    """Contained working-revision namespace for Task 05D."""

    artifact_relative_root: Path
    working_namespace_template: Literal["working/05d/revisionv1-{activity_hash}"]
    completion_written_last: Literal[True]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> CompleteOutputPolicy:
        """Keep Task 05D output below a portable artifact-root path."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class CompleteCachePolicy(StrictModel):
    """Replaceable cache boundary covering every declared 05D page."""

    relative_path_template: Path
    replaceable: Literal[True]
    all_declared_pages: Literal[True]
    retain_range_receipts: Literal[True]

    @model_validator(mode="after")
    def validate_path(self) -> CompleteCachePolicy:
        """Keep Task 05D caches below the artifact root."""
        _require_contained_path(self.relative_path_template, "cache")
        return self


class StopBehavior(StrictModel):
    """Material failures that stop rather than silently broaden the pilot."""

    on_source_binding_mismatch: Literal["stop"]
    on_invalid_anchor_or_schema: Literal["stop"]
    on_unclassified_page: Literal["stop"]
    on_new_structural_regime: Literal["stop"]
    on_nondeterministic_semantic_output: Literal["stop"]
    on_unsafe_restart_state: Literal["stop"]
    allow_additional_pages: Literal[False]
    allow_policy_repair_during_run: Literal[False]
    allowed_terminal_warning_codes: tuple[Literal["unit_boundary_ambiguous"], ...]


class CompleteStopBehavior(StrictModel):
    """Material 05D failures and its one allowed diagnostic class."""

    on_source_binding_mismatch: Literal["stop"]
    on_invalid_anchor_or_schema: Literal["stop"]
    on_unclassified_page: Literal["stop"]
    on_new_structural_regime: Literal["stop"]
    on_nondeterministic_semantic_output: Literal["stop"]
    on_unsafe_restart_state: Literal["stop"]
    allow_additional_pages: Literal[False]
    allow_policy_repair_during_run: Literal[False]
    allowed_terminal_warning_codes: tuple[Literal["source_response_heading_absent"], ...]

    @model_validator(mode="after")
    def validate_allowed_warning_class(self) -> CompleteStopBehavior:
        """Allow only reviewed source-authored missing response headings."""
        if self.allowed_terminal_warning_codes != TASK05D_ALLOWED_WARNING_CODES:
            raise ValueError("05D allows only the source_response_heading_absent warning class")
        return self


class AcceptedTask05D(StrictModel):
    """Exact accepted 05D candidate consumed by the source-free graph stage."""

    candidate_root: Path
    acceptance_path: Path
    revision_id: Literal[
        "revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030"
    ]
    acceptance_id: Literal[
        "acceptancev1-7edf64ffd5e283c736e9980c79f682997ce06c135038d4ceb3ecbc496ce6c027"
    ]
    activity_id: Literal[
        "activityv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030"
    ]
    completion_id: Literal[
        "completionv1-82d534e4e3cc7db7275892690fe4d357540131c9477775d5ebf1d54ad6ab555f"
    ]
    inventory_id: Literal[
        "fileinventoryv1-a04c715a6dff6bdfe6d28eaed9b40211382d60a74d540cdf46cd3b2c993c60a0"
    ]
    semantic_digest: Literal["f7aa9fd6e6d4e464b27b270e6f61a8dcbfb0d998dc44e7eda84abd07db5d9247"]

    @model_validator(mode="after")
    def validate_paths(self) -> AcceptedTask05D:
        """Keep both accepted paths portable and require an adjacent pointer."""
        _require_contained_path(self.candidate_root, "05D candidate")
        _require_contained_path(self.acceptance_path, "05D acceptance")
        expected = Path(f"{self.candidate_root.as_posix()}.acceptance.json")
        if self.acceptance_path != expected:
            raise ValueError("05D acceptance path must be adjacent to its candidate")
        if self.candidate_root.name != self.revision_id:
            raise ValueError("05D candidate path differs from its accepted revision ID")
        return self


class RelationshipOutputPolicy(StrictModel):
    """Replaceable, nonterminal namespace for the exact-only 05E baseline."""

    artifact_relative_root: Path
    baseline_namespace_template: Literal["working/05e/baselinev1-{activity_hash}"]
    completion_written: Literal[False]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> RelationshipOutputPolicy:
        """Keep Task 05E baseline output below the configured artifact root."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class RelationshipReviewOutputPolicy(StrictModel):
    """Replaceable namespace for one bounded, nonterminal Gate 2 review pass."""

    artifact_relative_root: Path
    review_namespace_template: Literal["working/05e/reviewpassv1-{activity_hash}"]
    completion_written: Literal[False]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> RelationshipReviewOutputPolicy:
        """Keep the amended review pass below the configured artifact root."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class AcceptedTask05E(StrictModel):
    """Exact accepted 05E candidate consumed by Task 05F."""

    candidate_root: Path
    acceptance_path: Path
    revision_id: Literal[
        "revisionv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1"
    ]
    acceptance_id: Literal[
        "acceptancev1-4b8a13393c57660fdb0a6b303912150ca9d1380688a86a6728267a4c79aacac5"
    ]
    activity_id: Literal[
        "activityv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1"
    ]
    completion_id: Literal[
        "completionv1-867b3e6f9d9cc1e2666cb184523590c2fd02154347ea9787144e61bb43851555"
    ]
    inventory_id: Literal[
        "fileinventoryv1-924533bd3c59160bd0853aa38dc095965b07b2d4bf2d78a5ad9431cd2836f667"
    ]
    semantic_digest: Literal["3a6f5b0f4f116b2800e0a8b02bb98fde9d37a48ccc0baff321fd484f2489e71b"]

    @model_validator(mode="after")
    def validate_paths(self) -> AcceptedTask05E:
        """Keep the candidate portable and require its adjacent pointer."""
        _require_contained_path(self.candidate_root, "05E candidate")
        _require_contained_path(self.acceptance_path, "05E acceptance")
        if self.acceptance_path != Path(f"{self.candidate_root.as_posix()}.acceptance.json"):
            raise ValueError("05E acceptance path must be adjacent to its candidate")
        if self.candidate_root.name != self.revision_id:
            raise ValueError("05E candidate path differs from its accepted revision ID")
        return self


class Task04ReferenceBindings(StrictModel):
    """Frozen Task 04A/04D paths and identities needed by exact resolution."""

    task04a_gate_d_root: Path
    task04a_review_id: Literal["reviewv1-task03j-final-c17"]
    gate_d_completion_sha256: Literal[
        "d480aa903d7ae65e7a4b1b6de93ad4cdebe6963e6fd724873ade548790712826"
    ]
    usability_registry_sha256: Literal[
        "0453aaf13cb7762e7718ce869ee3f1521a67625224bd35c83b641cc5ae8d47e1"
    ]
    ambiguous_dispositions_sha256: Literal[
        "9d3b8ac7c9fea34ecada607c99b96376d648c2ab419bfa381abbf30f4b2e3366"
    ]
    unresolved_risk_sha256: Literal[
        "b6ac41902ffdfc6c93b13c0be93af5d071f3811334a27367fc2ccdacf2f7a5ca"
    ]
    task04d_handoff_root: Path
    task04d_handoff_id: Literal[
        "handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1"
    ]
    handoff_completion_sha256: Literal[
        "387a07d62d96e4c5aba6f1f3d51f7f9026719b0d7de1b4eece06bed9fd78bc81"
    ]
    production_extraction_id: Literal[
        "exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3"
    ]
    scope_id: Literal["scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da"]
    target_index_root: Path
    target_index_id: Literal[
        "idxv1-31a3eacee1d03001d44f79d2fa15563cfd416b9a80c02e8d178d0843e4bb4a00"
    ]
    target_index_completion_sha256: Literal[
        "a661cfefed67927b7536fe791eb6f6dcfe705dc044e4e4dc9867977790cdfa31"
    ]
    source_family_catalog_path: Path
    source_family_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_paths(self) -> Task04ReferenceBindings:
        """Keep all artifact references relative and identity-named."""
        for label, path in (
            ("04A Gate D", self.task04a_gate_d_root),
            ("04D handoff", self.task04d_handoff_root),
            ("04D target index", self.target_index_root),
            ("source-family catalog", self.source_family_catalog_path),
        ):
            _require_contained_path(path, label)
        if self.task04a_gate_d_root.parent.name != self.task04a_review_id:
            raise ValueError("04A Gate D path differs from the accepted review ID")
        if self.task04d_handoff_root.name != self.task04d_handoff_id:
            raise ValueError("04D handoff path differs from its ID")
        if self.target_index_root.name != self.target_index_id:
            raise ValueError("04D target-index path differs from its ID")
        return self


class ReferenceOutputPolicy(StrictModel):
    """Nonterminal, activity-derived namespace for Task 05F qualified rules."""

    artifact_relative_root: Path
    candidate_namespace_template: Literal["working/05f/rulesv1-{activity_hash}"]
    completion_written: Literal[False]
    copy_source_payload: Literal[False]
    copy_upstream_payloads: Literal[False]

    @model_validator(mode="after")
    def validate_path(self) -> ReferenceOutputPolicy:
        """Keep qualified-rule output below the configured artifact root."""
        _require_contained_path(self.artifact_relative_root, "output")
        return self


class ReferenceStopBehavior(StrictModel):
    """Freeze the reviewed source-free exact resolution policy."""

    on_input_binding_mismatch: Literal["stop"]
    on_invalid_record_or_schema: Literal["stop"]
    on_population_mismatch: Literal["stop"]
    exact_first: Literal[True]
    leading_identifier_fallback: Literal[True]
    attached_title_fallback: Literal[True]
    structured_appendix_designator_normalization: Literal[True]
    unique_outer_appendix_document: Literal[True]
    reject_more_specific_appendix_downgrade: Literal[True]
    block_known_f1_source_identity_failure: Literal[True]
    source_filter_before_cardinality: Literal[True]
    deduplicate_target_ids_before_cardinality: Literal[True]
    fuzzy_or_semantic_matching: Literal[False]
    source_pdf_access: Literal[False]
    hash_large_upstream_payloads: Literal[False]
    allow_policy_repair_during_run: Literal[False]


class RelationshipStopBehavior(StrictModel):
    """Freeze exact-only Gate 1 and forbid in-run matching expansion."""

    on_input_binding_mismatch: Literal["stop"]
    on_invalid_record_or_schema: Literal["stop"]
    on_nondeterministic_semantic_output: Literal["stop"]
    exact_official_labels_only: Literal[True]
    normalize_whitespace: Literal[False]
    normalize_punctuation: Literal[False]
    normalize_case: Literal[False]
    infer_letter_suffix_relationships: Literal[False]
    fuzzy_or_semantic_matching: Literal[False]
    allow_policy_repair_during_run: Literal[False]


class ResponseInventoryRunSpec(StrictModel):
    """One explicit and bounded Task 05C pilot recipe."""

    schema_version: Literal["er_commons.response_inventory_run_spec.v1"]
    task_stage: Literal["05c"]
    scope_kind: Literal["representative_pilot"]
    source: SourceBinding
    accepted_inputs: tuple[ArtifactReference, ...]
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_ranges: tuple[PageRange, ...]
    declared_page_count: int = Field(gt=0)
    restart_unit: Literal["declared_page_range"]
    cross_gap_continuations_allowed: Literal[False]
    output_policy: OutputPolicy
    cache_policy: CachePolicy
    stop_behavior: StopBehavior

    @model_validator(mode="after")
    def validate_closed_selection_and_roles(self) -> ResponseInventoryRunSpec:
        """Close range accounting and require one binding for every owned role."""
        if not self.page_ranges:
            raise ValueError("run spec must declare at least one page range")
        previous_last = 0
        for page_range in self.page_ranges:
            if page_range.first_page <= previous_last:
                raise ValueError("page ranges must be ordered and non-overlapping")
            if page_range.last_page > self.source.recorded_page_count:
                raise ValueError("page range exceeds the recorded source page count")
            previous_last = page_range.last_page
        actual_page_count = sum(item.page_count for item in self.page_ranges)
        if self.declared_page_count != actual_page_count:
            raise ValueError(
                "declared page count differs from inclusive ranges: "
                f"declared={self.declared_page_count}, ranges={actual_page_count}"
            )
        observed_ranges = tuple((item.first_page, item.last_page) for item in self.page_ranges)
        if observed_ranges != TASK05C_PILOT_RANGES:
            raise ValueError("05C run spec differs from the exact authorized pilot ranges")
        _require_exact_roles(
            [item.role for item in self.accepted_inputs],
            {"task05a_completion", "source_release_completion", "source_manifest"},
            "accepted input",
        )
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {"response_record_schema", "producer_run_spec_code"},
            "repository binding",
        )
        if self.stop_behavior.allowed_terminal_warning_codes != ("unit_boundary_ambiguous",):
            raise ValueError("05C allows only its declared right-censored boundary warning")
        return self


class ResponseInventoryRunSpecV2(StrictModel):
    """One exact complete-source Task 05D recipe."""

    schema_version: Literal["er_commons.response_inventory_run_spec.v2"]
    task_stage: Literal["05d"]
    scope_kind: Literal["complete_source_inventory"]
    source: SourceBinding
    accepted_task05c: AcceptedTask05C
    accepted_inputs: tuple[ArtifactReferenceV2, ...]
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_ranges: tuple[PageRange, ...]
    declared_page_count: Literal[744]
    restart_unit: Literal["declared_page_range"]
    cross_gap_continuations_allowed: Literal[False]
    output_policy: CompleteOutputPolicy
    cache_policy: CompleteCachePolicy
    stop_behavior: CompleteStopBehavior

    @model_validator(mode="after")
    def validate_complete_scope_and_roles(self) -> ResponseInventoryRunSpecV2:
        """Require the sole full-source range and every exact evidence role."""
        observed_ranges = tuple((item.first_page, item.last_page) for item in self.page_ranges)
        if observed_ranges != (TASK05D_RANGE,):
            raise ValueError("05D run spec must declare only the exact 1-744 range")
        if self.source.recorded_page_count != TASK05D_PAGE_COUNT:
            raise ValueError("05D source binding must record exactly 744 pages")
        _require_exact_roles(
            [item.role for item in self.accepted_inputs],
            {
                "task05a_structural_profile",
                "task05c_build_summary",
                "task05c_completion",
                "task05c_managed_inventory",
                "task05c_qualification",
                "task05c_source_records",
                "source_release_completion",
                "source_manifest",
            },
            "accepted input",
        )
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {"response_record_schema", "producer_run_spec_code"},
            "repository binding",
        )
        return self


class ResponseRelationshipRunSpecV3(StrictModel):
    """One source-free exact-only Task 05E baseline recipe."""

    schema_version: Literal["er_commons.response_relationship_run_spec.v3"]
    task_stage: Literal["05e"]
    scope_kind: Literal["exact_relationship_baseline"]
    accepted_task05d: AcceptedTask05D
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_policy: RelationshipOutputPolicy
    stop_behavior: RelationshipStopBehavior

    @model_validator(mode="after")
    def validate_exact_gate(self) -> ResponseRelationshipRunSpecV3:
        """Require all source-free schema/code bindings for the frozen baseline."""
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {
                "response_record_schema",
                "producer_run_spec_code",
                "relationship_run_spec_schema",
            },
            "repository binding",
        )
        return self


class AcceptedRelationshipBaseline(StrictModel):
    """Exact Gate 1 evidence that the bounded review pass must preserve."""

    baseline_root: Path
    activity_id: Literal[
        "activityv1-50ae2f7de5f28e882e62627db103e03f0059677fcdfc1e1f8be3a9bf5232b778"
    ]
    census_digest: Literal["ff509e0a5434b7a4e41a83ac94b950c3a70a84f99f954aca57d1fd0f087ff246"]

    @model_validator(mode="after")
    def validate_path(self) -> AcceptedRelationshipBaseline:
        """Require the exact named Gate 1 namespace under the artifact root."""
        _require_contained_path(self.baseline_root, "05E Gate 1 baseline")
        expected = f"baselinev1-{self.activity_id.removeprefix('activityv1-')}"
        if self.baseline_root.name != expected:
            raise ValueError("Gate 1 baseline path differs from its activity ID")
        return self


class RelationshipReviewPolicy(StrictModel):
    """Exact bounded amendments authorized for the current Gate 2 review replay."""

    normalize_case: Literal[True]
    collapse_whitespace: Literal[True]
    recover_u0002_separator_in_reference_mentions: Literal[True]
    classify_self_mentions_without_edges: Literal[True]
    allow_general_response_response_edges: Literal[True]
    allow_general_response_general_response_edges: Literal[True]
    classify_running_headers_without_edges: Literal[True]
    classify_response_section_headings_without_edges: Literal[True]
    classify_ordinary_response_prose_without_edges: Literal[True]
    terminal_unresolved_reference_labels: tuple[Literal["Response OSEC-21"], ...]
    terminal_unpaired_source_labels: tuple[
        Literal["Comment SA-Caltrans-48", "Response SA-Caltrans-48a"], ...
    ]
    typed_membership_suffix: Literal[True]
    membership_aliases: dict[
        Literal["O-OSEC-106", "O-OSEC-370", "O-OSEC-371", "O-OSEC-375", "O-OSEC-379"],
        Literal["M-OSEC-106", "M-OSEC-370", "M-OSEC-371", "M-OSEC-375", "M-OSEC-379"],
    ]
    strip_one_terminal_period: Literal[True]
    infer_letter_suffix_relationships: Literal[False]
    fuzzy_or_semantic_matching: Literal[False]

    @model_validator(mode="after")
    def validate_aliases(self) -> RelationshipReviewPolicy:
        """Freeze the reviewed aliases and terminal document-specific exceptions."""
        expected = {
            "O-OSEC-106": "M-OSEC-106",
            "O-OSEC-370": "M-OSEC-370",
            "O-OSEC-371": "M-OSEC-371",
            "O-OSEC-375": "M-OSEC-375",
            "O-OSEC-379": "M-OSEC-379",
        }
        if self.membership_aliases != expected:
            raise ValueError("membership aliases must be exactly the five reviewed O-OSEC typos")
        if self.terminal_unresolved_reference_labels != ("Response OSEC-21",):
            raise ValueError("terminal unresolved references differ from the reviewed typo")
        if self.terminal_unpaired_source_labels != (
            "Comment SA-Caltrans-48",
            "Response SA-Caltrans-48a",
        ):
            raise ValueError("terminal unpaired labels differ from the reviewed source form")
        return self


class ResponseRelationshipReviewRunSpecV4(StrictModel):
    """One source-free bounded-amendment review replay for Task 05E."""

    schema_version: Literal["er_commons.response_relationship_run_spec.v4"]
    task_stage: Literal["05e"]
    scope_kind: Literal["bounded_relationship_review"]
    accepted_task05d: AcceptedTask05D
    accepted_gate1: AcceptedRelationshipBaseline
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_policy: RelationshipReviewOutputPolicy
    resolution_policy: RelationshipReviewPolicy

    @model_validator(mode="after")
    def validate_review_gate(self) -> ResponseRelationshipReviewRunSpecV4:
        """Require the same closed schema/code roles as the exact baseline."""
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {
                "response_record_schema",
                "producer_run_spec_code",
                "relationship_run_spec_schema",
            },
            "repository binding",
        )
        return self


class ResponseReferenceRunSpecV5(StrictModel):
    """One source-free qualified exact-rule recipe for Task 05F."""

    schema_version: Literal["er_commons.response_reference_run_spec.v5"]
    task_stage: Literal["05f"]
    scope_kind: Literal["qualified_exact_draft_eir_reference_rules"]
    accepted_task05d: AcceptedTask05D
    accepted_task05e: AcceptedTask05E
    task04: Task04ReferenceBindings
    repository_bindings: tuple[RepositoryBinding, ...]
    producer_code_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_policy: ReferenceOutputPolicy
    stop_behavior: ReferenceStopBehavior

    @model_validator(mode="after")
    def validate_qualified_rules(self) -> ResponseReferenceRunSpecV5:
        """Require the exact small schemas, code, and collection spec."""
        _require_exact_roles(
            [item.role for item in self.repository_bindings],
            {
                "producer_run_spec_code",
                "reference_outcome_schema",
                "response_record_schema",
                "reference_run_spec_schema",
                "task04d_collection_spec",
            },
            "repository binding",
        )
        return self


AnyResponseInventoryRunSpec = (
    ResponseInventoryRunSpec
    | ResponseInventoryRunSpecV2
    | ResponseRelationshipRunSpecV3
    | ResponseRelationshipReviewRunSpecV4
    | ResponseReferenceRunSpecV5
)


def load_response_inventory_run_spec(path: Path) -> tuple[AnyResponseInventoryRunSpec, str]:
    """Load one strict run spec and return the digest used by its activity."""
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("response inventory run spec must be a JSON object")
    spec: AnyResponseInventoryRunSpec
    if payload.get("schema_version") == "er_commons.response_reference_run_spec.v5":
        spec = ResponseReferenceRunSpecV5.model_validate_json(raw)
    elif payload.get("schema_version") == "er_commons.response_relationship_run_spec.v4":
        spec = ResponseRelationshipReviewRunSpecV4.model_validate_json(raw)
    elif payload.get("schema_version") == "er_commons.response_relationship_run_spec.v3":
        spec = ResponseRelationshipRunSpecV3.model_validate_json(raw)
    elif payload.get("schema_version") == "er_commons.response_inventory_run_spec.v2":
        spec = ResponseInventoryRunSpecV2.model_validate_json(raw)
    else:
        spec = ResponseInventoryRunSpec.model_validate_json(raw)
    return spec, hashlib.sha256(raw).hexdigest()


def verify_repository_bindings(spec: AnyResponseInventoryRunSpec, repository_root: Path) -> None:
    """Verify small checked-in dependencies without touching source artifacts."""
    root = repository_root.resolve()
    for binding in spec.repository_bindings:
        path = (root / binding.path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"repository binding is missing or escapes the repository: {path}")
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != binding.sha256:
            raise ValueError(f"repository binding digest mismatch: {binding.role}")
    if owned_code_digest(root) != spec.producer_code_sha256:
        raise ValueError("producer code digest mismatch")


def _require_contained_path(path: Path, label: str) -> None:
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{label} path must be a contained relative path")


def _require_exact_roles(actual: list[str], expected: set[str], label: str) -> None:
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(f"{label} roles must be exactly {sorted(expected)}")


__all__ = [
    "AnyResponseInventoryRunSpec",
    "ResponseInventoryRunSpec",
    "ResponseInventoryRunSpecV2",
    "ResponseRelationshipRunSpecV3",
    "ResponseRelationshipReviewRunSpecV4",
    "ResponseReferenceRunSpecV5",
    "load_response_inventory_run_spec",
    "verify_repository_bindings",
]
