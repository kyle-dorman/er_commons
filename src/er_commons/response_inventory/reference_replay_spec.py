"""Strict v6 consumer requests, separate from frozen historical writer recipes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.code_inventory import owned_code_paths
from er_commons.response_inventory.run_spec import AcceptedTask05D, AcceptedTask05E

VERSION = "er_commons.response_reference_run_spec.v6"
SCHEMA_PATH = "benchmarks/er_bench/schemas/response_inventory/v6/reference_run_spec.schema.json"
PACKAGE = "src/er_commons/response_inventory/"


class StrictRequest(BaseModel):
    """Reject coercion and unknown controls on the new consumer boundary."""

    model_config = ConfigDict(extra="forbid", strict=True)


class FileBinding(StrictRequest):
    """One contained relative file and its recorded digest."""

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def contained(self) -> FileBinding:
        """Reject absolute paths and traversal before any access."""
        relative_path(self.path)
        return self


class BaselineBinding(StrictRequest):
    """The accepted nonterminal 05F result has a receipt, not a completion."""

    root: str
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inventory_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    rules_id: str = Field(pattern=r"^rulesv1-[0-9a-f]{64}$")


class MechanicalBinding(StrictRequest):
    """Explicit selected mechanical roots; no historical layout inference."""

    readiness_root: str
    readiness_completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    readiness_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    correspondence_root: str
    correspondence_completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    publication_root: str
    catalog: FileBinding
    handoff_completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceGraphReplacement(StrictRequest):
    """Pin the historical pair whose source evidence a replacement must preserve."""

    task05d: AcceptedTask05D
    task05e: AcceptedTask05E


class ReplayInputBindings(StrictRequest):
    """Accepted source, graph, baseline, mechanical and human authorities."""

    task06h_pointer: str
    task05d: AcceptedTask05D
    task05e: AcceptedTask05E
    task05f: BaselineBinding
    task06g: MechanicalBinding
    replaces_source_graph: SourceGraphReplacement | None = None


class ReplayLimits(StrictRequest):
    """The reviewed fixed limits cannot silently expand in a retry."""

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


class ReplayAuthorization(StrictRequest):
    """New operational authorization never mutates an upstream acceptance record."""

    replay: bool
    finalization: bool
    acceptance: bool


INNER_POLICY = "accepted_05f_rules_with_general_inner_references_v1"
HEADER_POLICY = "accepted_05f_rules_with_inner_and_header_qualification_v1"
# The header trial retains every previously qualified inner-reference rule.
INNER_REFERENCE_POLICIES = frozenset({INNER_POLICY, HEADER_POLICY})


class PriorReplayBinding(StrictRequest):
    """Seal the previous working candidate and the review scope of one rule cycle."""

    candidate_root: str
    completion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    allowed_change_mentions: list[str]


class ReferenceReplaySpec(StrictRequest):
    """One explicit source-free consumer run, with no input or output defaults."""

    schema_version: Literal["er_commons.response_reference_run_spec.v6"]
    task_stage: Literal["05g"]
    policy: Literal[
        "accepted_05f_rules_with_verified_final_f1_substitution",
        "accepted_05f_rules_with_general_inner_references_v1",
        "accepted_05f_rules_with_inner_and_header_qualification_v1",
    ]
    prior_replay: PriorReplayBinding | None = None
    binding_freeze: str
    population_freeze: str
    inputs: ReplayInputBindings
    repository_bindings: list[FileBinding]
    output_relative_root: str = Field(
        pattern=r"^pipelines/brisbane_baylands/task_05_response_inventory/working/05g(?:/[a-zA-Z0-9_-]+)*$"
    )
    authorization: ReplayAuthorization
    limits: ReplayLimits
    source_pdf_access: Literal[False]
    model_access: Literal[False]
    hash_large_upstream_payloads: Literal[False]
    task05h_execution_authorized: Literal[False]

    @model_validator(mode="after")
    def validate_paths(self) -> ReferenceReplaySpec:
        """Validate every declared path before deriving a production identity."""
        if (self.policy in INNER_REFERENCE_POLICIES) != (self.prior_replay is not None):
            raise ValueError("inner-reference policy requires the prior replay comparison binding")
        if self.prior_replay is not None:
            relative_path(self.prior_replay.candidate_root)
            ids = self.prior_replay.allowed_change_mentions
            if (not ids and self.inputs.replaces_source_graph is None) or len(ids) != len(set(ids)):
                raise ValueError("rule-cycle comparison population must be nonempty and unique")
        relative_path(self.binding_freeze)
        relative_path(self.population_freeze)
        relative_path(self.output_relative_root)
        data = self.inputs.model_dump(mode="json")
        for name in ("task05d", "task05e"):
            relative_path(data[name]["candidate_root"])
            relative_path(data[name]["acceptance_path"])
        relative_path(data["task06h_pointer"])
        relative_path(data["task05f"]["root"])
        for key in ("readiness_root", "correspondence_root", "publication_root"):
            relative_path(data["task06g"][key])
        paths = [binding.path for binding in self.repository_bindings]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate repository binding")
        if not {self.binding_freeze, self.population_freeze, SCHEMA_PATH} <= set(paths):
            raise ValueError("missing frozen plan/population/schema repository binding")
        return self


def relative_path(value: str) -> Path:
    """Require a nonempty portable path beneath its declared root."""
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"not a contained relative path: {value!r}")
    return path


def contained_path(root: Path, value: str) -> Path:
    """Resolve a declared path and reject symlink escape before reading/writing."""
    path = (root / relative_path(value)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {value}")
    return path


def required_repository_paths(repository_root: Path) -> set[str]:
    """Freeze current owned consumers and all transitive historical helper owners."""
    paths = {
        path.relative_to(repository_root).as_posix()
        for path in owned_code_paths(repository_root, stage="reference")
    }
    paths.update(
        path.relative_to(repository_root).as_posix()
        for path in (repository_root / PACKAGE).glob("reference_replay*.py")
    )
    paths.update(
        {
            PACKAGE + "cli.py",
            PACKAGE + "code_inventory.py",
            "src/er_commons/document_publication/background_execution.py",
            "src/er_commons/document_records/document_structure/normalization.py",
            "src/er_commons/document_records/document_references/table_aliases.py",
            "src/er_commons/document_records/document_references/policy.py",
            "src/er_commons/document_records/document_references/exact_resolution.py",
            "src/er_commons/document_records/document_references/indexing.py",
            "src/er_commons/document_records/document_references/linking_core.py",
            "src/er_commons/document_records/document_references/types.py",
            "pyproject.toml",
            "uv.lock",
            SCHEMA_PATH,
            "benchmarks/er_bench/schemas/response_inventory/v6/reference_outcome.schema.json",
            "benchmarks/er_bench/schemas/response_inventory/v6/records.schema.json",
        }
    )
    return paths


def load_replay_spec(path: Path, repository_root: Path) -> tuple[dict[str, Any], str]:
    """Validate the v6 recipe and current writer digests without external reads."""
    raw = path.read_bytes()
    model = ReferenceReplaySpec.model_validate_json(raw)
    spec = model.model_dump(mode="json", exclude_none=True)
    expected = required_repository_paths(repository_root) | {
        model.binding_freeze,
        model.population_freeze,
    }
    if {item.path for item in model.repository_bindings} != expected:
        raise ValueError("repository binding inventory differs from current owned files")
    for binding in model.repository_bindings:
        selected = contained_path(repository_root, binding.path)
        if hashlib.sha256(selected.read_bytes()).hexdigest() != binding.sha256:
            raise ValueError(f"repository digest mismatch: {binding.path}")
    return spec, replay_identity(spec)


def replay_identity(spec: dict[str, Any]) -> str:
    """Hash behavior and inputs; later operational approvals do not rewrite the candidate."""
    return canonical_json_sha256(
        {key: value for key, value in spec.items() if key != "authorization"}
    )


def is_replay_spec(path: Path) -> bool:
    """Select only the explicit v6 branch without relaxing historical dispatch."""
    payload = json.loads(path.read_text())
    return isinstance(payload, dict) and payload.get("schema_version") == VERSION
