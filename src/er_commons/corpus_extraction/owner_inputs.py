"""Resolve content-owner configs and verify their shared execution inputs."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.config import RunSpec
from er_commons.document_extraction.producer_config import load_producer_config


@dataclass(frozen=True)
class OwnerConfigs:
    """Resolved configuration paths for the six stage-one content owners."""

    baseline_producer: Path
    hierarchy_producer: Path
    canonical: Path
    hierarchy_correction: Path
    semantic: Path
    cross_references: Path

    def as_dict(self) -> dict[str, Path]:
        """Return paths keyed by their persisted stage role names."""
        return {
            "baseline_producer": self.baseline_producer,
            "hierarchy_producer": self.hierarchy_producer,
            "canonical": self.canonical,
            "hierarchy_correction": self.hierarchy_correction,
            "semantic": self.semantic,
            "cross_references": self.cross_references,
        }


def prepare_owner_configs(
    *,
    project_root: Path,
    data_root: Path,
    run_spec: RunSpec,
    source_id: str,
) -> OwnerConfigs:
    """Resolve contained configs and join source/resource declarations."""
    selected = run_spec.content_owners(source_id)
    configs = OwnerConfigs(
        **{
            role: _contained_config(project_root, path)
            for role, path in selected.model_dump().items()
        }
    )
    for path in configs.as_dict().values():
        _require_selected_source(path, source_id)
    verify_owner_resources(configs, run_spec, data_root=data_root)
    return configs


def verify_owner_resources(configs: OwnerConfigs, run_spec: RunSpec, *, data_root: Path) -> None:
    """Verify effective owner settings and current host admission capacity."""
    _verify_effective_resources(configs, run_spec)
    _verify_host_capacity(data_root, run_spec)


def _contained_config(project_root: Path, relative_path: Path) -> Path:
    resolved = (project_root / relative_path).resolve()
    if not resolved.is_relative_to(project_root.resolve()) or not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _require_selected_source(path: Path, source_id: str) -> None:
    """Read the documented source selection shapes used by current owners."""
    config = json.loads(path.read_text())
    declared: list[str] = []
    if isinstance(config.get("source_id"), str):
        declared.append(config["source_id"])
    source = config.get("source")
    if isinstance(source, dict) and isinstance(source.get("source_id"), str):
        declared.append(source["source_id"])
    scope = config.get("ordered_materialization_scope")
    if isinstance(scope, list):
        declared.extend(
            item["source_id"]
            for item in scope
            if isinstance(item, dict) and isinstance(item.get("source_id"), str)
        )
    if declared and set(declared) != {source_id}:
        raise ValueError(
            "content-owner config selects another source: "
            f"expected={source_id}, observed={sorted(set(declared))}, path={path}"
        )


def _verify_effective_resources(configs: OwnerConfigs, run_spec: RunSpec) -> None:
    """Join declared bounds to the effective producer settings."""
    policy = run_spec.resource_policy
    expected_batches = (4, 4, 100)
    observed_batches = (
        policy.page_batch_size,
        policy.stage_batch_size,
        policy.queue_capacity,
    )
    if observed_batches != expected_batches:
        raise ValueError(
            "run-spec batch/queue bounds differ from installed Docling defaults: "
            f"expected={expected_batches}, observed={observed_batches}"
        )
    for role, path in (
        ("baseline_producer", configs.baseline_producer),
        ("hierarchy_producer", configs.hierarchy_producer),
    ):
        producer, _digest = load_producer_config(path)
        expected = (
            policy.cpu_threads_per_document,
            policy.device,
            policy.docling_timeout_seconds,
        )
        observed = (
            producer.thread_count,
            producer.device,
            producer.document_timeout_seconds,
        )
        if observed != expected:
            raise ValueError(
                f"resource policy differs from {role} effective config: "
                f"expected={expected}, observed={observed}, path={path}"
            )


def _verify_host_capacity(data_root: Path, run_spec: RunSpec) -> None:
    """Reject execution when declared storage or memory is unavailable."""
    policy = run_spec.resource_policy
    free_storage = shutil.disk_usage(data_root).free
    if free_storage < policy.storage_estimate_bytes:
        raise ValueError(
            "available artifact storage is below the declared estimate: "
            f"required={policy.storage_estimate_bytes}, observed={free_storage}, path={data_root}"
        )
    physical_memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    if physical_memory < policy.memory_estimate_bytes:
        raise ValueError(
            "physical memory is below the declared estimate: "
            f"required={policy.memory_estimate_bytes}, observed={physical_memory}"
        )
