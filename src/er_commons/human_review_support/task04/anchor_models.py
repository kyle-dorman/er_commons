"""Immutable typed records used by the Task 04 finding-anchor workflow."""

from __future__ import annotations

from dataclasses import dataclass

from er_commons.human_review_support.task04.models import JsonValue


@dataclass(frozen=True)
class SourceAnchor:
    """Verified source and optional publication-terminal identity."""

    source_id: str
    catalog_sha256: str
    source_pdf_sha256: str | None
    candidate_id: str | None
    candidate_completion_sha256: str | None
    candidate_inventory_sha256: str | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize exact source and candidate terminal checksums."""
        candidate: dict[str, JsonValue] | None = None
        if self.candidate_id is not None:
            candidate = {
                "candidate_id": self.candidate_id,
                "completion_sha256": self.candidate_completion_sha256,
                "inventory_sha256": self.candidate_inventory_sha256,
            }
        return {
            "source": {
                "source_id": self.source_id,
                "catalog_sha256": self.catalog_sha256,
                "source_pdf_sha256": self.source_pdf_sha256,
            },
            "candidate": candidate,
        }


@dataclass(frozen=True)
class PageAnchor:
    """One selected physical page bound to source and candidate terminals."""

    binding: SourceAnchor
    physical_page: int

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated page anchor."""
        return {"kind": "page", **self.binding.to_record(), "physical_page": self.physical_page}


@dataclass(frozen=True)
class TableFamilyAnchor:
    """One selected table family and its exact sampled physical pages."""

    binding: SourceAnchor
    table_family_id: str
    physical_pages: tuple[int, ...]

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated table-family anchor."""
        return {
            "kind": "table_family",
            **self.binding.to_record(),
            "table_family_id": self.table_family_id,
            "physical_pages": list(self.physical_pages),
        }


@dataclass(frozen=True)
class WarningAnchor:
    """One normalized warning class and optional selected context page."""

    binding: SourceAnchor
    warning_fingerprint: str
    physical_page: int | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated warning anchor."""
        return {
            "kind": "warning",
            **self.binding.to_record(),
            "warning_fingerprint": self.warning_fingerprint,
            "physical_page": self.physical_page,
        }


@dataclass(frozen=True)
class FailureAnchor:
    """One source-level failure history and its retained attempt identities."""

    binding: SourceAnchor
    attempt_ids: tuple[str, ...]

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated failure anchor."""
        return {
            "kind": "failure",
            **self.binding.to_record(),
            "attempt_ids": list(self.attempt_ids),
        }


@dataclass(frozen=True)
class CanonicalTableAnchor:
    """One retained canonical table in displayed-page coordinates."""

    binding: SourceAnchor
    table_id: str
    physical_page: int
    bbox: tuple[float, float, float, float] | None
    table_family_id: str | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated canonical-table anchor."""
        return {
            "kind": "canonical_table",
            **self.binding.to_record(),
            "table_id": self.table_id,
            "physical_page": self.physical_page,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "coordinate_space": "displayed_page",
            "table_family_id": self.table_family_id,
        }


@dataclass(frozen=True)
class CanonicalBlockAnchor:
    """One retained canonical block in displayed-page coordinates."""

    binding: SourceAnchor
    block_id: str
    physical_page: int
    bbox: tuple[float, float, float, float] | None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated canonical-block anchor."""
        return {
            "kind": "canonical_block",
            **self.binding.to_record(),
            "block_id": self.block_id,
            "physical_page": self.physical_page,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "coordinate_space": "displayed_page",
        }


@dataclass(frozen=True)
class ObservationAnchor:
    """One exact retained warning or failed-attempt observation."""

    binding: SourceAnchor
    observation_kind: str
    observation_id: str

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize a discriminated observation anchor."""
        return {
            "kind": "observation",
            **self.binding.to_record(),
            "observation_kind": self.observation_kind,
            "observation_id": self.observation_id,
        }


@dataclass(frozen=True)
class FindingSelectors:
    """Optional human-selected exact IDs that must resolve to retained evidence."""

    table_ids: tuple[str, ...] = ()
    block_ids: tuple[str, ...] = ()
    observation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for label, values in (
            ("table", self.table_ids),
            ("block", self.block_ids),
            ("observation", self.observation_ids),
        ):
            if any(not value.strip() for value in values):
                raise ValueError(f"{label} selectors must be non-empty IDs")

    def normalized(self) -> FindingSelectors:
        """Strip, deduplicate, and sort selectors before resolution."""
        return FindingSelectors(
            table_ids=tuple(sorted({value.strip() for value in self.table_ids})),
            block_ids=tuple(sorted({value.strip() for value in self.block_ids})),
            observation_ids=tuple(sorted({value.strip() for value in self.observation_ids})),
        )


type FindingAnchor = (
    PageAnchor
    | TableFamilyAnchor
    | WarningAnchor
    | FailureAnchor
    | CanonicalTableAnchor
    | CanonicalBlockAnchor
    | ObservationAnchor
)


__all__ = [
    "CanonicalBlockAnchor",
    "CanonicalTableAnchor",
    "FailureAnchor",
    "FindingAnchor",
    "FindingSelectors",
    "ObservationAnchor",
    "PageAnchor",
    "SourceAnchor",
    "TableFamilyAnchor",
    "WarningAnchor",
]
