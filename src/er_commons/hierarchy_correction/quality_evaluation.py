"""External quality-report producers for development and control evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.hierarchy.specification import (
    HierarchyEvaluationSpec,
    load_hierarchy_evaluation_spec,
)
from er_commons.hierarchy_correction.decision_builder import build_rule_decisions
from er_commons.hierarchy_correction.digests import canonical_json_sha256
from er_commons.hierarchy_correction.evaluation import (
    build_correction_review_inventory,
    evaluate_development_cases,
    evaluate_expected_cases,
)
from er_commons.hierarchy_correction.features import build_feature_seeds
from er_commons.hierarchy_correction.preservation import (
    ManagedArtifactSnapshot,
    assert_artifacts_preserved,
)
from er_commons.hierarchy_correction.regime_builder import build_numbering_regimes
from er_commons.hierarchy_correction.toc_builder import build_visible_toc

JsonRecord = dict[str, Any]
_REPORT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ControlArtifact:
    """One fixed diagnostic range loaded from accepted Task 03E evidence."""

    range_name: str
    document_path: Path
    conversion_pages_path: Path
    document: JsonRecord
    conversion_pages: JsonRecord


@dataclass(frozen=True)
class EvaluationSurface:
    """One explicitly named source surface and its pure correction records."""

    name: str
    source_id: str
    features: tuple[JsonRecord, ...]
    regimes: tuple[JsonRecord, ...]
    decisions: tuple[JsonRecord, ...]


@dataclass(frozen=True)
class ControlProjection:
    """Both fixed main-report surfaces and their combined decisions."""

    surfaces: tuple[EvaluationSurface, ...]

    @property
    def decisions(self) -> tuple[JsonRecord, ...]:
        return tuple(item for surface in self.surfaces for item in surface.decisions)


def _json_object(path: Path) -> JsonRecord:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_fixed_control_artifacts(
    *,
    evaluation_config_path: Path,
    control_ranges_root: Path,
) -> tuple[HierarchyEvaluationSpec, tuple[ControlArtifact, ...]]:
    """Load exactly the two range names frozen by the Task 03E evaluation config."""
    specification, _digest = load_hierarchy_evaluation_spec(evaluation_config_path)
    artifacts: list[ControlArtifact] = []
    for range_name in specification.control_harness.expected_range_names:
        range_root = control_ranges_root / range_name
        document_path = range_root / "document.json"
        conversion_path = range_root / "conversion_pages.json"
        if not document_path.is_file() or not conversion_path.is_file():
            raise FileNotFoundError(f"fixed control artifacts are incomplete: {range_name}")
        artifacts.append(
            ControlArtifact(
                range_name=range_name,
                document_path=document_path,
                conversion_pages_path=conversion_path,
                document=_json_object(document_path),
                conversion_pages=_json_object(conversion_path),
            )
        )
    return specification, tuple(artifacts)


def build_control_projection(
    artifacts: tuple[ControlArtifact, ...],
    *,
    source_id: str = "deir_main",
) -> ControlProjection:
    """Run both fixed controls through the same pure feature and rule stages."""
    surfaces: list[EvaluationSurface] = []
    for artifact in artifacts:
        seeds = build_feature_seeds(artifact.document, artifact.conversion_pages)
        toc = build_visible_toc(seeds, ())
        regimes = build_numbering_regimes(list(toc.features), ())
        decisions = build_rule_decisions(
            features=regimes.features,
            toc_entries=toc.entries,
            reconciliations=toc.reconciliations,
            regimes=regimes.regimes,
        )
        surfaces.append(
            EvaluationSurface(
                name=artifact.range_name,
                source_id=source_id,
                features=regimes.features,
                regimes=regimes.regimes,
                decisions=decisions.decisions,
            )
        )
    return ControlProjection(tuple(surfaces))


def evaluate_control_cases(
    *,
    development_cases: tuple[JsonRecord, ...],
    projection: ControlProjection,
) -> JsonRecord:
    """Require the two R02 demotions and one R06 ambiguity exactly."""
    cases = tuple(item for item in development_cases if item["source_id"] == "deir_main")
    if len(cases) != 3:
        raise ValueError(f"expected exactly three main-control cases, found {len(cases)}")
    report = evaluate_expected_cases(cases=cases, decisions=projection.decisions)
    expected_rules = sorted(
        ["R02_DEMOTE_BULLET_HEADING", "R02_DEMOTE_BULLET_HEADING", "R06_FLAG_STRUCTURAL_AMBIGUITY"]
    )
    if sorted(item["expected_rule_id"] for item in cases) != expected_rules:
        raise ValueError("main-control case rules differ from the frozen 2xR02 plus R06 scope")
    return {**report, "source_id": "deir_main"}


def combine_development_report(
    *,
    development_cases: tuple[JsonRecord, ...],
    appendix_decisions: tuple[JsonRecord, ...],
    control_projection: ControlProjection,
) -> JsonRecord:
    """Combine five Appendix and three control decisions into the exact 8/8 gate."""
    appendix_cases = tuple(
        item for item in development_cases if item["source_id"] == "deir_appendix_p"
    )
    control_cases = tuple(item for item in development_cases if item["source_id"] == "deir_main")
    if (len(appendix_cases), len(control_cases)) != (5, 3):
        raise ValueError("development source partition differs from frozen 5+3 scope")
    return evaluate_development_cases(
        cases=development_cases,
        decisions=(*appendix_decisions, *control_projection.decisions),
    )


def evaluate_document_development_cases(
    *,
    source_id: str,
    development_cases: tuple[JsonRecord, ...],
    decisions: tuple[JsonRecord, ...],
) -> JsonRecord:
    """Evaluate an arbitrary nonempty case bundle for exactly one selected document."""
    if {item.get("source_id") for item in development_cases} != {source_id}:
        raise ValueError("generic development cases differ from the selected source")
    return evaluate_expected_cases(cases=development_cases, decisions=decisions)


def build_combined_review_inventory(
    surfaces: tuple[EvaluationSurface, ...],
) -> JsonRecord:
    """Build one complete applied R02/R04/R05/R07 inventory across named surfaces."""
    records: list[JsonRecord] = []
    counts: dict[str, int] = {}
    surface_counts: dict[str, int] = {}
    for surface in surfaces:
        inventory = build_correction_review_inventory(
            features=surface.features,
            decisions=surface.decisions,
        )
        surface_counts[surface.name] = inventory["record_count"]
        for rule_id, count in inventory["counts_by_rule"].items():
            counts[rule_id] = counts.get(rule_id, 0) + count
        for record in inventory["records"]:
            records.append(
                {
                    "surface": surface.name,
                    "source_id": surface.source_id,
                    **record,
                }
            )
    records.sort(
        key=lambda item: (
            item["source_id"],
            item["surface"],
            item["reading_order_index"],
            item["stable_item_key"],
        )
    )
    return {
        "status": "complete",
        "surface_count": len(surfaces),
        "record_count": len(records),
        "surface_record_counts": surface_counts,
        "counts_by_rule": dict(sorted(counts.items())),
        "records": records,
    }


def build_preservation_report(
    *,
    before: tuple[ManagedArtifactSnapshot, ...],
    after: tuple[ManagedArtifactSnapshot, ...],
) -> JsonRecord:
    """Summarize exact producer and Task 03D.1 before/after preservation."""
    expected_kinds = {"producer", "task03d1_reference"}
    if {item.kind for item in before} != expected_kinds:
        return {
            "status": "reject",
            "artifact_count": len(before),
            "detail": "preservation report requires producer and Task 03D.1 snapshots",
        }
    try:
        assert_artifacts_preserved(before, after)
    except ValueError as error:
        return {
            "status": "reject",
            "artifact_count": len(before),
            "detail": str(error),
        }
    artifacts = []
    for snapshot in before:
        snapshot_record = {
            "kind": snapshot.kind,
            "identity": snapshot.identity,
            "completion_sha256": snapshot.completion_sha256,
            "inventory_sha256": snapshot.inventory_sha256,
            "files": [
                {
                    "path": item.path,
                    "byte_size": item.byte_size,
                    "sha256": item.sha256,
                }
                for item in snapshot.files
            ],
        }
        artifacts.append(
            {
                "kind": snapshot.kind,
                "identity": snapshot.identity,
                "managed_file_count": len(snapshot.files),
                "snapshot_sha256": canonical_json_sha256(snapshot_record),
            }
        )
    return {
        "status": "pass",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def build_repeat_resource_report(
    *,
    candidate_id: str,
    repeat_comparison: JsonRecord,
    metrics: JsonRecord,
) -> JsonRecord:
    """Combine the prepublication normalized-repeat and resource gates."""
    wall_time_ratio = metrics.get("wall_time_ratio")
    artifact_bytes_ratio = metrics.get("artifact_bytes_ratio")
    repeat_passed = bool(
        repeat_comparison.get("candidate_id") == candidate_id
        and repeat_comparison.get("semantic_match") is True
        and len(repeat_comparison.get("builds", [])) == 3
    )
    resource_passed = bool(
        metrics.get("candidate_id") == candidate_id
        and metrics.get("cheap_relative_to_producer") is True
        and isinstance(wall_time_ratio, (int, float))
        and wall_time_ratio < 1
        and isinstance(artifact_bytes_ratio, (int, float))
        and artifact_bytes_ratio < 1
    )
    passed = repeat_passed and resource_passed
    return {
        "status": "pass" if passed else "reject",
        "candidate_id": candidate_id,
        "fresh_build_count": len(repeat_comparison.get("builds", [])),
        "semantic_match": repeat_comparison.get("semantic_match") is True,
        "repeat_passed": repeat_passed,
        "median_fresh_wall_time_seconds": metrics.get("median_fresh_wall_time_seconds"),
        "wall_time_ratio": wall_time_ratio,
        "artifact_bytes": metrics.get("artifact_bytes"),
        "artifact_bytes_ratio": artifact_bytes_ratio,
        "peak_rss_bytes": metrics.get("peak_rss_bytes"),
        "resource_passed": resource_passed,
    }


def stable_report_bytes(report: Mapping[str, Any]) -> bytes:
    """Serialize one named external report deterministically."""
    return (
        json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def write_named_quality_reports(
    root: Path,
    reports: Mapping[str, JsonRecord],
) -> JsonRecord:
    """Persist reports and a digest manifest suitable for a terminal quality gate."""
    root.mkdir(parents=True, exist_ok=True)
    entries: list[JsonRecord] = []
    accepted_statuses = {"pass", "complete"}
    for name in sorted(reports):
        if _REPORT_NAME.fullmatch(name) is None:
            raise ValueError(f"invalid quality report name: {name}")
        path = root / f"{name}.json"
        if path.exists():
            raise FileExistsError(path)
        value = stable_report_bytes(reports[name])
        path.write_bytes(value)
        entries.append(
            {
                "name": name,
                "path": path.relative_to(root).as_posix(),
                "status": reports[name].get("status"),
                "byte_size": len(value),
                "sha256": hashlib.sha256(value).hexdigest(),
            }
        )
    overall = (
        "pass"
        if entries and all(item["status"] in accepted_statuses for item in entries)
        else "reject"
    )
    manifest: JsonRecord = {
        "status": overall,
        "report_count": len(entries),
        "reports": entries,
    }
    manifest_bytes = stable_report_bytes(manifest)
    manifest_path = root / "quality_report_manifest.json"
    if manifest_path.exists():
        raise FileExistsError(manifest_path)
    manifest_path.write_bytes(manifest_bytes)
    return {
        **manifest,
        "manifest_path": manifest_path.relative_to(root).as_posix(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
