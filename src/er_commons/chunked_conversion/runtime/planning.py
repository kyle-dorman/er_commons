"""Deterministic source-neutral fallback planning from prepared source facts."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from er_commons.artifact_io import canonical_json_sha256
from er_commons.chunked_conversion.range_contract import (
    OverlapOwner,
    OverlapPolicy,
    PageInterval,
    RangeDefinition,
    RangePlan,
    RangePlanInputs,
    SourceIdentity,
    build_range_plan,
)
from er_commons.chunked_conversion.runtime.inputs import RuntimeCodeIdentity
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_parsing.content_parsing.routing import all_page_features


@dataclass(frozen=True)
class NativeContentPage:
    """Validated native-text complexity signals for one physical PDF page."""

    physical_pdf_page: int
    native_text_rectangle_count: int
    nonspace_character_count: int

    @classmethod
    def from_page_features(
        cls,
        features: Mapping[str, object],
        *,
        profile_index: int,
    ) -> NativeContentPage:
        """Read the three planning fields with strict integer/count validation."""
        return cls(
            physical_pdf_page=_required_integer(
                features,
                "physical_pdf_page",
                profile_index=profile_index,
                minimum=1,
            ),
            native_text_rectangle_count=_required_integer(
                features,
                "native_text_rectangle_count",
                profile_index=profile_index,
                minimum=0,
            ),
            nonspace_character_count=_required_integer(
                features,
                "nonspace_character_count",
                profile_index=profile_index,
                minimum=0,
            ),
        )

    @property
    def native_content_units(self) -> int:
        """Return the stable page-retention cost proxy used by the planner."""
        return max(
            1,
            self.native_text_rectangle_count,
            math.ceil(self.nonspace_character_count / 4),
        )

    def identity_record(self) -> dict[str, int]:
        """Serialize the existing adaptive-profile identity preimage exactly."""
        return {
            "physical_pdf_page": self.physical_pdf_page,
            "native_text_rectangle_count": self.native_text_rectangle_count,
            "nonspace_character_count": self.nonspace_character_count,
            "native_content_units": self.native_content_units,
        }


@dataclass(frozen=True)
class NativeContentProfile:
    """Complete ordered native-content profile for one source PDF."""

    pages: tuple[NativeContentPage, ...]

    @classmethod
    def from_page_features(
        cls,
        features: Sequence[Mapping[str, object]],
        *,
        expected_page_count: int,
    ) -> NativeContentProfile:
        """Require exactly one ordered feature record for every physical page."""
        pages = tuple(
            NativeContentPage.from_page_features(feature, profile_index=index)
            for index, feature in enumerate(features)
        )
        page_numbers = tuple(page.physical_pdf_page for page in pages)
        duplicates = sorted(
            page_number for page_number, count in Counter(page_numbers).items() if count > 1
        )
        if duplicates:
            raise ValueError(
                f"native content profile contains duplicate physical pages: {duplicates!r}"
            )

        expected_pages = tuple(range(1, expected_page_count + 1))
        actual_page_set = set(page_numbers)
        expected_page_set = set(expected_pages)
        if actual_page_set != expected_page_set:
            missing = sorted(expected_page_set - actual_page_set)
            unexpected = sorted(actual_page_set - expected_page_set)
            raise ValueError(
                "native content profile must cover every source page exactly once: "
                f"missing={missing!r} unexpected={unexpected!r}"
            )
        if page_numbers != expected_pages:
            raise ValueError(
                "native content profile must be ordered by physical page: "
                f"expected={expected_pages!r} actual={page_numbers!r}"
            )
        return cls(pages=pages)

    @property
    def content_units(self) -> tuple[int, ...]:
        """Return per-page cost units in validated physical-page order."""
        return tuple(page.native_content_units for page in self.pages)

    def identity_records(self) -> list[dict[str, int]]:
        """Return canonical records for the adaptive profile digest."""
        return [page.identity_record() for page in self.pages]


def _required_integer(
    features: Mapping[str, object],
    field: str,
    *,
    profile_index: int,
    minimum: int,
) -> int:
    """Read one strict integer field with profile-row context on failure."""
    if field not in features:
        raise ValueError(f"native content profile row {profile_index} is missing {field!r}")
    value = features[field]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"native content profile row {profile_index} field {field!r} "
            f"must be an integer, got {value!r}"
        )
    if value < minimum:
        raise ValueError(
            f"native content profile row {profile_index} field {field!r} "
            f"must be at least {minimum}, got {value}"
        )
    return value


def build_fixed_size_plan(
    prepared: PreparedContentParsing,
    code: RuntimeCodeIdentity,
    *,
    target_range_size: int = 225,
    hard_maximum: int = 275,
    overlap_pages: int = 1,
) -> RangePlan:
    """Build contiguous fixed-size cores without inspecting source PDF content."""
    if not 1 <= target_range_size <= hard_maximum:
        raise ValueError("target range size must be within the hard maximum")
    if overlap_pages not in {0, 1}:
        raise ValueError("the maintained fallback supports zero or one overlap page")
    page_count = prepared.source.source_page_count
    cores = tuple(
        PageInterval(start=start, end=min(start + target_range_size - 1, page_count))
        for start in range(1, page_count + 1, target_range_size)
    )
    definitions = tuple(_definition(core, cores, page_count, overlap_pages) for core in cores)
    return _build_plan(
        prepared,
        code,
        definitions,
        target_range_size=target_range_size,
        hard_maximum=hard_maximum,
        overlap_pages=overlap_pages,
    )


def build_content_adaptive_plan(
    prepared: PreparedContentParsing,
    code: RuntimeCodeIdentity,
    *,
    target_range_size: int = 225,
    hard_maximum: int = 275,
    overlap_pages: int = 1,
    max_native_content_units_per_range: int = 500_000,
) -> RangePlan:
    """Build ranges from cheap native-PDF content complexity before Docling runs.

    The content units are a deterministic upper-bound proxy for retained page
    state: the larger of native text rectangles and one quarter of non-space
    characters.  Normal pages remain bounded by ``target_range_size``; dense
    pages close a range when the content budget would be exceeded.
    """
    if max_native_content_units_per_range <= 0:
        raise ValueError("native content budget must be positive")
    profile = NativeContentProfile.from_page_features(
        all_page_features(prepared.source.source_path),
        expected_page_count=prepared.source.source_page_count,
    )
    units = profile.content_units
    cores = _content_adaptive_cores(
        units,
        target_range_size=target_range_size,
        hard_maximum=hard_maximum,
        max_native_content_units_per_range=max_native_content_units_per_range,
    )
    definitions = tuple(
        _definition(core, cores, prepared.source.source_page_count, overlap_pages) for core in cores
    )
    profile_sha256 = canonical_json_sha256(
        {
            "source_id": prepared.source.source_id,
            "features": profile.identity_records(),
        }
    )
    return _build_plan(
        prepared,
        code,
        definitions,
        target_range_size=target_range_size,
        hard_maximum=hard_maximum,
        overlap_pages=overlap_pages,
        planner_mode="content_adaptive",
        max_native_content_units_per_range=max_native_content_units_per_range,
        content_profile_sha256=profile_sha256,
    )


def _content_adaptive_cores(
    units: tuple[int, ...],
    *,
    target_range_size: int,
    hard_maximum: int,
    max_native_content_units_per_range: int,
) -> tuple[PageInterval, ...]:
    """Greedily partition pages without exceeding page or content bounds."""
    if not 1 <= target_range_size <= hard_maximum:
        raise ValueError("target range size must be within the hard maximum")
    cores: list[PageInterval] = []
    start = 1
    current_units = 0
    for page_number, page_units in enumerate(units, start=1):
        current_length = page_number - start
        budget_exceeded = (
            current_length > 0 and current_units + page_units > max_native_content_units_per_range
        )
        page_cap_reached = current_length >= target_range_size
        hard_cap_reached = current_length >= hard_maximum
        if budget_exceeded or page_cap_reached or hard_cap_reached:
            cores.append(PageInterval(start=start, end=page_number - 1))
            start = page_number
            current_units = 0
        current_units += page_units
    if start <= len(units):
        cores.append(PageInterval(start=start, end=len(units)))
    return tuple(cores)


def _build_plan(
    prepared: PreparedContentParsing,
    code: RuntimeCodeIdentity,
    definitions: tuple[RangeDefinition, ...],
    *,
    target_range_size: int,
    hard_maximum: int,
    overlap_pages: int,
    planner_mode: Literal["fixed_size", "content_adaptive"] = "fixed_size",
    max_native_content_units_per_range: int | None = None,
    content_profile_sha256: str | None = None,
) -> RangePlan:
    """Bind one canonical range partition to verified source and runtime identities."""
    page_count = prepared.source.source_page_count
    conversion = prepared.conversion_identity.payload
    return build_range_plan(
        RangePlanInputs(
            source=SourceIdentity(
                source_id=prepared.source.source_id,
                sha256=prepared.source.source_sha256,
                byte_size=prepared.source.source_byte_size,
                physical_page_count=page_count,
            ),
            sealed_source_release_identity=canonical_json_sha256(conversion["sealed_release"]),
            converter_identity=prepared.conversion_identity.run_id,
            package_identity=canonical_json_sha256(conversion["package_versions"]),
            model_identity=canonical_json_sha256(conversion["model_inventory"]),
            adapter_identity=code.page_evidence,
            page_evidence_contract_identity=f"compact_typed_page_evidence:{code.page_evidence}",
            range_conversion_identity=code.range_conversion,
            range_planner_identity=code.planning,
            aggregate_merge_identity=code.aggregate,
            target_range_size=target_range_size,
            hard_maximum=hard_maximum,
            planner_mode=planner_mode,
            max_native_content_units_per_range=max_native_content_units_per_range,
            content_profile_sha256=content_profile_sha256,
            overlap_policy=OverlapPolicy(
                max_left_pages=overlap_pages,
                max_right_pages=overlap_pages,
            ),
            ranges=definitions,
            aggregate_output_schema_identity="docling_conversion_bundle.v1",
            global_interpretation_policy_identity="docling_reading_order_heading_once.v1",
        )
    )


def _definition(
    core: PageInterval,
    cores: tuple[PageInterval, ...],
    page_count: int,
    overlap_pages: int,
) -> RangeDefinition:
    read = PageInterval(
        start=max(1, core.start - overlap_pages),
        end=min(page_count, core.end + overlap_pages),
    )
    owners = tuple(
        OverlapOwner(page=page, owner_core=next(item for item in cores if item.contains(page)))
        for page in read.pages
        if not core.contains(page)
    )
    return RangeDefinition(core=core, read=read, overlap_owners=owners)


__all__ = [
    "NativeContentPage",
    "NativeContentProfile",
    "build_content_adaptive_plan",
    "build_fixed_size_plan",
]
