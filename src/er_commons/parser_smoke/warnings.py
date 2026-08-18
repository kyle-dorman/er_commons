"""Persist and summarize smoke warnings at their true provenance scope."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

from er_commons.artifact_io import write_json_atomic
from er_commons.parser_smoke.records import PageOutcome


class WarningScopeCounts(TypedDict):
    """Counts that distinguish raw evidence from aggregate warning events."""

    source_manifest_raw: int
    source_manifest_unique: int
    conversion: int
    page: int
    aggregate: int


def retain_source_warnings(source_root: Path, source_id: str, warnings: list[str]) -> None:
    """Persist source-manifest warnings once without suppressing duplicates."""
    source_root.mkdir(parents=True, exist_ok=True)
    write_json_atomic(
        source_root / "source_warnings.json",
        {
            "scope": "source_manifest",
            "source_id": source_id,
            "raw_warnings": warnings,
            "raw_count": len(warnings),
            "exact_unique_count": len(set(warnings)),
        },
    )


def _source_warning_strings(source_root: Path) -> list[str]:
    """Load source evidence and verify its persisted self-accounting."""
    path = source_root / "source_warnings.json"
    if not path.is_file():
        return []
    evidence = json.loads(path.read_text())
    warnings = [str(item) for item in evidence["raw_warnings"]]
    if int(evidence["raw_count"]) != len(warnings):
        raise ValueError("source warning raw count disagrees with retained evidence")
    if int(evidence["exact_unique_count"]) != len(set(warnings)):
        raise ValueError("source warning unique count disagrees with retained evidence")
    return warnings


def count_warning_scopes(
    source_root: Path,
    observations: list[dict[str, Any]],
    outcomes: list[PageOutcome],
) -> WarningScopeCounts:
    """Count warnings once at source, conversion, or page scope."""
    source_warnings = _source_warning_strings(source_root)
    source_unique_count = len(set(source_warnings))
    conversion_count = sum(
        len(observation.get("captured_python_warnings", [])) for observation in observations
    )
    page_count = sum(len(outcome["warnings"]) for outcome in outcomes)
    return {
        "source_manifest_raw": len(source_warnings),
        "source_manifest_unique": source_unique_count,
        "conversion": conversion_count,
        "page": page_count,
        "aggregate": source_unique_count + conversion_count + page_count,
    }


def warning_evidence_paths(source_root: Path) -> list[str]:
    """Return deterministic relative paths supporting a source summary."""
    paths = []
    if (source_root / "source_warnings.json").is_file():
        paths.append("source_warnings.json")
    paths.extend(
        path.relative_to(source_root).as_posix()
        for path in sorted((source_root / "conversion").glob("*/observation.json"))
    )
    return paths


def sum_warning_scopes(source_counts: list[WarningScopeCounts]) -> WarningScopeCounts:
    """Aggregate already scoped source counts without changing their meaning."""
    return {
        "source_manifest_raw": sum(counts["source_manifest_raw"] for counts in source_counts),
        "source_manifest_unique": sum(counts["source_manifest_unique"] for counts in source_counts),
        "conversion": sum(counts["conversion"] for counts in source_counts),
        "page": sum(counts["page"] for counts in source_counts),
        "aggregate": sum(counts["aggregate"] for counts in source_counts),
    }


def parse_warning_scope_counts(value: dict[str, Any]) -> WarningScopeCounts:
    """Read persisted source-summary counts into their closed internal shape."""
    return {
        "source_manifest_raw": int(value["source_manifest_raw"]),
        "source_manifest_unique": int(value["source_manifest_unique"]),
        "conversion": int(value["conversion"]),
        "page": int(value["page"]),
        "aggregate": int(value["aggregate"]),
    }
