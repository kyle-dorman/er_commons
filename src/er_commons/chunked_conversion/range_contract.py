"""Strict identities and records for restartable inclusive page ranges."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal, Never, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.document_parsing.content_parsing.identity import canonical_json_sha256


class RangeContractError(ValueError):
    """One fail-closed range invariant with artifact-level context."""


class StrictRangeRecord(BaseModel):
    """Immutable contract record that rejects unknown fields and coercion."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class PageInterval(StrictRangeRecord):
    """One one-based inclusive physical-page interval."""

    start: int = Field(ge=1)
    end: int = Field(ge=1)

    @model_validator(mode="after")
    def require_ordered_bounds(self) -> Self:
        """Reject reversed intervals rather than silently normalizing them."""
        if self.end < self.start:
            raise ValueError("inclusive page interval end must be at least start")
        return self

    @property
    def pages(self) -> tuple[int, ...]:
        """Return every owned physical page in inclusive order."""
        return tuple(range(self.start, self.end + 1))

    def contains(self, page: int) -> bool:
        """Report whether a physical page lies inside the inclusive interval."""
        return self.start <= page <= self.end


class SourceIdentity(StrictRangeRecord):
    """Source facts that every plan and child completion must reproduce."""

    source_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)
    physical_page_count: int = Field(gt=0)


class OverlapPolicy(StrictRangeRecord):
    """Maximum pages a range may read outside each side of its core."""

    max_left_pages: int = Field(ge=0)
    max_right_pages: int = Field(ge=0)
    comparison: Literal["page_evidence_digest"] = "page_evidence_digest"


class OverlapOwner(StrictRangeRecord):
    """Core interval that owns one overlap page read by another range."""

    page: int = Field(ge=1)
    owner_core: PageInterval


class RangeDefinition(StrictRangeRecord):
    """Identity-bearing core/read intervals before plan and range IDs exist."""

    core: PageInterval
    read: PageInterval
    overlap_owners: tuple[OverlapOwner, ...] = ()

    @model_validator(mode="after")
    def require_local_interval_consistency(self) -> Self:
        """Require the read interval to contain the core and name each overlap once."""
        if self.read.start > self.core.start or self.read.end < self.core.end:
            raise ValueError("read interval must contain the complete core interval")
        overlap_pages = tuple(owner.page for owner in self.overlap_owners)
        expected = tuple(page for page in self.read.pages if not self.core.contains(page))
        if overlap_pages != expected:
            raise ValueError(
                "overlap owners must name every non-core read page once in physical-page order"
            )
        return self


class RangePlanInputs(StrictRangeRecord):
    """Complete semantic preimage for one deterministic range plan."""

    schema_version: Literal["er_commons.docling_range_plan_inputs.v1"] = (
        "er_commons.docling_range_plan_inputs.v1"
    )
    source: SourceIdentity
    sealed_source_release_identity: str = Field(min_length=1)
    converter_identity: str = Field(min_length=1)
    package_identity: str = Field(min_length=1)
    model_identity: str = Field(min_length=1)
    adapter_identity: str = Field(min_length=1)
    page_evidence_contract_identity: str = Field(min_length=1)
    range_conversion_identity: str = Field(min_length=1)
    range_planner_identity: str = Field(min_length=1)
    aggregate_merge_identity: str = Field(min_length=1)
    target_range_size: int = Field(gt=0)
    hard_maximum: int = Field(gt=0)
    planner_mode: Literal["fixed_size", "content_adaptive"] = "fixed_size"
    max_native_content_units_per_range: int | None = Field(default=None, gt=0)
    content_profile_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    overlap_policy: OverlapPolicy
    ranges: tuple[RangeDefinition, ...] = Field(min_length=1)
    aggregate_output_schema_identity: str = Field(min_length=1)
    global_interpretation_policy_identity: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_sensible_sizes(self) -> Self:
        """Keep the target at or below the planner's hard core-page cap."""
        if self.target_range_size > self.hard_maximum:
            raise ValueError("target range size cannot exceed hard maximum")
        adaptive_fields = {
            "max_native_content_units_per_range": self.max_native_content_units_per_range,
            "content_profile_sha256": self.content_profile_sha256,
        }
        if self.planner_mode == "content_adaptive":
            missing = [name for name, value in adaptive_fields.items() if value is None]
            if missing:
                raise ValueError(
                    "content-adaptive plans require both a native content budget "
                    f"and profile digest; missing={missing!r}"
                )
        else:
            declared = [name for name, value in adaptive_fields.items() if value is not None]
            if declared:
                raise ValueError(
                    "fixed-size plans cannot declare adaptive planning fields; "
                    f"declared={declared!r}"
                )
        return self


