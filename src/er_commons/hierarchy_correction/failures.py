"""Explicit lifecycle stages and durable failure dispositions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from er_commons.hierarchy_correction.constants import FATAL_CODES


class RunStage(StrEnum):
    """Human-readable application stages that can leave attempt evidence."""

    FRESH_BUILDS = "fresh_builds"
    PRESERVATION = "preservation"
    CANDIDATE_ASSEMBLY = "candidate_assembly"
    QUALITY_GATE = "quality"
    PUBLICATION = "publication"


_DEFAULT_CODE_BY_STAGE = {
    RunStage.FRESH_BUILDS: "UNKNOWN_REFERENCE",
    RunStage.PRESERVATION: "INPUT_INVENTORY_MISMATCH",
    RunStage.CANDIDATE_ASSEMBLY: "UNKNOWN_REFERENCE",
    RunStage.QUALITY_GATE: "UNKNOWN_REFERENCE",
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


class QualityGateRejected(CorrectionFailure):
    """Terminal quality rejection distinguished from gate infrastructure errors."""

    def __init__(self, rejected_reports: tuple[str, ...]) -> None:
        if not rejected_reports:
            raise ValueError("quality rejection must name at least one report")
        self.rejected_reports = rejected_reports
        super().__init__(
            FailureDisposition(
                RunStage.QUALITY_GATE,
                "QUALITY_GATE_REJECTED",
                f"reports={','.join(rejected_reports)}",
            )
        )
        self.args = (f"quality gate rejected reports: {', '.join(rejected_reports)}",)


def explicit_failure(stage: RunStage, fatal_code: str, detail: str) -> CorrectionFailure:
    """Construct a typed failure at the operation that knows its disposition."""
    return CorrectionFailure(FailureDisposition(stage, fatal_code, detail))


def disposition_for(error: Exception, stage: RunStage) -> FailureDisposition:
    """Select attempt evidence from operation context, never exception wording."""
    if isinstance(error, CorrectionFailure):
        return error.disposition
    detail = str(error) or type(error).__name__
    return FailureDisposition(stage, _DEFAULT_CODE_BY_STAGE[stage], detail)
