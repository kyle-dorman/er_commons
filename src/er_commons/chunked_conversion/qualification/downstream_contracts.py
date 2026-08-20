"""Typed identities, paths, and CLI records for Gate C downstream qualification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ID = "deir_appendix_g1"
GATE_C_RUN_ID = "gatec1-53d220f716dbb5a9ae1ec031b9ef86c2c14884c0744beee7227708504afe1124"
AGGREGATE_ID = "dconv1-08a9a730efde0a5607ea2cc38c4b821e91c435fc0b1520a4cd4c612a44a2a25b"
ACCEPTED_PRODUCER_ID = "prv1-159379eb52f63824b22b9ae529044c5c983aa5ef80abcf874502fe6c9e3c1b74"
QUALIFICATION_PRODUCER_ID = "prv1-44774afd5475af0f5a4415a5a6e8e76dd32b9e2c0f3a53fe39e1053535a38bb8"
ACCEPTED_DOCUMENT_ID = "docv1-54e6036f6c7caffc3d2a10fff0239f751b9af91ef9de3ee755e48f7873c9fdef"
QUALIFICATION_DOCUMENT_ID = "docv1-b62932c4076202e1c950847e36625dd2a163f5a71bd0136b4ef246bcc03b78b6"
ACCEPTED_STAGE_IDS = {
    "mapped_records": "exv1-7b4aa0b6d190d32b40687c4bf90fc0b7b4d6c4fd766a2502caf7d5afb05fd288",
    "hierarchy_decisions": (
        "hcorv1-69f06ba65275c80278e254fc4d9d16485ad6988beaff6af7ec92f8f13bfc949c"
    ),
    "structured_document": (
        "exv1-f217696174ba93eee73cd1ac451af78f41fb12ad8268403db1fee9807c7e5db6"
    ),
    "linked_document": "exv1-5d92614d33fb83997f46eef73462e1501e748ef877e4dcfd47a7bf615d941af3",
}
QUALIFICATION_STAGE_IDS = {
    "mapped_records": "exv1-820e3f043c15ff0f47c9a05b64f6241d4cb8feb317054a29e41fe43864d5698d",
    "hierarchy_decisions": (
        "hcorv1-33ddb8e965710a3837039e9e04e62a958d2cd77a32f7c7feed09bb9390caaffe"
    ),
    "structured_document": (
        "exv1-ac49f82f161e6043a99314d20bf359d7c0cb1417d972c875b1793bea7ed79bee"
    ),
    "linked_document": "exv1-86bce06b5f810355d6af0b50c584d9270d3903b6a996cf6ceb90e7e466f7a563",
}
GATE_C_RELATIVE_ROOT = Path(
    "pipelines/brisbane_baylands/task_03h2_chunked_docling_conversion/gate_c"
)


class DownstreamStage(StrEnum):
    """Public resumable stages exposed by the qualification CLI."""

    PRODUCER = "producer"
    RECORDS = "records"
    PUBLICATION = "publication"
    REPORT = "report"


class StrictRecord(BaseModel):
    """Reject coercion and undeclared fields at qualification boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class DownstreamRequest(StrictRecord):
    """Validated request passed from the CLI to the application shell."""

    data_root: Path
    stage: DownstreamStage = DownstreamStage.PRODUCER

    @field_validator("data_root")
    @classmethod
    def require_absolute_root(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("downstream data root must be absolute")
        return value


class DownstreamCompletion(StrictRecord):
    """Exact terminal record required before reusing a downstream report."""

    schema_version: Literal["er_commons.task03h2_gate_c_downstream_completion.v1"]
    status: Literal["complete"]
    gate_c_run_id: str = Field(pattern=r"^gatec1-[0-9a-f]{64}$")
    aggregate_conversion_id: str = Field(pattern=r"^dconv1-[0-9a-f]{64}$")
    report: str
    artifact_inventory: Literal["records/artifact_inventory.json"]
    artifact_inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    completion_last: Literal[True]


class DownstreamProgress(StrictRecord):
    """Machine-readable CLI result for one requested stage."""

    schema_version: Literal["er_commons.task03h2_gate_c_downstream_progress.v1"] = (
        "er_commons.task03h2_gate_c_downstream_progress.v1"
    )
    gate_c_run_id: str = GATE_C_RUN_ID
    stage: DownstreamStage
    result: object
    wall_seconds: float = Field(ge=0)


@dataclass(frozen=True)
class DownstreamPaths:
    """All checked-in and artifact paths owned by downstream qualification."""

    data_root: Path
    project_root: Path = PROJECT_ROOT

    @property
    def gate_c_run(self) -> Path:
        return self.data_root / GATE_C_RELATIVE_ROOT / "runs" / GATE_C_RUN_ID

    @property
    def aggregate(self) -> Path:
        return self.gate_c_run / "aggregate" / AGGREGATE_ID

    @property
    def downstream(self) -> Path:
        return self.data_root / GATE_C_RELATIVE_ROOT / "downstream" / GATE_C_RUN_ID

    @property
    def accepted_task(self) -> Path:
        return self.data_root / "pipelines/brisbane_baylands/task_03h_clean_full_v1"

    @property
    def template_root(self) -> Path:
        return self.project_root / "tmp/task03h2_gate_c_downstream" / GATE_C_RUN_ID / "v3"

    def config(self, name: str) -> Path:
        """Resolve one checked-in Task 03H process configuration."""
        if name == "document_spec":
            return (
                self.project_root / "configs/brisbane_baylands_2025_deir_task03h_document_v2.json"
            )
        return self.project_root / f"configs/task03h/{SOURCE_ID}/{name}.json"


def completion_result(paths: dict[str, Path], data_root: Path) -> dict[str, str]:
    """Render stage completions relative to the explicit artifact root."""
    return {role: path.relative_to(data_root).as_posix() for role, path in paths.items()}


JsonObject = dict[str, Any]

__all__ = [
    "ACCEPTED_DOCUMENT_ID",
    "ACCEPTED_PRODUCER_ID",
    "ACCEPTED_STAGE_IDS",
    "AGGREGATE_ID",
    "DownstreamCompletion",
    "DownstreamPaths",
    "DownstreamProgress",
    "DownstreamRequest",
    "DownstreamStage",
    "GATE_C_RUN_ID",
    "JsonObject",
    "PROJECT_ROOT",
    "QUALIFICATION_DOCUMENT_ID",
    "QUALIFICATION_PRODUCER_ID",
    "QUALIFICATION_STAGE_IDS",
    "SOURCE_ID",
    "completion_result",
]