class PlannedRange(StrictRangeRecord):
    """One canonical range bound to its deterministic child identity."""

    range_id: str = Field(pattern=r"^drange1-[0-9a-f]{64}$")
    core: PageInterval
    read: PageInterval
    overlap_owners: tuple[OverlapOwner, ...] = ()

    @property
    def definition(self) -> RangeDefinition:
        """Project the persisted range back to its ID preimage record."""
        return RangeDefinition(
            core=self.core,
            read=self.read,
            overlap_owners=self.overlap_owners,
        )


class RangePlan(StrictRangeRecord):
    """Canonical ordered plan whose ID excludes operational completion order."""

    schema_version: Literal["er_commons.docling_range_plan.v1"] = "er_commons.docling_range_plan.v1"
    plan_id: str = Field(pattern=r"^dplan1-[0-9a-f]{64}$")
    inputs: RangePlanInputs
    ranges: tuple[PlannedRange, ...]

    @model_validator(mode="after")
    def require_canonical_identity_and_order(self) -> Self:
        """Reject forged IDs or persisted ranges outside canonical core order."""
        definitions = _canonical_definitions(self.inputs)
        if self.inputs.ranges != definitions:
            raise ValueError("range plan inputs must persist ranges in canonical core order")
        expected_plan_id = f"dplan1-{canonical_json_sha256(_plan_preimage(self.inputs))}"
        if self.plan_id != expected_plan_id:
            raise ValueError("range plan ID does not match its canonical identity preimage")
        if len(self.ranges) != len(definitions):
            raise ValueError("planned ranges must exactly match the input range definitions")
        for planned, definition in zip(self.ranges, definitions, strict=True):
            if planned.definition != definition:
                raise ValueError("planned range differs from its canonical input definition")
            if planned.range_id != _derive_range_id(self.plan_id, self.inputs, definition):
                raise ValueError("range ID does not match its canonical identity preimage")
        return self


class RangeCompletion(StrictRangeRecord):
    """Completion-last semantic seal for one independently verified child range."""

    schema_version: Literal["er_commons.docling_range_completion.v1"] = (
        "er_commons.docling_range_completion.v1"
    )
    plan_id: str = Field(pattern=r"^dplan1-[0-9a-f]{64}$")
    range_id: str = Field(pattern=r"^drange1-[0-9a-f]{64}$")
    source: SourceIdentity
    core: PageInterval
    read: PageInterval
    overlap_owners: tuple[OverlapOwner, ...]
    range_conversion_identity: str = Field(min_length=1)
    expected_pages: tuple[int, ...]
    converted_pages: tuple[int, ...]
    successful_pages: tuple[int, ...]
    overlap_pages: tuple[int, ...]
    core_owned_pages: tuple[int, ...]
    artifact_inventory_path: str = Field(min_length=1)
    artifact_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["complete"] = "complete"
    errors: tuple[()] = ()
    completion_last: Literal[True] = True

    @model_validator(mode="after")
    def require_contained_inventory_path(self) -> Self:
        """Keep child inventory references relative to their immutable bundle."""
        path = PurePosixPath(self.artifact_inventory_path)
        if path.is_absolute() or ".." in path.parts or path.as_posix() in {"", "."}:
            raise ValueError("artifact inventory path must be a contained relative path")
        return self


def _raise_contract_error(
    *,
    plan_id: str,
    range_id: str,
    path: str,
    invariant: str,
    expected: object,
    actual: object,
) -> Never:
    """Raise one diagnostic containing every context field required by the spec."""
    raise RangeContractError(
        f"plan={plan_id} range={range_id} path={path} invariant={invariant} "
        f"expected={expected!r} actual={actual!r}"
    )


