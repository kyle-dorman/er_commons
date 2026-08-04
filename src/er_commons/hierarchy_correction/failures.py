"""Explicit lifecycle stages and durable failure dispositions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from er_commons.hierarchy_correction.constants import FATAL_CODES


class RunStage(StrEnum):
    """Human-readable application stages that can leave attempt evidence."""

    BUILD = "build"
    CANDIDATE_ASSEMBLY = "candidate_assembly"
    AUTHORIZATION = "authorization"
    PUBLICATION = "publication"


_DEFAULT_CODE_BY_STAGE = {
    RunStage.BUILD: "UNKNOWN_REFERENCE",
    RunStage.CANDIDATE_ASSEMBLY: "UNKNOWN_REFERENCE",
    RunStage.AUTHORIZATION: "UNKNOWN_REFERENCE",
    RunStage.PUBLICATION: "PUBLICATION_COLLISION",
}


@dataclass(frozen=True)
class FailureDisposition:
    """Schema-compatible fatal code plus a stage-qualified human detail."""

    stage: RunStage
    fatal_code: str
    detail: str

    def __post_init__(self) -> None:
        if self.fatal_code not in FATAL_CODES:
            raise ValueError(f"unknown hierarchy-correction fatal code: {self.fatal_code}")
        if not self.detail:
            raise ValueError("failure detail must not be empty")

    @property
    def persisted_detail(self) -> str:
        """Include the failed stage without changing the frozen attempt schema."""
        return f"{self.stage.value}: {self.detail}"


class CorrectionFailure(ValueError):
    """A failure whose durable code is selected where the operation is known."""

    def __init__(self, disposition: FailureDisposition) -> None:
        self.disposition = disposition
        super().__init__(f"{disposition.fatal_code}: {disposition.detail}")

    @property
    def fatal_code(self) -> str:
        """Expose the durable code to callers without unpacking disposition."""
        return self.disposition.fatal_code

    @property
    def stage(self) -> str:
        """Expose the human lifecycle stage as its persisted string value."""
        return self.disposition.stage.value


def explicit_failure(stage: RunStage, fatal_code: str, detail: str) -> CorrectionFailure:
    """Construct a typed failure at the operation that knows its disposition."""
    return CorrectionFailure(FailureDisposition(stage, fatal_code, detail))


def disposition_for(error: Exception, stage: RunStage) -> FailureDisposition:
    """Select attempt evidence from operation context, never exception wording."""
    if isinstance(error, CorrectionFailure):
        return error.disposition
    detail = str(error) or type(error).__name__
    return FailureDisposition(stage, _DEFAULT_CODE_BY_STAGE[stage], detail)
