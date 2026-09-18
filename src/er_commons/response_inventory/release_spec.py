"""Strict, source-free Task 05H requests and cycle-free plan identities."""

from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import canonical_json_sha256

VERSION = "er_commons.response_inventory_release_request.v1"
SCHEMA_ROOT = "benchmarks/er_bench/schemas/response_inventory/release_v1/"
SCHEMA_PATH = SCHEMA_ROOT + "run_spec.schema.json"
PACKAGE = "src/er_commons/response_inventory/"
SELECTION_POLICY = "task05h_curator_selection.v1"
QUESTION_VERSION = "task05h_composition_review.v1"
VIEW_POLICY = "task05h_lazy_text_view.v1"


class StrictRecord(BaseModel):
    """Reject unknown fields and coercion at the new release boundary."""

    model_config = ConfigDict(extra="forbid", strict=True)


def relative_path(value: str) -> Path:
    """Require canonical portable relative paths, without traversal or aliases."""
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or path == Path(".")
        or "\\" in value
        or path.as_posix() != value
    ):
        raise ValueError(f"not a contained canonical relative path: {value!r}")
    return path


def contained_path(root: Path, value: str) -> Path:
    """Reject symlink escape before any declared file access."""
    path = (root / relative_path(value)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {value}")
    return path


class FileBinding(StrictRecord):
    """A relative repository file with an exact byte digest."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> FileBinding:
        """Validate paths before reading or deriving plan identities."""
        relative_path(self.path)
        return self


class EvidenceBinding(FileBinding):
    """Explicit authority for mutable review inputs kept outside plan identity."""

    authority: Literal["repository", "artifact_root"]


class ReleaseLimits(StrictRecord):
    """Freeze the approved 05G-sized ceilings for all new 05H output."""

    workers: Literal[1] = 1
    cpu_threads: Literal[2] = 2
    max_seconds: Literal[1800] = 1800
    max_rss_bytes: Literal[4294967296] = 4294967296
    max_output_bytes: Literal[2147483648] = 2147483648
    min_free_bytes: Literal[8589934592] = 8589934592
    max_swap_growth_bytes: Literal[0] = 0
    sample_seconds: float = Field(default=0.1, ge=0.1, le=0.1)
    disk_sample_seconds: float = Field(default=1.0, ge=1.0, le=1.0)
    termination_grace_seconds: float = Field(default=15.0, ge=15.0, le=15.0)

    @model_validator(mode="before")
    @classmethod
    def strict_integer_limits(cls, value: Any) -> Any:
        """Do not let Python boolean/integer equality bypass fixed limits."""
        if isinstance(value, dict):
            names = {
                "workers",
                "cpu_threads",
                "max_seconds",
                "max_rss_bytes",
                "max_output_bytes",
                "min_free_bytes",
                "max_swap_growth_bytes",
            }
            if any(type(value[name]) is not int for name in names & value.keys()):
                raise ValueError("resource limits require JSON integers")
        return value


class ReleaseAuthorization(StrictRecord):
    """Execution, finalization, publication and acceptance are independent gates."""

    execution: bool
    finalization: bool
    publication: bool
    acceptance: bool


class RuntimeVersions(StrictRecord):
    """Pin only the installed runtime dependencies used by release and supervision."""

    python: str = Field(min_length=1)
    pydantic: str = Field(min_length=1)
    jsonschema: str = Field(min_length=1)
    rfc8785: str = Field(min_length=1)
    psutil: str = Field(min_length=1)


def current_runtime_versions() -> dict[str, str]:
    """Read the current local runtime without imports, installs, or network access."""
    return {
        "python": platform.python_version(),
        **{
            package: version(package) for package in ("pydantic", "jsonschema", "rfc8785", "psutil")
        },
    }


def verify_runtime_versions(expected: dict[str, str]) -> None:
    """Stop reuse if any frozen interpreter or dependency version has changed."""
    actual = current_runtime_versions()
    if expected != actual:
        changed = sorted(
            key for key in set(expected) | set(actual) if expected.get(key) != actual.get(key)
        )
        raise ValueError(f"05H runtime versions differ: {', '.join(changed)}")


class ReleaseSpec(StrictRecord):
    """An explicit 05H composition request, never an upstream workflow request."""

    schema_version: Literal["er_commons.response_inventory_release_request.v1"]
    task_stage: Literal["05h"]
    binding_freeze: FileBinding
    selection_freeze: FileBinding
    selection_policy: Literal["task05h_curator_selection.v1"]
    question_version: Literal["task05h_composition_review.v1"]
    view_policy: Literal["task05h_lazy_text_view.v1"]
    repository_bindings: list[FileBinding]
    runtime_versions: RuntimeVersions
    output_relative_root: Literal[
        "pipelines/brisbane_baylands/task_05_response_inventory/working/05h"
    ]
    limits: ReleaseLimits
    authorization: ReleaseAuthorization
    source_pdf_access: Literal[False]
    image_access: Literal[False]
    render_access: Literal[False]
    model_access: Literal[False]
    network_access: Literal[False]
    hash_large_upstream_payloads: Literal[False]
    review_decisions: EvidenceBinding | None = None
    quality_report: EvidenceBinding | None = None

    @model_validator(mode="before")
    @classmethod
    def strict_access_controls(cls, value: Any) -> Any:
        """Access controls must be explicit JSON false, never numeric aliases."""
        if isinstance(value, dict):
            names = {
                "source_pdf_access",
                "image_access",
                "render_access",
                "model_access",
                "network_access",
                "hash_large_upstream_payloads",
            }
            if any(value[name] is not False for name in names & value.keys()):
                raise ValueError("source-free access controls require JSON false")
        return value

    @model_validator(mode="after")
    def distinct_bindings(self) -> ReleaseSpec:
        """Reject duplicates and identity cycles before checking repository bytes."""
        paths = [item.path for item in self.repository_bindings]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate repository binding")
        mutable_paths = {self.selection_freeze.path}
        mutable_paths.update(
            item.path
            for item in (self.review_decisions, self.quality_report)
            if item is not None and item.authority == "repository"
        )
        if mutable_paths & set(paths):
            raise ValueError("mutable selection/review inputs cannot be repository owner bindings")
        return self


def required_repository_paths(repository_root: Path | None = None) -> set[str]:
    """Enumerate explicit output-affecting owners, never discover by broad glob."""
    del repository_root
    return {
        PACKAGE + name + ".py"
        for name in (
            "release_spec",
            "release_inputs",
            "release_validation",
            "release_review",
            "release_views",
            "release_storage",
            "release_publication",
            "release_workflow",
            "release_launch",
            "release_execution",
            "cli",
            "__init__",
            "observations",
            "producer",
            "run_spec",
            "code_inventory",
            "contract",
            "complete_source_policy",
            "pilot_policy",
            "source_structure",
        )
    } | {
        "src/er_commons/artifact_io.py",
        "src/er_commons/document_publication/background_execution.py",
        "scripts/prepare_task05h_execution.py",
        "pyproject.toml",
        "uv.lock",
        "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json",
        SCHEMA_PATH,
        SCHEMA_ROOT + "records.schema.json",
    }


def verify_file_binding(binding: dict[str, Any], root: Path) -> Path:
    """Check one exact byte binding under its explicitly chosen authority."""
    path = contained_path(root, binding["path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["sha256"]:
        raise ValueError(f"file digest mismatch: {binding['path']}")
    return path


def verify_repository_bindings(spec: dict[str, Any], repository_root: Path) -> None:
    """Require the exact finite owner inventory plus the accepted dependency freeze."""
    model = ReleaseSpec.model_validate(spec)
    verify_runtime_versions(model.runtime_versions.model_dump())
    expected = required_repository_paths(repository_root) | {model.binding_freeze.path}
    if {item.path for item in model.repository_bindings} != expected:
        raise ValueError("repository binding inventory differs from current owned files")
    for binding in model.repository_bindings:
        verify_file_binding(binding.model_dump(), repository_root)
    verify_file_binding(model.binding_freeze.model_dump(), repository_root)
    verify_file_binding(model.selection_freeze.model_dump(), repository_root)


def plan_identity(spec: dict[str, Any]) -> str:
    """Bind immutable behavior; exclude later decisions and operational approvals."""
    normalized = ReleaseSpec.model_validate(spec).model_dump(mode="json", exclude_none=True)
    excluded = {"authorization", "selection_freeze", "review_decisions", "quality_report"}
    preimage = {key: value for key, value in normalized.items() if key not in excluded}
    preimage["repository_bindings"] = sorted(
        preimage["repository_bindings"], key=lambda item: item["path"]
    )
    return canonical_json_sha256(preimage)


def load_release_spec(path: Path, repository_root: Path) -> tuple[dict[str, Any], str]:
    """Validate repository-only bindings without reading production artifacts."""
    model = ReleaseSpec.model_validate_json(path.read_bytes())
    spec = model.model_dump(mode="json", exclude_none=True)
    verify_repository_bindings(spec, repository_root)
    return spec, plan_identity(spec)


def is_release_spec(path: Path) -> bool:
    """Dispatch only the explicitly versioned 05H request."""
    payload = json.loads(path.read_text())
    return isinstance(payload, dict) and payload.get("schema_version") == VERSION
