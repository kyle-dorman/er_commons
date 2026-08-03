"""Validate stage lineage and document-specific hierarchy authorization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.corpus_extraction.owner_inputs import OwnerConfigs
from er_commons.source_freeze import sha256_file


@dataclass(frozen=True)
class OwnerCompletions:
    """Completion records returned by every stage-one content owner."""

    baseline_producer: Path
    hierarchy_producer: Path
    canonical: Path
    hierarchy_correction: Path
    semantic: Path
    cross_references: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "baseline_producer": self.baseline_producer,
            "hierarchy_producer": self.hierarchy_producer,
            "canonical": self.canonical,
            "hierarchy_correction": self.hierarchy_correction,
            "semantic": self.semantic,
            "cross_references": self.cross_references,
        }


def validate_owner_lineage(
    *,
    data_root: Path,
    source_id: str,
    hierarchy_disposition: dict[str, object],
    configs: OwnerConfigs,
    completions: OwnerCompletions,
) -> None:
    """Prove every owner consumed the immediately preceding sealed artifact."""
    baseline_id = completions.baseline_producer.parents[1].name
    hierarchy_id = completions.hierarchy_producer.parents[1].name
    canonical_id = completions.canonical.parents[1].name
    correction_id = completions.hierarchy_correction.parents[1].name
    semantic_id = completions.semantic.parents[1].name
    _require_producer_sources(completions, source_id)

    canonical_config = _json(configs.canonical)
    correction_config = _json(configs.hierarchy_correction)
    semantic_config = _json(configs.semantic)
    cross_reference_config = _json(configs.cross_references)
    expected_joins = {
        "canonical baseline producer": (
            canonical_config.get("producer_run_id"),
            baseline_id,
        ),
        "correction hierarchy producer": (
            correction_config.get("producer_run_id"),
            hierarchy_id,
        ),
        "semantic baseline candidate": (
            semantic_config.get("baseline_candidate_id"),
            canonical_id,
        ),
        "semantic baseline producer": (
            semantic_config.get("baseline_producer_run_id"),
            baseline_id,
        ),
        "semantic hierarchy producer": (
            semantic_config.get("hierarchy_producer_run_id"),
            hierarchy_id,
        ),
        "semantic hierarchy correction": (
            semantic_config.get("hierarchy_candidate_id"),
            correction_id,
        ),
        "cross-reference semantic input": (
            cross_reference_config.get("upstream_candidate_id"),
            semantic_id,
        ),
    }
    for label, (configured, observed) in expected_joins.items():
        if configured != observed:
            raise ValueError(
                f"stage lineage differs for {label}: expected={configured}, observed={observed}"
            )
    validate_hierarchy_authorization(
        data_root=data_root,
        source_id=source_id,
        disposition=hierarchy_disposition,
        correction_config=correction_config,
        semantic_config=semantic_config,
        correction_id=correction_id,
        correction_config_path=configs.hierarchy_correction,
    )
    _require_final_source(completions.cross_references, source_id)


def validate_hierarchy_authorization(
    *,
    data_root: Path,
    source_id: str,
    disposition: dict[str, object],
    correction_config: dict[str, object],
    semantic_config: dict[str, object],
    correction_id: str,
    correction_config_path: Path,
) -> None:
    """Join strict or bounded hierarchy authority through semantic materialization."""
    authority = disposition.get("authority")
    if correction_config.get("publication_authorization") != authority:
        raise ValueError("hierarchy disposition differs from correction authorization")
    relative = disposition.get("authorization_relative_path")
    semantic_relative = semantic_config.get("bounded_acceptance_relative_path")
    if authority == "strict_quality_gate":
        if relative is not None or semantic_relative is not None:
            raise ValueError("strict hierarchy authority joins bounded evidence")
        return
    if not isinstance(relative, str) or semantic_relative != relative:
        raise ValueError("hierarchy authorization path differs across stage owners")
    evidence_path = (data_root / relative).resolve()
    if not evidence_path.is_relative_to(data_root.resolve()) or not evidence_path.is_file():
        raise FileNotFoundError(evidence_path)
    evidence = _json(evidence_path)
    candidate = evidence.get("candidate")
    scope = evidence.get("scope")
    if not isinstance(candidate, dict) or not isinstance(scope, dict):
        raise ValueError("bounded hierarchy authorization lacks candidate or scope")
    identity = candidate.get("identity")
    accepted = bool(
        evidence.get("status") == "accepted_with_known_limitations"
        and scope.get("source_id") == source_id
        and scope.get("corpus_wide_acceptance") is False
        and isinstance(identity, dict)
        and identity.get("candidate_id") == correction_id
        and identity.get("config_sha256") == sha256_file(correction_config_path)
    )
    if not accepted:
        raise ValueError(
            "bounded hierarchy authorization does not seal this correction: "
            f"source={source_id}, candidate={correction_id}, path={evidence_path}"
        )


def _require_producer_sources(completions: OwnerCompletions, source_id: str) -> None:
    observed = {
        _json(completions.baseline_producer).get("source_id"),
        _json(completions.hierarchy_producer).get("source_id"),
    }
    if observed != {source_id}:
        raise ValueError(
            "producer completions do not join to the selected source: "
            f"expected={source_id}, observed={sorted(str(item) for item in observed)}"
        )


def _require_final_source(completion: Path, source_id: str) -> None:
    document_path = completion.parents[1] / "canonical" / "documents.jsonl"
    document = json.loads(document_path.read_text().splitlines()[0])
    if document.get("source_id") != source_id:
        raise ValueError(
            "final candidate source differs from selected source: "
            f"expected={source_id}, observed={document.get('source_id')}, path={document_path}"
        )


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
