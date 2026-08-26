"""Contract-only tests for restartable chunk range identities and seals."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from er_commons.chunked_conversion.range_contract import (
    OverlapOwner,
    OverlapPolicy,
    PageInterval,
    RangeCompletion,
    RangeContractError,
    RangeDefinition,
    RangePlan,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
    canonicalize_completions,
    validate_range_completion,
)


def _definitions() -> tuple[RangeDefinition, ...]:
    first = PageInterval(start=1, end=3)
    second = PageInterval(start=4, end=6)
    third = PageInterval(start=7, end=8)
    return (
        RangeDefinition(
            core=first,
            read=PageInterval(start=1, end=4),
            overlap_owners=(OverlapOwner(page=4, owner_core=second),),
        ),
        RangeDefinition(
            core=second,
            read=PageInterval(start=3, end=7),
            overlap_owners=(
                OverlapOwner(page=3, owner_core=first),
                OverlapOwner(page=7, owner_core=third),
            ),
        ),
        RangeDefinition(
            core=third,
            read=PageInterval(start=6, end=8),
            overlap_owners=(OverlapOwner(page=6, owner_core=second),),
        ),
    )


def _inputs(
    ranges: tuple[RangeDefinition, ...] | None = None,
    *,
    page_count: int = 8,
    max_left: int = 1,
    max_right: int = 1,
) -> RangePlanInputs:
    return RangePlanInputs(
        source=SourceIdentity(
            source_id="example",
            sha256="a" * 64,
            byte_size=1234,
            physical_page_count=page_count,
        ),
        sealed_source_release_identity="release-v1",
        converter_identity="converter-v1",
        package_identity="packages-v1",
        model_identity="models-v1",
        adapter_identity="adapter-v1",
        page_evidence_contract_identity="page-evidence-v1",
        range_conversion_identity="range-conversion-v1",
        range_planner_identity="planner-v1",
        aggregate_merge_identity="merge-v1",
        target_range_size=3,
        hard_maximum=3,
        overlap_policy=OverlapPolicy(
            max_left_pages=max_left,
            max_right_pages=max_right,
        ),
        ranges=_definitions() if ranges is None else ranges,
        aggregate_output_schema_identity="outputs-v1",
        global_interpretation_policy_identity="interpretation-v1",
    )


def _completion(plan_index: int = 0) -> RangeCompletion:
    plan = build_range_plan(_inputs())
    planned = plan.ranges[plan_index]
    return RangeCompletion(
        plan_id=plan.plan_id,
        range_id=planned.range_id,
        source=plan.inputs.source,
        core=planned.core,
        read=planned.read,
        overlap_owners=planned.overlap_owners,
        range_conversion_identity=plan.inputs.range_conversion_identity,
        expected_pages=planned.read.pages,
        converted_pages=planned.read.pages,
        successful_pages=planned.read.pages,
        overlap_pages=tuple(owner.page for owner in planned.overlap_owners),
        core_owned_pages=planned.core.pages,
        artifact_inventory_path="records/artifact_inventory.json",
        artifact_inventory_sha256="b" * 64,
    )


def test_intervals_are_one_based_inclusive_and_strict() -> None:
    assert PageInterval(start=2, end=4).pages == (2, 3, 4)
    with pytest.raises(ValidationError):
        PageInterval(start=0, end=1)
    with pytest.raises(ValidationError, match="end must be at least start"):
        PageInterval(start=2, end=1)
    with pytest.raises(ValidationError):
        PageInterval(start="1", end=2)  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PageInterval.model_validate({"start": 1, "end": 2, "inclusive": True})


def test_plan_identity_is_canonical_and_completion_order_independent() -> None:
    forward = build_range_plan(_inputs())
    reversed_input = build_range_plan(_inputs(tuple(reversed(_definitions()))))

    assert forward == reversed_input
    assert [item.core.pages for item in forward.ranges] == [(1, 2, 3), (4, 5, 6), (7, 8)]
    assert len({item.range_id for item in forward.ranges}) == 3

    completions = tuple(_completion(index) for index in range(3))
    assert canonicalize_completions(forward, completions) == completions
    assert canonicalize_completions(forward, tuple(reversed(completions))) == completions


@pytest.mark.parametrize(
    "missing_field",
    ["max_native_content_units_per_range", "content_profile_sha256"],
)
def test_adaptive_plan_inputs_require_budget_and_profile_digest(missing_field: str) -> None:
    payload = _inputs().model_dump(mode="python")
    payload.update(
        {
            "planner_mode": "content_adaptive",
            "max_native_content_units_per_range": 500_000,
            "content_profile_sha256": "b" * 64,
            missing_field: None,
        }
    )

    with pytest.raises(ValidationError, match="require both"):
        RangePlanInputs.model_validate(payload)


@pytest.mark.parametrize(
    "declared_field",
    ["max_native_content_units_per_range", "content_profile_sha256"],
)
def test_fixed_plan_inputs_reject_adaptive_fields(declared_field: str) -> None:
    payload = _inputs().model_dump(mode="python")
    payload[declared_field] = 500_000 if declared_field.startswith("max_") else "b" * 64

    with pytest.raises(ValidationError, match="cannot declare adaptive planning fields"):
        RangePlanInputs.model_validate(payload)


@pytest.mark.parametrize(
    ("ranges", "message"),
    [
        (
            (
                RangeDefinition(
                    core=PageInterval(start=1, end=2), read=PageInterval(start=1, end=2)
                ),
                RangeDefinition(
                    core=PageInterval(start=4, end=6), read=PageInterval(start=4, end=6)
                ),
                RangeDefinition(
                    core=PageInterval(start=7, end=8), read=PageInterval(start=7, end=8)
                ),
            ),
            "invariant=coverage_gap",
        ),
        (
            (
                RangeDefinition(
                    core=PageInterval(start=1, end=3), read=PageInterval(start=1, end=3)
                ),
                RangeDefinition(
                    core=PageInterval(start=3, end=5), read=PageInterval(start=3, end=5)
                ),
                RangeDefinition(
                    core=PageInterval(start=6, end=8), read=PageInterval(start=6, end=8)
                ),
            ),
            "invariant=duplicate_core_owner",
        ),
    ],
)
def test_plan_rejects_gapped_or_duplicate_core_coverage(
    ranges: tuple[RangeDefinition, ...], message: str
) -> None:
    with pytest.raises(RangeContractError, match=message):
        build_range_plan(_inputs(ranges, page_count=8))


def test_plan_rejects_overlap_beyond_policy_with_context() -> None:
    first, second, third = _definitions()
    expanded = RangeDefinition(
        core=second.core,
        read=PageInterval(start=2, end=7),
        overlap_owners=(
            OverlapOwner(page=2, owner_core=first.core),
            OverlapOwner(page=3, owner_core=first.core),
            OverlapOwner(page=7, owner_core=third.core),
        ),
    )
    with pytest.raises(
        RangeContractError,
        match=r"path=ranges\[1\]\.read\.start invariant=left_overlap_bound",
    ):
        build_range_plan(_inputs((first, expanded, third)))


def test_plan_rejects_wrong_overlap_core_owner() -> None:
    first, second, third = _definitions()
    wrong = RangeDefinition(
        core=second.core,
        read=second.read,
        overlap_owners=(
            OverlapOwner(page=3, owner_core=third.core),
            OverlapOwner(page=7, owner_core=third.core),
        ),
    )
    with pytest.raises(RangeContractError, match="invariant=overlap_core_owner"):
        build_range_plan(_inputs((first, wrong, third)))


def test_merge_only_change_preserves_plan_and_child_identities() -> None:
    original = build_range_plan(_inputs())
    changed_inputs = _inputs().model_copy(update={"aggregate_merge_identity": "merge-v2"})
    changed = build_range_plan(changed_inputs)

    assert changed.plan_id == original.plan_id
    assert [item.range_id for item in changed.ranges] == [item.range_id for item in original.ranges]


def test_child_semantic_change_invalidates_plan_and_ranges() -> None:
    original = build_range_plan(_inputs())
    changed_inputs = _inputs().model_copy(update={"range_conversion_identity": "range-v2"})
    changed = build_range_plan(changed_inputs)

    assert changed.plan_id != original.plan_id
    assert [item.range_id for item in changed.ranges] != [item.range_id for item in original.ranges]


def test_persisted_plan_rejects_forged_plan_or_range_ids() -> None:
    plan = build_range_plan(_inputs())
    payload = plan.model_dump(mode="python")
    with pytest.raises(ValidationError, match="plan ID does not match"):
        RangePlan.model_validate({**payload, "plan_id": "dplan1-" + "f" * 64})

    forged_range = copy.deepcopy(payload)
    forged_range["ranges"][0]["range_id"] = "drange1-" + "f" * 64
    with pytest.raises(ValidationError, match="range ID does not match"):
        RangePlan.model_validate(forged_range)


def test_completion_requires_exact_planned_page_sequences_and_context() -> None:
    plan = build_range_plan(_inputs())
    completion = _completion(1)
    changed = completion.model_copy(update={"converted_pages": (3, 5, 4, 6, 7)})

    with pytest.raises(RangeContractError) as failure:
        validate_range_completion(plan, changed, path="children/range-2/completion_record.json")

    message = str(failure.value)
    assert f"plan={plan.plan_id}" in message
    assert f"range={completion.range_id}" in message
    assert "path=children/range-2/completion_record.json.converted_pages" in message
    assert "invariant=page_coverage" in message


def test_completion_set_rejects_missing_duplicate_and_identity_mismatch() -> None:
    plan = build_range_plan(_inputs())
    completions = tuple(_completion(index) for index in range(3))
    with pytest.raises(RangeContractError, match="invariant=missing_range"):
        canonicalize_completions(plan, completions[:2])
    with pytest.raises(RangeContractError, match="invariant=duplicate_range_completion"):
        canonicalize_completions(plan, (*completions, completions[0]))

    foreign_payload = copy.deepcopy(completions[0].model_dump(mode="python"))
    foreign_payload["range_id"] = "drange1-" + "f" * 64
    foreign = RangeCompletion.model_validate(foreign_payload)
    with pytest.raises(RangeContractError, match="invariant=range_identity_mismatch"):
        validate_range_completion(plan, foreign, path="foreign/completion_record.json")


def test_completion_record_is_closed_and_requires_terminal_success() -> None:
    valid = _completion().model_dump(mode="python")
    invalid_status = {**valid, "status": "partial"}
    with pytest.raises(ValidationError):
        RangeCompletion.model_validate(invalid_status)
    with pytest.raises(ValidationError):
        RangeCompletion.model_validate({**valid, "errors": ({"message": "failed"},)})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RangeCompletion.model_validate({**valid, "completed_at_utc": "arrival-order-data"})
    with pytest.raises(ValidationError, match="contained relative path"):
        RangeCompletion.model_validate({**valid, "artifact_inventory_path": "../inventory.json"})
