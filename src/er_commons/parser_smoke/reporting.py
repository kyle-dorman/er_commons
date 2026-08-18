"""Construct diagnostic summaries and enforce terminal smoke invariants."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.artifact_io import directory_bytes
from er_commons.parser_smoke.records import (
    FORBIDDEN_PUBLICATION_NAMES,
    TERMINAL_PAGE_STATUSES,
    PageOutcome,
    SourceSummary,
)
from er_commons.parser_smoke.warnings import (
    count_warning_scopes,
    parse_warning_scope_counts,
    sum_warning_scopes,
    warning_evidence_paths,
)


def write_jsonl(path: Path, records: list[PageOutcome]) -> None:
    """Write deterministic newline-delimited page outcomes."""
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    )


def _counts(
    records: list[PageOutcome],
    value: Callable[[PageOutcome], str],
) -> dict[str, int]:
    return dict(sorted(Counter(value(record) for record in records).items()))


def _range_observations(source_root: Path) -> list[dict[str, Any]]:
    conversion_root = source_root / "conversion"
    if not conversion_root.is_dir():
        return []
    return [
        json.loads(path.read_text()) for path in sorted(conversion_root.glob("*/observation.json"))
    ]


def build_source_summary(
    source_id: str,
    outcomes: list[PageOutcome],
    source_root: Path,
    source_wall_seconds: float,
) -> SourceSummary:
    """Aggregate one source from page outcomes and retained range observations."""
    observations = _range_observations(source_root)
    warning_scope_counts = count_warning_scopes(source_root, observations, outcomes)
    routes = Counter(str(outcome["route"]) for outcome in outcomes if "route" in outcome)
    return {
        "source_id": source_id,
        "requested_page_count": len(outcomes),
        "status_counts": _counts(outcomes, lambda outcome: outcome["status"]),
        "conversion_status_counts": _counts(outcomes, lambda outcome: outcome["conversion"]),
        "route_counts": dict(sorted(routes.items())),
        "table_stage_status_counts": _counts(outcomes, lambda outcome: outcome["table_stage"]),
        "logical_table_count": sum(
            int(outcome.get("tables", {}).get("table_count", 0)) for outcome in outcomes
        ),
        "warning_count": warning_scope_counts["aggregate"],
        "warning_scope_counts": warning_scope_counts,
        "warning_evidence": warning_evidence_paths(source_root),
        "error_count": sum(len(outcome["errors"]) for outcome in outcomes),
        "conversion_wall_seconds": sum(
            float(observation["wall_seconds"]) for observation in observations
        ),
        "observed_peak_rss_bytes": max(
            (int(observation["peak_rss_bytes"]) for observation in observations),
            default=None,
        ),
        "source_wall_seconds": source_wall_seconds,
        "retained_bytes_before_summary": directory_bytes(source_root),
    }


def validate_terminal_run(
    outcomes: list[PageOutcome],
    expected_page_count: int,
    smoke_root: Path,
) -> None:
    """Reject incomplete diagnostics and any production-like publication artifact."""
    if len(outcomes) != expected_page_count:
        raise RuntimeError("smoke did not retain one outcome per requested page")
    if any(outcome["status"] not in TERMINAL_PAGE_STATUSES for outcome in outcomes):
        raise RuntimeError("smoke retained a nonterminal page outcome")
    if any(outcome["table_stage"] == "pending" for outcome in outcomes):
        raise RuntimeError("smoke retained a nonterminal table-stage outcome")
    forbidden = [path for path in smoke_root.rglob("*") if path.name in FORBIDDEN_PUBLICATION_NAMES]
    if forbidden:
        raise RuntimeError(f"smoke wrote forbidden publication artifacts: {forbidden}")


def build_run_summary(
    *,
    run_id: str,
    attempt_id: str,
    outcomes: list[PageOutcome],
    source_summaries: list[SourceSummary],
    source_count: int,
    wall_seconds: float,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """Build the terminal aggregate from already validated source evidence."""
    routes = Counter(str(outcome["route"]) for outcome in outcomes if "route" in outcome)
    return {
        "schema_version": "er_commons.task03g1_smoke_summary.v2",
        "smoke_id": run_id,
        "attempt_id": attempt_id,
        "scope_status": "diagnostic_complete",
        "complete_document_semantics": False,
        "source_count": source_count,
        "requested_page_count": len(outcomes),
        "status_counts": _counts(outcomes, lambda outcome: outcome["status"]),
        "conversion_status_counts": _counts(outcomes, lambda outcome: outcome["conversion"]),
        "route_counts": dict(sorted(routes.items())),
        "table_stage_status_counts": _counts(outcomes, lambda outcome: outcome["table_stage"]),
        "logical_table_count": sum(
            int(outcome.get("tables", {}).get("table_count", 0)) for outcome in outcomes
        ),
        "warning_count": sum(int(summary["warning_count"]) for summary in source_summaries),
        "warning_scope_counts": sum_warning_scopes(
            [
                parse_warning_scope_counts(summary["warning_scope_counts"])
                for summary in source_summaries
            ]
        ),
        "error_count": sum(len(outcome["errors"]) for outcome in outcomes),
        "wall_seconds": wall_seconds,
        "observed_peak_rss_bytes": max(
            (
                int(summary["observed_peak_rss_bytes"])
                for summary in source_summaries
                if summary["observed_peak_rss_bytes"] is not None
            ),
            default=None,
        ),
        "source_summaries": [
            (
                Path("attempts")
                / attempt_id
                / "sources"
                / str(summary["source_id"])
                / "summary.json"
            ).as_posix()
            for summary in source_summaries
        ],
        "retained_artifact_bytes_before_inventory_and_summary": inventory["byte_count"],
        "artifact_inventory": (
            Path("attempts") / attempt_id / "artifact_inventory.json"
        ).as_posix(),
        "forbidden_publication_artifacts": [],
    }
