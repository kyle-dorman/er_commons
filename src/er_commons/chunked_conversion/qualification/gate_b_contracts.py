"""Typed contracts and accepted constants for the Gate B qualification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from er_commons.chunked_conversion.range_contract import PageInterval

CONVERSION_ID = "dconv1-97a8d4048839d9ba26c78151d0446e1c1bbef9848183f1ce9b9140c92e4c3f68"
SOURCE_ID = "deir_appendix_g1"
SOURCE_SHA256 = "e11835a7c6346c6780bfe26bee0037f4b6206b0a1573b3d480cb2b4170e79f7f"
SOURCE_PAGE_COUNT = 2488
THREAD_COUNT = 4
DEFAULT_SOURCE_ROOT = Path(
    "/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/"
    "task_03h_clean_full_v1/document_parse_evidence/docling_conversions/" + CONVERSION_ID
)
DEFAULT_CONFIG = Path("configs/task03h/deir_appendix_g1/content_parsing.json")
DOCUMENT_COLLECTIONS = (
    "texts",
    "pictures",
    "tables",
    "key_value_items",
    "form_items",
    "groups",
)


class GateBContractError(ValueError):
    """A typed Gate B request or persisted record violates its contract."""

    def __init__(self, code: str, path: str, detail: str) -> None:
        self.code = code
        self.path = path
        self.detail = detail
        super().__init__(f"code={code} path={path} detail={detail}")


class Seam(BaseModel):
    """One four-page window split into adjacent two-page cores."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seam_id: str = Field(min_length=1)
    seam_class: str = Field(min_length=1)
    window: PageInterval
    left_core: PageInterval
    left_read: PageInterval
    right_core: PageInterval
    right_read: PageInterval

    @property
    def comparison_pages(self) -> tuple[int, int]:
        """Return the two pages touching the proposed cut."""
        return (self.left_core.end, self.right_core.start)

    @model_validator(mode="after")
    def validate_topology(self) -> Self:
        """Require adjacent cores and read windows contained by the control window."""
        if self.left_core.end + 1 != self.right_core.start:
            raise ValueError("left and right cores must be adjacent")
        for name, interval in (
            ("left_core", self.left_core),
            ("left_read", self.left_read),
            ("right_core", self.right_core),
            ("right_read", self.right_read),
        ):
            if interval.start < self.window.start or interval.end > self.window.end:
                raise ValueError(f"{name} must be contained by window")
        if (
            self.left_read.start > self.left_core.start
            or self.left_read.end < self.left_core.end
            or self.right_read.start > self.right_core.start
            or self.right_read.end < self.right_core.end
        ):
            raise ValueError("each read interval must contain its core")
        return self


SEAMS = (
    Seam(
        seam_id="p0086_p0087_calibration",
        seam_class="ordinary_prose_calibration",
        window=PageInterval(start=85, end=88),
        left_core=PageInterval(start=85, end=86),
        left_read=PageInterval(start=85, end=87),
        right_core=PageInterval(start=87, end=88),
        right_read=PageInterval(start=86, end=88),
    ),
    Seam(
        seam_id="p0013_p0014_cross_page",
        seam_class="cross_page_prose_heading_furniture_caption",
        window=PageInterval(start=12, end=15),
        left_core=PageInterval(start=12, end=13),
        left_read=PageInterval(start=12, end=14),
        right_core=PageInterval(start=14, end=15),
        right_read=PageInterval(start=13, end=15),
    ),
    Seam(
        seam_id="p0422_p0423_table_run",
        seam_class="long_table_run_consecutive_tables_figures",
        window=PageInterval(start=421, end=424),
        left_core=PageInterval(start=421, end=422),
        left_read=PageInterval(start=421, end=423),
        right_core=PageInterval(start=423, end=424),
        right_read=PageInterval(start=422, end=424),
    ),
    Seam(
        seam_id="p1405_p1406_footnote",
        seam_class="positive_footnote_figure",
        window=PageInterval(start=1404, end=1407),
        left_core=PageInterval(start=1404, end=1405),
        left_read=PageInterval(start=1404, end=1406),
        right_core=PageInterval(start=1406, end=1407),
        right_read=PageInterval(start=1405, end=1407),
    ),
)


@dataclass(frozen=True)
class GateBRunRequest:
    """Resolved coordinator inputs supplied by the CLI shell."""

    source_root: Path
    config_path: Path
    data_root: Path
    output_root: Path
    max_rss_bytes: int
    max_wall_seconds: float

    def __post_init__(self) -> None:
        if self.max_rss_bytes <= 0 or self.max_wall_seconds <= 0:
            raise GateBContractError(
                "invalid_resource_limit", "request.resource_limits", "limits must be positive"
            )


class GateBWorkerSpec(BaseModel):
    """Strict persisted input for one isolated seam worker."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_root: Path
    config_path: Path
    data_root: Path
    seam_root: Path
    sealed_trace_path: Path
    seam: Seam
    max_rss_bytes: int = Field(gt=0)

    @field_validator(
        "source_root",
        "config_path",
        "data_root",
        "seam_root",
        "sealed_trace_path",
        mode="after",
    )
    @classmethod
    def resolve_paths(cls, value: Path) -> Path:
        """Make worker path meaning independent of its process working directory."""
        return value.resolve()

    @model_validator(mode="after")
    def validate_attempt_ownership(self) -> Self:
        """Keep a seam and its shared trace inside one attempt namespace."""
        if self.seam_root.name != self.seam.seam_id:
            raise ValueError("seam root name must equal seam ID")
        if self.sealed_trace_path.name != "sealed_g1_page_trace.json":
            raise ValueError("sealed trace filename differs")
        if self.seam_root.parents[1] != self.sealed_trace_path.parents[1]:
            raise ValueError("seam root and sealed trace must share one attempt root")
        return self


class GateBSeamCompletion(BaseModel):
    """Completion-last record required before a coordinator reuses a seam."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str
    status: str
    seam_id: str
    artifact_inventory: str
    artifact_inventory_sha256: str
    completion_last: bool

    @model_validator(mode="after")
    def require_complete(self) -> Self:
        """Reject incomplete or foreign terminal records."""
        if self.status != "complete" or not self.completion_last:
            raise ValueError("seam completion is not terminal")
        return self


class GateBRunCompletion(BaseModel):
    """Strict terminal record required before a coordinator reuses a Gate B run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str
    status: str
    run_id: str
    source_conversion_id: str
    artifact_inventory: str
    artifact_inventory_sha256: str
    completion_last: bool
    gate_c_started: bool
    g2_started: bool

    @model_validator(mode="after")
    def require_closed_gate_b(self) -> Self:
        """Require a completed Gate B record that did not cross later boundaries."""
        if (
            self.status != "complete"
            or not self.completion_last
            or self.source_conversion_id != CONVERSION_ID
            or self.gate_c_started
            or self.g2_started
        ):
            raise ValueError("Gate B completion has invalid terminal or scope state")
        return self


def seam_payload(seam: Seam) -> dict[str, Any]:
    """Serialize a seam using the historical Gate B JSON shape."""
    payload = seam.model_dump(mode="json")
    payload["comparison_pages"] = list(seam.comparison_pages)
    return payload


def parse_worker_spec(path: Path) -> GateBWorkerSpec:
    """Read and strictly validate a worker specification with path context."""
    try:
        return GateBWorkerSpec.model_validate_json(path.read_bytes())
    except (OSError, ValueError) as error:
        raise GateBContractError("invalid_worker_spec", path.as_posix(), str(error)) from error