def _derive_range_id(
    plan_id: str,
    inputs: RangePlanInputs,
    definition: RangeDefinition,
) -> str:
    """Hash one child identity without operational scheduling or resource facts."""
    payload = {
        "plan_id": plan_id,
        "source": inputs.source.model_dump(mode="json"),
        "core": definition.core.model_dump(mode="json"),
        "read": definition.read.model_dump(mode="json"),
        "overlap_owners": [owner.model_dump(mode="json") for owner in definition.overlap_owners],
        "range_conversion_identity": inputs.range_conversion_identity,
    }
    return f"drange1-{canonical_json_sha256(payload)}"


def _plan_preimage(inputs: RangePlanInputs) -> dict[str, object]:
    """Exclude aggregate-only interpretation from reusable child-plan identity."""
    payload = inputs.model_dump(mode="json")
    # Keep the v1 fixed-size identity byte-compatible with plans written before
    # content-adaptive planning was added.  Adaptive plans intentionally retain
    # their planner mode, budget, and source-derived profile digest.
    if inputs.planner_mode == "fixed_size":
        payload.pop("planner_mode", None)
        payload.pop("max_native_content_units_per_range", None)
        payload.pop("content_profile_sha256", None)
    for key in (
        "aggregate_merge_identity",
        "aggregate_output_schema_identity",
        "global_interpretation_policy_identity",
    ):
        payload.pop(key)
    return payload


def _canonical_definitions(inputs: RangePlanInputs) -> tuple[RangeDefinition, ...]:
    """Validate and sort range definitions into physical core order."""
    definitions = tuple(sorted(inputs.ranges, key=lambda item: (item.core.start, item.core.end)))
    expected_start = 1
    cores = {item.core for item in definitions}
    for index, definition in enumerate(definitions):
        path = f"ranges[{index}]"
        if definition.core.start != expected_start:
            invariant = (
                "duplicate_core_owner" if definition.core.start < expected_start else "coverage_gap"
            )
            _raise_contract_error(
                plan_id="unbuilt",
                range_id="unbuilt",
                path=f"{path}.core.start",
                invariant=invariant,
                expected=expected_start,
                actual=definition.core.start,
            )
        if definition.core.end - definition.core.start + 1 > inputs.hard_maximum:
            _raise_contract_error(
                plan_id="unbuilt",
                range_id="unbuilt",
                path=f"{path}.core",
                invariant="hard_maximum",
                expected=f"at most {inputs.hard_maximum} pages",
                actual=definition.core.pages,
            )
        if definition.read.end > inputs.source.physical_page_count:
            _raise_contract_error(
                plan_id="unbuilt",
                range_id="unbuilt",
                path=f"{path}.read.end",
                invariant="source_page_bounds",
                expected=inputs.source.physical_page_count,
                actual=definition.read.end,
            )
        left_overlap = definition.core.start - definition.read.start
        right_overlap = definition.read.end - definition.core.end
        if left_overlap > inputs.overlap_policy.max_left_pages:
            _raise_contract_error(
                plan_id="unbuilt",
                range_id="unbuilt",
                path=f"{path}.read.start",
                invariant="left_overlap_bound",
                expected=f"at most {inputs.overlap_policy.max_left_pages}",
                actual=left_overlap,
            )
        if right_overlap > inputs.overlap_policy.max_right_pages:
            _raise_contract_error(
                plan_id="unbuilt",
                range_id="unbuilt",
                path=f"{path}.read.end",
                invariant="right_overlap_bound",
                expected=f"at most {inputs.overlap_policy.max_right_pages}",
                actual=right_overlap,
            )
        for owner_index, overlap in enumerate(definition.overlap_owners):
            owner_path = f"{path}.overlap_owners[{owner_index}]"
            if overlap.owner_core not in cores:
                _raise_contract_error(
                    plan_id="unbuilt",
                    range_id="unbuilt",
                    path=f"{owner_path}.owner_core",
                    invariant="overlap_owner_exists",
                    expected="one plan core interval",
                    actual=overlap.owner_core,
                )
            if not overlap.owner_core.contains(overlap.page):
                _raise_contract_error(
                    plan_id="unbuilt",
                    range_id="unbuilt",
                    path=f"{owner_path}.page",
                    invariant="overlap_core_owner",
                    expected=overlap.owner_core.pages,
                    actual=overlap.page,
                )
        expected_start = definition.core.end + 1
    if expected_start != inputs.source.physical_page_count + 1:
        _raise_contract_error(
            plan_id="unbuilt",
            range_id="unbuilt",
            path="ranges",
            invariant="coverage_gap",
            expected=f"coverage through page {inputs.source.physical_page_count}",
            actual=f"coverage through page {expected_start - 1}",
        )
    return definitions


