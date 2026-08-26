"""Compact exact-object evidence retained independently of rendered Task 04 pages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from er_commons.human_review_support.task04.models import JsonValue, ReviewCard, ReviewQueue


class CanonicalObjectKind(StrEnum):
    """Canonical object categories that a human finding may select."""

    BLOCK = "canonical_block"
    TABLE = "canonical_table"


class ObservationKind(StrEnum):
    """Retained non-canonical observations that a finding may select."""

    WARNING = "warning_observation"
    FAILURE = "failure_observation"


@dataclass(frozen=True)
class ExactCanonicalObject:
    """One canonical identifier and geometry retained for later finding edits."""

    kind: CanonicalObjectKind
    object_id: str
    physical_page: int
    bbox: tuple[float, float, float, float] | None
    table_family_id: str | None = None

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize without retaining text, cells, or disposable render paths."""
        return {
            "kind": self.kind.value,
            "object_id": self.object_id,
            "physical_page": self.physical_page,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "coordinate_space": "displayed_page",
            "table_family_id": self.table_family_id,
        }


@dataclass(frozen=True)
class ExactObservation:
    """One stable warning or failed-attempt observation identifier."""

    kind: ObservationKind
    observation_id: str

    def to_record(self) -> dict[str, JsonValue]:
        """Serialize the discriminated observation reference."""
        return {"kind": self.kind.value, "observation_id": self.observation_id}


def retained_exact_evidence(card: ReviewCard) -> dict[str, JsonValue]:
    """Project a review card into small durable IDs and exact source geometry."""
    objects = _canonical_objects(card)
    observations = _observations(card)
    return {
        "canonical_objects": [item.to_record() for item in objects],
        "observations": [item.to_record() for item in observations],
    }


def _canonical_objects(card: ReviewCard) -> tuple[ExactCanonicalObject, ...]:
    objects: dict[tuple[str, str, int, str], ExactCanonicalObject] = {}
    for rendered in card.rendered_pages:
        page = rendered.evidence
        for block in page.blocks:
            item = ExactCanonicalObject(
                CanonicalObjectKind.BLOCK,
                block.identifier,
                page.physical_page,
                block.bbox,
            )
            objects[_object_key(item)] = item
        for table in page.tables:
            item = ExactCanonicalObject(
                CanonicalObjectKind.TABLE,
                table.identifier,
                page.physical_page,
                table.bbox,
                table.table_family_id,
            )
            objects[_object_key(item)] = item
    return tuple(objects[key] for key in sorted(objects))


def _object_key(item: ExactCanonicalObject) -> tuple[str, str, int, str]:
    """Deduplicate identical regions without collapsing multi-region objects."""
    return (item.kind.value, item.object_id, item.physical_page, repr(item.bbox))


def _observations(card: ReviewCard) -> tuple[ExactObservation, ...]:
    item = card.item
    observations: list[ExactObservation] = []
    if item.queue is ReviewQueue.WARNING and item.warning is not None:
        evidence_id = item.warning.warning_class.representative.evidence_id
        if evidence_id:
            observations.append(ExactObservation(ObservationKind.WARNING, evidence_id))
    if item.queue is ReviewQueue.FAILURE and item.failure is not None:
        observations.extend(
            ExactObservation(ObservationKind.FAILURE, attempt.attempt_id)
            for attempt in item.failure.attempts
        )
    return tuple(sorted(observations, key=lambda value: (value.kind.value, value.observation_id)))


__all__ = [
    "CanonicalObjectKind",
    "ExactCanonicalObject",
    "ExactObservation",
    "ObservationKind",
    "retained_exact_evidence",
]
