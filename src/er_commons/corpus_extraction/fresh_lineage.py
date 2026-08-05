"""Deterministically bind fresh owner configs to newly completed upstreams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.canonical_extraction.config import load_canonicalization_config
from er_commons.corpus_extraction.owner_inputs import OwnerConfigs
from er_commons.cross_reference_enrichment.config import CrossReferenceEnrichmentConfig
from er_commons.document_extraction.producer_config import load_producer_config
from er_commons.hierarchy_correction.configuration import load_hierarchy_correction_config
from er_commons.semantic_materialization.config import load_semantic_materialization_config
from er_commons.source_freeze import sha256_file, write_json_atomic

JsonObject = dict[str, Any]


class FreshLineageBinder:
    """Create exact attempt-local configs only after their upstreams are sealed."""

    def __init__(
        self,
        *,
        data_root: Path,
        project_root: Path,
        source_id: str,
        templates: OwnerConfigs,
        attempt_root: Path,
    ) -> None:
        self._data_root = data_root
        self._project_root = project_root
        self._source_id = source_id
        self._templates = templates
        self._root = attempt_root / "effective_owner_configs"
        self._bindings: dict[str, JsonObject] = {}

    def initial_configs(self) -> tuple[Path, Path]:
        """Materialize byte-equivalent producer configs before either producer runs."""
        return (
            self._materialize("baseline_producer", {}),
            self._materialize("hierarchy_producer", {}),
        )

    def canonical_config(self, baseline_completion: Path) -> Path:
        """Bind canonicalization to the newly observed baseline producer."""
        return self._materialize(
            "canonical",
            {"producer_run_id": _candidate_id(baseline_completion)},
            upstreams={"baseline_producer": baseline_completion},
        )

    def correction_config(self, hierarchy_completion: Path) -> Path:
        """Bind hierarchy correction to the newly observed hierarchy producer."""
        return self._materialize(
            "hierarchy_correction",
            {"producer_run_id": _candidate_id(hierarchy_completion)},
            upstreams={"hierarchy_producer": hierarchy_completion},
        )

    def semantic_config(
        self,
        *,
        baseline_completion: Path,
        hierarchy_completion: Path,
        canonical_completion: Path,
        correction_completion: Path,
    ) -> Path:
        """Bind the semantic join to all four fresh upstream completions."""
        baseline_root = canonical_completion.parents[1]
        correction_root = correction_completion.parents[1]
        return self._materialize(
            "semantic",
            {
                "baseline_candidate_relative_root": _relative(baseline_root, self._data_root),
                "baseline_candidate_id": baseline_root.name,
                "baseline_producer_relative_root": _relative(
                    baseline_completion.parents[2], self._data_root
                ),
                "baseline_producer_run_id": _candidate_id(baseline_completion),
                "hierarchy_producer_relative_root": _relative(
                    hierarchy_completion.parents[2], self._data_root
                ),
                "hierarchy_producer_run_id": _candidate_id(hierarchy_completion),
                "hierarchy_candidate_relative_root": _relative(correction_root, self._data_root),
                "hierarchy_candidate_id": correction_root.name,
                "bounded_acceptance_relative_path": None,
                "bounded_acceptance_policy_relative_path": None,
                "producer_comparison_relative_path": None,
            },
            upstreams={
                "baseline_producer": baseline_completion,
                "hierarchy_producer": hierarchy_completion,
                "canonical": canonical_completion,
                "hierarchy_correction": correction_completion,
            },
        )

    def cross_reference_config(self, semantic_completion: Path) -> Path:
        """Bind enrichment to the exact fresh semantic completion and inventory."""
        semantic_root = semantic_completion.parents[1]
        inventory = semantic_root / "records" / "artifact_inventory.json"
        return self._materialize(
            "cross_references",
            {
                "upstream_candidate_id": semantic_root.name,
                "upstream_completion_sha256": sha256_file(semantic_completion),
                "upstream_inventory_sha256": sha256_file(inventory),
            },
            upstreams={"semantic": semantic_completion, "semantic_inventory": inventory},
        )

    def effective_configs(self) -> OwnerConfigs:
        """Return all six generated paths after every binding has been materialized."""
        paths = {role: self._root / f"{role}.json" for role in self._templates.as_dict()}
        missing = [role for role, path in paths.items() if not path.is_file()]
        if missing:
            raise ValueError(f"fresh effective configs are incomplete: {missing}")
        return OwnerConfigs(**paths)

    def _materialize(
        self,
        role: str,
        updates: JsonObject,
        *,
        upstreams: dict[str, Path] | None = None,
    ) -> Path:
        template = self._templates.as_dict()[role]
        value = _json(template)
        value.update(updates)
        path = self._root / f"{role}.json"
        write_json_atomic(path, value)
        _validate_effective_config(role, path)
        self._bindings[role] = {
            "template": _project_ref(template, self._project_root),
            "effective": {
                "path": path.relative_to(self._root.parent).as_posix(),
                "sha256": sha256_file(path),
            },
            "upstreams": {
                name: _data_ref(upstream, self._data_root)
                for name, upstream in (upstreams or {}).items()
            },
        }
        write_json_atomic(
            self._root / "binding_manifest.json",
            {
                "schema_version": "er_commons.fresh_owner_bindings.v1",
                "source_id": self._source_id,
                "lineage_mode": "fresh_build",
                "bindings": self._bindings,
            },
        )
        return path


def _validate_effective_config(role: str, path: Path) -> None:
    """Use each maintained owner loader as the generated-config gate."""
    loaders = {
        "baseline_producer": load_producer_config,
        "hierarchy_producer": load_producer_config,
        "canonical": load_canonicalization_config,
        "hierarchy_correction": load_hierarchy_correction_config,
        "semantic": load_semantic_materialization_config,
        "cross_references": CrossReferenceEnrichmentConfig.load,
    }
    loaders[role](path)


def _candidate_id(completion: Path) -> str:
    candidate_id = completion.parents[1].name
    if not candidate_id:
        raise ValueError(f"completion has no candidate parent: {completion}")
    return candidate_id


def _relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"fresh upstream escapes the data root: {path}")
    return resolved.relative_to(root.resolve()).as_posix()


def _project_ref(path: Path, root: Path) -> JsonObject:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}


def _data_ref(path: Path, root: Path) -> JsonObject:
    return {"path": _relative(path, root), "sha256": sha256_file(path)}


def _json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