def build_range_plan(inputs: RangePlanInputs) -> RangePlan:
    """Validate a plan and derive canonical plan/range IDs from semantic inputs."""
    definitions = _canonical_definitions(inputs)
    canonical_inputs = inputs.model_copy(update={"ranges": definitions})
    plan_id = f"dplan1-{canonical_json_sha256(_plan_preimage(canonical_inputs))}"
    ranges = tuple(
        PlannedRange(
            range_id=_derive_range_id(plan_id, canonical_inputs, definition),
            core=definition.core,
            read=definition.read,
            overlap_owners=definition.overlap_owners,
        )
        for definition in definitions
    )
    return RangePlan(plan_id=plan_id, inputs=canonical_inputs, ranges=ranges)


def validate_range_completion(
    plan: RangePlan,
    completion: RangeCompletion,
    *,
    path: str,
) -> None:
    """Fail closed unless one child completion exactly matches its planned range."""
    range_by_id = {item.range_id: item for item in plan.ranges}
    planned = range_by_id.get(completion.range_id)
    if planned is None:
        _raise_contract_error(
            plan_id=plan.plan_id,
            range_id=completion.range_id,
            path=path,
            invariant="range_identity_mismatch",
            expected=tuple(range_by_id),
            actual=completion.range_id,
        )
    comparisons = (
        ("plan_id", plan.plan_id, completion.plan_id, "plan_identity"),
        ("source", plan.inputs.source, completion.source, "source_identity"),
        ("core", planned.core, completion.core, "core_interval"),
        ("read", planned.read, completion.read, "read_interval"),
        (
            "overlap_owners",
            planned.overlap_owners,
            completion.overlap_owners,
            "overlap_ownership",
        ),
        (
            "range_conversion_identity",
            plan.inputs.range_conversion_identity,
            completion.range_conversion_identity,
            "range_conversion_identity",
        ),
        ("expected_pages", planned.read.pages, completion.expected_pages, "expected_pages"),
        ("converted_pages", planned.read.pages, completion.converted_pages, "page_coverage"),
        ("successful_pages", planned.read.pages, completion.successful_pages, "page_success"),
        (
            "overlap_pages",
            tuple(owner.page for owner in planned.overlap_owners),
            completion.overlap_pages,
            "overlap_page_coverage",
        ),
        (
            "core_owned_pages",
            planned.core.pages,
            completion.core_owned_pages,
            "core_page_coverage",
        ),
    )
    for field, expected, actual, invariant in comparisons:
        if actual != expected:
            _raise_contract_error(
                plan_id=plan.plan_id,
                range_id=completion.range_id,
                path=f"{path}.{field}",
                invariant=invariant,
                expected=expected,
                actual=actual,
            )


def canonicalize_completions(
    plan: RangePlan,
    completions: tuple[RangeCompletion, ...],
    *,
    path: str = "range_completions",
) -> tuple[RangeCompletion, ...]:
    """Validate an unordered completion set and return canonical core-page order."""
    by_id: dict[str, RangeCompletion] = {}
    for index, completion in enumerate(completions):
        if completion.range_id in by_id:
            _raise_contract_error(
                plan_id=plan.plan_id,
                range_id=completion.range_id,
                path=f"{path}[{index}]",
                invariant="duplicate_range_completion",
                expected="one completion per range",
                actual=completion.range_id,
            )
        validate_range_completion(plan, completion, path=f"{path}[{index}]")
        by_id[completion.range_id] = completion
    missing = tuple(item.range_id for item in plan.ranges if item.range_id not in by_id)
    if missing:
        _raise_contract_error(
            plan_id=plan.plan_id,
            range_id=missing[0],
            path=path,
            invariant="missing_range",
            expected=tuple(item.range_id for item in plan.ranges),
            actual=tuple(by_id),
        )
    return tuple(by_id[item.range_id] for item in plan.ranges)


__all__ = [
    "OverlapOwner",
    "OverlapPolicy",
    "PageInterval",
    "PlannedRange",
    "RangeCompletion",
    "RangeContractError",
    "RangeDefinition",
    "RangePlan",
    "RangePlanInputs",
    "SourceIdentity",
    "build_range_plan",
    "canonicalize_completions",
    "validate_range_completion",
]
