"""Interpret retained table-parser attempt evidence for human review."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_list,
    require_mapping,
)
from er_commons.human_review_support.task04.models import (
    JsonValue,
    ParserAttempt,
    ParserPageEvidence,
    TableParserEvidence,
)


def table_parser_page_evidence(
    data_root: Path, candidate: Path, source_id: str, physical_page: int
) -> ParserPageEvidence | None:
    """Summarize retained parser attempts for one physical PDF page."""
    table_root = _producer_table_root(data_root, candidate, source_id)
    if table_root is None:
        return None
    result_path = table_root / "pages" / f"page_{physical_page:05d}" / "result.json"
    if not result_path.is_file():
        return None
    result = read_json_object(result_path)
    parser_evidence_value = result.get("parser_evidence")
    parser_evidence = (
        require_mapping(parser_evidence_value, path=f"{result_path}.parser_evidence")
        if isinstance(parser_evidence_value, dict)
        else {}
    )
    attempts = tuple(_parser_attempts(result, parser_evidence, result_path))
    tables = require_list(result.get("tables", []), path=f"{result_path}.tables")
    selected = Counter(
        str(require_mapping(table, path=f"{result_path}.tables[]").get("parser") or "unknown")
        for table in tables
    )
    return ParserPageEvidence(
        physical_page=physical_page,
        route=_optional_text(result.get("route")),
        detected_table_count=_optional_int(result.get("detected_table_count")),
        producer_table_count=_optional_int(result.get("table_count")),
        selected_parser_counts=tuple(sorted(selected.items())),
        attempts=attempts,
    )


def _parser_attempts(
    result: dict[str, JsonValue], evidence: dict[str, JsonValue], path: Path
) -> list[ParserAttempt]:
    """Translate parser-specific retained fields into a stable typed vocabulary."""
    attempts: list[ParserAttempt] = []
    attempts.extend(_camelot_attempts(result, evidence, path))
    attempts.extend(_region_stream_attempts(evidence, path))
    attempts.extend(_learned_attempts(evidence, path))
    return attempts or [ParserAttempt("No retained table-parser attempt detail", "not_recorded")]


def _camelot_attempts(
    result: dict[str, JsonValue], evidence: dict[str, JsonValue], path: Path
) -> list[ParserAttempt]:
    """Build Stream, Lattice, and Network attempt summaries."""
    attempts: list[ParserAttempt] = []
    if "stream_return_count" in evidence:
        retained = _integer(evidence.get("stream_retained_count"), default=0)
        attempts.append(
            ParserAttempt(
                "Camelot Stream",
                "retained" if retained else "no_retained_table",
                {
                    "returned": _integer(evidence.get("stream_return_count"), default=0),
                    "retained": retained,
                },
            )
        )
    if "lattice_return_count" in evidence:
        matches = require_list(
            evidence.get("region_matches", []), path=f"{path}.parser_evidence.region_matches"
        )
        matched = sum(
            bool(
                require_mapping(value, path=f"{path}.region_matches[]").get(
                    "camelot_matched",
                    require_mapping(value, path=f"{path}.region_matches[]").get("matched", False),
                )
            )
            for value in matches
        )
        attempts.append(
            ParserAttempt(
                "Camelot Lattice",
                "matched" if matched else "no_region_match",
                {
                    "returned": _integer(evidence.get("lattice_return_count"), default=0),
                    "matched_regions": matched,
                    "region_count": len(matches),
                },
            )
        )
    if "network_return_count" in evidence:
        decisions = require_list(
            evidence.get("network_decisions", []),
            path=f"{path}.parser_evidence.network_decisions",
        )
        returned = _integer(evidence.get("network_return_count"), default=0)
        route = _optional_text(result.get("route"))
        status = (
            "not_enabled_for_layout_route"
            if route == "layout_regions"
            else "retained"
            if returned
            else "no_return"
        )
        retained = sum(
            bool(require_mapping(value, path=f"{path}.network_decisions[]").get("retained"))
            for value in decisions
        )
        attempts.append(
            ParserAttempt("Camelot Network", status, {"returned": returned, "retained": retained})
        )
    return attempts


def _region_stream_attempts(evidence: dict[str, JsonValue], path: Path) -> list[ParserAttempt]:
    """Translate bounded region-stream fallback attempts."""
    values = require_list(
        evidence.get("region_stream_attempts", []),
        path=f"{path}.parser_evidence.region_stream_attempts",
    )
    result: list[ParserAttempt] = []
    for value in values:
        attempt = require_mapping(value, path=f"{path}.region_stream_attempts[]")
        details = _present_fields(attempt, ("region_id", "reason"))
        result.append(
            ParserAttempt(
                "Camelot region-stream fallback",
                str(attempt.get("status") or "unknown"),
                details,
            )
        )
    return result


def _learned_attempts(evidence: dict[str, JsonValue], path: Path) -> list[ParserAttempt]:
    """Translate retained TableFormer fallback attempts and measurements."""
    values = require_list(
        evidence.get("learned_fallback_attempts", []),
        path=f"{path}.parser_evidence.learned_fallback_attempts",
    )
    result: list[ParserAttempt] = []
    for value in values:
        attempt = require_mapping(value, path=f"{path}.learned_fallback_attempts[]")
        measurements_value = attempt.get("measurements", {})
        measurements = (
            require_mapping(measurements_value, path=f"{path}.learned.measurements")
            if isinstance(measurements_value, dict)
            else {}
        )
        details = _present_fields(attempt, ("region_id", "reason"))
        details.update(
            {
                "predicted_shape": [
                    measurements.get("predicted_rows"),
                    measurements.get("predicted_columns"),
                ],
                "matched_native_tokens": measurements.get("tableformer_matched_native_token_count"),
                "native_tokens": measurements.get("native_token_count"),
                "unmatched_leading_tokens": measurements.get("unmatched_leading_token_count"),
            }
        )
        result.append(
            ParserAttempt(
                "TableFormer learned fallback",
                str(attempt.get("status") or "unknown"),
                details,
            )
        )
    return result


def table_family_parser_evidence(
    data_root: Path, candidate: Path, source_id: str, physical_pages: list[int]
) -> TableParserEvidence | None:
    """Collect retained parser attempts for every page in a sampled family."""
    pages = tuple(
        evidence
        for page in physical_pages
        if (evidence := table_parser_page_evidence(data_root, candidate, source_id, page))
        is not None
    )
    return (
        TableParserEvidence(pages, "every selected page in this table family", False)
        if pages
        else None
    )


def warning_table_parser_evidence(
    data_root: Path,
    candidate: Path | None,
    source_id: str,
    physical_page: int | None,
) -> TableParserEvidence | None:
    """Attach parser evidence for the exact or contextual warning page."""
    if candidate is None or physical_page is None:
        return None
    evidence = table_parser_page_evidence(data_root, candidate, source_id, physical_page)
    return (
        TableParserEvidence((evidence,), "the example page shown above")
        if evidence is not None
        else None
    )


def _producer_table_root(data_root: Path, candidate: Path, source_id: str) -> Path | None:
    """Resolve retained table evidence bound to a selected publication candidate."""
    identity_path = candidate / "records" / "document_identity.json"
    if not identity_path.is_file():
        return None
    identity = read_json_object(identity_path)
    completions_value = identity.get("stage_completions")
    if not isinstance(completions_value, dict):
        return None
    completions = require_mapping(completions_value, path=f"{identity_path}.stage_completions")
    stable_value = completions.get("stable_content_evidence")
    if not isinstance(stable_value, dict):
        return None
    stable = require_mapping(stable_value, path=f"{identity_path}.stable_content_evidence")
    relative_path = stable.get("path")
    if not isinstance(relative_path, str):
        return None
    producer_root = (data_root / relative_path).parent.parent
    table_root = producer_root / "documents" / source_id / "producer" / "tables"
    return table_root if table_root.is_dir() else None


def _present_fields(source: dict[str, JsonValue], fields: tuple[str, ...]) -> dict[str, JsonValue]:
    """Copy only present parser-specific diagnostic fields."""
    return {field: source[field] for field in fields if source.get(field) is not None}


def _integer(value: object, *, default: int) -> int:
    """Coerce retained numeric counters without accepting booleans."""
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _optional_int(value: object) -> int | None:
    """Narrow an optional integer counter."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_text(value: object) -> str | None:
    """Narrow optional string metadata."""
    return value if isinstance(value, str) else None


__all__ = [
    "table_family_parser_evidence",
    "table_parser_page_evidence",
    "warning_table_parser_evidence",
]
